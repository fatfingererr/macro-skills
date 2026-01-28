# 輸入參數定義

<overview>
本文件定義 analyze-gas-fertilizer-contract-shock 技能的完整輸入參數結構。
</overview>

---

## 必要參數

### start_date

| 屬性 | 值             |
|------|----------------|
| 類型 | string         |
| 格式 | YYYY-MM-DD     |
| 必填 | 是             |
| 說明 | 分析起始日期   |
| 範例 | `"2025-08-01"` |

### end_date

| 屬性 | 值             |
|------|----------------|
| 類型 | string         |
| 格式 | YYYY-MM-DD     |
| 必填 | 是             |
| 說明 | 分析結束日期   |
| 範例 | `"2026-02-01"` |

### freq

| 屬性   | 值               |
|--------|------------------|
| 類型   | string           |
| 必填   | 是               |
| 固定值 | `"1D"`           |
| 說明   | 資料頻率（日頻） |

### te_symbols

| 屬性 | 值                        |
|------|---------------------------|
| 類型 | object                    |
| 必填 | 是                        |
| 說明 | TradingEconomics 商品代碼 |

**結構**：

```json
{
  "natural_gas": "natural-gas",
  "fertilizer": "urea"
}
```

**natural_gas 選項**：

| 值                 | 說明                         |
|--------------------|------------------------------|
| `"natural-gas"`    | 美國天然氣（Henry Hub 基準） |
| `"eu-natural-gas"` | 歐洲天然氣（TTF 基準）       |
| `"uk-natural-gas"` | 英國天然氣                   |

**fertilizer 選項**：

| 值              | 說明               |
|-----------------|--------------------|
| `"urea"`        | 尿素（最常見氮肥） |
| `"dap"`         | 磷酸二銨           |
| `"fertilizers"` | 化肥綜合指數       |

---

## 選填參數

### te_ui_time_range

| 屬性 | 值                             |
|------|--------------------------------|
| 類型 | string                         |
| 必填 | 否                             |
| 預設 | `"6M"`                         |
| 說明 | TradingEconomics UI 的區間按鈕 |

**選項**：

| 值      | 說明     |
|---------|----------|
| `"1M"`  | 1 個月   |
| `"3M"`  | 3 個月   |
| `"6M"`  | 6 個月   |
| `"1Y"`  | 1 年     |
| `"5Y"`  | 5 年     |
| `"All"` | 全部歷史 |

---

### cdp

| 屬性 | 值              |
|------|-----------------|
| 類型 | object          |
| 必填 | 否              |
| 說明 | Chrome CDP 配置 |

**結構**：

```json
{
  "port": 9222,
  "timeout_seconds": 30,
  "cache_hours": 12
}
```

**欄位說明**：

| 欄位            | 類型 | 預設   | 說明                   |
|-----------------|------|--------|------------------------|
| port            | int  | `9222` | Chrome 調試端口        |
| timeout_seconds | int  | `30`   | WebSocket 連線超時時間 |
| cache_hours     | int  | `12`   | 快取有效時間（小時）   |

---

### spike_detection

| 屬性 | 值                   |
|------|----------------------|
| 類型 | object               |
| 必填 | 否                   |
| 說明 | Shock/Spike 偵測參數 |

**結構**：

```json
{
  "return_window": 1,
  "z_window": 60,
  "parabolic_threshold": {
    "z": 3.0,
    "slope_pct_per_day": 1.5
  }
}
```

**欄位說明**：

| 欄位                                  | 類型  | 預設  | 說明                       |
|---------------------------------------|-------|-------|----------------------------|
| return_window                         | int   | `1`   | 報酬計算窗口（天）         |
| z_window                              | int   | `60`  | rolling z-score 視窗（天） |
| parabolic_threshold.z                 | float | `3.0` | z-score 閾值               |
| parabolic_threshold.slope_pct_per_day | float | `1.5` | 斜率閾值（%/天）           |

**調參建議**：

