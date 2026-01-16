# 失敗模式與緩解策略

<overview>
本文件列舉 nickel-concentration-risk-analyzer 可能遇到的
失敗模式、錯誤類型與對應的緩解策略。
</overview>

<failure_category name="data_ingestion">
**數據擷取失敗**

<failure name="pdf_parse_fail">
**PDF 解析失敗**

| 項目 | 說明 |
|------|------|
| 症狀 | camelot/tabula 無法正確提取表格 |
| 原因 | PDF 格式變更、掃描件、圖片式表格 |
| 頻率 | 中等 |

**緩解策略：**
```python
def robust_pdf_parse(pdf_path):
    """
    多重策略 PDF 解析
    """
    # 策略 1: camelot (stream)
    try:
        tables = camelot.read_pdf(pdf_path, flavor='stream')
        if len(tables) > 0:
            return tables
    except:
        pass

    # 策略 2: camelot (lattice)
    try:
        tables = camelot.read_pdf(pdf_path, flavor='lattice')
        if len(tables) > 0:
            return tables
    except:
        pass

    # 策略 3: tabula
    try:
        tables = tabula.read_pdf(pdf_path, pages='all')
        if len(tables) > 0:
            return tables
    except:
        pass

    # 策略 4: OCR fallback
    try:
        tables = ocr_extract(pdf_path)
        return tables
    except:
        pass

    # 全部失敗
    raise PDFParseError(f"All parse methods failed for {pdf_path}")
```
</failure>

<failure name="url_change">
**URL 變更/失效**

| 項目 | 說明 |
|------|------|
| 症狀 | 404 錯誤、重新導向 |
| 原因 | 網站改版、檔案更名 |
| 頻率 | 低（年度報告）至 中（月度更新）|

**緩解策略：**
```python
URL_ALTERNATIVES = {
    "usgs_nickel": [
        "https://www.usgs.gov/centers/national-minerals-information-center/nickel-statistics-and-information",
        "https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-nickel.pdf",
        "https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-nickel.pdf",  # fallback
    ],
    "insg_main": [
        "https://insg.org/",
        "https://insg.org/index.php/about-nickel/",
    ]
}

def fetch_with_fallback(source_key):
    for url in URL_ALTERNATIVES[source_key]:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
        except:
            continue
    raise DataFetchError(f"All URLs failed for {source_key}")
```
</failure>

<failure name="anti_scraping">
**反爬蟲阻擋**

| 項目 | 說明 |
|------|------|
| 症狀 | 403 Forbidden、CAPTCHA |
| 原因 | 網站反爬蟲機制 |
| 頻率 | 中等（付費來源） |

**緩解策略：**
見 `design-human-like-crawler.md` 指南：
- 隨機延遲
- User-Agent 輪換
- Selenium/Playwright fallback
</failure>
</failure_category>

<failure_category name="unit_errors">
**單位錯誤**

<failure name="ore_content_mix">
**礦石/含量混淆**

| 項目 | 說明 |
|------|------|
| 症狀 | 計算結果差異 50-100x |
| 原因 | 誤將 ore wet tonnes 當作 nickel content |
| 頻率 | **高**（最常見錯誤） |

**檢測方法：**
```python
def detect_unit_anomaly(value, unit, country, year):
    """
    檢測可能的單位錯誤
    """
    # 全球年產量約 3-4 Mt Ni content
    # 單一國家不應超過 3 Mt
    if unit == "t_Ni_content" and value > 3_000_000:
        return {
            "warning": "POSSIBLE_ORE_NOT_CONTENT",
            "message": f"Value {value:,} seems too high for nickel content",
            "suggestion": "Check if this is ore wet tonnes instead"
        }

    # Indonesia 2024 約 2.3 Mt，不應超過 3 Mt
    if country == "Indonesia" and unit == "t_Ni_content":
        if value > 3_000_000:
            return {
                "warning": "POSSIBLE_ORE_NOT_CONTENT",
                "message": "Indonesia Ni content should be ~2-2.5 Mt in 2024"
            }

    return {"status": "OK"}
```

**緩解策略：**
- 強制在 schema 中標註 unit
- 執行 sanity check
- 異常值需人工確認
</failure>

<failure name="product_content_mix">
**產品噸/含量混淆**

| 項目 | 說明 |
|------|------|
| 症狀 | 計算結果差異 5-10x |
| 原因 | 誤將 NPI 產品噸當作 nickel content |
| 頻率 | 中等 |

**範例：**
```
❌ 錯誤：NPI production 100,000 t = 100,000 t Ni
✅ 正確：NPI production 100,000 t = ~12,000-15,000 t Ni (at 12-15%)
```
</failure>
</failure_category>

<failure_category name="calculation_errors">
**計算錯誤**

<failure name="share_calculation">
**份額計算錯誤**

| 項目 | 說明 |
|------|------|
| 症狀 | 份額總和 ≠ 100% |
| 原因 | 遺漏 "Other" 類別、重複計算 |
| 頻率 | 低 |

**驗證方法：**
```python
def validate_shares(shares_dict):
    total = sum(shares_dict.values())
    if abs(total - 1.0) > 0.01:  # 容許 1% 誤差
        return {
            "error": "SHARES_NOT_SUM_TO_ONE",
            "total": total,
            "suggestion": "Check for missing 'Other' category or double counting"
        }
    return {"status": "OK"}
```
</failure>

<failure name="hhi_overflow">
**HHI 計算溢出**

| 項目 | 說明 |
|------|------|
| 症狀 | HHI > 10000 |
| 原因 | 份額未正規化為 0-1 |
| 頻率 | 低 |

