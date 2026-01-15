# 數據來源 (Data Sources)

本技能使用**無需 API key** 的公開數據來源。

## FRED (Federal Reserve Economic Data)

**存取方式**：CSV endpoint（無需 API key）
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}&cosd={START_DATE}&coed={END_DATE}
```

### 領先指標 (Leading Indicators)

| 系列代碼 | 名稱 | 說明 | 頻率 | 領先時間 |
|----------|------|------|------|----------|
| T10Y3M | 10-Year Treasury Constant Maturity Minus 3-Month | 殖利率曲線（10年-3月） | 日 | 12-18 月 |
| T10Y2Y | 10-Year Treasury Constant Maturity Minus 2-Year | 殖利率曲線（10年-2年） | 日 | 12-18 月 |
| PERMIT | New Privately-Owned Housing Units Authorized | 建築許可（房市領先） | 月 | 6-12 月 |
| ACDGNO | Value of Manufacturers' New Orders: Durable Goods | 耐久財新訂單 | 月 | 3-6 月 |
| UMCSENT | University of Michigan: Consumer Sentiment | 消費者信心指數 | 月 | 3-6 月 |
| HOUST | Housing Starts | 新屋開工 | 月 | 6-12 月 |
| NEWORDER | Manufacturers' New Orders: Nondefense Capital Goods | 非國防資本財訂單 | 月 | 3-6 月 |

### 同時指標 (Coincident Indicators)

| 系列代碼 | 名稱 | 說明 | 頻率 |
|----------|------|------|------|
| PAYEMS | All Employees, Total Nonfarm | 非農就業 | 月 |
| INDPRO | Industrial Production Index | 工業生產指數 | 月 |
| W875RX1 | Real Personal Income Excluding Current Transfer Receipts | 實質個人所得（排除轉移支付） | 月 |
| CMRMTSPL | Real Manufacturing and Trade Industries Sales | 實質製造與貿易銷售 | 月 |
| UNRATE | Unemployment Rate | 失業率（方向相反） | 月 |

### 風險濾鏡指標 (Risk Filter Indicators)

| 系列代碼 | 名稱 | 說明 | 用途 |
|----------|------|------|------|
| BAA10Y | Moody's Baa Corporate Bond Yield Relative to 10-Year Treasury | Baa 信用利差 | Euphoria filter |
| AAA10Y | Moody's Aaa Corporate Bond Yield Relative to 10-Year Treasury | Aaa 信用利差 | Euphoria filter |
| VIXCLS | CBOE Volatility Index (VIX) | VIX 波動率指數 | Euphoria filter |
| BAMLH0A0HYM2 | ICE BofA US High Yield Index Option-Adjusted Spread | 高收益債利差 | Euphoria filter |

## Yahoo Finance

**存取方式**：`yfinance` Python 套件

### 價格資產 (Price Assets)

| Ticker | 名稱 | 說明 | 用途 |
|--------|------|------|------|
| SPY | SPDR S&P 500 ETF | S&P 500 指數 ETF | Risk-On 資產 |
| TLT | iShares 20+ Year Treasury Bond ETF | 20年以上國債 ETF | Risk-Off 資產 |
| ^GSPC | S&P 500 Index | S&P 500 指數 | 替代 SPY |
| ^VIX | CBOE Volatility Index | VIX 指數 | 風險濾鏡 |

### 價格數據說明

- 使用 **Adjusted Close** 價格（含配息再投資）
- 月頻數據取**月末收盤價**
- TLT 從 2002 年開始有數據，之前需用 FRED 長債指數替代

## 數據對齊 (Data Alignment)

### 頻率對齊

所有數據統一對齊到**月頻（M）**：
- 日頻數據：取月末值或月均值
- 月頻數據：直接使用
- 價格數據：取月末收盤價

### 時區與日期

- FRED 數據以美東時間為準
- Yahoo 數據以美東時間為準
- 統一使用 **UTC** 或 **America/New_York**

### 發布延遲 (Publication Lag)

| 數據類型 | 典型延遲 | 說明 |
|----------|----------|------|
| 殖利率曲線 | 1 日 | 即時性高 |
| 工業生產 | 15 天 | 月中發布上月數據 |
| 就業數據 | 5 天 | 月初發布上月數據 |
| 建築許可 | 18 天 | 月中發布上月數據 |
| 消費者信心 | 立即 | 調查完成即發布 |

**實務建議**：回測時使用 `T-1` 或 `T-2` 月數據，模擬真實可得資訊。

## 替代數據 (Alternative Data Sources)

若主要數據不可用，可使用以下替代：

| 主要 | 替代 | 說明 |
|------|------|------|
| SPY | ^GSPC, VOO | S&P 500 替代 |
| TLT | VGLT, FRED:DGS20 | 長債替代 |
| T10Y3M | 手動計算 DGS10 - DGS3MO | 殖利率曲線替代 |

## FRED API 程式碼範例

```python
import pandas as pd
import requests

def fetch_fred_series(series_id, start_date, end_date):
    """從 FRED 抓取時間序列（無需 API key）"""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    from io import StringIO
    df = pd.read_csv(StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
    df.columns = [series_id]
    return df

# 範例：抓取殖利率曲線
yield_curve = fetch_fred_series("T10Y3M", "2000-01-01", "2026-01-01")
```

## yfinance 程式碼範例

```python
import yfinance as yf
import pandas as pd

def fetch_yahoo_prices(ticker, start_date, end_date):
    """從 Yahoo Finance 抓取價格數據"""
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    return data["Adj Close"]

# 範例：抓取 SPY 和 TLT
spy = fetch_yahoo_prices("SPY", "2000-01-01", "2026-01-01")
tlt = fetch_yahoo_prices("TLT", "2002-07-01", "2026-01-01")
```
