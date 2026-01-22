# 資料來源與代碼

## 資料來源總覽

| 指標 | 主要來源 | 備用來源 | 歷史起始 | 頻率 |
|------|----------|----------|----------|------|
| CAPE | Shiller Online Data | Multpl.com | 1871 | 月 |
| 市值/GDP | FRED (WILL5000PRFC / GDP) | 手動計算 | 1950s | 季 |
| Trailing PE | Yahoo Finance / Multpl | FRED (SP500_PE) | 1980s | 月/日 |
| Forward PE | Yahoo Finance | FactSet | 2000s | 日 |
| PB | Yahoo Finance | Bloomberg | 1980s | 月 |
| PS | Yahoo Finance | - | 1990s | 月 |
| EV/EBITDA | Bloomberg | - | 1990s | 季 |
| Q Ratio | FRED (NCBEILQ027S) | - | 1950s | 季 |

---

## Shiller CAPE 資料

### 來源

Robert Shiller 教授維護的公開資料集，可追溯至 1871 年。

**URL**: http://www.econ.yale.edu/~shiller/data.htm

**檔案**: `ie_data.xls`

### 欄位說明

| 欄位 | 說明 |
|------|------|
| Date | 日期（YYYY.MM 格式） |
| S&P Comp. P | S&P 綜合指數價格 |
| Dividend D | 股息 |
| Earnings E | 盈餘 |
| CPI | 消費者物價指數 |
| Long Interest Rate GS10 | 10 年期公債利率 |
| Real Price | 實質價格（CPI 調整） |
| Real Dividend | 實質股息 |
| Real Earnings | 實質盈餘 |
| **CAPE** | 景氣循環調整本益比 |

### 抓取方法

```python
import pandas as pd

def fetch_shiller_cape():
    """
    從 Shiller 資料集抓取 CAPE
    """
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

    # 讀取 Excel（跳過標題行）
    df = pd.read_excel(url, sheet_name="Data", skiprows=7)

    # 清理欄位名稱
    df.columns = ['Date', 'SP_Price', 'Dividend', 'Earnings', 'CPI',
                  'Date_Fraction', 'Long_Rate', 'Real_Price', 'Real_Dividend',
                  'Real_TR_Price', 'Real_Earnings', 'Real_TR_Scaled_Earnings',
                  'CAPE', 'TR_CAPE', 'Excess_CAPE_Yield', 'Monthly_TR',
                  'Monthly_TR_Reinvested', 'Monthly_Real_TR', 'Monthly_Real_TR_Reinvested']

    # 轉換日期
    df['Date'] = pd.to_datetime(df['Date'].astype(str).str[:7], format='%Y.%m', errors='coerce')
    df = df.dropna(subset=['Date', 'CAPE'])
    df = df.set_index('Date')

    return df['CAPE']
```

---

## FRED 資料

### 系列代碼

| 系列代碼 | 名稱 | 用途 |
|----------|------|------|
| WILL5000PRFC | Wilshire 5000 Total Market Full Cap | 市值（計算市值/GDP） |
| GDP | Gross Domestic Product | GDP |
| NCBEILQ027S | Nonfinancial Corporate Business; Corporate Equities | Q Ratio 分子 |
| TNWMVBSNNCB | Nonfinancial Corporate Business; Net Worth | Q Ratio 分母 |
| SP500 | S&P 500 | 價格指數 |

### 抓取方法（無需 API Key）

```python
import pandas as pd
from datetime import datetime

def fetch_fred_series(series_id: str, start: str = "1900-01-01") -> pd.Series:
    """
    從 FRED 抓取時間序列（使用 CSV endpoint，無需 API key）

    Parameters
    ----------
    series_id : str
        FRED 系列代碼，如 'WILL5000PRFC'
    start : str
        起始日期

    Returns
    -------
    pd.Series
        時間序列資料
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

    try:
        df = pd.read_csv(url, parse_dates=['DATE'], index_col='DATE')
        df = df.rename(columns={series_id: 'value'})
        df = df[df.index >= start]
        return df['value']
    except Exception as e:
        print(f"FRED 資料抓取失敗 ({series_id}): {e}")
        return None
```

### 市值/GDP 計算

