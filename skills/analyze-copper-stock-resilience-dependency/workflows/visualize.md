# Workflow: 視覺化圖表

<required_reading>
**執行前請閱讀：**
1. references/data-sources.md - 確認資料來源
</required_reading>

<process>

## Step 1: 準備數據

確保已執行過完整分析，產生 `result.json`：

```bash
python scripts/copper_stock_analyzer.py \
    --start 2020-01-01 \
    --end 2026-01-20 \
    --output data/result.json
```

## Step 2: 生成視覺化圖表

### 2.1 主圖表（銅價 + 股市韌性 + 殖利率）

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/copper_analysis.png \
    --chart main
```

此圖表包含：
- **上半部**：銅價與 60 月 SMA，標記關卡位置（10,000 / 13,000）
- **中間**：股市韌性評分（0-100）
- **下半部**：中國 10Y 殖利率

### 2.2 依賴關係圖（滾動 Beta）

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/copper_beta.png \
    --chart beta
```

此圖表包含：
- **上半部**：銅價走勢
- **下半部**：滾動 β_equity 與 β_yield，標記高/低分位區間

### 2.3 回補事件分析圖

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/backfill_analysis.png \
    --chart backfill
```

此圖表包含：
- 銅價走勢，標記觸及 13,000 的時點
- 區分「續航」（綠色）與「回補」（紅色）事件
- 各事件對應的股市韌性評分

### 2.4 生成所有圖表

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/ \
    --chart all
```

## Step 3: 圖表配置選項

### 自定義樣式

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/copper_analysis.png \
    --chart main \
    --style dark \
    --figsize 14,10 \
    --dpi 150
```

### 可用選項

| 選項 | 預設值 | 說明 |
|------|--------|------|
| `--style` | light | light / dark / paper |
| `--figsize` | 12,8 | 圖表尺寸（寬,高） |
| `--dpi` | 100 | 解析度 |
| `--show-events` | true | 是否標記事件 |
| `--levels` | 10000,13000 | 關卡位置 |

## Step 4: 互動式圖表（可選）

使用 Plotly 生成互動式 HTML：

```bash
python scripts/visualize.py \
    -i data/result.json \
    -o output/copper_interactive.html \
    --format html
```

此圖表支援：
- 縮放與平移
- 懸停顯示數值
- 時間區間選擇

</process>

<success_criteria>
視覺化成功時應產出：

- [ ] 主圖表（銅價 + 韌性 + 殖利率）
- [ ] 依賴關係圖（滾動 Beta）
- [ ] 回補事件分析圖
- [ ] 圖表檔案存放於 `output/` 目錄
- [ ] 圖表清晰可讀，關卡位置標記明確
</success_criteria>
