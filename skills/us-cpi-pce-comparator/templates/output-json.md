<template_description>
CPI-PCE 比較分析的 JSON 輸出模板。
此模板定義完整分析結果的結構。
</template_description>

<json_schema>
```json
{
  "metadata": {
    "analysis_time": "ISO 8601 timestamp",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "measure": "yoy | mom_saar | qoq_saar",
    "as_of_date": "YYYY-MM-DD (資料最新日期)"
  },

  "headline": {
    "cpi_headline": "number (CPI YoY %)",
    "pce_headline": "number (PCE YoY %)",
    "headline_gap_bps": "number (PCE - CPI in bps)",
    "cpi_core": "number (Core CPI YoY %)",
    "pce_core": "number (Core PCE YoY %)",
    "core_gap_bps": "number (Core PCE - Core CPI in bps)"
  },

  "low_vol_high_weight_buckets": [
    {
      "bucket": "string (桶位名稱)",
      "volatility": "number (24M 標準差)",
      "weight": "number (PCE 權重)",
      "latest_inflation": "number (最新通膨率)",
      "momentum_3m": "number (3M 動能)",
      "signal": "upside | neutral | downside"
    }
  ],

  "attribution": {
    "top_contributors": [
      {
        "bucket": "string",
        "weight": "number",
        "inflation": "number",
        "contribution": "number (weight * inflation)"
      }
    ],
    "weight_effect_bps": "number (權重效應 in bps)"
  },

  "baseline_adjustment": {
    "baseline_range": "string (e.g., 2018-10-01:2018-12-31)",
    "mode": "subtract_mean | subtract_end",
    "latest_deviation": "number (最新偏離度)"
  },

  "interpretation": [
    "string (解讀文字 1)",
    "string (解讀文字 2)"
  ],

  "caveats": [
    "string (注意事項 1)",
    "string (注意事項 2)"
  ]
}
```
</json_schema>

<example_output>
```json
{
  "metadata": {
    "analysis_time": "2026-01-14T16:57:00.000Z",
    "start_date": "2020-01-01",
    "end_date": "2026-01-01",
    "measure": "yoy",
    "as_of_date": "2025-12-01"
  },
  "headline": {
    "cpi_headline": 2.65,
    "pce_headline": 2.79,
    "headline_gap_bps": 14,
    "cpi_core": 2.65,
    "pce_core": 2.83,
    "core_gap_bps": 18
  },
  "low_vol_high_weight_buckets": [
    {
      "bucket": "pce_services",
      "volatility": 0.42,
      "weight": 0.69,
      "latest_inflation": 3.21,
      "momentum_3m": 0.15,
      "signal": "upside"
    },
    {
      "bucket": "pce_housing",
      "volatility": 0.38,
      "weight": 0.18,
      "latest_inflation": 4.85,
      "momentum_3m": -0.22,
      "signal": "neutral"
    }
  ],
  "attribution": {
    "top_contributors": [
      {"bucket": "pce_services", "weight": 0.69, "inflation": 3.21, "contribution": 2.21},
      {"bucket": "pce_goods", "weight": 0.31, "inflation": 0.58, "contribution": 0.18}
    ],
    "weight_effect_bps": 12
  },
  "baseline_adjustment": {
    "baseline_range": "2018-10-01:2018-12-31",
    "mode": "subtract_mean",
    "latest_deviation": 0.45
  },
  "interpretation": [
    "PCE 通膨高於 CPI 約 14 bps，Fed 關注的通膨指標比 CPI 更具黏性。",
    "低波動高權重桶位 (pce_services) 顯示上行訊號，若趨勢延續將推升 PCE。",
    "監控重點：core_goods 和 core_services_ex_housing 的 3M 動能 vs 12M 趨勢。"
  ],
  "caveats": [
    "權重為近似值，基於 BEA/BLS 2024 年數據",
    "部分桶位對應可能有誤差",
    "此為權重效應的工程近似，非完整 BEA/BLS 方法論調和"
  ]
}
```
</example_output>

<field_descriptions>

<field name="metadata">
分析元資料，包含時間範圍和計算方式。
</field>

<field name="headline">
Headline level 的通膨數據與分歧。
- `headline_gap_bps`: PCE - CPI 的差距（正數表示 PCE 較高）
- `core_gap_bps`: Core PCE - Core CPI 的差距
</field>

<field name="low_vol_high_weight_buckets">
識別出的低波動高權重桶位列表。這些是 PCE 上行風險的關鍵監控點。
- `signal: upside` 表示 3M 動能為正，有上行風險
- `signal: neutral` 表示無明顯方向
</field>

<field name="attribution">
各桶位對總體通膨的貢獻分析。
- `contribution = weight × inflation`
- `weight_effect_bps`: 因 PCE/CPI 權重差異造成的分歧
</field>

<field name="baseline_adjustment">
相對於歷史基準期的偏離度。若 `latest_deviation > 0`，表示當前通膨高於歷史常態。
</field>

<field name="interpretation">
可操作的解讀文字，適合直接用於報告或交易筆記。
</field>

<field name="caveats">
分析的限制與注意事項，務必閱讀。
</field>

</field_descriptions>
