"""
新聞爬蟲核心模組

負責從目標網站抓取商品新聞。
"""

from typing import List, Dict, Optional
import random
import asyncio
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .config import CrawlerConfig
from .commodity_mapper import CommodityMapper
from .news_storage import NewsStorage


# User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]


class NewsCrawler:
    """
    商品新聞爬蟲

    負責從 tradingeconomics.com 抓取商品新聞。
    """

    def __init__(self, config: CrawlerConfig):
        """
        初始化爬蟲

        參數:
            config: 爬蟲配置
        """
        self.config = config
        self.mapper = CommodityMapper(config.markets_dir)
        self.storage = NewsStorage(config.markets_dir)

        logger.info("新聞爬蟲初始化完成")

    async def fetch_page(self) -> Optional[str]:
        """
        使用 Selenium 抓取目標網頁 HTML（支援 JavaScript 動態載入）

        回傳:
            HTML 內容，失敗時回傳 None

        注意:
            Selenium 操作在獨立線程中執行，避免阻塞 Discord 心跳。
        """
        # 隨機延遲（0.5-2 秒）
        delay = random.uniform(0.5, 2.0)
        logger.debug(f"請求前延遲 {delay:.2f} 秒")
        await asyncio.sleep(delay)

        # 在獨立線程中執行 Selenium 操作，避免阻塞事件循環
        logger.info("在獨立線程中啟動 Selenium...")
        return await asyncio.to_thread(self._fetch_page_sync)

    def _fetch_page_sync(self) -> Optional[str]:
        """
        同步的 Selenium 抓取操作（在獨立線程中執行）

        回傳:
            HTML 內容，失敗時回傳 None

        注意:
            此方法包含阻塞操作，必須在獨立線程中執行。
        """
        import time

        driver = None
        try:
            # 設定 Chrome 選項
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 無頭模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 隨機 User-Agent
            user_agent = random.choice(USER_AGENTS)
            chrome_options.add_argument(f'user-agent={user_agent}')

            # 創建 WebDriver
            logger.info("正在啟動 Chrome 瀏覽器...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 設定頁面載入超時（增加到 60 秒）
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)

            # 載入頁面
            logger.info(f"正在抓取：{self.config.target_url}")
            driver.get(self.config.target_url)

            # 等待頁面載入（等待新聞列表出現）
            # 嘗試等待各種可能的元素
            logger.info("等待頁面載入...")
            wait = WebDriverWait(driver, 20)  # 增加到 20 秒

            # 嘗試等待可能的新聞容器
            selectors_to_wait = [
                (By.CLASS_NAME, "te-stream-item"),  # 最優先
                (By.ID, "stream"),
                (By.CLASS_NAME, "list-group-item"),
                (By.TAG_NAME, "li")
            ]

            page_loaded = False
            for by, value in selectors_to_wait:
                try:
                    wait.until(EC.presence_of_element_located((by, value)))
                    logger.info(f"頁面已載入（找到元素：{value}）")
                    page_loaded = True
                    break
                except:
                    logger.debug(f"等待元素 {value} 失敗，嘗試下一個...")
                    continue

            if not page_loaded:
                logger.warning("未找到預期的頁面元素，但繼續處理...")

            # 額外等待 JavaScript 執行（使用同步 sleep）
            logger.debug("等待 JavaScript 執行...")
            time.sleep(3)

            # 取得頁面 HTML
            html = driver.page_source
            logger.info("網頁抓取成功")

            return html

        except Exception as e:
            logger.error(f"網頁抓取異常：{e}")
            return None

        finally:
            # 關閉瀏覽器
            if driver:
                try:
                    driver.quit()
                    logger.debug("瀏覽器已關閉")
                except:
                    pass

    def parse_news(self, html: str) -> List[Dict[str, str]]:
        """
        解析 HTML，提取新聞列表

        ⚠️ 重要：此函式的 CSS 選擇器需要根據實際網站結構調整！

        參數:
            html: 網頁 HTML 內容

        回傳:
            新聞列表 [{'title': ..., 'content': ..., 'full_text': ..., 'time': ...}, ...]
        """
        soup = BeautifulSoup(html, 'lxml')
        news_list = []

        # ⚠️ TODO: 根據實際網站結構調整選擇器
        # 請訪問 https://tradingeconomics.com/stream?c=commodity 並使用 F12 分析 HTML
        try:
            # 嘗試多個可能的選擇器
            items = []

            # 第一次嘗試：te-stream-item (Trading Economics 實際使用的選擇器)
            items = soup.select('li.te-stream-item')
            if items:
                logger.info(f"使用選擇器 'li.te-stream-item' 找到 {len(items)} 個項目")

            # 第二次嘗試：list-group-item (備用)
            if not items:
                logger.debug("嘗試備用選擇器 'li.list-group-item'")
                items = soup.select('li.list-group-item')
                if items:
                    logger.info(f"使用選擇器 'li.list-group-item' 找到 {len(items)} 個項目")

            # 第三次嘗試：更通用的選擇器
            if not items:
                logger.debug("嘗試備用選擇器 'div.stream-item'")
                items = soup.select('div.stream-item')
                if items:
                    logger.info(f"使用選擇器 'div.stream-item' 找到 {len(items)} 個項目")

            # 第四次嘗試：基於常見 HTML 結構
            if not items:
                logger.debug("嘗試基於 article 標籤")
                items = soup.select('article')
                if items:
                    logger.info(f"使用 article 標籤找到 {len(items)} 個項目")

            if not items:
                logger.warning("所有選擇器都無法匹配新聞項目")
                logger.debug(f"HTML 前 500 字元：{html[:500]}")

                # 保存完整 HTML 供調試用
                debug_file = "debug_page.html"
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    logger.warning(f"已將完整 HTML 保存到 {debug_file} 供調試用")
                    logger.warning("請手動打開此檔案並使用瀏覽器的開發者工具（F12）檢查新聞項目的 CSS 選擇器")
                except Exception as e:
                    logger.error(f"保存調試檔案失敗：{e}")

                return news_list

            for item in items:
                try:
                    # 提取標題（Trading Economics 使用 te-stream-title 或 te-stream-title-2）
                    title_elem = item.select_one('a.te-stream-title b, a.te-stream-title-2 b')
                    if not title_elem:
                        # 備用：嘗試直接選擇 a 標籤
                        title_elem = item.select_one('a.te-stream-title, a.te-stream-title-2')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    # 提取內容（Trading Economics 使用 te-stream-item-description）
                    content_elem = item.select_one('span.te-stream-item-description')
                    content = content_elem.get_text(strip=True) if content_elem else ''

                    # 提取時間（Trading Economics 使用 te-stream-item-date）
                    time_elem = item.select_one('small.te-stream-item-date')
                    time_str = ''
                    if time_elem:
                        time_str = time_elem.get('datetime', '') or time_elem.get_text(strip=True)

                    # 組合完整文本
                    full_text = f"{title}\n{content}" if content else title

                    # 過濾條件
                    # 1. 過濾空新聞
                    if not full_text.strip():
                        logger.debug("跳過空新聞項目")
                        continue

                    # 2. 過濾通知性新聞（無詳細內容）
                    if "Commodities Updates:" in title and not content.strip():
                        logger.debug(f"跳過通知性新聞：{title[:50]}...")
                        continue

                    # 通過所有過濾條件，添加到列表
                    news_list.append({
                        'title': title,
                        'content': content,
                        'full_text': full_text,
                        'time': time_str
                    })

                except Exception as e:
                    logger.warning(f"解析單則新聞時發生錯誤：{e}")
                    continue

            logger.info(f"成功解析 {len(news_list)} 則新聞")

            # 顯示最新一則新聞的標題（限制 20 字元）
            if news_list:
                latest_title = news_list[0].get('title', '')
                if len(latest_title) > 20:
                    display_title = latest_title[:20] + "..."
                else:
                    display_title = latest_title
                logger.info(f"最新新聞：{display_title}")

        except Exception as e:
            logger.error(f"解析 HTML 時發生錯誤：{e}")

        return news_list

    async def process_and_save(
        self,
        news_list: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """
        處理新聞列表並保存

        參數:
            news_list: 解析後的新聞列表

        回傳:
            已保存的新聞列表（包含商品和 ID 資訊）
        """
        saved_news = []

        for news in news_list:
            full_text = news['full_text']
            title = news['title']

            # 提取商品
            commodity = self.mapper.extract_commodity(full_text)
            if not commodity:
                # 未匹配商品，保存到 Others/
                commodity = 'Others'
                logger.debug(f"新聞未匹配任何商品，保存到 Others/：{full_text[:50]}...")

            # 檢查重複（基於標題）
            if self.storage.check_duplicate(commodity, title):
                logger.debug(f"新聞重複，忽略：{title[:50]}...")
                continue

            # 保存新聞（傳入完整數據）
            success, news_id = self.storage.save_news(
                commodity,
                full_text,
                news_data=news  # 傳入完整新聞數據
            )

            if success:
                saved_news.append({
                    'commodity': commodity,
                    'news_id': news_id,
                    'title': news.get('title', ''),
                    'content': news.get('content', ''),
                    'text': full_text,
                    'time': news.get('time', '')
                })
                logger.info(f"新聞已保存：{commodity} ID={news_id}")

        return saved_news

    async def crawl(self) -> List[Dict[str, any]]:
        """
        執行完整的爬取流程

        回傳:
            已保存的新聞列表
        """
        logger.info("=" * 60)
        logger.info("開始爬取商品新聞")
        logger.info("=" * 60)

        # 1. 抓取網頁
        html = await self.fetch_page()
        if not html:
            logger.error("網頁抓取失敗，本次爬取結束")
            return []

        # 2. 解析新聞
        news_list = self.parse_news(html)
        if not news_list:
            logger.warning("未解析到任何新聞")
            return []

        # 3. 處理並保存
        saved_news = await self.process_and_save(news_list)

        logger.info("=" * 60)
        logger.info(f"爬取完成：共保存 {len(saved_news)} 則新聞")
        logger.info("=" * 60)

        return saved_news
