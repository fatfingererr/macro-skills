# 輸入參數結構 (Input Schema)

## 主要參數

### entities (必填)
- **型別**: `list[string]`
- **說明**: 要分析的國家/地區代碼列表
- **格式**: ISO 3166-1 alpha-3 或預設群組名稱

**單一國家範例**:
```json
["JPN"]
```

**多國範例**:
```json
["JPN", "USA", "DEU", "GBR", "FRA", "ITA", "CAN"]
```

**預設群組**:
| 群組名稱 | 包含國家 |
|----------|----------|
| G7 | USA, JPN, DEU, GBR, FRA, ITA, CAN |
| G20 | G7 + CHN, IND, BRA, RUS, AUS, KOR, MEX, IDN, TUR, SAU, ARG, ZAF, EU |
| OECD | 38 個 OECD 成員國 |
| EU27 | 27 個歐盟成員國 |
| ASEAN | SGP, MYS, THA, IDN, PHL, VNM, MMR, KHM, LAO, BRN |
| EM_ASIA | CHN, IND, KOR, TWN, THA, MYS, IDN, PHL, VNM |

**使用群組**:
```json
["G7"]  // 展開為 7 個國家
```

---

### start_year (必填)
- **型別**: `int`
- **說明**: 歷史資料起始年份
- **建議**: 2010 或更早，以獲得足夠的趨勢資料
- **範圍**: 1960 - 當前年份

**範例**:
```json
2010
```

---

### end_year (必填)
- **型別**: `int`
- **說明**: 歷史資料結束年份（通常為最近可用年份）
- **建議**: 2022 或 2023（視資料可用性）
- **範圍**: start_year - 當前年份

**範例**:
```json
2023
```

---

### forecast_end_year (選填)
- **型別**: `int`
- **預設值**: `2050`
- **說明**: 撫養比預測結束年份
- **範圍**: end_year - 2100

**範例**:
```json
2050
```

---

### dependency_components (選填)
- **型別**: `list[string]`
- **預設值**: `["old_age", "youth", "total"]`
- **說明**: 要分析的撫養比組成

**可選項**:
| 組成 | 定義 |
|------|------|
| old_age | 老年撫養比 (65+ / 15-64) |
| youth | 青年撫養比 (0-14 / 15-64) |
| total | 總撫養比 ((0-14 + 65+) / 15-64) |

**範例**:
```json
["old_age"]  // 僅分析老年撫養比
```

---

### fiscal_modules (選填)
- **型別**: `list[string]`
- **預設值**: `["debt", "spending", "health"]`
- **說明**: 要啟用的財政分析模組

**可選項**:
| 模組 | 說明 |
|------|------|
| debt | 政府債務/GDP 分析 |
| spending | 政府支出/GDP 分析 |
| health | 健康支出/GDP 分析 |
| pension | 養老金支出分析（若資料可用）|
| revenue | 政府收入分析 |
| primary_balance | 基本財政餘額分析 |

**範例**:
```json
["debt", "spending", "health", "primary_balance"]
```

---

### bureaucracy_proxies (選填)
- **型別**: `list[string]`
- **預設值**: `["gov_wage_bill", "public_employment_share", "gov_consumption"]`
- **說明**: 官僚膨脹代理指標

**可選項**:
| 指標 | 說明 | 資料可用性 |
|------|------|-----------|
| gov_wage_bill | 公部門薪資/GDP | 中等 |
| public_employment_share | 公務員/總就業人口 | 低 |
| gov_consumption | 政府消費/GDP | 高 |
| consulting_proxy | 政府諮詢支出代理 | 低 |

**範例**:
```json
["gov_consumption"]  // 僅使用高可用性指標
```

---

### inflation_channel (選填)
- **型別**: `string`
- **預設值**: `"real_rates"`
- **說明**: 通膨/稀釋路徑分析方式

**可選項**:
| 選項 | 說明 |
|------|------|
| expected_inflation | 使用通膨預期（需調查資料）|
| real_rates | 使用事後實質利率 |
| money_growth | 使用貨幣供給成長率 |
| financial_repression | 綜合金融抑制指數 |

**範例**:
```json
"real_rates"
```

---

### weights (選填)
- **型別**: `dict[string, float]`
- **預設值**:
```json
{
  "aging": 0.35,
  "debt": 0.35,
  "bloat": 0.15,
  "growth_drag": 0.15
}
```
- **說明**: 四支柱的權重配置
- **限制**: 所有權重加總應為 1.0

**自訂範例**:
```json
{
  "aging": 0.40,
  "debt": 0.30,
  "bloat": 0.15,
  "growth_drag": 0.15
}
```

---

## 完整輸入範例

### 範例 1: 單一國家完整分析
```json
{
  "entities": ["JPN"],
  "start_year": 2010,
  "end_year": 2023,
  "forecast_end_year": 2050,
  "dependency_components": ["old_age", "youth", "total"],
  "fiscal_modules": ["debt", "spending", "health"],
  "bureaucracy_proxies": ["gov_consumption"],
  "inflation_channel": "real_rates",
  "weights": {
    "aging": 0.35,
    "debt": 0.35,
    "bloat": 0.15,
    "growth_drag": 0.15
  }
}
```

### 範例 2: G7 跨國比較（簡化）
```json
{
  "entities": ["G7"],
  "start_year": 2015,
  "end_year": 2023
}
```

### 範例 3: 亞洲新興市場自訂權重
```json
{
  "entities": ["CHN", "IND", "IDN", "THA", "VNM"],
  "start_year": 2010,
  "end_year": 2023,
  "forecast_end_year": 2050,
  "weights": {
    "aging": 0.40,
    "debt": 0.25,
    "bloat": 0.20,
    "growth_drag": 0.15
  }
}
```

---

## 參數驗證規則

```python
def validate_input(params):
    errors = []

    # 必填檢查
    if "entities" not in params or not params["entities"]:
        errors.append("entities is required and cannot be empty")

    if "start_year" not in params:
        errors.append("start_year is required")

    if "end_year" not in params:
        errors.append("end_year is required")

    # 範圍檢查
    if params.get("start_year", 0) > params.get("end_year", 9999):
        errors.append("start_year must be <= end_year")

    if params.get("forecast_end_year", 2050) < params.get("end_year", 0):
        errors.append("forecast_end_year must be >= end_year")

    # 權重加總檢查
    weights = params.get("weights", {})
    if weights:
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"weights must sum to 1.0, got {total}")

    return errors
```
