# 輸入參數定義

本文件定義 `backsolve-miner-vs-metal-ratio-with-fundamentals` 技能的完整輸入參數。

## 核心參數

### metal_symbol

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | string                            |
| 必要性   | Required                          |
| 預設值   | `"SI=F"`                          |
| 說明     | 金屬價格代碼（Yahoo Finance 格式）|

**可用值**

| 金屬   | 代碼      | 說明                   |
|--------|-----------|------------------------|
| 白銀   | SI=F      | COMEX 白銀期貨（推薦） |
| 白銀   | XAGUSD=X  | 白銀現貨               |
| 白銀   | SLV       | iShares 白銀 ETF       |
| 黃金   | GC=F      | COMEX 黃金期貨         |
| 黃金   | XAUUSD=X  | 黃金現貨               |
| 黃金   | GLD       | SPDR 黃金 ETF          |

---

### miner_universe

| 屬性     | 值                                              |
|----------|-------------------------------------------------|
| 類型     | object                                          |
| 必要性   | Required                                        |
| 說明     | 礦業股/ETF 定義                                 |

**結構**

```json
{
  "type": "etf_holdings" | "ticker_list",
  "etf_ticker": "SIL",                    // type=etf_holdings 時必填
  "tickers": ["PAAS", "AG", "HL", ...],   // type=ticker_list 時必填
  "weights": [0.12, 0.08, 0.07, ...]      // 選填，空則等權
}
```

**ETF 選項**

| ETF   | 說明                              | 適用場景           |
|-------|-----------------------------------|--------------------|
| SIL   | Global X Silver Miners ETF        | 白銀礦業（推薦）   |
| SILJ  | ETFMG Prime Junior Silver Miners  | 小型白銀礦業       |
| GDX   | VanEck Gold Miners ETF            | 黃金礦業           |
| GDXJ  | VanEck Junior Gold Miners ETF     | 小型黃金礦業       |

---

### region_profile

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | string                            |
| 必要性   | Required                          |
| 預設值   | `"us_sec"`                        |
| 說明     | 監管與揭露來源配置                |

**可用值**

| 值            | 說明                                             |
|---------------|--------------------------------------------------|
| us_sec        | 美國 SEC EDGAR（10-K/10-Q XBRL）                 |
| canada_sedar  | 加拿大 SEDAR+（年報/MD&A）                       |
| mixed         | 混合模式：依公司上市地自動選擇                   |

---

### time_range

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Required                          |
| 說明     | 分析時間區間                      |

**結構**

```json
{
  "start": "2020-01-01",    // YYYY-MM-DD
  "end": "2026-01-21",      // YYYY-MM-DD 或 "today"
  "frequency": "weekly"     // daily | weekly | monthly
}
```

**頻率建議**

| 頻率    | 適用場景                         |
|---------|----------------------------------|
| daily   | 短期分析、高精度回測             |
| weekly  | 中長期分析（推薦）               |
| monthly | 長期趨勢、降低雜訊               |

---

### ratio_thresholds

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Optional                          |
| 說明     | 統計門檻定義                      |

**結構**

```json
{
  "bottom_quantile": 0.20,   // 底部分位數（預設 20%）
  "top_quantile": 0.80       // 頂部分位數（預設 80%）
}
```

**建議範圍**

| 風格     | bottom | top  | 說明                       |
|----------|--------|------|----------------------------|
| 標準     | 0.20   | 0.80 | 平衡敏感度與可靠性         |
| 保守     | 0.10   | 0.90 | 更極端才觸發訊號           |
| 積極     | 0.25   | 0.75 | 更早觸發訊號               |

---

## 因子方法選擇

### fundamental_methods

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Optional                          |
| 說明     | 各因子的計算方法選擇              |

**結構**

```json
{
  "aisc_method": "hybrid",
  "leverage_method": "net_debt_to_ev",
  "multiple_method": "ev_to_ebitda",
  "dilution_method": "weighted_avg_shares"
}
```

---

#### aisc_method

AISC（全維持成本）的抽取方法。

| 值                           | 說明                                              |
|------------------------------|---------------------------------------------------|
| reported_text_extract        | 從 MD&A 文字抽取揭露的 AISC                       |
| proxy_cash_cost_plus_sustaining | Proxy 回算：(OpCost + SustCapex + G&A - Byproduct) / Oz |
| hybrid                       | 優先抽取，缺失時用 proxy 補齊（推薦）             |

---

#### leverage_method

槓桿因子的計算方法。

| 值                  | 公式                        | 說明                     |
|---------------------|-----------------------------|--------------------------|
| net_debt_to_ev      | NetDebt / EV                | 推薦，直觀反映財務風險   |
| net_debt_to_ebitda  | NetDebt / EBITDA            | 獲利能力視角             |
| interest_coverage   | EBITDA / InterestExpense    | 償債能力視角             |

---

#### multiple_method

倍數因子的計算方法。

| 值           | 公式           | 說明                       |
|--------------|----------------|----------------------------|
| ev_to_ebitda | EV / EBITDA    | 推薦，業界標準估值倍數     |
| p_to_nav_proxy | P / NAV      | 資產淨值視角（需礦區估值） |
| fcf_yield    | FCF / MarketCap| 自由現金流視角             |

---

#### dilution_method

稀釋因子的計算方法。

| 值                  | 說明                                   |
|---------------------|----------------------------------------|
| weighted_avg_shares | 加權平均股數 YoY 變化（推薦）          |
| shares_outstanding  | 流通股數 YoY 變化                      |

---

## 數據源偏好

### data_sources

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Optional                          |
| 說明     | 數據源偏好設定                    |

**結構**

```json
{
  "prices": "yfinance",
  "filings": "sec_edgar",
  "holdings": "etf_provider"
}
```

**選項**

| 類別     | 選項                                             |
|----------|--------------------------------------------------|
| prices   | yfinance（預設）、stooq、alphavantage            |
| filings  | sec_edgar（預設）、sedar_plus、company_reports   |
| holdings | etf_provider（預設）、sec_nport、manual_csv_url  |

---

## 快取設定

### cache

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Optional                          |
| 說明     | 快取與重現性設定                  |

**結構**

```json
{
  "enabled": true,
  "dir": "./cache",
  "max_age_hours": 168   // 7 天
}
```

---

## 輸出選項

### output_options

| 屬性     | 值                                |
|----------|-----------------------------------|
| 類型     | object                            |
| 必要性   | Optional                          |
| 說明     | 輸出內容控制                      |

**結構**

```json
{
  "export_tables": true,
  "export_charts": true,
  "export_intermediate_json": true,
  "output_format": "json"    // json | markdown | both
}
```

---

## 完整輸入範例

```json
{
  "metal_symbol": "SI=F",
  "miner_universe": {
    "type": "etf_holdings",
    "etf_ticker": "SIL"
  },
  "region_profile": "mixed",
  "time_range": {
    "start": "2015-01-01",
    "end": "today",
    "frequency": "weekly"
  },
  "ratio_thresholds": {
    "bottom_quantile": 0.20,
    "top_quantile": 0.80
  },
  "fundamental_methods": {
    "aisc_method": "hybrid",
    "leverage_method": "net_debt_to_ev",
    "multiple_method": "ev_to_ebitda",
    "dilution_method": "weighted_avg_shares"
  },
  "data_sources": {
    "prices": "yfinance",
    "filings": "sec_edgar",
    "holdings": "etf_provider"
  },
  "cache": {
    "enabled": true,
    "dir": "./cache"
  },
  "output_options": {
    "export_tables": true,
    "export_charts": true,
    "output_format": "json"
  }
}
```
