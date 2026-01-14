"""
商品名稱映射模組

提供新聞中的商品名稱與 markets/ 目錄的映射關係。
"""

from typing import Optional
from pathlib import Path
from loguru import logger


class CommodityMapper:
    """
    商品名稱映射器

    負責將新聞中的商品名稱映射到 markets/ 目錄名稱。
    """

    # 商品名稱映射表（新聞關鍵字 -> markets 目錄名）
    COMMODITY_MAP = {
        # 貴金屬
        'gold': 'Gold',
        'silver': 'Silver',
        'platinum': 'Platinum',
        'palladium': 'Palladium',

        # 能源
        'crude oil': 'Wti',
        'wti': 'Wti',
        'brent': 'Brent',
        'oil': 'Wti',  # 預設為 WTI

        # 基本金屬
        'copper': 'Copper',
        'aluminium': 'Aluminium',
        'aluminum': 'Aluminium',  # 美式拼法
        'zinc': 'Zinc',
        'lead': 'Lead',

        # 加密貨幣
        'bitcoin': 'Bitcoin',
        'btc': 'Bitcoin',
        'ethereum': 'Ethereum',
        'eth': 'Ethereum',
        'solana': 'Solana',
        'sol': 'Solana',

        # 農產品
        'cocoa': 'Cocoa',
        'coffee': 'Coffee',
        'corn': 'Corn',
        'cotton': 'Cotton',
        'soybean': 'Sbean',
        'sugar': 'Sugar',
        'wheat': 'Wheat',
    }

    def __init__(self, markets_dir: str = 'markets'):
        """
        初始化映射器

        參數:
            markets_dir: markets 目錄路徑
        """
        self.markets_dir = Path(markets_dir)
        self._load_available_commodities()

    def _load_available_commodities(self):
        """載入 markets/ 目錄下實際存在的商品"""
        if not self.markets_dir.exists():
            logger.warning(f"markets 目錄不存在：{self.markets_dir}")
            self.available_commodities = set()
            return

        # 取得所有子目錄名稱
        self.available_commodities = {
            d.name for d in self.markets_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        }

        logger.info(f"已載入 {len(self.available_commodities)} 個可用商品目錄")
        logger.debug(f"可用商品：{sorted(self.available_commodities)}")

    def extract_commodity(self, news_text: str) -> Optional[str]:
        """
        從新聞文本中提取商品名稱

        參數:
            news_text: 新聞文本（英文）

        回傳:
            商品目錄名稱（如 'Gold'），若無匹配則回傳 None
        """
        news_lower = news_text.lower()

        # 按映射表逐一檢查
        for keyword, commodity_dir in self.COMMODITY_MAP.items():
            if keyword in news_lower:
                # 檢查該商品目錄是否存在
                if commodity_dir in self.available_commodities:
                    logger.debug(f"匹配商品：{keyword} -> {commodity_dir}")
                    return commodity_dir
                else:
                    logger.debug(f"商品 {commodity_dir} 目錄不存在，忽略")

        return None

    def is_valid_commodity(self, commodity_dir: str) -> bool:
        """
        檢查商品目錄是否有效

        參數:
            commodity_dir: 商品目錄名稱

        回傳:
            是否有效
        """
        return commodity_dir in self.available_commodities
