"""
爬蟲配置模組

管理爬蟲相關的配置參數。
"""

from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv


@dataclass
class CrawlerConfig:
    """
    爬蟲配置資料類別

    屬性:
        target_url: 目標網站 URL
        crawl_interval_minutes: 爬取間隔（分鐘）
        interval_jitter_seconds: 間隔隨機化範圍（秒）
        markets_dir: markets 目錄路徑
        enabled: 是否啟用爬蟲
        telegram_notify_groups: 要通知的 Telegram 群組 ID 列表
        enable_translation: 是否啟用新聞翻譯
        translation_target_lang: 翻譯目標語言
        translation_max_retries: 翻譯最大重試次數
    """

    target_url: str
    crawl_interval_minutes: int
    interval_jitter_seconds: int
    markets_dir: str
    enabled: bool
    telegram_notify_groups: List[int]

    # 翻譯相關配置
    enable_translation: bool
    translation_target_lang: str
    translation_max_retries: int

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        """
        從環境變數載入配置

        回傳:
            CrawlerConfig 實例
        """
        load_dotenv()

        return cls(
            target_url=os.getenv(
                'CRAWLER_TARGET_URL',
                'https://tradingeconomics.com/stream?c=commodity'
            ),
            crawl_interval_minutes=int(os.getenv('CRAWLER_INTERVAL_MINUTES', '5')),
            interval_jitter_seconds=int(os.getenv('CRAWLER_JITTER_SECONDS', '15')),
            markets_dir=os.getenv('MARKETS_DIR', 'markets'),
            enabled=os.getenv('CRAWLER_ENABLED', 'true').lower() in ('true', '1', 'yes'),
            telegram_notify_groups=[
                int(gid.strip())
                for gid in os.getenv('CRAWLER_NOTIFY_GROUPS', '').split(',')
                if gid.strip()
            ],

            # 翻譯配置
            enable_translation=os.getenv('CRAWLER_ENABLE_TRANSLATION', 'true').lower() in ('true', '1', 'yes'),
            translation_target_lang=os.getenv('CRAWLER_TRANSLATION_TARGET_LANG', 'zh-TW'),
            translation_max_retries=int(os.getenv('CRAWLER_TRANSLATION_MAX_RETRIES', '3')),
        )
