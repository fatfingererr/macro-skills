# Markdown 報告模板

## 報告結構

```markdown
# 聯準會未攤銷折價走勢模式分析報告

**分析日期**: {as_of_date}
**目標序列**: {target_series}
**分析版本**: {version}

---

## TL;DR

{interpretation.summary}

---

## 形狀比對結果

### 最佳匹配

| 項目           | 值                                                    |
|----------------|-------------------------------------------------------|
| 匹配基準       | {best_match.baseline}                                 |
| 匹配區間       | {best_match.segment_start} ~ {best_match.segment_end} |
| 相關係數       | {best_match.corr:.2f}                                 |
| DTW 距離       | {best_match.dtw:.2f}                                  |
| 形狀特徵       | {best_match.feature_sim:.2f}                          |
| **綜合相似度** | **{best_match.pattern_similarity_score:.2f}**         |

### 相似度解讀

| 分數範圍  | 解讀                                                           |
|-----------|----------------------------------------------------------------|
| > 0.8     | 高度相似 ← **當前: {best_match.pattern_similarity_score:.2f}** |
| 0.5 ~ 0.8 | 中度相似                                                       |
| < 0.5     | 低度相似                                                       |

---

## 壓力驗證結果

**壓力驗證分數**: {stress_confirmation.score:.2f}

| 指標 | 當前值 | z-score | 訊號 |
|------|--------|---------|------|
{for indicator in stress_confirmation.details}
| {indicator.name} | {indicator.current_value:.2f} | {indicator.z:.2f} | {indicator.signal} |
{endfor}

### 壓力訊號解讀

- 🟢 **neutral**: 中性，無壓力訊號
- 🟡 **mild_stress**: 輕微壓力，持續觀察
- 🔴 **stress**: 壓力訊號，需要關注
- ⚫ **extreme_stress**: 極端壓力，高度警戒

---

## 綜合風險評估

| 項目         | 分數                                      | 權重 |
|--------------|-------------------------------------------|------|
| 形狀相似度   | {best_match.pattern_similarity_score:.2f} | 60%  |
| 壓力驗證     | {stress_confirmation.score:.2f}           | 40%  |
| **合成風險** | **{composite_risk_score:.2f}**            | -    |

**風險等級**: {risk_level}

| 等級     | 分數範圍  | 當前                                          |
|----------|-----------|-----------------------------------------------|
| 低風險   | < 0.3     | {if risk_level == "low"}← 當前{endif}         |
| 中風險   | 0.3 ~ 0.5 | {if risk_level == "medium"}← 當前{endif}      |
| 中高風險 | 0.5 ~ 0.7 | {if risk_level == "medium_high"}← 當前{endif} |
| 高風險   | > 0.7     | {if risk_level == "high"}← 當前{endif}        |

---

## 分析解讀

### 形狀分析

**發現**: {interpretation.pattern_analysis.finding}

**可能成因**:
{for cause in interpretation.pattern_analysis.possible_causes}
- {cause}
{endfor}

**不太可能的成因**: {interpretation.pattern_analysis.unlikely_cause}

### 壓力分析

**發現**: {interpretation.stress_analysis.finding}

**關鍵觀察**:
{for obs in interpretation.stress_analysis.key_observations}
- {obs}
{endfor}

---

## 未來 60 天觀察重點

{for item in interpretation.what_to_watch_next_60d}
- {item}
{endfor}

---

## 對「黑天鵝」敘事的反證

{for item in interpretation.rebuttal_to_claim}
> {item}
{endfor}

---

## 資料品質說明

| 序列                                   | 資料截止                              | 狀態 |
|----------------------------------------|---------------------------------------|------|
| {data_quality.target_series.series_id} | {data_quality.target_series.data_end} | ✓    |
{for series in data_quality.confirmatory_series}
| {series.series_id} | {series.data_end} | {if series.status == "ok"}✓{else}⚠{endif} |
{endfor}

---

## 風險警語

{for caveat in caveats}
⚠️ {caveat}
{endfor}

---

## 執行資訊

| 項目     | 值                                        |
|----------|-------------------------------------------|
| 執行時間 | {metadata.executed_at}                    |
| 耗時     | {metadata.execution_time_ms} ms           |
| 快取     | {if metadata.cache_used}是{else}否{endif} |
| 版本     | {metadata.skill_version}                  |

---

*本報告由 detect-fed-unamortized-discount-pattern 技能自動生成*
*形狀比對 ≠ 事件預測，請結合其他資訊綜合判斷*
```

