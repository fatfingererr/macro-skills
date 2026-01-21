<overview>
本文件定義技能的完整輸入參數，包含參數類型、預設值、有效範圍與說明。
</overview>

<core_parameters>

<parameter name="country">
**country**
- **類型**: string
- **預設值**: `"US"`
- **有效值**: `["US"]`（目前僅支援美國）
- **說明**: 國家代碼。本技能目前僅支援美國數據，因為所使用的 FRED 系列專屬於美國。
</parameter>

<parameter name="lookback_years">
**lookback_years**
- **類型**: int
- **預設值**: `30`
- **有效範圍**: `10-50`
- **說明**: 回看年數，用於建立歷史分布與識別事件樣本。建議使用 30 年以涵蓋多個經濟週期。

| 設定 | 樣本涵蓋 | 事件數 |
|------|----------|--------|
| 20   | 2006-今  | ~4     |
| 30   | 1996-今  | ~6     |
| 40   | 1986-今  | ~8     |
</parameter>

<parameter name="frequency">
**frequency**
- **類型**: string
- **預設值**: `"quarterly"`
- **有效值**: `["monthly", "quarterly"]`
- **說明**: 分析頻率。季頻較適合財政/GDP 分析，月頻適合勞動指標監控。

**注意**：選擇 `monthly` 時，財政數據會進行插值或使用代理指標。
</parameter>

<parameter name="horizon_quarters">
**horizon_quarters**
- **類型**: int
- **預設值**: `8`
- **有效範圍**: `4-12`
- **說明**: 推演期數（季度）。觀察事件後多少季的赤字/GDP。

| 設定 | 時間範圍 | 適用情境 |
|------|----------|----------|
| 4    | 1 年     | 短期衝擊 |
| 8    | 2 年     | 標準週期 |
| 12   | 3 年     | 長期影響 |
</parameter>

<parameter name="model">
**model**
- **類型**: string
- **預設值**: `"event_study_banding"`
- **有效值**: `["event_study_banding", "quantile_mapping", "robust_regression"]`
- **說明**: 分析模型選擇。

| 模型                | 輸出形式        | 適用情境       |
|---------------------|-----------------|----------------|
| event_study_banding | 區間 + 事件清單 | 預設，最直觀   |
| quantile_mapping    | 條件分布        | 連續型分析     |
| robust_regression   | 預測路徑 + 係數 | 多變數情境推演 |
</parameter>

<parameter name="output_format">
**output_format**
- **類型**: string
- **預設值**: `"json"`
- **有效值**: `["json", "markdown"]`
- **說明**: 輸出格式。JSON 適合程式處理，Markdown 適合報告閱讀。
</parameter>

</core_parameters>

<labor_indicator_set>

<parameter name="use_jolts">
**labor_indicator_set.use_jolts**
- **類型**: bool
- **預設值**: `true`
- **說明**: 是否使用 JOLTS 職缺資料計算 UJO（失業/職缺比）。
- **注意**: JOLTS 從 2001 年開始，設為 false 可用更長歷史但犧牲 UJO 指標。
</parameter>

<parameter name="use_unemployment_rate">
**labor_indicator_set.use_unemployment_rate**
- **類型**: bool
- **預設值**: `true`
- **說明**: 是否使用失業率（UNRATE）計算 薩姆規則 和 ΔUR。
</parameter>

<parameter name="use_unemployed_level">
**labor_indicator_set.use_unemployed_level**
- **類型**: bool
- **預設值**: `true`
- **說明**: 是否使用失業人數（UNEMPLOY）。與 JOLTS 結合計算 UJO。
</parameter>

<parameter name="use_sahm_rule">
**labor_indicator_set.use_sahm_rule**
- **類型**: bool
- **預設值**: `true`
- **說明**: 是否計算 薩姆規則（失業率 3M MA 相對近 12M 低點的上升）。
</parameter>

<parameter name="slack_metric">
**slack_metric**
- **類型**: string
- **預設值**: `"unemployed_to_job_openings_ratio"`
- **有效值**:
  - `"unemployed_to_job_openings_ratio"` - UJO 比率
  - `"unemployment_rate_change"` - ΔUR 半年變化
  - `"sahm_rule"` - 薩姆規則 數值
  - `"composite"` - 加權複合指標
- **說明**: 定義「勞動轉弱」的核心度量方式。

| 指標 | 轉弱門檻  | 特性                 |
|------|-----------|----------------------|
| UJO  | > 80 分位 | 早期預警，對職缺敏感 |
| ΔUR  | > +1.0%   | 中等延遲，直觀       |
| Sahm | ≥ 0.5     | 確認型，準確度高     |
</parameter>

