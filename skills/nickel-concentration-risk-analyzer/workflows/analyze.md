# Workflow: 供給集中度分析

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/concentration-metrics.md
3. references/indonesia-supply-structure.md
</required_reading>

<process>
## Step 1: 確認分析參數

收集或確認以下參數：

```yaml
asof_date: "2026-01-16"  # 分析基準日
horizon:
  history_start_year: 2015  # 歷史起始年
  history_end_year: 2024    # 歷史結束年（通常為最新可用年）
scope:
  supply_type: "mined"      # 必填：mined | refined
  unit: "t_Ni_content"      # 預設為鎳金屬含量
countries:
  - Indonesia
  - Philippines
  - Russia
  - Canada
  - Australia
  - New Caledonia
  - Other
data_level: "free_nolimit"  # 數據等級
```

**若用戶未提供參數**，使用上述預設值並告知。

## Step 2: 數據擷取

依 data_level 決定數據來源優先序：

**Tier 0（必須）- Baseline：**
- USGS Mineral Commodity Summaries (Nickel)
  - URL: https://www.usgs.gov/centers/national-minerals-information-center/nickel-statistics-and-information
  - 抓取：全球 + 主要國家 mine production (nickel content)
- INSG World Nickel Statistics
  - 抓取：供需平衡、產量增長率

**Tier 1（建議）- Mine-level 錨點：**
- 若需要 mine_CR5，需抓取公司報告
- 見 references/mine-level-anchors.md

**Tier 2（選填）- 精度驗證：**
- 若 data_level 為 paid_low 或 paid_high，可用 S&P Global 數據交叉驗證

## Step 3: 數據標準化

將所有數據轉換為統一 schema：

```python
schema = {
    "year": int,
    "country": str,
    "supply_type": str,  # "mined" | "refined"
    "product_group": str,  # "all" | "NPI" | "matte" | "class1" ...
    "value": float,
    "unit": str,  # "t_Ni_content" | "t_ore_wet" | "t_NPI_product"
    "source_id": str,  # "USGS" | "INSG" | "S&P" | "Company"
    "confidence": float  # 0-1
}
```

**關鍵檢查：**
- 若來源數據單位為 ore wet tonnes，必須：
  1. 標記 unit = "t_ore_wet"
  2. 若需轉換為 nickel content，需提供 assay_grade 假設
  3. 轉換後的數據標記 confidence 降低

## Step 4: 計算集中度指標

使用 scripts/compute_concentration.py 或以下邏輯：

```python
def compute_concentration(df, year):
    # Filter to mined nickel content
    data = df[(df.supply_type == "mined") & (df.year == year)]

    # Country share
    global_prod = data.value.sum()
    share = data.groupby("country").value.sum() / global_prod

    # CR_n (top N concentration)
    sorted_share = share.sort_values(ascending=False)
    cr1 = sorted_share.iloc[0]
    cr3 = sorted_share.head(3).sum()
    cr5 = sorted_share.head(5).sum()

    # HHI (Herfindahl-Hirschman Index)
    hhi = (share * 10000).pow(2).sum() / 10000  # Scale to 0-10000

    return {
        "indonesia_share": share.get("Indonesia", 0),
        "cr1": cr1,
        "cr3": cr3,
        "cr5": cr5,
        "hhi": hhi,
        "market_structure": classify_hhi(hhi)
    }

def classify_hhi(hhi):
    if hhi < 1500:
        return "低集中 (Unconcentrated)"
    elif hhi < 2500:
        return "中等集中 (Moderately Concentrated)"
    else:
        return "高集中 (Highly Concentrated)"
```

## Step 5: 生成時序趨勢

計算歷史年份的集中度變化：

| 年份 | Indonesia Share | CR5 | HHI | 判讀 |
|------|-----------------|-----|-----|------|
| 2015 | XX% | XX% | XXXX | ... |
| ... | ... | ... | ... | ... |
| 2024 | ~60% | XX% | XXXX | 高集中 |

**關鍵觀察點：**
- 印尼市佔從 2020 的 ~31.5% 增至 2024 的 ~60.2%（S&P 口徑）
- 這個增長主要來自 NPI 產能擴張

## Step 6: 生成視覺化圖表（可選）

使用 scripts/visualize_concentration.py 生成視覺化圖表：

```bash
python scripts/visualize_concentration.py
```

**生成的圖表**：
1. `nickel_indonesia_share_trend_YYYYMMDD.png` - 印尼市佔率與HHI時序趨勢
2. `nickel_country_share_pie_YYYYMMDD.png` - 2024年國家份額餅圖
3. `nickel_concentration_metrics_YYYYMMDD.png` - 集中度指標演進（CR1, CR3, CR5）
4. `nickel_production_volume_YYYYMMDD.png` - 印尼vs全球產量對比
5. `nickel_risk_matrix_YYYYMMDD.png` - 集中度風險矩陣

圖表自動保存到項目根目錄的 `output/` 資料夾，檔名包含當天日期。

## Step 7: 輸出結果

使用 templates/output-json.md 和 templates/output-markdown.md 生成輸出。

**JSON 輸出結構：**

```json
{
  "commodity": "nickel",
  "asof_date": "2026-01-16",
  "scope": {
    "supply_type": "mined",
    "unit": "t_Ni_content"
  },
  "concentration": {
    "indonesia_share_2024": 0.602,
    "cr1_2024": 0.602,
    "cr3_2024": 0.XX,
    "cr5_2024": 0.XX,
    "hhi_2024": XXXX,
    "market_structure": "高集中"
  },
  "time_series": [...],
  "data_sources_used": [
    "USGS MCS (Nickel)",
    "INSG World Nickel Statistics"
  ],
  "unit_warnings": []
}
```

**Markdown 報告結構：**

```markdown
## 全球鎳供給集中度分析

**分析日期**: 2026-01-16
**數據口徑**: Mined nickel content (鎳金屬含量)

### 關鍵發現

- **Indonesia share (2024)**: ~60% (S&P Global 口徑為 60.2%)
- **市場結構**: 高集中 (HHI > 2500)
- **趨勢**: 印尼市佔從 2020 的 31.5% 升至 2024 的 60.2%

### 集中度指標

| 指標 | 2024 值 | 解讀 |
|------|---------|------|
| CR1 (Indonesia) | 60.2% | 單一國家主導 |
| CR5 | XX% | 前五國控制 XX% |
| HHI | XXXX | 高集中市場 |

### 數據來源

- USGS Mineral Commodity Summaries 2025
- INSG World Nickel Statistics
- S&P Global Market Intelligence (驗證用)

### 口徑說明

本分析使用 **mined nickel content**（礦場產量的鎳金屬含量），
非 ore wet tonnes（礦石濕噸）或 refined production（精煉產量）。
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 分析參數已確認或使用預設值
- [ ] 數據來源明確標註（source_id）
- [ ] 單位一致為 t_Ni_content
- [ ] 計算 share, CR_n, HHI 指標
- [ ] 輸出 JSON + Markdown 格式
- [ ] 包含時序趨勢（至少近 5 年）
- [ ] 標註數據口徑與來源
</success_criteria>
