# Workflow: Ingest（數據擷取與標準化）

<required_reading>
**Read these reference files NOW:**
1. references/data-sources.md
2. references/unit-conversion.md
</required_reading>

<process>
## Step 1: Determine Data Sources

根據 `data_level` 決定要擷取的數據源：

```python
def get_data_sources(data_level, sources_config):
    """
    根據數據等級決定來源
    """

    source_tiers = {
        "free_nolimit": {
            "usgs": True,
            "iea_ev_outlook": True,
            "australia_req": True,
            "abs_exports": True,
            "etf_holdings": True,
            "fastmarkets": False,  # 只有方法學
            "smm": False           # 只有方法學
        },
        "free_limit": {
            "usgs": True,
            "iea_ev_outlook": True,
            "australia_req": True,
            "abs_exports": True,
            "etf_holdings": True,
            "fastmarkets": "methodology_only",
            "smm": "methodology_only"
        },
        "paid_low": {
            "usgs": True,
            "iea_ev_outlook": True,
            "australia_req": True,
            "abs_exports": True,
            "etf_holdings": True,
            "fastmarkets": True,
            "smm": True
        },
        "paid_high": {
            "usgs": True,
            "iea_ev_outlook": True,
            "australia_req": True,
            "abs_exports": True,
            "etf_holdings": True,
            "fastmarkets": True,
            "smm": True,
            "benchmark": True,
            "bnef": True
        }
    }

    # 取得預設來源
    defaults = source_tiers.get(data_level, source_tiers["free_nolimit"])

    # 合併用戶配置
    if sources_config:
        for source, enabled in sources_config.items():
            defaults[source] = enabled

    return defaults
```

## Step 2: Ingest USGS Data

```python
def ingest_usgs_lithium():
    """
    從 USGS 擷取鋰統計數據

    來源：
    - https://www.usgs.gov/centers/national-minerals-information-center/lithium-statistics-and-information
    - https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lithium.pdf
    """

    import requests
    from bs4 import BeautifulSoup

    # 主頁面
    url = "https://www.usgs.gov/centers/national-minerals-information-center/lithium-statistics-and-information"

    # 抓取頁面
    response = fetch_with_retry(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # 找到數據表格或 PDF 連結
    data_links = extract_data_links(soup)

    # 下載並解析 MCS（Mineral Commodity Summaries）
    mcs_data = parse_mcs_lithium(data_links.get("mcs"))

    # 標準化
    standardized = {
        "source_id": "USGS",
        "asof_date": date.today().isoformat(),
        "data": {
            "world_production": mcs_data["world_production"],
            "by_country": mcs_data["by_country"],
            "reserves": mcs_data["reserves"],
            "consumption": mcs_data.get("consumption")
        },
        "unit": "kt_LCE",
        "confidence": 0.95,
        "update_frequency": "annual"
    }

    return standardized
```

## Step 3: Ingest IEA Data

```python
def ingest_iea_ev_outlook():
    """
    從 IEA 擷取 EV/電池需求數據

    來源：
    - https://www.iea.org/reports/global-ev-outlook-2024
    - https://www.iea.org/data-and-statistics/data-product/global-ev-data-explorer
    """

    # 嘗試 API（如有）
    api_data = try_iea_api()

    if not api_data:
        # 從報告頁面抓取關鍵數字
        url = "https://www.iea.org/reports/global-ev-outlook-2024"
        report_data = scrape_iea_report(url)

    # 提取關鍵指標
    extracted = {
        "ev_sales_by_year": report_data.get("ev_sales"),
        "battery_demand_gwh": report_data.get("battery_demand"),
        "lithium_demand": report_data.get("lithium_demand"),  # 如有
        "projections": report_data.get("projections")
    }

    # 標準化
    standardized = {
        "source_id": "IEA",
        "asof_date": date.today().isoformat(),
        "data": extracted,
        "unit": "mixed",  # 需在欄位級別標註
        "confidence": 0.90,
        "update_frequency": "annual"
    }

    return standardized
```

## Step 4: Ingest Australia Data

### 4.1 Resources & Energy Quarterly

```python
def ingest_australia_req():
    """
    從澳洲政府擷取 REQ 數據

    來源：
    - https://www.industry.gov.au/publications/resources-and-energy-quarterly
    """

    url = "https://www.industry.gov.au/publications/resources-and-energy-quarterly"

    # 找到最新季度報告
    latest_report = find_latest_req_report(url)

    # 下載 PDF 或 Excel
    report_file = download_report(latest_report["url"])

    # 解析鋰相關章節
    lithium_section = extract_lithium_section(report_file)

    # 標準化
    standardized = {
        "source_id": "AU_REQ",
        "asof_date": latest_report["quarter"],
        "data": {
            "production": lithium_section.get("production"),
            "exports": lithium_section.get("exports"),
            "outlook": lithium_section.get("outlook"),
            "prices": lithium_section.get("prices")
        },
        "unit": "mixed",
        "confidence": 0.90,
        "update_frequency": "quarterly"
    }

    return standardized
```

### 4.2 ABS Exports

```python
def ingest_abs_exports():
    """
    從 ABS 擷取鋰出口數據

    來源：
    - https://www.abs.gov.au/
    - 國際貿易統計
    """

    # ABS 通常需要使用 TableBuilder 或特定 API
    # 這裡提供概念性代碼

    abs_data = query_abs_trade_data(
        commodity="lithium",
        measure=["value", "quantity"],
        frequency="monthly"
    )

    # 標準化
    standardized = {
        "source_id": "ABS",
        "asof_date": abs_data["latest_period"],
        "data": {
            "export_value_aud": abs_data["value"],
            "export_quantity": abs_data.get("quantity")
        },
        "unit": "AUD/tonnes",
        "confidence": 0.90,
        "update_frequency": "monthly"
    }

    return standardized
```

