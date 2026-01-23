<template_description>
CASS Freight Index 週期轉折分析的 Markdown 報告模板。
適合用於研究報告、交易筆記或團隊分享。
</template_description>

<markdown_template>
```markdown
# CASS Freight Index 週期轉折分析報告

**分析日期**: {{analysis_time}}
**資料期間**: {{start_date}} 至 {{end_date}}
**分析指標**: {{indicator_name}}
**領先月數**: {{lead_months}} 個月
**資料截至**: {{as_of_date}}

---

## 摘要

{{signal_emoji}} **訊號**: {{signal_text}}
**信心水準**: {{confidence_text}}

> {{macro_implication}}

---

## CASS Freight Index 狀態

| 指標 | 數值 | 說明 |
|------|------|------|
| Shipments YoY | {{shipments_yoy}}% | {{shipments_interpretation}} |
| Expenditures YoY | {{expenditures_yoy}}% | {{expenditures_interpretation}} |
| 週期狀態 | {{cycle_status_emoji}} {{cycle_status_text}} | {{cycle_interpretation}} |
| 連續負值月數 | {{consecutive_months}} | {{consecutive_interpretation}} |

### 四個指標概覽

| 指標 | 最新值 | 狀態 |
|------|-------|------|
| Shipments Index | {{shipments_index}} | {{shipments_index_status}} |
| Expenditures Index | {{expenditures_index}} | {{expenditures_index_status}} |
| Shipments YoY | {{shipments_yoy}}% | {{shipments_yoy_status}} |
| Expenditures YoY | {{expenditures_yoy}}% | {{expenditures_yoy_status}} |

---

## CPI 對照

| 指標 | 數值 |
|------|------|
| CPI YoY | {{cpi_yoy}}% |
| CPI 3M 平均 | {{cpi_yoy_3m}}% |
| 趨勢 | {{cpi_trend_emoji}} {{cpi_trend}} |

**領先對照**：
- CASS YoY 於 {{cass_turn_date}} 轉折
- 預期 CPI 於 {{expected_cpi_turn}} 開始反映

---

## 領先性驗證

| 指標 | 數值 | 說明 |
|------|------|------|
| 相關係數 | {{correlation}} | {{correlation_interpretation}} |
| 最佳領先月數 | {{optimal_lead}} 個月 | 歷史最佳 |
| 對齊品質 | {{alignment_quality_emoji}} {{alignment_quality}} | |

---

## 歷史定位

**當前百分位**: {{percentile}}%（越低越接近歷史低點）

**類似歷史時期**：
{{#similar_periods}}
- {{period}}: {{context}}
{{/similar_periods}}

**歷史對照**：{{historical_context}}

---

## 解讀與建議

{{#interpretation}}
- {{.}}
{{/interpretation}}

### 監控重點

1. **短期**：觀察 CASS Shipments YoY 是否持續負增長
2. **中期**：CPI 是否在預期時間內開始放緩
3. **驗證**：Shipments 和 Expenditures 是否一致

### 可能的交易含義

{{#signal_is_easing}}
- 通膨放緩利好：長期國債、成長股
- Fed 降息預期可能上升
- 防禦性資產相對優勢
{{/signal_is_easing}}

{{#signal_is_rising}}
- 通膨壓力延續：大宗商品、通膨連結債券
- 升息預期可能維持
- 價值股相對優勢
{{/signal_is_rising}}

{{#signal_is_neutral}}
- 方向不明，建議觀望
- 等待更明確訊號
- 維持平衡配置
{{/signal_is_neutral}}

---

## 注意事項

{{#caveats}}
- ⚠️ {{.}}
{{/caveats}}

---

*此報告由 detect-freight-led-inflation-turn Skill 自動生成*
*資料來源: MacroMicro (CASS), FRED (CPI)*
```
</markdown_template>

