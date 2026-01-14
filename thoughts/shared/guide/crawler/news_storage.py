"""
新聞儲存模組

負責將新聞保存到 markets/<商品>/yyyymmdd.txt，並管理 ID。
"""

from typing import Optional, Tuple, Dict
from pathlib import Path
from datetime import datetime
from loguru import logger


class NewsStorage:
    """
    新聞儲存管理器

    負責將新聞保存到對應商品目錄，並管理遞增 ID。
    """

    def __init__(self, markets_dir: str = 'markets'):
        """
        初始化儲存管理器

        參數:
            markets_dir: markets 目錄路徑
        """
        self.markets_dir = Path(markets_dir)
        self.markets_dir.mkdir(parents=True, exist_ok=True)

    def save_news(
        self,
        commodity_dir: str,
        news_text: str,
        date: Optional[datetime] = None,
        news_data: Optional[Dict] = None
    ) -> Tuple[bool, int]:
        """
        保存新聞到指定商品目錄

        參數:
            commodity_dir: 商品目錄名稱（如 'Gold'）
            news_text: 新聞文本（英文原文，用於相容性）
            date: 日期（預設為當天）
            news_data: 新聞詳細資料（包含 title, content, time）

        回傳:
            (是否成功, 新聞 ID)
        """
        if date is None:
            date = datetime.now()

        # 確保商品目錄存在
        commodity_path = self.markets_dir / commodity_dir
        commodity_path.mkdir(parents=True, exist_ok=True)

        # 檔案路徑
        date_str = date.strftime('%Y%m%d')
        file_path = commodity_path / f"{date_str}.txt"

        # 取得下一個 ID
        next_id = self._get_next_id(file_path)

        # 寫入新聞（附加模式）
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                # Windows 不支援 fcntl，使用 try-except 包裝
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                except (ImportError, OSError):
                    # Windows 或不支援檔案鎖的系統，直接寫入
                    pass

                # 結構化寫入格式
                if news_data:
                    title = news_data.get('title', '').strip()
                    content = news_data.get('content', '').strip()
                    time_str = news_data.get('time', '').strip()

                    # 寫入標題
                    f.write(f"[{next_id}] {title}\n")
                    
                    # 寫入內容（如果有）
                    if content:
                        f.write(f"\n{content}\n")
                    else:
                        f.write("(無詳細內容)\n")
                else:
                    # 舊格式相容：直接寫入 news_text
                    f.write(f"[{next_id}] {news_text}\n")

                f.write("-" * 80 + "\n")

                # 解鎖（若有鎖）
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (ImportError, OSError):
                    pass

            logger.info(f"新聞已保存：{file_path} (ID: {next_id})")
            return True, next_id

        except Exception as e:
            logger.error(f"保存新聞失敗：{e}")
            return False, -1

    def _get_next_id(self, file_path: Path) -> int:
        """
        取得檔案中的下一個 ID

        參數:
            file_path: 檔案路徑

        回傳:
            下一個 ID（從 1 開始）
        """
        if not file_path.exists():
            return 1

        # 讀取檔案，計算現有 ID 數量
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 統計 [ID] 出現次數
            id_count = sum(1 for line in lines if line.strip().startswith('['))
            return id_count + 1

        except Exception as e:
            logger.warning(f"讀取檔案失敗，ID 從 1 開始：{e}")
            return 1

    def check_duplicate(
        self,
        commodity_dir: str,
        news_text: str,
        date: Optional[datetime] = None
    ) -> bool:
        """
        檢查新聞是否已存在（去重）

        參數:
            commodity_dir: 商品目錄名稱
            news_text: 新聞標題（用於比對）
            date: 日期

        回傳:
            是否重複
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime('%Y%m%d')
        file_path = self.markets_dir / commodity_dir / f"{date_str}.txt"

        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 提取所有已保存新聞的標題
            # 格式：[ID] 標題
            input_title = news_text.strip()
            for line in lines:
                line = line.strip()
                # 檢查是否為標題行（以 [數字] 開頭）
                if line.startswith('[') and ']' in line:
                    # 提取標題部分（移除 [ID] 前綴）
                    try:
                        title_part = line.split(']', 1)[1].strip()
                        # 比對標題
                        if title_part == input_title:
                            logger.debug(f"發現重複標題：{input_title[:50]}...")
                            return True
                    except IndexError:
                        continue

            return False

        except Exception as e:
            logger.warning(f"檢查重複時發生錯誤：{e}")
            return False
