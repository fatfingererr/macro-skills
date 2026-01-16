# Mine-Level 產量錨點

<overview>
本文件提供主要礦區/園區的產量數據錨點，
用於驗證國家級數據或計算 Mine_CR5 指標。
數據來源主要為公司報告（Tier 1）。
</overview>

<data_quality_note>
**數據品質說明**

Mine-level 數據的挑戰：
1. **口徑不一致**：各公司報告口徑不同
2. **時間差異**：財年 vs 日曆年
3. **整合難度**：需手動收集多個來源
4. **保守估計**：部分數據為估計值

**Confidence 評分基準：**
| 來源類型 | Confidence |
|----------|------------|
| 審計財報數字 | 0.90 |
| 公司新聞稿 | 0.80 |
| 產業報告估計 | 0.65 |
| 媒體報導 | 0.50 |
</data_quality_note>

<indonesia_anchors>
**印尼主要礦區錨點**

<anchor name="weda_bay">
**Weda Bay Nickel (Eramet 合資)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| Ore sold | ~X Mt | wet tonnes | 2024e | Eramet |
| Ni grade | ~1.8% | | | |
| Implied Ni | ~X kt | Ni content | 2024e | 計算 |

**來源 URL：**
- https://www.eramet.com/en/investors
- https://www.wedabaynickel.com/

**⚠️ 注意：**
Eramet 報告的是 "tonnes sold"，可能包含第三方購入礦石。
</anchor>

<anchor name="IMIP">
**IMIP (Indonesia Morowali Industrial Park)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| NPI capacity | ~X Mt | NPI product | 2024 | 產業報告 |
| Implied Ni | ~X-X kt | Ni content | 2024 | @12-15% |

**⚠️ 注意：**
- IMIP 無單一公開報告
- 需整合多家公司數據
- 產能 ≠ 實際產量
</anchor>

<anchor name="nickel_industries">
**Nickel Industries (NIC.AX)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| NPI production | ~100 kt | product tonnes | 2024 | Annual Report |
| Nickel metal | ~X kt | Ni content | 2024 | Annual Report |
| Total Ni | ~15-18 kt | Ni content | 2024 | 計算 |

**來源 URL：**
- https://nickelindustries.com/investors/

**數據結構：**
```json
{
  "company": "Nickel Industries",
  "ticker": "NIC.AX",
  "products": [
    {
      "type": "NPI",
      "volume": 100000,
      "unit": "t_NPI_product",
      "ni_content_pct": 0.13,
      "implied_ni": 13000
    },
    {
      "type": "Nickel metal",
      "volume": 5000,
      "unit": "t_Ni_content",
      "ni_content_pct": 0.99
    }
  ],
  "total_ni_content": 18000,
  "year": 2024,
  "confidence": 0.85
}
```
</anchor>

<anchor name="pt_vale">
**PT Vale Indonesia (INCO.JK)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| Matte production | ~70-75 kt | matte tonnes | 2024 | 財報 |
| Ni content | ~75% | | | |
| Implied Ni | ~52-56 kt | Ni content | 2024 | 計算 |

**來源 URL：**
- https://www.vale.com/indonesia

**特點：**
- 印尼唯一 Class 1 nickel 生產商
- 高純度鎳鋶 (~75% Ni)
- 歷史出口合約至日本
</anchor>

<anchor name="antam">
**PT Antam (ANTM.JK)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| Ferronickel | ~18-20 kt | Ni content | 2024 | 財報 |
| Ore sales | ~X Mt | wet tonnes | 2024 | |

**來源 URL：**
- https://www.antam.com/investor-relations
</anchor>

<anchor name="harita">
**Harita Group (OSS Park)**

| 項目 | 數據 | 口徑 | 年份 | 來源 |
|------|------|------|------|------|
| NPI capacity | ~X kt | Ni content | 2024 | 產業報告 |
| HPAL capacity | ~X kt | Ni content | 2025+ | 建設中 |

**⚠️ 注意：**
- 私人企業，公開數據有限
- 需依賴產業報告估計
</anchor>
</indonesia_anchors>

<global_anchors>
**全球其他主要礦區**

<anchor name="russia">
**俄羅斯**

| 礦區/公司 | 產量 (kt Ni) | 年份 | 來源 |
|-----------|-------------|------|------|
| Norilsk Nickel | ~180-200 | 2024 | 公司報告 |
| (全國總計) | ~210 | 2024 | USGS |

**Norilsk Nickel (MCX: GMKN):**
- 全球最大硫化鎳生產商
- 副產品：鈀、鉑、銅
- 受制裁影響出口
</anchor>

<anchor name="philippines">
**菲律賓**

| 礦區 | 產量 (kt Ni) | 年份 | 來源 |
|------|-------------|------|------|
| Nickel Asia | ~X | 2024 | 公司報告 |
| Others | ~X | 2024 | 產業報告 |
| (全國總計) | ~400 | 2024 | USGS |

