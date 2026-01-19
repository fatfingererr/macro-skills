# 輸入參數定義 (Input Schema)

本文件定義 `usd-reserve-loss-gold-revaluation` 技能的完整輸入參數。

---

## 參數總覽

| 參數 | 類型 | 必要 | 預設值 | 說明 |
|------|------|------|--------|------|
| scenario_date | string | ✅ | - | 情境估算基準日期 |
| entities | array[string] | ✅ | - | 分析對象清單 |
| monetary_aggregate | string | ✅ | - | 貨幣口徑 |
| liability_scope | string | ❌ | broad_money | 負債口徑 |
| weighting_method | string | ✅ | - | 加權方式 |
| weights | object | ❌ | - | 自訂權重 |
| fx_base | string | ❌ | USD | 計價幣別基準 |
| gold_reserve_unit | string | ❌ | troy_oz | 黃金單位 |
| gold_price_spot | float | ❌ | auto | 基準日金價 |
| fx_rates | object | ❌ | auto | 匯率 |
| data_providers | object | ❌ | - | 資料來源偏好 |
| output_format | string | ❌ | json | 輸出格式 |

---

## 詳細參數定義

### scenario_date

**類型**: `string` (YYYY-MM-DD)
**必要**: ✅

情境估算的基準日期，用於對應匯率、金價、貨幣量。

```json
{
  "scenario_date": "2026-01-07"
}
```

**特殊值**:
- `"today"`: 使用當日日期
- `"latest"`: 使用最新可得數據

---

### entities

**類型**: `array[string]`
**必要**: ✅

分析對象清單（國家或貨幣代碼）。

```json
{
  "entities": ["USD", "CNY", "JPY", "EUR", "GBP", "CHF", "AUD", "CAD"]
}
```

**支援的代碼**:

| 代碼 | 國家/地區 | 說明 |
|------|-----------|------|
| USD | 美國 | |
| EUR | 歐元區 | 包含 ECB + 成員國 |
| CNY | 中國 | |
| JPY | 日本 | |
| GBP | 英國 | |
| CHF | 瑞士 | |
| AUD | 澳洲 | |
| CAD | 加拿大 | 注意：無黃金儲備 |
| INR | 印度 | |
| RUB | 俄羅斯 | 數據可能受限 |
| ZAR | 南非 | |
| KZT | 哈薩克 | |

---

### monetary_aggregate

**類型**: `string`
**必要**: ✅

貨幣口徑選擇。

```json
{
  "monetary_aggregate": "M0"
}
```

**可用值**:

| 值 | 說明 | 使用場景 |
|----|------|----------|
| M0 | 貨幣基數（央行負債） | 央行壓力測試 |
| M1 | 狹義貨幣 | 中間口徑 |
| M2 | 廣義貨幣（含銀行存款） | 全體系壓力測試 |
| MB | Monetary Base（同 M0） | 美國術語 |
| M3 | 最廣義貨幣 | 某些國家使用 |

---

### liability_scope

**類型**: `string`
**必要**: ❌
**預設**: `"broad_money"`

貨幣負債口徑。

```json
{
  "liability_scope": "central_bank"
}
```

**可用值**:

| 值 | 說明 |
|----|------|
| central_bank | 央行直接負債（偏向貨幣基數） |
| broad_money | 全體銀行體系的廣義貨幣 |

---

### weighting_method

**類型**: `string`
**必要**: ✅

加權方式選擇。

```json
{
  "weighting_method": "fx_turnover"
}
```

**可用值**:

| 值 | 說明 | 來源 |
|----|------|------|
| fx_turnover | 外匯成交佔比加權 | BIS Triennial Survey |
| reserve_share | 外匯儲備幣別佔比 | IMF COFER |
| equal | 等權重 | - |
| custom | 自訂權重 | 需配合 weights 參數 |

---

### weights

**類型**: `object{string: float}`
**必要**: 當 `weighting_method="custom"` 時必要

自訂權重。

```json
{
  "weighting_method": "custom",
  "weights": {
    "USD": 0.88,
    "EUR": 0.31,
    "JPY": 0.17,
    "CNY": 0.10
  }
}
```

**注意**:
- 權重總和不需要等於 1（BIS 口徑允許 > 1）
- 未列出的 entity 權重視為 0

---

### fx_base

**類型**: `string`
**必要**: ❌
**預設**: `"USD"`

將各國貨幣量換算成同一計價幣別的基準。

```json
{
  "fx_base": "USD"
}
```

**可用值**: `USD`, `EUR`, `SDR`（特別提款權）

---

### gold_reserve_unit

**類型**: `string`
**必要**: ❌
**預設**: `"troy_oz"`

黃金儲備的輸出單位。

```json
{
  "gold_reserve_unit": "tonnes"
}
```

**可用值**:

| 值 | 說明 |
|----|------|
| troy_oz | 金衡盎司（內部計算用） |
| tonnes | 公噸（WGC 常用） |

---

### gold_price_spot

**類型**: `float`
**必要**: ❌
**預設**: 自動抓取

基準日金價（USD per troy oz）。

```json
{
  "gold_price_spot": 2050.0
}
```

