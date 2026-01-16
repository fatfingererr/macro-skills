# Workflow: 數據擷取與標準化

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/unit-conversion.md
3. references/mine-level-anchors.md
</required_reading>

<process>
## Step 1: 確認數據需求

根據分析目標確認需要擷取的數據：

```yaml
ingest_config:
  data_level: "free_nolimit"  # free_nolimit | free_limit | paid_low | paid_high

  target_data:
    - type: "country_production"
      years: [2015, 2024]
      granularity: "annual"

    - type: "mine_level"  # 選填，用於 mine_CR5
      countries: ["Indonesia"]

    - type: "policy_info"  # 選填，用於情境分析
      topics: ["RKAB", "export_rules"]
```

## Step 2: Tier 0 數據擷取（必須）

**2.1 USGS Mineral Commodity Summaries**

```python
# scripts/ingest_sources.py

def ingest_usgs_nickel():
    """
    擷取 USGS Nickel MCS 數據
    """
    config = {
        "url": "https://www.usgs.gov/centers/national-minerals-information-center/nickel-statistics-and-information",
        "pdf_pattern": "mcs*nickel*.pdf",
        "tables_to_extract": [
            "World Mine Production",
            "U.S. Salient Statistics"
        ]
    }

    # 方法 1: 直接下載 PDF 並解析
    pdf_data = fetch_usgs_pdf(config["url"])
    tables = extract_tables_from_pdf(pdf_data, method="camelot")

    # 方法 2: 使用 USGS Data 頁面（若有結構化數據）
    # https://www.usgs.gov/media/files/nickel-data-through-2023

    # 標準化輸出
    return normalize_usgs_data(tables)

def normalize_usgs_data(tables):
    """
    將 USGS 數據轉換為標準 schema
    """
    records = []
    for row in tables["World Mine Production"]:
        records.append({
            "year": row["Year"],
            "country": row["Country"],
            "supply_type": "mined",
            "product_group": "all",
            "value": float(row["Production"]) * 1000,  # kt → t
            "unit": "t_Ni_content",
            "source_id": "USGS",
            "confidence": 0.95
        })
    return records
```

**2.2 INSG 數據**

```python
def ingest_insg():
    """
    擷取 INSG 數據（需要處理 PDF 或網頁）
    """
    sources = [
        {
            "name": "INSG Market Commentary",
            "url": "https://insg.org/index.php/about-nickel/market-commentary/",
            "type": "webpage"
        },
        {
            "name": "INSG World Nickel Factbook",
            "url": "https://insg.org/index.php/publications/",
            "type": "pdf"
        }
    ]

    # INSG 數據通常需要手動解析或 OCR
    # 主要提取：
    # - Global nickel production (tonnes)
    # - Usage/consumption
    # - Supply-demand balance

    return normalize_insg_data(extracted_data)
```

## Step 3: Tier 1 數據擷取（建議）

**3.1 公司報告擷取**

```python
def ingest_company_reports():
    """
    擷取上市公司的產量報告
    """
    companies = [
        {
            "name": "Nickel Industries",
            "ticker": "NIC.AX",
            "report_type": "annual_report",
            "metrics": ["NPI_production", "nickel_metal_production"],
            "url_pattern": "https://nickelindustries.com/investors/"
        },
        {
            "name": "PT Vale Indonesia",
            "ticker": "INCO.JK",
            "report_type": "quarterly_report",
            "metrics": ["matte_production"],
            "url_pattern": "https://www.vale.com/indonesia"
        },
        {
            "name": "Eramet (Weda Bay)",
            "ticker": "ERA.PA",
            "report_type": "activity_report",
            "metrics": ["ore_sold_wet_tonnes"],
            "url_pattern": "https://www.eramet.com/en/investors"
        }
    ]

    results = []
    for company in companies:
        data = scrape_company_report(company)
        normalized = normalize_company_data(data, company)
        results.extend(normalized)

    return results
```

**3.2 產量錨點驗證**

