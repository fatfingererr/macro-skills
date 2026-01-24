# Workflow: 供需缺口與系統風險情境模擬

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/geopolitics-risk.md
</required_reading>

<process>
## Step 1: 確認情境參數

收集或確認以下參數：

```yaml
# 需求情境
demand_scenarios:
  - name: "base"
    demand_cagr: 0.03    # 年化需求成長率
    horizon_years: 10     # 預測年限
  - name: "electrification"
    demand_cagr: 0.05    # 電氣化加速情境
    horizon_years: 10
  - name: "slowdown"
    demand_cagr: 0.015   # 經濟放緩情境
    horizon_years: 10

# 供應約束
supply_lead_time_years: 10   # 新礦開發週期

# 地緣風險
geopolitics_mode: "gdelt"    # none | gdelt | news_count
focus_countries:
  - Chile
  - Peru
  - Democratic Republic of Congo
```

## Step 2: 建立供需基準

```python
def establish_baseline(df, base_year):
    """建立供需基準數據"""
    world_data = df[df.country == "World"]
    latest = world_data[world_data.year == base_year]

    return {
        "base_year": base_year,
        "production_mt": latest.production.values[0] / 1e6,  # 轉換為 Mt
        "consumption_mt": latest.production.values[0] / 1e6 * 1.02,  # 假設消費略高於產量
        "inventory_mt": 2.0  # 約 2 個月消費量
    }

baseline = establish_baseline(df, end_year)
```

## Step 3: 需求預測

```python
def project_demand(baseline, scenario):
    """
    根據情境預測未來需求

    Parameters:
    -----------
    baseline : dict
        基準年供需數據
    scenario : dict
        情境參數（name, demand_cagr, horizon_years）

    Returns:
    --------
    list of dict : 逐年需求預測
    """
    projections = []
    current_demand = baseline["consumption_mt"]

    for year in range(1, scenario["horizon_years"] + 1):
        future_demand = current_demand * (1 + scenario["demand_cagr"]) ** year
        projections.append({
            "year": baseline["base_year"] + year,
            "demand_mt": future_demand,
            "cumulative_growth": future_demand / baseline["consumption_mt"] - 1
        })

    return projections

# 計算各情境需求預測
demand_projections = {}
for scenario in demand_scenarios:
    demand_projections[scenario["name"]] = project_demand(baseline, scenario)
```

## Step 4: 供應約束建模

```python
def model_supply_constraints(baseline, lead_time_years, chile_decline_info, replacement_info):
    """
    建模供應約束

    供應增量來源：
    1. 現有產能擴建（短期可行）
    2. 在建項目釋放（中期）
    3. 智利減產（負向）
    4. 秘魯/DRC 增量

    約束：
    - 新礦開發需要 lead_time 年
    - 現有產能擴建有上限
    """
    current_supply = baseline["production_mt"]

    # 各來源增量估算
    increments = {
        "brownfield_expansion": 0.3 * lead_time_years / 10,  # 現有礦擴建
        "under_construction": 0.2 * lead_time_years / 10,    # 在建項目
        "chile_decline": -abs(chile_decline_info["expected_decline"]) / 1e6,
        "peru_increment": replacement_info["Peru"]["expected_increment"] / 1e6,
        "drc_increment": replacement_info["DRC"]["expected_increment"] / 1e6
    }

    # 總可行增量
    feasible_increment = sum(increments.values())

    return {
        "current_supply_mt": current_supply,
        "feasible_increment_mt": feasible_increment,
        "increment_breakdown": increments,
        "supply_ceiling_mt": current_supply + feasible_increment,
        "lead_time_years": lead_time_years
    }

supply_model = model_supply_constraints(baseline, supply_lead_time_years, chile_decline, replacement_result)
```

## Step 5: 計算供需缺口

```python
def compute_supply_demand_gap(demand_projections, supply_model):
    """
    計算各情境下的供需缺口

    Returns:
    --------
    dict : 各情境的缺口分析
    """
    results = {}

    for scenario_name, demand_proj in demand_projections.items():
        # 取最終年需求
        final_demand = demand_proj[-1]["demand_mt"]
        supply_ceiling = supply_model["supply_ceiling_mt"]

        gap = final_demand - supply_ceiling
        gap_pct = gap / supply_model["current_supply_mt"]

        # 判斷缺口嚴重程度
        if gap <= 0:
            severity = "無缺口"
        elif gap_pct < 0.05:
            severity = "小缺口"
        elif gap_pct < 0.15:
            severity = "中等缺口"
        else:
            severity = "嚴重缺口"

        results[scenario_name] = {
            "final_demand_mt": final_demand,
            "supply_ceiling_mt": supply_ceiling,
            "gap_mt": gap,
            "gap_pct": gap_pct,
            "severity": severity,
            "demand_projections": demand_proj
        }

    return results

gap_analysis = compute_supply_demand_gap(demand_projections, supply_model)
```

