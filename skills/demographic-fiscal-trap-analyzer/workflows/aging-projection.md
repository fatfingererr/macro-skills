# 老化投影工作流 (Aging Projection Workflow)

## 概述
利用 UN World Population Prospects 撫養比預測數據，前瞻性評估各國的老化壓力演化與長期財政影響。

## 前置條件
- 已確認分析實體
- 可存取 UN WPP 預測資料
- 已設定預測結束年（forecast_end_year）

## 執行步驟

### Step 1: 歷史資料擷取
```
從 World Bank WDI 擷取歷史撫養比：
- SP.POP.DPND.OL (老年撫養比: 65+/15-64)
- SP.POP.DPND.YG (青年撫養比: 0-14/15-64)
- SP.POP.DPND (總撫養比)

時間範圍: start_year 至 end_year
```

### Step 2: 預測資料擷取
```
從 UN WPP 擷取預測數據：
- 中位數預測 (Medium variant)
- 可選：高/低預測區間

時間範圍: end_year 至 forecast_end_year (如 2050)
```

### Step 3: 趨勢分析
```python
# 歷史趨勢
historical_slope = linear_slope(old_age_dep[start_year:end_year])
historical_level = old_age_dep[end_year]

# 預測趨勢
forecast_slope = linear_slope(old_age_dep[end_year:forecast_end_year])
forecast_level = old_age_dep[forecast_end_year]

# 加速度（斜率變化）
acceleration = forecast_slope - historical_slope

# 關鍵轉折點
peak_year = old_age_dep.idxmax()  # 撫養比峰值年份（若有）
```

### Step 4: 跨國相對位置
```python
# 計算 end_year 的跨國 z-score
aging_zscore_current = zscore(historical_level)

# 計算 forecast_end_year 的跨國 z-score
aging_zscore_future = zscore(forecast_level)

# 相對排名
rank_current = rank_among_entities(historical_level)
rank_future = rank_among_entities(forecast_level)
```

### Step 5: 財政壓力推估
```python
# 老年相關支出佔 GDP 比例（粗估）
# 基於 OECD 經驗：每增加 1% 老年撫養比 → 約增加 0.3% GDP 的養老金+健保支出

baseline_elderly_spending = elderly_spending_to_gdp[end_year]
projected_spending_increase = (forecast_level - historical_level) * 0.3

projected_elderly_spending = baseline_elderly_spending + projected_spending_increase

# 財政壓力指數
fiscal_pressure_index = projected_spending_increase / nominal_gdp_growth_avg
```

### Step 6: 情境分析
```
模擬不同人口情境：

1. 中位數預測 (Medium variant)
   - UN 基準假設

2. 高生育情境 (High fertility)
   - 青年撫養比上升，老年撫養比壓力略減

3. 低生育情境 (Low fertility)
   - 老化壓力加速

4. 移民情境 (Migration adjustment)
   - 淨移入對工作年齡人口的支撐效果
```

### Step 7: 老化階段分類
```python
# 基於老年撫養比水準與趨勢分類

if historical_level > 0.40:
    if forecast_slope > 0.005:
        stage = "SUPER_AGED_ACCELERATING"  # 超高齡且加速（如韓國）
    else:
        stage = "SUPER_AGED_PLATEAU"  # 超高齡但趨緩（如日本）
elif historical_level > 0.25:
    if forecast_slope > 0.008:
        stage = "AGING_RAPID"  # 快速老化中（如中國、台灣）
    else:
        stage = "AGING_MODERATE"  # 溫和老化（如美國）
else:
    if forecast_slope > 0.005:
        stage = "YOUNG_BUT_TURNING"  # 年輕但轉向（如印度）
    else:
        stage = "DEMOGRAPHIC_DIVIDEND"  # 人口紅利期
```

## 輸出格式
```json
{
  "entity": "KOR",
  "aging_projection": {
    "current_year": 2023,
    "forecast_year": 2050,
    "old_age_dependency": {
      "current": 0.24,
      "forecast": 0.78,
      "change": 0.54,
      "zscore_current": 0.8,
      "zscore_forecast": 2.5
    },
    "total_dependency": {
      "current": 0.40,
      "forecast": 0.95
    },
    "trend": {
      "historical_slope_10y": 0.012,
      "forecast_slope": 0.020,
      "acceleration": 0.008,
      "peak_year": 2065
    },
    "fiscal_pressure": {
      "baseline_elderly_spending_pct_gdp": 8.5,
      "projected_increase_pct_gdp": 16.2,
      "projected_total_pct_gdp": 24.7
    },
    "stage": "AGING_RAPID",
    "rank_among_oecd": {
      "current": 15,
      "forecast": 1
    }
  },
  "interpretation": "南韓正經歷全球最快速的老化，預計2050年老年撫養比將達0.78，躍升OECD第一，老年相關支出將佔GDP近25%"
}
```

## 注意事項
- UN WPP 每 2 年更新一次，確認使用最新版本
- 長期預測不確定性高，應呈現區間而非單一點估計
- 移民政策變化可能顯著影響預測
- 退休年齡改革可降低有效撫養比
