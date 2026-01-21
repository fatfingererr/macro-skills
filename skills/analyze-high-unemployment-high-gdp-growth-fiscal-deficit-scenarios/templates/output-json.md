<overview>
本文件定義技能的 JSON 輸出結構，包含所有欄位的說明與範例。
</overview>

<schema>
**完整 JSON 輸出結構**

```json
{
  "skill": "analyze_high_unemployment_fiscal_deficit_scenarios",
  "version": "0.1.0",
  "as_of": "2026-01-21",
  "inputs": {
    "country": "US",
    "lookback_years": 30,
    "frequency": "quarterly",
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
    "model": "event_study_banding"
  },
  "diagnostics": {
    "data_coverage": {
      "start_date": "1996-01-01",
      "end_date": "2026-01-01",
      "series_available": ["UNRATE", "UNEMPLOY", "JTSJOL", "GDP", "FYFSGDA188S"]
    },
    "current_indicators": {
      "unemployment_rate": 4.1,
      "unemployed_level": 6800,
      "job_openings": 9400,
      "ujo_ratio": 0.72,
      "sahm_rule": 0.21,
      "delta_ur_6m": 0.3
    },
    "current_slack_percentile": 0.84,
    "high_gdp_condition": true,
    "gdp_percentile": 0.95,
    "triggered_labor_softening": true,
    "trigger_reasons": ["ujo_above_threshold"]
  },
  "deficit_gdp_projection": {
    "baseline_deficit_gdp": 0.065,
    "conditional_range_next_8q": {
      "p25": 0.11,
      "p50": 0.135,
      "p75": 0.16,
      "min": 0.095,
      "max": 0.175
    },
    "n_episodes": 6,
    "episode_years": ["2001-2003", "2008-2010", "2020-2021", "1990-1991", "1980-1982", "2023-2024"]
  },
  "historical_episodes": [
    {
      "start_date": "2001-03-31",
      "end_date": "2003-06-30",
      "duration_quarters": 9,
      "ujo_at_start": 1.21,
      "sahm_at_start": 0.4,
      "gdp_percentile_at_start": 0.82,
      "deficit_gdp_peak": 0.034,
      "context": "科技泡沫破裂 + 911"
    },
    {
      "start_date": "2008-01-31",
      "end_date": "2010-09-30",
      "duration_quarters": 11,
      "ujo_at_start": 1.45,
      "sahm_at_start": 0.6,
      "gdp_percentile_at_start": 0.78,
      "deficit_gdp_peak": 0.098,
      "context": "全球金融海嘯"
    },
    {
      "start_date": "2020-03-31",
      "end_date": "2021-03-31",
      "duration_quarters": 4,
      "ujo_at_start": 4.60,
      "sahm_at_start": 1.2,
      "gdp_percentile_at_start": 0.91,
      "deficit_gdp_peak": 0.149,
      "context": "COVID-19 財政刺激"
    }
  ],
  "interpretation": {
    "macro_story": "在歷史上勞動市場明顯轉弱且 GDP 仍處高位的樣本中，赤字/GDP 常出現階躍式上移，區間落在約 11%–16%（中位數約 13.5%）。當前勞動市場鬆緊度處於 84 分位（UJO 基準），已觸發轉弱條件，而 GDP 仍處於 95 分位高位。若失業率在未來 2 季快速上升 1.5 百分點，歷史經驗顯示財政赤字可能從當前 6.5% 跳升至 11-16% 區間。",
    "ust_duration_implications": [
      {
        "channel": "supply_pressure",
        "assessment": "高",
        "description": "赤字/GDP 若進入 12%+ 區間，通常意味更高的國債淨發行需求，長端對期限溢酬變化更敏感。以當前 GDP 規模估算，赤字 13.5% 對應約 3.8 兆美元的年度淨發行，較當前增加近一倍。"
      },
      {
        "channel": "risk_aversion",
        "assessment": "中等",
        "description": "若同時出現風險趨避（信用利差擴大、波動上升），長端可能先被避險買盤壓低殖利率；需用風險指標判斷主導力量。當前 VIX 處於正常水準，信用利差穩定，避險力量尚未啟動。"
      }
    ],
    "dominant_force": "目前偏向供給壓力主導，但需持續監控避險指標",
    "watchlist_switch_indicators": [
      "信用利差/金融壓力指數是否急升（避險力道）",
      "通膨預期是否黏著（長端期限溢酬）",
      "國債拍賣尾差/投標倍數（供給壓力顯性化）",
      "Fed 政策立場（QE 暫停/重啟）",
      "股債相關性（轉負表示避險模式）"
    ]
  },
  "metadata": {
    "generated_at": "2026-01-21T10:30:00Z",
    "model_used": "event_study_banding",
    "data_freshness": {
      "UNRATE": "2025-12-31",
      "JTSJOL": "2025-11-30",
      "GDP": "2025-09-30"
    }
  }
}
```
</schema>

