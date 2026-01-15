# 方法論：指數趨勢擬合與偏離度計算

本文件說明資產趨勢偏離度的計算方法論，適用於各類具有長期指數成長特性的資產。

## 核心假設

### 資產長期遵循指數成長

許多資產在長期（數十年）尺度上遵循指數成長路徑，主要原因：

1. **經濟成長**：全球經濟、貨幣供應量長期以指數方式增長
2. **複利效應**：任何穩定的成長率在長期都會表現為指數形式
3. **通膨因素**：名目價格會隨著通膨而增長

**適用資產範例**：
- **商品**：黃金、白銀、原油（受貨幣供應與購買力影響）
- **股票指數**：S&P 500、NASDAQ（受經濟成長與盈利成長驅動）
- **加密貨幣**：比特幣、以太坊（受採用率與網絡效應驅動）
- **房地產**：房價指數（受收入成長與都市化影響）

### 偏離度的意義

偏離度衡量當前價格與「公允長期趨勢」的距離：

- **正偏離**：價格高於趨勢，可能反映過度樂觀或極端事件
- **負偏離**：價格低於趨勢，可能反映過度悲觀或錯誤定價

## 計算步驟

### Step 1: 數據準備

```python
import pandas as pd
import numpy as np
import yfinance as yf

# 下載資產價格（日頻）
def fetch_asset_prices(symbol: str, start: str, end: str = None) -> pd.DataFrame:
    """從 Yahoo Finance 下載資產價格"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    return df

# 範例：黃金
prices = fetch_asset_prices(symbol="GC=F", start="1970-01-01")

# 轉換為月頻（降低噪音）
monthly_prices = prices["Close"].resample("ME").last().dropna()
```

### Step 2: 對數轉換

```python
# 對價格取自然對數
log_prices = np.log(monthly_prices)
```

**為什麼取對數？**

指數函數 `y = e^(a + bt)` 取對數後變為線性：`ln(y) = a + bt`

這使得我們可以用簡單的線性回歸來擬合指數趨勢。

### Step 3: 線性回歸擬合

```python
def fit_exponential_trend(prices: pd.Series) -> tuple:
    """
    擬合指數趨勢線

    Args:
        prices: 價格序列

    Returns:
        (trend_series, (a, b))
        - trend_series: 趨勢價格序列
        - a: 截距（初始對數價格）
        - b: 斜率（對數成長率）
    """
    # 時間索引（0, 1, 2, ...）
    t = np.arange(len(prices))

    # 對數價格
    y = np.log(prices.values)

    # 建立設計矩陣 [1, t]
    X = np.vstack([np.ones_like(t), t]).T

    # OLS 求解 y = a + b*t
    params, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    a, b = params

    # 趨勢價格 = exp(a + b*t)
    trend = np.exp(a + b * t)

    return pd.Series(trend, index=prices.index), (a, b)
```

### Step 4: 計算偏離度

```python
def distance_from_trend_pct(prices: pd.Series, trend: pd.Series) -> pd.Series:
    """
    計算偏離度百分比

    Args:
        prices: 實際價格
        trend: 趨勢價格

    Returns:
        偏離度序列（百分比）
    """
    return (prices / trend - 1.0) * 100.0
```

**偏離度公式**：

```
distance_pct = (price / trend - 1) × 100%
            = (price - trend) / trend × 100%
```

### Step 5: 計算歷史分位數

```python
def calculate_percentile(distance_series: pd.Series) -> float:
    """
    計算當前偏離度在歷史中的分位數

    Returns:
        分位數（0-100）
    """
    current = distance_series.iloc[-1]
    percentile = (distance_series < current).sum() / len(distance_series) * 100
    return percentile
```

## 參數選擇

### 趨勢擬合區間

| 策略 | 優點 | 缺點 | 適用場景 |
|------|------|------|----------|
| 全樣本（full） | 穩定、不受近期波動影響 | 可能忽略結構性變化 | 長期分析（推薦） |
| 滾動窗口（rolling） | 能捕捉趨勢變化 | 對窗口大小敏感 | 觀察斜率演變 |

**推薦**：使用全樣本擬合，從 1970 年開始。

### 數據頻率

| 頻率 | 優點 | 缺點 | 適用場景 |
|------|------|------|----------|
| 日頻 | 數據量大、精細 | 噪音大 | 短期分析 |
| 月頻 | 平滑、穩定 | 信息量較少 | 長期趨勢分析（推薦） |

**推薦**：長期趨勢分析使用月頻數據。

## 數學細節

### 指數成長模型

假設資產價格遵循指數成長：

```
P(t) = P₀ × e^(r × t)
```

其中：
- `P(t)` = 時間 t 的價格
- `P₀` = 初始價格
- `r` = 年化成長率（對數成長率）
- `t` = 時間（年）

**成長率範例**：
- 黃金（1970-2026）：~5-6% 年化
- S&P 500（1950-2026）：~7-8% 年化
- 比特幣（2013-2026）：~100%+ 年化（高波動）

### 對數線性回歸

取對數：

```
ln(P(t)) = ln(P₀) + r × t
         = a + b × t
```

其中：
- `a = ln(P₀)` = 截距
- `b = r` = 斜率（對數成長率）

### OLS 估計

最小化殘差平方和：

```
min Σ (ln(Pᵢ) - a - b × tᵢ)²
```

解：

```
b = Cov(t, ln(P)) / Var(t)
a = mean(ln(P)) - b × mean(t)
```

### 趨勢價格

```
trend(t) = exp(a + b × t)
```

### 偏離度

```
distance_pct(t) = (P(t) / trend(t) - 1) × 100%
```

## 注意事項

### 結構性變化

資產的長期成長率可能因結構性因素而改變：

**商品範例**：
- 貨幣制度變化（如 1971 年布雷頓森林體系瓦解）
- 央行政策轉變（量化寬鬆、負利率政策）
- 供需結構變化（新礦場、新需求來源）

**股票範例**：
- 科技革新（網際網路、AI）
- 監管環境變化（反壟斷、財務會計準則）
- 全球化程度（新興市場崛起）

**加密貨幣範例**：
- 減半事件（比特幣供應減少）
- 監管態度轉變（合法化或禁止）
- 採用率階段轉換（早期採用 → 主流採用）

**處理方式**：可考慮分段擬合或允許趨勢斜率隨時間變化。

### 樣本外推

趨勢線外推至未來有風險：

- 過去的成長率不保證未來
- 極端偏離可能持續比預期更久

**建議**：偏離度僅作為參考，而非交易訊號。

### 數據品質

長期數據可能有以下問題：

- 不同數據源的定義差異
- 早期數據可能不精確
- 合約展期造成的價格跳躍

**建議**：使用一致的數據源，並檢查異常值。
