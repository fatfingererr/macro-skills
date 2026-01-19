# 資料來源 (Data Sources)

## 概述
本技能使用的所有資料均來自公開、免費、可重現的來源，確保分析的透明度與可複製性。

---

## 一、人口與撫養比資料

### 1.1 World Bank World Development Indicators (WDI)
- **官方網站**: https://data.worldbank.org/
- **API 端點**: https://api.worldbank.org/v2/
- **Python 套件**: `wbdata`

| 指標代碼 | 名稱 | 定義 |
|----------|------|------|
| SP.POP.DPND.OL | Age dependency ratio, old | 65+ / 15-64 × 100 |
| SP.POP.DPND.YG | Age dependency ratio, young | 0-14 / 15-64 × 100 |
| SP.POP.DPND | Age dependency ratio | (0-14 + 65+) / 15-64 × 100 |
| SP.POP.65UP.TO.ZS | Population ages 65+ (% of total) | |
| SP.POP.TOTL | Total population | |

**使用範例**:
```python
import wbdata

# 設定日期範圍
date_range = (datetime.datetime(2010, 1, 1), datetime.datetime(2023, 12, 31))

# 擷取老年撫養比
data = wbdata.get_dataframe(
    {"SP.POP.DPND.OL": "old_age_dependency"},
    country=["JPN", "USA", "DEU"],
    date=date_range
)
```

### 1.2 UN World Population Prospects (WPP)
- **官方網站**: https://population.un.org/wpp/
- **下載頁面**: https://population.un.org/wpp/Download/Standard/CSV/
- **更新頻率**: 每 2 年（最新 2024 年版）

**檔案類型**:
- Historical estimates (1950-2023)
- Medium variant projections (2024-2100)
- High/Low variant projections

**適用情境**: 用於撫養比預測至 2050 年或更遠

---

## 二、政府債務資料

### 2.1 IMF World Economic Outlook (WEO)
- **官方網站**: https://www.imf.org/en/Publications/WEO
- **資料庫**: https://www.imf.org/en/Publications/WEO/weo-database/
- **下載格式**: Excel, CSV

| 指標代碼 | 名稱 | 定義 |
|----------|------|------|
| GGXWDG_NGDP | General government gross debt | % of GDP |
| GGXCNL_NGDP | General government net lending/borrowing | % of GDP |
| NGDP_RPCH | Real GDP growth | Annual % change |
| PCPIPCH | Inflation (CPI) | Annual % change |

**使用範例**:
```python
# IMF WEO 通常以 Excel 提供，需手動下載或使用 imfpy
import pandas as pd

weo_data = pd.read_csv("WEOApr2024.csv", encoding="latin-1")
debt_data = weo_data[weo_data["WEO Subject Code"] == "GGXWDG_NGDP"]
```

### 2.2 World Bank WDI 債務指標
| 指標代碼 | 名稱 |
|----------|------|
| GC.DOD.TOTL.GD.ZS | Central government debt, total (% of GDP) |
| GC.DOD.TOTL.CN | Central government debt, total (current LCU) |

**注意**: World Bank 債務資料覆蓋率較 IMF 低，部分國家可能缺失

---

## 三、政府支出資料

### 3.1 World Bank WDI
| 指標代碼 | 名稱 | 定義 |
|----------|------|------|
| NE.CON.GOVT.ZS | General government final consumption expenditure | % of GDP |
| GC.XPN.TOTL.GD.ZS | Expense | % of GDP |
| GC.REV.XGRT.GD.ZS | Revenue, excluding grants | % of GDP |

### 3.2 IMF Government Finance Statistics (GFS)
- **官方網站**: https://data.imf.org/GFS
- **涵蓋範圍**: 更細緻的政府財政分類

| 指標 | 說明 |
|------|------|
| Compensation of employees | 公部門薪資 |
| Goods and services | 政府採購 |
| Social benefits | 社會福利支出 |
| Interest | 利息支出 |

---

## 四、健康支出資料

### 4.1 WHO Global Health Expenditure Database (GHED)
- **官方網站**: https://apps.who.int/nha/database
- **下載格式**: Excel, CSV
- **更新頻率**: 年度

| 指標 | 說明 |
|------|------|
| CHE_GDP | Current health expenditure as % of GDP |
| GGHE_CHE | Government health expenditure as % of CHE |
| OOPS_CHE | Out-of-pocket as % of CHE |

### 4.2 World Bank WDI
| 指標代碼 | 名稱 |
|----------|------|
| SH.XPD.CHEX.GD.ZS | Current health expenditure (% of GDP) |
| SH.XPD.GHED.GD.ZS | Domestic general government health expenditure (% of GDP) |

---

