# 輸入參數定義 (Input Schema)

本文檔定義 `analyze-move-risk-gauges-leadlag` 技能的完整輸入參數。

---

## 核心參數（必填）

| 參數         | 類型   | 說明                      | 範例           |
|--------------|--------|---------------------------|----------------|
| `start_date` | string | 分析起始日期 (YYYY-MM-DD) | `"2024-01-01"` |
| `end_date`   | string | 分析結束日期 (YYYY-MM-DD) | `"2026-01-01"` |

---

## 指標參數（選填）

### 利率波動率指標

| 參數               | 類型   | 預設值   | 說明               |
|--------------------|--------|----------|--------------------|
| `rates_vol_symbol` | string | `"MOVE"` | 利率波動率指標代碼 |

**可用值**：
- `"MOVE"`: ICE BofA MOVE Index（需爬蟲或代理）
- `"RATES_VOL_PROXY"`: 使用 DGS10 計算的實現波動率代理

### 股市波動率指標

| 參數                | 類型   | 預設值  | 說明               |
|---------------------|--------|---------|--------------------|
| `equity_vol_symbol` | string | `"VIX"` | 股市波動率指標代碼 |

**可用值**：
- `"VIX"`: CBOE VIX Index（Yahoo: ^VIX）
- `"VIXCLS"`: FRED VIX 系列

### 信用利差/風險指標

| 參數                   | 類型   | 預設值           | 說明                  |
|------------------------|--------|------------------|-----------------------|
| `credit_spread_symbol` | string | `"CDX_IG_PROXY"` | 信用利差/風險指標代碼 |

**可用值**：
- `"CDX_IG_PROXY"`: 使用 FRED IG OAS 作為 CDX IG 代理
- `"BAMLC0A0CM"`: ICE BofA US Corporate Index OAS
- `"BAMLC0A4CBBB"`: ICE BofA BBB US Corporate Index OAS
- `"BAMLH0A0HYM2"`: ICE BofA US High Yield Index OAS

### 日本國債殖利率

| 參數               | 類型   | 預設值     | 說明                |
|--------------------|--------|------------|---------------------|
| `jgb_yield_symbol` | string | `"JGB10Y"` | 日本 10Y 殖利率代碼 |

**可用值**：
- `"JGB10Y"`: 日本 10 年期國債殖利率（需爬蟲）
- `"INTGSTJPM193N"`: FRED 月頻 JGB 數據（不建議用於日頻分析）

---

## 分析參數（選填）

### 頻率

| 參數   | 類型   | 預設值 | 說明     |
|--------|--------|--------|----------|
| `freq` | string | `"D"`  | 資料頻率 |

**可用值**：
- `"D"`: 日頻（建議）
- `"W"`: 週頻（每週五或最後交易日）

### 平滑處理

| 參數            | 類型 | 預設值 | 範圍 | 說明                             |
|-----------------|------|--------|------|----------------------------------|
| `smooth_window` | int  | `5`    | 0-20 | 平滑用移動平均窗（0 表示不平滑） |

**建議**：
- `5`: 一週平滑，適合中期分析
- `10`: 兩週平滑，更平滑但可能損失訊號
- `0`: 不平滑，保留所有噪音

### Z 分數標準化

| 參數            | 類型 | 預設值 | 範圍   | 說明                   |
|-----------------|------|--------|--------|------------------------|
| `zscore_window` | int  | `60`   | 20-252 | 標準化回看窗（交易日） |

**建議**：
- `60`: 約 3 個月，適合中期視角
- `252`: 1 年，更穩定但反應較慢
- `20`: 1 個月，對近期變化更敏感

### 領先落後分析

| 參數                | 類型 | 預設值 | 範圍 | 說明                 |
|---------------------|------|--------|------|----------------------|
| `lead_lag_max_days` | int  | `20`   | 5-60 | 交叉相關最大位移天數 |

**建議**：
- `20`: 約 1 個月，適合大多數分析
- `10`: 短期視角
- `40`: 長期視角（但樣本量減少）

