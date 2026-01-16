# Markdown 報告模板

## 單次偵測報告

```markdown
# 白銀（{silver_symbol}）與鈀金（{palladium_symbol}）跨金屬拐點偵測報告

**數據截至**：{as_of}
**時間尺度**：{timeframe}
**回溯範圍**：{lookback_bars} 根 K 棒

---

## 摘要

| 指標                       | 數值     | 狀態                       |
|----------------------------|----------|----------------------------|
| 鈀金領先白銀               | {lead} bars | {lead_description}      |
| 領先滯後相關係數           | {corr}   | {corr_description}         |
| 確認率                     | {conf_rate}% | 白銀拐點被鈀金確認的比例 |
| 未確認失敗率               | {fail_rate}% | 未被確認的拐點失敗比例   |

---

## 最新事件

**時間**：{latest_ts}
**類型**：{latest_turn}（{turn_cn}拐點）

| 判定項目     | 結果     |
|--------------|----------|
| 鈀金確認     | {confirmed} |
| 參與度       | {participation} |
| 失敗走勢     | {failed} |

### 判定說明

{event_explanation}

---

## 可操作建議

{tactics_list}

---

## 行情解讀

{interpretation}

---

## 技術細節

### 領先滯後分析

- 最佳滯後：{best_lag} bars（{lag_meaning}）
- 相關係數：{corr}（{corr_level}）
- 置信區間：[{ci_low}, {ci_high}] bars
- 穩定性：{stability}

### 確認統計

| 類型   | 總數 | 已確認 | 確認率 |
|--------|------|--------|--------|
| 頂部   | {top_total} | {top_confirmed} | {top_rate}% |
| 底部   | {bottom_total} | {bottom_confirmed} | {bottom_rate}% |
| 合計   | {total} | {confirmed_total} | {total_rate}% |

### 失敗走勢統計

- 未確認事件失敗率：{unconf_fail}%
- 已確認事件失敗率：{conf_fail}%
- 失敗率比值：{ratio}x

---

**報告生成時間**：{generated_at}
**技能版本**：{version}
```

---

## 回測報告

```markdown
# 跨金屬確認歷史回測報告

**標的**：{silver_symbol} vs {palladium_symbol}
**時間尺度**：{timeframe}
**回測期間**：{start_date} 至 {end_date}
**總 K 棒數**：{total_bars}

---

## 執行摘要

{executive_summary}

---

## 領先滯後分析

### 整體估計

| 指標           | 數值     | 說明               |
|----------------|----------|--------------------|
| 最佳滯後       | {lag} bars | {lag_meaning}    |
| 相關係數       | {corr}   | {corr_level}       |
| p-value        | {pval}   | {significance}     |
| 置信區間       | [{ci_low}, {ci_high}] | 95% CI  |

### 穩定性分析

| 期間     | 滯後 (bars) | 相關係數 |
|----------|-------------|----------|
| {period1}| {lag1}      | {corr1}  |
| {period2}| {lag2}      | {corr2}  |
| {period3}| {lag3}      | {corr3}  |
| {period4}| {lag4}      | {corr4}  |

**穩定性評估**：{stability_assessment}

---

## 確認有效性分析

### 整體統計

| 指標           | 數值     |
|----------------|----------|
| 白銀拐點總數   | {total}  |
| 被確認數       | {confirmed} |
| 確認率         | {rate}%  |

### 按拐點類型

| 類型   | 總數 | 已確認 | 確認率 |
|--------|------|--------|--------|
| 頂部   | {top_total} | {top_confirmed} | {top_rate}% |
| 底部   | {bottom_total} | {bottom_confirmed} | {bottom_rate}% |

### 確認滯後分布

- 平均值：{lag_mean} bars
- 中位數：{lag_median} bars
- 標準差：{lag_std} bars
- 範圍：[{lag_min}, {lag_max}] bars

---

## 失敗走勢分析

### 失敗率比較

| 事件類型 | 事件數 | 失敗數 | 失敗率 |
|----------|--------|--------|--------|
| 未確認   | {unconf_n} | {unconf_fail_n} | {unconf_rate}% |
| 已確認   | {conf_n} | {conf_fail_n} | {conf_rate}% |

**失敗率比值**：{ratio}x

### 回撤速度

| 事件類型 | 平均回撤 K 數 |
|----------|---------------|
| 未確認   | {unconf_revert} bars |
| 已確認   | {conf_revert} bars |

---

## 結論

### 有效性評估

{effectiveness_conclusion}

### 建議

{recommendations}

---

**報告生成時間**：{generated_at}
**使用參數**：

```json
{parameters_json}
```
```

---

## 監控日報

```markdown
# 鈀金-白銀跨金屬監控日報

**日期**：{date}
**標的**：{silver_symbol} vs {palladium_symbol}
**時間尺度**：{timeframe}

---

## 當日新拐點

| 時間 | 類型 | 白銀價格 | 確認狀態 | 參與度 | 判定 |
|------|------|----------|----------|--------|------|
{events_table}

---

## 統計匯總

- 新拐點數：{new_turns}
- 已確認數：{confirmed}
- 未確認數：{unconfirmed}
- 失敗走勢：{failed}

---

## 告警事件

{alerts_section}

---

## 領先滯後關係變化

| 指標           | 昨日     | 今日     | 變化     |
|----------------|----------|----------|----------|
| 滾動 7 日確認率| {prev_rate}% | {curr_rate}% | {rate_change} |
| 滾動相關係數   | {prev_corr} | {curr_corr} | {corr_change} |

---

## 明日關注點

{watchlist}

---

**生成時間**：{generated_at}
```

---

## 佔位符說明

| 佔位符              | 說明                     | 範例                   |
|---------------------|--------------------------|------------------------|
| `{silver_symbol}`   | 白銀標的代碼             | SI=F                   |
| `{palladium_symbol}`| 鈀金標的代碼             | PA=F                   |
| `{as_of}`           | 數據截止日期             | 2026-01-14             |
| `{timeframe}`       | 時間尺度                 | 1h                     |
| `{lead}`            | 領先 K 棒數              | 6                      |
| `{corr}`            | 相關係數                 | 0.42                   |
| `{conf_rate}`       | 確認率百分比             | 71                     |
| `{fail_rate}`       | 失敗率百分比             | 64                     |
| `{latest_ts}`       | 最新事件時間             | 2026-01-15T14:00:00Z   |
| `{latest_turn}`     | 最新事件類型             | top                    |
| `{confirmed}`       | 確認狀態                 | 否 / 是                |
| `{participation}`   | 參與度狀態               | 不足 / 足夠            |
| `{failed}`          | 失敗走勢判定             | 是 / 否                |
| `{tactics_list}`    | 建議列表（Markdown）     | - 建議1\n- 建議2       |
| `{interpretation}`  | 行情解讀                 | 文字段落               |
| `{generated_at}`    | 報告生成時間             | 2026-01-15T15:00:00Z   |
