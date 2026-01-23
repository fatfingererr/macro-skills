# FRED 資料抓取與處理指南

> **沉澱日期**: 2026-01-23
> **目的**: 提供未來 Skill 設計時的 FRED 資料處理參考，避免重複犯錯

---

## 1. 核心問題與解決方案

### 1.1 常見錯誤：假設 CSV 列名

**錯誤寫法**：
```python
# ❌ 假設列名是 "DATE"，會導致 KeyError
df = pd.read_csv(StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
```

**錯誤訊息**：
```
KeyError: "None of ['DATE'] are in the columns"
Missing column provided to 'parse_dates': 'DATE'
```

**正確寫法**：
```python
# ✅ 手動處理列名，更健壯
df = pd.read_csv(StringIO(response.text))
df.columns = ["DATE", series_id]  # 明確指定列名
df["DATE"] = pd.to_datetime(df["DATE"])
df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
df = df.dropna()
df = df.set_index("DATE")
```

---

## 2. 標準 FRED 抓取函數模板

### 2.1 基本抓取函數

```python
import pandas as pd
import requests
from io import StringIO

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Parameters:
    -----------
    series_id : str
        FRED 系列代碼 (e.g., "DGS10", "BAMLC0A0CM")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns:
    --------
    pd.Series
        時間序列數據，index 為 DatetimeIndex
    """
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        # 健壯的 CSV 解析方式
        df = pd.read_csv(StringIO(response.text))

        # FRED CSV 格式：第一列是日期，第二列是數值
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])

        # 處理缺失值（FRED 使用 '.' 表示缺失）
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        df = df.dropna()
        df = df.set_index("DATE")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)
```

### 2.2 進階版本（含 User-Agent 和延遲）

參考 `us-cpi-pce-comparator/scripts/fetch_fred_data.py` 的 `FREDFetcher` 類別：

```python
import random
import time

class FREDFetcher:
    BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    ]

    def _random_delay(self, min_sec=0.3, max_sec=1.0):
        """模擬人類行為的隨機延遲"""
        time.sleep(random.uniform(min_sec, max_sec))

    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/csv,text/html,application/xhtml+xml',
        }

    def fetch_single_series(self, series_id, start_date, end_date):
        self._random_delay()

        params = {'id': series_id, 'cosd': start_date, 'coed': end_date}
        url = f"{self.BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True, na_values=['.'])
        return df.iloc[:, 0]
```

---

## 3. 快取處理最佳實踐

### 3.1 快取的常見問題

**問題**：DataFrame 索引名稱不一致導致載入失敗

```python
# ❌ 保存時索引可能沒有名稱
data = df.reset_index().to_dict(orient="records")

# ❌ 載入時假設列名是 "DATE"
df = pd.DataFrame(data).set_index("DATE")  # KeyError!
```

### 3.2 正確的快取處理

```python
def save_cache(key: str, df: pd.DataFrame):
    """儲存快取"""
    CACHE_DIR.mkdir(exist_ok=True)

    # ✅ 確保索引有名稱
    df_to_save = df.copy()
    if df_to_save.index.name is None:
        df_to_save.index.name = "DATE"

    data = df_to_save.reset_index().to_dict(orient="records")
    with open(CACHE_DIR / f"{key}.json", "w", encoding="utf-8") as f:
        json.dump({
            "cached_at": datetime.now().isoformat(),
            "data": data
        }, f, default=str)


def load_cache(key: str):
    """載入快取"""
    if is_cache_valid(key):
        with open(CACHE_DIR / f"{key}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data["data"])

            # ✅ 動態取得第一列作為索引（不假設列名）
            first_col = df.columns[0]
            df[first_col] = pd.to_datetime(df[first_col])
            df = df.set_index(first_col)
            return df
    return None
```

---

## 4. 常用 FRED 系列代碼

### 4.1 利率相關