## 五、經濟成長與通膨資料

### 5.1 World Bank WDI
| 指標代碼 | 名稱 |
|----------|------|
| NY.GDP.MKTP.KD.ZG | GDP growth (annual %) | 實質 |
| NY.GDP.MKTP.CD | GDP (current US$) |
| FP.CPI.TOTL.ZG | Inflation, consumer prices (annual %) |

### 5.2 名義 GDP 成長計算
```python
# 名義 GDP 成長 ≈ 實質 GDP 成長 + CPI 通膨
nominal_gdp_growth = real_gdp_growth + cpi_inflation

# 或直接從名義 GDP 計算
nominal_gdp = wbdata.get_dataframe({"NY.GDP.MKTP.CD": "gdp_nominal"})
nominal_growth = nominal_gdp.pct_change() * 100
```

---

## 六、利率資料

### 6.1 OECD Statistics
- **官方網站**: https://stats.oecd.org/
- **API**: https://stats.oecd.org/SDMX-JSON/

| 指標代碼 | 名稱 |
|----------|------|
| IRLT | Long-term interest rates (10-year government bonds) |
| IRSTCI | Short-term interest rates |

**覆蓋範圍**: 主要為 OECD 成員國

### 6.2 各國央行資料
對於非 OECD 國家或缺失資料，需直接從央行網站取得：

| 國家 | 來源 |
|------|------|
| 美國 | FRED (Federal Reserve Economic Data) |
| 日本 | Bank of Japan Statistics |
| 中國 | PBOC / Wind |
| 印度 | RBI Database |

### 6.3 回退策略
當 10 年公債殖利率不可用時：
1. 使用 5 年公債殖利率
2. 使用政策利率（央行基準利率）
3. 使用銀行貸款利率

```python
def get_interest_rate(entity, year):
    # 嘗試順序：10Y yield → 5Y yield → policy rate → lending rate
    for indicator in ["IRLT", "IRS5Y", "IRSTCI", "FR.INR.LEND"]:
        rate = fetch_indicator(entity, indicator, year)
        if rate is not None:
            return rate
    return None
```

---

## 七、資本管制與金融抑制指標

### 7.1 Chinn-Ito Index
- **官方網站**: http://web.pdx.edu/~ito/Chinn-Ito_website.htm
- **說明**: 衡量資本帳戶開放程度
- **範圍**: -1.89 (最封閉) 至 2.39 (最開放)

### 7.2 IMF AREAER
- **官方網站**: https://www.elibrary-areaer.imf.org/
- **說明**: Annual Report on Exchange Arrangements and Exchange Restrictions

---

## 八、資料取得 Python 程式碼範例

```python
import wbdata
import pandas as pd
import datetime

def fetch_worldbank_data(entities, indicators, start_year, end_year):
    """
    從 World Bank API 擷取資料

    Parameters:
    - entities: list of ISO3 country codes
    - indicators: dict of {indicator_code: column_name}
    - start_year, end_year: int
    """
    date_range = (
        datetime.datetime(start_year, 1, 1),
        datetime.datetime(end_year, 12, 31)
    )

    data = wbdata.get_dataframe(
        indicators,
        country=entities,
        date=date_range
    )

    return data.reset_index()


# 使用範例
indicators = {
    "SP.POP.DPND.OL": "old_age_dependency",
    "GC.DOD.TOTL.GD.ZS": "debt_to_gdp",
    "NE.CON.GOVT.ZS": "gov_consumption",
    "NY.GDP.MKTP.KD.ZG": "real_gdp_growth",
    "FP.CPI.TOTL.ZG": "cpi_inflation"
}

entities = ["JPN", "USA", "DEU", "GBR", "FRA", "ITA", "CAN"]

df = fetch_worldbank_data(entities, indicators, 2010, 2023)
```

---

## 九、資料品質與限制

### 9.1 常見問題
| 問題 | 影響 | 因應方式 |
|------|------|----------|
| 資料延遲 | 最新年份可能缺失 | 使用 T-1 或 T-2 年份 |
| 跨國定義差異 | 指標不完全可比 | 註記資料來源，謹慎解讀 |
| 部分國家缺失 | 截面不完整 | 從截面統計中排除 |
| 殖利率不可用 | 無法計算 r-g | 使用政策利率替代 |

### 9.2 資料更新時程
| 來源 | 更新頻率 | 延遲 |
|------|----------|------|
| World Bank WDI | 持續 | 1-2 年 |
| IMF WEO | 每年 4 月、10 月 | 數月 |
| UN WPP | 每 2 年 | - |
| WHO GHED | 年度 | 1-2 年 |
| OECD | 月度/季度/年度 | 數週至數月 |
