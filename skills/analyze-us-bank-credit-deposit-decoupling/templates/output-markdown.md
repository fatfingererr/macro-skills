# Markdown 報告模板

本文件定義美國銀行信貸存款脫鉤分析的 Markdown 報告格式。

---

## 報告模板

```markdown
# 銀行信貸-存款脫鉤分析報告

**生成時間**: {{generated_at}}
**分析期間**: {{start_date}} 至 {{end_date}}

---

## TL;DR

{{macro_implication}}

**關鍵數據**：
- 脫鉤落差：{{decoupling_gap_trillion_usd}} 兆美元
- 存款壓力比率：{{deposit_stress_ratio}} ({{stress_level}})
- 緊縮類型：{{tightening_type_label}}
- 信心水準：{{confidence}}

---

## 1. 數據摘要

### 1.1 累積變化量（自 {{base_date}}）

| 指標     | 累積變化                               |
|----------|----------------------------------------|
| 銀行貸款 | +{{new_loans_trillion_usd}} 兆美元     |
| 銀行存款 | +{{new_deposits_trillion_usd}} 兆美元  |
| 脫鉤落差 | {{decoupling_gap_trillion_usd}} 兆美元 |

### 1.2 最新數據點

| 指標         | 數值                  | 日期              |
|--------------|-----------------------|-------------------|
| 銀行貸款總量 | {{loans_latest}} B    | {{loans_date}}    |
| 銀行存款總量 | {{deposits_latest}} B | {{deposits_date}} |
| 隔夜逆回購   | {{rrp_latest}} B      | {{rrp_date}}      |

---

## 2. 脫鉤分析

### 2.1 Decoupling Gap

**定義**: 累積新增貸款 - 累積新增存款

**當前值**: {{decoupling_gap_trillion_usd}} 兆美元

**解讀**: {{decoupling_gap_interpretation}}

### 2.2 Deposit Stress Ratio

**定義**: Decoupling Gap / 累積新增貸款

**當前值**: {{deposit_stress_ratio}} (歷史分位數: {{stress_percentile}})

**壓力等級**: {{stress_level}}

| 等級 | 門檻    | 意義           |
|------|---------|----------------|
| 低   | < 0.3   | 正常信貸創造   |
| 中   | 0.3-0.5 | 輕度脫鉤       |
| 高   | 0.5-0.7 | 顯著脫鉤       |
| 極高 | > 0.7   | 嚴重負債端壓力 |

### 2.3 RRP 相關性驗證

**RRP 與 Gap 相關係數**: {{rrp_correlation}}

**解讀**: {{rrp_correlation_interpretation}}

---

## 3. 緊縮判定

### 3.1 判定結果

- **緊縮類型**: {{tightening_type_label}}
- **主要驅動因素**: {{primary_driver_label}}
- **信心水準**: {{confidence}}

### 3.2 判定依據

{{assessment_reasoning}}

---

## 4. 歷史對照

### 4.1 當前位置

- 歷史分位數: {{historical_percentile}}
- 可比較時期: {{comparable_periods}}

### 4.2 類似歷史事件

| 時期 | stress_ratio | 後續發展 |
|------|--------------|----------|
{{#each comparable_events}}
| {{period}} | {{ratio}} | {{outcome}} |
{{/each}}

---

## 5. 宏觀意涵

{{macro_implication_detailed}}

### 5.1 對銀行的影響

{{bank_impact}}

### 5.2 對信貸市場的影響

{{credit_impact}}

### 5.3 對流動性的影響

{{liquidity_impact}}

---

## 6. 建議後續追蹤

{{#each recommended_checks}}
- {{this}}
{{/each}}

---

## 7. 資料來源與限制

### 7.1 數據來源

| 指標       | FRED Series ID | 頻率   |
|------------|----------------|--------|
| 銀行貸款   | TOTLL          | Weekly |
| 銀行存款   | DPSACBW027SBOG | Weekly |
| 隔夜逆回購 | RRPONTSYD      | Daily  |

### 7.2 分析限制

{{#each caveats}}
- {{this}}
{{/each}}

---

## 8. 附錄：視覺化圖表

![信貸-存款脫鉤分析圖]({{chart_path}})

---

*報告由 analyze-us-bank-credit-deposit-decoupling skill 生成*
*版本: {{version}}*
```

---

## 範例輸出

```markdown
# 銀行信貸-存款脫鉤分析報告

**生成時間**: 2026-01-23 10:30:00 UTC
**分析期間**: 2022-06-01 至 2026-01-23

---

## TL;DR

本次緊縮並非來自銀行縮手放貸，而是聯準會透過 RRP 抽走體系存款，導致市場必須爭奪有限的存款來支撐既有負債結構，屬於「隱性金融緊縮」狀態。

**關鍵數據**：
- 脫鉤落差：1.6 兆美元
- 存款壓力比率：0.76 (極高)
- 緊縮類型：隱性資產負債表緊縮
- 信心水準：高

---

## 1. 數據摘要

### 1.1 累積變化量（自 2022-06-01）

| 指標     | 累積變化    |
|----------|-------------|
| 銀行貸款 | +2.1 兆美元 |
| 銀行存款 | +0.5 兆美元 |
| 脫鉤落差 | 1.6 兆美元  |

...（後續內容）
```
