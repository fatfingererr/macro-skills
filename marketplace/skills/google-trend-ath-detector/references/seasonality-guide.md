<overview>
季節性分解方法詳解。用於區分「真正的異常」與「預期的季節性波動」。
</overview>

<why_seasonality_matters>
**為什麼季節性分析重要**

很多搜尋趨勢有固定的年度週期：
- **Health Insurance**：每年 11-12 月 Open Enrollment 期間上升
- **Tax**：每年 1-4 月報稅季上升
- **Flu**：每年秋冬季上升
- **Travel**：每年暑假和節日期間上升

如果不做季節性分解，可能把**正常的季節性高點**誤判為**異常飆升**。

**核心問題：**
> 「這個高點是『每年這時候都會這樣』還是『今年特別不尋常』？」
</why_seasonality_matters>

<stl_decomposition>
**STL 分解（推薦方法）**

STL = Seasonal and Trend decomposition using Loess

**原理：**
將時間序列分解為三個組成部分：
```
Y(t) = Trend(t) + Seasonal(t) + Residual(t)
```

| 組成 | 說明 | 用途 |
|------|------|------|
| Trend | 長期趨勢 | 識別結構性變化 |
| Seasonal | 季節性模式 | 識別週期性波動 |
| Residual | 殘差 | 識別真正的異常 |

**Python 實作：**

```python
from statsmodels.tsa.seasonal import STL
import pandas as pd

def stl_decompose(ts, granularity='weekly'):
    """
    執行 STL 季節性分解

    Args:
        ts: pandas Series with DatetimeIndex
        granularity: 'weekly' or 'monthly'

    Returns:
        dict with trend, seasonal, resid, seasonal_strength
    """
    # 確定週期
    period = 52 if granularity == 'weekly' else 12

    # 移除 NaN
    ts_clean = ts.dropna()

    # 需要至少 2 個週期的數據
    if len(ts_clean) < period * 2:
        raise ValueError(f"需要至少 {period * 2} 個數據點")

    # STL 分解
    stl = STL(ts_clean, period=period, robust=True)
    result = stl.fit()

    # 計算季節性強度
    # 公式: 1 - Var(Residual) / Var(Seasonal + Residual)
    seasonal_plus_resid = result.seasonal + result.resid
    seasonal_strength = 1 - result.resid.var() / seasonal_plus_resid.var()

    return {
        'trend': result.trend,
        'seasonal': result.seasonal,
        'resid': result.resid,
        'seasonal_strength': round(seasonal_strength, 3)
    }
```

**季節性強度解讀：**

| 範圍 | 解讀 |
|------|------|
| > 0.7 | 強季節性（模式主導） |
| 0.4 - 0.7 | 中等季節性 |
| 0.2 - 0.4 | 弱季節性 |
| < 0.2 | 幾乎無季節性 |
</stl_decomposition>

<deseasonalized_analysis>
**去季節化分析**

去季節化後的序列 = 原序列 - 季節性成分

```python
def get_deseasonalized(ts, decomposition):
    """取得去季節化序列"""
    return ts - decomposition['seasonal']

def analyze_deseasonalized_anomaly(deseasonalized, method='zscore', threshold=2.5):
    """
    在去季節化序列上進行異常偵測

    這才是「真正的異常」，因為已經排除了季節性因素
    """
    if method == 'zscore':
        mean = deseasonalized.mean()
        std = deseasonalized.std()
        zscore = (deseasonalized.iloc[-1] - mean) / std
        is_anomaly = abs(zscore) >= threshold
        return {
            'method': 'zscore',
            'score': round(zscore, 2),
            'is_anomaly': is_anomaly,
            'interpretation': '去季節化後仍顯著異常' if is_anomaly else '季節性可解釋大部分波動'
        }
```
</deseasonalized_analysis>

<month_fixed_effects>
**月份固定效果（替代方法）**

當季節性模式非常規律且穩定時，可以用更簡單的月份固定效果：