---

## 範例輸出

```markdown
# 聯準會未攤銷折價走勢模式分析報告

**分析日期**: 2026-01-26
**目標序列**: WUDSHO
**分析版本**: 0.1.0

---

## TL;DR

走勢形狀與 COVID 早期片段相似度高（0.88），但壓力驗證指標偏中性（0.22），綜合風險分數 0.49（中等）。這更像是「利率/會計結構造成的圖形相似」，不足以支持「系統性壓力升高」的假說。

---

## 形狀比對結果

### 最佳匹配

| 項目           | 值                      |
|----------------|-------------------------|
| 匹配基準       | COVID_2020              |
| 匹配區間       | 2020-01-08 ~ 2020-06-17 |
| 相關係數       | 0.91                    |
| DTW 距離       | 0.38                    |
| 形狀特徵       | 0.82                    |
| **綜合相似度** | **0.88**                |

### 相似度解讀

| 分數範圍  | 解讀                      |
|-----------|---------------------------|
| > 0.8     | 高度相似 ← **當前: 0.88** |
| 0.5 ~ 0.8 | 中度相似                  |
| < 0.5     | 低度相似                  |

---

## 壓力驗證結果

**壓力驗證分數**: 0.22

| 指標          | 當前值  | z-score | 訊號         |
|---------------|---------|---------|--------------|
| credit_spread | 1.05    | 0.40    | neutral      |
| equity_vol    | 14.50   | -0.44   | mild_risk_on |
| hy_spread     | 3.20    | 0.17    | neutral      |
| yield_curve   | 0.15    | -1.08   | mild_stress  |
| fed_balance   | 7500000 | 0.60    | neutral      |

### 壓力訊號解讀

- 🟢 **neutral**: 中性，無壓力訊號（3 個指標）
- 🟡 **mild_stress**: 輕微壓力（殖利率曲線）
- 🔵 **mild_risk_on**: 偏風險偏好（VIX 偏低）

---

## 綜合風險評估

| 項目         | 分數     | 權重 |
|--------------|----------|------|
| 形狀相似度   | 0.88     | 60%  |
| 壓力驗證     | 0.22     | 40%  |
| **合成風險** | **0.49** | -    |

**風險等級**: 中風險

---

## 未來 60 天觀察重點

- 若形狀相似度維持高檔，同時信用利差明顯走寬（z > 1.5），才應升級風險警報
- 若 VIX 持續上升並突破 25，顯示市場開始定價風險
- 觀察 Fed 是否啟用緊急流動性工具

---

## 對「黑天鵝」敘事的反證

> 「像」可以量化（相關係數 0.91），但「像 COVID」不等於「會發生 COVID 級事件」

> WUDSHO 變動最常見的原因是利率效果，不是金融壓力

> 把「黑天鵝」定義成「精心策劃」屬於不可驗證敘事

---

## 風險警語

⚠️ 形狀相似不代表因果相同；該序列可能強烈受利率、持有期限結構與會計攤銷影響。

⚠️ 若缺乏壓力指標同步惡化，不應把圖形類比直接升級成『黑天鵝預言』。

⚠️ 本工具提供的是『樣態比對 + 交叉驗證』，不是預測器。

---

*本報告由 detect-fed-unamortized-discount-pattern 技能自動生成*
```
