# 輸入參數詳細定義

## 必要參數

### start_date

| 項目 | 內容         |
|------|--------------|
| 類型 | string       |
| 格式 | YYYY-MM      |
| 必要 | 是           |
| 說明 | 分析起始年月 |
| 範例 | `"2020-01"`  |

**驗證規則**：
- 必須是有效的年月格式
- 不能晚於 `end_date`
- 不能早於 JSDA 數據起點（約 2010 年）

### end_date

| 項目 | 內容         |
|------|--------------|
| 類型 | string       |
| 格式 | YYYY-MM      |
| 必要 | 是           |
| 說明 | 分析結束年月 |
| 範例 | `"2025-12"`  |

**驗證規則**：
- 必須是有效的年月格式
- 不能早於 `start_date`
- 不能晚於最新可用數據月份

### investor_group

| 項目 | 內容                    |
|------|-------------------------|
| 類型 | string                  |
| 必要 | 是                      |
| 預設 | `"insurance_companies"` |
| 說明 | 投資人分類（JSDA 定義） |

**可用選項**：

| 值                    | 說明         | JSDA 對應          |
|-----------------------|--------------|--------------------|
| `insurance_companies` | 全體保險公司 | 壽險 + 產險        |
| `life_insurance`      | 壽險公司     | Life Insurance     |
| `non_life_insurance`  | 產險公司     | Non-life Insurance |

### maturity_bucket

| 項目 | 內容           |
|------|----------------|
| 類型 | string         |
| 必要 | 是             |
| 預設 | `"super_long"` |
| 說明 | 天期區間       |

**可用選項**：

| 值                     | 說明              | 典型範圍               |
|------------------------|-------------------|------------------------|
| `super_long`           | 超長端            | 20Y+ 或 30Y+           |
| `long`                 | 長端              | 5-10Y 或 10Y           |
| `10y_plus`             | 10 年以上         | 需確認 JSDA 是否有此桶 |
| `long_plus_super_long` | 長端 + 超長端合併 | 需手動計算             |

### measure

| 項目 | 內容              |
|------|-------------------|
| 類型 | string            |
| 必要 | 是                |
| 預設 | `"net_purchases"` |
| 說明 | 指標類型          |

**可用選項**：

| 值                | 說明           | 公式        |
|-------------------|----------------|-------------|
| `net_purchases`   | 淨買入（核心） | 買入 - 賣出 |
| `gross_purchases` | 買入金額       | -           |
| `gross_sales`     | 賣出金額       | -           |

### frequency

| 項目 | 內容        |
|------|-------------|
| 類型 | string      |
| 必要 | 是          |
| 預設 | `"monthly"` |
| 說明 | 頻率        |

**目前僅支援**：`monthly`（JSDA 僅提供月度數據）

---

## 選用參數

### currency

| 項目 | 內容     |
|------|----------|
| 類型 | string   |
| 必要 | 否       |
| 預設 | `"JPY"`  |
| 說明 | 輸出幣別 |

**可用選項**：

| 值    | 說明               |
|-------|--------------------|
| `JPY` | 日圓（原始單位）   |
| `USD` | 美元（需匯率換算） |

### usd_fx_source

| 項目 | 內容                             |
|------|----------------------------------|
| 類型 | string                           |
| 必要 | 否（僅當 `currency=USD` 時需要） |
| 說明 | USD 換算的匯率來源               |

**可用選項**：

| 值      | 來源            | 說明         |
|---------|-----------------|--------------|
| `fred`  | FRED DEXJPUS    | 美聯儲數據   |
| `boe`   | Bank of England | 英格蘭銀行   |
| `stooq` | Stooq           | 免費金融數據 |

### record_lookback_years

| 項目 | 內容                            |
|------|---------------------------------|
| 類型 | int                             |
| 必要 | 否                              |
| 預設 | `999`                           |
| 說明 | 計算「歷史新高/新低」的回溯年數 |

**說明**：
- `999` = 全樣本（從數據起點至 `end_date`）
- `5` = 近 5 年
- `10` = 近 10 年

### streak_sign

| 項目 | 內容           |
|------|----------------|
| 類型 | string         |
| 必要 | 否             |
| 預設 | `"negative"`   |
| 說明 | 連續判斷的符號 |

**可用選項**：

| 值         | 說明                    |
|------------|-------------------------|
| `negative` | 連續淨賣出（value < 0） |
| `positive` | 連續淨買入（value > 0） |

### output_format

| 項目 | 內容         |
|------|--------------|
| 類型 | string       |
| 必要 | 否           |
| 預設 | `"markdown"` |
| 說明 | 輸出格式     |

**可用選項**：

| 值         | 說明                      |
|------------|---------------------------|
| `json`     | JSON 格式（適合程式處理） |
| `markdown` | Markdown 格式（適合報告） |

---

## 輸入範例

### 快速檢查

```json
{
  "end_date": "2025-12",
  "investor_group": "insurance_companies",
  "maturity_bucket": "super_long",
  "measure": "net_purchases",
  "output_format": "markdown"
}
```

### 完整分析

```json
{
  "start_date": "2020-01",
  "end_date": "2025-12",
  "investor_group": "life_insurance",
  "maturity_bucket": "long_plus_super_long",
  "measure": "net_purchases",
  "frequency": "monthly",
  "currency": "USD",
  "usd_fx_source": "fred",
  "record_lookback_years": 10,
  "streak_sign": "negative",
  "output_format": "json"
}
```

### 驗證新聞

```json
{
  "end_date": "2025-12",
  "investor_group": "insurance_companies",
  "maturity_bucket": "super_long",
  "verify_claim": {
    "value_billion_jpy": -800,
    "source": "新聞/Bloomberg"
  }
}
```
