<required_reading>
執行快速檢查前，了解基本概念：
- CASS Shipments YoY < 0 且創新低 → 通膨緩解訊號
- 領先 CPI 約 4-6 個月
</required_reading>

<objective>
快速檢查最新的 CASS Freight Index 狀態與通膨先行訊號。
</objective>

<process>

<step number="1" name="執行快速檢查">

```bash
cd skills/detect-freight-led-inflation-turn

# 首次使用需安裝依賴
pip install pandas numpy requests selenium webdriver-manager

# 執行快速檢查
python scripts/freight_inflation_detector.py --quick
```

**輸出範例**：
```json
{
  "as_of_date": "2025-12-01",
  "indicator": "shipments_yoy",
  "freight_yoy": -2.9,
  "cycle_status": "new_cycle_low",
  "signal": "inflation_easing",
  "confidence": "high",
  "macro_implication": "通膨壓力正在放緩，未來 CPI 下行風險上升",
  "all_indicators": {
    "shipments_yoy": -2.9,
    "expenditures_yoy": -1.5,
    "shipments_index": 1.15,
    "expenditures_index": 4.25
  }
}
```

</step>

<step number="2" name="解讀結果">

**訊號對照表**：

| signal | cycle_status | confidence | 含義 |
|--------|--------------|------------|------|
| `inflation_easing` | `new_cycle_low` | `high` | 強烈的通膨放緩訊號 |
| `inflation_easing` | `negative` | `medium` | 通膨可能開始降溫 |
| `neutral` | `positive` | `low` | 通膨方向待觀察 |
| `inflation_rising` | `positive` | `medium` | 通膨上行壓力可能延續 |

**快速判斷**：

```
如果 shipments_yoy < 0 且 cycle_status == new_cycle_low：
  → 通膨緩解訊號成立，預期 CPI 在未來 4-6 個月內放緩

如果 shipments_yoy > 0 且持續上升：
  → 通膨壓力可能延續

如果 shipments_yoy 在 0 附近震盪：
  → 中性，需要更多數據確認
```

**多指標交叉驗證**：

```
如果 shipments_yoy 和 expenditures_yoy 同時轉負：
  → 訊號更為可靠

如果兩者分歧：
  → 需要進一步分析原因
```

</step>

<step number="3" name="後續行動">

**若訊號為 `inflation_easing`**：
1. 執行完整分析確認（`workflows/analyze.md`）
2. 查看歷史案例對照（`references/historical-episodes.md`）
3. 考慮對利率敏感資產的配置調整

**若訊號為 `neutral` 或 `inflation_rising`**：
1. 設定監控頻率（每月檢查）
2. 關注其他通膨指標（CPI、PCE、PPI）
3. 留意 Fed 政策聲明

</step>

</process>

<quick_reference>

**CASS 四個指標快速對照**

| 指標 | 用途 | 解讀 |
|------|------|------|
| `shipments_yoy` | 主要分析指標 | < 0 → 需求減弱訊號 |
| `expenditures_yoy` | 交叉驗證 | < 0 → 運費成本壓力下降 |
| `shipments_index` | 絕對水準 | 長期趨勢參考 |
| `expenditures_index` | 絕對水準 | 運費支出水準 |

</quick_reference>

<success_criteria>
快速檢查完成時應得到：

- [ ] 最新 CASS Shipments YoY 數值
- [ ] 週期狀態判斷
- [ ] 通膨訊號評估
- [ ] 一句話宏觀含義
- [ ] 四個指標概覽
</success_criteria>
