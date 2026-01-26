# Markdown 報告模板

## 快速檢查報告模板

```markdown
### 日本保險公司超長端 JGB 淨買入驗證（JSDA 公開數據）

**分析日期**：{as_of}
**數據來源**：JSDA Trends in Bond Transactions (by investor type)

---

#### 核心指標

| 指標                        | 數值                      | 說明                       |
|-----------------------------|---------------------------|----------------------------|
| 本月（{latest_date}）淨買入 | **{latest_value} 兆日圓** | {interpretation}           |
| 是否創紀錄                  | **{is_record}**           | {record_note}              |
| 連續淨賣出月數              | **{streak_len} 個月**     | 自 {streak_start} 起       |
| 本輪累積淨賣出              | **{cumulative} 兆日圓**   | 過去 {streak_len} 個月合計 |

---

#### 口徑說明

- 投資人分類：{investor_group}
- 天期桶：{maturity_bucket}

> 若新聞口徑與本分析不同，數值可能略有差異。

---

**Headline**: {headline}
```

---

## 完整分析報告模板

```markdown
### 日本保險公司超長端 JGB 淨買入完整分析

**分析期間**：{start_date} 至 {end_date}
**分析日期**：{as_of}
**數據來源**：JSDA Trends in Bond Transactions (by investor type)

---

#### 一、最新月份狀態

| 指標       | 數值                          | 說明               |
|------------|-------------------------------|--------------------|
| 本月淨買入 | {latest_value_billion} 億日圓 | {interpretation}   |
| 是否創紀錄 | {is_record}                   | {record_note}      |
| 歷史最低值 | {record_low_billion} 億日圓   | {record_low_date}  |
| 歷史最高值 | {record_high_billion} 億日圓  | {record_high_date} |

---

#### 二、連續賣超分析

| 指標           | 數值                         |
|----------------|------------------------------|
| 連續淨賣出月數 | {streak_len} 個月            |
| 本輪起始月     | {streak_start}               |
| 本輪累積淨賣出 | {cumulative_trillion} 兆日圓 |

**趨勢解讀**：{streak_interpretation}

---

#### 三、歷史分布

| 統計量         | 數值                           |
|----------------|--------------------------------|
| 樣本期間       | {sample_start} 至 {sample_end} |
| 樣本月數       | {sample_count} 個月            |
| 平均淨買入     | {mean_billion} 億日圓/月       |
| 標準差         | {std_billion} 億日圓           |
| 當前值 Z-score | {zscore}                       |
| 當前值分位數   | {percentile}%                  |

**分布解讀**：{distribution_interpretation}

---

#### 四、口徑說明

##### 4.1 投資人分類

| 本分析使用       | 說明            |
|------------------|-----------------|
| {investor_group} | {investor_note} |

##### 4.2 天期桶

| 本分析使用        | 說明            |
|-------------------|-----------------|
| {maturity_bucket} | {maturity_note} |

**口徑警示**：{caliber_warning}

---

#### 五、結論與建議

**Headline Takeaways**：
1. {takeaway_1}
2. {takeaway_2}
3. {takeaway_3}

**信心水準**：{confidence_level}

**注意事項**：
- {caveat_1}
- {caveat_2}

---

*本報告基於 JSDA 公開數據生成，計算邏輯透明可重現。*
```

---

## 驗證報告模板

```markdown
### 新聞數字驗證報告

**驗證日期**：{as_of}

---

#### 新聞聲稱

| 項目 | 內容            |
|------|-----------------|
| 數字 | {claim_value}   |
| 時間 | {claim_date}    |
| 口徑 | {claim_caliber} |
| 來源 | {claim_source}  |

---

#### JSDA 原始數據對照

| 口徑              | JSDA 數值         | 與新聞差異        | 說明              |
|-------------------|-------------------|-------------------|-------------------|
| super_long        | {jsda_super_long} | {diff_super_long} | {note_super_long} |
| long              | {jsda_long}       | {diff_long}       | {note_long}       |
| long + super_long | {jsda_combined}   | {diff_combined}   | {note_combined}   |

---

#### 驗證結論

| 檢查項     | 結果              | 說明             |
|------------|-------------------|------------------|
| 數量級一致 | {magnitude_match} | {magnitude_note} |
| 符號一致   | {sign_match}      | {sign_note}      |
| 口徑對齊   | {caliber_match}   | {caliber_note}   |

**總體評估**：{overall_assessment}

**建議**：{recommendation}
```

---

## 變數說明

| 變數                     | 類型   | 說明                     |
|--------------------------|--------|--------------------------|
| `{as_of}`                | string | 分析日期                 |
| `{start_date}`           | string | 分析起始年月             |
| `{end_date}`             | string | 分析結束年月             |
| `{latest_date}`          | string | 最新月份                 |
| `{latest_value}`         | string | 最新月份淨買入（兆日圓） |
| `{latest_value_billion}` | string | 最新月份淨買入（億日圓） |
| `{is_record}`            | string | 是否創紀錄（是/否）      |
| `{record_note}`          | string | 紀錄說明                 |
| `{streak_len}`           | int    | 連續月數                 |
| `{streak_start}`         | string | 本輪起始月               |
| `{cumulative}`           | string | 累積金額（兆日圓）       |
| `{investor_group}`       | string | 投資人分類               |
| `{maturity_bucket}`      | string | 天期桶                   |
| `{interpretation}`       | string | 解讀（淨買入/淨賣出）    |
| `{headline}`             | string | 一句話結論               |
| `{zscore}`               | float  | Z-score                  |
| `{percentile}`           | float  | 分位數（%）              |
| `{confidence_level}`     | string | 信心水準（高/中/低）     |