若不填，腳本會從 FRED 或 Yahoo Finance 抓取。

---

### fx_rates

**類型**: `object{string: float}`
**必要**: ❌
**預設**: 自動抓取

基準日匯率。格式：`1 單位該貨幣 = ? USD`。

```json
{
  "fx_rates": {
    "USD": 1.0,
    "EUR": 1.08,
    "JPY": 0.0068,
    "CNY": 0.14,
    "GBP": 1.27,
    "CHF": 1.17
  }
}
```

若不填，腳本會自動抓取。

---

### data_providers

**類型**: `object`
**必要**: ❌

指定資料來源偏好。

```json
{
  "data_providers": {
    "money": "FRED",
    "gold": "WGC",
    "fx_turnover": "BIS",
    "fx_rates": "ECB"
  }
}
```

**可用值**:

| 數據類型 | 可用來源 |
|----------|----------|
| money | FRED, IMF, central_bank |
| gold | WGC, IMF |
| fx_turnover | BIS |
| fx_rates | FRED, ECB, yahoo |

---

### output_format

**類型**: `string`
**必要**: ❌
**預設**: `"json"`

輸出格式。

```json
{
  "output_format": "markdown"
}
```

**可用值**:

| 值 | 說明 |
|----|------|
| json | JSON 格式（工程串接用） |
| markdown | Markdown 格式（人類閱讀用） |

---

## 完整輸入範例

### 範例 1: 快速檢查（使用預設）

```json
{
  "scenario_date": "today",
  "entities": ["USD", "EUR", "CNY", "JPY"],
  "monetary_aggregate": "M0",
  "weighting_method": "fx_turnover"
}
```

### 範例 2: 完整自訂

```json
{
  "scenario_date": "2026-01-07",
  "entities": ["USD", "CNY", "JPY", "GBP", "ZAR", "RUB", "KZT"],
  "monetary_aggregate": "M2",
  "liability_scope": "broad_money",
  "weighting_method": "fx_turnover",
  "fx_base": "USD",
  "gold_reserve_unit": "troy_oz",
  "gold_price_spot": 2050.0,
  "fx_rates": {
    "USD": 1.0,
    "CNY": 0.14,
    "JPY": 0.0068,
    "GBP": 1.27,
    "ZAR": 0.053,
    "RUB": 0.011,
    "KZT": 0.0020
  },
  "data_providers": {
    "money": "FRED",
    "gold": "WGC"
  },
  "output_format": "json"
}
```

### 範例 3: 自訂權重

```json
{
  "scenario_date": "2026-01-07",
  "entities": ["USD", "EUR", "CNY"],
  "monetary_aggregate": "M0",
  "weighting_method": "custom",
  "weights": {
    "USD": 0.70,
    "EUR": 0.20,
    "CNY": 0.15
  },
  "output_format": "markdown"
}
```

### 範例 4: M0 vs M2 比較

```json
{
  "mode": "compare_aggregates",
  "scenario_date": "2026-01-07",
  "entities": ["USD", "EUR", "CNY", "JPY", "GBP"],
  "weighting_method": "fx_turnover",
  "output_format": "json"
}
```

---

## 參數驗證規則

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal
from datetime import date

class GoldRevaluationInput(BaseModel):
    scenario_date: str
    entities: List[str] = Field(min_items=1)
    monetary_aggregate: Literal["M0", "M1", "M2", "MB", "M3"]
    liability_scope: Literal["central_bank", "broad_money"] = "broad_money"
    weighting_method: Literal["fx_turnover", "reserve_share", "equal", "custom"]
    weights: Optional[Dict[str, float]] = None
    fx_base: str = "USD"
    gold_reserve_unit: Literal["troy_oz", "tonnes"] = "troy_oz"
    gold_price_spot: Optional[float] = None
    fx_rates: Optional[Dict[str, float]] = None
    data_providers: Optional[Dict[str, str]] = None
    output_format: Literal["json", "markdown"] = "json"

    @validator('weights', always=True)
    def validate_weights(cls, v, values):
        if values.get('weighting_method') == 'custom' and v is None:
            raise ValueError('weights required when weighting_method is custom')
        return v

    @validator('entities')
    def validate_entities(cls, v):
        valid = {"USD", "EUR", "CNY", "JPY", "GBP", "CHF", "AUD", "CAD",
                 "INR", "RUB", "ZAR", "KZT", "BRL", "MXN", "KRW"}
        for e in v:
            if e not in valid:
                raise ValueError(f'Unknown entity: {e}')
        return v
```

---

## CLI 參數對應

```bash
python scripts/gold_revaluation.py \
  --date 2026-01-07 \
  --entities USD,CNY,JPY,EUR,GBP \
  --aggregate M0 \
  --weighting fx_turnover \
  --gold-price 2050 \
  --output result.json \
  --format json
```

| CLI 參數 | JSON 參數 |
|----------|-----------|
| --date | scenario_date |
| --entities | entities |
| --aggregate | monetary_aggregate |
| --weighting | weighting_method |
| --gold-price | gold_price_spot |
| --output | (輸出檔案路徑) |
| --format | output_format |
