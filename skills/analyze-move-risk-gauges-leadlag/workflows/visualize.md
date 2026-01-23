# Workflow: Bloomberg 風格視覺化圖表

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 了解各圖表的含義
2. thoughts/shared/guide/bloomberg-style-chart-guide.md - Bloomberg 風格規範
</required_reading>

<process>

## Step 1: 執行視覺化

### 方式一：分析時同時生成圖表（推薦）

```bash
cd .claude/skills/analyze-move-risk-gauges-leadlag/scripts
python analyze.py --start 2024-01-01 --end 2026-01-31 --output-mode markdown --chart
```

### 方式二：單獨生成圖表

```bash
# 使用快取數據（若有）
python visualize.py --start 2024-01-01 --end 2026-01-31

# 指定輸出路徑
python visualize.py --start 2024-01-01 --end 2026-01-31 -o output/custom-chart.png

# 高解析度輸出
python visualize.py --start 2024-01-01 --end 2026-01-31 --dpi 300
```

圖表預設輸出路徑：`output/move-leadlag-YYYY-MM-DD.png`

## Step 2: 圖表說明

### 2x3 多面板結構

```
┌──────────────────────┬─────────────────────────────────────────────┐
│ 左上 (1,1): 交叉相關  │ 右上 (1,2)+(1,3): 波動率指標時間序列         │
│   • MOVE vs VIX 曲線  │   • MOVE Index（左軸，橙紅）                 │
│   • MOVE vs Credit   │   • VIX（右軸，橙黃）                        │
│   • 最佳 lag 標記     │   • JGB 衝擊事件（紅色虛線）                 │
│                      │   • 最新 MOVE 數值標註                       │
├──────────────────────┼─────────────────────────────────────────────┤
│ 左下 (2,1): 事件反應  │ 右下 (2,2)+(2,3): 標準化序列（Z 分數）       │
│   • 直方圖（橙紅）    │   • MOVE Z（橙紅）                          │
│   • 平均反應線       │   • VIX Z（橙黃）                           │
│   • 恐慌判定框       │   • Credit Z（黃色）                        │
│                      │   • 當前 MOVE Z 標記點                       │
└──────────────────────┴─────────────────────────────────────────────┘
```

### Bloomberg 配色方案

| 元素           | 顏色代碼   | 說明                 |
|----------------|------------|----------------------|
| 背景           | `#1a1a2e`  | 深藍黑色             |
| MOVE           | `#ff6b35`  | 橙紅色（主要指標）   |
| VIX            | `#ffaa00`  | 橙黃色（次要指標）   |
| Credit         | `#ffff00`  | 黃色（第三指標）     |
| JGB/未恐慌     | `#00ff88`  | 綠色                 |
| 衝擊/恐慌      | `#ff4444`  | 紅色                 |
| 網格線         | `#2d2d44`  | 暗灰紫               |
| 文字           | `#ffffff`  | 白色                 |

### Panel 1: 交叉相關分析（左上）

- **X 軸**: Lag（天數），正值 = MOVE 領先
- **Y 軸**: 相關係數
- **曲線**: MOVE vs VIX（橙黃）、MOVE vs Credit（綠色）
- **最佳點**: 最大相關係數位置以圓點標記，並標註 lag 與 r 值

### Panel 2: 事件反應分布（左下）

- **直方圖**: JGB 衝擊發生時 MOVE 的變化分布（橙紅）
- **平均線**: 橙黃色虛線標示平均反應
- **判定框**: 右上角顯示「判定: 恐慌」或「判定: 未恐慌」

### Panel 3: 波動率時間序列（右上，跨兩格）

- **左軸**: MOVE Index（橙紅線，線寬 2）
- **右軸**: VIX（橙黃線，透明度 0.8）
- **衝擊事件**: JGB 殖利率變動 ≥ 15bp 時標記紅色虛線
- **最新值標註**: 圖表右端顯示當前 MOVE 數值

### Panel 4: Z 分數標準化序列（右下，跨兩格）

- **三條曲線**: MOVE Z、VIX Z、Credit Z（同一尺度）
- **參考線**: Z = 0（實線）、Z = ±1（灰虛線）、Z = ±2（紅虛線）
- **當前標記**: 最新 MOVE Z 分數以圓點標記

### 頁尾資訊

- **中央偏左**: 一句話結論（headline）
- **右下**: 截止日期

## Step 3: 輸出選項

### CLI 參數

```bash
usage: visualize.py [-h] [-i INPUT] [-o OUTPUT] [--start START] [--end END] [--dpi DPI]

options:
  -i, --input   輸入 JSON 結果檔案（可選，會自動執行分析）
  -o, --output  輸出圖片路徑（預設: output/move-leadlag-YYYY-MM-DD.png）
  --start       起始日期 (YYYY-MM-DD)
  --end         結束日期 (YYYY-MM-DD)
  --dpi         解析度（預設: 150，印刷用: 300）
```

### 輸出範例

```bash
# 標準輸出
python visualize.py --start 2024-01-01 --end 2026-01-31
# → output/move-leadlag-2026-01-23.png (16x12 in, 150 DPI)

# 高解析度印刷
python visualize.py --start 2024-01-01 --end 2026-01-31 --dpi 300
# → output/move-leadlag-2026-01-23.png (16x12 in, 300 DPI)

# 自定義路徑
python visualize.py --start 2024-01-01 --end 2026-01-31 -o reports/2026Q1.png
```

</process>

<success_criteria>
完成此 workflow 時：

- [ ] 生成 Bloomberg 風格 2x3 佈局圖表
- [ ] 左上 (1,1): 交叉相關分析與最佳 lag 標註
- [ ] 左下 (2,1): 事件反應分布與恐慌判定
- [ ] 右上 (跨2格): MOVE/VIX 時間序列與衝擊事件標記
- [ ] 右下 (跨2格): Z 分數與當前 MOVE 標記
- [ ] 圖表包含截止日期、結論
- [ ] 圖表已保存到指定路徑
</success_criteria>
