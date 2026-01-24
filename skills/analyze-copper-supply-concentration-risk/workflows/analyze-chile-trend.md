# Workflow: 智利銅產量結構性趨勢分析

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/chile-supply-dynamics.md
</required_reading>

<process>
## Step 1: 確認分析參數

收集或確認以下參數：

```yaml
country: "Chile"          # 目標國家
start_year: 1970          # 分析起始年
end_year: 2023            # 分析結束年
rolling_window: 10        # 滾動趨勢視窗（年）
structural_break: true    # 是否偵測結構斷點
ore_grade_mode: "country_proxy"  # none | country_proxy | mine_level
```

**ore_grade_mode 說明：**
- `none`：只做產量趨勢分析
- `country_proxy`：用產量趨勢作為品位下滑的間接代理
- `mine_level`：如有礦場級品位數據則使用

## Step 2: 擷取智利產量數據

從 OWID 擷取智利歷年銅產量：

```bash
python scripts/fetch_owid.py --commodity=copper --country=Chile --start={start_year} --end={end_year}
```

確保數據包含：
- 年度產量（公噸銅金屬含量）
- 全球總產量（用於計算份額）

## Step 3: 計算基礎趨勢指標

```python
def compute_trend_metrics(df, country="Chile"):
    """計算智利產量趨勢指標"""
    chile_data = df[df.country == country].sort_values("year")

    # 峰值分析
    peak_idx = chile_data.production.idxmax()
    peak_year = chile_data.loc[peak_idx, "year"]
    peak_production = chile_data.loc[peak_idx, "production"]

    # 最新數據
    latest = chile_data.iloc[-1]
    latest_year = latest.year
    latest_production = latest.production

    # 峰值回撤 (Drawdown)
    drawdown = (peak_production - latest_production) / peak_production

    return {
        "peak_year": peak_year,
        "peak_production": peak_production,
        "latest_year": latest_year,
        "latest_production": latest_production,
        "drawdown": drawdown
    }
```

## Step 4: 計算滾動趨勢斜率

```python
import numpy as np

def rolling_slope(series, window=10):
    """
    計算滾動線性回歸斜率

    Parameters:
    -----------
    series : pd.Series
        時間序列數據（index 為年份）
    window : int
        滾動視窗大小

    Returns:
    --------
    pd.Series
        滾動斜率序列（單位：t/年）
    """
    slopes = []
    years = series.index.values

    for i in range(window - 1, len(series)):
        y = series.values[i - window + 1:i + 1]
        x = years[i - window + 1:i + 1]
        # 線性回歸
        coeffs = np.polyfit(x, y, 1)
        slopes.append(coeffs[0])

    # 前面補 NaN
    result = [np.nan] * (window - 1) + slopes
    return pd.Series(result, index=series.index)

# 計算智利產量的滾動斜率
chile_series = df[df.country == "Chile"].set_index("year")["production"]
chile_rolling_slope = rolling_slope(chile_series, window=rolling_window)
latest_slope = chile_rolling_slope.iloc[-1]
```

## Step 5: 偵測結構斷點

**方法一：簡易雙線段回歸**

```python
def find_breakpoint_simple(series, min_segment=5):
    """
    簡易結構斷點偵測：找到使兩段線性回歸總誤差最小的分割點

    Returns:
    --------
    dict with break_year, pre_slope, post_slope
    """
    years = series.index.values
    values = series.values
    n = len(series)

    best_mse = float('inf')
    best_break = None

    for i in range(min_segment, n - min_segment):
        # 前段回歸
        x1, y1 = years[:i], values[:i]
        p1 = np.polyfit(x1, y1, 1)
        mse1 = np.mean((y1 - np.polyval(p1, x1)) ** 2)

        # 後段回歸
        x2, y2 = years[i:], values[i:]
        p2 = np.polyfit(x2, y2, 1)
        mse2 = np.mean((y2 - np.polyval(p2, x2)) ** 2)

        total_mse = mse1 * len(x1) + mse2 * len(x2)

        if total_mse < best_mse:
            best_mse = total_mse
            best_break = {
                "break_year": years[i],
                "pre_slope": p1[0],
                "post_slope": p2[0]
            }

    return best_break
```

**方法二：使用 ruptures（如已安裝）**

```python
# Optional: 使用 ruptures 套件做更精確的斷點偵測
try:
    import ruptures as rpt

    def find_breakpoint_ruptures(series, n_breakpoints=1):
        signal = series.values.reshape(-1, 1)
        algo = rpt.Pelt(model="l2").fit(signal)
        result = algo.predict(pen=10)
        break_indices = result[:-1]  # 排除最後一個（序列結尾）
        break_years = [series.index[i] for i in break_indices]
        return break_years

except ImportError:
    # 退回使用簡易方法
    pass
```

## Step 6: 判定結構性衰退

根據三指標組合判定：

