# Workflow: Balance Nowcast（供需平衡即時估計）

<required_reading>
**Read these reference files NOW:**
1. references/data-sources.md
2. references/supply-chain-mapping.md
3. references/unit-conversion.md
</required_reading>

<process>
## Step 1: Load Supply Data

從各來源載入供給數據：

### 1.1 USGS（年度基準）

```python
usgs_data = load_usgs_lithium()

# 產出結構
# {
#   "world_production": {2020: 82, 2021: 107, 2022: 130, 2023: 180, 2024: 220},  # kt LCE
#   "by_country": {
#     "Australia": {...},
#     "Chile": {...},
#     "China": {...},
#     "Argentina": {...}
#   },
#   "unit": "kt_LCE",
#   "source_id": "USGS",
#   "confidence": 0.95
# }
```

### 1.2 Australia REQ（季度展望）

```python
aus_req = load_australia_req()

# 產出結構
# {
#   "lithium_exports": {...},  # 出口量/金額
#   "production_outlook": {...},  # 產量展望
#   "quarterly_update": "2025-Q4",
#   "source_id": "AU_REQ",
#   "confidence": 0.90
# }
```

### 1.3 ABS Exports（出口統計）

```python
abs_exports = load_abs_lithium_exports()

# 產出結構
# {
#   "export_value_aud": {...},  # 出口金額
#   "export_volume": {...},  # 出口量（如可得）
#   "monthly": True,
#   "source_id": "ABS",
#   "confidence": 0.90
# }
```

## Step 2: Load Demand Data

### 2.1 IEA EV/Battery Demand

```python
iea_data = load_iea_ev_outlook()

# 產出結構
# {
#   "ev_sales": {2020: 3.1, 2021: 6.5, 2022: 10.6, 2023: 14.2, 2024: 17.5},  # million units
#   "battery_demand_gwh": {2020: 150, 2021: 330, 2022: 550, 2023: 750, 2024: 1000},
#   "lithium_demand_by_battery": {...},  # IEA 自己的估計（如有）
#   "source_id": "IEA",
#   "confidence": 0.90
# }
```

## Step 3: Build Supply Proxy

整合供給數據成單一 proxy：

```python
def blend_supply(usgs, aus_req, abs_exports):
    """
    策略：
    1. 以 USGS 年度數據為基準
    2. 用 AUS REQ 季度更新調整當年估計
    3. 用 ABS 月度出口驗證趨勢
    """

    # 年度基準
    supply_annual = usgs["world_production"]

    # 季度調整（如果 REQ 有更新預測）
    if aus_req["quarterly_update"] >= current_quarter:
        supply_annual = adjust_with_req(supply_annual, aus_req)

    # 趨勢驗證（用出口數據）
    trend_confirmation = validate_with_exports(supply_annual, abs_exports)

    return {
        "values": supply_annual,
        "unit": "kt_LCE",
        "trend": trend_confirmation,
        "confidence": min(usgs["confidence"], aus_req["confidence"])
    }
```

## Step 4: Build Demand Proxy

將電池需求轉換為鋰需求（三情境）：

```python
def build_demand_proxy(iea_data, kg_per_kwh_scenarios=[0.12, 0.15, 0.18]):
    """
    轉換公式: Li demand (kt) = Battery (GWh) × kg/kWh
    """

    battery_gwh = iea_data["battery_demand_gwh"]

    demand_scenarios = {}
    for i, kg_kwh in enumerate(kg_per_kwh_scenarios):
        scenario_name = ["conservative", "neutral", "aggressive"][i]
        demand_scenarios[scenario_name] = {
            year: gwh * kg_kwh for year, gwh in battery_gwh.items()
        }

    return {
        "scenarios": demand_scenarios,
        "unit": "kt_LCE",
        "assumptions": {
            "conservative": {"kg_per_kwh": 0.12, "rationale": "LFP 佔比上升"},
            "neutral": {"kg_per_kwh": 0.15, "rationale": "混合 NMC/LFP"},
            "aggressive": {"kg_per_kwh": 0.18, "rationale": "高鎳 NMC 主導"}
        },
        "source_id": "IEA_derived",
        "confidence": 0.85
    }
```

## Step 5: Compute Balance Index

```python
def compute_balance_index(supply_proxy, demand_proxy):
    """
    Balance Index = zscore(demand - supply)

    解讀：
    - > 0: 需求 > 供給，缺口擴大
    - < 0: 供給 > 需求，過剩
    - 趨勢變化比絕對值更重要
    """

    results = {}
    for scenario in ["conservative", "neutral", "aggressive"]:
        demand = demand_proxy["scenarios"][scenario]
        supply = supply_proxy["values"]

        # 計算年度缺口
        gap = {year: demand.get(year, 0) - supply.get(year, 0)
               for year in set(demand.keys()) | set(supply.keys())}

        # Z-score 標準化
        gap_values = list(gap.values())
        zscore = (gap_values[-1] - np.mean(gap_values)) / np.std(gap_values)

        results[scenario] = {
            "balance_index": zscore,
            "raw_gap_kt": gap,
            "latest_year": max(gap.keys()),
            "trend": "widening" if zscore > 0 else "narrowing"
        }

    return results
```

