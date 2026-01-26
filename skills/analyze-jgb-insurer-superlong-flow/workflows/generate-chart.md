# Workflow: 生成視覺化圖表

<required_reading>
**執行前請先閱讀**：
1. references/data-sources.md - 確認數據可用性
2. thoughts/shared/guide/bloomberg-style-chart-guide.md - Bloomberg 風格設計規範
</required_reading>

<process>

## Step 1: 確認圖表參數

**可選參數**：
- `--output-dir`: 輸出目錄（預設專案根目錄 `output/`）
- `--filename`: 輸出檔名（預設 `jgb-insurer-superlong-flow-YYYYMMDD.png`）
- `--no-rolling`: 不顯示 12M 滾動累積線
- `--no-stats`: 不顯示統計摘要面板
- `--no-record`: 不標記創紀錄月份
- `--refresh`: 強制重新下載數據

## Step 2: 安裝依賴

```bash
pip install pandas numpy openpyxl matplotlib
```

## Step 3: 生成圖表

```bash
cd .claude/skills/analyze-jgb-insurer-superlong-flow
python scripts/generate_flow_chart.py --output-dir ../../../output
```

輸出：`output/jgb-insurer-superlong-flow-YYYYMMDD.png`

## Step 4: 圖表內容說明

生成的圖表遵循 Bloomberg 風格設計：

### 4.1 配色方案

| 元素 | 顏色 | 說明 |
|------|------|------|
| 背景 | #1a1a2e | 深藍黑色 |
| 網格 | #2d2d44 | 暗灰紫色 |
| 淨賣出柱 | #ff4444 | 紅色（需求↓）|
| 淨買入柱 | #00ff88 | 綠色（需求↑）|
| 12M 滾動線 | #ffaa00 | 橙黃色 |
| 創紀錄標記 | #ff00ff | 品紅色 |

### 4.2 主圖：淨賣出/買入柱狀圖

- X 軸：時間（月度，年為主刻度）
- Y 軸：淨賣出金額（億日圓）
- 正值（紅色）：淨賣出（賣出 > 買入）
- 負值（綠色）：淨買入（買入 > 賣出）
- 零線：水平參考線

### 4.3 疊加：12M 滾動累積線

- 橙黃色虛線
- 顯示過去 12 個月的累積淨賣出
- 便於識別中期趨勢轉向

### 4.4 創紀錄月份標記

- 品紅色箭頭標註
- 顯示紀錄值（億日圓）

### 4.5 統計摘要面板

位於左上角，包含：
- 最新月份與數值
- 連續淨賣出月數
- 本輪累積金額
- Z-score
- 創紀錄月份與數值

### 4.6 頁尾資訊

- 資料來源：JSDA 公社債店頭売買高
- 截至日期、投資人類型、天期桶

## Step 5: 自訂選項

```bash
# 不顯示滾動線
python scripts/generate_flow_chart.py --no-rolling

# 不顯示統計面板
python scripts/generate_flow_chart.py --no-stats

# 指定檔名
python scripts/generate_flow_chart.py --filename my-chart.png

# 完整選項
python scripts/generate_flow_chart.py \
  --output-dir ../../../output \
  --filename jgb-flow-custom.png \
  --refresh
```

## Step 6: 輸出範例

生成的圖表範例位置：
```
output/jgb-insurer-superlong-flow-20260126.png
```

圖表特點：
- Bloomberg 終端風格深色背景
- 清晰的紅綠對比顯示淨賣出/買入
- 12M 滾動線便於識別趨勢
- 左上角統計摘要面板
- 創紀錄月份明確標記
- 完整的頁尾資訊標註

</process>

<success_criteria>
圖表生成完成時：

- [x] 成功生成 PNG 圖表
- [x] 採用 Bloomberg 風格深色背景
- [x] 正確顯示淨賣出（紅色）vs 淨買入（綠色）
- [x] 顯示 12M 滾動累積線
- [x] 標記創紀錄月份
- [x] 包含統計摘要面板
- [x] 明確標示天期桶口徑與數據來源
- [x] 輸出到指定目錄
</success_criteria>
