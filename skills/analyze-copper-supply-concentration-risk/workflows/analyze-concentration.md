# Workflow: 銅供應集中度分析

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/concentration-metrics.md
</required_reading>

<process>
## Step 1: 確認分析參數

收集或確認以下參數：

```yaml
start_year: 1970          # 分析起始年
end_year: 2023            # 分析結束年（最新可用年）
concentration_metric: "HHI"  # HHI | CR4 | CR8
top_n_producers: 12       # 計算集中度時納入的國家數
focus_countries:
  - Chile
  - Peru
  - Democratic Republic of Congo
  - China
  - United States
  - Russia
  - Australia
  - Mexico
  - Kazakhstan
  - Canada
```

**若用戶未提供參數**，使用上述預設值並告知。

## Step 2: 數據擷取

使用 OWID Minerals 作為主要來源，USGS 作為驗證：

**主要來源 - OWID Minerals：**
- URL: https://ourworldindata.org/minerals
- 抓取：Copper mine production by country（長序列，1900 年起）
- 單位：tonnes of copper content

**驗證來源 - USGS：**
- URL: https://www.usgs.gov/centers/national-minerals-information-center/copper-statistics-and-information
- 用於交叉驗證最新年度數據

執行數據擷取：
```bash
python scripts/fetch_owid.py --commodity=copper --start={start_year} --end={end_year}
```

## Step 3: 數據標準化

將所有數據轉換為統一 schema：

```python
schema = {
    "year": int,
    "country": str,
    "production": float,  # 公噸
    "unit": "t_Cu_content",
    "source_id": str,  # "OWID" | "USGS"
    "confidence": float  # 0-1
}
```

**關鍵處理：**
- 將 "World" 或 "Global" 單獨標記為 world_total
- 確保國家名稱標準化（如 "DRC" → "Democratic Republic of Congo"）
- 標記缺失值（不補值，標記為 NaN）

## Step 4: 計算集中度指標

使用 scripts/compute_concentration.py 或以下邏輯：

```python
def compute_shares(df, year):
    """計算各國市場份額"""
    year_data = df[df.year == year]
    world_prod = year_data[year_data.country == "World"].production.values[0]

    country_data = year_data[year_data.country != "World"]
    shares = country_data.copy()
    shares["share"] = shares.production / world_prod

    return shares.sort_values("share", ascending=False)

def compute_hhi(shares_df):
    """計算 Herfindahl-Hirschman Index"""
    # HHI = Σ (share_i × 100)²，範圍 0-10000
    return ((shares_df["share"] * 100) ** 2).sum()

def compute_cr_n(shares_df, n):
    """計算前 N 大國家集中度"""
    return shares_df.head(n)["share"].sum()

def classify_market(hhi):
    """根據 HHI 分類市場結構"""
    if hhi < 1500:
        return "低集中 (Unconcentrated)"
    elif hhi < 2500:
        return "中等集中 (Moderately Concentrated)"
    else:
        return "高集中 (Highly Concentrated)"
```

計算所有年份的指標：
```python
results = []
for year in range(start_year, end_year + 1):
    shares = compute_shares(df, year)
    results.append({
        "year": year,
        "hhi": compute_hhi(shares),
        "cr4": compute_cr_n(shares, 4),
        "cr8": compute_cr_n(shares, 8),
        "chile_share": shares[shares.country == "Chile"]["share"].values[0],
        "top_producer": shares.iloc[0].country,
        "top_producer_share": shares.iloc[0]["share"]
    })
```

## Step 5: 生成時序趨勢分析

分析集中度指標的時間演變：

| 年份 | HHI | CR4 | Chile Share | 市場結構 |
|------|-----|-----|-------------|----------|
| 1970 | XXXX | XX% | XX% | ... |
| ... | ... | ... | ... | ... |
| 2023 | XXXX | XX% | XX% | ... |

**關鍵觀察點：**
- HHI 是上升還是下降趨勢？
- 智利份額在哪些年份達到峰值？
- 是否有明顯的結構變化年份？

## Step 6: 生成國家份額排名

計算最新年度（end_year）的國家排名：

```python
latest_shares = compute_shares(df, end_year)
ranking = latest_shares.head(top_n_producers)[["country", "production", "share"]]
```

輸出格式：
| 排名 | 國家 | 產量 (Mt) | 份額 | 累積份額 |
|------|------|-----------|------|----------|
| 1 | Chile | X.XX | XX.X% | XX.X% |
| 2 | Peru | X.XX | XX.X% | XX.X% |
| ... | ... | ... | ... | ... |

## Step 7: 生成視覺化圖表（可選）

使用 scripts/visualize_analysis.py 生成：

```bash
python scripts/visualize_analysis.py --mode=concentration
```

**生成的圖表**：
1. `copper_hhi_trend_YYYYMMDD.png` - HHI 時序趨勢
2. `copper_country_share_YYYYMMDD.png` - 最新年度國家份額餅圖
3. `copper_cr_metrics_YYYYMMDD.png` - CR4/CR8 演進圖

## Step 8: 輸出結果

**JSON 輸出結構：**

```json
{
  "commodity": "copper",
  "analysis_type": "concentration",
  "period": {
    "start_year": 1970,
    "end_year": 2023
  },
  "concentration": {
    "metric": "HHI",
    "hhi_latest": 1820,
    "hhi_10y_ago": 1750,
    "trend_direction": "上升",
    "cr4_latest": 0.562,
    "cr8_latest": 0.734,
    "market_structure": "中等集中"
  },
  "top_producers": [
    {"country": "Chile", "share": 0.268, "production_mt": 5.26},
    {"country": "Peru", "share": 0.102, "production_mt": 2.00},
    {"country": "DRC", "share": 0.095, "production_mt": 1.86}
  ],
  "chile_analysis": {
    "share_latest": 0.268,
    "share_peak": 0.342,
    "peak_year": 2003,
    "share_percentile": 75
  },
  "data_sources": ["OWID Minerals", "USGS MCS"],
  "generated_at": "2026-01-24"
}
```

**Markdown 報告結構：**

```markdown
## 銅供應集中度分析 ({start_year}-{end_year})

### 執行摘要

全球銅供應呈現 [市場結構] 結構。HHI 指數為 {hhi_latest}，
較 10 年前 [上升/下降] {change}。前四大生產國控制 {cr4_latest:.1%} 的全球供應。

### 關鍵發現

| 指標 | {end_year} 年值 | 解讀 |
|------|-----------------|------|
| HHI | {hhi_latest:.0f} | {market_structure} |
| CR4 | {cr4_latest:.1%} | 前四國控制超過半數供應 |
| CR8 | {cr8_latest:.1%} | 前八國控制絕大多數供應 |
| 智利份額 | {chile_share:.1%} | [高於/低於]歷史中位數 |

### 國家份額排名

[國家份額表格]

### 時序趨勢

[HHI 趨勢描述]
[集中度變化分析]

### 數據來源

- OWID Minerals Explorer
- USGS Copper Statistics and Information

### 口徑說明

本分析使用 **mined copper content**（礦場產量的銅金屬含量），
非 ore tonnes（礦石噸數）或 refined production（精煉產量）。
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 分析參數已確認或使用預設值
- [ ] 數據來源明確標註（OWID/USGS）
- [ ] 計算 HHI, CR4, CR8 指標
- [ ] 生成國家份額排名表
- [ ] 包含時序趨勢分析（至少近 10 年）
- [ ] 輸出 JSON + Markdown 格式
- [ ] 標註數據口徑為 mined copper content
</success_criteria>