<variable_definitions>

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{analysis_time}}` | 分析執行時間 | 2026-01-23 10:30 |
| `{{start_date}}` | 分析起始日 | 2015-01-01 |
| `{{end_date}}` | 分析結束日 | 2025-12-01 |
| `{{indicator_name}}` | 分析指標名稱 | CASS Shipments YoY |
| `{{lead_months}}` | 使用的領先月數 | 6 |
| `{{as_of_date}}` | 資料最新日期 | 2025-12-01 |
| `{{signal_emoji}}` | 訊號符號 | 📉 / 📈 / ⚪ |
| `{{signal_text}}` | 訊號文字 | 通膨緩解 |
| `{{confidence_text}}` | 信心水準 | 高 / 中 / 低 |
| `{{macro_implication}}` | 宏觀含義 | 通膨壓力正在放緩... |
| `{{shipments_yoy}}` | Shipments YoY | -2.9 |
| `{{expenditures_yoy}}` | Expenditures YoY | -1.5 |
| `{{cycle_status_emoji}}` | 週期狀態符號 | 🔻 / ⚪ / 🔺 |
| `{{cycle_status_text}}` | 週期狀態文字 | 週期新低 |
| `{{percentile}}` | 歷史百分位 | 15.2 |

</variable_definitions>

<signal_emoji_mapping>
- `inflation_easing` → 📉 通膨緩解
- `inflation_rising` → 📈 通膨上行
- `neutral` → ⚪ 中性
</signal_emoji_mapping>

<cycle_status_emoji_mapping>
- `new_cycle_low` → 🔻 週期新低
- `negative` → ⬇️ 負增長
- `positive` → ⬆️ 正增長
</cycle_status_emoji_mapping>

<alignment_quality_emoji_mapping>
- `high` → 🟢 高
- `medium` → 🟡 中
- `low` → 🔴 低
</alignment_quality_emoji_mapping>

<example_filled_report>
```markdown
# CASS Freight Index 週期轉折分析報告

**分析日期**: 2026-01-23 10:30
**資料期間**: 2015-01-01 至 2025-12-01
**分析指標**: CASS Shipments YoY
**領先月數**: 6 個月
**資料截至**: 2025-12-01

---

## 摘要

📉 **訊號**: 通膨緩解
**信心水準**: 高

> 通膨壓力正在放緩，未來 CPI 下行風險上升

---

## CASS Freight Index 狀態

| 指標 | 數值 | 說明 |
|------|------|------|
| Shipments YoY | -2.9% | 年增率轉負 |
| Expenditures YoY | -1.5% | 同樣轉負，交叉驗證 |
| 週期狀態 | 🔻 週期新低 | 創 18 個月新低 |
| 連續負值月數 | 4 | 訊號強度高 |

### 四個指標概覽

| 指標 | 最新值 | 狀態 |
|------|-------|------|
| Shipments Index | 1.15 | 穩定 |
| Expenditures Index | 4.25 | 下降 |
| Shipments YoY | -2.9% | 週期新低 |
| Expenditures YoY | -1.5% | 負增長 |

---

## CPI 對照

| 指標 | 數值 |
|------|------|
| CPI YoY | 2.8% |
| CPI 3M 平均 | 2.9% |
| 趨勢 | ⬇️ 略降 |

**領先對照**：
- CASS YoY 於 2025-08 轉負
- 預期 CPI 於 2026-02 開始明顯放緩

---

## 領先性驗證

| 指標 | 數值 | 說明 |
|------|------|------|
| 相關係數 | 0.62 | 領先關係穩定 |
| 最佳領先月數 | 5 個月 | 歷史最佳 |
| 對齊品質 | 🟢 高 | |

---

## 歷史定位

**當前百分位**: 15.2%（越低越接近歷史低點）

**類似歷史時期**：
- 2015-11: 製造業衰退期，後續 CPI 放緩
- 2019-08: 經濟放緩期，Fed 降息

**歷史對照**：偏低，通常對應經濟放緩期

---

## 解讀與建議

- CASS Shipments YoY 已轉為負值（-2.9%），並創下本輪週期新低。
- Expenditures YoY 同樣轉負（-1.5%），交叉驗證支持此訊號。
- 歷史上此類訊號通常領先 CPI 約 5-6 個月。
- 當前 CPI 仍在 2.8%，但預期將在未來 4-6 個月內開始放緩。
- 訊號強度高：連續 4 個月負增長 + 創 18 個月新低。

### 監控重點

1. **短期**：觀察 CASS Shipments YoY 是否持續負增長
2. **中期**：CPI 是否在預期時間內開始放緩
3. **驗證**：Shipments 和 Expenditures 是否一致

### 可能的交易含義

- 通膨放緩利好：長期國債、成長股
- Fed 降息預期可能上升
- 防禦性資產相對優勢

---

## 注意事項

- ⚠️ CASS 數據來自 MacroMicro，透過 Highcharts 爬取
- ⚠️ 數據約滯後 1 個月，最新值為 2025-12
- ⚠️ 若有供給側衝擊（如罷工、天災），訊號可能失真
- ⚠️ 領先相關性基於歷史數據，未來關係可能改變

---

*此報告由 detect-freight-led-inflation-turn Skill 自動生成*
*資料來源: MacroMicro (CASS), FRED (CPI)*
```
</example_filled_report>
