# 輸入參數定義

## 必要參數

| 參數     | 類型   | 說明                               |
|----------|--------|------------------------------------|
| `symbol` | string | 資產代碼（例：SI=F, GC=F, XAGUSD） |

## 時間範圍參數

| 參數         | 類型                | 預設值          | 說明                                        |
|--------------|---------------------|-----------------|---------------------------------------------|
| `start_date` | string (YYYY-MM-DD) | today - 5 years | 取樣開始日。建議至少涵蓋 3 年以建立有效基準 |
| `end_date`   | string (YYYY-MM-DD) | today           | 取樣結束日                                  |
| `timeframe`  | string              | "1d"            | 價格頻率。支援：1d（日線）、1h（小時線）    |

## ATR 計算參數

| 參數              | 類型   | 預設值 | 說明                                                               |
|-------------------|--------|--------|--------------------------------------------------------------------|
| `atr_period`      | int    | 14     | ATR 計算週期。建議範圍：10-20                                      |
| `atr_smoothing`   | string | "ema"  | ATR 平滑方法。支援："ema"（指數移動平均）、"wilder"（Wilder 平滑） |
| `use_percent_atr` | bool   | true   | 是否將 ATR 轉為百分比（ATR / Close * 100）                         |

## 行情判定參數

| 參數                     | 類型  | 預設值 | 說明                                                   |
|--------------------------|-------|--------|--------------------------------------------------------|
| `baseline_window_days`   | int   | 756    | 長期常態基準窗口。756 ≈ 3 年交易日                     |
| `spike_threshold_x`      | float | 2.0    | ATR% 對基準的倍率門檻。超過此值視為擠壓風險            |
| `high_vol_threshold_pct` | float | 6.0    | 絕對 ATR% 高波動門檻。需與倍率門檻同時滿足才判定為擠壓 |

## 輔助指標參數

| 參數                           | 類型 | 預設值 | 說明                                                  |
|--------------------------------|------|--------|-------------------------------------------------------|
| `rsi_period`                   | int  | 14     | RSI 週期。用於輔助判讀是否過熱                        |
| `include_microstructure_notes` | bool | true   | 是否輸出「被迫流/保證金/期權避險/回補」的行情解釋模板 |

## 輸出控制參數

| 參數                 | 類型   | 預設值 | 說明                                   |
|----------------------|--------|--------|----------------------------------------|
| `output`             | string | null   | 輸出檔案路徑。若不指定則輸出到標準輸出 |
| `format`             | string | "json" | 輸出格式。支援："json"、"markdown"     |
| `include_timeseries` | bool   | false  | 是否在輸出中包含完整時間序列           |

## 批次模式參數

| 參數       | 類型   | 預設值 | 說明                                                 |
|------------|--------|--------|------------------------------------------------------|
| `scan`     | string | null   | 批次掃描的資產清單（逗號分隔）。例："SI=F,GC=F,CL=F" |
| `monitor`  | bool   | false  | 是否進入持續監控模式                                 |
| `interval` | int    | 3600   | 監控間隔（秒）。預設 1 小時                          |
| `webhook`  | string | null   | 狀態變化時發送通知的 webhook URL                     |

## 回測模式參數

| 參數          | 類型   | 預設值      | 說明               |
|---------------|--------|-------------|--------------------|
| `backtest`    | bool   | false       | 是否執行回測模式   |
| `plot`        | bool   | false       | 是否生成視覺化圖表 |
| `plot_output` | string | "chart.png" | 圖表輸出路徑       |

## 參數驗證規則

### symbol
- 必須是有效的資產代碼
- Yahoo Finance 期貨格式：XXX=F（如 SI=F）
- 外匯格式：XXXYYY（如 XAGUSD）

### start_date / end_date
- 格式：YYYY-MM-DD
- start_date 必須早於 end_date
- 建議 start_date 至少比所需分析期早 3 年

### atr_period
- 必須 > 0
- 建議範圍：10-20
- 小於 10 可能過於敏感
- 大於 20 可能反應遲鈍

### baseline_window_days
- 必須 > atr_period
- 建議至少 252（1 年）
- 最佳值：756（3 年）

### spike_threshold_x
- 必須 > 1.0
- 建議範圍：1.5-3.0
- 較低值更敏感，較高值更保守

### high_vol_threshold_pct
- 必須 > 0
- 需根據資產類型調整
- 貴金屬建議：5-8%
- 股指建議：3-5%
- 外匯建議：2-4%

## 命令行範例

### 快速檢查

```bash
python atr_squeeze.py --symbol SI=F --quick
```

### 完整分析

```bash
python atr_squeeze.py \
  --symbol SI=F \
  --start 2020-01-01 \
  --end 2026-01-01 \
  --atr-period 14 \
  --atr-smoothing ema \
  --baseline-window 756 \
  --spike-threshold 2.0 \
  --high-vol-threshold 6.0 \
  --output result.json
```

### 批次掃描

```bash
python atr_squeeze.py \
  --scan SI=F,GC=F,CL=F,NG=F \
  --format markdown
```

### 回測模式

```bash
python atr_squeeze.py \
  --symbol SI=F \
  --start 2015-01-01 \
  --backtest \
  --plot \
  --output backtest.json \
  --plot-output chart.png
```

## 程式化呼叫

```python
from atr_squeeze import detect_atr_squeeze_regime

result = detect_atr_squeeze_regime(
    symbol="SI=F",
    start_date="2020-01-01",
    end_date="2026-01-01",
    atr_period=14,
    atr_smoothing="ema",
    use_percent_atr=True,
    baseline_window_days=756,
    spike_threshold_x=2.0,
    high_vol_threshold_pct=6.0,
    rsi_period=14,
    include_microstructure_notes=True
)

print(result["regime"])
print(result["atr_pct"])
print(result["atr_ratio_to_baseline"])
```
