# 輸入參數完整定義

## 核心參數

| 參數              | 類型   | 必要 | 預設值 | 說明                         |
|-------------------|--------|------|--------|------------------------------|
| silver_symbol     | string | ✅   | SI=F   | 白銀標的代碼                 |
| palladium_symbol  | string | ✅   | PA=F   | 鈀金標的代碼                 |
| timeframe         | string | ✅   | 1h     | 分析時間尺度                 |
| lookback_bars     | int    | ✅   | 1000   | 回溯 K 棒數                  |

### silver_symbol / palladium_symbol

支援的標的代碼：

| 來源          | 白銀              | 鈀金              |
|---------------|-------------------|-------------------|
| Yahoo Finance | SI=F, XAGUSD=X    | PA=F              |
| 自定義        | 任何 OHLCV 資料源 | 任何 OHLCV 資料源 |

### timeframe

| 值   | 說明         | 適用場景             |
|------|--------------|----------------------|
| 1h   | 1 小時       | 短期交易確認         |
| 4h   | 4 小時       | 日內波段             |
| 1d   | 日線         | 中期趨勢             |

### lookback_bars

| 值        | 說明                 | 統計有效性           |
|-----------|----------------------|----------------------|
| 500       | 最小建議             | 基本分析             |
| 1000      | 標準                 | 良好                 |
| 2000-3000 | 深度回測             | 優秀                 |

---

## 拐點偵測參數

| 參數        | 類型   | 必要 | 預設值 | 說明                   |
|-------------|--------|------|--------|------------------------|
| turn_method | string | ✅   | pivot  | 拐點偵測方法           |
| pivot_left  | int    | ❌   | 3      | pivot 左側確認 K 數    |
| pivot_right | int    | ❌   | 3      | pivot 右側確認 K 數    |

### turn_method

| 值           | 說明                           | 參數                    |
|--------------|--------------------------------|-------------------------|
| pivot        | 左右 N 根內局部極值            | pivot_left, pivot_right |
| peaks        | scipy find_peaks + prominence  | prominence, distance    |
| slope_change | 趨勢斜率符號變化               | slope_window            |

### pivot 法參數

| 參數        | 範圍  | 建議值           | 效果                   |
|-------------|-------|------------------|------------------------|
| pivot_left  | 2-10  | 3（1h）, 2（1d） | 越大越少拐點           |
| pivot_right | 2-10  | 3（1h）, 2（1d） | 越大確認越晚           |

### peaks 法參數

| 參數       | 類型  | 預設值 | 說明                   |
|------------|-------|--------|------------------------|
| prominence | float | 0.5    | 突出度門檻（標準差倍數）|
| distance   | int   | 5      | 最小間隔 K 數          |

### slope_change 法參數

| 參數          | 類型  | 預設值 | 說明                   |
|---------------|-------|--------|------------------------|
| slope_window  | int   | 10     | 斜率計算窗口           |
| slope_threshold| float| 0.0    | 斜率變化門檻           |

---

## 確認參數

| 參數                | 類型   | 必要 | 預設值 | 說明                      |
|---------------------|--------|------|--------|---------------------------|
| confirm_window_bars | int    | ✅   | 6      | 跨金屬確認窗口 K 數       |
| lead_lag_max_bars   | int    | ❌   | 24     | 領先滯後估計最大滯後 K 數 |

### confirm_window_bars

建議配置：

| timeframe | 建議值  | 說明                   |
|-----------|---------|------------------------|
| 1h        | 6-12    | 約半天到一天           |
| 4h        | 3-6     | 約半天到一天           |
| 1d        | 2-5     | 約一週                 |

### lead_lag_max_bars

建議配置：

| timeframe | 建議值  | 說明                   |
|-----------|---------|------------------------|
| 1h        | 24-72   | 1-3 天                 |
| 4h        | 12-24   | 2-4 天                 |
| 1d        | 5-15    | 1-3 週                 |

---

## 參與度參數

