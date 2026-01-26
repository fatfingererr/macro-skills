# Workflow: 完整分析

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認 JSDA 數據可用性與下載方式
2. references/methodology.md - 了解 streak、record、cumulative 計算邏輯
</required_reading>

<process>

## Step 1: 確認分析參數

**可選參數**：
- `--start-year`: 起始財年（預設 2018，日本財年 4 月開始）
- `--lookback`: 回溯月數（預設全樣本）
- `--format`: 輸出格式（`json` 或 `markdown`，預設 markdown）
- `--refresh`: 強制重新下載數據

## Step 2: 抓取 JSDA 數據

數據會自動從 JSDA 網站下載並緩存：

```bash
cd .claude/skills/analyze-jgb-insurer-superlong-flow
python scripts/jsda_flow_analyzer.py --full --refresh
```

**數據來源**：
- 當前財年：`https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai.xlsx`
- 歷史財年：`https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai{YYYY}.xlsx`

腳本會：
1. 從 JSDA 下載最新 Excel 檔案
2. 解析 Sheet「(Ｊ)合計差引」
3. 提取「生保・損保」的「超長期」淨賣出數據
4. 緩存到 `data/cache/` 目錄

## Step 3: 執行完整分析

```bash
# Markdown 格式輸出
python scripts/jsda_flow_analyzer.py --full

# JSON 格式輸出
python scripts/jsda_flow_analyzer.py --full --format json

# 指定起始年份
python scripts/jsda_flow_analyzer.py --full --start-year 2020

# 輸出到檔案
python scripts/jsda_flow_analyzer.py --full --format json --output ../../output/analysis.json
```

## Step 4: 計算關鍵指標

### 4.1 符號慣例（重要）

JSDA 使用「賣出 - 買入」計算差引：
```
net_sale = 売付額 - 買付額
```

- **正值 = 淨賣出**（賣出 > 買入，需求減少）
- **負值 = 淨買入**（買入 > 賣出，需求增加）

### 4.2 判斷是否為歷史極值

```python
record_high = max(series)  # 最大淨賣出（正值最大）
is_record_sale = (latest == record_high) and (latest > 0)
```

### 4.3 計算連續淨賣出月數

```python
def calc_streak(series):
    streak = 0
    for v in reversed(series.values):
        if v > 0:  # 正值 = 淨賣出
            streak += 1
        else:
            break
    return streak
```

### 4.4 計算本輪累積淨賣出

```python
cumulative = series.tail(streak_len).sum()
```

## Step 5: 口徑說明

**數據口徑**：
- **投資人分類**：生保・損保（Life & Non-Life Insurance Companies）
- **天期桶**：超長期（Interest-bearing Long-term over 10-year）
- **交易類型**：店頭交易（OTC），不含交易所交易
- **單位**：億日圓（100 million yen）

## Step 6: 生成完整報告

Markdown 輸出範例：

```markdown
## 日本保險公司超長期 JGB 淨買賣驗證報告

**分析期間**：2021-04 ~ 2025-12（57 個月）

### 核心結論

| 指標 | 數值 | 說明 |
|------|------|------|
| 本月（2025-12）| **8,224 億日圓** | 淨賣出 |
| 是否創歷史紀錄 | **✓ 是** | 全樣本 (57 個月) |
| 連續淨賣出月數 | **5 個月** | 自 2025-08 起 |
| 本輪累積淨賣出 | **13,959 億日圓** | 1.40 兆日圓 |

### 歷史統計

| 指標 | 數值 |
|------|------|
| 平均值 | -2,872 億/月（淨買入為主）|
| 標準差 | 3,830 億 |
| Z-score | 2.90（極端淨賣出）|
| 分位數 | 98.25%（歷史高位）|

### Headline Takeaways

1. ✓ 驗證屬實：日本保險公司在 2025/12 創下歷史最大單月淨賣出
2. 已連續 5 個月淨賣出超長期國債，累積 1.40 兆日圓
3. 當前淨賣出規模處於歷史極端區間（Z-score: 2.90）
```

## Step 7: 輸出 JSON（結構化）

```bash
python scripts/jsda_flow_analyzer.py --full --format json --output ../../output/jgb-insurer-superlong-flow-2025-12.json
```

JSON 輸出包含完整的數據來源、參數、分析結果和 headline takeaways。

</process>

<success_criteria>
完整分析完成時：

- [x] 成功抓取指定期間的 JSDA 數據
- [x] 計算並輸出最新月份淨賣出數值
- [x] 判斷是否為歷史極值（含回溯期間說明）
- [x] 計算連續淨賣出月數與累積金額
- [x] 提供歷史分布統計（均值、標準差、Z-score）
- [x] 明確標示天期桶與投資人口徑
- [x] 生成完整 Markdown 或 JSON 報告
</success_criteria>