## Step 6: 地緣風險指數計算（GDELT 模式）

```python
def compute_geo_risk_gdelt(countries, lookback_months=12):
    """
    使用 GDELT 事件資料計算地緣風險指數

    方法：
    1. 抓取各國與採礦/衝突/罷工相關的事件
    2. 計算事件頻率的 rolling z-score
    3. 輸出標準化風險分數

    注意：需要 GDELT API 存取
    """
    # 模擬 GDELT 數據（實際需要 API 請求）
    # 實際實作請參考 references/geopolitics-risk.md

    risk_scores = {
        "Chile": {
            "event_count_12m": 45,
            "z_score": 0.3,
            "risk_level": "低"
        },
        "Peru": {
            "event_count_12m": 120,
            "z_score": 1.2,
            "risk_level": "中高"
        },
        "DRC": {
            "event_count_12m": 280,
            "z_score": 2.1,
            "risk_level": "高"
        }
    }

    return risk_scores

geo_risk = compute_geo_risk_gdelt(focus_countries)
```

## Step 7: 計算系統風險分數

```python
def compute_system_risk_score(concentration_result, replacement_result, geo_risk):
    """
    綜合計算系統風險分數

    公式：
    system_risk = concentration_score × (1 + dependency_score) × (1 + geo_risk_weighted)

    各分項：
    - concentration_score: HHI 標準化 (0-100)
    - dependency_score: 1 - replacement_ratio (調整)
    - geo_risk_weighted: 替代國風險加權平均
    """
    # Concentration score (HHI 標準化到 0-100)
    hhi = concentration_result["hhi_latest"]
    concentration_score = min(hhi / 100, 100)  # HHI=10000 → 100

    # Dependency score
    ratio = replacement_result["replacement_ratio"]
    dependency_score = max(1 - ratio, 0)  # ratio < 1 → 有依賴風險

    # Geo risk weighted
    # 按替代國增量比例加權
    total_increment = (replacement_result["Peru"]["expected_increment"] +
                       replacement_result["DRC"]["expected_increment"])
    peru_weight = replacement_result["Peru"]["expected_increment"] / total_increment
    drc_weight = replacement_result["DRC"]["expected_increment"] / total_increment

    geo_risk_weighted = (
        geo_risk["Peru"]["z_score"] * peru_weight +
        geo_risk["DRC"]["z_score"] * drc_weight
    )

    # 綜合分數
    system_risk = concentration_score * (1 + dependency_score) * (1 + geo_risk_weighted * 0.2)
    system_risk = min(system_risk, 100)  # 上限 100

    return {
        "system_risk_score": system_risk,
        "components": {
            "concentration_score": concentration_score,
            "dependency_score": dependency_score,
            "geo_risk_weighted": geo_risk_weighted
        },
        "interpretation": interpret_system_risk(system_risk)
    }

def interpret_system_risk(score):
    if score < 30:
        return "低風險 - 供應鏈相對穩健"
    elif score < 50:
        return "中等風險 - 需關注關鍵國家動態"
    elif score < 70:
        return "高風險 - 建議評估對沖策略"
    else:
        return "極高風險 - 供應中斷可能性顯著"

system_risk = compute_system_risk_score(concentration_result, replacement_result, geo_risk)
```

## Step 8: 生成視覺化圖表

```bash
python scripts/visualize_analysis.py --mode=scenario
```

**生成的圖表**：
1. `copper_demand_supply_gap_YYYYMMDD.png` - 各情境供需缺口
2. `copper_geo_risk_map_YYYYMMDD.png` - 地緣風險熱力圖
3. `copper_system_risk_YYYYMMDD.png` - 系統風險分解

## Step 9: 輸出結果

**JSON 輸出：**

