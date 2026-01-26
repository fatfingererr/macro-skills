# Workflow: 完整分析

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性與下載方式
2. references/methodology.md - 了解 streak、record、cumulative 計算邏輯
3. references/jsda-structure.md - 了解 XLS 結構與投資人分類
</required_reading>

<process>

## Step 1: 確認分析參數

**必要參數**：
- `start_date`: 分析起始年月（如 2020-01）
- `end_date`: 分析結束年月（如 2025-12）
- `investor_group`: 投資人分類（預設 insurance_companies）
- `maturity_bucket`: 天期桶（預設 super_long）

若用戶未提供，使用預設值並詢問確認。

## Step 2: 抓取 JSDA 數據

```bash
cd skills/analyze-jgb-insurer-superlong-flow
python scripts/fetch_jsda_data.py --refresh
```

腳本會：
1. 從 JSDA 下載最新 XLS
2. 解析投資人別交易數據
3. 緩存到 `data/cache/` 目錄

## Step 3: 執行完整分析

```bash
python scripts/jsda_flow_analyzer.py --full \
  --start 2020-01 \
  --end 2025-12 \
  --investor insurance_companies \
  --maturity super_long
```

## Step 4: 計算關鍵指標

### 4.1 取得本月值

```python
latest = series.loc[end_date]  # 單位：兆日圓
```

### 4.2 判斷是否為歷史極值

```python
record_low = series.min()
is_record_sale = (latest == record_low) and (latest < 0)
```

若 `record_lookback_years` 不是全樣本，需調整計算範圍。

### 4.3 計算連續賣超月數

```python
def calc_streak(series, sign="negative"):
    s = series.dropna()
    streak = 0
    for v in reversed(s.values):
        if (sign == "negative" and v < 0) or (sign == "positive" and v > 0):
            streak += 1
        else:
            break
    return streak
```

### 4.4 計算本輪累積賣超

```python
streak_window = series.loc[:end_date].tail(streak_len)
cum = streak_window.sum()
```

## Step 5: 口徑對照檢查

若新聞使用「10+ years」而分析使用「super_long」：

1. 檢查 JSDA XLS 是否有「10年以上」合併桶
2. 若有，同時輸出兩個口徑的數值
3. 若無，標註「口徑可能不完全一致」

## Step 6: 生成完整報告

使用 `templates/output-markdown.md` 模板生成報告：

```markdown
### 日本保險公司超長端 JGB 淨買入完整分析

**分析期間**：2020-01 至 2025-12
**數據來源**：JSDA Trends in Bond Transactions (by investor type)

---

#### 一、最新月份狀態

| 指標       | 數值       | 說明          |
|------------|------------|---------------|
| 本月淨買入 | -¥8,224 億 | 負值 = 淨賣出 |
| 是否創紀錄 | 是         | 全樣本最低值  |
| 歷史最低值 | -¥8,224 億 | 2025-12       |
| 歷史最高值 | +¥XXX 億   | YYYY-MM       |

---

#### 二、連續賣超分析

| 指標           | 數值      |
|----------------|-----------|
| 連續淨賣出月數 | 5 個月    |
| 本輪起始月     | 2025-08   |
| 本輪累積淨賣出 | -¥1.37 兆 |

---

#### 三、歷史分布

- 全樣本平均淨買入：+¥XXX 億/月
- 全樣本標準差：¥XXX 億
- 當前值 Z-score：-X.XX

---

#### 四、口徑說明

- 投資人分類：insurance_companies（含壽險 + 產險）
- 天期桶：super_long（超長端）
- 若需嚴格對齊「10 年以上」，請使用 long_plus_super_long 合併桶

---

#### 五、結論

1. 日本保險公司確實在 2025-12 創下歷史最大單月淨賣出紀錄
2. 已連續 5 個月淨賣出，累積金額達 ¥1.37 兆
3. 此趨勢與 JGB 殖利率上升期間吻合
```

## Step 7: 輸出 JSON（可選）

若 `output_format` 為 JSON：

```bash
python scripts/jsda_flow_analyzer.py --full --format json > output/analysis_result.json
```

</process>

<success_criteria>
完整分析完成時：

- [ ] 成功抓取指定期間的 JSDA 數據
- [ ] 計算並輸出最新月份淨買賣數值
- [ ] 判斷是否為歷史極值（含回溯期間說明）
- [ ] 計算連續賣超月數與累積金額
- [ ] 提供歷史分布統計（均值、標準差、Z-score）
- [ ] 明確標示天期桶與投資人口徑
- [ ] 若口徑不一致，提供警示
- [ ] 生成完整 Markdown 報告
</success_criteria>