```python
def calculate_mktcap_to_gdp():
    """
    計算市值/GDP（巴菲特指標）
    """
    # 抓取資料
    mktcap = fetch_fred_series('WILL5000PRFC')  # 十億美元
    gdp = fetch_fred_series('GDP')              # 十億美元

    # GDP 是季度資料，需要 forward fill 到月度
    gdp_monthly = gdp.resample('M').ffill()
    mktcap_monthly = mktcap.resample('M').last()

    # 對齊並計算
    df = pd.DataFrame({
        'mktcap': mktcap_monthly,
        'gdp': gdp_monthly
    }).dropna()

    df['mktcap_to_gdp'] = (df['mktcap'] / df['gdp']) * 100  # 百分比

    return df['mktcap_to_gdp']
```

---

## Yahoo Finance 資料

### 使用 yfinance 套件

```bash
pip install yfinance
```

### 抓取 PE/PB 等估值指標

```python
import yfinance as yf

def fetch_yahoo_valuation(ticker: str = "^GSPC"):
    """
    從 Yahoo Finance 抓取估值指標

    注意：Yahoo Finance 的估值指標歷史較短，主要提供近期數據
    """
    stock = yf.Ticker(ticker)

    # 取得基本資料
    info = stock.info

    return {
        'trailing_pe': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'pb': info.get('priceToBook'),
        'ps': info.get('priceToSalesTrailing12Months'),
        'ev_to_ebitda': info.get('enterpriseToEbitda')
    }
```

### 抓取價格歷史

```python
def fetch_price_history(ticker: str = "^GSPC", start: str = "1950-01-01"):
    """
    抓取價格歷史
    """
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, auto_adjust=True)
    return df['Close']
```

---

## Multpl.com 資料（備用）

Multpl.com 提供長期估值指標的視覺化和下載。

### 可用資料

| 頁面 | 資料 | URL |
|------|------|-----|
| S&P 500 PE Ratio | Trailing PE | https://www.multpl.com/s-p-500-pe-ratio/table/by-month |
| Shiller PE Ratio | CAPE | https://www.multpl.com/shiller-pe/table/by-month |
| S&P 500 Price to Book | PB | https://www.multpl.com/s-p-500-price-to-book/table/by-month |
| S&P 500 Price to Sales | PS | https://www.multpl.com/s-p-500-price-to-sales/table/by-month |

### 爬蟲方法（需 Selenium）

參照 `design-human-like-crawler.md` 的方法，使用 Selenium 模擬瀏覽器抓取。

```python
# 基本架構（需搭配完整爬蟲設定）
from selenium import webdriver
from bs4 import BeautifulSoup

def fetch_multpl_data(url: str):
    """
    從 Multpl.com 抓取估值資料
    """
    # 設定瀏覽器（參照爬蟲指南）
    driver = get_selenium_driver()

    try:
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        table = soup.select_one('#datatable')

        # 解析表格...
        # (略)

    finally:
        driver.quit()
```

---

## MacroMicro 資料（可選）

財經 M 平方提供 Highcharts 圖表，可抓取完整時間序列。

### 可用圖表

| 指標 | 圖表 URL |
|------|----------|
| 美股 PE | /charts/xxx/us-pe-ratio |
| 美股 CAPE | /charts/xxx/us-shiller-pe |

### 抓取方法

參照 `macromicro-highcharts-crawler.md`，使用 Selenium 等待 Highcharts 渲染完成後提取資料。

---

## 資料品質說明

### 各來源比較

| 來源 | 優點 | 缺點 |
|------|------|------|
| Shiller | 歷史最長（150年）、學術標準 | 更新頻率低（月度） |
| FRED | 官方資料、免費無限制 | 部分系列歷史較短 |
| Yahoo Finance | 即時、方便 | 歷史短、估值數據不完整 |
| Multpl | 長期視覺化、免費 | 需爬蟲、更新可能延遲 |
| MacroMicro | 完整 Highcharts 資料 | 需爬蟲、可能被封鎖 |

### 資料對齊注意事項

1. **頻率不同**：CAPE 是月度，GDP 是季度，PE 可能是日度
2. **時區問題**：美股收盤後才有當日數據
3. **修正問題**：GDP 等經濟數據會修正，需使用「首次公布值」或「最終值」
4. **缺值處理**：使用前向填充（ffill）或線性插值

```python
def align_data(series_dict, freq='M'):
    """
    將多個時間序列對齊到相同頻率
    """
    aligned = {}
    for name, series in series_dict.items():
        # 重採樣到月末
        if freq == 'M':
            aligned[name] = series.resample('M').last()
        elif freq == 'Q':
            aligned[name] = series.resample('Q').last()

    # 合併並 dropna
    df = pd.DataFrame(aligned)
    df = df.ffill()  # 前向填充

    return df
```