```json
{
  "commodity": "copper",
  "analysis_type": "scenario_analysis",
  "baseline": {
    "year": 2023,
    "production_mt": 22.0,
    "consumption_mt": 22.4
  },
  "supply_constraints": {
    "lead_time_years": 10,
    "supply_ceiling_mt": 24.7,
    "increment_breakdown": {
      "brownfield_expansion": 0.3,
      "under_construction": 0.2,
      "chile_decline": -0.82,
      "peru_increment": 0.52,
      "drc_increment": 0.61
    }
  },
  "scenarios": {
    "base": {
      "demand_cagr": 0.03,
      "final_demand_mt": 29.6,
      "gap_mt": 4.9,
      "gap_pct": 0.223,
      "severity": "嚴重缺口"
    },
    "electrification": {
      "demand_cagr": 0.05,
      "final_demand_mt": 35.8,
      "gap_mt": 11.1,
      "gap_pct": 0.505,
      "severity": "嚴重缺口"
    },
    "slowdown": {
      "demand_cagr": 0.015,
      "final_demand_mt": 25.6,
      "gap_mt": 0.9,
      "gap_pct": 0.041,
      "severity": "小缺口"
    }
  },
  "geo_risk": {
    "Chile": {"z_score": 0.3, "level": "低"},
    "Peru": {"z_score": 1.2, "level": "中高"},
    "DRC": {"z_score": 2.1, "level": "高"}
  },
  "system_risk": {
    "score": 73.5,
    "interpretation": "極高風險 - 供應中斷可能性顯著",
    "components": {
      "concentration_score": 18.2,
      "dependency_score": 0.12,
      "geo_risk_weighted": 1.65
    }
  },
  "generated_at": "2026-01-24"
}
```

**Markdown 報告：**

```markdown
## 銅供需缺口與系統風險情境分析

### 執行摘要

在基準需求情境（CAGR 3%）下，10 年後供需缺口達 {gap_mt:.1f} Mt，
佔當前產量的 {gap_pct:.1%}。考慮集中度、替代依賴與地緣風險後，
系統風險分數為 **{system_risk:.1f}/100**（{interpretation}）。

### 供應約束分析

**供應反應時間約束**：{lead_time} 年

| 增量來源 | 預期增量 | 說明 |
|----------|----------|------|
| 現有產能擴建 | +{brownfield:.2f} Mt | 短期可行 |
| 在建項目 | +{construction:.2f} Mt | 中期釋放 |
| 智利減產 | {chile:.2f} Mt | 結構性趨勢 |
| 秘魯增量 | +{peru:.2f} Mt | 執行風險中 |
| DRC 增量 | +{drc:.2f} Mt | 執行風險高 |
| **淨可行增量** | +{feasible:.2f} Mt | - |
| **供應天花板** | {ceiling:.2f} Mt | 10 年內上限 |

### 情境分析

| 情境 | 需求 CAGR | 10年後需求 | 供需缺口 | 嚴重程度 |
|------|-----------|------------|----------|----------|
| 經濟放緩 | 1.5% | {slow_demand:.1f} Mt | {slow_gap:.1f} Mt | {slow_severity} |
| 基準情境 | 3.0% | {base_demand:.1f} Mt | {base_gap:.1f} Mt | {base_severity} |
| 電氣化加速 | 5.0% | {elec_demand:.1f} Mt | {elec_gap:.1f} Mt | {elec_severity} |

### 地緣風險指數

| 國家 | 事件頻率 Z分數 | 風險等級 |
|------|----------------|----------|
| 智利 | {chile_z:.1f} | {chile_level} |
| 秘魯 | {peru_z:.1f} | {peru_level} |
| DRC | {drc_z:.1f} | {drc_level} |

*數據來源：GDELT 事件資料庫（近 12 個月）*

### 系統風險分數

**綜合分數：{system_risk:.1f}/100**

| 分項 | 分數 | 說明 |
|------|------|------|
| 集中度分數 | {concentration_score:.1f} | HHI 標準化 |
| 依賴度分數 | {dependency_score:.2f} | 1 - replacement_ratio |
| 地緣風險加權 | {geo_weighted:.2f} | 替代國風險加權 |

**解讀**：{interpretation}

### 含義與建議

1. **供應鏈反應慢**：價格上漲不能在短期內解決缺口
2. **決策窗口**：2025-2028 年間的投資決策將決定 2033 年供應
3. **風險集中**：替代供應依賴高風險國家
4. **監控重點**：秘魯勞工動態、DRC 政治穩定性

### 數據來源

- OWID Minerals Explorer（產量）
- USGS MCS（驗證）
- GDELT（地緣事件）
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 建立供需基準
- [ ] 計算多情境需求預測
- [ ] 建模供應約束與天花板
- [ ] 計算各情境供需缺口
- [ ] 計算地緣風險指數（GDELT）
- [ ] 計算綜合系統風險分數
- [ ] 輸出 JSON + Markdown 格式
- [ ] 包含視覺化圖表
</success_criteria>
