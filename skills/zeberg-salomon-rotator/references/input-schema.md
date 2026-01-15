# 輸入參數定義 (Input Schema)

## 完整參數列表

### 時間與頻率

<parameter name="start_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 回測起始日期
**Example**: `"2000-01-01"`
</parameter>

<parameter name="end_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Default**: today
**Description**: 回測結束日期
**Example**: `"2026-01-15"`
</parameter>

<parameter name="freq" required="false">
**Type**: string
**Default**: `"M"`
**Options**: `M` (月) | `W` (週)
**Description**: 數據頻率。建議使用月頻（M）以對齊宏觀數據發布週期。
</parameter>

### 標的資產（兩態資產）

<parameter name="equity_proxy" required="false">
**Type**: string
**Default**: `"SPY"`
**Options**: `SPY`, `^GSPC`, `VOO`
**Description**: Risk-On 狀態持有的風險資產代理。
</parameter>

<parameter name="bond_proxy" required="false">
**Type**: string
**Default**: `"TLT"`
**Options**: `TLT`, `VGLT`, `IEF`
**Description**: Risk-Off 狀態持有的長天期公債代理。
</parameter>

<parameter name="use_total_return" required="false">
**Type**: boolean
**Default**: `false`
**Description**: 若為 true，優先使用總報酬數據（含配息再投資）。
</parameter>

### 領先指標配置

<parameter name="leading_series" required="true">
**Type**: array[object]
**Description**: 領先指標序列配置清單。

**Object 結構**:
```json
{
  "id": "string",        // FRED series ID 或數據鍵
  "transform": "string", // level|yoy|mom|diff|logdiff
  "direction": 1,        // +1: 上升=景氣好, -1: 上升=景氣壞
  "weight": 0.25         // 權重 (所有權重總和建議為 1.0)
}
```

**預設配置**:
```json
[
  {"id": "T10Y3M", "transform": "level", "direction": 1, "weight": 0.25},
  {"id": "T10Y2Y", "transform": "level", "direction": 1, "weight": 0.15},
  {"id": "PERMIT", "transform": "yoy", "direction": 1, "weight": 0.20},
  {"id": "ACDGNO", "transform": "yoy", "direction": 1, "weight": 0.20},
  {"id": "UMCSENT", "transform": "level", "direction": 1, "weight": 0.20}
]
```
</parameter>

### 同時指標配置

<parameter name="coincident_series" required="true">
**Type**: array[object]
**Description**: 同時指標序列配置清單。格式同 leading_series。

**預設配置**:
```json
[
  {"id": "PAYEMS", "transform": "yoy", "direction": 1, "weight": 0.30},
  {"id": "INDPRO", "transform": "yoy", "direction": 1, "weight": 0.30},
  {"id": "W875RX1", "transform": "yoy", "direction": 1, "weight": 0.20},
  {"id": "CMRMTSPL", "transform": "yoy", "direction": 1, "weight": 0.20}
]
```
</parameter>

### 標準化與平滑

<parameter name="standardize_window" required="false">
**Type**: integer
**Default**: `120`
**Description**: Z-score 滾動視窗期數。以 freq 為單位，月頻 120 = 10 年。
**Range**: 60-240
</parameter>

<parameter name="smooth_window" required="false">
**Type**: integer
**Default**: `3`
**Description**: EMA 平滑視窗期數。
**Range**: 1-12
</parameter>

### 門檻與切換邏輯

<parameter name="baseline_method" required="false">
**Type**: string
**Default**: `"z0"`
**Options**: `z0` | `percentile` | `rolling_mean`
**Description**: 基準線計算方法。
- `z0`: 基準線 = 0（最可重現）
- `percentile`: 基準線 = 歷史分位數
- `rolling_mean`: 基準線 = 滾動均值
</parameter>

<parameter name="iceberg_threshold" required="true">
**Type**: number
**Default**: `-0.3`
**Description**: 領先指標跌破此門檻觸發「冰山事件」。若 baseline_method=z0，建議設定為 -0.3 至 0。
**Range**: -1.0 至 0.5
</parameter>

<parameter name="sinking_threshold" required="true">
**Type**: number
**Default**: `-0.5`
**Description**: 同時指標跌破此門檻觸發「下沉事件」。
**Range**: -1.5 至 0
</parameter>

<parameter name="confirm_periods" required="false">
**Type**: integer
**Default**: `2`
**Description**: 連續確認期數，避免假訊號。
**Range**: 1-6
</parameter>

