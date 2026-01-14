<template_description>
CPI-PCE 比較分析的 Markdown 報告模板。
適合用於研究報告、交易筆記或團隊分享。
</template_description>

<markdown_template>
```markdown
# CPI-PCE 通膨分歧分析報告

**分析日期**: {{analysis_time}}
**資料期間**: {{start_date}} 至 {{end_date}}
**計算方式**: {{measure_description}}
**資料截至**: {{as_of_date}}

---

## 摘要

| 指標 | CPI | PCE | 分歧 (bps) |
|------|-----|-----|-----------|
| Headline | {{cpi_headline}}% | {{pce_headline}}% | {{headline_gap_bps}} |
| Core | {{cpi_core}}% | {{pce_core}}% | {{core_gap_bps}} |

**結論**: {{headline_summary}}

---

## 低波動高權重桶位分析

這些桶位在 PCE 中權重較高，且價格波動相對穩定。若這些桶位的通膨走高，將顯著推升 Fed 關注的 PCE 指標。

| 桶位 | PCE 權重 | 波動度 (24M) | 最新通膨 | 3M 動能 | 訊號 |
|------|---------|-------------|---------|--------|------|
{{#low_vol_buckets}}
| {{bucket}} | {{weight}} | {{volatility}} | {{latest_inflation}}% | {{momentum_3m}} | {{signal_emoji}} {{signal}} |
{{/low_vol_buckets}}

### 關鍵觀察

{{low_vol_interpretation}}

---

## 通膨貢獻分解

各消費桶位對 PCE 通膨的貢獻：

| 桶位 | 權重 | 通膨率 | 加權貢獻 |
|------|------|-------|---------|
{{#top_contributors}}
| {{bucket}} | {{weight}} | {{inflation}}% | {{contribution}} |
{{/top_contributors}}

**權重效應**: {{weight_effect_bps}} bps

> 權重效應說明：因 PCE 使用動態權重、CPI 使用固定權重，同樣的分項通膨會產生不同的加總結果。

---

## Baseline 偏離度分析

{{#baseline_adjustment}}
**基準期**: {{baseline_range}}
**調整方式**: {{mode_description}}
**最新偏離**: {{latest_deviation}} 個百分點

{{baseline_interpretation}}
{{/baseline_adjustment}}

{{^baseline_adjustment}}
*本次分析未設定 baseline 基準期*
{{/baseline_adjustment}}

---

## 解讀與建議

{{#interpretation}}
- {{.}}
{{/interpretation}}

### 監控重點

1. **短期動能**: 觀察 3M SAAR 是否加速
2. **桶位動態**: 低波動高權重桶位的走勢
3. **權重變化**: PCE 權重是否向通膨較高的桶位移動

---

## 注意事項

{{#caveats}}
- ⚠️ {{.}}
{{/caveats}}

---

*此報告由 CPI-PCE Comparator Skill 自動生成*
*資料來源: FRED (St. Louis Fed), BLS*
```
</markdown_template>

<variable_definitions>

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{analysis_time}}` | 分析執行時間 | 2026-01-14 16:57 |
| `{{start_date}}` | 分析起始日 | 2020-01-01 |
| `{{end_date}}` | 分析結束日 | 2026-01-01 |
| `{{measure_description}}` | 計算方式描述 | 年增率 (YoY) |
| `{{as_of_date}}` | 資料最新日期 | 2025-12-01 |
| `{{cpi_headline}}` | CPI Headline 通膨 | 2.65 |
| `{{pce_headline}}` | PCE Headline 通膨 | 2.79 |
| `{{headline_gap_bps}}` | Headline 分歧 | +14 |
| `{{cpi_core}}` | Core CPI 通膨 | 2.65 |
| `{{pce_core}}` | Core PCE 通膨 | 2.83 |
| `{{core_gap_bps}}` | Core 分歧 | +18 |
| `{{headline_summary}}` | Headline 結論 | PCE 高於 CPI... |
| `{{signal_emoji}}` | 訊號符號 | 🔺 / ⚪ / 🔻 |

</variable_definitions>

<signal_emoji_mapping>
- `upside` → 🔺 (上行風險)
- `neutral` → ⚪ (中性)
- `downside` → 🔻 (下行風險)
</signal_emoji_mapping>

<measure_descriptions>
- `yoy` → 年增率 (Year-over-Year)
- `mom_saar` → 月增年化率 (MoM SAAR)
- `qoq_saar` → 季增年化率 (QoQ SAAR)
</measure_descriptions>

<example_filled_report>
```markdown
# CPI-PCE 通膨分歧分析報告

**分析日期**: 2026-01-14 16:57
**資料期間**: 2020-01-01 至 2026-01-01
**計算方式**: 年增率 (YoY)
**資料截至**: 2025-12-01

---

## 摘要

| 指標 | CPI | PCE | 分歧 (bps) |
|------|-----|-----|-----------|
| Headline | 2.65% | 2.79% | +14 |
| Core | 2.65% | 2.83% | +18 |

**結論**: PCE 通膨持續高於 CPI，Fed 關注的通膨指標比市場常看的 CPI 更具黏性。

---

## 低波動高權重桶位分析

| 桶位 | PCE 權重 | 波動度 (24M) | 最新通膨 | 3M 動能 | 訊號 |
|------|---------|-------------|---------|--------|------|
| pce_services | 0.69 | 0.42 | 3.21% | +0.15 | 🔺 upside |
| pce_housing | 0.18 | 0.38 | 4.85% | -0.22 | ⚪ neutral |

### 關鍵觀察

Services 桶位（PCE 權重 69%）顯示上行動能，若趨勢延續將對 PCE 造成上行壓力。Housing 通膨雖高但動能已轉弱。

---

## 解讀與建議

- PCE 通膨高於 CPI 約 14 bps，Fed 關注的通膨指標比 CPI 更具黏性。
- 低波動高權重桶位 (pce_services) 顯示上行訊號，若趨勢延續將推升 PCE。
- 監控重點：core_goods 和 core_services_ex_housing 的 3M 動能 vs 12M 趨勢。

---

## 注意事項

- ⚠️ 權重為近似值，基於 BEA/BLS 2024 年數據
- ⚠️ 部分桶位對應可能有誤差
- ⚠️ 此為權重效應的工程近似，非完整 BEA/BLS 方法論調和

---

*此報告由 CPI-PCE Comparator Skill 自動生成*
*資料來源: FRED (St. Louis Fed), BLS*
```
</example_filled_report>
