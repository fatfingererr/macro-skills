# JSDA XLS 結構說明

## 1. 數據來源概覽

### 1.1 JSDA 統計頁面

日本證券業協會（JSDA）在官網發布多種債券交易統計：

```
JSDA 統計
├── Bonds（債券）
│   ├── Trading Volume（交易量）
│   ├── Trends in Bond Transactions (by investor type)  ← 本 Skill 使用
│   ├── Government Bonds
│   └── Corporate Bonds
└── Stocks（股票）
```

### 1.2 目標數據集

**Trends in Bond Transactions (by investor type)**

| 項目 | 內容 |
|------|------|
| 更新頻率 | 月度 |
| 發布時間 | 約次月月底 |
| 格式 | Excel (XLS/XLSX) |
| 歷史範圍 | 約 2010 年至今 |

---

## 2. XLS 結構

### 2.1 Sheet 結構

典型的 JSDA XLS 包含多個 sheet：

```
XLS 工作簿
├── JGBs（國債）          ← 主要使用
├── Corporate Bonds（公司債）
├── Municipal Bonds（地方債）
└── Notes / Definitions
```

### 2.2 JGBs Sheet 結構

**列結構**（通常）：

| 列 | 內容 |
|----|------|
| A | 年月 (YYYY/MM 或 YYYY-MM) |
| B | 投資人類型 |
| C | 天期桶 |
| D | 買入金額 (Gross Purchases) |
| E | 賣出金額 (Gross Sales) |
| F | 淨買入 (Net Purchases) |

**注意**：實際列順序可能因版本而異，需動態解析。

### 2.3 投資人類型列舉

| JSDA 英文 | JSDA 日文 | 本 Skill 映射 |
|-----------|-----------|---------------|
| City Banks | 都市銀行 | - |
| Regional Banks | 地方銀行 | - |
| Trust Banks | 信託銀行 | - |
| Life Insurance | 生命保険 | `life_insurance` |
| Non-life Insurance | 損害保険 | `non_life_insurance` |
| Investment Trusts | 投資信託 | - |
| Foreigners | 外国人 | - |
| Others | その他 | - |

### 2.4 天期桶列舉

| JSDA 英文 | JSDA 日文 | 典型範圍 | 本 Skill 映射 |
|-----------|-----------|----------|---------------|
| Short-term | 短期 | < 1Y | - |
| Medium-term | 中期 | 1-5Y | - |
| Long-term | 長期 | 5-10Y | `long` |
| Super-long | 超長期 | > 10Y | `super_long` |

**注意**：
- 天期桶定義可能隨時間調整
- 部分年份可能有更細的分類（如 10Y、20Y、30Y 分開）

---

## 3. 解析邏輯

### 3.1 讀取 XLS

```python
import pandas as pd
import requests
from io import BytesIO

def load_jsda_xls(xls_url: str) -> dict:
    """
    下載並解析 JSDA XLS

    Returns:
        dict: {sheet_name: DataFrame}
    """
    response = requests.get(xls_url, timeout=30)
    response.raise_for_status()

    # 讀取所有 sheet
    xls = pd.ExcelFile(BytesIO(response.content))
    sheets = {}

    for sheet_name in xls.sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)

    return sheets
```

### 3.2 提取目標數據

```python
def extract_investor_series(
    sheets: dict,
    investor_group: str,
    maturity_bucket: str,
    target_sheet: str = "JGBs"
) -> pd.Series:
    """
    從 XLS 提取特定投資人 + 天期桶的淨買入序列

    Returns:
        pd.Series: index=日期, values=淨買入
    """
    df = sheets.get(target_sheet)
    if df is None:
        raise ValueError(f"Sheet '{target_sheet}' not found")

    # 1. 識別列名（動態處理不同格式）
    date_col = find_date_column(df)
    investor_col = find_investor_column(df)
    maturity_col = find_maturity_column(df)
    net_col = find_net_purchases_column(df)

    # 2. 過濾
    mask = (
        df[investor_col].str.contains(INVESTOR_PATTERNS[investor_group], case=False) &
        df[maturity_col].str.contains(MATURITY_PATTERNS[maturity_bucket], case=False)
    )

    filtered = df[mask].copy()

    # 3. 轉換為序列
    filtered[date_col] = pd.to_datetime(filtered[date_col])
    series = filtered.set_index(date_col)[net_col]
    series = pd.to_numeric(series, errors="coerce")

    return series.dropna().sort_index()
```

### 3.3 合併天期桶

```python
def merge_maturity_buckets(
    sheets: dict,
    investor_group: str,
    buckets: list = ["long", "super_long"]
) -> pd.Series:
    """
    合併多個天期桶（如 long + super_long = 10y_plus）
    """
    series_list = []

    for bucket in buckets:
        s = extract_investor_series(sheets, investor_group, bucket)
        series_list.append(s)

    # 對齊日期並加總
    combined = pd.concat(series_list, axis=1).sum(axis=1)
    return combined
```

---

## 4. 常見問題

### 4.1 XLS 格式變更

**問題**：JSDA 更新網站後，XLS 格式可能改變。

**解決**：
1. 使用動態列名識別（正則匹配）
2. 保留原始 XLS 副本用於對照
3. 在輸出中標註數據版本

### 4.2 歷史數據不連續

**問題**：部分歷史月份可能缺失。

**解決**：
1. 在解析時檢測缺失月份
2. 輸出時標註數據完整性
3. 計算 streak 時跳過缺失月份（或中斷計算）

### 4.3 天期桶定義不一致

**問題**：不同年份的天期桶定義可能不同。

**解決**：
1. 在 references/jsda-structure.md 記錄歷史變更
2. 提供多口徑輸出讓用戶選擇
3. 明確標註使用的定義

---

## 5. 數據驗證

### 5.1 基本檢查

```python
def validate_series(series: pd.Series, expected_start: str, expected_end: str) -> dict:
    """驗證序列完整性"""
    return {
        "actual_start": str(series.index.min()),
        "actual_end": str(series.index.max()),
        "expected_months": count_months(expected_start, expected_end),
        "actual_months": len(series),
        "missing_pct": 1 - len(series) / count_months(expected_start, expected_end),
        "has_null": series.isnull().any()
    }
```

### 5.2 數量級檢查

```python
def sanity_check(series: pd.Series) -> dict:
    """數量級合理性檢查"""
    return {
        "min": series.min(),
        "max": series.max(),
        "mean": series.mean(),
        "unit_likely": "billion_jpy" if abs(series.mean()) < 10000 else "million_jpy"
    }
```