```python
def classify_trend(slope, drawdown, break_info, threshold_slope=-20000):
    """
    判定產量趨勢類型

    Parameters:
    -----------
    slope : float
        近 N 年趨勢斜率（t/年）
    drawdown : float
        從峰值回撤幅度（0-1）
    break_info : dict
        斷點資訊（含 pre_slope, post_slope）
    threshold_slope : float
        負向斜率門檻

    Returns:
    --------
    str : "structural_decline" | "plateau" | "growth"
    """
    slope_negative = slope < threshold_slope
    significant_drawdown = drawdown > 0.10
    trend_reversal = (break_info["pre_slope"] > 0 and break_info["post_slope"] < 0)

    if slope_negative and significant_drawdown and trend_reversal:
        return "structural_decline"  # 結構性衰退
    elif abs(slope) < abs(threshold_slope) and significant_drawdown:
        return "plateau"  # 高原期
    elif slope > 0:
        return "growth"  # 仍在增長
    else:
        return "uncertain"  # 需要更多分析
```

## Step 7: 品位代理分析（country_proxy 模式）

當 ore_grade_mode = "country_proxy" 時，使用以下邏輯：

```python
def infer_grade_decline(production_series, world_demand_growth=0.03):
    """
    從產量趨勢推斷品位下滑

    邏輯：若全球需求成長 3%/年，價格處於高位，但智利產量停滯/下滑
    → 說明不是需求問題，而是供應端（品位、成本）問題
    """
    growth_rate = (production_series.iloc[-1] / production_series.iloc[-10]) ** 0.1 - 1

    if growth_rate < world_demand_growth / 2:
        inference = {
            "grade_decline_likely": True,
            "evidence": [
                "產量增速遠低於全球需求增速",
                "高銅價環境下產量仍未提升",
                "主要礦區公開報告品位下滑"
            ],
            "confidence": 0.7
        }
    else:
        inference = {
            "grade_decline_likely": False,
            "evidence": ["產量增速與需求增速匹配"],
            "confidence": 0.5
        }

    return inference
```

## Step 8: 生成視覺化圖表

```bash
python scripts/visualize_analysis.py --mode=chile-trend
```

**生成的圖表**：
1. `chile_production_trend_YYYYMMDD.png` - 智利產量與趨勢線
2. `chile_slope_rolling_YYYYMMDD.png` - 滾動斜率變化
3. `chile_breakpoint_YYYYMMDD.png` - 結構斷點視覺化

## Step 9: 輸出結果

**JSON 輸出：**

```json
{
  "commodity": "copper",
  "analysis_type": "chile_trend",
  "country": "Chile",
  "period": {
    "start_year": 1970,
    "end_year": 2023
  },
  "trend_metrics": {
    "peak_year": 2018,
    "peak_production_mt": 5.83,
    "latest_production_mt": 5.26,
    "drawdown": 0.098,
    "rolling_slope_t_per_year": -47000,
    "rolling_window": 10
  },
  "structural_break": {
    "detected": true,
    "break_year": 2016,
    "pre_slope_t_per_year": 85000,
    "post_slope_t_per_year": -38000
  },
  "classification": "structural_decline",
  "grade_inference": {
    "mode": "country_proxy",
    "grade_decline_likely": true,
    "confidence": 0.7
  },
  "data_sources": ["OWID Minerals"],
  "generated_at": "2026-01-24"
}
```

**Markdown 報告：**

```markdown
## 智利銅產量結構性趨勢分析

### 執行摘要

智利銅產量已進入 **{classification}** 期。從 {peak_year} 年的峰值
{peak_production_mt:.2f} Mt 下滑至 {end_year} 年的 {latest_production_mt:.2f} Mt，
回撤幅度 {drawdown:.1%}。結構斷點出現在 {break_year} 年。

### 關鍵指標

| 指標 | 數值 | 解讀 |
|------|------|------|
| 峰值年份 | {peak_year} | 產量達到歷史最高點 |
| 峰值產量 | {peak_production_mt:.2f} Mt | - |
| 最新產量 | {latest_production_mt:.2f} Mt | 較峰值下滑 {drawdown:.1%} |
| 近 {window} 年斜率 | {slope:+,.0f} t/年 | {slope_interpretation} |
| 結構斷點 | {break_year} | 趨勢由升轉降 |

### 判定邏輯

- slope < 0 : {slope_check}
- structural_break detected : {break_check}
- drawdown > 10% : {drawdown_check}

**結論**：{conclusion}

### 品位推斷（country_proxy 模式）

{grade_inference_text}

### 風險提示

- 儲量排名全球第一 ≠ 產量能持續增長
- 品位下滑意味著需要挖掘更多礦石維持同樣產出
- 水資源限制可能進一步約束產能

### 數據來源

- OWID Minerals Explorer
- 口徑：mined copper content（銅金屬含量）
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 計算峰值、回撤、滾動斜率三指標
- [ ] 偵測結構斷點（若 structural_break=true）
- [ ] 判定趨勢類型（structural_decline/plateau/growth）
- [ ] 如使用 country_proxy 模式，輸出品位推斷
- [ ] 輸出 JSON + Markdown 格式
- [ ] 包含視覺化圖表（可選）
</success_criteria>
