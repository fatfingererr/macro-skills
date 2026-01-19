# 數據來源 (Data Sources)

本技能需要整合多種宏觀經濟數據，以下詳細說明各數據的來源與獲取方式。

## 數據總覽

| 數據類型 | 主要來源 | 替代來源 | 更新頻率 | API/下載方式 |
|----------|----------|----------|----------|--------------|
| 黃金儲備 | World Gold Council | IMF IFS | 月度/季度 | 公開報告 |
| 貨幣量 M0 | 各國央行 | FRED, IMF | 月度 | API / CSV |
| 貨幣量 M2 | 各國央行 | FRED, IMF | 月度 | API / CSV |
| 金價 | FRED | Yahoo Finance | 即時 | API |
| 匯率 | ECB | FRED, 各國央行 | 即時 | API |
| FX Turnover | BIS | - | 三年 | 公開報告 |

---

## 1. 黃金儲備 (Gold Reserves)

### 主要來源：World Gold Council

**網址**: https://www.gold.org/goldhub/data/gold-reserves-by-country

**數據內容**：
- 各國央行持有的黃金儲備（噸）
- 月度更新
- 歷史數據可追溯至 2000 年

**獲取方式**：
```python
# 手動下載 CSV 或使用 Selenium 爬取
# WGC 網站需要點擊下載按鈕

import requests
from bs4 import BeautifulSoup

# 示例：解析 WGC 頁面
# 注意：WGC 可能需要接受 cookies
```

### 替代來源：IMF IFS

**網址**: https://data.imf.org/regular.aspx?key=61280849

**數據內容**：
- 官方儲備資產中的黃金持有量
- 以 SDR 或美元計價

**API 存取**：
```python
# IMF 提供 SDMX API
# 但需要解析複雜的 XML 結構
```

### 主要國家黃金儲備參考值（2024 Q3）

| 國家/地區 | 代碼 | 黃金儲備 (噸) | 佔外匯儲備比例 |
|-----------|------|--------------|---------------|
| 美國 | USD | 8,133.5 | 72.4% |
| 德國 | EUR | 3,351.5 | 71.5% |
| 義大利 | EUR | 2,451.8 | 67.8% |
| 法國 | EUR | 2,436.9 | 68.1% |
| 俄羅斯 | RUB | 2,335.9 | 28.6% |
| 中國 | CNY | 2,264.3 | 4.9% |
| 瑞士 | CHF | 1,040.0 | 7.3% |
| 日本 | JPY | 845.9 | 4.4% |
| 印度 | INR | 840.8 | 9.3% |
| 荷蘭 | EUR | 612.5 | 60.8% |
| 英國 | GBP | 310.3 | 12.3% |
| 澳洲 | AUD | 79.9 | 6.7% |
| 加拿大 | CAD | 0.0 | 0.0% |

---

## 2. 貨幣量 (Money Supply)

### 美國：FRED

**網址**: https://fred.stlouisfed.org

**系列代碼**：

| 系列 | 名稱 | 說明 |
|------|------|------|
| BOGMBASE | Monetary Base; Total | M0 貨幣基數 |
| M1SL | M1 Money Stock | M1 |
| M2SL | M2 Money Stock | M2 |

**API 存取（無需 API Key）**：
```python
import pandas as pd
import requests
from io import StringIO

def fetch_fred_series(series_id, start_date, end_date):
    """從 FRED 抓取時間序列"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
    df.columns = [series_id]
    return df

# 範例
m0_us = fetch_fred_series("BOGMBASE", "2020-01-01", "2026-01-01")
m2_us = fetch_fred_series("M2SL", "2020-01-01", "2026-01-01")
```

### 歐元區：ECB

**網址**: https://data.ecb.europa.eu

**系列代碼**：

