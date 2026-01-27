# Workflow: 數據源研究與替代方案

<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 數據來源完整說明
</required_reading>

<process>

## Step 1: 殖利率數據來源

### 主要來源：FRED

FRED 提供免費的美國國債殖利率數據：

| 系列代碼 | 名稱                                    | 頻率 | 用途               |
|----------|-----------------------------------------|------|--------------------|
| DGS2     | 2-Year Treasury Constant Maturity Rate  | 日   | 短端殖利率（預設） |
| DGS10    | 10-Year Treasury Constant Maturity Rate | 日   | 長端殖利率（預設） |
| DGS3MO   | 3-Month Treasury Bill Secondary Market  | 日   | 極短端替代         |
| DGS30    | 30-Year Treasury Constant Maturity Rate | 日   | 超長端替代         |

**抓取方式：**
```python
import pandas as pd
import requests
from io import StringIO

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    params = {"id": series_id, "cosd": start_date, "coed": end_date}
    response = requests.get(FRED_CSV_URL, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["DATE", series_id]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df[series_id] = df[series_id].replace(".", pd.NA)
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna().set_index("DATE")
    return df[series_id]
```

### 替代來源

| 來源               | 優點           | 缺點                 |
|--------------------|----------------|----------------------|
| Yahoo Finance ^TNX | 即時更新       | 僅 10Y，需自行計算利差 |
| Treasury.gov       | 官方原始       | 需手動下載 CSV       |
| Quandl             | 多種期限       | 部分需付費           |

## Step 2: 資產價格數據來源

### 主要來源：Yahoo Finance (yfinance)

yfinance 提供免費的 ETF/股票價格數據：

**成長股代理：**
| 代號 | 名稱                  | 說明                    |
|------|-----------------------|-------------------------|
| QQQ  | Invesco QQQ Trust     | Nasdaq 100 ETF（預設）  |
| ^NDX | Nasdaq 100 Index      | 指數本身（數據可能不穩）|
| TQQQ | ProShares UltraPro QQQ| 3x 槓桿（僅供參考）     |
| IWF  | iShares Russell 1000 Growth | 更廣義成長股      |

**防禦股代理：**
| 代號 | 名稱                          | 說明                    |
|------|-------------------------------|-------------------------|
| XLV  | Health Care Select Sector SPDR| Healthcare ETF（預設）  |
| VHT  | Vanguard Health Care ETF      | 更廣泛 Healthcare       |
| IYH  | iShares U.S. Healthcare ETF   | 替代方案                |
| XLP  | Consumer Staples Select Sector| 消費必需品（另一防禦）  |

**抓取方式：**
```python
import yfinance as yf

def fetch_price_series(ticker: str, start_date: str, end_date: str, freq: str = "1wk") -> pd.Series:
    data = yf.download(ticker, start=start_date, end=end_date, interval=freq, progress=False)
    return data["Adj Close"]
```

### 替代來源

| 來源           | 優點             | 缺點               |
|----------------|------------------|--------------------|
| Alpha Vantage  | 免費 API         | 有速率限制         |
| Tiingo         | 歷史數據完整     | 需註冊             |
| Polygon.io     | 專業級數據       | 付費                |

## Step 3: 其他利差組合

除了預設的 2Y-10Y，可考慮其他組合：

| 組合      | 計算               | 特點                       |
|-----------|--------------------|----------------------------|
| 3M-10Y    | DGS10 - DGS3MO     | 最常見衰退指標             |
| 2Y-10Y    | DGS10 - DGS2       | 中期預期（本 skill 預設）  |
| 2Y-30Y    | DGS30 - DGS2       | 長期結構性預期             |
| 5Y-30Y    | DGS30 - DGS5       | 超長端斜率                 |

**注意**：不同利差組合可能有不同的最佳領先期。

## Step 4: 數據品質檢查

### 常見問題與處理

1. **缺失值**
   - FRED 使用 `.` 表示缺失
   - 處理：`df[col].replace(".", pd.NA)` + `dropna()`

2. **時區對齊**
   - FRED 為美東時間，yfinance 可能不一致
   - 處理：統一使用日期（無時間），以收盤價為準

3. **非交易日**
   - 債券市場與股票市場假日不同
   - 處理：resample 到週頻後 inner join

4. **股息調整**
   - 使用 `Adj Close` 而非 `Close`
   - 確保含股息再投資效果

### 驗證腳本

```python
def validate_data(yield_df, price_df):
    """驗證數據品質"""
    issues = []

    # 檢查缺失值
    if yield_df.isna().sum() > len(yield_df) * 0.05:
        issues.append("殖利率數據缺失超過 5%")

    if price_df.isna().sum() > len(price_df) * 0.05:
        issues.append("價格數據缺失超過 5%")

    # 檢查日期範圍
    if yield_df.index.min() > price_df.index.min():
        issues.append(f"殖利率數據起始較晚: {yield_df.index.min()}")

    # 檢查異常值
    if (yield_df > 20).any():
        issues.append("殖利率超過 20%，可能有異常值")

    if (price_df < 0).any():
        issues.append("價格為負，數據有誤")

    return issues
```

## Step 5: Fallback 策略

當主要數據源不可用時：

1. **FRED 不可用**
   - 使用 Yahoo Finance ^TNX（10Y）
   - 使用 cached 數據（若有）

2. **yfinance 不可用**
   - 使用 Alpha Vantage
   - 使用本地 CSV 備份

3. **特定 ETF 不存在**
   - QQQ 替代：^NDX 或 IWF
   - XLV 替代：VHT 或 IYH

**實作範例：**
```python
def fetch_with_fallback(primary_ticker, fallback_tickers, start_date, end_date):
    for ticker in [primary_ticker] + fallback_tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not data.empty:
                return data["Adj Close"], ticker
        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}")

    raise ValueError("All data sources failed")
```

</process>

<success_criteria>
數據研究完成時應確認：

- [ ] 了解殖利率主要與替代來源
- [ ] 了解資產價格主要與替代來源
- [ ] 了解不同利差組合選項
- [ ] 了解數據品質檢查方法
- [ ] 了解 Fallback 策略
</success_criteria>