### 事件窗檢定

| 參數                  | 類型  | 預設值 | 範圍 | 說明               |
|-----------------------|-------|--------|------|--------------------|
| `shock_window_days`   | int   | `5`    | 1-20 | 事件窗天數         |
| `shock_threshold_bps` | float | `15`   | 5-50 | JGB 衝擊門檻 (bps) |

**建議**：
- `shock_window_days = 5`: 一週窗口，捕捉短期衝擊
- `shock_threshold_bps = 15`: 15 bps 變動代表顯著的殖利率波動

**歷史參考**（JGB 10Y 單日變動）：
- 正常：1-5 bps
- 偏大：5-15 bps
- 顯著：15-30 bps
- 極端：> 30 bps（如 2022 年 BOJ 政策轉向）

### 輸出格式

| 參數          | 類型   | 預設值       | 說明     |
|---------------|--------|--------------|----------|
| `output_mode` | string | `"markdown"` | 輸出格式 |

**可用值**：
- `"markdown"`: Markdown 格式，適合人類閱讀
- `"json"`: JSON 格式，適合程式處理

---

## 參數組合範例

### 快速檢查

```json
{
  "start_date": "2025-01-01",
  "end_date": "2026-01-23",
  "smooth_window": 5,
  "output_mode": "markdown"
}
```

### 詳細分析

```json
{
  "start_date": "2024-01-01",
  "end_date": "2026-01-23",
  "rates_vol_symbol": "MOVE",
  "equity_vol_symbol": "VIX",
  "credit_spread_symbol": "CDX_IG_PROXY",
  "jgb_yield_symbol": "JGB10Y",
  "freq": "D",
  "smooth_window": 5,
  "zscore_window": 60,
  "lead_lag_max_days": 20,
  "shock_window_days": 5,
  "shock_threshold_bps": 15,
  "output_mode": "json"
}
```

### 長期視角

```json
{
  "start_date": "2020-01-01",
  "end_date": "2026-01-23",
  "zscore_window": 252,
  "lead_lag_max_days": 40,
  "shock_threshold_bps": 20,
  "output_mode": "markdown"
}
```

### 使用代理數據

```json
{
  "start_date": "2024-01-01",
  "end_date": "2026-01-23",
  "rates_vol_symbol": "RATES_VOL_PROXY",
  "credit_spread_symbol": "BAMLC0A4CBBB",
  "output_mode": "json"
}
```

---

## 參數驗證規則

### 日期驗證

```python
from datetime import datetime

def validate_dates(start_date: str, end_date: str) -> bool:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # 結束日期必須晚於起始日期
    if end <= start:
        raise ValueError("end_date must be after start_date")

    # 分析區間至少 60 天（zscore_window 最小需求）
    if (end - start).days < 60:
        raise ValueError("Analysis period must be at least 60 days")

    return True
```

### 窗口參數驗證

```python
def validate_windows(params: dict) -> bool:
    smooth = params.get("smooth_window", 5)
    zscore = params.get("zscore_window", 60)
    leadlag = params.get("lead_lag_max_days", 20)
    shock = params.get("shock_window_days", 5)

    # 平滑窗口不能超過 Z 分數窗口的 1/3
    if smooth > zscore / 3:
        raise ValueError("smooth_window should be less than zscore_window / 3")

    # 領先落後窗口不能超過數據長度的 1/4
    # （需在運行時根據實際數據長度檢查）

    return True
```

---

## 預設配置

```python
DEFAULT_CONFIG = {
    "rates_vol_symbol": "MOVE",
    "equity_vol_symbol": "VIX",
    "credit_spread_symbol": "CDX_IG_PROXY",
    "jgb_yield_symbol": "JGB10Y",
    "freq": "D",
    "smooth_window": 5,
    "zscore_window": 60,
    "lead_lag_max_days": 20,
    "shock_window_days": 5,
    "shock_threshold_bps": 15.0,
    "output_mode": "markdown"
}
```
