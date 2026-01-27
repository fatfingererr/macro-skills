# 數據來源與獲取方式

本文件說明技能所需數據的來源、獲取方式、注意事項與替代方案。

---

## 1. 殖利率數據

### 主要來源：FRED（Federal Reserve Economic Data）

| 項目       | 說明                                                 |
|------------|------------------------------------------------------|
| 提供者     | Federal Reserve Bank of St. Louis                    |
| 網址       | https://fred.stlouisfed.org                          |
| 費用       | 免費                                                 |
| API        | 免費 CSV API，無需 API Key                           |
| 更新頻率   | 每日（T+1，美東時間下午更新）                        |
| 歷史深度   | 大部分系列自 1962 年起                               |

**常用系列代碼：**

| 代碼    | 名稱                                    | 期限 | 起始日期   |
|---------|-----------------------------------------|------|------------|
| DGS3MO  | 3-Month Treasury Bill Secondary Market  | 3M   | 1982-01-04 |
| DGS1    | 1-Year Treasury Constant Maturity Rate  | 1Y   | 1962-01-02 |
| DGS2    | 2-Year Treasury Constant Maturity Rate  | 2Y   | 1976-06-01 |
| DGS5    | 5-Year Treasury Constant Maturity Rate  | 5Y   | 1962-01-02 |
| DGS7    | 7-Year Treasury Constant Maturity Rate  | 7Y   | 1969-07-01 |
| DGS10   | 10-Year Treasury Constant Maturity Rate | 10Y  | 1962-01-02 |
| DGS30   | 30-Year Treasury Constant Maturity Rate | 30Y  | 1977-02-15 |

**獲取方式：**

```python
import pandas as pd
import requests
from io import StringIO

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Parameters:
    -----------
    series_id : str
        FRED 系列代碼 (e.g., "DGS10", "DGS2")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns:
    --------
    pd.Series
        時間序列數據，index 為 DatetimeIndex
    """
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        # 健壯的 CSV 解析方式
        df = pd.read_csv(StringIO(response.text))

        # FRED CSV 格式：第一列是日期，第二列是數值
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])

        # 處理缺失值（FRED 使用 '.' 表示缺失）
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        df = df.dropna()
        df = df.set_index("DATE")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)
```

**注意事項：**
- FRED 使用 `.` 表示缺失值，需特別處理
- 假日（非交易日）無數據，需考慮對齊
- 時區為美東時間

### 替代來源

| 來源           | 優點             | 缺點                 | 適用場景       |
|----------------|------------------|----------------------|----------------|
| Yahoo Finance  | 即時更新         | 僅提供 ^TNX (10Y)    | 快速驗證       |
| Treasury.gov   | 官方原始數據     | 需手動下載 CSV       | 高精度需求     |
| Quandl/Nasdaq  | API 友善         | 部分需付費           | 自動化系統     |

---

## 2. 資產價格數據

### 主要來源：Yahoo Finance (via yfinance)

| 項目       | 說明                                    |
|------------|-----------------------------------------|
| 提供者     | Yahoo Finance                           |
| 網址       | https://finance.yahoo.com               |
| 費用       | 免費                                    |
| Python 套件| yfinance                                |
| 更新頻率   | 盤中即時（有延遲）                      |
| 歷史深度   | 視標的而定，ETF 通常自成立日起          |

**預設標的：**

| 代碼 | 名稱                           | 類型     | 成立日期   |
|------|--------------------------------|----------|------------|
| QQQ  | Invesco QQQ Trust              | 成長股   | 1999-03-10 |
| XLV  | Health Care Select Sector SPDR | 防禦股   | 1998-12-16 |

**替代標的：**

| 類型   | 代碼 | 名稱                          | 說明                    |
|--------|------|-------------------------------|-------------------------|
| 成長股 | ^NDX | Nasdaq 100 Index              | 指數本身（非 ETF）      |
| 成長股 | IWF  | iShares Russell 1000 Growth   | 更廣義成長股            |
| 成長股 | VUG  | Vanguard Growth ETF           | 低成本成長股 ETF        |
| 防禦股 | VHT  | Vanguard Health Care ETF      | 更廣泛 Healthcare       |
| 防禦股 | IYH  | iShares U.S. Healthcare ETF   | 另一 Healthcare ETF     |
| 防禦股 | XLP  | Consumer Staples Select Sector| 消費必需品（另一防禦）  |

**獲取方式：**

