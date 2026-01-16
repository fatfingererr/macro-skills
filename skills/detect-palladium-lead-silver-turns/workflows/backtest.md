# Workflow: 歷史回測

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 了解跨金屬確認邏輯
2. references/input-schema.md - 完整參數定義
3. references/data-sources.md - 數據來源與覆蓋範圍
</required_reading>

<process>

## Step 1: 定義回測範圍

確認以下參數：

| 參數              | 範例值       | 說明                   |
|-------------------|--------------|------------------------|
| silver_symbol     | SI=F         | 白銀標的代碼           |
| palladium_symbol  | PA=F         | 鈀金標的代碼           |
| timeframe         | 1h           | 分析時間尺度           |
| start_date        | 2024-01-01   | 回測開始日期           |
| end_date          | 2026-01-01   | 回測結束日期           |

建議回測至少 6 個月以上的數據以獲得統計有效性。

## Step 2: 執行回測

```bash
cd skills/detect-palladium-lead-silver-turns
python scripts/palladium_lead_silver.py \
  --silver SI=F \
  --palladium PA=F \
  --timeframe 1h \
  --start 2024-01-01 \
  --end 2026-01-01 \
  --backtest \
  --output backtest_result.json
```

## Step 3: 分析領先滯後穩定性

檢查輸出中的 `lead_lag_analysis` 區塊：

```json
{
  "lead_lag_analysis": {
    "best_lag": 6,
    "correlation": 0.42,
    "confidence_interval": [3, 9],
    "stability": {
      "rolling_windows": [
        {"period": "2024-Q1", "lag": 5, "corr": 0.38},
        {"period": "2024-Q2", "lag": 7, "corr": 0.45},
        {"period": "2024-Q3", "lag": 6, "corr": 0.41},
        {"period": "2024-Q4", "lag": 6, "corr": 0.44}
      ],
      "is_stable": true,
      "std_deviation": 0.8
    }
  }
}
```

### 穩定性判斷標準

| 指標           | 穩定閾值 | 說明                   |
|----------------|----------|------------------------|
| std_deviation  | < 2.0    | 各期 lag 標準差        |
| corr_range     | < 0.2    | 相關係數變動範圍       |
| direction_flip | 0        | lag 正負號翻轉次數     |

## Step 4: 分析確認有效性

檢查 `confirmation_analysis` 區塊：

```json
{
  "confirmation_analysis": {
    "total_ag_turns": 48,
    "confirmed_turns": 34,
    "confirmation_rate": 0.71,
    "by_type": {
      "top": {"total": 24, "confirmed": 16, "rate": 0.67},
      "bottom": {"total": 24, "confirmed": 18, "rate": 0.75}
    },
    "confirmation_lag_distribution": {
      "mean": -2.3,
      "median": -3,
      "std": 1.8
    }
  }
}
```

### 有效性指標

| 指標                | 良好閾值 | 說明                   |
|---------------------|----------|------------------------|
| confirmation_rate   | > 0.6    | 整體確認率             |
| rate_diff_top_bottom| < 0.2    | 頂底確認率差異         |
| lag_std             | < 3.0    | 確認滯後的穩定性       |

## Step 5: 分析失敗走勢

檢查 `failure_analysis` 區塊：

```json
{
  "failure_analysis": {
    "unconfirmed_events": 14,
    "failed_moves": 9,
    "unconfirmed_failure_rate": 0.64,
    "confirmed_events": 34,
    "confirmed_failures": 6,
    "confirmed_failure_rate": 0.18,
    "failure_rate_ratio": 3.6,
    "average_revert_bars": {
      "unconfirmed": 8.2,
      "confirmed": 15.6
    }
  }
}
```

### 關鍵發現

1. **失敗率比值 (failure_rate_ratio)**
   - > 2.0：跨金屬確認有顯著過濾價值
   - 1.5 - 2.0：確認有一定幫助但不顯著
   - < 1.5：確認邏輯在此數據集上無效

2. **平均回撤速度 (average_revert_bars)**
   - 未確認事件回撤更快 → 確認邏輯有效

## Step 6: 生成回測報告

```bash
# 生成 Markdown 報告
python scripts/palladium_lead_silver.py \
  --silver SI=F \
  --palladium PA=F \
  --backtest \
  --format markdown \
  --output backtest_report.md
```

報告內容：
1. **數據概覽**：時間範圍、樣本數
2. **領先滯後分析**：最佳 lag、穩定性
3. **確認有效性**：確認率、分布
4. **失敗走勢統計**：失敗率比較
5. **結論與建議**

## Step 7: 視覺化回測結果（可選）

```bash
python scripts/plot_palladium_silver.py \
  --silver SI=F \
  --palladium PA=F \
  --start 2024-01-01 \
  --end 2026-01-01 \
  --backtest \
  --output output/backtest/
```

輸出圖表：
- 價格疊加與所有拐點標記
- 確認 vs 未確認事件的後續表現
- 滾動領先滯後時間序列
- 失敗率按時間分布

</process>

<interpretation_guide>

## 結果解讀指南

### 領先滯後解讀

| 結果                | 含義                       | 建議               |
|---------------------|----------------------------|--------------------|
| lag > 0, corr > 0.3 | 鈀金有效領先白銀           | 可用於確認         |
| lag > 0, corr < 0.3 | 領先關係弱                 | 謹慎使用           |
| lag ≈ 0             | 同步移動                   | 調整參數或時間尺度 |
| lag < 0             | 白銀領先鈀金               | 反向使用確認邏輯   |

### 確認有效性解讀

| 確認率  | 失敗率比值 | 結論                     |
|---------|------------|--------------------------|
| > 70%   | > 3.0      | 確認邏輯非常有效         |
| > 60%   | > 2.0      | 確認邏輯有效             |
| > 50%   | > 1.5      | 確認邏輯有一定幫助       |
| < 50%   | < 1.5      | 確認邏輯在此數據集無效   |

### 穩定性解讀

| 穩定性指標          | 良好     | 警告     | 差       |
|---------------------|----------|----------|----------|
| lag 標準差          | < 1.5    | 1.5-3.0  | > 3.0    |
| corr 變動範圍       | < 0.15   | 0.15-0.3 | > 0.3    |
| 方向翻轉次數        | 0        | 1        | > 1      |

</interpretation_guide>

<success_criteria>
此工作流程完成時應有：

- [ ] 領先滯後估計及其穩定性分析
- [ ] 確認率統計（整體、按類型）
- [ ] 失敗走勢分析（失敗率比值）
- [ ] 回測報告（JSON 或 Markdown）
- [ ] 結論：確認邏輯是否有效
- [ ] （可選）回測視覺化圖表
</success_criteria>
