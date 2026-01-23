#!/usr/bin/env python3
"""
fetch_data.py - 數據抓取工具

從公開來源抓取 MOVE、VIX、信用利差、JGB 殖利率數據。
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:
    yf = None
    print("Warning: yfinance not installed, VIX from Yahoo will not be available")

# =============================================================================
# Configuration
# =============================================================================

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
CDP_PORT = 9222
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_MAX_AGE = timedelta(hours=12)


# =============================================================================
# Cache Utilities
# =============================================================================

def is_cache_valid(key: str) -> bool:
    """檢查快取是否有效"""
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return (datetime.now() - mtime) < CACHE_MAX_AGE


def load_cache(key: str):
    """載入快取"""
    if is_cache_valid(key):
        with open(CACHE_DIR / f"{key}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return pd.DataFrame(data["data"]).set_index("DATE")
    return None


def save_cache(key: str, df: pd.DataFrame):
    """儲存快取"""
    CACHE_DIR.mkdir(exist_ok=True)
    data = df.reset_index().to_dict(orient="records")
    with open(CACHE_DIR / f"{key}.json", "w", encoding="utf-8") as f:
        json.dump({"cached_at": datetime.now().isoformat(), "data": data}, f, default=str)


# =============================================================================
# FRED Data Fetching
# =============================================================================

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Parameters:
    -----------
    series_id : str
        FRED 系列代碼 (e.g., "DGS10", "BAMLC0A0CM")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns:
    --------
    pd.Series
        時間序列數據
    """
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text), parse_dates=["DATE"], index_col="DATE")
        df.columns = [series_id]

        # Replace '.' with NaN (FRED uses '.' for missing values)
        df = df.replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)


def fetch_ig_oas(start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取 IG 信用利差 (OAS)

    使用 BAMLC0A0CM (ICE BofA US Corporate Index OAS) 作為 CDX IG 代理
    """
    return fetch_fred_series("BAMLC0A0CM", start_date, end_date)


def fetch_dgs10(start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取 10 年期國債殖利率"""
    return fetch_fred_series("DGS10", start_date, end_date)


# =============================================================================
# Yahoo Finance Data Fetching
# =============================================================================

def fetch_vix_yahoo(start_date: str, end_date: str) -> pd.Series:
    """
    從 Yahoo Finance 抓取 VIX

    Parameters:
    -----------
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns:
    --------
    pd.Series
        VIX 收盤價
    """
    if yf is None:
        print("yfinance not available, returning empty series")
        return pd.Series(dtype=float)

    try:
        data = yf.download("^VIX", start=start_date, end=end_date, progress=False)
        if data.empty:
            print("No VIX data returned from Yahoo Finance")
            return pd.Series(dtype=float)

        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            vix = data[("Close", "^VIX")]
        else:
            vix = data["Close"]

        vix.name = "VIX"
        return vix

    except Exception as e:
        print(f"Error fetching VIX from Yahoo Finance: {e}")
        return pd.Series(dtype=float)


# =============================================================================
# MOVE Proxy (Rates Volatility)
# =============================================================================

def compute_rates_vol_proxy(dgs10: pd.Series, window: int = 21) -> pd.Series:
    """
    使用 10 年期國債殖利率的實現波動率作為 MOVE 代理

    Parameters:
    -----------
    dgs10 : pd.Series
        10 年期國債殖利率
    window : int
        計算窗口（交易日）

    Returns:
    --------
    pd.Series
        年化實現波動率（可作為 MOVE 代理）
    """
    # 殖利率變化（bps）
    daily_change = dgs10.diff() * 100
    # 21 日滾動標準差，年化
    realized_vol = daily_change.rolling(window).std() * (252 ** 0.5)
    realized_vol.name = "MOVE"
    return realized_vol


# =============================================================================
# JGB Data (Placeholder for CDP scraping)
# =============================================================================

def fetch_jgb_placeholder(start_date: str, end_date: str) -> pd.Series:
    """
    JGB 10Y 殖利率佔位符

    實際使用需要 CDP 爬蟲，這裡返回模擬數據用於測試。
    """
    print("Warning: JGB10Y data requires CDP scraping, using placeholder")

    # 生成日期範圍
    dates = pd.date_range(start=start_date, end=end_date, freq="B")

    # 模擬數據（實際應從 Investing.com 爬取）
    import numpy as np
    np.random.seed(42)
    jgb = pd.Series(
        0.5 + 0.3 * np.random.randn(len(dates)).cumsum() * 0.01,
        index=dates,
        name="JGB10Y"
    )

    return jgb


# =============================================================================
# Main Fetch Function
# =============================================================================

def fetch_all_data(
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    抓取所有需要的數據

    Parameters:
    -----------
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)
    use_cache : bool
        是否使用快取

    Returns:
    --------
    pd.DataFrame
        columns: ["MOVE", "VIX", "CREDIT", "JGB10Y"]
    """
    cache_key = f"data_{start_date}_{end_date}"

    if use_cache:
        cached = load_cache(cache_key)
        if cached is not None:
            print(f"Loaded data from cache")
            return cached

    print("Fetching data from sources...")

    # 1. VIX from Yahoo
    print("  Fetching VIX from Yahoo Finance...")
    vix = fetch_vix_yahoo(start_date, end_date)
    vix.name = "VIX"

    # 2. IG OAS from FRED (as CDX IG proxy)
    print("  Fetching IG OAS from FRED...")
    credit = fetch_ig_oas(start_date, end_date)
    credit.name = "CREDIT"

    # 3. DGS10 from FRED (for MOVE proxy)
    print("  Fetching DGS10 from FRED...")
    dgs10 = fetch_dgs10(start_date, end_date)

    # Compute MOVE proxy
    move = compute_rates_vol_proxy(dgs10)
    move.name = "MOVE"

    # 4. JGB placeholder
    print("  Fetching JGB10Y (placeholder)...")
    jgb = fetch_jgb_placeholder(start_date, end_date)
    jgb.name = "JGB10Y"

    # Combine
    df = pd.concat([move, vix, credit, jgb], axis=1)

    # Align to business days
    df = df.sort_index()
    df.index = pd.to_datetime(df.index)

    # Forward fill missing values
    df = df.ffill()

    # Save cache
    if use_cache:
        save_cache(cache_key, df)
        print(f"  Data cached")

    return df


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fetch data for rates vol leadlag analysis")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", "-o", help="Output CSV path")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--symbols", default="MOVE,VIX,CREDIT,JGB10Y", help="Symbols to fetch")

    args = parser.parse_args()

    # Fetch data
    df = fetch_all_data(args.start, args.end, use_cache=not args.no_cache)

    # Filter symbols
    symbols = [s.strip() for s in args.symbols.split(",")]
    df = df[[s for s in symbols if s in df.columns]]

    # Output
    if args.output:
        df.to_csv(args.output)
        print(f"Data saved to {args.output}")
    else:
        print(df.tail(10))

    # Print summary
    print(f"\nData Summary:")
    print(f"  Period: {df.index.min()} to {df.index.max()}")
    print(f"  Observations: {len(df)}")
    print(f"  Missing ratio: {df.isna().mean().to_dict()}")


if __name__ == "__main__":
    main()