```python
import yfinance as yf
import pandas as pd

def fetch_price_series(
    ticker: str,
    start_date: str,
    end_date: str,
    freq: str = "1wk"
) -> pd.Series:
    """
    從 Yahoo Finance 抓取調整後收盤價

    Parameters:
    -----------
    ticker : str
        股票/ETF 代碼 (e.g., "QQQ", "XLV")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)
    freq : str
        頻率 ("1d", "1wk", "1mo")

    Returns:
    --------
    pd.Series
        調整後收盤價序列
    """
    try:
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=freq,
            progress=False
        )

        if data.empty:
            print(f"No data returned for {ticker}")
            return pd.Series(dtype=float)

        # 使用調整後收盤價（含股息、拆分）
        return data["Adj Close"]

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.Series(dtype=float)
```

**注意事項：**
- 使用 `Adj Close`（調整後收盤價）而非 `Close`
- yfinance 偶爾會有 API 問題，建議加入重試機制
- 不同 ETF 的交易時間可能略有差異

### 替代來源

| 來源          | 優點               | 缺點               | 適用場景       |
|---------------|--------------------|--------------------|----------------|
| Alpha Vantage | 免費 API           | 速率限制嚴格       | 低頻需求       |
| Tiingo        | 歷史數據完整       | 需註冊取得 API Key | 研究需求       |
| Polygon.io    | 專業級數據品質     | 付費               | 生產系統       |

---

## 3. 數據對齊

### 頻率對齊

殖利率（日頻）與價格（日/週/月頻）需對齊：

```python
def align_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """將數據對齊到週五收盤"""
    return df.resample("W-FRI").last().dropna()
```

### 日期對齊

```python
def align_data(yield_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """對齊殖利率與價格數據"""
    # Inner join 確保兩邊都有值
    aligned = yield_df.join(price_df, how="inner")
    return aligned.dropna()
```

### 處理缺失值

| 策略           | 說明                   | 適用場景           |
|----------------|------------------------|--------------------|
| dropna         | 刪除缺失               | 預設，最保守       |
| ffill          | 向前填充               | 假日數據延續       |
| interpolate    | 線性插值               | 短期缺失           |

---

## 4. 快取策略

建議對 FRED 與 yfinance 數據實作快取：

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("cache")

def save_cache(key: str, df: pd.DataFrame, ttl_hours: int = 24):
    """儲存快取"""
    CACHE_DIR.mkdir(exist_ok=True)

    df_to_save = df.copy()
    if df_to_save.index.name is None:
        df_to_save.index.name = "DATE"

    data = df_to_save.reset_index().to_dict(orient="records")

    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({
            "cached_at": datetime.now().isoformat(),
            "ttl_hours": ttl_hours,
            "data": data
        }, f, default=str)


def load_cache(key: str) -> pd.DataFrame | None:
    """載入快取（若有效）"""
    cache_file = CACHE_DIR / f"{key}.json"

    if not cache_file.exists():
        return None

    with open(cache_file, "r", encoding="utf-8") as f:
        cached = json.load(f)

    cached_at = datetime.fromisoformat(cached["cached_at"])
    ttl_hours = cached.get("ttl_hours", 24)

    if datetime.now() - cached_at > timedelta(hours=ttl_hours):
        return None  # 快取過期

    df = pd.DataFrame(cached["data"])
    first_col = df.columns[0]
    df[first_col] = pd.to_datetime(df[first_col])
    df = df.set_index(first_col)

    return df
```

---

## 5. 錯誤處理與 Fallback

```python
def fetch_with_fallback(
    primary_source: callable,
    fallback_source: callable,
    *args, **kwargs
) -> pd.Series:
    """帶 fallback 的數據抓取"""
    try:
        data = primary_source(*args, **kwargs)
        if not data.empty:
            return data
    except Exception as e:
        print(f"Primary source failed: {e}")

    try:
        data = fallback_source(*args, **kwargs)
        if not data.empty:
            print("Using fallback source")
            return data
    except Exception as e:
        print(f"Fallback source failed: {e}")

    raise ValueError("All data sources failed")
```

---

## 6. 數據品質檢查清單

執行分析前應確認：

- [ ] 殖利率數據無異常值（如 > 20%）
- [ ] 價格數據無負值
- [ ] 兩邊日期範圍足夠（> lookback_years）
- [ ] 缺失值比例 < 5%
- [ ] 對齊後數據點數量足夠（> 100 週）
