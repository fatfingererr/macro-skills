<overview>
Google Trend ATH Detector 使用的數據來源清單，包含主要數據（Google Trends）和驗證數據（FRED、BLS 等）。
</overview>

<google_trends>
**Google Trends 數據**

| 項目 | 說明 |
|------|------|
| 官網 | https://trends.google.com |
| Python 介面 | pytrends (https://pypi.org/project/pytrends/) |
| 替代 API | SerpAPI Google Trends API |
| 數據類型 | 相對搜尋指數（0-100） |
| 更新頻率 | 接近即時（2-3 天延遲） |
| 歷史數據 | 2004 年至今 |

**pytrends 安裝與使用：**

```bash
pip install pytrends
```

```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
pytrends.build_payload(kw_list=['Health Insurance'], geo='US', timeframe='today 5-y')

# Interest over time
df = pytrends.interest_over_time()

# Related queries
related = pytrends.related_queries()
```

**注意事項：**
- 非官方 API，可能被 rate limit
- 每次最多 5 個關鍵字
- 建議使用 proxies 避免封鎖
</google_trends>

<fred_data>
**FRED 經濟數據**

| Series ID | 名稱 | 用途 |
|-----------|------|------|
| CUSR0000SAM | Medical Care CPI | 醫療成本壓力 |
| CUSR0000SAM2 | Health Insurance CPI | 保險成本壓力 |
| CPIAUCSL | CPI All Items | 整體通膨 |
| PCEPILFE | Core PCE | 核心通膨（Fed 偏好） |
| UNRATE | Unemployment Rate | 失業率 |
| ICSA | Initial Claims | 初次申請失業救濟 |
| PAYEMS | Nonfarm Payrolls | 非農就業 |
| JTSJOL | Job Openings | 職位空缺 |
| FEDFUNDS | Federal Funds Rate | 聯邦基金利率 |
| UMCSENT | Consumer Sentiment | 消費者信心 |

**FRED API 使用：**

```python
import pandas_datareader as pdr

# 抓取 Medical Care CPI
medical_cpi = pdr.get_data_fred('CUSR0000SAM', start='2020-01-01')

# 或使用 fredapi
from fredapi import Fred
fred = Fred(api_key='YOUR_API_KEY')
data = fred.get_series('CUSR0000SAM')
```

**官網：** https://fred.stlouisfed.org
</fred_data>

<bls_data>
**BLS 勞動統計數據**

| 數據系列 | 說明 | 用途 |
|----------|------|------|
| CES Employment | 就業統計 | 行業就業變化 |
| JOLTS | 職位空缺與離職 | 勞動市場健康度 |
| CPI Detailed | CPI 細項 | 特定品類通膨 |
| Layoffs and Discharges | 裁員數據 | 就業焦慮指標 |

**官網：** https://www.bls.gov
</bls_data>

<cms_data>
**CMS 醫療保險數據**

| 數據 | 說明 | 用途 |
|------|------|------|
| Medicaid Enrollment | Medicaid 參保人數 | 政策影響追蹤 |
| Marketplace Enrollment | ACA 市場參保 | 投保季影響 |
| Medicare Enrollment | Medicare 參保 | 醫療保險覆蓋 |

**官網：** https://www.cms.gov/data-research
</cms_data>

<alternative_attention_proxies>
**替代注意力指標**

| 來源 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| Wikipedia Pageviews | 頁面瀏覽量 | 有 API、精確到日 | 僅限維基百科主題 |
| GDELT | 新聞注意力 | 涵蓋全球新聞 | 需要處理大數據 |
| Reddit/Twitter API | 社群討論量 | 即時性高 | API 限制多 |

**Wikipedia Pageviews API：**

```python
import requests

url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Health_insurance/daily/20200101/20251231"
response = requests.get(url, headers={'User-Agent': 'MacroSkills/1.0'})
data = response.json()
```
</alternative_attention_proxies>

<event_calendars>
**事件日曆來源**

| 事件類型 | 來源 | 時間點 |
|----------|------|--------|
| Open Enrollment | Healthcare.gov | 每年 11/1 - 1/15 |
| Tax Season | IRS | 每年 1/27 - 4/15 |
| Fed Meetings | Federal Reserve | FOMC 日曆 |
| Jobs Report | BLS | 每月第一個週五 |
| CPI Release | BLS | 每月中旬 |

**Open Enrollment 時間（2024-2025 範例）：**

```yaml
open_enrollment_2025:
  start: "2024-11-01"
  end: "2025-01-15"
  peak_search_period: "2024-11-01 to 2024-12-15"
```
</event_calendars>

<data_access_patterns>
**數據存取模式**

```python
class DataSourceManager:
    """統一數據來源管理"""

    def __init__(self, fred_api_key=None):
        self.fred_key = fred_api_key

    def get_google_trends(self, topic, geo, timeframe):
        from pytrends.request import TrendReq
        pytrends = TrendReq()
        pytrends.build_payload([topic], geo=geo, timeframe=timeframe)
        return pytrends.interest_over_time()

    def get_fred_series(self, series_id, start_date=None):
        from fredapi import Fred
        fred = Fred(api_key=self.fred_key)
        return fred.get_series(series_id, observation_start=start_date)

    def get_related_queries(self, topic, geo, timeframe):
        from pytrends.request import TrendReq
        pytrends = TrendReq()
        pytrends.build_payload([topic], geo=geo, timeframe=timeframe)
        return pytrends.related_queries()

    def get_wikipedia_pageviews(self, article, start, end):
        import requests
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/daily/{start}/{end}"
        response = requests.get(url, headers={'User-Agent': 'MacroSkills/1.0'})
        return response.json()
```
</data_access_patterns>

<rate_limits>
**速率限制與建議**

| 來源 | 限制 | 建議 |
|------|------|------|
| Google Trends (pytrends) | ~10 req/min | 使用 proxies、加延遲 |
| FRED API | 120 req/min | 無需特殊處理 |
| Wikipedia | 100 req/sec | 批量抓取後本地快取 |
| BLS API | 500 req/day | 每日執行、本地快取 |
</rate_limits>
