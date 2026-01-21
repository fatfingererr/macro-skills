# Workflow: 完整情境分析

<required_reading>
**執行前請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/methodology.md - 方法論與計算邏輯
3. references/data-sources.md - 數據來源說明
</required_reading>

<process>

## Step 1: 確認分析參數

確認用戶提供或使用預設的分析參數：

| 參數                | 預設值          | 用戶指定值 |
|---------------------|-----------------|------------|
| miner_proxy         | SIL             |            |
| metal_proxy         | SI=F            |            |
| start_date          | 10 年前         |            |
| end_date            | 今日            |            |
| freq                | 1wk             |            |
| smoothing_window    | 4               |            |
| bottom_quantile     | 0.20            |            |
| top_quantile        | 0.80            |            |
| min_separation_days | 180             |            |
| forward_horizons    | [252, 504, 756] |            |
| scenario_target     | return_to_top   |            |

若用戶未指定，使用預設值執行。

## Step 2: 執行分析腳本

使用確認的參數執行腳本：

```bash
cd skills/analyze-silver-miner-metal-ratio
python scripts/ratio_analyzer.py \
  --miner-proxy {miner_proxy} \
  --metal-proxy {metal_proxy} \
  --start-date {start_date} \
  --freq {freq} \
  --smoothing-window {smoothing_window} \
  --bottom-quantile {bottom_quantile} \
  --top-quantile {top_quantile} \
  --min-separation-days {min_separation_days} \
  --scenario-target {scenario_target} \
  --output result.json
```

**快速執行（使用所有預設值）：**
```bash
python scripts/ratio_analyzer.py --quick
```

## Step 3: 解讀分析結果

### 3.1 當前狀態判讀

檢查 `current` 區塊：

```json
"current": {
  "ratio": 1.14,
  "ratio_percentile": 18.7,
  "zone": "bottom",
  "bottom_threshold": 1.16,
  "top_threshold": 2.45
}
```

**解讀邏輯：**
- `ratio_percentile` < 20 → 礦業相對白銀處於歷史低檔
- `zone` = "bottom" → 確認處於底部估值區
- 對照 `bottom_threshold` 和當前 `ratio` 驗證

### 3.2 歷史類比分析

檢查 `history_analogs` 區塊：

```json
"history_analogs": {
  "bottom_event_dates": ["2010-08-06", "2016-01-29", "2020-03-20"],
  "forward_metal_returns": {
    "252": {"count": 3, "median": 0.42, "win_rate": 1.0, "worst": 0.18}
  }
}
```

**解讀邏輯：**
- `bottom_event_dates`：歷史上落入底部區間的日期
- `forward_metal_returns`：這些日期後白銀的 1/2/3 年報酬
- `win_rate`：正報酬的機率
- `worst`：最差情境的報酬

**風險提示：** 樣本量僅 3 次，統計意義有限。

### 3.3 情境推演

檢查 `scenarios` 區塊：

```json
"scenarios": {
  "target": "return_to_top",
  "target_ratio": 2.45,
  "miner_multiplier_if_metal_flat": 2.15,
  "metal_drop_pct_if_miner_flat": 0.54
}
```

**解讀邏輯：**
- 若白銀不變，礦業需漲 `2.15x`（115%）才回到頂部估值
- 若礦業不變，白銀需跌 `54%` 才回到頂部估值
- 這是極端情境邊界，實際可能是兩者同時調整

## Step 4: 生成報告

根據分析結果生成報告，使用 `templates/output-markdown.md` 或 `templates/output-json.md` 格式。

**報告應包含：**
1. 一句話結論（當前是相對低估/高估/中性）
2. 當前比率與分位數
3. 類比證據（歷史事件與前瞻報酬）
4. 情境推演（回到頂部需要的條件）
5. 風險提示（比率訊號的限制）
6. 後續研究建議

## Step 5: 後續研究建議

根據分析結果提供交叉驗證建議：

**若處於底部區間：**
- 檢查礦業成本曲線（AISC 是否上升）
- 檢查 ETF 流量（SLV、SIL 的資金流向）
- 檢查 COT 持倉（投機部位是否極端）
- 檢查白銀實質利率與美元指數

**若處於頂部區間：**
- 檢查礦業是否有增產/併購動作
- 檢查成本通膨（柴油、工資、試劑）
- 評估均值回歸風險

</process>

<success_criteria>
完成情境分析時應確認：

- [ ] 參數確認（使用預設或用戶指定）
- [ ] 腳本執行成功
- [ ] 當前狀態解讀（比率、分位數、區間）
- [ ] 歷史類比分析（事件日期、前瞻報酬）
- [ ] 情境推演（礦業倍數、白銀跌幅）
- [ ] 報告生成（含風險提示）
- [ ] 後續研究建議
</success_criteria>
