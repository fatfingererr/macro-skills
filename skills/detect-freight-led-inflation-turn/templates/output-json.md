<template_description>
CASS Freight Index 週期轉折分析的 JSON 輸出模板。
此模板定義完整分析結果的結構。
</template_description>

<json_schema>
```json
{
  "metadata": {
    "analysis_time": "ISO 8601 timestamp",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "indicator": "shipments_yoy | expenditures_yoy | shipments_index | expenditures_index",
    "lead_months": "integer",
    "as_of_date": "YYYY-MM-DD (資料最新日期)"
  },

  "freight_status": {
    "indicator": "string (如 shipments_yoy)",
    "series_name": "string (如 CASS Shipments YoY)",
    "latest_value": "number (最新值)",
    "yoy": "number (年增率 % - 若使用 YoY 指標則與 latest_value 相同)",
    "yoy_3m_avg": "number (3 個月平均 %)",
    "cycle_status": "new_cycle_low | negative | positive",
    "is_new_cycle_low": "boolean",
    "cycle_low_window": "integer (回看月數)",
    "consecutive_negative_months": "integer (連續負值月數)"
  },

  "all_indicators": {
    "shipments_index": {
      "latest_value": "number",
      "status": "string"
    },
    "expenditures_index": {
      "latest_value": "number",
      "status": "string"
    },
    "shipments_yoy": {
      "latest_value": "number",
      "status": "string"
    },
    "expenditures_yoy": {
      "latest_value": "number",
      "status": "string"
    }
  },

  "cpi_status": {
    "latest_yoy": "number (CPI YoY %)",
    "yoy_3m_avg": "number (3 個月平均 CPI YoY %)",
    "trend": "rising | falling | stable"
  },

  "lead_alignment": {
    "correlation": "number (CASS 領先 vs CPI 相關係數)",
    "lead_months": "integer (使用的領先月數)",
    "optimal_lead": "integer (最佳領先月數)",
    "alignment_quality": "high | medium | low"
  },

  "signal_assessment": {
    "signal": "inflation_easing | inflation_rising | neutral",
    "confidence": "high | medium | low",
    "macro_implication": "string (宏觀含義)"
  },

  "historical_positioning": {
    "current_percentile": "number (當前 YoY 在歷史中的百分位)",
    "similar_periods": ["YYYY-MM (類似歷史時期)"],
    "context": "string (歷史對照說明)"
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
    "analysis_time": "2026-01-23T10:30:00.000Z",
    "start_date": "2015-01-01",
    "end_date": "2025-12-01",
    "indicator": "shipments_yoy",
    "lead_months": 6,
    "as_of_date": "2025-12-01"
  },
  "freight_status": {
    "indicator": "shipments_yoy",
    "series_name": "CASS Shipments YoY",
    "latest_value": -2.9,
    "yoy": -2.9,
    "yoy_3m_avg": -2.1,
    "cycle_status": "new_cycle_low",
    "is_new_cycle_low": true,
    "cycle_low_window": 18,
    "consecutive_negative_months": 4
  },
  "all_indicators": {
    "shipments_index": {
      "latest_value": 1.15,
      "status": "stable"
    },
    "expenditures_index": {
      "latest_value": 4.25,
      "status": "declining"
    },
    "shipments_yoy": {
      "latest_value": -2.9,
      "status": "new_cycle_low"
    },
    "expenditures_yoy": {
      "latest_value": -1.5,
      "status": "negative"
    }
  },
  "cpi_status": {
    "latest_yoy": 2.8,
    "yoy_3m_avg": 2.9,
    "trend": "stable"
  },
  "lead_alignment": {
    "correlation": 0.62,
    "lead_months": 6,
    "optimal_lead": 5,
    "alignment_quality": "high"
  },
  "signal_assessment": {
    "signal": "inflation_easing",
    "confidence": "high",
    "macro_implication": "通膨壓力正在放緩，未來 CPI 下行風險上升"
  },
  "historical_positioning": {
    "current_percentile": 15.2,
    "similar_periods": ["2015-11", "2019-08"],
    "context": "偏低，通常對應經濟放緩期"
  },
  "interpretation": [
    "CASS Shipments YoY 已轉為負值（-2.9%），並創下本輪週期新低。",
    "歷史上此類訊號通常領先 CPI 約 5-6 個月。",
    "當前 CPI 仍在 2.8%，但預期將在未來 4-6 個月內開始放緩。",
    "訊號強度高：連續 4 個月負增長 + 創 18 個月新低。",
    "Expenditures YoY 同樣轉負（-1.5%），交叉驗證支持此訊號。"
  ],
  "caveats": [
    "CASS 數據來自 MacroMicro，透過 Highcharts 爬取",
    "數據約滯後 1 個月，最新值為 2025-12",
    "若有供給側衝擊（如罷工、天災），訊號可能失真",
    "領先相關性基於歷史數據，未來關係可能改變"
  ]
}
```
</example_output>

<field_descriptions>

<field name="metadata">
分析元資料，包含時間範圍、使用的指標和參數。
</field>

<field name="freight_status">
CASS Freight Index 狀態分析。
- `indicator`: 選用的 CASS 指標
- `yoy`: 最新年增率（若使用 Index 指標則需計算）
- `cycle_status`: 週期狀態
  - `new_cycle_low`: YoY 轉負且創 N 個月新低
  - `negative`: YoY 為負但非新低
  - `positive`: YoY 為正
- `consecutive_negative_months`: 連續負增長月數，越長訊號越強
</field>

<field name="all_indicators">
CASS 四個指標的最新狀態概覽。
- `shipments_index`: 出貨量指數
- `expenditures_index`: 支出指數
- `shipments_yoy`: 出貨量年增率（主要分析指標）
- `expenditures_yoy`: 支出年增率（交叉驗證用）
</field>

<field name="cpi_status">
CPI 通膨狀態，用於對照驗證。
- `trend`: 根據 3M 動量判斷趨勢方向
</field>

<field name="lead_alignment">
CASS 對 CPI 的領先性分析。
- `correlation`: 相關係數，越高表示領先關係越穩定
- `optimal_lead`: 歷史最佳領先月數（相關性最高時）
- `alignment_quality`: 根據相關係數判斷對齊品質
</field>

<field name="signal_assessment">
訊號評估與宏觀解讀。
- `signal`: 訊號類型
- `confidence`: 信心水準
- `macro_implication`: 一句話宏觀含義，可直接用於報告
</field>

<field name="historical_positioning">
當前數據在歷史分布中的位置。
- `current_percentile`: 百分位數，越低表示越接近歷史低點
- `similar_periods`: 歷史上類似的時期
- `context`: 歷史對照說明
</field>

<field name="interpretation">
可操作的解讀文字，適合直接用於報告或交易筆記。
</field>

<field name="caveats">
分析的限制與注意事項，務必閱讀。
</field>

</field_descriptions>

<signal_definitions>

**訊號類型定義**

| Signal | 條件 | 含義 |
|--------|------|------|
| `inflation_easing` | CASS YoY < 0 | 通膨壓力緩解中 |
| `inflation_rising` | CASS YoY > 5 且上升 | 通膨壓力可能上升 |
| `neutral` | 其他情況 | 方向不明，需持續觀察 |

**信心水準定義**

| Confidence | 條件 | 建議行動 |
|------------|------|---------|
| `high` | 新週期低點 + 連續負值 + 高對齊品質 + 多指標一致 | 可作為主要參考 |
| `medium` | 部分條件滿足 | 結合其他指標驗證 |
| `low` | 訊號模糊或對齊品質低 | 僅作參考，謹慎使用 |

</signal_definitions>
