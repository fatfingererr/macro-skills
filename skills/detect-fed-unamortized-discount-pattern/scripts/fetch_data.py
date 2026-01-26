#!/usr/bin/env python3
"""
FRED 資料抓取工具

從 FRED 抓取時間序列資料，支援快取機制。
"""

import json
import random
import time
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

# ============================================================================
# 常數定義
# ============================================================================

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

CACHE_DIR = Path(__file__).parent.parent / "cache"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
]

# ============================================================================
# 快取函數
# ============================================================================


def get_cache_path(series_id: str, start_date: str, end_date: str) -> Path:
    """取得快取檔案路徑"""
    return CACHE_DIR / f"{series_id}_{start_date}_{end_date}.json"


def is_cache_valid(cache_path: Path, max_age_hours: int = 24) -> bool:
    """檢查快取是否有效"""
    if not cache_path.exists():
        return False
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(hours=max_age_hours)


def load_cache(cache_path: Path) -> Optional[pd.Series]:
    """載入快取"""
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        series = pd.Series(
            data["values"],
            index=pd.to_datetime(data["dates"]),
            name=data.get("series_id", "value")
        )
        return series
    except Exception:
        return None


def save_cache(cache_path: Path, series: pd.Series, series_id: str) -> None:
    """儲存快取"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({
            "series_id": series_id,
            "dates": series.index.strftime("%Y-%m-%d").tolist(),
            "values": series.tolist(),
            "fetched_at": datetime.now().isoformat()
        }, f, ensure_ascii=False)


# ============================================================================
# 資料抓取函數
# ============================================================================


def random_delay(min_sec: float = 0.3, max_sec: float = 1.0) -> None:
    """模擬人類行為的隨機延遲"""
    time.sleep(random.uniform(min_sec, max_sec))


def get_headers() -> Dict[str, str]:
    """取得隨機 User-Agent"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/csv,text/html,application/xhtml+xml',
    }


