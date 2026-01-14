# 模擬人類行為的爬蟲設計指南

專業爬蟲實作經驗整理，適用於設計更多避免 API、模擬人類行為的爬蟲工具，以 Trading Economics 為例。

---

## 目錄

1. [核心架構](#核心架構)
2. [技術棧選擇](#技術棧選擇)
3. [防偵測策略](#防偵測策略)
4. [完整實作流程](#完整實作流程)
5. [程式碼模板](#程式碼模板)
6. [常見問題處理](#常見問題處理)

---

## 核心架構

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
│  2. 頁面抓取 (Selenium)                                      │
│     ├─ 啟動 Chrome (headless)                               │
│     ├─ 載入目標 URL                                         │
│     ├─ 等待動態內容載入 (WebDriverWait)                     │
│     ├─ 額外等待 JS 執行 (3 秒)                              │
│     └─ 取得完整 HTML                                        │
│                                                              │
│  3. 內容解析 (BeautifulSoup)                                │
│     ├─ 多層備用選擇器策略                                   │
│     ├─ 提取目標資料                                         │
│     └─ 失敗時保存 debug HTML                                │
│                                                              │
│  4. 資料處理與儲存                                           │
│     ├─ 資料映射/分類                                        │
│     ├─ 重複檢測                                             │
│     └─ 持久化儲存                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 技術棧選擇

### 必要套件

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

| 套件                | 用途              | 說明                            |
|---------------------|-------------------|---------------------------------|
| `selenium`          | 瀏覽器自動化      | 執行 JavaScript、模擬真實瀏覽器 |
| `webdriver-manager` | ChromeDriver 管理 | 自動下載匹配版本的 driver       |
| `beautifulsoup4`    | HTML 解析         | 簡單易用的 DOM 操作             |
| `lxml`              | 解析器            | 高效能、容錯能力強              |
| `loguru`            | 日誌              | 方便調試                        |

### 為何選擇 Selenium 而非 requests/httpx？

| 方案           | 優點                                | 缺點                  | 適用場景              |
|----------------|-------------------------------------|-----------------------|-----------------------|
| **Selenium**   | 執行 JS、模擬真實瀏覽器、繞過反爬蟲 | 資源消耗大、速度較慢  | **動態網站、JS 渲染** |
| requests/httpx | 輕量、快速                          | 無法執行 JS、易被偵測 | 靜態 HTML 網站        |
| Playwright     | 現代化、更好的 API                  | 學習曲線              | 需要更多瀏覽器支援    |

---

## 防偵測策略

### 1. Chrome 選項配置

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()

# 基本設定
chrome_options.add_argument('--headless')               # 無頭模式
chrome_options.add_argument('--no-sandbox')             # Linux/Docker 相容
chrome_options.add_argument('--disable-dev-shm-usage')  # 避免記憶體問題
chrome_options.add_argument('--disable-gpu')            # headless 建議關閉

# 🔴 核心防偵測設定
chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 移除 navigator.webdriver 標記
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 移除自動化提示
chrome_options.add_experimental_option('useAutomationExtension', False)  # 禁用自動化擴展
```

### 2. User-Agent 輪換

```python
import random

USER_AGENTS = [
    # Windows Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # macOS Chrome
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Windows Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    # macOS Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    # Linux Chrome
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# 每次請求隨機選擇
user_agent = random.choice(USER_AGENTS)
chrome_options.add_argument(f'user-agent={user_agent}')
```

### 3. 隨機延遲

```python
import asyncio
import random

# 請求前隨機延遲 (模擬人類思考時間)
delay = random.uniform(0.5, 2.0)
await asyncio.sleep(delay)
```

### 4. 定時任務加入 Jitter

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

# 每 5 分鐘執行，±15 秒隨機偏移
scheduler.add_job(
    crawl_function,
    trigger=IntervalTrigger(minutes=5, jitter=15),
    id='crawler_job'
)
```

### 防偵測策略總結

| 策略                       | 效果               | 優先級  |
|----------------------------|--------------------|---------|
| 移除 `navigator.webdriver` | 核心，防止 JS 偵測 | 🔴 必要 |
| 隨機 User-Agent            | 避免固定 UA 被識別 | 🔴 必要 |
| 請求前隨機延遲             | 模擬人類行為       | 🔴 必要 |
| 禁用自動化擴展             | 移除 Chrome 痕跡   | 🟡 建議 |
| 定時任務 Jitter            | 避免固定間隔       | 🟡 建議 |

---

## 完整實作流程

### 步驟 1：建立配置類

```python
# config.py
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class CrawlerConfig:
    """爬蟲配置"""
    target_url: str                           # 目標 URL
    crawl_interval_minutes: int = 5           # 爬取間隔 (分鐘)
    interval_jitter_seconds: int = 15         # 隨機偏移 (秒)
    output_dir: str = 'data'                  # 輸出目錄
    enabled: bool = True                      # 是否啟用

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        """從環境變數載入配置"""
        return cls(
            target_url=os.getenv('CRAWLER_URL', ''),
            crawl_interval_minutes=int(os.getenv('CRAWLER_INTERVAL', '5')),
            interval_jitter_seconds=int(os.getenv('CRAWLER_JITTER', '15')),
            output_dir=os.getenv('CRAWLER_OUTPUT_DIR', 'data'),
            enabled=os.getenv('CRAWLER_ENABLED', 'true').lower() == 'true'
        )
```

### 步驟 2：建立爬蟲核心類

```python
# crawler.py
from typing import Optional, List, Dict
import random
import asyncio
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from loguru import logger

from config import CrawlerConfig

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    # ... 更多 UA
]


class BaseCrawler:
    """爬蟲基礎類"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        logger.info(f"爬蟲初始化完成: {config.target_url}")

    async def fetch_page(self) -> Optional[str]:
        """抓取頁面 (非同步包裝)"""
        # 隨機延遲
        delay = random.uniform(0.5, 2.0)
        logger.debug(f"請求前延遲 {delay:.2f} 秒")
        await asyncio.sleep(delay)

        # 在獨立執行緒執行 Selenium (避免阻塞事件循環)
        return await asyncio.to_thread(self._fetch_page_sync)

    def _fetch_page_sync(self) -> Optional[str]:
        """同步的 Selenium 操作"""
        driver = None
        try:
            # 配置 Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 隨機 UA
            user_agent = random.choice(USER_AGENTS)
            chrome_options.add_argument(f'user-agent={user_agent}')

            # 啟動瀏覽器
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(60)

            # 載入頁面
            logger.info(f"正在抓取: {self.config.target_url}")
            driver.get(self.config.target_url)

            # 等待頁面載入 (子類可覆寫此方法)
            self._wait_for_page_load(driver)

            # 額外等待 JS 執行
            time.sleep(3)

            return driver.page_source

        except Exception as e:
            logger.error(f"抓取失敗: {e}")
            return None

        finally:
            if driver:
                driver.quit()

    def _wait_for_page_load(self, driver):
        """等待頁面載入 (子類可覆寫)"""
        wait = WebDriverWait(driver, 20)

        # 預設等待 body 載入
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            logger.warning("等待頁面載入超時")

    def parse(self, html: str) -> List[Dict]:
        """解析 HTML (子類必須實作)"""
        raise NotImplementedError("子類必須實作 parse 方法")

    async def crawl(self) -> List[Dict]:
        """執行完整爬取流程"""
        # 1. 抓取
        html = await self.fetch_page()
        if not html:
            return []

        # 2. 解析
        data = self.parse(html)

        # 3. 後處理 (子類可覆寫)
        return await self.post_process(data)

    async def post_process(self, data: List[Dict]) -> List[Dict]:
        """後處理 (子類可覆寫)"""
        return data
```

### 步驟 3：建立特定網站爬蟲

```python
# example_crawler.py
from typing import List, Dict
from bs4 import BeautifulSoup
from loguru import logger

from crawler import BaseCrawler


class ExampleSiteCrawler(BaseCrawler):
    """範例網站爬蟲"""

    def _wait_for_page_load(self, driver):
        """覆寫等待邏輯"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(driver, 20)

        # 嘗試多個可能的選擇器
        selectors = [
            (By.CLASS_NAME, "main-content"),
            (By.ID, "content"),
            (By.TAG_NAME, "article"),
        ]

        for by, value in selectors:
            try:
                wait.until(EC.presence_of_element_located((by, value)))
                logger.info(f"頁面已載入 (找到: {value})")
                return
            except:
                continue

        logger.warning("未找到預期元素，繼續處理")

    def parse(self, html: str) -> List[Dict]:
        """解析 HTML"""
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # 🔴 多層備用選擇器策略
        items = []

        # 第一優先
        items = soup.select('div.item-class')
        if items:
            logger.info(f"使用選擇器 'div.item-class' 找到 {len(items)} 項")

        # 備用 1
        if not items:
            items = soup.select('article.post')
            if items:
                logger.info(f"使用備用選擇器 'article.post' 找到 {len(items)} 項")

        # 備用 2
        if not items:
            items = soup.select('li.list-item')
            if items:
                logger.info(f"使用備用選擇器 'li.list-item' 找到 {len(items)} 項")

        # 全部失敗 -> 保存 debug HTML
        if not items:
            logger.warning("所有選擇器都失敗")
            self._save_debug_html(html)
            return results

        # 解析每個項目
        for item in items:
            try:
                title = item.select_one('h2, .title')
                content = item.select_one('p, .content')

                if title:
                    results.append({
                        'title': title.get_text(strip=True),
                        'content': content.get_text(strip=True) if content else ''
                    })
            except Exception as e:
                logger.warning(f"解析項目失敗: {e}")
                continue

        return results

    def _save_debug_html(self, html: str):
        """保存 debug HTML"""
        try:
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.warning("已保存 debug_page.html，請手動檢查選擇器")
        except Exception as e:
            logger.error(f"保存 debug 檔案失敗: {e}")
```

### 步驟 4：使用爬蟲

```python
# main.py
import asyncio
from config import CrawlerConfig
from example_crawler import ExampleSiteCrawler


async def main():
    config = CrawlerConfig(
        target_url='https://example.com/news',
        crawl_interval_minutes=5
    )

    crawler = ExampleSiteCrawler(config)
    results = await crawler.crawl()

    for item in results:
        print(f"標題: {item['title']}")
        print(f"內容: {item['content'][:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 程式碼模板

### 快速開始模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用爬蟲模板
用法: 修改 TARGET_URL 和 parse() 方法中的選擇器
"""

import asyncio
import random
import time
from typing import Optional, List, Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ========== 配置區域 (修改這裡) ==========
TARGET_URL = 'https://example.com/page'
WAIT_SELECTOR = (By.CLASS_NAME, 'content')  # 等待此元素出現
ITEM_SELECTOR = 'div.item'                   # 項目選擇器
TITLE_SELECTOR = 'h2'                        # 標題選擇器
CONTENT_SELECTOR = 'p'                       # 內容選擇器
# =========================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


async def fetch_page() -> Optional[str]:
    """抓取頁面"""
    # 隨機延遲
    await asyncio.sleep(random.uniform(0.5, 2.0))
    return await asyncio.to_thread(_fetch_sync)


def _fetch_sync() -> Optional[str]:
    """同步抓取"""
    driver = None
    try:
        # Chrome 配置
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')

        # 啟動
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)

        # 載入
        driver.get(TARGET_URL)

        # 等待
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(WAIT_SELECTOR)
        )
        time.sleep(3)

        return driver.page_source

    except Exception as e:
        print(f"抓取失敗: {e}")
        return None

    finally:
        if driver:
            driver.quit()


def parse(html: str) -> List[Dict]:
    """解析 HTML"""
    soup = BeautifulSoup(html, 'lxml')
    results = []

    items = soup.select(ITEM_SELECTOR)
    for item in items:
        title = item.select_one(TITLE_SELECTOR)
        content = item.select_one(CONTENT_SELECTOR)

        if title:
            results.append({
                'title': title.get_text(strip=True),
                'content': content.get_text(strip=True) if content else ''
            })

    return results


async def main():
    html = await fetch_page()
    if html:
        data = parse(html)
        for item in data:
            print(f"標題: {item['title']}")
            print(f"內容: {item['content'][:100]}...")
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 常見問題處理

### 問題 1：頁面載入不完整

**症狀**: 抓到的 HTML 內容為空或不完整

**解決方案**:
```python
# 1. 增加等待時間
time.sleep(5)  # 從 3 秒增加到 5 秒

# 2. 等待特定元素
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "target-class")))

# 3. 等待 JS 完成
wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
```

### 問題 2：被網站封鎖

**症狀**: 返回 403/429 錯誤，或顯示驗證碼

**解決方案**:
```python
# 1. 增加隨機延遲
delay = random.uniform(2.0, 5.0)  # 增加延遲範圍

# 2. 降低爬取頻率
crawl_interval_minutes = 10  # 從 5 分鐘改為 10 分鐘

# 3. 使用 undetected-chromedriver (進階)
# pip install undetected-chromedriver
import undetected_chromedriver as uc
driver = uc.Chrome()
```

### 問題 3：選擇器失效

**症狀**: 網站改版後抓不到資料

**解決方案**:
```python
# 1. 多層備用選擇器
selectors = ['div.new-class', 'div.old-class', 'article']
for selector in selectors:
    items = soup.select(selector)
    if items:
        break

# 2. 保存 debug HTML
with open('debug.html', 'w') as f:
    f.write(html)

# 3. 定期監控告警
if not items:
    send_alert("選擇器失效，請檢查網站結構")
```

### 問題 4：記憶體洩漏

**症狀**: 長時間運行後記憶體不斷增加

**解決方案**:
```python
# 確保 driver 正確關閉
finally:
    if driver:
        try:
            driver.quit()  # 使用 quit() 而非 close()
        except:
            pass
```

---

## 參考資源

- **Selenium 官方文檔**: https://www.selenium.dev/documentation/
- **BeautifulSoup 文檔**: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- **undetected-chromedriver**: https://github.com/ultrafunkamsterdam/undetected-chromedriver
- **Playwright (替代方案)**: https://playwright.dev/python/

---

## 本專案範例實作參考

| 檔案                          | 說明                             |
|-------------------------------|----------------------------------|
| `crawler/news_crawler.py`     | 範例爬蟲核心 - Trading Economics |
| `crawler/config.py`           | 配置管理                         |
| `crawler/commodity_mapper.py` | 資料映射                         |
| `crawler/news_storage.py`     | 儲存和去重                       |
| `crawler/scheduler.py`        | 定時任務調度                     |