</labor_indicator_set>

<scenario_parameters>

<parameter name="gdp_path">
**scenario.gdp_path**
- **類型**: string
- **預設值**: `"high_gdp_sticky"`
- **有效值**: `["high_gdp_sticky", "soft_gdp", "recession_gdp"]`
- **說明**: GDP 路徑假設。

| 路徑            | GDP 分位數 | GDP 成長  | 說明           |
|-----------------|------------|-----------|----------------|
| high_gdp_sticky | > 70%      | > 0%      | GDP 維持高位   |
| soft_gdp        | 50-70%     | -1% ~ +2% | GDP 溫和趨緩   |
| recession_gdp   | < 50%      | < 0%      | GDP 進入負成長 |
</parameter>

<parameter name="unemployment_shock">
**scenario.unemployment_shock**
- **類型**: object
- **預設值**: `{"type": "rate_jump", "size": 1.5, "speed": "fast"}`
- **說明**: 失業衝擊設定。

**子參數**：

| 參數  | 類型   | 有效值                        | 說明     |
|-------|--------|-------------------------------|----------|
| type  | string | `"rate_jump"`, `"level_jump"` | 衝擊類型 |
| size  | float  | 0.5-5.0                       | 衝擊幅度 |
| speed | string | `"fast"`, `"gradual"`         | 衝擊速度 |

**衝擊幅度解讀**：
- `type: "rate_jump"` + `size: 1.5` → 失業率上升 1.5 百分點
- `type: "level_jump"` + `size: 150` → 失業人數上升 150 萬人

**衝擊速度**：
- `fast` → 2 季內達到
- `gradual` → 4-6 季逐步達到
</parameter>

</scenario_parameters>

<threshold_parameters>

<parameter name="high_gdp_percentile_threshold">
**high_gdp_percentile_threshold**
- **類型**: float
- **預設值**: `0.70`
- **有效範圍**: `0.5-0.9`
- **說明**: 定義「高 GDP」的分位數門檻。GDP 水平高於此分位數視為高位。
</parameter>

<parameter name="labor_soft_percentile_threshold">
**labor_soft_percentile_threshold**
- **類型**: float
- **預設值**: `0.80`
- **有效範圍**: `0.6-0.95`
- **說明**: 定義「勞動轉弱」的分位數門檻（針對 UJO）。UJO 高於此分位數視為轉弱。
</parameter>

<parameter name="sahm_threshold">
**sahm_threshold**
- **類型**: float
- **預設值**: `0.5`
- **有效範圍**: `0.3-1.0`
- **說明**: 薩姆規則 觸發門檻。經典門檻為 0.5，可調低以更早預警。
</parameter>

<parameter name="delta_ur_threshold">
**delta_ur_threshold**
- **類型**: float
- **預設值**: `1.0`
- **有效範圍**: `0.5-2.0`
- **說明**: ΔUR（6M 變化）觸發門檻。失業率半年上升超過此值視為快速惡化。
</parameter>

</threshold_parameters>

<complete_example>
**完整參數範例**

```json
{
  "country": "US",
  "lookback_years": 30,
  "frequency": "quarterly",
  "labor_indicator_set": {
    "use_jolts": true,
    "use_unemployment_rate": true,
    "use_unemployed_level": true,
    "use_sahm_rule": true
  },
  "slack_metric": "unemployed_to_job_openings_ratio",
  "scenario": {
    "horizon_quarters": 8,
    "gdp_path": "high_gdp_sticky",
    "unemployment_shock": {
      "type": "rate_jump",
      "size": 1.5,
      "speed": "fast"
    }
  },
  "model": "event_study_banding",
  "output_format": "json",
  "thresholds": {
    "high_gdp_percentile": 0.70,
    "labor_soft_percentile": 0.80,
    "sahm_threshold": 0.5,
    "delta_ur_threshold": 1.0
  }
}
```
</complete_example>

<cli_usage>
**命令列使用範例**

```bash
# 快速診斷（使用所有預設值）
python scripts/analyzer.py --quick

# 完整分析
python scripts/analyzer.py \
    --lookback 30 \
    --horizon 8 \
    --model event_study_banding \
    --output result.json

# 自訂情境
python scripts/analyzer.py \
    --scenario '{"horizon_quarters": 8, "gdp_path": "high_gdp_sticky", "unemployment_shock": {"type": "rate_jump", "size": 1.5, "speed": "fast"}}' \
    --output scenario_result.json

# Markdown 報告輸出
python scripts/analyzer.py --quick --format markdown --output report.md
```
</cli_usage>
