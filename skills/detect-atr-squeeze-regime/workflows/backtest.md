# 歷史回測工作流

回溯識別過去的擠壓行情期間，評估識別準確性與持續時間統計。

## 前置條件

- 使用者提供了資產代碼和回測期間
- 建議至少 5 年數據以涵蓋多個週期

## 步驟

### Step 1: 確認參數

| 參數        | 說明       | 預設值               |
|-------------|------------|----------------------|
| symbol      | 資產代碼   | SI=F                 |
| start_date  | 回測起始日 | 2015-01-01           |
| end_date    | 回測結束日 | today                |
| output_file | 輸出檔案   | backtest_result.json |

### Step 2: 執行回測

```bash
cd skills/detect-atr-squeeze-regime
python scripts/atr_squeeze.py \
  --symbol SI=F \
  --start 2015-01-01 \
  --end 2026-01-01 \
  --backtest \
  --output backtest_result.json
```

### Step 3: 識別擠壓期間

腳本會輸出所有識別到的擠壓期間：

```json
{
  "squeeze_periods": [
    {
      "start": "2020-03-09",
      "end": "2020-04-15",
      "duration_days": 37,
      "peak_atr_pct": 12.45,
      "peak_ratio": 4.15,
      "peak_date": "2020-03-16",
      "context": "COVID-19 市場恐慌"
    },
    {
      "start": "2024-07-22",
      "end": "2024-08-28",
      "duration_days": 37,
      "peak_atr_pct": 8.92,
      "peak_ratio": 2.97,
      "peak_date": "2024-08-05",
      "context": "日圓套利平倉風暴"
    }
  ]
}
```

### Step 4: 計算統計指標

**擠壓期間統計**：

| 指標          | 數值   |
|---------------|--------|
| 擠壓期間總數  | N      |
| 平均持續天數  | X days |
| 最長持續天數  | Y days |
| 平均峰值 ATR% | Z%     |
| 平均峰值倍率  | W x    |

**行情分布**：

| 行情                         | 佔比 | 天數 |
|------------------------------|------|------|
| orderly_market               | 70%  | 2555 |
| elevated_volatility_trend    | 22%  | 803  |
| volatility_dominated_squeeze | 8%   | 292  |

### Step 5: 與重大事件對照

將識別的擠壓期間與已知市場事件對照：

| 期間    | 事件          | 匹配 |
|---------|---------------|------|
| 2020-03 | COVID-19 崩盤 | YES  |
| 2022-03 | 俄烏戰爭爆發  | YES  |
| 2024-08 | 日圓套利平倉  | YES  |

### Step 6: 生成回測報告

報告結構：

1. **回測摘要**
   - 回測期間
   - 資料點數量
   - 行情分布統計

2. **擠壓期間清單**
   - 起止日期
   - 持續天數
   - 峰值數據
   - 事件背景

3. **視覺化圖表**（可選）
   - ATR% 時間序列
   - 行情標記條帶
   - 峰值標註

4. **準確性評估**
   - 與已知事件的匹配率
   - 假陽性/假陰性分析

## 回測輸出範例

```json
{
  "skill": "detect-atr-squeeze-regime",
  "symbol": "SI=F",
  "backtest_period": {
    "start": "2015-01-01",
    "end": "2026-01-14"
  },
  "data_points": 2778,
  "regime_distribution": {
    "orderly_market": {"days": 1945, "pct": 70.0},
    "elevated_volatility_trend": {"days": 611, "pct": 22.0},
    "volatility_dominated_squeeze": {"days": 222, "pct": 8.0}
  },
  "squeeze_periods": [...],
  "statistics": {
    "total_squeeze_periods": 5,
    "avg_duration_days": 44.4,
    "max_duration_days": 67,
    "avg_peak_atr_pct": 9.8,
    "avg_peak_ratio": 3.27
  },
  "known_events_matched": 4,
  "known_events_total": 5,
  "match_rate": 0.80
}
```

## 視覺化輸出

若安裝了 matplotlib：

```bash
python scripts/atr_squeeze.py --symbol SI=F --backtest --plot --output chart.png
```

圖表包含：
- 上圖：價格走勢
- 中圖：ATR% 與基準
- 下圖：行情條帶（紅=squeeze, 黃=elevated, 綠=orderly）

## 注意事項

- 回測使用「預知」的 3 年基準，實際交易時基準是滾動計算的
- 邊界效應：前 756 天（約 3 年）無法計算有效基準
- 建議從 start_date 前額外取 3 年數據以避免邊界問題
