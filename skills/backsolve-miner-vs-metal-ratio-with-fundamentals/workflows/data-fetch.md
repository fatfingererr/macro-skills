# Workflow: 數據抓取

<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 數據來源說明
2. thoughts/shared/guide/design-human-like-crawler.md - 爬蟲設計指南
</required_reading>

<process>

## Step 1: 價格數據抓取

使用 yfinance 取得價格序列：

```python
import yfinance as yf
import pandas as pd

def fetch_prices(symbol: str, start: str, end: str, interval: str = "1wk"):
    """
    抓取價格數據

    Parameters
    ----------
    symbol : str
        Yahoo Finance 代碼（如 SI=F, SIL）
    start : str
        起始日期 YYYY-MM-DD
    end : str
        結束日期 YYYY-MM-DD
    interval : str
        取樣頻率（1d, 1wk, 1mo）

    Returns
    -------
    pd.Series
        收盤價序列
    """
    data = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        progress=False
    )
    return data['Close'].dropna()
```

**常用代碼對照**

| 資產           | Yahoo Finance 代碼 |
|----------------|-------------------|
| 白銀期貨       | SI=F              |
| 黃金期貨       | GC=F              |
| 白銀現貨       | XAGUSD=X          |
| SIL 銀礦 ETF   | SIL               |
| SILJ 小型銀礦  | SILJ              |
| GDX 金礦 ETF   | GDX               |
| SLV 白銀 ETF   | SLV               |

## Step 2: ETF 持股抓取

### 方法 1: 官方 CSV（優先）

```python
import pandas as pd
import httpx

def fetch_etf_holdings_csv(etf_ticker: str) -> dict:
    """
    從 ETF 發行商官網抓取持股 CSV

    Returns
    -------
    dict
        {ticker: weight} 格式
    """
    # Global X SIL/SILJ
    if etf_ticker in ['SIL', 'SILJ']:
        url = f"https://www.globalxetfs.com/funds/{etf_ticker.lower()}/"
        # 需解析 HTML 找到 CSV 下載連結
        # 或使用已知的 holdings CSV URL

    # VanEck GDX/GDXJ
    elif etf_ticker in ['GDX', 'GDXJ']:
        # VanEck 官網 holdings

    # 解析 CSV
    df = pd.read_csv(holdings_url)
    holdings = dict(zip(df['Ticker'], df['Weight'] / 100))

    return holdings
```

### 方法 2: SEC N-PORT（備援）

```python
def fetch_nport_holdings(cik: str, filing_date: str = None):
    """
    從 SEC N-PORT 抓取基金持股

    Parameters
    ----------
    cik : str
        基金的 CIK 編號
    filing_date : str
        申報日期（若空則取最新）
    """
    # SEC EDGAR API
    base_url = "https://data.sec.gov/submissions/CIK{cik}.json"

    # 找到 N-PORT 申報
    # 解析 XML 取得持股
```

### 方法 3: 手動 CSV

若以上方法不可用，支援手動提供 CSV URL：

```python
def fetch_manual_holdings(csv_url: str) -> dict:
    df = pd.read_csv(csv_url)
    # 假設欄位為 Ticker, Weight
    return dict(zip(df['Ticker'], df['Weight']))
```

## Step 3: 財報數據抓取（SEC EDGAR）

### 3.1 XBRL JSON API（推薦）

```python
import httpx

def fetch_sec_xbrl(cik: str, ticker: str):
    """
    使用 SEC XBRL JSON API 抓取財報數據

    API 端點：
    https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
    """
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"

    headers = {
        'User-Agent': 'YourApp/1.0 (your@email.com)',
        'Accept': 'application/json'
    }

    response = httpx.get(url, headers=headers)
    data = response.json()

    # 提取常用欄位
    facts = data.get('facts', {}).get('us-gaap', {})

    result = {
        'total_debt': extract_latest(facts, 'LongTermDebt'),
        'cash': extract_latest(facts, 'CashAndCashEquivalentsAtCarryingValue'),
        'shares': extract_latest(facts, 'CommonStockSharesOutstanding'),
        'revenue': extract_latest(facts, 'Revenues'),
        'operating_income': extract_latest(facts, 'OperatingIncomeLoss'),
        'cfo': extract_latest(facts, 'NetCashProvidedByUsedInOperatingActivities'),
        'capex': extract_latest(facts, 'PaymentsToAcquirePropertyPlantAndEquipment'),
    }

    return result


def extract_latest(facts: dict, concept: str):
    """從 XBRL facts 提取最新值"""
    if concept not in facts:
        return None

    units = facts[concept].get('units', {})
    # 通常是 USD 或 shares
    values = units.get('USD', units.get('shares', []))

    if not values:
        return None

    # 取最新申報
    latest = sorted(values, key=lambda x: x.get('end', ''), reverse=True)[0]
    return latest.get('val')
```