| 參數                   | 類型   | 必要 | 預設值          | 說明                 |
|------------------------|--------|------|-----------------|----------------------|
| participation_metric   | string | ✅   | direction_agree | 參與度衡量方式       |
| participation_threshold| float  | ❌   | 0.6             | 參與度門檻           |

### participation_metric

| 值               | 說明                     | 適用場景             |
|------------------|--------------------------|----------------------|
| returns_corr     | 報酬率滾動相關係數       | 精確量化             |
| direction_agree  | 同向漲跌的比例           | 簡單直觀             |
| vol_expansion    | 兩者波動同步擴張         | 波動確認             |
| breakout_confirm | 銀突破時鈀金也突破       | 突破交易             |

### participation_threshold

| 指標             | 建議範圍 | 說明                   |
|------------------|----------|------------------------|
| returns_corr     | 0.3-0.6  | 相關係數門檻           |
| direction_agree  | 0.5-0.7  | 同向比例門檻           |
| vol_expansion    | 0.7-1.0  | 波動比值門檻           |
| breakout_confirm | N/A      | 二元判定               |

---

## 失敗走勢參數

| 參數         | 類型   | 必要 | 預設值                  | 說明                 |
|--------------|--------|------|-------------------------|----------------------|
| failure_rule | string | ❌   | no_confirm_then_revert  | 失敗走勢判定規則     |
| revert_bars  | int    | ❌   | 10                      | 回撤檢查 K 數        |

### failure_rule

| 值                        | 說明                               |
|---------------------------|------------------------------------|
| no_confirm_then_revert    | 無確認 + 回撤過起點                |
| no_confirm_then_break_fail| 無確認 + 突破後回落跌破突破點      |

---

## 宏觀濾鏡參數（可選）

| 參數          | 類型   | 預設值 | 說明                   |
|---------------|--------|--------|------------------------|
| macro_filters | object | null   | 宏觀濾鏡配置           |

### macro_filters 結構

```json
{
  "use_dxy": true,
  "dxy_threshold": 0.5,
  "use_real_yield": false,
  "real_yield_series": "DFII10",
  "use_vix": true,
  "vix_threshold": 20
}
```

| 濾鏡          | 說明                     | 作用                     |
|---------------|--------------------------|--------------------------|
| use_dxy       | 使用美元指數             | 過濾美元驅動的波動       |
| use_real_yield| 使用實質利率             | 過濾利率變動期           |
| use_vix       | 使用 VIX                 | 過濾風險事件期           |

---

## 輸出參數

| 參數        | 類型   | 預設值 | 說明                   |
|-------------|--------|--------|------------------------|
| output      | string | null   | 輸出文件路徑           |
| format      | string | json   | 輸出格式（json/markdown）|
| include_timeseries | bool | false | 是否包含時間序列資料 |

---

## 命令行參數對照

```bash
python scripts/palladium_lead_silver.py \
  --silver SI=F \                      # silver_symbol
  --palladium PA=F \                   # palladium_symbol
  --timeframe 1h \                     # timeframe
  --lookback 1000 \                    # lookback_bars
  --turn-method pivot \                # turn_method
  --pivot-left 3 \                     # pivot_left
  --pivot-right 3 \                    # pivot_right
  --confirm-window 6 \                 # confirm_window_bars
  --lead-lag-max 24 \                  # lead_lag_max_bars
  --participation direction_agree \    # participation_metric
  --participation-threshold 0.6 \      # participation_threshold
  --failure-rule no_confirm_then_revert \ # failure_rule
  --output result.json                 # output
```

---

## 完整配置範例

```json
{
  "silver_symbol": "SI=F",
  "palladium_symbol": "PA=F",
  "timeframe": "1h",
  "lookback_bars": 1000,
  "turn_method": "pivot",
  "pivot_left": 3,
  "pivot_right": 3,
  "confirm_window_bars": 6,
  "lead_lag_max_bars": 24,
  "participation_metric": "direction_agree",
  "participation_threshold": 0.6,
  "failure_rule": "no_confirm_then_revert",
  "revert_bars": 10,
  "macro_filters": null,
  "output": "result.json",
  "format": "json",
  "include_timeseries": false
}
```
