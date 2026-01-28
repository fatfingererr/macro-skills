# 數據來源與 Chrome CDP 爬蟲說明

<overview>
此參考文件列出天然氣與化肥價格分析所需的資料來源。

**主要來源**：TradingEconomics（透過 Chrome CDP 爬取）
**備援來源**：FRED（天然氣）、World Bank Pink Sheet（化肥）

**爬取方法**：Chrome CDP（繞過 Cloudflare，完全模擬真人瀏覽）
</overview>

---

## 1. TradingEconomics 商品頁面

### 天然氣

| 商品 | URL | Slug |
|------|-----|------|
| Natural Gas | https://tradingeconomics.com/commodity/natural-gas | `natural-gas` |
| EU Natural Gas | https://tradingeconomics.com/commodity/eu-natural-gas | `eu-natural-gas` |
| UK Natural Gas | https://tradingeconomics.com/commodity/uk-natural-gas | `uk-natural-gas` |

### 化肥

| 商品 | URL | Slug |
|------|-----|------|
| Urea | https://tradingeconomics.com/commodity/urea | `urea` |
| DAP | https://tradingeconomics.com/commodity/dap | `dap` |
| Fertilizers Index | https://tradingeconomics.com/commodity/fertilizers | `fertilizers` |

---

## 2. Chrome CDP 爬取方法

### 2.1 核心原理

透過 Chrome DevTools Protocol (CDP) 連接到**你自己開啟的 Chrome 瀏覽器**，完全繞過 Cloudflare。這個方法對網站來說就是「真人在用瀏覽器」。

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  Python Script  │ ◄────────────────► │  Chrome Browser │
│  (CDP Client)   │    Port 9222       │  (你的 Profile) │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │ Runtime.evaluate()                   │
        ▼                                      ▼
   執行 JavaScript ──────────────────► 提取 Highcharts 數據
```

### 2.2 前置準備

```bash
pip install requests websocket-client pandas numpy
```

建立專用的 Chrome profile 目錄（只需執行一次）：

```bash
# Windows
mkdir "%USERPROFILE%\.chrome-debug-profile"

# macOS / Linux
mkdir -p ~/.chrome-debug-profile
```

### 2.3 操作流程

**Step 1：關閉所有 Chrome 視窗**

確保沒有其他 Chrome 實例在執行，否則調試端口會無法啟動。

**Step 2：啟動 Chrome（帶調試端口）**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://tradingeconomics.com/commodity/natural-gas"
```

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$HOME/.chrome-debug-profile" \
  "https://tradingeconomics.com/commodity/natural-gas"
```

**Step 3：等待頁面完全載入**（圖表顯示）

如果遇到 Cloudflare 驗證，手動完成驗證即可。

**Step 4：驗證連線**

```bash
curl -s http://127.0.0.1:9222/json
```

成功的回應範例：
```json
[{
   "title": "Natural Gas | 2025 Data...",
   "url": "https://tradingeconomics.com/commodity/natural-gas",
   "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/XXXXXX"
}]
```

**Step 5：執行爬蟲腳本**

```bash
cd scripts
python fetch_te_data.py --symbol natural-gas
```

### 2.4 關鍵參數說明

| 參數 | 說明 |
|------|------|
| `--remote-debugging-port=9222` | 開啟 CDP 調試端口（可改用其他端口） |
| `--remote-allow-origins=*` | 允許所有來源連線（**必要**，否則 WebSocket 會被拒絕） |
| `--user-data-dir=<path>` | 指定 profile 目錄（**必須是非預設目錄**） |

---

## 3. Highcharts 數據提取

TradingEconomics 使用 Highcharts 渲染圖表，數據存儲在全域 `Highcharts.charts` 陣列中。

### 提取 JavaScript

```javascript
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found'});
    }

    var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
    var result = [];

    for (var i = 0; i < charts.length; i++) {
        var chart = charts[i];
        var chartInfo = {
            title: chart.title ? chart.title.textStr : 'Chart ' + i,
            series: []
        };

        for (var j = 0; j < chart.series.length; j++) {
            var s = chart.series[j];
            var seriesData = [];

            if (s.xData && s.xData.length > 0) {
                for (var k = 0; k < s.xData.length; k++) {
                    if (s.yData[k] !== null) {
                        seriesData.push({
                            x: s.xData[k],
                            y: s.yData[k],
                            date: new Date(s.xData[k]).toISOString().split('T')[0]
                        });
                    }
                }
            }

            if (seriesData.length > 0) {
                chartInfo.series.push({
                    name: s.name,
                    dataLength: seriesData.length,
                    data: seriesData
                });
            }
        }
        result.push(chartInfo);
    }
    return JSON.stringify(result);
})()
```

---

## 4. 抓取多個商品

### 方法一：手動切換頁面

1. 在 Chrome 中抓完 natural-gas 後
2. 在同一分頁切換到 urea 頁面
3. 等待頁面載入後執行第二次爬蟲

```bash
python fetch_te_data.py --symbol natural-gas
# 在 Chrome 中切換到 urea 頁面
python fetch_te_data.py --symbol urea
```

### 方法二：開啟新分頁（CDP 指令）

```python
import requests

