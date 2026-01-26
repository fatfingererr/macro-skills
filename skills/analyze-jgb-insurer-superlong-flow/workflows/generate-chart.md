# Workflow: 生成視覺化圖表

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認數據可用性
2. references/methodology.md - 了解指標定義
</required_reading>

<process>

## Step 1: 確認圖表參數

**可選參數**：
- `start_date`: 圖表起始年月（預設 5 年前）
- `end_date`: 圖表結束年月（預設最新）
- `maturity_bucket`: 天期桶（預設 super_long）
- `output_dir`: 輸出目錄（預設 `../../output`）

## Step 2: 抓取數據

```bash
cd skills/analyze-jgb-insurer-superlong-flow
python scripts/fetch_jsda_data.py --refresh
```

## Step 3: 生成圖表

```bash
python scripts/generate_flow_chart.py \
  --start 2020-01 \
  --end 2025-12 \
  --maturity super_long \
  --output-dir ../../output
```

輸出：`output/jgb_insurer_flow_YYYYMMDD.png`

## Step 4: 圖表內容說明

生成的圖表包含：

### 4.1 主圖：淨買賣月度走勢

- X 軸：時間（月度）
- Y 軸：淨買入金額（十億日圓）
- 正值區域：綠色（淨買入）
- 負值區域：紅色（淨賣出）
- 標記：創紀錄月份特別標註

### 4.2 副圖：累積走勢

- 顯示滾動 12 個月累積淨買入
- 便於識別中期趨勢

### 4.3 統計摘要面板

- 最新月份數值
- 連續賣超月數
- 本輪累積金額
- 歷史分位數

## Step 5: 圖表格式選項

```bash
# PNG 格式（預設）
python scripts/generate_flow_chart.py --format png

# PDF 格式（高品質列印）
python scripts/generate_flow_chart.py --format pdf

# 互動式 HTML（含 hover 資訊）
python scripts/generate_flow_chart.py --format html
```

## Step 6: 自定義樣式

```bash
# Bloomberg 風格（深色背景）
python scripts/generate_flow_chart.py --style bloomberg

# 簡潔風格（白色背景）
python scripts/generate_flow_chart.py --style minimal

# 報告風格（適合嵌入文件）
python scripts/generate_flow_chart.py --style report
```

## Step 7: 多口徑對比圖

```bash
# 同時顯示 long 與 super_long
python scripts/generate_flow_chart.py --compare long,super_long

# 顯示合併的 10Y+
python scripts/generate_flow_chart.py --maturity long_plus_super_long
```

</process>

<success_criteria>
圖表生成完成時：

- [ ] 成功生成 PNG/PDF/HTML 圖表
- [ ] 圖表包含月度淨買賣走勢
- [ ] 正確標註正負區間（淨買入 vs 淨賣出）
- [ ] 標記創紀錄月份
- [ ] 包含統計摘要面板
- [ ] 明確標示天期桶口徑與數據來源
</success_criteria>
