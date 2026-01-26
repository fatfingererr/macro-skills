# Workflow: 快速檢查

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性
2. references/methodology.md - 了解計算邏輯
</required_reading>

<process>

## Step 1: 執行快速分析腳本

```bash
cd .claude/skills/analyze-jgb-insurer-superlong-flow
python scripts/jsda_flow_analyzer.py --quick
```

若首次使用，先安裝依賴：
```bash
pip install pandas numpy openpyxl
```

## Step 2: 檢視輸出結果

腳本將輸出最新月份的關鍵指標：

```json
{
  "skill": "analyze_jgb_insurer_superlong_flow",
  "latest_month": {
    "date": "2025-12",
    "net_sale_100m_yen": 8224,
    "net_sale_trillion_yen": 0.8224,
    "interpretation": "淨賣出"
  },
  "record_analysis": {
    "is_record_sale": true,
    "record_sale_100m_yen": 8224,
    "record_sale_date": "2025-12"
  },
  "streak_analysis": {
    "consecutive_net_sale_months": 5,
    "cumulative_net_sale_100m_yen": 13959
  }
}
```

## Step 3: 解讀結果

**符號慣例（重要）**：

JSDA 使用「賣出 - 買入」計算差引：
- **正值 = 淨賣出**（賣出 > 買入，需求減少）
- **負值 = 淨買入**（買入 > 賣出，需求增加）

**關鍵指標解讀**：

| 指標                             | 意義                            |
|----------------------------------|---------------------------------|
| `net_sale_100m_yen`              | 最新月份淨賣出（億日圓）        |
| `is_record_sale`                 | 是否為歷史最大淨賣出（正值最大）|
| `consecutive_net_sale_months`    | 連續淨賣出月數                  |
| `cumulative_net_sale_100m_yen`   | 本輪連續淨賣出的累積金額        |

## Step 4: 生成摘要

根據結果生成可複製的摘要：

```markdown
### 日本保險公司超長期 JGB 淨買賣驗證（JSDA 公開數據）

- 本月（2025-12）：**淨賣出 8,224 億日圓**（0.82 兆日圓）
- 是否創紀錄：**是**（全樣本最大淨賣出）
- 連續淨賣出月數：**5 個月**（自 2025-08 起）
- 本輪累積淨賣出：**13,959 億日圓**（1.40 兆日圓）

> 註：天期桶採用 JSDA「超長期」分類（10 年以上利付債）。
> 數據來源：JSDA 公社債店頭売買高 (Trading Volume of OTC Bonds)
```

## Step 5: 強制重新下載數據（可選）

若需要最新數據，使用 `--refresh` 參數：

```bash
python scripts/jsda_flow_analyzer.py --quick --refresh
```

</process>

<success_criteria>
快速檢查完成時：

- [x] 成功抓取最新月份數據
- [x] 輸出淨賣出數值與正負判斷
- [x] 判斷是否為歷史極值
- [x] 計算連續淨賣出月數
- [x] 生成可複製的摘要
</success_criteria>