| 礦區/公司 | 2024 產量 | 口徑 | 來源 |
|-----------|-----------|------|------|
| Weda Bay | ~X Mt | ore wet tonnes | Eramet 報告 |
| IMIP (Morowali) | ~X kt | NPI capacity | Industry reports |
| PT Vale | ~X kt | matte | 公司財報 |
| Nickel Industries | ~X kt | nickel metal | 年報 |

## Step 4: Tier 2 數據（選填）

若 data_level 為 paid_low 或 paid_high：

```python
def ingest_sp_global():
    """
    S&P Global Market Intelligence 數據
    需要訂閱或 API access
    """
    # S&P 數據點：
    # - Indonesia 2024: 2.28 Mt (nickel content)
    # - Indonesia share: 60.2%
    # - Global production breakdown by country

    # 若無 API，可從研報引用
    sp_anchors = {
        "indonesia_prod_2024": 2280000,  # tonnes Ni content
        "indonesia_share_2024": 0.602,
        "source": "S&P Global Market Intelligence",
        "confidence": 0.90
    }

    return sp_anchors
```

## Step 5: 數據標準化與合併

```python
def normalize_and_merge(tier0, tier1, tier2=None):
    """
    合併所有來源數據並標準化
    """
    all_records = []

    # Tier 0: 主幹數據
    all_records.extend(tier0)

    # Tier 1: 補充數據（標記較低 confidence）
    for record in tier1:
        record["confidence"] = min(record.get("confidence", 0.8), 0.85)
        all_records.append(record)

    # Tier 2: 驗證錨點
    if tier2:
        # 用 Tier 2 校正 Tier 0/1 數據
        all_records = calibrate_with_anchors(all_records, tier2)

    # 轉換為 DataFrame
    df = pd.DataFrame(all_records)

    # 強制 schema 驗證
    validate_schema(df)

    return df

def validate_schema(df):
    """
    驗證數據符合標準 schema
    """
    required_columns = [
        "year", "country", "supply_type", "product_group",
        "value", "unit", "source_id", "confidence"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # 驗證 unit 值
    valid_units = ["t_Ni_content", "t_ore_wet", "t_NPI_product", "t_matte", "t_MHP"]
    invalid_units = df[~df.unit.isin(valid_units)].unit.unique()
    if len(invalid_units) > 0:
        raise ValueError(f"Invalid unit values: {invalid_units}")

    return True
```

## Step 6: 輸出標準化數據集

**輸出格式：**

```python
# Parquet（推薦，保留 schema）
df.to_parquet("data/nickel/curated/nickel_supply.parquet")

# JSON（交換用）
df.to_json("data/nickel/curated/nickel_supply.json", orient="records")

# CSV（備用）
df.to_csv("data/nickel/curated/nickel_supply.csv", index=False)
```

**輸出目錄結構：**

```
data/nickel/
├── raw/                          # 原始下載檔案
│   ├── usgs/
│   │   └── mcs-2025-nickel.pdf
│   ├── insg/
│   │   └── factbook-2024.pdf
│   └── companies/
│       └── nickel-industries-ar-2024.pdf
├── intermediate/                 # 中間處理結果
│   ├── usgs_extracted.json
│   └── ingest_status.json
└── curated/                      # 標準化數據集
    ├── nickel_supply.parquet
    ├── nickel_supply.json
    └── metadata.json
```

**Metadata 範例：**

```json
{
  "created_at": "2026-01-16T12:00:00Z",
  "data_level": "free_nolimit",
  "sources_used": [
    {"name": "USGS MCS 2025", "tier": 0, "records": 150},
    {"name": "INSG Factbook 2024", "tier": 0, "records": 50},
    {"name": "Company Reports", "tier": 1, "records": 25}
  ],
  "coverage": {
    "years": [2015, 2024],
    "countries": 20,
    "supply_types": ["mined", "refined"]
  },
  "quality_metrics": {
    "avg_confidence": 0.88,
    "records_with_warnings": 5
  }
}
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] Tier 0 數據已擷取（USGS + INSG）
- [ ] Tier 1 數據已擷取（若需要 mine-level）
- [ ] 所有數據已標準化為統一 schema
- [ ] schema 驗證通過
- [ ] 輸出 parquet/json 數據集
- [ ] 生成 metadata.json
- [ ] ingest_status 報告已產生
</success_criteria>