### 3.2 公司代碼到 CIK 映射

```python
# 常見銀礦公司 CIK
SILVER_MINER_CIKS = {
    'PAAS': '0001209028',  # Pan American Silver
    'AG': '0001331877',    # First Majestic Silver
    'HL': '0000719413',    # Hecla Mining
    'MAG': '0001331255',   # MAG Silver
    'EXK': '0001437419',   # Endeavour Silver
    'CDE': '0000018974',   # Coeur Mining
    'FSM': '0001555280',   # Fortuna Silver
}
```

## Step 4: AISC 抽取（MD&A 文字）

```python
from bs4 import BeautifulSoup
import re

def extract_aisc_from_mda(mda_html: str) -> float:
    """
    從 MD&A 文字中抽取 AISC

    常見模式：
    - "AISC of $X.XX per ounce"
    - "all-in sustaining cost of $X.XX/oz"
    - "AISC was $X.XX per silver ounce"
    """
    soup = BeautifulSoup(mda_html, 'lxml')
    text = soup.get_text()

    patterns = [
        r'AISC\s+(?:of\s+)?\$?([\d.]+)\s*(?:per\s+)?(?:ounce|oz)',
        r'all-in\s+sustaining\s+cost\s+(?:of\s+)?\$?([\d.]+)',
        r'AISC\s+was\s+\$?([\d.]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None


def proxy_aisc(financials: dict, production_oz: float) -> float:
    """
    Proxy 回算 AISC（當直接抽取失敗時）

    AISC ≈ (OpCost + SustainingCapex + G&A - ByproductCredits) / Oz
    """
    operating_cost = financials.get('cost_of_revenue', 0)
    sustaining_capex = financials.get('capex', 0) * 0.6  # 假設 60% 為維持性
    ga = financials.get('ga_expense', 0)
    byproduct = financials.get('byproduct_credits', 0)

    if production_oz <= 0:
        return None

    aisc = (operating_cost + sustaining_capex + ga - byproduct) / production_oz
    return aisc
```

## Step 5: 加拿大公司（SEDAR+）

```python
def fetch_sedar_filing(issuer_name: str):
    """
    從 SEDAR+ 抓取加拿大公司年報

    注意：SEDAR+ 需要 Selenium 模擬瀏覽器
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 搜尋公司
        driver.get(f"https://www.sedarplus.ca/csa-party/records/search")
        # ... 填寫搜尋表單
        # ... 下載 MD&A PDF

    finally:
        driver.quit()
```

## Step 6: 快取策略

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

class DataCache:
    """數據快取管理"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def is_fresh(self, key: str, max_age_hours: int = 24) -> bool:
        path = self._cache_path(key)
        if not path.exists():
            return False

        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=max_age_hours)

    def get(self, key: str):
        if not self.is_fresh(key):
            return None
        with open(self._cache_path(key)) as f:
            return json.load(f)

    def set(self, key: str, data):
        with open(self._cache_path(key), 'w') as f:
            json.dump(data, f, indent=2, default=str)


# 使用範例
cache = DataCache()

# 財報快取 7 天（季報頻率）
if not cache.is_fresh(f"sec_{ticker}", max_age_hours=24*7):
    data = fetch_sec_xbrl(cik, ticker)
    cache.set(f"sec_{ticker}", data)
else:
    data = cache.get(f"sec_{ticker}")
```

## Step 7: 防偵測策略

參考 `thoughts/shared/guide/design-human-like-crawler.md`：

```python
import random
import time

# 隨機延遲
def random_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

# User-Agent 輪換
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
]

def get_random_ua():
    return random.choice(USER_AGENTS)
```

</process>

<success_criteria>
此工作流完成時應：

- [ ] 價格數據已從 yfinance 取得
- [ ] ETF 持股已從官方/N-PORT/手動來源取得
- [ ] 財報數據已從 SEC EDGAR XBRL API 取得
- [ ] AISC 已從 MD&A 抽取或 proxy 回算
- [ ] 數據已快取以避免重複抓取
- [ ] 爬蟲已設定防偵測策略
- [ ] 數據來源已標註（aisc_method、data_source）
</success_criteria>
