# 數據來源 (Data Sources)

本技能需要四條主要時間序列，使用 Chrome CDP 連接到 MacroMicro 抓取真實數據。

## 數據需求概覽

| 指標 | 來源 | 方式 | 頻率 |
|------|------|------|------|
| **MOVE** | MacroMicro | Chrome CDP 爬蟲 | 日 |
| **JGB 10Y** | MacroMicro | Chrome CDP 爬蟲 | 日 |
| **VIX** | Yahoo Finance | yfinance API | 日 |
| **Credit (IG OAS)** | FRED | HTTP CSV | 日 |

---

## MOVE Index（利率波動率）

### 主要來源：MacroMicro (CDP)

**URL**: https://en.macromicro.me/charts/35584/us-treasury-move-index

**技術細節**：
- 使用 Chrome DevTools Protocol (CDP) 連接到已開啟的 Chrome
- 透過 JavaScript 執行從 Highcharts 對象提取時間序列數據
- 無需 API key，繞過 Cloudflare 防護

**數據特性**：
- 頻率：日
- 延遲：T+1
- 歷史深度：完整（視圖表顯示範圍）

### 程式碼範例

```python
from fetch_data import fetch_macromicro_via_cdp

# 確保 Chrome 已用 CDP 模式啟動並開啟 MOVE 頁面
move = fetch_macromicro_via_cdp("MOVE", port=9222)
print(f"MOVE: {len(move)} 筆, {move.index.min()} ~ {move.index.max()}")
```

---

## JGB 10Y（日本 10 年期國債殖利率）

### 主要來源：MacroMicro (CDP)

**URL**: https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield

**技術細節**：
- 同 MOVE，使用 Chrome CDP 爬蟲
- 數據單位：%（殖利率）

**數據特性**：
- 頻率：日
- 延遲：T+1
- 歷史深度：完整

### 程式碼範例

```python
from fetch_data import fetch_macromicro_via_cdp

# 確保 Chrome 已開啟 JGB 頁面
jgb = fetch_macromicro_via_cdp("JGB10Y", port=9222)
print(f"JGB10Y: {len(jgb)} 筆, {jgb.index.min()} ~ {jgb.index.max()}")
```

---

## VIX（股市波動率）

### 主要來源：Yahoo Finance

```python
import yfinance as yf

def fetch_vix(start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 取得 VIX"""
    data = yf.download("^VIX", start=start_date, end=end_date, progress=False)
    # Handle MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        return data[("Close", "^VIX")]
    return data["Close"]
```

### 替代來源：FRED

| 系列代碼 | 名稱 | 頻率 |
|----------|------|------|
| VIXCLS | CBOE Volatility Index: VIX | 日 |

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2020-01-01&coed=2026-01-01
```

---

## CDX IG（信用利差/風險指標）

### 公開替代：FRED IG OAS

CDX IG 指數需要訂閱，公開替代使用 ICE BofA 投資級公司債利差：

| 系列代碼 | 名稱 | 說明 |
|----------|------|------|
| BAMLC0A0CM | ICE BofA US Corporate Index OAS | 全投資級公司債利差 |
| BAMLC0A4CBBB | ICE BofA BBB US Corporate Index OAS | BBB 級公司債利差 |
| BAMLH0A0HYM2 | ICE BofA US High Yield Index OAS | 高收益債利差（更敏感） |

```python
def fetch_ig_oas(start_date: str, end_date: str) -> pd.Series:
    """從 FRED 取得 IG 信用利差"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": "BAMLC0A0CM",
        "cosd": start_date,
        "coed": end_date
    }
    response = requests.get(url, params=params)
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = ["DATE", "BAMLC0A0CM"]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["BAMLC0A0CM"] = pd.to_numeric(df["BAMLC0A0CM"].replace(".", pd.NA), errors="coerce")
    df = df.dropna().set_index("DATE")
    return df["BAMLC0A0CM"]
```

---

## Chrome CDP 啟動方式

### Windows

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/35584/us-treasury-move-index"
```

### macOS

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://en.macromicro.me/charts/35584/us-treasury-move-index"
```

### 需要開啟的頁面

1. **MOVE Index**: https://en.macromicro.me/charts/35584/us-treasury-move-index
2. **JGB 10Y**: https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield

### 驗證連線

```bash
curl -s http://127.0.0.1:9222/json
```

成功回應範例：
```json
[{
   "title": "US Treasury MOVE Index",
   "url": "https://en.macromicro.me/charts/35584/us-treasury-move-index",
   "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/XXXXXX"
}]
```

---

## 數據對齊 (Data Alignment)

### 頻率處理

所有數據統一對齊到**交易日（Business Day）**：

```python
def align_to_business_days(df: pd.DataFrame) -> pd.DataFrame:
    """將數據對齊到交易日，缺值前向填充"""
    df = df.sort_index()
    df.index = pd.to_datetime(df.index)
    df = df.ffill()
    return df
```

### 時區

- FRED 數據：美東時間 (America/New_York)
- Yahoo 數據：美東時間
- MacroMicro 數據：UTC
- JGB 數據：日本時間 (Asia/Tokyo)
- 統一轉換為 **UTC** 或 **America/New_York**

### 發布延遲

| 數據 | 典型延遲 | 說明 |
|------|----------|------|
| VIX | 即時 | 交易時間即時更新 |
| MOVE | T+1 | MacroMicro 次日更新 |
| IG OAS | T+1 | FRED 次日更新 |
| JGB 10Y | T+1 | MacroMicro 次日更新 |

**實務建議**：分析時使用 T-1 日數據，模擬真實可得資訊。

---

## 快取機制

為避免重複請求，腳本內建 12 小時快取：

```python
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_MAX_AGE = timedelta(hours=12)

def is_cache_valid(key: str) -> bool:
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return (datetime.now() - mtime) < CACHE_MAX_AGE
```

使用 `--no-cache` 參數可強制重新抓取：

```bash
python fetch_data.py --start 2024-01-01 --end 2026-01-31 --no-cache
```

---

## Fallback 策略

| 主要來源 | Fallback |
|----------|----------|
| MOVE (MacroMicro CDP) | 利率實現波動率（DGS10 衍生） |
| JGB (MacroMicro CDP) | FRED 月頻數據 / 日銀公開數據 |
| VIX (Yahoo) | FRED VIXCLS |
| IG OAS (FRED) | LQD 價格反向 |

### 利率實現波動率代理（備選）

若 MacroMicro 無法連接，可使用 10Y 國債殖利率的實現波動率作為 MOVE 代理：

```python
def compute_rates_vol_proxy(dgs10: pd.Series, window: int = 21) -> pd.Series:
    """使用 10 年期國債殖利率的 21 日實現波動率作為 MOVE 代理"""
    daily_change = dgs10.diff() * 100  # 殖利率變化（bps）
    realized_vol = daily_change.rolling(window).std() * (252 ** 0.5)  # 年化
    return realized_vol
```

**注意**：實現波動率是後視（backward-looking），而 MOVE 是前瞻（forward-looking，隱含波動率）。

---

## 完整數據抓取流程

```bash
# Step 1: 啟動 Chrome CDP
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/35584/us-treasury-move-index"

# Step 2: 在 Chrome 中開啟 JGB 頁面
# https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield

# Step 3: 等待圖表載入（約 30-40 秒）

# Step 4: 執行抓取
python fetch_data.py --start 2024-01-01 --end 2026-01-31 --output data.csv
```
