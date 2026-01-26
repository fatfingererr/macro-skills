# Workflow: 快速檢查

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性
2. references/methodology.md - 了解計算邏輯
</required_reading>

<process>

## Step 1: 執行快速分析腳本

```bash
cd skills/analyze-jgb-insurer-superlong-flow
python scripts/jsda_flow_analyzer.py --quick
```

若首次使用，先安裝依賴：
```bash
pip install pandas numpy requests openpyxl
```

## Step 2: 檢視輸出結果

腳本將輸出最新月份的關鍵指標：

```json
{
  "end_date": "2025-12",
  "investor_group": "insurance_companies",
  "maturity_bucket": "super_long",
  "latest_net_purchases_trillion_jpy": -0.8224,
  "is_record_sale": true,
  "consecutive_negative_months": 5,
  "cumulative_net_purchases_over_streak_trillion_jpy": -1.37
}
```

## Step 3: 解讀結果

**關鍵指標解讀**：

| 指標                          | 意義                            |
|-------------------------------|---------------------------------|
| `latest_net_purchases`        | 最新月份淨買入（負值 = 淨賣出） |
| `is_record_sale`              | 是否為歷史最大淨賣出            |
| `consecutive_negative_months` | 連續淨賣出月數                  |
| `cumulative_over_streak`      | 本輪連續賣超的累積金額          |

## Step 4: 生成摘要

根據結果生成可複製的摘要：

```markdown
### 日本保險公司超長端 JGB 淨買入驗證（JSDA 公開數據）

- 本月（2025-12）淨買入：**-0.8224 兆日圓**（負值＝淨賣出）
- 是否創紀錄：**是**（全樣本最低值）
- 連續淨賣出月數：**5 個月**
- 本輪累積淨賣出：**-1.37 兆日圓**

> 註：天期桶採用 JSDA「super_long」分類。若新聞口徑為「10 年以上」，數值可能略有差異。
```

</process>

<success_criteria>
快速檢查完成時：

- [ ] 成功抓取最新月份數據
- [ ] 輸出淨買賣數值與正負判斷
- [ ] 判斷是否為歷史極值
- [ ] 計算連續賣超月數
- [ ] 生成可複製的摘要
</success_criteria>