| 場景       | z       | slope |
|------------|---------|-------|
| 一般市場   | 3.0     | 1.5   |
| 高波動市場 | 3.5-4.0 | 2.0   |
| 保守偵測   | 2.5     | 1.0   |

---

### lead_lag

| 屬性 | 值               |
|------|------------------|
| 類型 | object           |
| 必填 | 否               |
| 說明 | 領先落後分析參數 |

**結構**：

```json
{
  "max_lag_days": 60,
  "method": "corr_returns"
}
```

**欄位說明**：

| 欄位         | 類型   | 預設             | 說明              |
|--------------|--------|------------------|-------------------|
| max_lag_days | int    | `60`             | 最大領先/落後天數 |
| method       | string | `"corr_returns"` | 相關計算方法      |

**method 選項**：

| 值               | 說明                     |
|------------------|--------------------------|
| `"corr_returns"` | 報酬率的交叉相關（推薦） |
| `"corr_levels"`  | 價格水準的交叉相關       |

---

### hedge_hypothesis

| 屬性 | 值               |
|------|------------------|
| 類型 | object           |
| 必填 | 否               |
| 說明 | 合約對沖假說參數 |

**結構**：

```json
{
  "gas_contract_price": 0.80,
  "gas_contract_unit": "USD/MMBtu",
  "profit_proxy_mode": "spot_minus_contract"
}
```

**欄位說明**：

| 欄位               | 類型   | 預設                    | 說明               |
|--------------------|--------|-------------------------|--------------------|
| gas_contract_price | float  | 無預設                  | 新聞宣稱的合約價格 |
| gas_contract_unit  | string | `"USD/MMBtu"`           | 價格單位           |
| profit_proxy_mode  | string | `"spot_minus_contract"` | 計算模式           |

**注意**：只有在執行 hedge-hypothesis workflow 時才需要此參數。

---

### output

| 屬性 | 值       |
|------|----------|
| 類型 | object   |
| 必填 | 否       |
| 說明 | 輸出配置 |

**結構**：

```json
{
  "format": "json",
  "include_charts": true
}
```

**欄位說明**：

| 欄位           | 類型    | 預設     | 說明                                 |
|----------------|---------|----------|--------------------------------------|
| format         | string  | `"json"` | 輸出格式（`"json"` 或 `"markdown"`） |
| include_charts | boolean | `true`   | 是否輸出圖表檔案路徑                 |

---

## 完整範例

### 最小配置

```json
{
  "start_date": "2025-08-01",
  "end_date": "2026-02-01",
  "freq": "1D",
  "te_symbols": {
    "natural_gas": "natural-gas",
    "fertilizer": "urea"
  }
}
```

### 完整配置

```json
{
  "start_date": "2025-08-01",
  "end_date": "2026-02-01",
  "freq": "1D",
  "te_symbols": {
    "natural_gas": "natural-gas",
    "fertilizer": "urea"
  },
  "te_ui_time_range": "6M",
  "cdp": {
    "port": 9222,
    "timeout_seconds": 30,
    "cache_hours": 12
  },
  "spike_detection": {
    "return_window": 1,
    "z_window": 60,
    "parabolic_threshold": {
      "z": 3.0,
      "slope_pct_per_day": 1.5
    }
  },
  "lead_lag": {
    "max_lag_days": 60,
    "method": "corr_returns"
  },
  "hedge_hypothesis": {
    "gas_contract_price": 0.80,
    "gas_contract_unit": "USD/MMBtu",
    "profit_proxy_mode": "spot_minus_contract"
  },
  "output": {
    "format": "json",
    "include_charts": true
  }
}
```

---

## Chrome CDP 前置要求

使用本技能前，需要：

1. **安裝 Google Chrome**（版本 90+）
2. **建立專用 profile 目錄**：
   ```bash
   # Windows
   mkdir "%USERPROFILE%\.chrome-debug-profile"

   # macOS / Linux
   mkdir -p ~/.chrome-debug-profile
   ```
3. **啟動 Chrome 調試模式**：
   ```bash
   chrome --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="<profile-path>"
   ```

詳細說明請參閱 `references/data-sources.md`。
