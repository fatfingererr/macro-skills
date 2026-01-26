# 資料來源與 FRED 系列代碼

## 主要資料來源

### FRED (Federal Reserve Economic Data)

**URL**: https://fred.stlouisfed.org

**API**: CSV endpoint（無需 API key）

**抓取方式**:
```python
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }
    response = requests.get(FRED_CSV_URL, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["DATE", series_id]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df[series_id] = df[series_id].replace(".", pd.NA)
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna().set_index("DATE")

    return df[series_id]
```

---

## 系列代碼清單

### 目標序列

| 系列代碼 | 名稱 | 頻率 | 說明 |
|----------|------|------|------|
| **WUDSHO** | Unamortized Discounts on Securities Held Outright | 週 | 聯準會持有證券的未攤銷折價 |

### 交叉驗證指標

#### 信用利差

| 系列代碼 | 名稱 | 頻率 | 用途 |
|----------|------|------|------|
| **BAMLC0A0CM** | ICE BofA US Corporate Index OAS | 日 | IG 信用利差 |
| **BAMLH0A0HYM2** | ICE BofA US High Yield Index OAS | 日 | 高收益債利差 |
| **BAMLC0A4CBBB** | ICE BofA BBB US Corporate Index OAS | 日 | BBB 級利差 |

#### 波動率

| 系列代碼 | 名稱 | 頻率 | 用途 |
|----------|------|------|------|
| **VIXCLS** | CBOE Volatility Index: VIX | 日 | 股市隱含波動率 |

#### 國債殖利率

| 系列代碼 | 名稱 | 頻率 | 用途 |
|----------|------|------|------|
| **DGS10** | 10-Year Treasury Constant Maturity Rate | 日 | 10 年期國債殖利率 |
| **DGS2** | 2-Year Treasury Constant Maturity Rate | 日 | 2 年期國債殖利率 |
| **DGS3MO** | 3-Month Treasury Bill Secondary Market Rate | 日 | 3 個月國庫券利率 |

殖利率曲線 = DGS10 - DGS2（正常為正，倒掛為負）

#### 聯準會資產負債表

| 系列代碼 | 名稱 | 頻率 | 用途 |
|----------|------|------|------|
| **WALCL** | Fed Total Assets | 週 | Fed 資產負債表總規模 |
| **WTREGEN** | Treasury General Account | 週 | 財政部在 Fed 的帳戶餘額 |
| **WSHOSHO** | Securities Held Outright | 週 | Fed 持有的證券總額 |

#### 貨幣市場壓力

| 系列代碼 | 名稱 | 頻率 | 用途 |
|----------|------|------|------|
| **SOFR** | Secured Overnight Financing Rate | 日 | 有擔保隔夜融資利率 |
| **EFFR** | Effective Federal Funds Rate | 日 | 有效聯邦基金利率 |

---

## 資料頻率與延遲

| 類型 | 頻率 | 延遲 | 說明 |
|------|------|------|------|
| Fed 資產負債表 | 週 | T+1~3 | 每週三發布上週數據 |
| 信用利差 | 日 | T+0 | 當日可得 |
| VIX | 日 | T+0 | 當日可得 |
| 國債殖利率 | 日 | T+0 | 當日可得 |

**處理方式**：
- 對齊至週頻時，取週末值（或該週最後有效值）
- 揭露「資料截止日」

---

## 資料品質注意事項

### 缺失值處理

FRED 使用 `.` 表示缺失值：

```python
df[series_id] = df[series_id].replace(".", pd.NA)
df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
df = df.dropna()
```

### 歷史可得期間

| 系列 | 可回溯至 | 說明 |
|------|----------|------|
| WUDSHO | 2003 年 | Fed 資產負債表現代格式 |
| BAMLC0A0CM | 1996 年 | ICE BofA 指數 |
| VIXCLS | 1990 年 | CBOE VIX |
| DGS10 | 1962 年 | 國債殖利率 |

### 結構性斷點

- **2008 年**：QE 開始，Fed 資產負債表結構性變化
- **2020 年**：無限 QE，規模再次劇增
- **2022 年**：QT 開始，規模縮減

比對時應注意這些結構性變化。

---

## Fallback 替代方案

若主要來源不可用，可使用：

| 主要來源 | Fallback | 說明 |
|----------|----------|------|
| FRED WUDSHO | Fed H.4.1 PDF | 需手動解析 |
| BAMLC0A0CM | Yahoo Finance ^AMLC | 可能有差異 |
| VIXCLS | Yahoo Finance ^VIX | 即時更新 |

---

## 快取機制

建議使用本地快取避免重複請求：

```python
CACHE_DIR = Path("cache")

def get_with_cache(series_id: str, start: str, end: str, max_age_hours: int = 24):
    cache_file = CACHE_DIR / f"{series_id}_{start}_{end}.json"

    if cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=max_age_hours):
            with open(cache_file) as f:
                data = json.load(f)
            return pd.Series(data["values"], index=pd.to_datetime(data["dates"]))

    # Fetch fresh data
    series = fetch_fred_series(series_id, start, end)

    # Save to cache
    CACHE_DIR.mkdir(exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump({
            "dates": series.index.strftime("%Y-%m-%d").tolist(),
            "values": series.tolist(),
            "fetched_at": datetime.now().isoformat()
        }, f)

    return series
```