```python
def month_fixed_effects_adjustment(ts):
    """
    用月份固定效果調整季節性

    適用於：季節性非常穩定、變化不大的主題
    """
    # 計算每個月的平均值
    monthly_mean = ts.groupby(ts.index.month).transform('mean')

    # 計算整體平均值
    overall_mean = ts.mean()

    # 月份效果 = 月平均 - 整體平均
    month_effect = monthly_mean - overall_mean

    # 去季節化 = 原值 - 月份效果
    deseasonalized = ts - month_effect

    return deseasonalized, month_effect
```

**與 STL 的比較：**

| 特性 | STL | 月份固定效果 |
|------|-----|--------------|
| 靈活性 | 高（季節性可隨時間變化） | 低（假設季節性恆定） |
| 計算複雜度 | 較高 | 很低 |
| 數據需求 | 至少 2 個週期 | 至少 1 個週期 |
| 適用場景 | 通用 | 穩定季節性 |
</month_fixed_effects>

<seasonal_comparison>
**同期比較分析**

另一種處理季節性的方法是直接比較「今年 vs 歷史同期」：

```python
def compare_to_same_period(ts, lookback_years=5):
    """
    比較當前值與歷史同期

    Args:
        ts: pandas Series with DatetimeIndex
        lookback_years: 回看年數

    Returns:
        dict with percentile, comparison stats
    """
    current_month = ts.index[-1].month
    current_week = ts.index[-1].isocalendar().week
    current_value = ts.iloc[-1]

    # 收集歷史同期數據
    historical_same_period = []
    for year in range(ts.index[-1].year - lookback_years, ts.index[-1].year):
        mask = (ts.index.year == year) & (ts.index.month == current_month)
        if mask.any():
            historical_same_period.extend(ts[mask].values)

    if not historical_same_period:
        return {'error': '歷史同期數據不足'}

    # 計算百分位數
    percentile = (sum(v < current_value for v in historical_same_period)
                  / len(historical_same_period) * 100)

    return {
        'current_value': float(current_value),
        'historical_same_period_mean': round(sum(historical_same_period) / len(historical_same_period), 1),
        'historical_same_period_max': max(historical_same_period),
        'historical_same_period_min': min(historical_same_period),
        'percentile_vs_same_period': round(percentile, 1),
        'interpretation': interpret_percentile(percentile)
    }

def interpret_percentile(percentile):
    if percentile >= 95:
        return "顯著高於歷史同期（異常）"
    elif percentile >= 75:
        return "高於歷史同期平均"
    elif percentile >= 25:
        return "接近歷史同期平均"
    else:
        return "低於歷史同期平均"
```
</seasonal_comparison>

<common_seasonal_patterns>
**常見搜尋主題的季節性模式**

| 主題 | 高峰月份 | 原因 |
|------|----------|------|
| Health Insurance | 11-12 月 | Open Enrollment |
| Tax / IRS | 1-4 月 | 報稅季 |
| Flu / Cold | 10-2 月 | 流感季 |
| Travel / Vacation | 6-8 月 | 暑假 |
| Christmas / Gift | 11-12 月 | 聖誕購物 |
| Back to School | 8-9 月 | 開學季 |
| Allergy | 3-5 月 | 春季花粉 |
| Diet / Weight Loss | 1 月 | 新年決心 |
| Sunscreen | 5-8 月 | 夏季 |
| Heating | 10-2 月 | 冬季 |
</common_seasonal_patterns>

<decision_tree>
**季節性分析決策樹**

```
                    ┌──────────────────┐
                    │ 抓取 Google Trends │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ 數據足夠 (>104週)? │
                    └────────┬─────────┘
                      Yes    │    No
                    ┌────────┴────────┐
                    │                 │
           ┌────────▼────────┐  ┌─────▼─────┐
           │   STL 分解      │  │ 簡化分析  │
           └────────┬────────┘  └───────────┘
                    │
           ┌────────▼────────┐
           │ 季節強度 > 0.5? │
           └────────┬────────┘
              Yes   │   No
           ┌────────┴────────┐
           │                 │
   ┌───────▼───────┐ ┌───────▼───────┐
   │ 去季節化後    │ │ 直接在原序列  │
   │ 做異常偵測    │ │ 做異常偵測    │
   └───────┬───────┘ └───────┬───────┘
           │                 │
           └────────┬────────┘
                    │
           ┌────────▼────────┐
           │   輸出結果      │
           └─────────────────┘
```
</decision_tree>
