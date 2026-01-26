#!/usr/bin/env python3
"""
JSDA 數據抓取腳本

從 JSDA 官網下載 Trends in Bond Transactions (by investor type) XLS 並解析。

注意：JSDA 網站結構可能變更，需定期維護下載邏輯。
"""

import argparse
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

# 專案路徑設定
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# 確保目錄存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 配置
# ============================================================

# JSDA 統計頁面（需定期確認是否變更）
JSDA_STATS_URL = "https://www.jsda.or.jp/shiryoshitsu/toukei/data_bb/"

# User-Agent（模擬瀏覽器）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.5",
}

# 快取有效期（秒）
CACHE_TTL = 7 * 24 * 60 * 60  # 7 天


# ============================================================
# 數據抓取
# ============================================================

def fetch_jsda_page() -> str:
    """抓取 JSDA 統計頁面 HTML"""
    try:
        response = requests.get(JSDA_STATS_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"錯誤：無法抓取 JSDA 頁面 - {e}")
        return ""


def find_xls_url(html: str) -> Optional[str]:
    """
    從 HTML 中找到投資人別交易 XLS 的下載連結

    注意：此正則需根據 JSDA 網站結構調整
    """
    # 尋找包含「投資家別」或「investor」的 XLS 連結
    patterns = [
        r'href=["\']([^"\']*investor[^"\']*\.xlsx?)["\']',
        r'href=["\']([^"\']*投資家[^"\']*\.xlsx?)["\']',
        r'href=["\']([^"\']*bond[^"\']*transaction[^"\']*\.xlsx?)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            url = match.group(1)
            # 處理相對路徑
            if not url.startswith("http"):
                url = f"https://www.jsda.or.jp{url}" if url.startswith("/") else f"{JSDA_STATS_URL}{url}"
            return url

    return None


def download_xls(url: str) -> Optional[bytes]:
    """下載 XLS 檔案"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=60)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"錯誤：無法下載 XLS - {e}")
        return None


def parse_jsda_xls(
    xls_content: bytes,
    target_sheet: str = None
) -> Dict[str, pd.DataFrame]:
    """
    解析 JSDA XLS

    Args:
        xls_content: XLS 檔案內容
        target_sheet: 目標 sheet 名稱（None 表示讀取所有）

    Returns:
        dict: {sheet_name: DataFrame}
    """
    xls = pd.ExcelFile(BytesIO(xls_content))

    sheets = {}
    for sheet_name in xls.sheet_names:
        if target_sheet and sheet_name != target_sheet:
            continue
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            sheets[sheet_name] = df
        except Exception as e:
            print(f"警告：無法解析 sheet '{sheet_name}' - {e}")

    return sheets


def extract_investor_data(
    sheets: Dict[str, pd.DataFrame],
    investor_pattern: str = "Insurance",
    maturity_pattern: str = "Super-long"
) -> pd.DataFrame:
    """
    從解析後的 sheets 中提取目標投資人 + 天期桶的數據

    注意：此函數需根據 JSDA XLS 的實際結構調整
    """
    # TODO: 根據實際 XLS 結構實作
    # 這是一個示範框架

    for sheet_name, df in sheets.items():
        # 嘗試識別數據區域
        # JSDA XLS 結構通常：
        # - 前幾行是標題/說明
        # - 資料區域以日期為第一列
        # - 後續列是各投資人/天期的買賣數據

        print(f"處理 sheet: {sheet_name}")
        print(f"Shape: {df.shape}")
        print(df.head(10))

    # 返回空 DataFrame（實際需根據結構實作）
    return pd.DataFrame()


# ============================================================
# 快取管理
# ============================================================

def is_cache_valid(cache_file: Path) -> bool:
    """檢查快取是否有效"""
    if not cache_file.exists():
        return False

    # 檢查檔案修改時間
    mtime = cache_file.stat().st_mtime
    age = datetime.now().timestamp() - mtime
    return age < CACHE_TTL


def save_cache(data: Dict, cache_file: Path):
    """保存快取"""
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_cache(cache_file: Path) -> Optional[Dict]:
    """載入快取"""
    if not is_cache_valid(cache_file):
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ============================================================
# 主要函數
# ============================================================

def fetch_and_parse(
    refresh: bool = False,
    investor_group: str = "insurance_companies",
    maturity_bucket: str = "super_long"
) -> pd.DataFrame:
    """
    完整的抓取與解析流程

    Args:
        refresh: 是否強制刷新
        investor_group: 投資人分類
        maturity_bucket: 天期桶

    Returns:
        pd.DataFrame: 淨買入時間序列
    """
    cache_file = CACHE_DIR / f"jsda_{investor_group}_{maturity_bucket}.json"

    # 檢查快取
    if not refresh:
        cached = load_cache(cache_file)
        if cached:
            print("使用快取數據")
            df = pd.DataFrame(cached["data"])
            df["date"] = pd.to_datetime(df["date"])
            return df.set_index("date")

    # 抓取數據
    print("從 JSDA 抓取數據...")

    # 1. 抓取統計頁面
    html = fetch_jsda_page()
    if not html:
        print("錯誤：無法抓取 JSDA 頁面")
        return pd.DataFrame()

    # 2. 找到 XLS 下載連結
    xls_url = find_xls_url(html)
    if not xls_url:
        print("錯誤：無法找到 XLS 下載連結")
        print("請手動確認 JSDA 網站結構是否變更")
        return pd.DataFrame()

    print(f"XLS URL: {xls_url}")

    # 3. 下載 XLS
    xls_content = download_xls(xls_url)
    if not xls_content:
        return pd.DataFrame()

    # 保存原始 XLS
    raw_cache = CACHE_DIR / f"jsda_raw_{datetime.now().strftime('%Y%m')}.xlsx"
    with open(raw_cache, "wb") as f:
        f.write(xls_content)
    print(f"原始 XLS 已保存至: {raw_cache}")

    # 4. 解析 XLS
    sheets = parse_jsda_xls(xls_content)

    # 5. 提取目標數據
    df = extract_investor_data(
        sheets,
        investor_pattern=investor_group,
        maturity_pattern=maturity_bucket
    )

    # 6. 保存快取
    if not df.empty:
        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "investor_group": investor_group,
            "maturity_bucket": maturity_bucket,
            "source_url": xls_url,
            "data": df.reset_index().to_dict(orient="records")
        }
        save_cache(cache_data, cache_file)

    return df


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="從 JSDA 抓取投資人別債券交易數據"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="強制刷新（忽略快取）"
    )
    parser.add_argument(
        "--investor",
        type=str,
        default="insurance_companies",
        choices=["insurance_companies", "life_insurance", "non_life_insurance"],
        help="投資人分類"
    )
    parser.add_argument(
        "--maturity",
        type=str,
        default="super_long",
        choices=["super_long", "long", "10y_plus"],
        help="天期桶"
    )
    parser.add_argument(
        "--list-sheets",
        action="store_true",
        help="列出 XLS 中的所有 sheets"
    )

    args = parser.parse_args()

    if args.list_sheets:
        # 列出 sheets 模式
        print("抓取 JSDA XLS 並列出 sheets...")
        html = fetch_jsda_page()
        if html:
            xls_url = find_xls_url(html)
            if xls_url:
                xls_content = download_xls(xls_url)
                if xls_content:
                    sheets = parse_jsda_xls(xls_content)
                    print("\n可用的 Sheets:")
                    for name in sheets.keys():
                        print(f"  - {name}")
        return

    # 正常抓取模式
    df = fetch_and_parse(
        refresh=args.refresh,
        investor_group=args.investor,
        maturity_bucket=args.maturity
    )

    if df.empty:
        print("警告：未能取得數據")
        print("可能原因：")
        print("1. JSDA 網站結構已變更")
        print("2. 網路連線問題")
        print("3. XLS 格式不符預期")
        print("\n建議手動從 JSDA 下載 XLS 並檢查結構。")
    else:
        print(f"\n成功取得 {len(df)} 筆數據")
        print(df.tail())


if __name__ == "__main__":
    main()
