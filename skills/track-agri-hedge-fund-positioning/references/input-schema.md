# 輸入參數定義

## 1. 必要參數

### date_start
| 屬性     | 值                |
|----------|-------------------|
| 類型     | string            |
| 格式     | YYYY-MM-DD        |
| 必要     | 是                |
| 說明     | 分析起始日期      |
| 範例     | "2025-01-01"      |

### date_end
| 屬性     | 值                |
|----------|-------------------|
| 類型     | string            |
| 格式     | YYYY-MM-DD        |
| 必要     | 是                |
| 說明     | 分析結束日期      |
| 範例     | "2026-01-21"      |

### cot_report
| 屬性     | 值                                      |
|----------|-----------------------------------------|
| 類型     | string                                  |
| 必要     | 是                                      |
| 可用值   | "legacy", "disaggregated", "tff"        |
| 預設     | "legacy"                                |
| 說明     | COT 報表類型                            |

**各類型說明**：
- `legacy`: 傳統分類（Commercial/Non-Commercial），歷史最長
- `disaggregated`: 細分類（Producer/Swap/Managed Money），2009 年後
- `tff`: 金融期貨專用，不適用農產品

### trader_group
| 屬性     | 值                                      |
|----------|-----------------------------------------|
| 類型     | string                                  |
| 必要     | 是                                      |
| 可用值   | 依 cot_report 類型而定                  |
| 預設     | "noncommercial"                         |
| 說明     | 追蹤的交易者分類                        |

**Legacy 報表可用值**：
- `noncommercial`: 非商業（投機/基金）
- `commercial`: 商業（避險）
- `nonreportable`: 非報告（小戶）

**Disaggregated 報表可用值**：
- `managed_money`: 管理資金（對沖基金、CTA）
- `producer_merchant`: 生產商/貿易商
- `swap_dealer`: 交換交易商
- `other_reportable`: 其他報告者

### contracts_map
| 屬性     | 值                                      |
|----------|-----------------------------------------|
| 類型     | object                                  |
| 必要     | 是                                      |
| 說明     | 期貨合約 → 商品群組對照表               |

**範例**：
```json
{
  "CORN": "grains",
  "WHEAT-SRW": "grains",
  "WHEAT-HRW": "grains",
  "SOYBEANS": "oilseeds",
  "SOYBEAN OIL": "oilseeds",
  "SOYBEAN MEAL": "oilseeds",
  "LIVE CATTLE": "meats",
  "LEAN HOGS": "meats",
  "COFFEE C": "softs",
  "SUGAR NO. 11": "softs",
  "COTTON NO. 2": "softs"
}
```

詳細對照表見 `references/contracts-map.md`。

---

## 2. 選用參數

### position_metric
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | string                |
| 必要     | 否                    |
| 可用值   | "net", "long", "short"|
| 預設     | "net"                 |
| 說明     | 部位衡量方式          |

**計算邏輯**：
- `net`: Long - Short（淨部位）
- `long`: 只看多單部位
- `short`: 只看空單部位

### lookback_weeks_firepower
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | integer               |
| 必要     | 否                    |
| 預設     | 156                   |
| 範圍     | 26 - 520              |
| 說明     | 計算火力的歷史視窗週數|

**常用值**：
- 52: 1 年（短期循環）
- 104: 2 年（中期循環）
- 156: 3 年（完整景氣循環，推薦）
- 260: 5 年（跨多個循環）

### macro_indicators
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | object                |
| 必要     | 否                    |
| 說明     | 宏觀指標設定          |

**預設值**：
```json
{
  "usd": {
    "source": "yahoo",
    "symbol": "UUP",
    "description": "美元 ETF"
  },
  "crude": {
    "source": "yahoo",
    "symbol": "CL=F",
    "description": "WTI 原油期貨"
  },
  "metals": {
    "source": "yahoo",
    "symbol": "XME",
    "description": "金屬礦業 ETF"
  },
  "bcom_proxy": {
    "source": "yahoo",
    "symbol": "DBC",
    "description": "商品指數 ETF"
  }
}
```

### fundamental_inputs
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | object                |
| 必要     | 否                    |
| 說明     | 基本面資料設定        |

**預設值**：
```json
{
  "us_export_sales": true,
  "wasde_surprise": true,
  "crop_progress": false
}
```

### event_window_days
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | integer               |
| 必要     | 否                    |
| 預設     | 3                     |
| 範圍     | 1 - 5                 |
| 說明     | Wed-Fri 事件視窗天數  |

用於驗證 COT 週二截止後的週中回補。

### output_mode
| 屬性     | 值                          |
|----------|-----------------------------|
| 類型     | string                      |
| 必要     | 否                          |
| 可用值   | "markdown", "json", "both"  |
| 預設     | "both"                      |
| 說明     | 輸出格式                    |

---

## 3. 進階參數

### firepower_method
| 屬性     | 值                              |
|----------|--------------------------------|
| 類型     | string                          |
| 必要     | 否                              |
| 可用值   | "percentile", "distance", "oi_normalized" |
| 預設     | "percentile"                    |
| 說明     | 火力計算方法                    |

- `percentile`: 1 - 分位數
- `distance`: (P90 - current) / P90
- `oi_normalized`: 用 OI 標準化後的分位數

### tailwind_lookback_days
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | integer               |
| 必要     | 否                    |
| 預設     | 5                     |
| 範圍     | 1 - 20                |
| 說明     | 宏觀順風計算的回看天數|

### confidence_method
| 屬性     | 值                    |
|----------|-----------------------|
| 類型     | string                |
| 必要     | 否                    |
| 可用值   | "simple", "weighted"  |
| 預設     | "simple"              |
| 說明     | 信心水準計算方法      |

---

## 4. 完整輸入範例

```json
{
  "date_start": "2025-01-01",
  "date_end": "2026-01-21",
  "cot_report": "legacy",
  "trader_group": "noncommercial",
  "contracts_map": {
    "CORN": "grains",
    "WHEAT-SRW": "grains",
    "SOYBEANS": "oilseeds",
    "SOYBEAN OIL": "oilseeds",
    "LIVE CATTLE": "meats",
    "COFFEE C": "softs",
    "SUGAR NO. 11": "softs"
  },
  "position_metric": "net",
  "lookback_weeks_firepower": 156,
  "macro_indicators": {
    "usd": {"source": "yahoo", "symbol": "UUP"},
    "crude": {"source": "yahoo", "symbol": "CL=F"},
    "metals": {"source": "yahoo", "symbol": "XME"}
  },
  "fundamental_inputs": {
    "us_export_sales": true,
    "wasde_surprise": true
  },
  "event_window_days": 3,
  "output_mode": "both"
}
```