# 開啟新分頁
requests.get('http://127.0.0.1:9222/json/new?https://tradingeconomics.com/commodity/urea')

# 等待頁面載入後執行爬蟲
```

---

## 5. 備援數據源

### 5.1 FRED（天然氣）

若 TradingEconomics 不可用，使用 FRED Henry Hub：

```python
import pandas as pd
import requests
from io import StringIO

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_henry_hub(start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取 Henry Hub 天然氣價格

    Parameters
    ----------
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)
    """
    params = {
        "id": "DHHNGSP",  # Daily Henry Hub Natural Gas Spot Price
        "cosd": start_date,
        "coed": end_date
    }
    response = requests.get(FRED_CSV_URL, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["DATE", "DHHNGSP"]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["DHHNGSP"] = df["DHHNGSP"].replace(".", pd.NA)
    df["DHHNGSP"] = pd.to_numeric(df["DHHNGSP"], errors="coerce")
    df = df.dropna()

    return df.set_index("DATE")["DHHNGSP"]
```

### 5.2 World Bank Pink Sheet（化肥）

月頻數據，需手動下載：

- URL: https://www.worldbank.org/en/research/commodity-markets
- 檔案: CMO-Historical-Data-Monthly.xlsx
- 相關欄位: Urea, DAP, TSP

```python
# 讀取 World Bank 數據
import pandas as pd

wb_df = pd.read_excel(
    "CMO-Historical-Data-Monthly.xlsx",
    sheet_name="Monthly Prices"
)
urea = wb_df[["Date", "Urea"]].dropna()
```

---

## 6. 快取策略

| 參數 | 值 | 說明 |
|------|-----|------|
| 快取目錄 | `./data/cache` | 預設 |
| 最大有效期 | 12 小時 | 日頻數據，每日更新一次足夠 |
| 快取檔案 | `{symbol}_raw.json` | 原始 Highcharts 數據 |
| CSV 檔案 | `{symbol}.csv` | 提取後的價格序列 |

```python
from pathlib import Path
from datetime import datetime, timedelta
import json

CACHE_DIR = Path("data/cache")
CACHE_MAX_AGE_HOURS = 12

def is_cache_valid(symbol: str) -> bool:
    cache_file = CACHE_DIR / f"{symbol}_raw.json"
    if cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=CACHE_MAX_AGE_HOURS)
    return False
```

---

## 7. 數據單位與對齊

### 單位

| 商品 | 單位 | 說明 |
|------|------|------|
| Natural Gas | USD/MMBtu | 百萬英熱單位 |
| EU Natural Gas | EUR/MWh | 兆瓦時 |
| Urea | USD/ton | 噸 |
| DAP | USD/ton | 噸 |

### 對齊方法

```python
def align_daily(gas_df: pd.DataFrame, fert_df: pd.DataFrame) -> pd.DataFrame:
    """對齊兩個日頻序列"""
    merged = gas_df.merge(fert_df, left_index=True, right_index=True, how="outer")
    merged = merged.sort_index()
    merged = merged.ffill()  # forward-fill 缺值
    return merged.dropna()
```

---

## 8. 常見問題排解

### Q1: 無法連接到 Chrome 調試端口

1. 確保所有 Chrome 視窗都已關閉
2. 確認使用了非預設的 `--user-data-dir`
3. 檢查端口 9222：
   ```bash
   curl -s http://127.0.0.1:9222/json
   ```

### Q2: WebSocket 連線被拒絕 (403 Forbidden)

確認啟動 Chrome 時有加上 `--remote-allow-origins=*` 參數。

### Q3: Highcharts not found

1. 確認頁面已完全載入（圖表已顯示）
2. 在瀏覽器 Console 中執行 `typeof Highcharts` 確認
3. 頁面可能仍在載入，等待幾秒後再試

### Q4: 被 Cloudflare 擋住

1. 在 Chrome 中手動完成 Cloudflare 驗證
2. 登入 TradingEconomics 帳號後再執行
3. 使用你平常用的 Chrome profile（複製 cookies）

### Q5: 數據與其他來源不一致

1. 確認是否為同一合約（現貨 vs 期貨）
2. 確認時區（TradingEconomics 可能為 UTC）
3. 確認是否為日頻（非盤中價）

---

## 9. 腳本參考

| 腳本 | 功能 | 說明 |
|------|------|------|
| `scripts/fetch_te_data.py` | TradingEconomics CDP 爬蟲 | 主要爬蟲腳本 |
| `scripts/gas_fertilizer_analyzer.py` | 完整分析 | 含 FRED 備援 |
| `scripts/visualize_shock_regimes.py` | 視覺化 | 生成對比圖 |

```bash
# 抓取天然氣
python fetch_te_data.py --symbol natural-gas

# 抓取化肥（先在 Chrome 切換到化肥頁面）
python fetch_te_data.py --symbol urea

# 指定輸出路徑
python fetch_te_data.py --symbol natural-gas --output ../data/gas.csv

# 強制重新抓取（忽略快取）
python fetch_te_data.py --symbol urea --force-refresh
```

---

## 10. 相關指南

- [Chrome CDP 數據爬取 SOP](../../../thoughts/shared/guide/chrome-cdp-scraping-sop.md)
