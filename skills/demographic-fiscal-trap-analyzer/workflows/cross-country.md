# 跨國比較工作流 (Cross-Country Comparison Workflow)

## 概述
對多個國家/地區進行並排比較，產出財政陷阱分數排名、四支柱雷達圖、以及象限分布圖。

## 前置條件
- 至少 2 個以上的分析實體
- 統一的時間區間
- 所有實體的資料可用性確認

## 執行步驟

### Step 1: 定義比較群組
```
支援的預設群組：
- G7: USA, JPN, DEU, GBR, FRA, ITA, CAN
- G20: G7 + CHN, IND, BRA, RUS, AUS, KOR, MEX, IDN, TUR, SAU, ARG, ZAF, EU
- OECD: 38 個成員國
- EU27: 歐盟成員國
- ASEAN: SGP, MYS, THA, IDN, PHL, VNM, MMR, KHM, LAO, BRN
- EM_ASIA: CHN, IND, KOR, TWN, THA, MYS, IDN, PHL, VNM
- CUSTOM: 使用者自定義列表
```

### Step 2: 批量資料擷取
```python
# 對所有實體批量擷取資料
data = {}
for entity in entities:
    data[entity] = {
        "old_age_dep": fetch_old_age_dependency(entity, start_year, end_year),
        "debt_gdp": fetch_debt_to_gdp(entity, start_year, end_year),
        "gov_consumption": fetch_gov_consumption(entity, start_year, end_year),
        "gdp_growth": fetch_nominal_gdp_growth(entity, start_year, end_year),
        "cpi": fetch_cpi(entity, start_year, end_year),
        "yield_10y": fetch_10y_yield(entity, start_year, end_year)
    }

# 記錄資料可用性
availability_matrix = check_data_availability(data)
```

### Step 3: 跨國截面統計
```python
# 計算 end_year 的截面統計量
cross_section_stats = {
    "old_age_dep": {
        "mean": np.mean([d["old_age_dep"][end_year] for d in data.values()]),
        "std": np.std([d["old_age_dep"][end_year] for d in data.values()])
    },
    "debt_gdp": {...},
    "gov_consumption": {...},
    "gdp_growth": {...}
}
```

### Step 4: 計算各國分數
```python
results = {}
for entity in entities:
    # 計算四支柱 z-scores（使用截面統計量）
    aging_pressure = compute_aging_pressure(data[entity], cross_section_stats)
    debt_dynamics = compute_debt_dynamics(data[entity], cross_section_stats)
    bloat_index = compute_bloat_index(data[entity], cross_section_stats)
    growth_drag = compute_growth_drag(data[entity], cross_section_stats)

    # 加權總分
    fiscal_trap_score = weighted_sum(aging_pressure, debt_dynamics, bloat_index, growth_drag, weights)
    inflation_incentive = compute_inflation_incentive(data[entity], cross_section_stats)

    # 象限分類
    quadrant = classify_quadrant(aging_pressure, debt_dynamics)

    results[entity] = {
        "fiscal_trap_score": fiscal_trap_score,
        "inflation_incentive": inflation_incentive,
        "aging_pressure": aging_pressure,
        "debt_dynamics": debt_dynamics,
        "bloat_index": bloat_index,
        "growth_drag": growth_drag,
        "quadrant": quadrant
    }
```

### Step 5: 排名與分組
```python
# 按 fiscal_trap_score 排名
ranking = sorted(results.items(), key=lambda x: x[1]["fiscal_trap_score"], reverse=True)

# 風險分組
high_risk = [e for e, r in ranking if r["fiscal_trap_score"] > 1.5]
elevated = [e for e, r in ranking if 0.5 < r["fiscal_trap_score"] <= 1.5]
moderate = [e for e, r in ranking if -0.5 < r["fiscal_trap_score"] <= 0.5]
low_risk = [e for e, r in ranking if r["fiscal_trap_score"] <= -0.5]

# 象限分布
quadrant_distribution = Counter([r["quadrant"] for r in results.values()])
```

### Step 6: 視覺化建議
```
建議產出的圖表：

1. 排名條形圖 (Bar Chart)
   - X軸: 國家
   - Y軸: fiscal_trap_score
   - 顏色: 風險等級

2. 四支柱雷達圖 (Radar Chart)
   - 每個國家一張
   - 四軸: aging, debt, bloat, growth_drag

3. 象限散點圖 (Scatter Plot)
   - X軸: Aging Pressure
   - Y軸: Debt Dynamics
   - 點大小: fiscal_trap_score
   - 顏色: 通膨激勵指數

4. 熱力圖 (Heatmap)
   - 行: 國家
   - 列: 四支柱 + 總分
   - 顏色: z-score 強度
```

## 輸出格式
```json
{
  "comparison_group": "G7",
  "time_period": "2015-2023",
  "ranking": [
    {"rank": 1, "entity": "JPN", "fiscal_trap_score": 2.35, "quadrant": "Q1"},
    {"rank": 2, "entity": "ITA", "fiscal_trap_score": 1.82, "quadrant": "Q1"},
    {"rank": 3, "entity": "FRA", "fiscal_trap_score": 1.15, "quadrant": "Q2"},
    {"rank": 4, "entity": "GBR", "fiscal_trap_score": 0.85, "quadrant": "Q3"},
    {"rank": 5, "entity": "USA", "fiscal_trap_score": 0.72, "quadrant": "Q3"},
    {"rank": 6, "entity": "DEU", "fiscal_trap_score": 0.45, "quadrant": "Q2"},
    {"rank": 7, "entity": "CAN", "fiscal_trap_score": 0.12, "quadrant": "Q4"}
  ],
  "risk_groups": {
    "high_risk": ["JPN", "ITA"],
    "elevated": ["FRA", "GBR", "USA"],
    "moderate": ["DEU"],
    "low_risk": ["CAN"]
  },
  "quadrant_distribution": {
    "Q1_HighAging_HighDebt": 2,
    "Q2_HighAging_LowDebt": 2,
    "Q3_LowAging_HighDebt": 2,
    "Q4_LowAging_LowDebt": 1
  },
  "detailed_scores": {
    "JPN": {
      "fiscal_trap_score": 2.35,
      "inflation_incentive": 1.95,
      "aging_pressure": 2.8,
      "debt_dynamics": 2.5,
      "bloat_index": 0.8,
      "growth_drag": 1.2
    }
    // ... 其他國家
  },
  "cross_section_stats": {
    "fiscal_trap_score": {"mean": 1.07, "std": 0.78, "min": 0.12, "max": 2.35}
  },
  "interpretation": "G7中日本與義大利位於高風險區，兩國均處於Q1象限（高老化+高債務）；加拿大相對最健康"
}
```

## 注意事項
- 確保所有國家使用相同年份資料，避免時間不一致
- 資料缺失國家應標記並從截面統計中排除或做適當處理
- 新興市場與已開發國家的比較需謹慎解讀
