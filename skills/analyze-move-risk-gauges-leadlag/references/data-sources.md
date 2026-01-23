# 數據來源 (Data Sources)

本技能需要四條主要時間序列。由於部分數據（MOVE、CDX IG）需要付費訂閱，本文檔說明公開替代方案。

## 數據需求概覽

| 指標 | 原版數據 | 公開替代 | 來源 |
|------|----------|----------|------|
| MOVE | ICE BofA MOVE Index | 爬蟲取得 / 利率波動代理 | MacroMicro / Investing.com |
| VIX | CBOE VIX | yfinance `^VIX` | Yahoo Finance |
| CDX IG | Markit CDX IG Index | IG OAS (FRED) | FRED |
| JGB 10Y | Bloomberg JGB 10Y | 爬蟲取得 | Investing.com / MOF Japan |

---

## MOVE Index（利率波動率）

### 主要來源：爬蟲取得

**MacroMicro（財經 M 平方）**
```
URL: https://www.macromicro.me/charts/913/us-move-bond-market-volatility
方式: Chrome CDP 爬蟲（需登入）
頻率: 日
延遲: T+1
```

**Investing.com**
```
URL: https://www.investing.com/indices/ice-bofa-move-index
方式: Chrome CDP 爬蟲
頻率: 日
延遲: T+1
```

### 替代方案：利率實現波動率代理

若無法取得 MOVE，可使用國債殖利率的實現波動率作為代理：

```python
import pandas as pd

def compute_rates_vol_proxy(dgs10: pd.Series, window: int = 21) -> pd.Series:
    """
    使用 10 年期國債殖利率的 21 日實現波動率作為 MOVE 代理
    """
    # 殖利率變化（bps）
    daily_change = dgs10.diff() * 100
    # 21 日滾動標準差，年化
    realized_vol = daily_change.rolling(window).std() * (252 ** 0.5)
    return realized_vol
```

**注意**：實現波動率是後視（backward-looking），而 MOVE 是前瞻（forward-looking，隱含波動率）。

### FRED 數據（間接）

| 系列代碼 | 名稱 | 用途 |
|----------|------|------|
| DGS10 | 10-Year Treasury Constant Maturity Rate | 計算利率波動代理 |
| DGS2 | 2-Year Treasury Constant Maturity Rate | 短端利率波動 |

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2020-01-01&coed=2026-01-01
```

---

## VIX（股市波動率）

### 主要來源：Yahoo Finance

```python
import yfinance as yf

