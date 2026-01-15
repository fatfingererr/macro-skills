# 數據來源說明

本文件說明 evaluate-exponential-trend-deviation-regimes 技能使用的數據來源。

## 資產價格

### 首選：Yahoo Finance（yfinance）

適用於幾乎所有資產類型：股票、期貨、ETF、指數、加密貨幣等。

| 項目 | 說明 |
|------|------|
| API | `yfinance.Ticker(symbol).history()` |
| 費用 | 免費，無需 API key |
| 頻率 | 日頻（可轉換為月頻） |

```python
import yfinance as yf
import pandas as pd

def fetch_asset_yahoo(symbol: str, start: str, end: str) -> pd.DataFrame:
    """從 Yahoo Finance 下載資產價格"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    return df[["Close"]].rename(columns={"Close": "price"})
```

**支援的資產範例**：

| 資產類型 | 代碼範例 | 歷史數據長度 |
|----------|----------|--------------|
| 黃金期貨 | GC=F | ~2000 年起 |
| 白銀期貨 | SI=F | ~2000 年起 |
| 原油期貨 | CL=F | ~1983 年起 |
| S&P 500 | ^GSPC | ~1950 年起 |
| 納斯達克 | ^IXIC | ~1971 年起 |
| 比特幣 | BTC-USD | ~2014 年起 |
| 以太坊 | ETH-USD | ~2017 年起 |
| 黃金 ETF | GLD | ~2004 年起 |

### 替代：Stooq（黃金長期分析推薦）

適用於需要更長歷史數據的情況。**黃金完整歷史分析（1970+）建議使用 Stooq**。

| 項目 | 說明 |
|------|------|
| API | CSV 下載 |
| 費用 | 免費 |
| 歷史 | 部分資產可達 1970 年代 |

**黃金專用**：使用 `xauusd` 符號可取得 1970 年起的月頻數據：

```python
url = 'https://stooq.com/q/d/l/?s=xauusd&d1=19700101&d2=20260115&i=m'
gold = pd.read_csv(url)
```

```python
import pandas as pd

def fetch_asset_stooq(symbol: str, start: str, end: str) -> pd.DataFrame:
    """從 Stooq 下載資產價格"""
    # Stooq 使用不同的符號格式，需要轉換
    stooq_symbol = symbol.replace("^", "").lower()
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&d1={start.replace('-','')}&d2={end.replace('-','')}&i=d"
    df = pd.read_csv(url)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df[["Close"]].rename(columns={"Close": "price"})
```

### 特殊數據來源

**黃金長期歷史數據**（1970 年前）：

| 來源 | 說明 |
|------|------|
| FRED | GOLDAMGBD228NLBM（倫敦黃金定盤價） |
| World Gold Council | 歷史黃金價格 |

**股票指數長期數據**：

| 來源 | 說明 |
|------|------|
| Robert Shiller's Data | S&P 500 自 1871 年起 |
| Kenneth French Data Library | 各類因子與指數 |

## 宏觀代理指標

### FRED（Federal Reserve Economic Data）

使用 `pandas-datareader` 套件存取。

#### 實質利率

| 代碼 | 名稱 | 說明 |
|------|------|------|
| DFII10 | 10-Year TIPS | 10 年期 TIPS 收益率（實質利率代理） |
| REAINTRATREARAT10Y | 10-Year Real Interest Rate | 替代指標 |

```python
import pandas_datareader as pdr

def fetch_real_rate(start: str, end: str) -> pd.Series:
    """從 FRED 下載實質利率"""
    df = pdr.DataReader("DFII10", "fred", start, end)
    return df["DFII10"]
```

#### 通膨預期

| 代碼 | 名稱 | 說明 |
|------|------|------|
| T5YIE | 5-Year Breakeven | 5 年期損益平衡通膨率 |
| T10YIE | 10-Year Breakeven | 10 年期損益平衡通膨率 |
| T5YIFR | 5-Year, 5-Year Forward | 5y5y 遠期通膨預期 |

```python
def fetch_inflation_expectation(start: str, end: str) -> pd.Series:
    """從 FRED 下載通膨預期"""
    df = pdr.DataReader("T5YIE", "fred", start, end)
    return df["T5YIE"]
```

#### 美元指數

| 代碼 | 名稱 | 說明 |
|------|------|------|
| DTWEXBGS | Trade Weighted USD | 貿易加權美元指數（廣義） |
| DTWEXAFEGS | Trade Weighted USD (AFE) | 貿易加權美元（先進經濟體） |

