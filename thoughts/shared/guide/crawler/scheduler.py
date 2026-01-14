"""
爬蟲定時任務管理模組

負責啟動和管理新聞爬蟲的定時任務。
"""

from typing import Optional, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from telegram.ext import Application
from datetime import datetime
import discord

from .config import CrawlerConfig
from .news_crawler import NewsCrawler
from .translator import get_translator


class CrawlerScheduler:
    """
    爬蟲定時任務管理器

    使用 APScheduler 管理爬蟲的定時執行。
    """

    def __init__(
        self,
        config: CrawlerConfig,
        telegram_app: Optional[Application] = None,
        discord_bot: Optional[Any] = None
    ):
        """
        初始化調度器

        參數:
            config: 爬蟲配置
            telegram_app: Telegram Application 實例（用於發送通知）
            discord_bot: Discord Bot 實例（用於發送通知）
        """
        self.config = config
        self.telegram_app = telegram_app
        self.discord_bot = discord_bot
        self.crawler = NewsCrawler(config)
        self.scheduler = AsyncIOScheduler()

        logger.info("爬蟲調度器初始化完成")

    async def _crawl_and_notify(self):
        """
        爬取新聞並發送通知
        """
        try:
            # 執行爬取
            saved_news = await self.crawler.crawl()

            # 發送 Telegram 通知
            if saved_news and self.telegram_app and self.config.telegram_notify_groups:
                await self._send_telegram_notifications(saved_news)

            # 發送 Discord 通知
            if saved_news and self.discord_bot:
                await self._send_discord_notifications(saved_news)

        except Exception as e:
            logger.exception(f"爬蟲執行失敗：{e}")

    async def _send_telegram_notifications(self, saved_news: list):
        """
        發送 Telegram 通知

        參數:
            saved_news: 已保存的新聞列表
        """
        if not self.telegram_app or not self.telegram_app.bot:
            logger.warning("Telegram app 未正確初始化，跳過發送通知")
            return

        for news in saved_news:
            # 格式化訊息
            message = self._format_news_message(news)

            # 發送到所有配置的群組
            for group_id in self.config.telegram_notify_groups:
                try:
                    await self.telegram_app.bot.send_message(
                        chat_id=group_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"已發送通知到群組 {group_id}")

                except Exception as e:
                    logger.error(f"發送通知到群組 {group_id} 失敗：{e}")

    def _format_news_message(self, news: dict) -> str:
        """
        格式化新聞訊息

        參數:
            news: 新聞資料

        回傳:
            格式化後的 Markdown 訊息
        """
        commodity = news['commodity']
        news_id = news['news_id']
        text = news['text']  # 英文原文
        # time = news.get('time', 'N/A')  # 保留供未來使用

        # ========== 新增：根據配置決定是否翻譯 ==========
        if self.config.enable_translation:
            try:
                # 取得翻譯器實例
                translator = get_translator(
                    target_lang=self.config.translation_target_lang,
                    max_retries=self.config.translation_max_retries
                )

                # 翻譯新聞文本（失敗時自動降級回原文）
                translated_text = translator.translate(text, fallback_to_original=True)

                logger.debug(
                    f"新聞翻譯成功：{commodity} (ID: {news_id}), "
                    f"{len(text)} 字元 -> {len(translated_text)} 字元"
                )

            except Exception as e:
                # 翻譯失敗，降級回原文
                logger.error(f"翻譯失敗（{commodity}, ID: {news_id}），使用原文：{e}")
                translated_text = text
        else:
            # 未啟用翻譯，直接使用原文
            translated_text = text
            logger.debug(f"翻譯已停用，使用原文：{commodity} (ID: {news_id})")
        # ================================================

        # 限制文本長度（Telegram 單則訊息最多 4096 字元）
        max_length = 3000
        if len(translated_text) > max_length:
            translated_text = translated_text[:max_length] + "..."

        message = (
            f"**最新消息**\n"
            f"{translated_text}\n\n"  # 使用翻譯後的文本
        )

        return message

    def start(self):
        """
        啟動定時任務
        """
        if not self.config.enabled:
            logger.info("爬蟲已停用（CRAWLER_ENABLED=false），不啟動定時任務")
            return

        # 計算 jitter（隨機化範圍）
        jitter = self.config.interval_jitter_seconds

        # 新增任務
        self.scheduler.add_job(
            self._crawl_and_notify,
            trigger=IntervalTrigger(
                minutes=self.config.crawl_interval_minutes,
                jitter=jitter
            ),
            id='news_crawler',
            name='商品新聞爬蟲',
            replace_existing=True
        )

        # 啟動調度器
        self.scheduler.start()

        logger.info(
            f"爬蟲定時任務已啟動：每 {self.config.crawl_interval_minutes} 分鐘 "
            f"(±{jitter} 秒) 執行一次"
        )

    def stop(self):
        """
        停止定時任務
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("爬蟲定時任務已停止")

    async def _send_discord_notifications(self, saved_news: list):
        """
        發送 Discord 通知

        參數:
            saved_news: 已保存的新聞列表
        """
        for news in saved_news:
            commodity = news['commodity']
            title = news.get('title', '')
            content = news.get('content', '')
            time_str = news.get('time', '')

            # 翻譯標題和內容（若啟用）
            if self.config.enable_translation:
                try:
                    translator = get_translator(
                        target_lang=self.config.translation_target_lang,
                        max_retries=self.config.translation_max_retries
                    )
                    translated_title = translator.translate(title, fallback_to_original=True) if title else ''
                    translated_content = translator.translate(content, fallback_to_original=True) if content else ''
                except Exception as e:
                    logger.error(f"翻譯失敗，使用原文：{e}")
                    translated_title = title
                    translated_content = content
            else:
                translated_title = title
                translated_content = content

            # 限制內容長度
            if len(translated_content) > 4096:
                translated_content = translated_content[:4096] + "..."

            # 建立 Embed（標題為新聞標題，內容為新聞正文）
            embed = discord.Embed(
                title=f"📰 {translated_title}" if translated_title else f"📰 {commodity} 新聞",
                description=translated_content,
                color=self._get_commodity_color(commodity),
                timestamp=datetime.now()
            )

            embed.add_field(name="來源", value="Trading Economics", inline=True)
            embed.add_field(name="發布時間", value=time_str if time_str else "剛剛", inline=True)

            # 安全取得 icon_url
            icon_url = None
            if self.discord_bot and self.discord_bot.user and self.discord_bot.user.avatar:
                icon_url = self.discord_bot.user.avatar.url

            embed.set_footer(
                text="Trading Economics • Chip Whisperer",
                icon_url=icon_url
            )

            # 發送到所有配置的伺服器
            if not self.discord_bot or not hasattr(self.discord_bot, 'config'):
                logger.warning("Discord bot 未正確初始化，跳過發送通知")
                return

            for guild_id in self.discord_bot.config.discord_guild_ids:
                guild = self.discord_bot.get_guild(guild_id)
                if guild:
                    try:
                        # 取得目標頻道
                        from src.bot.discord_handlers import get_target_channel
                        channel = await get_target_channel(self.discord_bot, guild, commodity)

                        if channel:
                            await channel.send(embed=embed)
                            logger.info(f"已發送 Discord 通知到伺服器 {guild.name} 的頻道 {channel.name}")
                        else:
                            logger.warning(f"找不到頻道：{commodity}")

                    except Exception as e:
                        logger.error(f"發送 Discord 通知失敗：{e}")

    def _get_commodity_color(self, commodity: str) -> discord.Color:
        """
        根據商品分類回傳顏色
        """
        color_map = {
            # 貴金屬
            'Gold': discord.Color.gold(),
            'Silver': discord.Color.light_grey(),
            'Platinum': discord.Color.dark_grey(),
            'Palladium': discord.Color.lighter_grey(),

            # 加密貨幣
            'Bitcoin': discord.Color.orange(),
            'Ethereum': discord.Color.blue(),
            'Solana': discord.Color.purple(),

            # 能源
            'Wti': discord.Color.dark_orange(),
            'Brent': discord.Color.dark_orange(),

            # 基本金屬
            'Copper': discord.Color.dark_red(),
            'Aluminium': discord.Color.light_grey(),
            'Zinc': discord.Color.greyple(),
            'Lead': discord.Color.dark_grey(),

            # 農產品（綠色系）
            'Cocoa': discord.Color.green(),
            'Coffee': discord.Color.dark_green(),
            'Corn': discord.Color.green(),
            'Cotton': discord.Color.light_grey(),
            'Sbean': discord.Color.green(),
            'Sugar': discord.Color.lighter_grey(),
            'Wheat': discord.Color.gold(),
        }

        return color_map.get(commodity, discord.Color.blue())