| 系列代碼 | 名稱                                    | 頻率 | 用途                |
|----------|-----------------------------------------|------|---------------------|
| DGS10    | 10-Year Treasury Constant Maturity Rate | 日   | 長端利率、MOVE 代理 |
| DGS2     | 2-Year Treasury Constant Maturity Rate  | 日   | 短端利率            |
| FEDFUNDS | Federal Funds Effective Rate            | 日   | 政策利率            |

### 4.2 信用利差

| 系列代碼     | 名稱                                | 頻率 | 用途                       |
|--------------|-------------------------------------|------|----------------------------|
| BAMLC0A0CM   | ICE BofA US Corporate Index OAS     | 日   | IG 信用利差（CDX IG 代理） |
| BAMLC0A4CBBB | ICE BofA BBB US Corporate Index OAS | 日   | BBB 級利差                 |
| BAMLH0A0HYM2 | ICE BofA US High Yield Index OAS    | 日   | 高收益債利差               |

### 4.3 通膨相關

| 系列代碼 | 名稱                        | 頻率 | 用途     |
|----------|-----------------------------|------|----------|
| CPIAUCSL | CPI for All Urban Consumers | 月   | 整體 CPI |
| CPILFESL | CPI Less Food and Energy    | 月   | 核心 CPI |
| PCEPI    | PCE Price Index             | 月   | PCE 通膨 |
| PCEPILFE | PCE Less Food and Energy    | 月   | 核心 PCE |

### 4.4 銀行體系

| 系列代碼       | 名稱                            | 頻率 | 用途     |
|----------------|---------------------------------|------|----------|
| TOTLL          | Loans and Leases in Bank Credit | 週   | 銀行貸款 |
| DPSACBW027SBOG | Deposits, All Commercial Banks  | 週   | 銀行存款 |

### 4.5 波動率

| 系列代碼 | 名稱                       | 頻率 | 用途       |
|----------|----------------------------|------|------------|
| VIXCLS   | CBOE Volatility Index: VIX | 日   | 股市波動率 |

---

## 5. 已驗證的參考實作

以下 Skill 的 FRED 抓取已驗證可正常運作：

| Skill                                       | 檔案                             | 特點                                     |
|---------------------------------------------|----------------------------------|------------------------------------------|
| `us-cpi-pce-comparator`                     | `scripts/fetch_fred_data.py`     | 完整的 FREDFetcher 類別、User-Agent 輪換 |
| `analyze-us-bank-credit-deposit-decoupling` | `scripts/decoupling_analyzer.py` | 簡潔的單函數實作                         |
| `analyze-move-risk-gauges-leadlag`          | `scripts/fetch_data.py`          | 修復後的版本                             |

---

## 6. 除錯清單

當 FRED 抓取失敗時，依序檢查：

- [ ] **列名問題**：是否使用 `parse_dates=["DATE"]`？改用手動處理
- [ ] **快取問題**：刪除 `cache/` 目錄重新測試
- [ ] **網路問題**：檢查 `response.status_code` 和 `response.text`
- [ ] **日期格式**：確保使用 `YYYY-MM-DD` 格式
- [ ] **缺失值**：FRED 使用 `.` 表示缺失，需要 `replace(".", pd.NA)`
- [ ] **數值轉換**：使用 `pd.to_numeric(errors="coerce")` 處理異常值

---

## 7. 測試腳本模板

```python
#!/usr/bin/env python3
"""測試 FRED 資料抓取"""

from fetch_data import fetch_fred_series

def test_fred_fetch():
    series_to_test = [
        ("DGS10", "10Y 國債殖利率"),
        ("BAMLC0A0CM", "IG 信用利差"),
        ("VIXCLS", "VIX"),
    ]

    for series_id, name in series_to_test:
        print(f"測試 {series_id} ({name})...")
        data = fetch_fred_series(series_id, "2025-01-01", "2026-01-23")

        if not data.empty:
            print(f"  ✓ 成功！{len(data)} 筆資料")
            print(f"  日期範圍: {data.index.min()} 至 {data.index.max()}")
            print(f"  最新值: {data.iloc[-1]:.2f}")
        else:
            print(f"  ✗ 失敗")
        print()

if __name__ == "__main__":
    test_fred_fetch()
```