<field_descriptions>

<field name="skill">
**skill** (string): 技能識別碼
</field>

<field name="version">
**version** (string): 技能版本號
</field>

<field name="as_of">
**as_of** (string): 分析基準日期 (YYYY-MM-DD)
</field>

<field name="inputs">
**inputs** (object): 輸入參數回顯，方便追溯分析設定
</field>

<field name="diagnostics">
**diagnostics** (object): 診斷資訊

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| data_coverage | object | 數據覆蓋範圍 |
| current_indicators | object | 當前指標數值 |
| current_slack_percentile | float | 當前勞動鬆緊分位數 (0-1) |
| high_gdp_condition | bool | 是否滿足高 GDP 條件 |
| triggered_labor_softening | bool | 是否觸發勞動轉弱 |
| trigger_reasons | array | 觸發原因清單 |
</field>

<field name="deficit_gdp_projection">
**deficit_gdp_projection** (object): 赤字/GDP 投影結果

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| baseline_deficit_gdp | float | 當前基線赤字/GDP |
| conditional_range_next_8q | object | 條件分布區間 (p25/p50/p75/min/max) |
| n_episodes | int | 歷史樣本數量 |
| episode_years | array | 歷史事件年份清單 |
</field>

<field name="historical_episodes">
**historical_episodes** (array): 歷史事件詳細資料

每個事件包含：
| 欄位 | 類型 | 說明 |
|------|------|------|
| start_date | string | 事件起始日期 |
| end_date | string | 事件結束日期 |
| duration_quarters | int | 持續季數 |
| ujo_at_start | float | 起始時 UJO |
| sahm_at_start | float | 起始時 Sahm Rule |
| gdp_percentile_at_start | float | 起始時 GDP 分位數 |
| deficit_gdp_peak | float | 期間赤字/GDP 峰值 |
| context | string | 事件背景說明 |
</field>

<field name="interpretation">
**interpretation** (object): 情境解讀

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| macro_story | string | 宏觀敘事摘要 |
| ust_duration_implications | array | UST 風險通道分析 |
| dominant_force | string | 當前主導力量判斷 |
| watchlist_switch_indicators | array | 監控指標清單 |
</field>

<field name="metadata">
**metadata** (object): 元資料

| 子欄位 | 類型 | 說明 |
|--------|------|------|
| generated_at | string | 報告生成時間 (ISO 8601) |
| model_used | string | 使用的分析模型 |
| data_freshness | object | 各數據系列的最新日期 |
</field>

</field_descriptions>

<quick_output>
**快速診斷輸出（--quick 模式）**

```json
{
  "skill": "analyze_high_unemployment_fiscal_deficit_scenarios",
  "as_of": "2026-01-21",
  "state": {
    "current_slack_percentile": 0.84,
    "high_gdp_condition": true,
    "triggered_labor_softening": true
  },
  "deficit_gdp_projection": {
    "baseline": 0.065,
    "if_labor_softens": {
      "p25": 0.11,
      "p50": 0.135,
      "p75": 0.16
    }
  },
  "ust_risk_level": "elevated",
  "dominant_force": "supply_pressure"
}
```
</quick_output>