def fetch_fred_series(
    series_id: str,
    start_date: str,
    end_date: str,
    use_cache: bool = True,
    cache_max_age_hours: int = 24
) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Parameters
    ----------
    series_id : str
        FRED 系列代碼 (e.g., "WUDSHO", "BAMLC0A0CM")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)
    use_cache : bool
        是否使用快取
    cache_max_age_hours : int
        快取有效時間（小時）

    Returns
    -------
    pd.Series
        時間序列數據，index 為 DatetimeIndex
    """
    # 檢查快取
    if use_cache:
        cache_path = get_cache_path(series_id, start_date, end_date)
        if is_cache_valid(cache_path, cache_max_age_hours):
            cached = load_cache(cache_path)
            if cached is not None:
                print(f"[Cache] 使用快取: {series_id}")
                return cached

    # 抓取新資料
    print(f"[Fetch] 抓取 FRED: {series_id}")
    random_delay()

    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    try:
        response = requests.get(
            FRED_CSV_URL,
            params=params,
            headers=get_headers(),
            timeout=30
        )
        response.raise_for_status()

        # 健壯的 CSV 解析
        df = pd.read_csv(StringIO(response.text))

        # FRED CSV 格式：第一列是日期，第二列是數值
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])

        # 處理缺失值（FRED 使用 '.' 表示缺失）
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        df = df.dropna()
        df = df.set_index("DATE")

        series = df[series_id]

        # 儲存快取
        if use_cache:
            save_cache(cache_path, series, series_id)

        return series

    except Exception as e:
        print(f"[Error] 抓取 {series_id} 失敗: {e}")
        return pd.Series(dtype=float, name=series_id)


def fetch_multiple_series(
    series_list: List[str],
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> Dict[str, pd.Series]:
    """
    抓取多個 FRED 序列

    Returns
    -------
    dict
        {series_id: pd.Series}
    """
    result = {}
    for series_id in series_list:
        result[series_id] = fetch_fred_series(
            series_id, start_date, end_date, use_cache
        )
        random_delay(0.5, 1.5)  # 避免請求過快
    return result


def fetch_yield_curve(
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> pd.Series:
    """
    計算殖利率曲線（10Y - 2Y）

    Returns
    -------
    pd.Series
        殖利率曲線差值
    """
    dgs10 = fetch_fred_series("DGS10", start_date, end_date, use_cache)
    dgs2 = fetch_fred_series("DGS2", start_date, end_date, use_cache)

    # 對齊日期
    aligned = pd.concat([dgs10, dgs2], axis=1).dropna()
    if aligned.empty:
        return pd.Series(dtype=float, name="yield_curve")

    curve = aligned["DGS10"] - aligned["DGS2"]
    curve.name = "yield_curve"
    return curve


# ============================================================================
# 預設指標集
# ============================================================================

DEFAULT_SERIES = {
    "target": ["WUDSHO"],
    "credit_spread": ["BAMLC0A0CM", "BAMLH0A0HYM2"],
    "volatility": ["VIXCLS"],
    "rates": ["DGS10", "DGS2"],
    "fed_balance": ["WALCL"]
}


def fetch_all_indicators(
    start_date: str = "2015-01-01",
    end_date: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, pd.Series]:
    """
    抓取所有預設指標

    Returns
    -------
    dict
        包含所有指標的字典
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    result = {}

    # 目標序列
    for series_id in DEFAULT_SERIES["target"]:
        result[series_id] = fetch_fred_series(series_id, start_date, end_date, use_cache)

    # 信用利差
    for series_id in DEFAULT_SERIES["credit_spread"]:
        result[series_id] = fetch_fred_series(series_id, start_date, end_date, use_cache)

    # 波動率
    for series_id in DEFAULT_SERIES["volatility"]:
        result[series_id] = fetch_fred_series(series_id, start_date, end_date, use_cache)

    # 利率
    for series_id in DEFAULT_SERIES["rates"]:
        result[series_id] = fetch_fred_series(series_id, start_date, end_date, use_cache)

    # 殖利率曲線
    result["yield_curve"] = fetch_yield_curve(start_date, end_date, use_cache)

    # Fed 資產負債表
    for series_id in DEFAULT_SERIES["fed_balance"]:
        result[series_id] = fetch_fred_series(series_id, start_date, end_date, use_cache)

    return result


# ============================================================================
# 命令列介面
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FRED 資料抓取工具")
    parser.add_argument("--series", type=str, default="WUDSHO",
                        help="FRED 系列代碼（逗號分隔多個）")
    parser.add_argument("--start", type=str, default="2015-01-01",
                        help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None,
                        help="結束日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--no-cache", action="store_true",
                        help="不使用快取")
    parser.add_argument("--all", action="store_true",
                        help="抓取所有預設指標")

    args = parser.parse_args()

    if args.end is None:
        args.end = datetime.now().strftime("%Y-%m-%d")

    if args.all:
        print("抓取所有預設指標...")
        data = fetch_all_indicators(args.start, args.end, not args.no_cache)
        for name, series in data.items():
            if not series.empty:
                print(f"  ✓ {name}: {len(series)} 筆，最新 {series.index[-1].strftime('%Y-%m-%d')}")
            else:
                print(f"  ✗ {name}: 無資料")
    else:
        series_list = [s.strip() for s in args.series.split(",")]
        for series_id in series_list:
            data = fetch_fred_series(series_id, args.start, args.end, not args.no_cache)
            if not data.empty:
                print(f"✓ {series_id}: {len(data)} 筆")
                print(f"  日期範圍: {data.index.min().strftime('%Y-%m-%d')} ~ {data.index.max().strftime('%Y-%m-%d')}")
                print(f"  最新值: {data.iloc[-1]:.4f}")
            else:
                print(f"✗ {series_id}: 無資料")
