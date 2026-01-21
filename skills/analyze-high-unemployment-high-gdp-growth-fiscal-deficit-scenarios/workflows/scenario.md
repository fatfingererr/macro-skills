<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 了解情境推演邏輯
2. references/input-schema.md - 了解情境參數定義
</required_reading>

<objective>
執行自訂失業衝擊情境的財政赤字推演，讓使用者可以：
- 指定失業衝擊的類型、幅度與速度
- 選擇 GDP 路徑假設
- 觀察不同情境下的赤字/GDP 估算區間
</objective>

<process>

<step name="1_define_scenario">
**Step 1: 定義情境參數**

使用者需指定以下情境假設：

```python
scenario = {
    "horizon_quarters": 8,          # 推演期數（4 或 8）
    "gdp_path": "high_gdp_sticky",  # GDP 路徑
    "unemployment_shock": {
        "type": "rate_jump",        # "rate_jump" 或 "level_jump"
        "size": 1.5,                # 失業率 +1.5% 或 失業人數 +150萬
        "speed": "fast"             # "fast"（2季內）或 "gradual"（4-6季）
    }
}
```

**GDP 路徑選項**：
| 選項             | 描述                           |
|------------------|--------------------------------|
| high_gdp_sticky  | GDP 維持高位，僅小幅趨緩       |
| soft_gdp         | GDP 溫和下滑，但仍為正成長     |
| recession_gdp    | GDP 進入負成長                 |

**失業衝擊類型**：
| 類型       | 描述                    | 示例              |
|------------|-------------------------|-------------------|
| rate_jump  | 失業率跳升（百分點）    | size=1.5 → +1.5%  |
| level_jump | 失業人數跳升（萬人）    | size=150 → +150萬 |
</step>

<step name="2_map_to_historical">
**Step 2: 映射到歷史樣本**

根據情境設定，找出歷史上相似的事件：

```python
# 計算衝擊後的預期 slack_metric
if shock_type == "rate_jump":
    projected_ur = current_ur + shock_size
    projected_slack_pctl = estimate_percentile(projected_ur, historical_ur)
elif shock_type == "level_jump":
    projected_unemploy = current_unemploy + shock_size * 10000
    projected_ujo = projected_unemploy / current_jtsjol
    projected_slack_pctl = estimate_percentile(projected_ujo, historical_ujo)

# 篩選符合 GDP 路徑條件的歷史事件
if gdp_path == "high_gdp_sticky":
    condition = (gdp_pctl > 0.70) & (gdp_growth > 0)
elif gdp_path == "soft_gdp":
    condition = (gdp_growth > -1) & (gdp_growth < 2)
elif gdp_path == "recession_gdp":
    condition = (gdp_growth < 0)
```
</step>

<step name="3_compute_projection">
**Step 3: 計算赤字/GDP 投影**

使用選定的模型進行推演：

**event_study_banding**（預設）：
```python
# 找出滿足條件的歷史事件
matching_episodes = filter_episodes(
    all_episodes,
    slack_range=(projected_slack_pctl - 0.1, projected_slack_pctl + 0.1),
    gdp_condition=condition
)

# 計算這些事件後的赤字分布
forward_deficits = get_forward_deficits(matching_episodes, horizon_quarters)
```

**quantile_mapping**：
```python
# 直接使用投影的 slack 分位數進行映射
similar_periods = data[
    (abs(slack_pctl - projected_slack_pctl) < 0.1) &
    condition
]
```

**robust_regression**：
```python
# 使用迴歸模型預測
X_scenario = [projected_slack, gdp_growth_assumption, inflation_assumption]
predicted_deficit = model.predict(X_scenario)
```
</step>

<step name="4_sensitivity_analysis">
**Step 4: 敏感度分析（可選）**

執行多情境比較：

```bash
python scripts/analyzer.py --scenario-sweep \
    --shock-sizes 0.5,1.0,1.5,2.0 \
    --gdp-paths high_gdp_sticky,soft_gdp \
    --output sensitivity.json
```

輸出比較表：
| 失業衝擊 | GDP 路徑        | 赤字/GDP (p50) | 赤字/GDP 區間   |
|----------|-----------------|----------------|-----------------|
| +0.5%    | high_gdp_sticky | 8.5%           | 7.0% - 10.0%    |
| +1.0%    | high_gdp_sticky | 11.0%          | 9.0% - 13.0%    |
| +1.5%    | high_gdp_sticky | 13.5%          | 11.0% - 16.0%   |
| +2.0%    | high_gdp_sticky | 15.0%          | 12.0% - 17.5%   |
</step>

<step name="5_generate_interpretation">
**Step 5: 生成情境解讀**

根據投影結果生成解讀：

```python
interpretation = {
    "macro_story": generate_macro_story(scenario, projection),
    "ust_duration_implications": [
        generate_supply_pressure_analysis(projection),
        generate_risk_aversion_analysis(scenario)
    ],
    "watchlist_switch_indicators": [
        "信用利差/金融壓力指數是否急升（避險力道）",
        "通膨預期是否黏著（長端期限溢酬）",
        "國債拍賣尾差/投標倍數（供給壓力顯性化）"
    ]
}
```
</step>

<step name="6_output">
**Step 6: 輸出結果**

執行情境推演：
```bash
python scripts/analyzer.py \
    --scenario '{"horizon_quarters": 8, "gdp_path": "high_gdp_sticky", "unemployment_shock": {"type": "rate_jump", "size": 1.5, "speed": "fast"}}' \
    --model event_study_banding \
    --output scenario_result.json
```
</step>

</process>

<success_criteria>
情境推演完成時：
- [ ] 情境參數已正確解析
- [ ] 成功映射到歷史樣本（≥3 個事件）
- [ ] 產出赤字/GDP 投影區間
- [ ] 生成情境解讀與 UST 影響分析
- [ ] 輸出包含所有必要欄位
</success_criteria>