| 系列 | 名稱 | 說明 |
|------|------|------|
| BSI.M.U2.N.A.L20.A.1.U2.2300.Z01.E | M1 | 窄義貨幣 |
| BSI.M.U2.N.A.L21.A.1.U2.2300.Z01.E | M2 | 中間貨幣 |
| BSI.M.U2.N.A.L22.A.1.U2.2300.Z01.E | M3 | 廣義貨幣 |

### 中國：人民銀行

**網址**: http://www.pbc.gov.cn/diaochatongjisi/116219/index.html

**數據**：
- M0：流通中現金
- M1：M0 + 企業活期存款
- M2：M1 + 準貨幣

### 日本：日本銀行

**網址**: https://www.stat-search.boj.or.jp

**數據**：
- 貨幣基數（Monetary Base）
- M2

### IMF IFS（國際比較用）

**網址**: https://data.imf.org

**好處**：口徑相對統一，適合跨國比較
**壞處**：更新較慢，可能有 1-2 季度延遲

---

## 3. 金價 (Gold Price)

### FRED

**系列**: GOLDAMGBD228NLBM (London Bullion Market Association Gold Price)

```python
gold_price = fetch_fred_series("GOLDAMGBD228NLBM", "2020-01-01", "2026-01-01")
```

### Yahoo Finance

```python
import yfinance as yf

# 黃金期貨
gold_futures = yf.download("GC=F", start="2020-01-01", end="2026-01-01")

# 黃金 ETF
gld = yf.download("GLD", start="2020-01-01", end="2026-01-01")
```

---

## 4. 匯率 (Exchange Rates)

### FRED

```python
# 主要匯率對美元
fx_series = {
    "DEXJPUS": "JPY/USD",  # 日圓
    "DEXUSEU": "USD/EUR",  # 歐元
    "DEXCHUS": "CNY/USD",  # 人民幣
    "DEXUSUK": "USD/GBP",  # 英鎊
    "DEXSZUS": "CHF/USD",  # 瑞郎
    "DEXUSAL": "USD/AUD",  # 澳元
    "DEXCAUS": "CAD/USD",  # 加元
}
```

### ECB

**網址**: https://www.ecb.europa.eu/stats/eurofxref/

提供對歐元的匯率，需轉換為對美元。

### Yahoo Finance

```python
# 範例：美元/日圓
usdjpy = yf.download("USDJPY=X", start="2020-01-01", end="2026-01-01")
```

---

## 5. FX Turnover 權重 (BIS Triennial Survey)

### 來源：BIS

**網址**: https://www.bis.org/statistics/rpfx22.htm

**最新調查**: 2022 年（每三年更新）

**2022 年 FX Turnover 份額**：

| 貨幣 | 份額 | 說明 |
|------|------|------|
| USD | 88.25% | 全球最主要 |
| EUR | 30.92% | 第二大 |
| JPY | 16.92% | 第三大 |
| GBP | 12.88% | 第四大 |
| CNY | 7.04% | 持續上升 |
| AUD | 6.31% | - |
| CAD | 6.20% | - |
| CHF | 5.03% | - |
| HKD | 2.64% | - |
| SGD | 2.40% | - |

**注意**：BIS 使用雙邊計算，總和約 200%（因為每筆交易涉及兩種貨幣）。

**使用方式**：可直接使用份額作為權重，或正規化為總和 100%。

```python
# BIS 2022 原始份額
FX_TURNOVER_2022 = {
    "USD": 0.8825,
    "EUR": 0.3092,
    "JPY": 0.1692,
    "GBP": 0.1288,
    "CNY": 0.0704,
    "AUD": 0.0631,
    "CAD": 0.0620,
    "CHF": 0.0503,
}

# 正規化為總和 1.0（可選）
total = sum(FX_TURNOVER_2022.values())
FX_TURNOVER_NORMALIZED = {k: v/total for k, v in FX_TURNOVER_2022.items()}
```

---

## 6. 外匯儲備幣別組成 (IMF COFER)

### 來源：IMF

**網址**: https://data.imf.org/regular.aspx?key=41175

**2023 Q4 外匯儲備幣別組成**：

