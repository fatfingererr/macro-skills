# 輸入參數定義

本文件定義 evaluate-exponential-trend-deviation-regimes 技能的所有輸入參數。

## 必要參數

### symbol (string)

資產標的代碼。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 是 |
| 預設值 | 無（必須提供） |

**範例值**：
- `GC=F` - COMEX 黃金期貨（Yahoo Finance）
- `SI=F` - COMEX 白銀期貨
- `CL=F` - NYMEX 原油期貨
- `^GSPC` - S&P 500 指數
- `BTC-USD` - 比特幣
- `GLD` - SPDR Gold Shares ETF

### start_date (string)

計算用歷史起點，格式為 YYYY-MM-DD。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 建議提供 |
| 預設值 | "2000-01-01"（保守預設） |
| 格式 | YYYY-MM-DD |

**建議**：根據資產特性提供適當的起始日期，以捕捉完整的歷史週期。
- 黃金：1970-01-01（布雷頓森林體系瓦解後）
- S&P 500：1950-01-01
- 比特幣：2013-01-01
- 原油：1980-01-01

## 選用參數

### end_date (string)

結束日期，格式為 YYYY-MM-DD。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 否 |
| 預設值 | today |
| 格式 | YYYY-MM-DD |

### trend_fit_window (string)

趨勢線擬合區間策略。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 否 |
| 預設值 | "full" |

**可接受的值**：
- `full` - 全樣本擬合（推薦）
- `rolling` - 滾動窗口擬合（用於觀察趨勢斜率變化）

### trend_model (string)

趨勢模型類型。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 否 |
| 預設值 | "exponential_log_linear" |

**可接受的值**：
- `exponential_log_linear` - 對數價格線性回歸（推薦）

### compare_peak_dates (list[string])

需要比較的歷史峰值日期（選用）。

| 屬性 | 值 |
|------|-----|
| 類型 | list[string] |
| 必要 | 否 |
| 預設值 | null（自動偵測歷史極值） |
| 格式 | YYYY-MM-DD |

**說明**：
- 若不提供，系統會自動識別歷史最大/最小偏離度
- 若提供，將與指定日期的偏離度進行比較

**範例**（黃金）：
- `2011-09-06` - 後金融危機黃金峰值
- `1980-01-21` - 1970s 高通膨黃金峰值

**範例**（股市）：
- `2000-03-24` - 科技泡沫峰值
- `2007-10-09` - 金融危機前峰值
- `2020-02-19` - 疫情前峰值

### macro_proxies (object)

宏觀代理指標設定。

| 屬性 | 值 |
|------|-----|
| 類型 | object |
| 必要 | 否 |

**子欄位**：

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| real_rate_series | string | "DFII10" | 實質利率序列（FRED） |
| inflation_series | string | "T5YIE" | 通膨預期序列（FRED） |
| usd_series | string | "DTWEXBGS" | 美元指數序列（FRED） |
| geopolitical_risk_series | string | null | 地緣風險序列 |

### regime_rules (object)

1970s-like vs 2000s-like 的判定閾值。

| 屬性 | 值 |
|------|-----|
| 類型 | object |
| 必要 | 否 |

**子欄位**：

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| real_rate_weight | float | 0.30 | 實質利率因子權重 |
| inflation_weight | float | 0.25 | 通膨因子權重 |
| geopolitical_weight | float | 0.25 | 地緣風險因子權重 |
| usd_weight | float | 0.20 | 美元因子權重 |
| threshold_1970s | float | 0.50 | 判定為 1970s-like 的分數門檻 |

### output_format (string)

輸出格式。

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 否 |
| 預設值 | "json" |

**可接受的值**：
- `json` - JSON 格式輸出
- `markdown` - Markdown 格式報告

## 參數驗證規則

### 日期驗證

```python
def validate_date(date_str: str) -> bool:
    """驗證日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_date_range(start: str, end: str) -> bool:
    """驗證日期範圍"""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    return start_dt < end_dt
```

### Symbol 驗證

```python
def validate_symbol(symbol: str) -> bool:
    """
    驗證資產代碼

    接受所有 Yahoo Finance 支援的代碼格式
    """
    # 期貨合約 (以 =F 結尾)
    if symbol.endswith("=F"):
        return True
    # 指數 (以 ^ 開頭)
    if symbol.startswith("^"):
        return True
    # 加密貨幣 (包含 -USD, -EUR 等)
    if "-" in symbol and symbol.split("-")[1] in ["USD", "EUR", "BTC"]:
        return True
    # 一般股票/ETF (大寫字母和數字)
    if symbol.isalnum() and symbol.isupper():
        return True
    return False
```

### 權重驗證

```python
def validate_weights(weights: dict) -> bool:
    """驗證權重總和為 1"""
    total = sum([
        weights.get("real_rate_weight", 0.3),
        weights.get("inflation_weight", 0.25),
        weights.get("geopolitical_weight", 0.25),
        weights.get("usd_weight", 0.2),
    ])
    return abs(total - 1.0) < 0.01
```

## 範例輸入

### 基本使用（黃金）

```json
{
  "symbol": "GC=F",
  "start_date": "1970-01-01"
}
```

### 基本使用（S&P 500）

```json
{
  "symbol": "^GSPC",
  "start_date": "1950-01-01"
}
```

### 完整參數（黃金含宏觀分析）

```json
{
  "symbol": "GC=F",
  "start_date": "1970-01-01",
  "end_date": "2026-01-15",
  "trend_fit_window": "full",
  "trend_model": "exponential_log_linear",
  "compare_peak_dates": ["2011-09-06", "1980-01-21"],
  "macro_proxies": {
    "real_rate_series": "DFII10",
    "inflation_series": "T5YIE",
    "usd_series": "DTWEXBGS",
    "geopolitical_risk_series": null
  },
  "regime_rules": {
    "real_rate_weight": 0.30,
    "inflation_weight": 0.25,
    "geopolitical_weight": 0.25,
    "usd_weight": 0.20,
    "threshold_1970s": 0.50
  },
  "output_format": "json"
}
```

### 完整參數（比特幣）

```json
{
  "symbol": "BTC-USD",
  "start_date": "2013-01-01",
  "end_date": "2026-01-15",
  "trend_fit_window": "full",
  "trend_model": "exponential_log_linear",
  "compare_peak_dates": ["2021-11-10", "2017-12-17"],
  "output_format": "json"
}
```
