# Workflow: M0/M2 比較分析

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 理解 M0 與 M2 的差異
2. references/input-schema.md - 參數定義
</required_reading>

<process>

## Step 1: 確認比較參數

此工作流程會同時計算 M0 和 M2 兩種口徑的隱含金價：

```python
compare_params = {
    "scenario_date": "today",
    "entities": ["USD", "EUR", "CNY", "JPY", "GBP", "CHF"],
    "aggregates": ["M0", "M2"],           # 固定比較這兩個口徑
    "weighting_method": "fx_turnover",    # 可選擇加權方式
    "fx_base": "USD",
    "output_format": "json"
}
```

## Step 2: 執行雙口徑計算

```bash
python scripts/gold_revaluation.py \
  --compare-aggregates \
  --entities {entities} \
  --weighting {weighting_method} \
  --output comparison.json
```

或使用 Python API：

```python
from scripts.gold_revaluation import compute_gold_anchor_stress

# M0 版本
result_m0 = compute_gold_anchor_stress(
    monetary_aggregate="M0",
    weighting_method="fx_turnover",
    entities=params["entities"]
)

# M2 版本
result_m2 = compute_gold_anchor_stress(
    monetary_aggregate="M2",
    weighting_method="fx_turnover",
    entities=params["entities"]
)
```

## Step 3: 計算比較指標

### 3.1 Headline 比較

```python
comparison = {
    "m0": {
        "headline_implied_price": result_m0["headline"]["implied_gold_price_weighted"],
        "vs_spot_multiple": result_m0["headline"]["implied_gold_price_weighted"] / gold_spot
    },
    "m2": {
        "headline_implied_price": result_m2["headline"]["implied_gold_price_weighted"],
        "vs_spot_multiple": result_m2["headline"]["implied_gold_price_weighted"] / gold_spot
    },
    "credit_multiplier": result_m2["headline"]["implied_gold_price_weighted"] /
                         result_m0["headline"]["implied_gold_price_weighted"]
}
```

### 3.2 各實體比較

```python
entity_comparison = []
for entity in params["entities"]:
    entity_comparison.append({
        "entity": entity,
        "m0_implied_price": result_m0["table"][entity]["implied_gold_price_weighted"],
        "m2_implied_price": result_m2["table"][entity]["implied_gold_price_weighted"],
        "m0_backing_ratio": result_m0["table"][entity]["backing_ratio"],
        "m2_backing_ratio": result_m2["table"][entity]["backing_ratio"],
        "credit_expansion_ratio": result_m2["table"][entity]["money_base"] /
                                  result_m0["table"][entity]["money_base"]
    })
```

## Step 4: 生成比較洞察

```python
insights = [
    {
        "title": "M0 vs M2 差異反映信用乘數",
        "content": f"全體平均信用乘數約 {comparison['credit_multiplier']:.1f} 倍，"
                   f"代表銀行體系的信用擴張程度"
    },
    {
        "title": "使用場景區分",
        "content": "M0 適合評估央行資產負債表壓力；"
                   "M2 適合評估整體金融體系極端壓力"
    },
    {
        "title": "VanEck 的選擇",
        "content": "VanEck '$39k gold' 論點使用 M0 口徑，是相對保守的估計"
    },
    {
        "title": "各國信用擴張程度差異",
        "content": f"信用擴張最大：{max_credit_expansion_entity}；"
                   f"信用擴張最小：{min_credit_expansion_entity}"
    }
]
```

## Step 5: 輸出比較報告

輸出格式包含：

```json
{
  "skill": "usd-reserve-loss-gold-revaluation",
  "mode": "compare_aggregates",
  "scenario_date": "2026-01-07",
  "headline_comparison": {
    "m0": {
      "implied_gold_price": 39210.0,
      "vs_spot_multiple": 19.1
    },
    "m2": {
      "implied_gold_price": 184500.0,
      "vs_spot_multiple": 90.0
    },
    "credit_multiplier": 4.7
  },
  "entity_comparison": [...],
  "insights": [...]
}
```

</process>

<success_criteria>
比較分析完成時應產出：

- [ ] M0 口徑的 Headline 隱含金價
- [ ] M2 口徑的 Headline 隱含金價
- [ ] 兩者倍數比較（信用乘數）
- [ ] 各實體的 M0 vs M2 支撐率比較
- [ ] 各實體的信用擴張比率
- [ ] 比較洞察（至少 3 點）
- [ ] 使用場景建議
</success_criteria>
