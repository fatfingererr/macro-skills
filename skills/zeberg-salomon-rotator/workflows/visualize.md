# Workflow: 視覺化回測結果

<required_reading>
**執行前請先閱讀：**
1. workflows/backtest.md - 完整回測工作流程
</required_reading>

<process>

## Step 1: 執行回測

先執行完整回測以獲取數據：

```bash
python scripts/rotator.py --start 2000-01-01 --end 2026-01-01 --output result.json
```

## Step 2: 生成視覺化圖表

使用 `scripts/visualize.py` 生成多面板圖表：

```bash
# 從 JSON 檔案讀取
python scripts/visualize.py -i result.json -o output/zeberg-salomon-YYYY-MM-DD.png

# 或透過 pipe 直接生成
python scripts/rotator.py --start 2000-01-01 --end 2026-01-01 2>/dev/null | \
  python scripts/visualize.py -o output/zeberg-salomon-$(date +%Y-%m-%d).png
```

## Step 3: 圖表說明

生成的圖表包含四個面板：

### Panel 1: 景氣指標面板 (上)
- **Leading Index** (藍色): 領先指標，預測經濟轉折
- **Coincident Index** (紫色): 同時指標，確認經濟狀態
- **Iceberg Threshold** (橙色虛線): 冰山門檻 (-0.3)
- **Sinking Threshold** (紅色虛線): 下沉門檻 (-0.5)
- **背景色**: 綠色=RISK_ON, 紅色=RISK_OFF
- **圓點標記**: 切換事件位置

### Panel 2: 累積報酬面板 (中)
- **黑色粗線**: 策略累積報酬
- **藍色虛線**: SPY 買入持有基準
- **紫色虛線**: TLT 買入持有基準
- **三角形標記**: ▼=進入 RISK_OFF, ▲=進入 RISK_ON

### Panel 3: 狀態條帶 (下)
- **綠色區段**: RISK_ON (持有股票)
- **紅色區段**: RISK_OFF (持有長債)

### Panel 4: 績效摘要
- CAGR、總切換次數、當前狀態、最新指標值

## 參數選項

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `-i, --input` | 輸入 JSON 檔案路徑 | stdin |
| `-o, --output` | 輸出圖片路徑 | `output/zeberg-salomon-YYYY-MM-DD.png` |
| `--show` | 互動式顯示圖表 | False |

</process>

<success_criteria>
視覺化完成時應產出：

- [ ] 多面板 PNG 圖表
- [ ] 檔名包含當天日期
- [ ] 圖表儲存於 `output/` 目錄
</success_criteria>
