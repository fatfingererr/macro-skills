# Workflow: Full Analysis（完整供需×價格×傳導整合分析）

<required_reading>
**Read these reference files NOW:**
1. references/data-sources.md
2. references/supply-chain-mapping.md
3. references/price-methodology.md
4. references/etf-holdings-structure.md
5. references/failure-modes.md
</required_reading>

<process>
## Step 1: Initialize Parameters

解析輸入參數並設定預設值：

```python
params = {
    "etf_ticker": args.get("etf_ticker", "LIT"),
    "lookback_years": args.get("lookback_years", 10),
    "price_freq": args.get("price_freq", "weekly"),
    "region_focus": args.get("region_focus", ["China", "Australia", "Chile", "Argentina"]),
    "chem_focus": args.get("chem_focus", "both"),
    "data_level": args.get("data_level", "free_nolimit"),
    "output_format": args.get("output_format", "markdown")
}
```

## Step 2: Load Data Layers

### 2.1 ETF Exposure Layer

```python
# ETF 價格
lit_px = load_price(params["etf_ticker"], years=params["lookback_years"], freq=params["price_freq"])

# Holdings (從 Global X factsheet)
holdings = load_lit_holdings_from_factsheet()
# 輸出: {ticker, weight, segment: upstream/midstream/downstream, country}
```

### 2.2 Lithium Data Layer

根據 `data_level` 載入對應數據源：

```python
# 供給數據
usgs_supply = load_usgs_lithium_world_production()   # Tier 0: 年度基準
aus_req = load_australia_req_lithium_outlook()       # Tier 0: 季度更新
abs_exports = load_abs_lithium_exports()             # Tier 0: 出口量

# 需求數據
iea_battery = load_iea_battery_demand_proxy()        # Tier 0: GWh 需求

# 價格數據 (根據 data_level 選擇)
li_price = load_lithium_price_series(
    data_level=params["data_level"],
    chem=params["chem_focus"],
    providers=["fastmarkets", "smm", "cme_fallback"]
)
```

## Step 3: Compute Middle Layers

### 3.1 Balance Nowcast

```python
# 供給 proxy
supply_proxy = blend_supply(usgs_supply, aus_req, abs_exports)

# 需求 proxy (三情境)
demand_scenarios = build_demand_proxy(
    iea_battery,
    scenario_kgs_per_kwh=[0.12, 0.15, 0.18]  # 保守/中性/積極
)

# 平衡指數
balance_index = {
    "conservative": zscore(demand_scenarios["conservative"] - supply_proxy),
    "neutral": zscore(demand_scenarios["neutral"] - supply_proxy),
    "aggressive": zscore(demand_scenarios["aggressive"] - supply_proxy)
}
```

### 3.2 Price Regime

```python
price_regime = classify_regime(li_price)

# 輸出結構
# {
#   "carbonate": {
#       "regime": "bottoming",
#       "roc_12w": -2.3,
#       "roc_26w": -8.5,
#       "slope": -0.12,
#       "volatility": 4.2,
#       "mean_deviation": -12
#   },
#   "hydroxide": {...}
# }
```

### 3.3 ETF Transmission

```python
# 因子對齊
factor_df = align_factors(lit_px, li_price, demand_proxy)

# Rolling beta
beta_map = rolling_multifactor_beta(
    etf_returns=lit_px["ret"],
    factors=factor_df,
    window=52  # 52 週滾動
)

# 傳導狀態判斷
transmission_status = assess_transmission(beta_map)
# "normal" | "weakening" | "broken"
```

## Step 4: Generate Insights

### 4.1 Thesis Dashboard

```python
thesis = compute_thesis(
    balance_index=balance_index["neutral"],
    price_regime=price_regime,
    transmission=beta_map
)

# 輸出: "bullish" | "neutral" | "bearish" | "neutral_bullish" | "neutral_bearish"
```

### 4.2 Catalyst Map

識別近期/即將發生的催化劑：

```python
catalysts = [
    {"event": "IEA EV Outlook Release", "expected_date": "2026-04", "direction": "positive/negative/neutral"},
    {"event": "Australia REQ Update", "expected_date": "2026-Q1", "direction": "..."},
    {"event": "Chile Lithium Policy", "expected_date": "TBD", "direction": "..."}
]
```

### 4.3 Targets & Path

```python
targets = derive_weekly_targets(lit_px)

# 輸出:
# {
#   "mid_channel": 48.50,
#   "prior_high": 56.20,
#   "upper_channel": 68.00,
#   "support": 38.50
# }
```

### 4.4 Invalidation Rules

```python
invalidation = build_invalidation_rules(
    lit_px=lit_px,
    balance_index=balance_index,
    price_regime=price_regime,
    beta_map=beta_map
)

# 輸出:
# [
#   {"condition": "price < 38.50", "description": "跌破關鍵支撐"},
#   {"condition": "balance_index < 0", "description": "供需平衡轉負"},
#   {"condition": "regime == downtrend", "description": "價格型態轉弱"},
#   {"condition": "beta_li < 0.3 for 8w", "description": "傳導斷裂"}
# ]
```

## Step 5: Format Output

根據 `output_format` 生成報告：