<parameter name="hysteresis" required="false">
**Type**: number
**Default**: `0.15`
**Description**: 進出場門檻間距，避免來回抖動。
**Range**: 0.05-0.5
</parameter>

### 濾鏡配置（可選）

<parameter name="euphoria_filters" required="false">
**Type**: array[object]
**Default**: `[]`
**Description**: 亢奮濾鏡配置。當市場亢奮時，更容易觸發 Risk-Off。

**支援類型**:
```json
[
  {
    "type": "credit_spread_reversal",
    "series_id": "BAA10Y",
    "z_below": -1.0,
    "turn_up": true
  },
  {
    "type": "vix_turn_up",
    "ticker": "VIXCLS",
    "level_below": 15,
    "turn_up": true
  }
]
```
</parameter>

<parameter name="recovery_doubt_filters" required="false">
**Type**: array[object]
**Default**: `[]`
**Description**: 復甦懷疑濾鏡配置。當市場懷疑復甦時，更容易觸發 Risk-On。

**支援類型**:
```json
[
  {
    "type": "leading_momentum",
    "above": 0
  }
]
```
</parameter>

### 回測假設

<parameter name="rebalance_on" required="false">
**Type**: string
**Default**: `"next_month_open"`
**Options**: `signal_close` | `next_open` | `next_month_open`
**Description**: 切換執行時點。建議使用 `next_month_open` 以最保守方式回測。
</parameter>

<parameter name="transaction_cost_bps" required="false">
**Type**: number
**Default**: `5`
**Description**: 單邊交易成本（basis points）。
**Range**: 0-50
</parameter>

<parameter name="slippage_bps" required="false">
**Type**: number
**Default**: `0`
**Description**: 單邊滑價（basis points）。
**Range**: 0-50
</parameter>

### 輸出配置

<parameter name="output_format" required="false">
**Type**: string
**Default**: `"json"`
**Options**: `json` | `markdown`
**Description**: 輸出格式。
</parameter>

<parameter name="include_diagnostics" required="false">
**Type**: boolean
**Default**: `true`
**Description**: 是否輸出診斷資訊（各指標貢獻、觸發原因等）。
</parameter>

## 配置範例

### 基本配置

```json
{
  "start_date": "2000-01-01",
  "end_date": "2026-01-15",
  "iceberg_threshold": -0.3,
  "sinking_threshold": -0.5
}
```

### 完整配置

```json
{
  "start_date": "1990-01-01",
  "end_date": "2026-01-15",
  "freq": "M",
  "equity_proxy": "SPY",
  "bond_proxy": "TLT",
  "use_total_return": true,

  "leading_series": [
    {"id": "T10Y3M", "transform": "level", "direction": 1, "weight": 0.25},
    {"id": "T10Y2Y", "transform": "level", "direction": 1, "weight": 0.15},
    {"id": "PERMIT", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "ACDGNO", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "UMCSENT", "transform": "level", "direction": 1, "weight": 0.20}
  ],

  "coincident_series": [
    {"id": "PAYEMS", "transform": "yoy", "direction": 1, "weight": 0.30},
    {"id": "INDPRO", "transform": "yoy", "direction": 1, "weight": 0.30},
    {"id": "W875RX1", "transform": "yoy", "direction": 1, "weight": 0.20},
    {"id": "CMRMTSPL", "transform": "yoy", "direction": 1, "weight": 0.20}
  ],

  "standardize_window": 120,
  "smooth_window": 3,
  "baseline_method": "z0",
  "iceberg_threshold": -0.3,
  "sinking_threshold": -0.5,
  "confirm_periods": 2,
  "hysteresis": 0.15,

  "euphoria_filters": [
    {"type": "credit_spread_reversal", "series_id": "BAA10Y", "z_below": -1.0, "turn_up": true}
  ],

  "rebalance_on": "next_month_open",
  "transaction_cost_bps": 5,
  "slippage_bps": 0,

  "output_format": "json",
  "include_diagnostics": true
}
```

## CLI 參數對應

```bash
python scripts/rotator.py \
  --start 2000-01-01 \
  --end 2026-01-15 \
  --equity SPY \
  --bond TLT \
  --iceberg-threshold -0.3 \
  --sinking-threshold -0.5 \
  --confirm-periods 2 \
  --hysteresis 0.15 \
  --rebalance next_month_open \
  --cost-bps 5 \
  --output result.json
```