**特點：**
- 主要出口礦石（過去）
- 近年發展在地加工
</anchor>

<anchor name="australia">
**澳洲**

| 礦區/公司 | 產量 (kt Ni) | 年份 | 來源 |
|-----------|-------------|------|------|
| BHP Nickel West | ~70-80 | 2024 | 公司報告 |
| IGO | ~20-25 | 2024 | 公司報告 |
| (全國總計) | ~130-150 | 2024 | USGS |

**⚠️ 注意：**
- 澳洲鎳礦面臨成本壓力
- 部分礦山已停產或 care & maintenance
</anchor>

<anchor name="canada">
**加拿大**

| 礦區/公司 | 產量 (kt Ni) | 年份 | 來源 |
|-----------|-------------|------|------|
| Vale Sudbury | ~X | 2024 | Vale 報告 |
| Glencore | ~X | 2024 | Glencore 報告 |
| (全國總計) | ~130-150 | 2024 | USGS |
</anchor>

<anchor name="new_caledonia">
**新喀里多尼亞**

| 礦區/公司 | 產量 (kt Ni) | 年份 | 來源 |
|-----------|-------------|------|------|
| SLN (Eramet) | ~40-50 | 2024 | Eramet 報告 |
| Prony Resources | ~X | 2024 | |
| (全國總計) | ~100-120 | 2024 | USGS |

**⚠️ 注意：**
- 面臨營運困難
- 政治不穩定
- 高品位但成本高
</anchor>
</global_anchors>

<aggregation_template>
**數據整合模板**

```python
mine_level_data = [
    # Indonesia
    {
        "mine_name": "Weda Bay",
        "country": "Indonesia",
        "company": "Eramet JV",
        "year": 2024,
        "value": X,  # kt Ni content
        "unit": "t_Ni_content",
        "source_id": "Eramet_AR",
        "confidence": 0.80,
        "notes": "Converted from ore sales"
    },
    {
        "mine_name": "IMIP Aggregate",
        "country": "Indonesia",
        "company": "Multiple",
        "year": 2024,
        "value": X,
        "unit": "t_Ni_content",
        "source_id": "Industry_estimate",
        "confidence": 0.60,
        "notes": "Park-level aggregate"
    },
    {
        "mine_name": "Nickel Industries",
        "country": "Indonesia",
        "company": "Nickel Industries",
        "year": 2024,
        "value": 18,
        "unit": "kt_Ni_content",
        "source_id": "NIC_AR",
        "confidence": 0.85,
        "notes": "NPI + Nickel metal"
    },
    {
        "mine_name": "PT Vale",
        "country": "Indonesia",
        "company": "Vale",
        "year": 2024,
        "value": 55,
        "unit": "kt_Ni_content",
        "source_id": "INCO_AR",
        "confidence": 0.90,
        "notes": "Matte production"
    },
    # Russia
    {
        "mine_name": "Norilsk",
        "country": "Russia",
        "company": "Norilsk Nickel",
        "year": 2024,
        "value": 190,
        "unit": "kt_Ni_content",
        "source_id": "GMKN_AR",
        "confidence": 0.85,
        "notes": "Primary nickel"
    },
    # ... more entries
]
```
</aggregation_template>

<mine_cr5_calculation>
**Mine CR5 計算範例**

```python
def calculate_mine_cr5(mine_data, global_production):
    """
    計算前 5 大礦區集中度

    Args:
        mine_data: List of mine production records
        global_production: 全球總產量 (kt Ni)

    Returns:
        dict: Mine CR5 指標
    """
    # 按產量排序
    sorted_mines = sorted(
        mine_data,
        key=lambda x: x["value"],
        reverse=True
    )

    # 取前 5 大
    top_5 = sorted_mines[:5]
    top_5_total = sum(m["value"] for m in top_5)

    # 計算份額
    mine_cr5 = top_5_total / global_production

    return {
        "mine_cr5": mine_cr5,
        "top_5_mines": [
            {
                "name": m["mine_name"],
                "value": m["value"],
                "share": m["value"] / global_production,
                "confidence": m["confidence"]
            }
            for m in top_5
        ],
        "data_quality_note": "Mine-level data has higher uncertainty than country-level"
    }

# 範例計算
# global_production = 3700  # kt Ni (2024 estimate)
# mine_cr5_result = calculate_mine_cr5(mine_level_data, global_production)
```
</mine_cr5_calculation>

<limitations>
**數據限制**

1. **覆蓋率不完整**：無法覆蓋所有礦區
2. **口徑差異**：各公司報告標準不一
3. **時間差異**：財年與日曆年混合
4. **估計成分高**：部分數據為產業估計

**建議使用方式：**
- 作為「錨點」驗證國家級數據
- 計算 Mine_CR5 時標註高不確定性
- 優先使用審計數字
</limitations>