## Step 6: Assess Inflection Points

判斷是否出現拐點：

```python
def detect_inflection(balance_index_history):
    """
    拐點判斷條件：
    1. 連續 3 期同方向後反轉
    2. 變化幅度超過 0.5 標準差
    """

    # 檢查方向變化
    recent = balance_index_history[-4:]

    if len(recent) < 4:
        return {"inflection": False, "reason": "數據不足"}

    prev_direction = np.sign(recent[-2] - recent[-3])
    curr_direction = np.sign(recent[-1] - recent[-2])

    if prev_direction != curr_direction and abs(recent[-1] - recent[-2]) > 0.5:
        return {
            "inflection": True,
            "type": "bullish" if curr_direction > 0 else "bearish",
            "magnitude": abs(recent[-1] - recent[-2])
        }

    return {"inflection": False, "reason": "無明顯反轉"}
```

## Step 7: Format Output

```python
def format_balance_report(balance_results, inflection, supply_proxy, demand_proxy):
    return {
        "asof_date": date.today().isoformat(),
        "balance_index": {
            "conservative": balance_results["conservative"]["balance_index"],
            "neutral": balance_results["neutral"]["balance_index"],
            "aggressive": balance_results["aggressive"]["balance_index"]
        },
        "trend": balance_results["neutral"]["trend"],
        "inflection": inflection,
        "supply_summary": {
            "latest_value": supply_proxy["values"][max(supply_proxy["values"].keys())],
            "unit": supply_proxy["unit"],
            "sources": ["USGS", "AU_REQ", "ABS"]
        },
        "demand_summary": {
            "scenarios": demand_proxy["assumptions"],
            "sources": ["IEA"]
        },
        "interpretation": generate_interpretation(balance_results, inflection)
    }
```

## Step 8: Generate Inflection Point Chart

**強制執行**：每次 Balance Nowcast 都必須生成拐點分析視覺化圖表

```python
# 生成拐點分析圖表
from scripts.inflection_point_chart import generate_inflection_point_chart

chart_path = generate_inflection_point_chart(
    output_dir='output',
    asof_date=date.today().strftime("%Y-%m-%d")
)

# 輸出檔案：output/lithium_inflection_analysis_YYYY-MM-DD.png
```

**圖表內容**：
1. 供需平衡指數演變（2020-2027）
   - 歷史數據（實線）
   - 未來預測（虛線，含三情境區間）
2. 碳酸鋰價格走勢
   - 歷史價格
   - 預測價格
3. 關鍵拐點標註
   - 歷史拐點：2023Q2（供給反超需求）
   - 預期拐點：2026Q4（中性情境）
   - 當前位置
4. 市場階段背景色塊
   - 綠色：需求缺口期（2020-2023Q2）
   - 紅色：供給過剩期（2023Q2-2025Q4）
   - 黃色：預期反彈期（2026Q3+）
5. 關鍵催化劑時間軸
   - IEA EV Outlook、澳洲REQ更新等

**技術規格**：
- 解析度：300 DPI
- 格式：PNG
- 尺寸：16" × 12"
- 中文支持：自動配置中文字體
- 檔名格式：`lithium_inflection_analysis_YYYY-MM-DD.png`
</process>

<output_template>
**Markdown 輸出：**

```markdown
# 鋰供需平衡 Nowcast 報告

## 分析日期: [YYYY-MM-DD]
## 數據來源: USGS + IEA + Australia REQ/ABS

---
## Balance Index

| 情境 | Balance Index | 判讀 |
|------|---------------|------|
| 保守 | [值] | [缺口擴大/縮小] |
| 中性 | [值] | [缺口擴大/縮小] |
| 積極 | [值] | [缺口擴大/縮小] |

## 拐點判斷
- 是否出現拐點：[是/否]
- 類型：[bullish/bearish/none]
- 依據：[說明]

## 供給側摘要
| 年份 | 全球產量 (kt LCE) | YoY |
|------|-------------------|-----|
| ... | ... | ... |

## 需求側摘要
| 年份 | 電池需求 (GWh) | 鋰需求 (kt) | 假設 |
|------|----------------|-------------|------|
| ... | ... | ... | ... |

## 關鍵發現
1. [發現1]
2. [發現2]
3. [發現3]

## 數據來源
| 指標 | 來源 | 更新頻率 | 置信度 |
|------|------|----------|--------|
| ... | ... | ... | ... |
```
</output_template>

<success_criteria>
此工作流程完成時：
- [ ] 供給數據從至少兩個來源整合
- [ ] 需求 proxy 輸出三個情境
- [ ] Balance Index 計算正確
- [ ] 拐點判斷有明確條件
- [ ] 單位轉換假設已標註
- [ ] 數據來源可追溯
</success_criteria>
