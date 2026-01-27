# 期貨合約與商品群組對照表

## 1. 預設對照表

```python
DEFAULT_CONTRACTS_MAP = {
    # Grains (穀物)
    "CORN": "grains",
    "WHEAT-SRW": "grains",      # Soft Red Winter (CBOT)
    "WHEAT-HRW": "grains",      # Hard Red Winter (KCBT)
    "WHEAT-HRS": "grains",      # Hard Red Spring (MGE)
    "OATS": "grains",
    "ROUGH RICE": "grains",
    "SORGHUM": "grains",

    # Oilseeds (油籽)
    "SOYBEANS": "oilseeds",
    "SOYBEAN OIL": "oilseeds",
    "SOYBEAN MEAL": "oilseeds",

    # Meats (肉類)
    "LIVE CATTLE": "meats",
    "FEEDER CATTLE": "meats",
    "LEAN HOGS": "meats",

    # Softs (軟性商品)
    "COFFEE C": "softs",
    "SUGAR NO. 11": "softs",
    "COCOA": "softs",
    "COTTON NO. 2": "softs",
    "ORANGE JUICE": "softs"
}
```

---

## 2. 合約規格詳情

### 2.1 Grains（穀物）

| 商品       | CFTC 代碼 | 交易所 | 合約大小    | 報價單位       |
|------------|-----------|--------|-------------|----------------|
| Corn       | 002602    | CBOT   | 5,000 bu    | cents/bushel   |
| Wheat SRW  | 001602    | CBOT   | 5,000 bu    | cents/bushel   |
| Wheat HRW  | 001612    | KCBT   | 5,000 bu    | cents/bushel   |
| Wheat HRS  | 001626    | MGE    | 5,000 bu    | cents/bushel   |
| Oats       | 004603    | CBOT   | 5,000 bu    | cents/bushel   |
| Rough Rice | 039601    | CBOT   | 2,000 cwt   | cents/cwt      |

### 2.2 Oilseeds（油籽）

| 商品         | CFTC 代碼 | 交易所 | 合約大小    | 報價單位       |
|--------------|-----------|--------|-------------|----------------|
| Soybeans     | 005602    | CBOT   | 5,000 bu    | cents/bushel   |
| Soybean Oil  | 007601    | CBOT   | 60,000 lbs  | cents/lb       |
| Soybean Meal | 026603    | CBOT   | 100 tons    | $/ton          |

### 2.3 Meats（肉類）

| 商品          | CFTC 代碼 | 交易所 | 合約大小    | 報價單位       |
|---------------|-----------|--------|-------------|----------------|
| Live Cattle   | 057642    | CME    | 40,000 lbs  | cents/lb       |
| Feeder Cattle | 061641    | CME    | 50,000 lbs  | cents/lb       |
| Lean Hogs     | 054642    | CME    | 40,000 lbs  | cents/lb       |

### 2.4 Softs（軟性商品）

| 商品         | CFTC 代碼 | 交易所 | 合約大小    | 報價單位       |
|--------------|-----------|--------|-------------|----------------|
| Coffee C     | 083731    | ICE    | 37,500 lbs  | cents/lb       |
| Sugar No.11  | 080732    | ICE    | 112,000 lbs | cents/lb       |
| Cocoa        | 073732    | ICE    | 10 MT       | $/MT           |
| Cotton No.2  | 033661    | ICE    | 50,000 lbs  | cents/lb       |
| Orange Juice | 040701    | ICE    | 15,000 lbs  | cents/lb       |

---

## 3. CFTC COT 報表中的名稱

COT 報表中的商品名稱可能與上述不完全一致，以下是常見對照：

| COT 報表名稱                           | 簡稱         | 群組     |
|----------------------------------------|--------------|----------|
| CORN - CHICAGO BOARD OF TRADE          | CORN         | grains   |
| WHEAT-SRW - CHICAGO BOARD OF TRADE     | WHEAT-SRW    | grains   |
| WHEAT-HRW - KANSAS CITY BOARD OF TRADE | WHEAT-HRW    | grains   |
| WHEAT-HRS - MINNEAPOLIS GRAIN EXCHANGE | WHEAT-HRS    | grains   |
| SOYBEANS - CHICAGO BOARD OF TRADE      | SOYBEANS     | oilseeds |
| SOYBEAN OIL - CHICAGO BOARD OF TRADE   | SOYBEAN OIL  | oilseeds |
| SOYBEAN MEAL - CHICAGO BOARD OF TRADE  | SOYBEAN MEAL | oilseeds |
| LIVE CATTLE - CHICAGO MERCANTILE EXCH  | LIVE CATTLE  | meats    |
| LEAN HOGS - CHICAGO MERCANTILE EXCH    | LEAN HOGS    | meats    |
| COFFEE C - ICE FUTURES U.S.            | COFFEE C     | softs    |
| SUGAR NO. 11 - ICE FUTURES U.S.        | SUGAR NO. 11 | softs    |
| COTTON NO. 2 - ICE FUTURES U.S.        | COTTON NO. 2 | softs    |

---

## 4. 標準化邏輯

### 4.1 名稱匹配函數

```python
def normalize_contract_name(raw_name):
    """標準化 COT 報表中的商品名稱"""
    # 移除交易所後綴
    name = raw_name.split(" - ")[0].strip().upper()

    # 處理特殊情況
    mappings = {
        "WHEAT": "WHEAT-SRW",  # 預設為 SRW
        "WHEAT (SOFT RED WINTER)": "WHEAT-SRW",
        "WHEAT (HARD RED WINTER)": "WHEAT-HRW",
        "WHEAT (HARD RED SPRING)": "WHEAT-HRS",
        "SOYBEAN": "SOYBEANS",
        "SOY MEAL": "SOYBEAN MEAL",
        "SOY OIL": "SOYBEAN OIL",
        "HOGS": "LEAN HOGS",
        "CATTLE": "LIVE CATTLE",
        "COFFEE": "COFFEE C",
        "SUGAR": "SUGAR NO. 11",
        "COTTON": "COTTON NO. 2"
    }

    return mappings.get(name, name)
```

### 4.2 群組映射函數

```python
def get_group(contract_name, contracts_map=None):
    """取得商品所屬群組"""
    if contracts_map is None:
        contracts_map = DEFAULT_CONTRACTS_MAP

    normalized = normalize_contract_name(contract_name)
    return contracts_map.get(normalized, "other")
```

---

## 5. 自訂對照表

使用者可以自訂對照表以符合特定需求：

```json
{
  "custom_contracts_map": {
    "CORN": "row_crops",
    "WHEAT-SRW": "row_crops",
    "SOYBEANS": "row_crops",
    "LIVE CATTLE": "proteins",
    "LEAN HOGS": "proteins",
    "COFFEE C": "tropical",
    "SUGAR NO. 11": "tropical",
    "COCOA": "tropical"
  }
}
```

這樣可以依據分析目的調整分組邏輯。

---

## 6. 注意事項

1. **Mini/Micro 合約**：部分商品有 Mini 版本，通常應排除或分開計算
2. **期權與期貨**：COT 有分開報告和合併報告，建議使用合併報告
3. **新上市商品**：新商品可能需要手動加入對照表
4. **交易所變更**：部分商品可能轉移交易所，需注意歷史連續性
