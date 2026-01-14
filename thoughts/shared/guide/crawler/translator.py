"""
新聞翻譯模組

使用 deep-translator GoogleTranslator 將英文新聞翻譯為繁體中文。

主要功能：
- 英文到繁體中文（zh-TW）翻譯
- 指數退避重試機制（處理速率限制和網路錯誤）
- 降級策略（翻譯失敗時返回原文）
- 單例模式全域翻譯器實例
"""

from typing import Optional
import time
import random
from loguru import logger
from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    TooManyRequests,
    RequestError,
    NotValidLength,
    TranslationNotFound
)


class NewsTranslator:
    """
    新聞翻譯器

    使用 Google Translate（透過 deep-translator）翻譯新聞為繁體中文。

    功能：
    - 自動偵測來源語言（通常為英文）
    - 翻譯為繁體中文（zh-TW）
    - 速率限制和網路錯誤自動重試
    - 翻譯失敗時可選擇降級回原文
    """

    def __init__(
        self,
        source_lang: str = 'auto',
        target_lang: str = 'zh-TW',
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        """
        初始化翻譯器

        參數:
            source_lang: 來源語言（預設 'auto' 自動檢測）
            target_lang: 目標語言（預設 'zh-TW' 繁體中文）
            max_retries: 最大重試次數（預設 3）
            base_delay: 初始重試延遲（秒，預設 1.0）
            max_delay: 最大重試延遲（秒，預設 10.0）
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        # 初始化翻譯器
        self.translator = GoogleTranslator(
            source=source_lang,
            target=target_lang
        )

        logger.info(f"翻譯器初始化完成：{source_lang} -> {target_lang}")

    def translate(self, text: str, fallback_to_original: bool = True) -> str:
        """
        翻譯文本

        參數:
            text: 要翻譯的文本（英文）
            fallback_to_original: 失敗時是否降級回原文（預設 True）

        回傳:
            翻譯後的文本（繁體中文），失敗時返回原文（若 fallback_to_original=True）

        範例:
            >>> translator = NewsTranslator()
            >>> result = translator.translate("Gold prices surge")
            >>> print(result)
            黃金價格飆升
        """
        if not text or not text.strip():
            return text

        # 執行翻譯（帶重試機制）
        try:
            translated = self._translate_with_retry(text)
            logger.debug(f"翻譯成功：{text[:50]}... -> {translated[:50]}...")
            return translated

        except Exception as e:
            logger.error(f"翻譯失敗：{e}")

            if fallback_to_original:
                logger.warning("降級回英文原文")
                return text
            else:
                raise

    def _translate_with_retry(self, text: str) -> str:
        """
        使用指數退避重試機制翻譯

        參數:
            text: 要翻譯的文本

        回傳:
            翻譯後的文本

        例外:
            TooManyRequests: 超過速率限制且重試失敗
            RequestError: 請求錯誤且重試失敗
            NotValidLength: 文本長度無效（不重試）
            TranslationNotFound: 翻譯未找到（不重試）
            Exception: 其他未知錯誤
        """
        for attempt in range(self.max_retries + 1):
            try:
                # 執行翻譯
                translated = self.translator.translate(text)

                if attempt > 0:
                    logger.info(f"翻譯成功（重試 {attempt} 次後）")

                return translated

            except TooManyRequests:
                if attempt == self.max_retries:
                    logger.error(f"翻譯速率限制，重試 {self.max_retries} 次後仍失敗")
                    raise

                # 計算延遲（指數退避 + 隨機抖動）
                delay = self._calculate_backoff_delay(attempt)
                logger.warning(
                    f"翻譯速率限制，{delay:.2f} 秒後重試 "
                    f"（第 {attempt + 1}/{self.max_retries} 次）"
                )
                time.sleep(delay)

            except RequestError as e:
                if attempt == self.max_retries:
                    logger.error(f"翻譯請求錯誤（{e}），重試 {self.max_retries} 次後仍失敗")
                    raise

                delay = self._calculate_backoff_delay(attempt)
                logger.warning(
                    f"翻譯請求錯誤（{e}），{delay:.2f} 秒後重試 "
                    f"（第 {attempt + 1}/{self.max_retries} 次）"
                )
                time.sleep(delay)

            except NotValidLength as e:
                # 文本長度無效，不重試
                logger.error(f"文本長度無效：{e}")
                raise

            except TranslationNotFound as e:
                # 翻譯未找到，不重試
                logger.error(f"翻譯未找到：{e}")
                raise

            except Exception as e:
                # 未知錯誤，記錄並拋出
                logger.error(f"翻譯發生未知錯誤：{e}")
                raise

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        計算指數退避延遲時間

        使用公式：delay = min(base_delay * (2 ^ attempt), max_delay) * jitter
        其中 jitter 為 0.5 ~ 1.5 之間的隨機數

        參數:
            attempt: 當前重試次數（從 0 開始）

        回傳:
            延遲時間（秒）

        範例:
            attempt=0: 1.0 * (2^0) * jitter = 0.5~1.5 秒
            attempt=1: 1.0 * (2^1) * jitter = 1.0~3.0 秒
            attempt=2: 1.0 * (2^2) * jitter = 2.0~6.0 秒
        """
        # 指數退避：delay = base_delay * (2 ^ attempt)
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)

        # 添加隨機抖動（0.5 ~ 1.5 倍）
        jitter = 0.5 + random.random()
        delay = delay * jitter

        return delay


# 全域翻譯器實例（單例模式）
_global_translator: Optional[NewsTranslator] = None


def get_translator(
    target_lang: str = 'zh-TW',
    max_retries: int = 3,
    **kwargs
) -> NewsTranslator:
    """
    取得全域翻譯器實例（單例模式）

    參數:
        target_lang: 目標語言（預設 zh-TW）
        max_retries: 最大重試次數（預設 3）
        **kwargs: 其他 NewsTranslator 參數

    回傳:
        NewsTranslator 實例

    範例:
        >>> translator = get_translator()
        >>> result = translator.translate("Hello World")
        >>> print(result)
        你好世界
    """
    global _global_translator

    if _global_translator is None:
        _global_translator = NewsTranslator(
            target_lang=target_lang,
            max_retries=max_retries,
            **kwargs
        )

    return _global_translator