```python
def fetch_usd_index(start: str, end: str) -> pd.Series:
    """從 FRED 下載美元指數"""
    df = pdr.DataReader("DTWEXBGS", "fred", start, end)
    return df["DTWEXBGS"]
```

### 地緣政治風險

#### GPR Index（首選但不公開）

Caldara-Iacoviello Geopolitical Risk Index

- 官網：https://www.matteoiacoviello.com/gpr.htm
- 需手動下載或申請 API

#### 新聞關鍵詞計數（替代）

使用 GDELT 或其他新聞 API 計算關鍵詞出現次數。

```python
def estimate_geopolitical_risk(lookback_days: int = 30) -> float:
    """
    估算地緣政治風險（使用新聞關鍵詞）

    Returns:
        0-100 的風險分數
    """
    keywords = ["war", "conflict", "sanction", "military", "tension", "crisis"]
    # 實作：使用新聞 API 計算關鍵詞頻率
    # 此處為示意，實際需接入新聞 API
    return 50.0  # placeholder
```

## 數據頻率轉換

### 日頻轉月頻

```python
def to_monthly(daily_data: pd.Series) -> pd.Series:
    """將日頻數據轉為月頻"""
    return daily_data.resample("M").last()
```

### 處理缺失值

```python
def handle_missing(data: pd.Series, method: str = "ffill") -> pd.Series:
    """處理缺失值"""
    if method == "ffill":
        return data.ffill()
    elif method == "interpolate":
        return data.interpolate()
    else:
        return data.dropna()
```

## 數據品質檢查

### 異常值檢測

```python
def detect_outliers(data: pd.Series, n_std: float = 3.0) -> pd.Series:
    """檢測異常值"""
    mean = data.mean()
    std = data.std()
    is_outlier = (data - mean).abs() > n_std * std
    return is_outlier
```

### 數據連續性檢查

```python
def check_continuity(data: pd.Series, max_gap_days: int = 5) -> list:
    """檢查數據連續性"""
    gaps = []
    dates = data.index.to_series()
    diff = dates.diff().dt.days
    large_gaps = diff[diff > max_gap_days]
    for idx, gap in large_gaps.items():
        gaps.append({"date": idx, "gap_days": gap})
    return gaps
```

## 錯誤處理

### 數據不可用時的備援

```python
def fetch_with_fallback(primary_func, fallback_func, *args, **kwargs):
    """帶備援的數據抓取"""
    try:
        return primary_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Primary source failed: {e}, trying fallback")
        return fallback_func(*args, **kwargs)

# 使用範例
gold_prices = fetch_with_fallback(
    fetch_gold_yahoo,
    fetch_gold_stooq,
    start="1970-01-01",
    end="2026-01-15"
)
```

### 部分數據可用時的處理

```python
def analyze_with_partial_data(gold_prices, macro_data: dict) -> dict:
    """
    使用部分可用數據進行分析

    如果某些宏觀數據不可用，仍可輸出偏離度分析，
    但 regime 判定的信心度會降低。
    """
    result = {
        "deviation_analysis": calculate_deviation(gold_prices),
        "regime": None,
        "warnings": []
    }

    available_factors = sum(1 for v in macro_data.values() if v is not None)
    total_factors = len(macro_data)

    if available_factors == 0:
        result["warnings"].append("No macro data available, regime analysis skipped")
    elif available_factors < total_factors:
        result["warnings"].append(
            f"Only {available_factors}/{total_factors} macro factors available, "
            "regime confidence reduced"
        )
        result["regime"] = calculate_regime_partial(macro_data)
    else:
        result["regime"] = calculate_regime(macro_data)

    return result
```

## API 使用限制

| 來源 | 限制 | 建議 |
|------|------|------|
| Yahoo Finance | 無官方限制，但過於頻繁可能被封鎖 | 加入隨機延遲 |
| FRED | 無限制（公共數據） | 正常使用即可 |
| Stooq | 無官方限制 | 加入隨機延遲 |

## 數據更新頻率

| 數據 | 更新頻率 | 建議抓取頻率 |
|------|----------|--------------|
| 黃金價格 | 每個交易日 | 每日或每週 |
| TIPS 收益率 | 每個交易日 | 每週 |
| 通膨預期 | 每個交易日 | 每週 |
| 美元指數 | 每個交易日 | 每週 |
| GPR | 每月 | 每月 |
