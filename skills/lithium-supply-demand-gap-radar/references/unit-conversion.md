# 鋰單位轉換參考

鋰產業鏈中使用多種單位，混淆單位是最常見的分析錯誤之一。本文件提供標準轉換規則。

---

## 核心單位定義

### Li (Lithium Metal Content)
- 定義: 純鋰金屬含量
- 用途: USGS 等機構的標準報告口徑
- 符號: t Li, kt Li

### LCE (Lithium Carbonate Equivalent)
- 定義: 碳酸鋰當量，化學式 Li₂CO₃
- 用途: 產業界最常用的統一口徑
- 符號: t LCE, kt LCE
- 鋰含量: 18.79% Li

### LHE (Lithium Hydroxide Equivalent)
- 定義: 氫氧化鋰當量，化學式 LiOH·H₂O
- 用途: 電池級產品常用
- 符號: t LHE
- 鋰含量: 16.52% Li（一水合物）

---

## 轉換公式

### Li ↔ LCE

```python
# Li → LCE
LCE = Li * 5.323

# LCE → Li
Li = LCE / 5.323

# 推導: Li₂CO₃ 分子量 73.89, Li 分子量 6.94
# 73.89 / (6.94 * 2) = 5.323
```

**速算表**
| Li (kt) | LCE (kt) |
|---------|----------|
| 10 | 53.23 |
| 50 | 266.15 |
| 100 | 532.3 |
| 200 | 1,064.6 |

---

### Li ↔ LHE

```python
# Li → LHE (一水合物)
LHE = Li * 6.048

# LHE → Li
Li = LHE / 6.048

# 推導: LiOH·H₂O 分子量 41.96, Li 分子量 6.94
# 41.96 / 6.94 = 6.048
```

---

### LCE ↔ LHE

```python
# LCE → LHE
LHE = LCE * 1.136

# LHE → LCE
LCE = LHE / 1.136

# 推導: 6.048 / 5.323 = 1.136
```

---

## 鋰輝石 (Spodumene) 轉換

### Spodumene Concentrate (SC6)
- 定義: 6% Li₂O 鋰輝石精礦
- 用途: 澳洲礦場出口主要產品
- 實際 Li₂O 含量: 5.5-7.0%

```python
# SC6 → LCE (假設 6% Li₂O)
LCE = SC6_tonnes * 0.06 * 2.473 * (1 - moisture_loss)

# 其中:
# - 0.06 = 6% Li₂O 含量
# - 2.473 = Li₂O 到 Li₂CO₃ 的轉換係數
# - moisture_loss = 加工損失，通常 5-10%

# 簡化（假設 8% 損失）:
LCE ≈ SC6 * 0.136
```

**速算表**（SC6 @ 6% Li₂O, 8% 損失）
| SC6 (kt) | LCE (kt) |
|----------|----------|
| 100 | 13.6 |
| 500 | 68 |
| 1,000 | 136 |
| 5,000 | 680 |

---

## 電池需求轉換

### GWh → kg Li

電池到鋰需求的轉換取決於電池化學：

| 電池類型 | kg Li / kWh | 說明 |
|----------|-------------|------|
| NMC 111 | 0.14-0.16 | 三元正極 |
| NMC 532 | 0.12-0.14 | 改良三元 |
| NMC 622 | 0.10-0.12 | 高鎳三元 |
| NMC 811 | 0.08-0.10 | 超高鎳三元 |
| NCA | 0.10-0.12 | 鎳鈷鋁 |
| LFP | 0.05-0.08 | 磷酸鐵鋰（無鈷）|
| LMO | 0.08-0.10 | 錳酸鋰 |

**情境假設**

```python
# 保守估計（LFP 佔比上升）
kg_per_kwh_conservative = 0.12

# 中性估計（混合市場）
kg_per_kwh_neutral = 0.15

# 積極估計（高鎳主導）
kg_per_kwh_aggressive = 0.18
```

**計算公式**

```python
# GWh → kt LCE
li_demand_kt_lce = battery_gwh * kg_per_kwh * 5.323 / 1000

# 例: 1000 GWh @ 0.15 kg/kWh
# = 1000 * 0.15 * 5.323 / 1000 = 798.45 kt LCE
```

---

## 價格單位轉換

### 價格報價常見單位

| 單位 | 說明 | 典型範圍 |
|------|------|----------|
| USD/t LCE | 碳酸鋰每噸 | 10,000 - 80,000 |
| USD/kg LCE | 碳酸鋰每公斤 | 10 - 80 |
| CNY/t | 中國人民幣每噸 | 70,000 - 600,000 |
| USD/t SC6 | 鋰輝石每噸 | 1,000 - 6,000 |

