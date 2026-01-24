# Workflow: 數據擷取與標準化

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
</required_reading>

<process>
## Step 1: 確認擷取參數

```yaml
commodity: "copper"
start_year: 1970
end_year: 2023
sources:
  - OWID   # 主要來源
  - USGS   # 驗證來源
output_dir: "data/"
cache_enabled: true
cache_ttl_days: 7
```

## Step 2: 擷取 OWID Minerals 數據

OWID 提供免費、長序列的礦產數據。

**數據源 URL**：
```
https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Copper%20mine%20production%20(USGS%20%26%20BGS)/Copper%20mine%20production%20(USGS%20%26%20BGS).csv
```

**擷取腳本**：

```python
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

OWID_COPPER_URL = "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Copper%20mine%20production%20(USGS%20%26%20BGS)/Copper%20mine%20production%20(USGS%20%26%20BGS).csv"

def fetch_owid_copper(start_year: int, end_year: int, cache_dir: Path = Path("data/cache")):
    """
    從 OWID 擷取銅產量數據

    Returns:
    --------
    pd.DataFrame with columns: year, country, production, unit, source_id
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"owid_copper_{start_year}_{end_year}.csv"

    # 檢查快取
    if cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age.days < 7:
            print(f"使用快取: {cache_file}")
            return pd.read_csv(cache_file)

    # 下載數據
    print(f"從 OWID 下載銅產量數據...")
    response = requests.get(OWID_COPPER_URL, timeout=30)
    response.raise_for_status()

    # 解析 CSV
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))

    # 標準化欄位名稱
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "Copper mine production (USGS & BGS)": "production"
    })

    # 過濾年份
    df = df[(df.year >= start_year) & (df.year <= end_year)]

    # 添加標準化欄位
    df["unit"] = "t_Cu_content"
    df["source_id"] = "OWID"
    df["confidence"] = 0.9

    # 保存快取
    df.to_csv(cache_file, index=False)
    print(f"數據已快取: {cache_file}")

    return df[["year", "country", "production", "unit", "source_id", "confidence"]]
```

## Step 3: 擷取 USGS 數據（驗證用）

USGS 提供官方統計數據，用於交叉驗證最新年度。

**數據源**：
- 頁面：https://www.usgs.gov/centers/national-minerals-information-center/copper-statistics-and-information
- 下載：Mineral Commodity Summaries（年度 PDF）

**注意**：USGS 數據通常需要手動下載 PDF 或使用他們的 Data Series。
對於自動化擷取，建議：

```python
def fetch_usgs_copper_summary(year: int):
    """
    從 USGS 擷取銅產量摘要（最新年度驗證用）

    注意：USGS 數據格式較複雜，這裡提供簡化版本
    實際使用可能需要解析 PDF 或使用 API
    """
    # USGS Data Series 提供歷史數據
    # https://pubs.usgs.gov/ds/140/
    # https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities

    # 簡化版：使用預設值作為最新年度錨點
    usgs_latest = {
        2023: {
            "World": 22000000,
            "Chile": 5260000,
            "Peru": 2000000,
            "DRC": 1860000,
            "China": 1700000,
            "USA": 1100000
        }
    }

    return usgs_latest.get(year, {})
```

## Step 4: 數據標準化

將所有來源數據轉換為統一 schema：

```python
def normalize_production_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    標準化產量數據

    統一 Schema:
    - year: int
    - country: str (標準化國家名)
    - production: float (公噸)
    - unit: str ("t_Cu_content")
    - source_id: str ("OWID" | "USGS")
    - confidence: float (0-1)
    """
    # 國家名稱標準化映射
    country_mapping = {
        "Democratic Republic of the Congo": "Democratic Republic of Congo",
        "DRC": "Democratic Republic of Congo",
        "Congo, Dem. Rep.": "Democratic Republic of Congo",
        "United States of America": "United States",
        "USA": "United States",
        "US": "United States",
        "Russian Federation": "Russia",
        "USSR": "Russia",  # 歷史數據
    }

    df = df.copy()
    df["country"] = df["country"].replace(country_mapping)

    # 確保數值類型
    df["year"] = df["year"].astype(int)
    df["production"] = pd.to_numeric(df["production"], errors="coerce")

    # 過濾無效數據
    df = df.dropna(subset=["production"])
    df = df[df["production"] > 0]

    return df
```

## Step 5: 數據驗證

