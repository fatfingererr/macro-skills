# Workflow: 視覺化分析

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 形狀比對方法論
2. templates/output-markdown.md - 報告格式
</required_reading>

<process>

## Step 1: 確認依賴

```bash
pip install matplotlib pandas numpy requests scipy
```

## Step 2: 執行視覺化腳本

```bash
cd skills/detect-fed-unamortized-discount-pattern
python scripts/visualize_pattern.py -o output
```

**參數選項**：
- `-o, --output`: 輸出目錄（預設 output）
- `--target_series`: 目標序列（預設 WUDSHO）
- `--recent_days`: 近期窗口天數（預設 120）
- `--baseline`: 基準窗口名稱（預設 COVID_2020）

## Step 3: 輸出圖表說明

### 圖表 1: 形狀比對圖 (`pattern_comparison_YYYY-MM-DD.png`)

**內容**：
- 上圖：近期窗口 vs. 歷史基準窗口的正規化走勢疊加
- 下圖：原始數值走勢（雙 Y 軸）

**標註**：
- 相關係數、DTW 距離、形狀特徵相似度
- 時間對齊說明

### 圖表 2: 壓力指標儀表板 (`stress_dashboard_YYYY-MM-DD.png`)

**內容**：
- 各交叉驗證指標的當前 z-score
- 歷史分布參考（分位數標示）
- 壓力門檻線

**色彩編碼**：
- 綠色：中性（無壓力）
- 黃色：警戒（z-score 接近門檻）
- 紅色：壓力（z-score 超過門檻）

### 圖表 3: 歷史走勢對照 (`historical_overlay_YYYY-MM-DD.png`)

**內容**：
- WUDSHO 完整歷史走勢
- 標記所有基準窗口位置
- 當前位置標註

## Step 4: 輸出檔案清單

執行後應產生：

```
output/
├── pattern_comparison_YYYY-MM-DD.png    # 形狀比對圖
├── stress_dashboard_YYYY-MM-DD.png      # 壓力指標儀表板
├── historical_overlay_YYYY-MM-DD.png    # 歷史走勢對照
└── pattern_analysis_YYYY-MM-DD.json     # JSON 結果
```

## Step 5: 圖表解讀指引

### 如何解讀形狀比對圖

1. **看形狀趨勢**：兩條線是否「同漲同跌」
2. **看時間對齊**：拐點是否在相似位置
3. **看相關係數**：> 0.7 為高度相似
4. **看 DTW 距離**：< 0.5 為高度相似

### 如何解讀壓力儀表板

1. **綠色居多**：壓力驗證不支持風險假說
2. **黃色居多**：需要持續觀察
3. **紅色居多**：壓力驗證支持風險假說

### 綜合判讀

| 形狀相似度 | 壓力儀表板 | 解讀                            |
|------------|------------|---------------------------------|
| 高         | 綠色       | 可能是利率/會計效果，非真正壓力 |
| 高         | 黃/紅      | 需要提高警覺，持續觀察          |
| 低         | 任何       | 形狀不相似，圖形類比不成立      |

</process>

<success_criteria>
工作流完成時應產出：

- [ ] `pattern_comparison_YYYY-MM-DD.png` - 形狀比對圖
- [ ] `stress_dashboard_YYYY-MM-DD.png` - 壓力指標儀表板
- [ ] `historical_overlay_YYYY-MM-DD.png` - 歷史走勢對照
- [ ] `pattern_analysis_YYYY-MM-DD.json` - JSON 結果
- [ ] 圖表清晰可讀，標註完整
</success_criteria>