**正確計算：**
```python
def calculate_hhi_safe(shares):
    # 確保份額在 0-1 範圍
    shares = np.clip(shares, 0, 1)

    # 正規化使總和為 1
    if shares.sum() > 0:
        shares = shares / shares.sum()

    # HHI = Σ(share² × 10000)
    hhi = (shares ** 2).sum() * 10000

    # 驗證範圍
    assert 0 <= hhi <= 10000, f"HHI out of range: {hhi}"

    return hhi
```
</failure>
</failure_category>

<failure_category name="scenario_errors">
**情境模擬錯誤**

<failure name="execution_prob_range">
**執行機率超出範圍**

| 項目 | 說明 |
|------|------|
| 症狀 | 負數或 >1 的機率 |
| 原因 | 用戶輸入錯誤 |
| 頻率 | 低 |

**驗證方法：**
```python
def validate_scenario(scenario):
    errors = []

    if not 0 <= scenario.execution_prob <= 1:
        errors.append({
            "field": "execution_prob",
            "value": scenario.execution_prob,
            "error": "Must be between 0 and 1"
        })

    if scenario.cut_value < 0:
        errors.append({
            "field": "cut_value",
            "value": scenario.cut_value,
            "error": "Cut value cannot be negative"
        })

    return errors
```
</failure>

<failure name="baseline_mismatch">
**Baseline 口徑不匹配**

| 項目 | 說明 |
|------|------|
| 症狀 | 衝擊百分比異常大或小 |
| 原因 | 情境減產量與 baseline 口徑不一致 |
| 頻率 | 中等 |

**緩解策略：**
```python
def check_baseline_scenario_alignment(baseline, scenario):
    warnings = []

    # 檢查 supply_type 是否一致
    if baseline.supply_type != scenario.implied_supply_type:
        warnings.append({
            "type": "supply_type_mismatch",
            "baseline": baseline.supply_type,
            "scenario": scenario.implied_supply_type
        })

    # 檢查 unit 是否一致
    if baseline.unit != scenario.cut_unit:
        warnings.append({
            "type": "unit_mismatch",
            "baseline": baseline.unit,
            "scenario": scenario.cut_unit,
            "impact": "Results may be off by orders of magnitude"
        })

    return warnings
```
</failure>
</failure_category>

<failure_category name="output_errors">
**輸出錯誤**

<failure name="json_serialization">
**JSON 序列化失敗**

| 項目 | 說明 |
|------|------|
| 症狀 | TypeError: Object not JSON serializable |
| 原因 | numpy/pandas 類型未轉換 |
| 頻率 | 低 |

**緩解策略：**
```python
import json
import numpy as np
import pandas as pd

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)

# 使用
json.dumps(result, cls=NumpyEncoder)
```
</failure>

<failure name="encoding_issues">
**編碼問題**

| 項目 | 說明 |
|------|------|
| 症狀 | UnicodeEncodeError |
| 原因 | 非 ASCII 字元（如中文公司名） |
| 頻率 | 低 |

**緩解策略：**
```python
# 確保 UTF-8 輸出
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```
</failure>
</failure_category>

<error_recovery>
**錯誤恢復策略**

```python
class NickelAnalysisError(Exception):
    """基礎錯誤類"""
    pass

class DataIngestionError(NickelAnalysisError):
    """數據擷取錯誤"""
    pass

class UnitError(NickelAnalysisError):
    """單位錯誤"""
    pass

class CalculationError(NickelAnalysisError):
    """計算錯誤"""
    pass

def run_analysis_with_recovery(config):
    """
    帶錯誤恢復的分析執行
    """
    result = {
        "status": "unknown",
        "data": None,
        "errors": [],
        "warnings": []
    }

    try:
        # Step 1: 數據擷取
        data = ingest_data(config)
    except DataIngestionError as e:
        result["errors"].append({"stage": "ingestion", "error": str(e)})
        result["status"] = "failed"
        return result

    try:
        # Step 2: 數據驗證
        validation_result = validate_data(data)
        result["warnings"].extend(validation_result["warnings"])
    except UnitError as e:
        result["errors"].append({"stage": "validation", "error": str(e)})
        result["status"] = "failed"
        return result

    try:
        # Step 3: 計算
        analysis = compute_analysis(data, config)
        result["data"] = analysis
        result["status"] = "success"
    except CalculationError as e:
        result["errors"].append({"stage": "calculation", "error": str(e)})
        result["status"] = "partial"  # 可能有部分結果

    return result
```
</error_recovery>

<monitoring>
**監控建議**

```python
# 關鍵指標監控
MONITORING_CHECKS = {
    "indonesia_share_range": {
        "metric": "indonesia_share",
        "min": 0.50,
        "max": 0.75,
        "alert": "Indonesia share outside expected range"
    },
    "global_production_range": {
        "metric": "global_production",
        "min": 3_000_000,
        "max": 5_000_000,
        "unit": "t_Ni_content",
        "alert": "Global production outside expected range"
    },
    "hhi_range": {
        "metric": "hhi",
        "min": 2500,
        "max": 6000,
        "alert": "HHI outside expected range for nickel market"
    }
}

def run_monitoring_checks(result):
    alerts = []
    for check_name, check_config in MONITORING_CHECKS.items():
        value = result.get(check_config["metric"])
        if value is not None:
            if value < check_config["min"] or value > check_config["max"]:
                alerts.append({
                    "check": check_name,
                    "value": value,
                    "expected_range": [check_config["min"], check_config["max"]],
                    "alert": check_config["alert"]
                })
    return alerts
```
</monitoring>
