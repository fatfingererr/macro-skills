<overview>
Google Trends ATH Detector 專用數據來源指南。本技能使用 Selenium 模擬真人瀏覽器行為抓取 Google Trends 數據。
</overview>

<google_trends>
**Google Trends 數據**

| 項目     | 說明                       |
|----------|----------------------------|
| 官網     | https://trends.google.com  |
| 擷取方式 | Selenium + Chrome headless |
| 數據類型 | 相對搜尋指數（0-100）      |
| 更新頻率 | 接近即時（2-3 天延遲）     |
| 歷史數據 | 2004 年至今                |
</google_trends>

<data_types>
**可取得的數據類型**

| 數據類型           | API 端點        | 說明                        |
|--------------------|-----------------|-----------------------------|
| Interest over time | multiline       | 搜尋趨勢時間序列            |
| Related queries    | relatedsearches | 相關搜尋詞（Top 與 Rising） |
| Related topics     | relatedsearches | 相關主題                    |
| Interest by region | comparedgeo     | 地區分布                    |
</data_types>

<selenium_approach>
**Selenium 爬取方式（本技能使用）**

本技能的 `scripts/trend_fetcher.py` 使用 Selenium 模擬真人瀏覽器行為：

**安裝依賴：**

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

**基本使用：**

```python
from scripts.trend_fetcher import fetch_trends, analyze_ath

# 抓取數據（Selenium 自動處理 session 和 tokens）
data = fetch_trends(
    topic="Health Insurance",
    geo="US",
    timeframe="2004-01-01 2025-12-31"
)

# ATH 分析
result = analyze_ath(data, threshold=2.5)
```

**優點：**
- 模擬真人瀏覽器，避免被偵測
- 自動處理 JavaScript 渲染
- 內建防偵測策略
- 自動管理 ChromeDriver 版本
</selenium_approach>

<anti_detection_strategy>
**防偵測策略**

本技能實現以下防偵測措施（基於 design-human-like-crawler.md）：

| 策略                | 實作                                            | 效果               |
|---------------------|-------------------------------------------------|--------------------|
| 移除 webdriver 標記 | `--disable-blink-features=AutomationControlled` | 防止 JS 偵測       |
| 隨機 User-Agent     | 5 種瀏覽器 UA 輪換                              | 避免固定 UA 被識別 |
| 隨機延遲            | 0.5-2 秒 + 3-5 秒頁面等待                       | 模擬人類行為       |
| 禁用自動化擴展      | `excludeSwitches: ['enable-automation']`        | 移除 Chrome 痕跡   |
| 先訪問首頁          | 建立正常 session                                | 避免直接 API 請求  |

**User-Agent 池：**

```python
USER_AGENTS = [
    # Windows Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    # macOS Chrome
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    # Windows Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101...',
    # macOS Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...',
    # Linux Chrome
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...'
]
```

**Chrome 配置：**

```python
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

# 核心防偵測設定
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
```
</anti_detection_strategy>

<crawl_flow>
**爬取流程**

```
┌─────────────────────────────────────────────────────────────┐
│                     爬蟲流程總覽                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 請求前準備                                               │
│     ├─ 隨機延遲 (0.5-2 秒)                                  │
│     ├─ 隨機選擇 User-Agent                                  │
│     └─ 配置瀏覽器選項 (移除自動化標記)                       │
│                                                              │
│  2. Session 建立                                             │
│     ├─ 先訪問 trends.google.com 首頁                        │
│     ├─ 等待 cookies 建立 (2-3 秒)                           │
│     └─ 瀏覽器保持同一 session                               │
│                                                              │
│  3. API 請求                                                 │
│     ├─ 訪問 /api/explore 取得 widget tokens                 │
│     ├─ 訪問 /api/widgetdata/multiline 取得時間序列          │
│     └─ （可選）訪問 /api/widgetdata/relatedsearches         │
│                                                              │
│  4. 數據解析                                                 │
│     ├─ 移除 XSS 保護前綴 ")]}'\\n"                          │
│     ├─ JSON 解析                                             │
│     └─ 提取 timelineData                                    │
│                                                              │
│  5. 清理                                                     │
│     └─ driver.quit() 關閉瀏覽器                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
</crawl_flow>

<topic_vs_keyword>
**Topic Entity vs Search Term**

Google Trends 支援兩種查詢方式：

| 類型         | 說明                 | 優點                   | 缺點               |
|--------------|----------------------|------------------------|--------------------|
| Topic Entity | Knowledge Graph 實體 | 避免歧義、涵蓋語言變體 | 部分主題無對應實體 |
| Search Term  | 純文字關鍵字         | 精確匹配               | 可能錯過變體       |

**範例：**
- "Apple" 作為 Search Term → 包含水果和公司
- "Apple" 作為 Topic (Tech company) → 僅限蘋果公司

**如何找 Topic Entity：**
1. 在 trends.google.com 搜尋關鍵字
2. 點選自動完成建議中帶有分類描述的項目
3. URL 中的 mid 參數即為 Topic Entity ID
</topic_vs_keyword>

<timeframe_formats>
**時間範圍格式**

```python
# 絕對時間範圍
"2004-01-01 2025-12-31"  # YYYY-MM-DD YYYY-MM-DD