**轉換**

```python
# USD/t → USD/kg
usd_per_kg = usd_per_t / 1000

# CNY/t → USD/t (需匯率)
usd_per_t = cny_per_t / exchange_rate

# SC6 價格 → 隱含 LCE 價格
implied_lce = sc6_price / 0.136  # 大約
```

---

## 常見錯誤與陷阱

### 1. Li vs LCE 混淆

**錯誤**: 「全球鋰產量 100 萬噸」
**問題**: 是 Li 還是 LCE？差 5 倍！

**正確表述**:
- USGS 數據: 100 kt Li（鋰金屬含量）
- 等於: 532 kt LCE

### 2. Spodumene vs LCE 混淆

**錯誤**: 「澳洲出口 500 萬噸鋰」
**問題**: 是鋰輝石還是 LCE？

**正確表述**:
- 澳洲出口: 5,000 kt spodumene concentrate
- 等於: ~680 kt LCE

### 3. 電池容量 vs 鋰需求

**錯誤**: 「1000 GWh 電池 = 1000 kt 鋰」
**問題**: 完全錯誤的假設

**正確計算**:
- 1000 GWh × 0.15 kg/kWh = 150 kt Li
- = 798 kt LCE

### 4. 價格單位不一致

**錯誤**: 比較 USD/kg 和 CNY/t 價格
**問題**: 單位和幣種都不同

**正確做法**:
1. 統一為 USD/t 或 USD/kg
2. 使用當日匯率
3. 標註報價規格（CIF/FOB）

---

## 轉換函數模板

```python
class LithiumUnitConverter:
    """鋰單位轉換工具"""

    # 常數
    LI_TO_LCE = 5.323
    LI_TO_LHE = 6.048
    LCE_TO_LHE = 1.136
    SC6_TO_LCE = 0.136  # 假設 6% Li₂O, 8% 損失

    @staticmethod
    def li_to_lce(li_kt: float) -> float:
        """鋰金屬 → 碳酸鋰當量"""
        return li_kt * LithiumUnitConverter.LI_TO_LCE

    @staticmethod
    def lce_to_li(lce_kt: float) -> float:
        """碳酸鋰當量 → 鋰金屬"""
        return lce_kt / LithiumUnitConverter.LI_TO_LCE

    @staticmethod
    def sc6_to_lce(sc6_kt: float, li2o_pct: float = 6.0, loss_pct: float = 8.0) -> float:
        """鋰輝石精礦 → 碳酸鋰當量"""
        effective = 1 - loss_pct / 100
        return sc6_kt * (li2o_pct / 100) * 2.473 * effective

    @staticmethod
    def gwh_to_lce(gwh: float, kg_per_kwh: float = 0.15) -> float:
        """電池容量 → 碳酸鋰當量需求"""
        li_kt = gwh * kg_per_kwh / 1000  # GWh → kt Li
        return li_kt * LithiumUnitConverter.LI_TO_LCE

    @staticmethod
    def validate_unit(value: float, unit: str, context: str = "") -> dict:
        """驗證數值是否在合理範圍"""
        ranges = {
            "kt_LCE": (0, 5000),      # 全球年產量級
            "kt_Li": (0, 1000),       # 全球年產量級
            "USD_per_t_LCE": (5000, 100000),  # 價格範圍
            "GWh": (0, 10000),        # 全球電池需求級
        }

        min_val, max_val = ranges.get(unit, (0, float("inf")))
        in_range = min_val <= value <= max_val

        return {
            "value": value,
            "unit": unit,
            "in_range": in_range,
            "expected_range": f"{min_val} - {max_val}",
            "context": context
        }
```

---

## 單位標註最佳實踐

### 輸出格式

每個數值都應包含單位標註：

```json
{
  "global_production_2024": {
    "value": 180,
    "unit": "kt_LCE",
    "source": "USGS",
    "original_unit": "kt_Li",
    "conversion_applied": true
  }
}
```

### 報告中的表述

**推薦**:
- 「全球鋰產量達 180 kt LCE（USGS 口徑：34 kt Li）」
- 「電池需求 1,000 GWh，對應鋰需求約 150 kt Li（假設 0.15 kg/kWh）」

**避免**:
- 「全球鋰產量達 180 萬噸」（缺少單位說明）
- 「鋰需求 1,000」（沒有單位，無法理解）
