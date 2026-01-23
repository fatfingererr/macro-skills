# Chrome CDP 數據爬取 SOP

透過 Chrome DevTools Protocol (CDP) 連接到已開啟的 Chrome 瀏覽器，繞過反爬蟲防護，提取動態渲染的網頁數據。

---

## 適用情境

許多數據平台都有嚴格的反爬蟲機制：

1. **Cloudflare / reCAPTCHA 防護**：偵測自動化瀏覽器（Selenium、Playwright、Puppeteer）
2. **JavaScript 動態渲染**：數據透過 Highcharts、ECharts、D3.js 等圖表庫動態載入
3. **登入牆**：部分數據需要會員登入才能存取

**解決方案**：使用你自己的 Chrome（含登入狀態與瀏覽歷史），透過 CDP 遠端連接提取數據。這個方法對網站來說就是「真人在用瀏覽器」。

---

## 核心原理

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  Python Script  │ ◄────────────────► │  Chrome Browser │
│  (CDP Client)   │    Port 9222       │  (你的 Profile) │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │ Runtime.evaluate()                   │
        ▼                                      ▼
   執行 JavaScript ──────────────────► 提取頁面數據
```

---

## 前置準備

### 1. 安裝 Python 套件

```bash
pip install requests websocket-client
```

### 2. 建立 Chrome Debug Profile

建立一個專用的 Chrome profile 目錄（只需執行一次）：

```bash
# Windows
mkdir "%USERPROFILE%\.chrome-debug-profile"

# macOS / Linux
mkdir -p ~/.chrome-debug-profile
```

### 3. 複製登入狀態（可選）

如果你已經在原本的 Chrome 登入過目標網站，可以複製 cookies：

```bash
# Windows (Git Bash)
cp "$LOCALAPPDATA/Google/Chrome/User Data/Default/Cookies" "$USERPROFILE/.chrome-debug-profile/"
cp "$LOCALAPPDATA/Google/Chrome/User Data/Default/Login Data" "$USERPROFILE/.chrome-debug-profile/"
cp "$LOCALAPPDATA/Google/Chrome/User Data/Local State" "$USERPROFILE/.chrome-debug-profile/"
```

---

## 操作流程

### Step 1：關閉所有 Chrome 視窗

確保沒有其他 Chrome 實例在執行，否則調試端口會無法啟動。

### Step 2：啟動 Chrome（帶調試端口）

**Windows：**

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://your-target-website.com"
```

**macOS：**

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://your-target-website.com"
```

**Linux：**

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://your-target-website.com"
```

### Step 3：驗證連線

等待 Chrome 開啟並載入頁面後，確認調試端口可連線：

```bash
curl -s http://127.0.0.1:9222/json
```

成功的回應範例：

```json
[{
   "title": "頁面標題",
   "url": "https://your-target-website.com/...",
   "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/XXXXXX"
}]
```

### Step 4：透過 CDP 執行 JavaScript 提取數據

```python
import json
import requests
import websocket

CDP_PORT = 9222

def get_ws_url(url_contains=None):
    """獲取目標頁面的 WebSocket URL"""
    resp = requests.get(f'http://127.0.0.1:{CDP_PORT}/json')
    pages = resp.json()

    for page in pages:
        if url_contains and url_contains.lower() in page.get('url', '').lower():
            return page.get('webSocketDebuggerUrl')

    return pages[0].get('webSocketDebuggerUrl') if pages else None


def execute_js(ws_url, js_code):
    """透過 CDP 執行 JavaScript 並取得結果"""
    ws = websocket.create_connection(ws_url)

    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": js_code,
            "returnByValue": True
        }
    }
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    ws.close()

    return result['result']['result'].get('value')


# 使用範例
ws_url = get_ws_url('target-website')
data = execute_js(ws_url, 'document.title')
print(data)
```

---

## 關鍵參數說明

| 參數 | 說明 |
|------|------|
| `--remote-debugging-port=9222` | 開啟 CDP 調試端口（可改用其他端口） |
| `--remote-allow-origins=*` | 允許所有來源連線（**必要**，否則 WebSocket 會被拒絕） |
| `--user-data-dir=<path>` | 指定 profile 目錄（**必須是非預設目錄**） |

---

## 常見問題

### Q1: 為什麼一定要用非預設的 user-data-dir？

Chrome 的調試模式要求使用非預設目錄。如果使用預設目錄，會出現錯誤：
```
DevTools remote debugging requires a non-default data directory.
```

### Q2: 網站還是擋住怎麼辦？

1. **手動完成驗證**：在 Chrome 開啟後，手動完成 Cloudflare/reCAPTCHA 驗證
2. **登入帳號**：登入網站帳號後再執行爬取
3. **等待頁面載入**：確認圖表/數據完全載入後再執行
4. **增加人類行為**：在頁面上捲動、點擊，讓行為更像真人

### Q3: WebSocket 連線被拒絕 (403 Forbidden)

確認啟動 Chrome 時有加上 `--remote-allow-origins=*` 參數。

### Q4: 如何同時操作多個頁面？

```python
# 列出所有頁面
resp = requests.get('http://127.0.0.1:9222/json')
pages = resp.json()

# 開啟新分頁
requests.get('http://127.0.0.1:9222/json/new?https://another-page.com')

# 關閉特定分頁
page_id = pages[0]['id']
requests.get(f'http://127.0.0.1:9222/json/close/{page_id}')
```

---

## 常用 CDP 指令

### 頁面操作

```python
# 導航到新網址
execute_js(ws_url, 'window.location.href = "https://new-url.com"')

# 捲動頁面
execute_js(ws_url, 'window.scrollTo(0, 1000)')

# 點擊元素
execute_js(ws_url, 'document.querySelector("button.submit").click()')

# 填入表單
execute_js(ws_url, 'document.querySelector("input#email").value = "test@example.com"')
```

### 數據提取

```python
# 取得頁面標題
execute_js(ws_url, 'document.title')

# 取得所有連結
execute_js(ws_url, 'JSON.stringify([...document.querySelectorAll("a")].map(a => a.href))')

# 取得表格數據
execute_js(ws_url, '''
JSON.stringify([...document.querySelectorAll("table tr")].map(row =>
    [...row.querySelectorAll("td, th")].map(cell => cell.textContent.trim())
))
''')
```

---

## 整合到自動化流程的建議

### 快取機制

```python
from pathlib import Path
from datetime import datetime, timedelta
import json

CACHE_DIR = Path("cache")
CACHE_MAX_AGE = timedelta(hours=12)

def get_cache_path(key):
    return CACHE_DIR / f"{key}.json"

def is_cache_valid(key):
    cache_file = get_cache_path(key)
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return (datetime.now() - mtime) < CACHE_MAX_AGE

def load_cache(key):
    if is_cache_valid(key):
        with open(get_cache_path(key), 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_cache(key, data):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(get_cache_path(key), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### 錯誤處理

```python
def safe_execute_js(ws_url, js_code, retries=3):
    for attempt in range(retries):
        try:
            return execute_js(ws_url, js_code)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2)
```

---

## 相關資源

- [Chrome DevTools Protocol 官方文件](https://chromedevtools.github.io/devtools-protocol/)
- [CDP 指令完整列表](https://chromedevtools.github.io/devtools-protocol/tot/)

---

## 參考實作

針對特定平台的完整爬蟲實作，請參考：

- [MacroMicro Highcharts 爬蟲](./macromicro-highcharts-crawler.md)

---

*最後更新：2025-01-23*
