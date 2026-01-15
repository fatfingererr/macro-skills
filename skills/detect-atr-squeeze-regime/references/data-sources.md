# 資料來源說明

## 主要資料來源

### Yahoo Finance（推薦）

**優點**：
- 免費，無需 API key
- 使用 `yfinance` 套件直接抓取
- 覆蓋全球主要市場

**支援的資產類型**：

| 類型 | 格式 | 範例 |
|------|------|------|
| 期貨 | XXX=F | SI=F（白銀）, GC=F（黃金）, CL=F（原油） |
| 股票 | TICKER | AAPL, TSLA, SPY |
| 指數 | ^XXX | ^GSPC（S&P 500）, ^VIX |
| ETF | TICKER | GLD, SLV, USO |

**常用期貨代碼**：

| 資產 | 代碼 | 說明 |
|------|------|------|
| 白銀 | SI=F | COMEX 白銀期貨 |
| 黃金 | GC=F | COMEX 黃金期貨 |
| 原油 | CL=F | WTI 原油期貨 |
| 天然氣 | NG=F | Henry Hub 天然氣期貨 |
| 銅 | HG=F | COMEX 銅期貨 |
| 玉米 | ZC=F | CBOT 玉米期貨 |
| 小麥 | ZW=F | CBOT 小麥期貨 |
| 大豆 | ZS=F | CBOT 大豆期貨 |
| E-mini S&P | ES=F | CME E-mini S&P 500 |
| Nasdaq 100 | NQ=F | CME E-mini Nasdaq 100 |

**使用方式**：

```python
import yfinance as yf

# 下載數據
ticker = yf.Ticker("SI=F")
df = ticker.history(start="2020-01-01", end="2026-01-01")

# 必要欄位
# - High, Low, Close（用於 ATR 計算）
# - Open（可選）
# - Volume（可選）
```

**注意事項**：
- 期貨數據為連續合約（自動換月）
- 部分冷門期貨可能數據不完整
- 小時線數據僅保留近期

---

## 替代資料來源

### Stooq

**網址**：https://stooq.com

**優點**：
- 免費
- 長期歷史數據
- 覆蓋外匯、貴金屬現貨

**支援的資產類型**：

| 類型 | 格式 | 範例 |
|------|------|------|
| 外匯 | XXXYYY | EURUSD, USDJPY |
| 貴金屬現貨 | XAUXXX | XAUUSD（黃金）, XAGUSD（白銀） |
| 指數 | ^XXX | ^SPX, ^DJI |

**下載方式**：

```python
import pandas as pd

# 直接下載 CSV
url = "https://stooq.com/q/d/l/?s=xagusd&d1=20200101&d2=20260101&i=d"
df = pd.read_csv(url)

# 欄位：Date, Open, High, Low, Close, Volume
```

**注意事項**：
- 需要處理日期格式
- 部分資產可能有缺失值
- 下載頻率有限制（防爬蟲）

---

### Alpha Vantage

**網址**：https://www.alphavantage.co

**優點**：
- 免費 tier 可用
- API 穩定
- 支援即時數據

**限制**：
- 免費版每分鐘 5 次請求
- 每日 500 次請求上限
- 需要 API key

**使用方式**：

```python
import requests

API_KEY = "YOUR_API_KEY"
symbol = "SILVER"  # 不同於 yfinance 的符號
url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=full"

response = requests.get(url)
data = response.json()
```

---

### Twelve Data

**網址**：https://twelvedata.com

**優點**：
- 覆蓋範圍廣
- 支援技術指標 API
- 免費版可用

**限制**：
- 免費版每分鐘 8 次請求
- 歷史數據深度有限

---

## 數據需求

### 必要欄位

| 欄位 | 用途 |
|------|------|
| High | True Range 計算 |
| Low | True Range 計算 |
| Close | True Range 計算、ATR% 計算 |

### 可選欄位

| 欄位 | 用途 |
|------|------|
| Open | 視覺化、進階分析 |
| Volume | 流動性分析（未來擴展） |

### 數據頻率

| 頻率 | 建議場景 |
|------|----------|
| 日線（1d） | 預設，適合大多數分析 |
| 小時線（1h） | 更細粒度分析，但歷史深度有限 |

### 數據長度

| 長度 | 用途 |
|------|------|
| 3 年 | 建立有效基準（baseline_window_days = 756） |
| 5 年 | 涵蓋更多週期，更穩定的基準 |
| 10 年 | 長期回測 |

**建議**：至少取 5 年數據，前 3 年用於建立基準，後 2 年用於有效分析。

---

## 資料來源選擇建議

| 資產類型 | 建議來源 | 備註 |
|----------|----------|------|
| 期貨（美國） | Yahoo Finance | SI=F, GC=F, CL=F 等 |
| 貴金屬現貨 | Stooq | XAUUSD, XAGUSD |
| 外匯 | Stooq 或 Alpha Vantage | 視可用性 |
| 美股/ETF | Yahoo Finance | SPY, GLD, SLV |
| 國際指數 | Yahoo Finance | ^N225, ^FTSE |

---

## 錯誤處理

### 常見問題

1. **Symbol 無效**
   - 檢查格式是否正確
   - 嘗試替代符號（如 SI=F vs SILVER）

2. **數據缺失**
   - 檢查日期範圍
   - 嘗試替代資料來源

3. **下載失敗**
   - 檢查網路連接
   - 等待後重試（可能觸發限流）

4. **數據不足**
   - 減少 baseline_window_days
   - 或取更長期的數據

### 建議的錯誤處理流程

```python
def fetch_data(symbol, start, end):
    try:
        # 嘗試 yfinance
        df = yf.Ticker(symbol).history(start=start, end=end)
        if len(df) > 0:
            return df
    except Exception as e:
        print(f"yfinance failed: {e}")

    try:
        # 嘗試 Stooq
        url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&d1={start.replace('-','')}&d2={end.replace('-','')}&i=d"
        df = pd.read_csv(url)
        if len(df) > 0:
            return df
    except Exception as e:
        print(f"Stooq failed: {e}")

    raise ValueError(f"Cannot fetch data for {symbol}")
```