def fetch_vix(start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 取得 VIX"""
    data = yf.download("^VIX", start=start_date, end=end_date, progress=False)
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
    df = pd.read_csv(io.StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
    return df["BAMLC0A0CM"]
```

### LQD ETF 作為補充代理

若 FRED 數據延遲，可用 iShares IG Corporate Bond ETF (LQD) 的波動或價格作為即時代理：

```python
lqd = yf.download("LQD", start=start_date, end=end_date)["Adj Close"]
# 價格下跌 = 利差上升
lqd_spread_proxy = -lqd.pct_change()
```

---

## JGB 10Y（日本 10 年期國債殖利率）

### 主要來源：爬蟲取得

**Investing.com**
```
URL: https://www.investing.com/rates-bonds/japan-10-year-bond-yield-historical-data
方式: Chrome CDP 爬蟲
頻率: 日
延遲: T+1
```

**日本財務省（MOF Japan）**
```
URL: https://www.mof.go.jp/english/jgbs/reference/interest_rate/index.htm
方式: CSV 下載
頻率: 日
延遲: T+1
格式: Excel/CSV
```

### FRED 替代（僅月頻）

| 系列代碼 | 名稱 | 頻率 |
|----------|------|------|
| INTGSTJPM193N | Interest Rates: Long-Term Government Bond Yields: 10-Year: Main | 月 |

**注意**：月頻數據不適合做日頻的 lead/lag 分析。

### 程式碼範例：爬取 Investing.com

```python
import json
import requests
import websocket

CDP_PORT = 9222

def get_jgb_from_investing():
    """透過 CDP 從 Investing.com 爬取 JGB 10Y 殖利率"""
    # 1. 確保 Chrome 已開啟並導航到目標頁面
    # 2. 取得 WebSocket URL
    resp = requests.get(f"http://127.0.0.1:{CDP_PORT}/json")
    pages = resp.json()
    ws_url = None
    for page in pages:
        if "investing.com" in page.get("url", ""):
            ws_url = page.get("webSocketDebuggerUrl")
            break

    if not ws_url:
        raise Exception("請先在 Chrome 開啟 Investing.com JGB 頁面")

    # 3. 執行 JavaScript 提取數據
    ws = websocket.create_connection(ws_url)
    js_code = '''
    JSON.stringify([...document.querySelectorAll("table.datatable_table__D_jso tbody tr")].map(row => {
        const cells = row.querySelectorAll("td");
        return {
            date: cells[0]?.textContent?.trim(),
            price: cells[1]?.textContent?.trim(),
            open: cells[2]?.textContent?.trim(),
            high: cells[3]?.textContent?.trim(),
            low: cells[4]?.textContent?.trim(),
            change: cells[5]?.textContent?.trim()
        };
    }))
    '''
    cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": js_code, "returnByValue": True}}
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    ws.close()

    return result["result"]["result"].get("value")
```

---

## 數據對齊 (Data Alignment)

### 頻率處理

所有數據統一對齊到**交易日（Business Day）**：

```python
def align_to_business_days(df: pd.DataFrame) -> pd.DataFrame:
    """將數據對齊到交易日，缺值前向填充"""
    df = df.sort_index()
    df = df.asfreq("B")
    df = df.ffill()
    return df
```

### 時區

- FRED 數據：美東時間 (America/New_York)
- Yahoo 數據：美東時間
- JGB 數據：日本時間 (Asia/Tokyo)
- 統一轉換為 **UTC** 或 **America/New_York**

### 發布延遲

| 數據 | 典型延遲 | 說明 |
|------|----------|------|
| VIX | 即時 | 交易時間即時更新 |
| MOVE | T+1 | 收盤後發布 |
| IG OAS | T+1 | FRED 次日更新 |
| JGB 10Y | T+1 | 日本收盤後 |

**實務建議**：分析時使用 T-1 日數據，模擬真實可得資訊。

---

## 快取機制

為避免重複請求，建議使用本地快取：

```python
from pathlib import Path
from datetime import datetime, timedelta
import json

CACHE_DIR = Path("cache")
CACHE_MAX_AGE = timedelta(hours=12)

def is_cache_valid(key: str) -> bool:
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return (datetime.now() - mtime) < CACHE_MAX_AGE

def load_cache(key: str):
    if is_cache_valid(key):
        with open(CACHE_DIR / f"{key}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(key: str, data):
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_DIR / f"{key}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
```

---

## Fallback 策略

| 主要來源 | Fallback 1 | Fallback 2 |
|----------|------------|------------|
| MOVE (爬蟲) | 利率實現波動率 | 國債期貨隱含波動 |
| VIX (Yahoo) | FRED VIXCLS | VIX 期貨 (/VX) |
| IG OAS (FRED) | LQD 價格反向 | HYG/LQD 比率 |
| JGB (爬蟲) | FRED 月頻數據 | 日銀公開數據 |

---

## 程式碼範例：完整數據抓取

```python
import pandas as pd
import yfinance as yf
import requests
from io import StringIO
from pathlib import Path

def fetch_all_data(start_date: str, end_date: str) -> pd.DataFrame:
    """抓取所有需要的數據"""

    # 1. VIX from Yahoo
    vix = yf.download("^VIX", start=start_date, end=end_date, progress=False)["Close"]
    vix.name = "VIX"

    # 2. IG OAS from FRED
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {"id": "BAMLC0A0CM", "cosd": start_date, "coed": end_date}
    resp = requests.get(url, params=params)
    ig_oas = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
    ig_oas = ig_oas["BAMLC0A0CM"]
    ig_oas.name = "CREDIT"

    # 3. DGS10 for rates vol proxy
    params = {"id": "DGS10", "cosd": start_date, "coed": end_date}
    resp = requests.get(url, params=params)
    dgs10 = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
    dgs10 = dgs10["DGS10"]

    # Compute rates vol proxy
    move_proxy = (dgs10.diff() * 100).rolling(21).std() * (252 ** 0.5)
    move_proxy.name = "MOVE"

    # 4. JGB placeholder (需爬蟲或手動輸入)
    # jgb = fetch_jgb_from_investing(start_date, end_date)

    # Combine
    df = pd.concat([move_proxy, vix, ig_oas], axis=1)
    df = df.sort_index().asfreq("B").ffill()

    return df
```