```python
if params["output_format"] == "markdown":
    report = format_markdown_report(
        thesis=thesis,
        balance_index=balance_index,
        price_regime=price_regime,
        beta_map=beta_map,
        holdings=holdings,
        targets=targets,
        invalidation=invalidation,
        catalysts=catalysts
    )
elif params["output_format"] == "json":
    report = format_json_output(...)
```

## Step 6: Generate Visualizations

**強制執行**：每次完整分析都必須生成視覺化圖表

### 6.1 生成綜合儀表板

```python
# 生成完整儀表板（包含所有關鍵圖表）
from scripts.visualize_analysis import generate_comprehensive_dashboard

dashboard_path = generate_comprehensive_dashboard(
    output_dir='output',
    asof_date=params['asof_date']
)

# 輸出檔案：output/lithium_analysis_YYYY-MM-DD.png
```

**儀表板內容**：
1. 投資論述摘要（Thesis + Confidence + 關鍵指標）
2. 供需平衡演變圖（2024-2026，含缺口）
3. 供需平衡指數（三情境：保守/中性/積極）
4. 碳酸鋰價格走勢（歷史價格 + 市況型態）
5. ETF 傳導敏感度分析（Beta to 鋰價/EV需求）
6. LIT ETF 目標路徑（支撐/目標/上軌）

**技術規格**：
- 解析度：300 DPI（高畫質輸出）
- 格式：PNG
- 尺寸：18" × 12"（適合報告與簡報）
- 中文支持：自動配置中文字體
- 檔名格式：`lithium_analysis_YYYY-MM-DD.png`

### 6.2 生成拐點分析圖表

```python
# 生成拐點分析專用圖表
from scripts.inflection_point_chart import generate_inflection_point_chart

inflection_chart_path = generate_inflection_point_chart(
    output_dir='output',
    asof_date=params['asof_date']
)

# 輸出檔案：output/lithium_inflection_analysis_YYYY-MM-DD.png
```

**拐點圖表內容**：
1. 供需平衡指數演變（2020-2027）
   - 歷史數據（2020-2025）
   - 未來預測（2026-2027，含三情境區間）
2. 碳酸鋰價格走勢（歷史 + 預測）
3. 關鍵拐點標註
   - ⭐ 歷史拐點：2023Q2（供給反超需求）
   - ⭐ 預期拐點：2026Q4（中性情境）
   - 🔵 當前位置標記
4. 市場階段背景色塊
   - 需求缺口期 vs 供給過剩期 vs 預期反彈期
5. 關鍵催化劑時間軸

**技術規格**：
- 解析度：300 DPI
- 格式：PNG
- 尺寸：16" × 12"
- 中文支持：自動配置中文字體
- 檔名格式：`lithium_inflection_analysis_YYYY-MM-DD.png`
</process>

<output_template>
**Markdown 輸出骨架：**

```markdown
# LIT（鋰產業鏈 ETF）供需×價格×傳導整合評估

## 1) 數據源摘要（本次使用）
- 供給基準：[來源列表]
- 需求 proxy：[來源列表]
- 價格：[來源列表]
- ETF 暴露：[來源列表]
- 數據等級：[free_nolimit/free_limit/paid_low/paid_high]

## 2) 供需平衡 Nowcast
- Balance Index：[值]（上行/下行；是否出現拐點）
- 主要驅動：[需求/供給]
- 三情境：
  - 保守：[值]
  - 中性：[值]
  - 積極：[值]

## 3) 價格型態（Regime）
- 碳酸鋰：[downtrend/bottoming/uptrend/overheat]
- 氫氧化鋰：[...]
- 關鍵指標：
  - 12週動能：[值]
  - 波動率：[值]

## 4) 鋰→股票→ETF 傳導
- ETF 對鋰價因子 beta：[值]（上升=傳導恢復）
- ETF 對需求因子 beta：[值]
- 傳導狀態：[normal/weakening/broken]

## 5) 結論與路徑
- Thesis：[bullish/neutral/bearish]
- 目標路徑：
  - 中軌：[價格]
  - 前高：[價格]
  - 上軌：[價格]
- 失效條件：
  - [條件1]
  - [條件2]
  - [條件3]

## 6) 催化劑地圖
| 事件 | 預期時間 | 方向 |
|------|----------|------|
| ...  | ...      | ...  |

## 7) 數據來源追溯
| 指標 | 來源 | 更新頻率 | 置信度 |
|------|------|----------|--------|
| ...  | ...  | ...      | ...    |
```
</output_template>

<success_criteria>
此工作流程完成時：
- [ ] 三個中介層（Balance/Regime/Transmission）都已計算
- [ ] Thesis 判斷明確（含依據）
- [ ] 目標路徑已標註（技術位）
- [ ] 失效條件完整（供給/需求/市場端）
- [ ] 數據來源可追溯
- [ ] 輸出格式正確（markdown/json）
- [ ] **綜合儀表板已生成**（`output/lithium_analysis_YYYY-MM-DD.png`）
- [ ] **拐點分析圖表已生成**（`output/lithium_inflection_analysis_YYYY-MM-DD.png`）
- [ ] **報告與圖表檔名日期一致**
- [ ] **拐點判斷包含歷史與預期拐點**
</success_criteria>
