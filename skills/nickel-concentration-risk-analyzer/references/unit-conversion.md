# 單位轉換規則與假設

<overview>
鎳供給分析中最大的陷阱是單位混淆。本文件定義所有相關單位、
轉換規則與必要假設，確保分析口徑一致。
</overview>

<unit_definitions>
**單位定義**

| Unit Code | 中文 | 英文 | 說明 |
|-----------|------|------|------|
| `t_Ni_content` | 鎳金屬含量噸 | Tonnes of nickel content | 純鎳金屬重量，**本 Skill 預設** |
| `t_ore_wet` | 礦石濕噸 | Wet tonnes of ore | 含水礦石重量（最常見誤用） |
| `t_ore_dry` | 礦石乾噸 | Dry tonnes of ore | 乾燥後礦石重量 |
| `t_NPI_product` | NPI 產品噸 | Tonnes of NPI product | NPI 產品重量（約 10-15% Ni） |
| `t_matte` | 鎳鋶噸 | Tonnes of nickel matte | 鎳鋶重量（約 70-78% Ni） |
| `t_MHP` | MHP 產品噸 | Tonnes of MHP | 氫氧化鎳鈷（約 35-40% Ni） |
| `t_ferronickel` | 鎳鐵噸 | Tonnes of ferronickel | 鎳鐵合金（約 20-40% Ni） |
| `t_class1` | Class 1 鎳噸 | Tonnes of Class 1 nickel | 高純度鎳（≥99.8% Ni） |
| `t_class2` | Class 2 鎳噸 | Tonnes of Class 2 nickel | 低純度鎳（<99.8% Ni） |
</unit_definitions>

<conversion_formulas>
**轉換公式**

<formula name="ore_to_content">
**礦石 → 鎳含量**

```python
def ore_to_nickel_content(ore_tonnes, ni_grade, moisture=0.30):
    """
    將礦石噸數轉換為鎳金屬含量

    Args:
        ore_tonnes: 礦石噸數（濕噸或乾噸）
        ni_grade: 鎳品位（小數，如 0.015 = 1.5%）
        moisture: 水分含量（若輸入為濕噸，預設 30%）

    Returns:
        鎳金屬含量（噸）
    """
    # 若為濕噸，先轉乾噸
    dry_tonnes = ore_tonnes * (1 - moisture)

    # 計算鎳含量
    ni_content = dry_tonnes * ni_grade

    return ni_content
```

**範例：**
```
輸入：100 Mt ore wet tonnes, 1.5% Ni grade, 30% moisture
計算：100 * (1-0.30) * 0.015 = 1.05 Mt Ni content

⚠️ 這就是為什麼 379 Mt ore quota 不等於 379 Mt nickel！
```
</formula>

<formula name="NPI_to_content">
**NPI 產品 → 鎳含量**

```python
def npi_to_nickel_content(npi_tonnes, ni_content_pct=0.12):
    """
    NPI (Nickel Pig Iron) 轉換為鎳含量

    Args:
        npi_tonnes: NPI 產品噸數
        ni_content_pct: NPI 含鎳百分比（通常 10-15%）

    Returns:
        鎳金屬含量（噸）
    """
    return npi_tonnes * ni_content_pct
```

**NPI 品位範圍：**
| NPI 類型 | 典型 Ni% |
|----------|----------|
| Low-grade NPI | 8-12% |
| High-grade NPI | 12-18% |
| 常用假設 | 12-13% |
</formula>

<formula name="matte_to_content">
**鎳鋶 → 鎳含量**

```python
def matte_to_nickel_content(matte_tonnes, ni_content_pct=0.75):
    """
    Nickel matte 轉換為鎳含量

    Args:
        matte_tonnes: 鎳鋶噸數
        ni_content_pct: 鎳鋶含鎳百分比（通常 70-78%）
    """
    return matte_tonnes * ni_content_pct
```

**PT Vale Indonesia 範例：**
- 產出：~X tonnes matte
- 含鎳：~75%
- 等於：~X * 0.75 tonnes Ni content
</formula>

<formula name="MHP_to_content">
**MHP → 鎳含量**

```python
def mhp_to_nickel_content(mhp_tonnes, ni_content_pct=0.38):
    """
    Mixed Hydroxide Precipitate (MHP) 轉換

    MHP 常用於電池級鎳，含鎳約 35-40%
    """
    return mhp_tonnes * ni_content_pct
```
</formula>
</conversion_formulas>

<grade_assumptions>
**品位假設**

當來源數據未提供品位時，使用以下假設：