## Step 5: Ingest Price Data

```python
def ingest_lithium_prices(data_level, chem_focus):
    """
    根據數據等級擷取價格數據
    """

    prices = {}

    if data_level in ["paid_low", "paid_high"]:
        # 付費來源
        if chem_focus in ["carbonate", "both"]:
            prices["carbonate"] = ingest_fastmarkets_carbonate()
            prices["carbonate_smm"] = ingest_smm_carbonate()

        if chem_focus in ["hydroxide", "both"]:
            prices["hydroxide"] = ingest_fastmarkets_hydroxide()

    else:
        # 免費來源（proxy）
        prices["proxy"] = ingest_cme_lithium_futures()

        if not prices["proxy"]["data"]:
            # 使用股票籃子 proxy
            prices["stock_proxy"] = build_lithium_stock_proxy()

    return {
        "source_id": "mixed",
        "data": prices,
        "data_level": data_level,
        "confidence": 0.85 if data_level.startswith("paid") else 0.70
    }
```

## Step 6: Ingest ETF Holdings

```python
def ingest_etf_holdings(ticker="LIT"):
    """
    從 Global X 擷取 ETF 持股

    來源：
    - https://www.globalxetfs.com/funds/lit/
    """

    url = f"https://www.globalxetfs.com/funds/{ticker.lower()}/"

    # 嘗試從頁面抓取
    holdings = scrape_globalx_holdings(url)

    # 如果失敗，嘗試 factsheet PDF
    if not holdings:
        factsheet_url = find_factsheet_url(url)
        holdings = parse_factsheet_pdf(factsheet_url)

    # 標準化
    standardized = {
        "source_id": "GlobalX",
        "asof_date": holdings.get("asof_date", "unknown"),
        "data": {
            "holdings": holdings["list"],
            "total_assets": holdings.get("total_assets"),
            "num_holdings": len(holdings["list"])
        },
        "confidence": 0.90,
        "update_frequency": "daily"
    }

    return standardized
```

## Step 7: Normalize and Store

```python
def normalize_and_store(all_data):
    """
    標準化所有數據並存儲
    """

    import duckdb

    # 建立統一 schema
    schema = """
    CREATE TABLE IF NOT EXISTS lithium_data (
        date DATE,
        metric_type VARCHAR,
        metric_name VARCHAR,
        value DOUBLE,
        unit VARCHAR,
        region VARCHAR,
        source_id VARCHAR,
        data_level VARCHAR,
        confidence DOUBLE,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    conn = duckdb.connect("data/lithium_lake.duckdb")
    conn.execute(schema)

    # 轉換並插入各數據源
    for source_name, source_data in all_data.items():
        normalized_rows = normalize_source(source_name, source_data)
        insert_rows(conn, normalized_rows)

    conn.close()

    return {
        "status": "success",
        "records_inserted": count_inserted,
        "sources_processed": list(all_data.keys())
    }
```

## Step 8: Validate Data

```python
def validate_ingested_data(all_data):
    """
    驗證擷取的數據
    """

    validations = []

    for source_name, source_data in all_data.items():
        validation = {
            "source": source_name,
            "has_data": bool(source_data.get("data")),
            "asof_date": source_data.get("asof_date"),
            "confidence": source_data.get("confidence"),
            "issues": []
        }

        # 檢查數據新鮮度
        if is_stale(source_data.get("asof_date"), source_data.get("update_frequency")):
            validation["issues"].append("數據可能過期")

        # 檢查必要欄位
        if not source_data.get("unit"):
            validation["issues"].append("缺少單位標註")

        validations.append(validation)

    return {
        "validations": validations,
        "overall_status": "pass" if all(not v["issues"] for v in validations) else "warning"
    }
```
</process>

<output_template>
**擷取報告：**

```markdown
# 鋰數據擷取報告

## 擷取日期: [YYYY-MM-DD]
## 數據等級: [free_nolimit/free_limit/paid_low/paid_high]

---
## 擷取結果摘要

| 數據源 | 狀態 | 記錄數 | 更新日期 | 置信度 |
|--------|------|--------|----------|--------|
| USGS | ✅ 成功 | [n] | [date] | 0.95 |
| IEA | ✅ 成功 | [n] | [date] | 0.90 |
| Australia REQ | ✅ 成功 | [n] | [date] | 0.90 |
| ABS Exports | ✅ 成功 | [n] | [date] | 0.90 |
| ETF Holdings | ✅ 成功 | [n] | [date] | 0.90 |
| Price Data | ⚠️ Proxy | [n] | [date] | 0.70 |

---
## 數據驗證

| 檢查項目 | 結果 |
|----------|------|
| 數據新鮮度 | [pass/warning] |
| 單位一致性 | [pass/warning] |
| 必要欄位 | [pass/warning] |

---
## 存儲位置

- 本地數據湖: `data/lithium_lake.duckdb`
- 原始檔案: `data/raw/[source]/`

---
## 下次更新建議

| 數據源 | 建議更新頻率 | 下次更新 |
|--------|--------------|----------|
| USGS | 年度 | [date] |
| IEA | 年度 | [date] |
| Australia REQ | 季度 | [date] |
| ABS | 月度 | [date] |
| ETF Holdings | 週度 | [date] |
| Price | 日度/週度 | [date] |
```
</output_template>

<success_criteria>
此工作流程完成時：
- [ ] 根據 data_level 選擇正確的數據源
- [ ] 所有已啟用的數據源都已嘗試擷取
- [ ] 數據已標準化（統一 schema）
- [ ] 數據已存儲到本地數據湖
- [ ] 驗證報告已生成
- [ ] 失敗的來源有明確錯誤訊息
</success_criteria>
