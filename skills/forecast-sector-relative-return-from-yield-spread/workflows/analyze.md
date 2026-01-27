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

| 參數                  | 預設值            | 用戶指定值 |
|-----------------------|-------------------|------------|
| risk_ticker           | QQQ               |            |
| defensive_ticker      | XLV               |            |
| short_tenor           | 2Y                |            |
| long_tenor            | 10Y               |            |
| lead_months           | 24                |            |
| lookback_years        | 12                |            |
| freq                  | weekly            |            |
| smoothing_window      | 13                |            |
| return_horizon_months | 24                |            |
| model_type            | lagged_regression |            |
| confidence_level      | 0.80              |            |

若用戶未指定，使用預設值執行。

## Step 2: 執行分析腳本

使用確認的參數執行腳本：

```bash
cd skills/forecast-sector-relative-return-from-yield-spread
python scripts/spread_forecaster.py \
  --risk-ticker {risk_ticker} \
  --defensive-ticker {defensive_ticker} \
  --short-tenor {short_tenor} \
  --long-tenor {long_tenor} \
  --lead-months {lead_months} \
  --lookback-years {lookback_years} \
  --freq {freq} \
  --smoothing-window {smoothing_window} \
  --model-type {model_type} \
  --confidence-level {confidence_level} \
  --output result.json
```

**快速執行（使用所有預設值）：**
```bash
python scripts/spread_forecaster.py --quick
```

**執行領先掃描：**
```bash
python scripts/spread_forecaster.py --lead-scan --scan-range 6,12,18,24,30
```

## Step 3: 解讀分析結果

### 3.1 當前利差狀態

檢查 `current_spread` 區塊：

```json
{
  "current_spread": -0.35,
  "spread_percentile": 35,
  "spread_3m_change": 0.25,
  "spread_trend": "steepening"
}
```

**解讀邏輯：**
- `current_spread` < 0 → 曲線倒掛（短端高於長端）
- `spread_percentile` 35% → 處於歷史中等偏低位置
- `spread_3m_change` > 0 → 曲線正在變陡（從倒掛回正）

### 3.2 領先關係驗證

檢查 `model` 區塊：

```json
"model": {
  "type": "lagged_regression",
  "alpha": 0.02,
  "beta": -0.45,
  "fit_quality": {
    "corr_x_y": -0.32,
    "r_squared": 0.10,
    "p_value": 0.001
  }
}
```

**解讀邏輯：**
- `beta` 負值 → spread 越高，未來相對報酬越低（符合經濟直覺）
- `corr_x_y` = -0.32 → 中等負相關
- `r_squared` = 0.10 → spread 解釋約 10% 的相對報酬變異（其他 90% 由其他因子解釋）
- `p_value` < 0.05 → 統計顯著

**風險提示：** R² 僅 10% 意味 spread 不是主導因子。

### 3.3 預測結果

檢查 `forecast` 區塊：

```json
"forecast": {
  "future_24m_relative_return_log": -0.08,
  "future_24m_relative_return_pct": -0.077,
  "interval_pct_80": [-0.22, 0.04],
  "interpretation": "若此關係維持，未來24個月QQQ相對XLV期望報酬為-7.7%，XLV較可能跑贏。"
}
```

**解讀邏輯：**
- `future_24m_relative_return_pct` = -7.7% → 預期 QQQ 跑輸 XLV 約 7.7%
- `interval_pct_80` = [-22%, +4%] → 80% 機率落在此區間
- 區間含正值 → 不能排除 QQQ 仍跑贏的可能性

### 3.4 領先掃描結果（若執行）

檢查 `diagnostics.lead_scan` 區塊：

```json
"lead_scan": {
  "best_lead_months": 24,
  "correlation_by_lead": {
    "6": -0.15,
    "12": -0.22,
    "18": -0.28,
    "24": -0.32,
    "30": -0.30
  }
}
```

**解讀邏輯：**
- 相關性在 24 個月達到最高（-0.32）
- 18-30 個月區間相關性都較高，確認領先關係穩定

### 3.5 穩定性驗證

檢查 `diagnostics.stability_checks` 區塊：

```json
"stability_checks": {
  "first_half_corr": -0.30,
  "second_half_corr": -0.34,
  "consistency": "medium-high"
}
```

**解讀邏輯：**
- 前半段與後半段相關性接近 → 關係跨時期穩定
- `consistency` = "medium-high" → 領先關係可信度中高

## Step 4: 生成視覺化圖表（可選）

若需要視覺化，執行畫圖腳本：

**基本版（利差 vs 相對報酬對齊圖）：**
```bash
python scripts/spread_plotter.py --quick --output-dir ../../output
```

**完整版（含領先掃描熱圖、預測區間）：**
```bash
python scripts/spread_plotter.py --comprehensive --start-date 2007-01-01 --output-dir ../../output
```

**完整版圖表包含：**
1. 上圖：殖利率利差走勢（平移 lead_months 後）
2. 中圖：QQQ/XLV 相對報酬走勢
3. 下左：領先掃描相關性條形圖
4. 下右：預測區間分佈

圖表輸出路徑：
- 基本版：`output/spread_forecast_YYYY-MM-DD.png`
- 完整版：`output/spread_forecast_comprehensive_YYYY-MM-DD.png`

## Step 5: 生成報告

根據分析結果生成報告，使用 `templates/output-markdown.md` 或 `templates/output-json.md` 格式。

**報告應包含：**
1. 一句話結論（領先關係是否成立、預測方向）
2. 當前利差狀態與歷史分位數
3. 迴歸模型係數與解釋力
4. 未來相對報酬預測（點估計與區間）
5. 領先掃描結果（最佳領先期）
6. 穩定性驗證結果
7. 視覺化圖表（若生成）
8. 風險提示（模型限制）
9. 後續研究建議

## Step 6: 後續研究建議

根據分析結果提供交叉驗證建議：

**若預測 XLV 跑贏（spread 高/倒掛）：**
- 檢查經濟領先指標（如 ISM、消費者信心）
- 檢查企業獲利預測修正方向
- 觀察 Healthcare 防禦需求
- 評估成長股估值分位

**若預測 QQQ 跑贏（spread 低/變陡）：**
- 檢查經濟復甦訊號
- 觀察科技股資金流入
- 評估利率對成長股估值影響

**通用驗證：**
- 比較其他利差組合（3M-10Y, 2Y-30Y）
- 檢查 COT 持倉（利率期貨）
- 觀察信用利差變化

</process>

<success_criteria>
完成情境分析時應確認：

- [ ] 參數確認（使用預設或用戶指定）
- [ ] 腳本執行成功
- [ ] 當前利差狀態解讀
- [ ] 迴歸模型係數與顯著性
- [ ] 未來相對報酬預測（點估計與區間）
- [ ] 領先掃描結果（若執行）
- [ ] 穩定性驗證結果
- [ ] 視覺化圖表輸出（若需要）
- [ ] 報告生成（含風險提示）
- [ ] 後續研究建議
</success_criteria>
