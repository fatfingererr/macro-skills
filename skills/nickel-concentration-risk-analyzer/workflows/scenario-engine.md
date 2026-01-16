# Workflow: 政策情境衝擊模擬

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/concentration-metrics.md
3. references/unit-conversion.md
4. references/indonesia-supply-structure.md
</required_reading>

<process>
## Step 1: 收集情境參數

收集或確認政策情境定義：

```yaml
policy_scenarios:
  - name: "ID_RKAB_cut_2026"
    target_country: "Indonesia"
    policy_variable: "ore_quota_RKAB"  # ore_quota_RKAB | mine_permit | export_rule | smelter_capacity
    cut_type: "pct_country"  # pct_global | pct_country | absolute
    cut_value: 0.20  # 減產 20%
    start_year: 2026
    end_year: 2026
    execution_prob: 0.5  # 執行機率

baseline:
  indonesia_prod_2024: 2280000  # tonnes Ni content (S&P 口徑)
  global_prod_2024: 3780000     # tonnes Ni content (estimated)
  indonesia_share: 0.602
```

**若用戶只說「減產 20%」**：
- 詢問是減產國內產量的 20%（pct_country）還是全球的 20%（pct_global）
- 預設使用 pct_country
- 預設 execution_prob = 0.5

## Step 2: 口徑警告檢查

**關鍵檢查**：政策配額通常以 ore quota（礦石配額）表述，而非 nickel content。

```python
def check_unit_alignment(scenario):
    warnings = []

    # RKAB 配額通常是 ore wet tonnes
    if scenario.policy_variable == "ore_quota_RKAB":
        warnings.append({
            "type": "unit_mismatch",
            "message": "RKAB ore quota 通常以 ore wet tonnes 計算，非 nickel content",
            "impact": "若直接套用百分比到 nickel content，可能低估實際衝擊",
            "recommendation": "建議使用 assay_grade 轉換，或明確標註口徑假設"
        })

    return warnings
```

**輸出警告範例**：
```
⚠️ 口徑警告：RKAB 配額（ore_quota_wet_tonnes）與分析口徑（nickel_content）不同
   - 2026 配額 250 Mt vs 2025 目標 379 Mt 是「濕噸」非鎳含量
   - 若品位 1.5%，250 Mt ore ≈ 3.75 Mt Ni content
```

## Step 3: 計算衝擊量

使用 scripts/scenario_impact.py 或以下邏輯：

```python
def calculate_scenario_impact(scenario, baseline):
    """
    計算政策情境對全球供給的衝擊
    """
    # 確定減產基數
    if scenario.cut_type == "pct_country":
        base = baseline.country_prod  # e.g., 2.28 Mt for Indonesia
        cut_amount = base * scenario.cut_value
    elif scenario.cut_type == "pct_global":
        base = baseline.global_prod  # e.g., 3.78 Mt global
        cut_amount = base * scenario.cut_value
    elif scenario.cut_type == "absolute":
        cut_amount = scenario.cut_value  # 直接指定數量

    # 計算三層情境
    results = {
        "hard_cut": {
            "name": "完全執行",
            "execution_rate": 1.0,
            "cut_amount": cut_amount,
            "global_hit_pct": cut_amount / baseline.global_prod,
            "description": "政策 100% 落地"
        },
        "half_success": {
            "name": "半成功",
            "execution_rate": scenario.execution_prob,
            "cut_amount": cut_amount * scenario.execution_prob,
            "global_hit_pct": (cut_amount * scenario.execution_prob) / baseline.global_prod,
            "description": f"執行 {scenario.execution_prob:.0%}"
        },
        "soft_landing": {
            "name": "軟著陸",
            "execution_rate": 0.25,
            "cut_amount": cut_amount * 0.25,
            "global_hit_pct": (cut_amount * 0.25) / baseline.global_prod,
            "description": "只延遲新增產能/部分執行"
        }
    }

    return results
```