```python
def validate_data(df: pd.DataFrame, end_year: int) -> dict:
    """
    驗證數據完整性與一致性

    Returns:
    --------
    dict with validation results
    """
    results = {
        "total_records": len(df),
        "year_range": f"{df.year.min()}-{df.year.max()}",
        "countries": df.country.nunique(),
        "has_world_total": "World" in df.country.values,
        "latest_year_records": len(df[df.year == end_year]),
        "issues": []
    }

    # 檢查是否有世界總量
    if not results["has_world_total"]:
        results["issues"].append("缺少 World 總量數據")

    # 檢查最新年度是否有足夠國家
    if results["latest_year_records"] < 10:
        results["issues"].append(f"最新年度（{end_year}）記錄過少")

    # 檢查是否有重大缺值
    for year in range(end_year - 5, end_year + 1):
        year_data = df[df.year == year]
        if len(year_data) < 5:
            results["issues"].append(f"{year} 年數據不完整")

    results["is_valid"] = len(results["issues"]) == 0

    return results
```

## Step 6: 交叉驗證（OWID vs USGS）

```python
def cross_validate(owid_df: pd.DataFrame, usgs_data: dict, year: int) -> dict:
    """
    交叉驗證 OWID 與 USGS 數據

    Returns:
    --------
    dict with comparison results
    """
    owid_year = owid_df[owid_df.year == year]

    comparisons = []
    for country, usgs_value in usgs_data.items():
        owid_value = owid_year[owid_year.country == country]["production"].values
        if len(owid_value) > 0:
            owid_value = owid_value[0]
            diff_pct = abs(owid_value - usgs_value) / usgs_value
            comparisons.append({
                "country": country,
                "owid": owid_value,
                "usgs": usgs_value,
                "diff_pct": diff_pct,
                "is_aligned": diff_pct < 0.05  # 5% 容差
            })

    return {
        "year": year,
        "comparisons": comparisons,
        "all_aligned": all(c["is_aligned"] for c in comparisons)
    }
```

## Step 7: 保存標準化數據

```python
def save_normalized_data(df: pd.DataFrame, output_dir: Path = Path("data")):
    """
    保存標準化後的數據
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存完整數據
    output_file = output_dir / f"copper_production_normalized.csv"
    df.to_csv(output_file, index=False)
    print(f"標準化數據已保存: {output_file}")

    # 保存元數據
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "records": len(df),
        "year_range": f"{df.year.min()}-{df.year.max()}",
        "countries": df.country.nunique(),
        "sources": df.source_id.unique().tolist()
    }

    import json
    meta_file = output_dir / "copper_production_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return output_file
```

## Step 8: 完整擷取流程

```python
def run_ingestion_pipeline(
    start_year: int = 1970,
    end_year: int = 2023,
    output_dir: Path = Path("data")
):
    """
    執行完整數據擷取流程
    """
    print("=" * 50)
    print("銅產量數據擷取流程")
    print("=" * 50)

    # Step 1: 擷取 OWID 數據
    print("\n[1/5] 擷取 OWID 數據...")
    owid_df = fetch_owid_copper(start_year, end_year)
    print(f"  - 擷取 {len(owid_df)} 筆記錄")

    # Step 2: 標準化
    print("\n[2/5] 標準化數據...")
    normalized_df = normalize_production_data(owid_df)
    print(f"  - 標準化後 {len(normalized_df)} 筆記錄")

    # Step 3: 驗證
    print("\n[3/5] 驗證數據...")
    validation = validate_data(normalized_df, end_year)
    print(f"  - 驗證結果: {'通過' if validation['is_valid'] else '有問題'}")
    if validation["issues"]:
        for issue in validation["issues"]:
            print(f"    ⚠️ {issue}")

    # Step 4: 交叉驗證（可選）
    print("\n[4/5] 交叉驗證...")
    usgs_latest = fetch_usgs_copper_summary(end_year)
    if usgs_latest:
        cross_val = cross_validate(normalized_df, usgs_latest, end_year)
        print(f"  - OWID vs USGS 對齊: {'是' if cross_val['all_aligned'] else '否'}")

    # Step 5: 保存
    print("\n[5/5] 保存數據...")
    output_file = save_normalized_data(normalized_df, output_dir)

    print("\n" + "=" * 50)
    print("擷取完成！")
    print(f"輸出檔案: {output_file}")
    print("=" * 50)

    return normalized_df

# 執行
if __name__ == "__main__":
    df = run_ingestion_pipeline()
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] OWID 銅產量數據已擷取
- [ ] 數據已標準化為統一 schema
- [ ] 國家名稱已標準化
- [ ] 數據完整性已驗證
- [ ] 快取機制正常運作
- [ ] 輸出 CSV + 元數據 JSON
</success_criteria>