# 相對時間範圍
"today 5-y"              # 過去 5 年
"today 12-m"             # 過去 12 個月
"today 3-m"              # 過去 3 個月
"now 7-d"                # 過去 7 天
"now 1-H"                # 過去 1 小時
```

**粒度自動選擇：**

| 時間範圍      | 自動粒度 |
|---------------|----------|
| < 7 天        | 小時     |
| 7 天 - 9 個月 | 日       |
| 9 個月 - 5 年 | 週       |
| > 5 年        | 月       |
</timeframe_formats>

<geo_codes>
**常用地區代碼**

| 代碼  | 地區     |
|-------|----------|
| (空)  | 全球     |
| US    | 美國     |
| US-CA | 美國加州 |
| GB    | 英國     |
| DE    | 德國     |
| JP    | 日本     |
| TW    | 台灣     |
| CN    | 中國     |
| HK    | 香港     |
| SG    | 新加坡   |

完整列表見 Google Trends 網站的地區選擇器。
</geo_codes>

<rate_limits>
**速率限制與建議**

| 情況           | 限制        | 建議                    |
|----------------|-------------|-------------------------|
| 正常使用       | ~10 req/min | 每次請求間隔 1-3 秒     |
| 被偵測為機器人 | 429 錯誤    | 使用 VPN/代理、增加延遲 |
| 長時間大量抓取 | 可能被封鎖  | 分散請求時間、使用多 IP |

**最佳實踐：**
1. 模擬瀏覽器行為（Selenium + 防偵測配置）
2. 請求間加入隨機延遲（1-3 秒）
3. 先訪問首頁再進行 API 請求
4. 若被封鎖，等待 24 小時或更換 IP
5. 使用 `--no-related` 減少請求數量
</rate_limits>

<related_queries_guide>
**Related Queries 解讀指南**

| 類型     | 說明                 | 用途                   |
|----------|----------------------|------------------------|
| Top      | 最常被搜尋的相關詞   | 了解主要關聯概念       |
| Rising   | 上升幅度最大的相關詞 | 識別新興趨勢與驅動因素 |
| Breakout | 上升超過 5000%       | 全新出現的高熱度關鍵詞 |

**範例解讀：**
- Rising: "ACA enrollment deadline +450%" → 投保截止日驅動搜尋
- Breakout: "new health law" → 新政策引發關注
- Top: "health insurance plans" → 常態性搜尋需求
</related_queries_guide>

<troubleshooting>
**常見問題處理**

**問題 1：抓取失敗 / 被封鎖**

```bash
# 使用 debug 模式查看問題
python scripts/trend_fetcher.py --topic "test" --debug --no-headless
```

**問題 2：ChromeDriver 版本不匹配**

```bash
# webdriver-manager 會自動下載匹配版本
# 若仍有問題，嘗試更新：
pip install --upgrade webdriver-manager
```

**問題 3：Linux/Docker 環境**

```bash
# 確保安裝必要依賴
apt-get update && apt-get install -y \
    chromium-browser \
    chromium-chromedriver
```

**問題 4：記憶體洩漏**

```python
# 確保 driver 正確關閉
finally:
    if driver:
        driver.quit()  # 使用 quit() 而非 close()
```
</troubleshooting>

<alternative_attention_proxies>
**輔助參考資料（可選）**

若需進一步驗證 Google Trends 訊號，可參考以下公開資料：

| 來源                | 網址                          | 用途             |
|---------------------|-------------------------------|------------------|
| Wikipedia Pageviews | https://pageviews.wmcloud.org | 驗證特定主題熱度 |
| Google News         | https://news.google.com       | 搜尋相關新聞事件 |
| Reddit              | https://www.reddit.com        | 社群討論熱度     |

**注意：** 這些資料僅供手動參考驗證，本技能不自動抓取。
</alternative_attention_proxies>