## Step 4: 敏感度分析

計算不同執行率下的衝擊：

| 執行率 | 減產量 (kt Ni) | 全球衝擊 (%) | 敘事 |
|--------|----------------|--------------|------|
| 100% | 456 | 12.1% | Hard cut |
| 75% | 342 | 9.0% | |
| 50% | 228 | 6.0% | Half success |
| 25% | 114 | 3.0% | Soft landing |
| 0% | 0 | 0% | 空頭支票 |

## Step 5: 情境組合分析（若有多個情境）

若用戶提供多個情境，計算聯合衝擊：

```python
def combined_impact(scenarios, baseline):
    """
    假設情境獨立，計算聯合期望衝擊
    """
    total_expected_cut = 0
    for sc in scenarios:
        result = calculate_scenario_impact(sc, baseline)
        total_expected_cut += result["half_success"]["cut_amount"]

    return {
        "combined_expected_cut": total_expected_cut,
        "combined_global_hit_pct": total_expected_cut / baseline.global_prod
    }
```

## Step 6: 生成輸出

**JSON 輸出結構：**

```json
{
  "commodity": "nickel",
  "asof_date": "2026-01-16",
  "scope": {
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "baseline": {
    "indonesia_prod_2024": 2280000,
    "global_prod_2024": 3780000,
    "indonesia_share": 0.602
  },
  "scenarios": [
    {
      "name": "ID_RKAB_cut_2026",
      "target_country": "Indonesia",
      "policy_variable": "ore_quota_RKAB",
      "cut_type": "pct_country",
      "cut_value": 0.20,
      "execution_prob": 0.5,
      "results": {
        "hard_cut": {
          "cut_amount_kt": 456,
          "global_hit_pct": 0.121
        },
        "half_success": {
          "cut_amount_kt": 228,
          "global_hit_pct": 0.060
        },
        "soft_landing": {
          "cut_amount_kt": 114,
          "global_hit_pct": 0.030
        }
      }
    }
  ],
  "unit_warnings": [
    {
      "type": "unit_mismatch",
      "message": "RKAB ore quota 通常以 ore wet tonnes 計算"
    }
  ],
  "assumptions": [
    "execution_prob = 0.5",
    "cut_type = pct_country (印尼產量的 20%)",
    "baseline 使用 S&P Global 2024 數據"
  ]
}
```

**Markdown 報告結構：**

```markdown
## 政策情境衝擊分析

**情境名稱**: ID_RKAB_cut_2026
**目標國家**: Indonesia
**政策變數**: RKAB 礦石配額
**減產幅度**: 印尼產量的 20%

### 衝擊分析

| 情境 | 執行率 | 減產量 | 全球衝擊 |
|------|--------|--------|----------|
| Hard cut | 100% | 456 kt | 12.1% |
| Half success | 50% | 228 kt | 6.0% |
| Soft landing | 25% | 114 kt | 3.0% |

### 關鍵發現

- 即使只有「半成功」執行，印尼減產對全球供給仍有 **6%** 衝擊
- 這相當於全球約 2-3 週的消費量
- 對價格的影響可能是非對稱的（上行風險大於下行）

### 口徑警告

⚠️ **RKAB 配額口徑注意**：
- RKAB 配額以「ore wet tonnes」計算
- 本分析假設直接換算為 nickel content
- 若礦石品位 (Ni%) 有顯著變化，衝擊量需調整

### 假設說明

1. Baseline 使用 S&P Global 2024 數據
2. 執行機率預設 50%（政策不需完美執行）
3. 減產為印尼產量的百分比（非全球）
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 情境參數完整定義
- [ ] 輸出三層情境（hard/half/soft）
- [ ] 包含口徑警告（若適用）
- [ ] 敏感度分析表格
- [ ] JSON + Markdown 輸出
- [ ] 假設清楚說明
- [ ] 對價格影響的定性敘述
</success_criteria>