| 貨幣 | 份額 |
|------|------|
| USD | 58.89% |
| EUR | 19.98% |
| JPY | 5.45% |
| GBP | 4.87% |
| CNY | 2.62% |
| CAD | 2.53% |
| AUD | 2.02% |
| CHF | 0.20% |
| 其他 | 3.44% |

---

## 數據獲取程式碼範例

```python
"""
完整數據獲取範例
"""
import pandas as pd
import requests
import yfinance as yf
from io import StringIO
from typing import Dict, Optional
from datetime import datetime

class GoldRevaluationDataFetcher:
    """黃金重估數據獲取器"""

    FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def __init__(self):
        self.cache = {}

    def fetch_fred(self, series_id: str, start: str, end: str) -> pd.Series:
        """從 FRED 獲取數據"""
        params = {"id": series_id, "cosd": start, "coed": end}
        resp = requests.get(self.FRED_BASE_URL, params=params)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
        return df[series_id]

    def fetch_gold_price(self, start: str, end: str) -> pd.Series:
        """獲取金價"""
        return self.fetch_fred("GOLDAMGBD228NLBM", start, end)

    def fetch_us_money_supply(self, aggregate: str, start: str, end: str) -> pd.Series:
        """獲取美國貨幣供給"""
        series_map = {
            "M0": "BOGMBASE",
            "M1": "M1SL",
            "M2": "M2SL"
        }
        return self.fetch_fred(series_map[aggregate], start, end)

    def fetch_fx_rate(self, ticker: str, start: str, end: str) -> pd.Series:
        """從 Yahoo Finance 獲取匯率"""
        data = yf.download(ticker, start=start, end=end, progress=False)
        return data["Adj Close"]

    def get_gold_reserves_static(self) -> Dict[str, float]:
        """
        返回靜態的黃金儲備數據（噸）
        實際應用中應從 WGC/IMF 動態獲取
        """
        return {
            "USD": 8133.5,
            "EUR": 10773.5,  # 歐元區合計
            "CNY": 2264.3,
            "JPY": 845.9,
            "GBP": 310.3,
            "CHF": 1040.0,
            "AUD": 79.9,
            "CAD": 0.0,
            "RUB": 2335.9,
            "INR": 840.8,
        }

    def get_fx_turnover_weights(self) -> Dict[str, float]:
        """返回 BIS 2022 FX Turnover 權重"""
        return {
            "USD": 0.8825,
            "EUR": 0.3092,
            "JPY": 0.1692,
            "GBP": 0.1288,
            "CNY": 0.0704,
            "AUD": 0.0631,
            "CAD": 0.0620,
            "CHF": 0.0503,
        }

    def get_reserve_share_weights(self) -> Dict[str, float]:
        """返回 IMF COFER 外匯儲備幣別權重"""
        return {
            "USD": 0.5889,
            "EUR": 0.1998,
            "JPY": 0.0545,
            "GBP": 0.0487,
            "CNY": 0.0262,
            "CAD": 0.0253,
            "AUD": 0.0202,
            "CHF": 0.0020,
        }
```

---

## 數據更新時間表

| 數據 | 更新頻率 | 典型發布時間 |
|------|----------|--------------|
| 黃金儲備 (WGC) | 月度 | 每月中旬 |
| 美國 M0/M2 | 週度/月度 | 每週四/每月 |
| 金價 | 即時 | 交易日收盤 |
| 匯率 | 即時 | 交易日收盤 |
| BIS FX Survey | 三年 | 下次 2025 年 |
| IMF COFER | 季度 | 季度後約 3 個月 |

---

## 注意事項

1. **口徑差異**：各國 M0/M2 定義不完全一致，跨國比較需謹慎
2. **數據延遲**：宏觀數據有 1-3 個月發布延遲
3. **BIS 調查**：每三年更新，中間期間使用舊數據
4. **黃金儲備**：某些國家不完全公開，數據可能不準確
5. **匯率波動**：建議使用月均值或期末值保持一致
