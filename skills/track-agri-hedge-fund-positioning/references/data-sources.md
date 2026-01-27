# 資料來源

## 1. CFTC COT Reports（核心）

### 1.1 官方來源

| 項目         | 說明                                                    |
|--------------|--------------------------------------------------------|
| **官網**     | https://www.cftc.gov/MarketReports/CommitmentsofTraders |
| **發布日**   | 每週五 15:30 ET                                         |
| **截止日**   | 每週二收盤                                              |
| **格式**     | CSV, TXT                                                |
| **費用**     | 免費公開                                                |
| **歷史檔案** | 1986 年至今                                             |

### 1.2 下載 URL 格式

**當年資料**：
```
https://www.cftc.gov/dea/newcot/deafut.txt        # 期貨
https://www.cftc.gov/dea/newcot/deacom.txt        # 合併（期貨+選擇權）
https://www.cftc.gov/dea/newcot/f_disagg.txt      # Disaggregated
```

**歷史資料**：
```
https://www.cftc.gov/files/dea/history/fut_fin_txt_{YEAR}.zip
https://www.cftc.gov/files/dea/history/fut_disagg_txt_{YEAR}.zip
```

### 1.3 欄位說明（Legacy Report）

| 欄位                      | 說明                  |
|---------------------------|-----------------------|
| Market_and_Exchange_Names | 商品與交易所          |
| As_of_Date_In_Form_YYMMDD | COT 截止日期          |
| Open_Interest_All         | 總未平倉量            |
| NonComm_Positions_Long    | 非商業多單            |
| NonComm_Positions_Short   | 非商業空單            |
| NonComm_Positions_Spread  | 非商業價差            |
| Comm_Positions_Long       | 商業多單              |
| Comm_Positions_Short      | 商業空單              |
| NonRept_Positions_Long    | 非報告多單            |
| NonRept_Positions_Short   | 非報告空單            |

---

## 2. 宏觀指標

### 2.1 FRED（免費，無需 API Key）

**CSV 下載 URL**：
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}&cosd={START}&coed={END}
```

**可用序列**：

| 用途        | Series ID      | 說明                        |
|-------------|----------------|-----------------------------|
| 美元指數    | DTWEXBGS       | Trade Weighted USD (Broad)  |
| 短端利率    | DGS2           | 2Y Treasury                 |
| 長端利率    | DGS10          | 10Y Treasury                |
| VIX         | VIXCLS         | CBOE VIX                    |
| 信用利差    | BAMLC0A0CM     | IG OAS                      |

### 2.2 Yahoo Finance（免費）

使用 `yfinance` 套件：

```python
import yfinance as yf

# 美元指數代理
uup = yf.download("UUP", start="2025-01-01", end="2026-01-27")

# 原油
wti = yf.download("CL=F", start="2025-01-01", end="2026-01-27")

# 金屬 ETF
xme = yf.download("XME", start="2025-01-01", end="2026-01-27")

# 農產品 ETF
dba = yf.download("DBA", start="2025-01-01", end="2026-01-27")
```

**常用代碼**：

| 用途         | Symbol   | 說明                    |
|--------------|----------|-------------------------|
| 美元 ETF     | UUP      | Invesco DB US Dollar    |
| 原油期貨     | CL=F     | WTI Crude               |
| 黃金期貨     | GC=F     | Gold                    |
| 金屬 ETF     | XME      | SPDR S&P Metals & Mining|
| 農產品 ETF   | DBA      | Invesco DB Agriculture  |
| 玉米期貨     | ZC=F     | Corn                    |
| 大豆期貨     | ZS=F     | Soybeans                |
| 小麥期貨     | ZW=F     | Wheat                   |

---

## 3. 基本面資料

### 3.1 USDA Export Sales

| 項目         | 說明                                           |
|--------------|------------------------------------------------|
| **官網**     | https://apps.fas.usda.gov/export-sales/esrd1.html |
| **發布日**   | 每週四 8:30 ET                                  |
| **商品**     | 穀物、油籽、棉花、肉類                          |
| **格式**     | HTML, Excel                                     |
| **費用**     | 免費公開                                        |

### 3.2 USDA WASDE

| 項目         | 說明                                           |
|--------------|------------------------------------------------|
| **官網**     | https://www.usda.gov/oce/commodity/wasde       |
| **發布日**   | 每月約 10-12 日                                 |
| **格式**     | PDF, TXT                                        |
| **費用**     | 免費公開                                        |

可搭配 `wasde-ingestor` skill 使用。

### 3.3 USDA Crop Progress

| 項目         | 說明                                           |
|--------------|------------------------------------------------|
| **官網**     | https://usda.library.cornell.edu/concern/publications/8336h188j |
| **發布日**   | 每週一 16:00 ET（生長季）                       |
| **格式**     | PDF                                             |
| **費用**     | 免費公開                                        |

---

## 4. 資料抓取範例

### 4.1 抓取 COT 資料

```python
import pandas as pd
import requests
from io import StringIO

def fetch_cot_legacy(year=2026):
    """抓取 Legacy COT 資料"""
    if year == 2026:
        url = "https://www.cftc.gov/dea/newcot/deafut.txt"
    else:
        url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    return df
```

### 4.2 抓取 FRED 資料

```python
def fetch_fred_series(series_id, start_date, end_date):
    """從 FRED 抓取時間序列（無需 API key）"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["DATE", series_id]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df[series_id] = pd.to_numeric(df[series_id].replace(".", pd.NA), errors="coerce")
    df = df.dropna().set_index("DATE")

    return df[series_id]
```

---

## 5. 資料更新頻率

| 資料來源       | 更新頻率 | 發布時間        | 延遲   |
|----------------|----------|-----------------|--------|
| CFTC COT       | 週       | 週五 15:30 ET   | T+3    |
| FRED           | 日       | 即時            | T+0    |
| Yahoo Finance  | 日       | 即時            | T+0    |
| USDA Export    | 週       | 週四 8:30 ET    | T+0    |
| USDA WASDE     | 月       | 約 10-12 日     | T+0    |

---

## 6. 備援與 Fallback

### 6.1 COT 資料備援

| 主要來源   | 備援來源                    |
|------------|-----------------------------|
| CFTC 官網  | Quandl (付費)               |
| CFTC 官網  | CME Group (部分商品)        |
| CFTC 官網  | 手動下載 + 本地快取         |

### 6.2 宏觀指標備援

| 主要來源       | 備援來源              |
|----------------|-----------------------|
| FRED DXY proxy | Yahoo Finance UUP     |
| Yahoo CL=F     | FRED DCOILWTICO       |
| Yahoo XME      | FRED 工業金屬指數     |