| 礦區/國家 | 典型 Ni 品位 | 範圍 | 備註 |
|-----------|-------------|------|------|
| Indonesia (laterite) | 1.5% | 1.2-1.8% | 紅土鎳礦 |
| Philippines (laterite) | 1.3% | 1.0-1.6% | 紅土鎳礦 |
| Russia (sulfide) | 1.8% | 1.5-2.5% | 硫化鎳礦 |
| Canada (sulfide) | 1.2% | 0.8-2.0% | 硫化鎳礦 |
| New Caledonia (laterite) | 2.5% | 2.0-3.0% | 高品位紅土 |

**⚠️ 使用假設時必須：**
1. 在輸出中標記 `confidence` 降低（建議 -0.2）
2. 標記 `is_estimate: true`
3. 說明使用的假設值
</grade_assumptions>

<moisture_assumptions>
**水分假設**

紅土鎳礦（laterite）的濕噸 vs 乾噸差異：

| 地區 | 典型水分 | 範圍 |
|------|----------|------|
| Indonesia | 30% | 25-35% |
| Philippines | 28% | 23-33% |
| New Caledonia | 32% | 28-38% |

**濕噸 → 乾噸轉換：**
```python
dry_tonnes = wet_tonnes * (1 - moisture_pct)
```
</moisture_assumptions>

<common_mistakes>
**常見錯誤**

<mistake name="ore_as_content">
**錯誤 1：將礦石噸當作鎳含量**

```
❌ 錯誤："Indonesia produced 150 Mt of nickel in 2024"
✅ 正確："Indonesia produced 150 Mt of nickel ORE in 2024"
        "Indonesia produced ~2.25 Mt of nickel CONTENT in 2024"

數量級差異：~66x
```
</mistake>

<mistake name="product_as_content">
**錯誤 2：將產品噸當作鎳含量**

```
❌ 錯誤："NPI production of 1 Mt = 1 Mt nickel"
✅ 正確："NPI production of 1 Mt = ~0.12 Mt nickel content (at 12% Ni)"

數量級差異：~8x
```
</mistake>

<mistake name="mixed_units">
**錯誤 3：混用不同口徑做計算**

```
❌ 錯誤：
  global_share = Indonesia_ore / World_nickel_content

✅ 正確：
  global_share = Indonesia_nickel_content / World_nickel_content
  # 或
  global_share = Indonesia_ore / World_ore
```
</mistake>

<mistake name="RKAB_misinterpret">
**錯誤 4：誤解 RKAB 配額口徑**

```
新聞："Indonesia cuts 2026 RKAB quota to 250 Mt from 379 Mt"

❌ 錯誤解讀："Indonesia cuts nickel production by 34%"

✅ 正確解讀：
  - 250 Mt 是 ORE wet tonnes 配額
  - 假設 1.5% Ni, 30% moisture：
    250 Mt * 0.70 * 0.015 ≈ 2.6 Mt Ni content
  - 這是配額，實際開採量可能不同
```
</mistake>
</common_mistakes>

<validation_rules>
**驗證規則**

在處理數據時，執行以下檢查：

```python
def validate_unit_sanity(value, unit, country, year):
    """
    檢查數值是否在合理範圍
    """
    # 單一國家年產量上限（Ni content）
    if unit == "t_Ni_content":
        if value > 5_000_000:  # 5 Mt
            return Warning("Suspiciously high - check if this is ore not content")

    # 全球年產量合理範圍
    if country == "World" and unit == "t_Ni_content":
        if value < 2_000_000 or value > 6_000_000:
            return Warning("Global production outside expected range (2-6 Mt)")

    # Indonesia 產量快速增長，需依年份調整預期
    if country == "Indonesia" and unit == "t_Ni_content":
        expected_ranges = {
            2020: (600_000, 900_000),
            2021: (900_000, 1_200_000),
            2022: (1_400_000, 1_800_000),
            2023: (1_800_000, 2_200_000),
            2024: (2_100_000, 2_500_000),
        }
        if year in expected_ranges:
            low, high = expected_ranges[year]
            if value < low * 0.8 or value > high * 1.2:
                return Warning(f"Indonesia {year} outside expected range")

    return OK()
```
</validation_rules>

<conversion_workflow>
**轉換工作流程**

```
1. 識別來源單位
   ↓
2. 確認品位/含量假設
   ↓
3. 執行轉換
   ↓
4. 標記 confidence 調整
   ↓
5. 記錄假設
```

**輸出範例：**
```json
{
  "original_value": 100000000,
  "original_unit": "t_ore_wet",
  "converted_value": 1050000,
  "converted_unit": "t_Ni_content",
  "conversion_assumptions": {
    "ni_grade": 0.015,
    "moisture": 0.30
  },
  "confidence_adjustment": -0.2,
  "is_estimate": true
}
```
</conversion_workflow>
