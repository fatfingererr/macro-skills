#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Yahoo Finance Price Data Fetcher

Fetch historical stock/index prices from Yahoo Finance with caching support.

Features:
- Automatic caching (12-hour validity)
- Retry logic for network failures
- Input validation
- Data quality checks

Usage:
    python fetch_price_data.py --ticker NVDA --start 2022-01-01
    python fetch_price_data.py --ticker NVDA AMD GOOGL --start 2022-01-01 --end 2026-01-28

Version: 1.1.0
Last Updated: 2026-01-28
"""

import argparse
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf


# ========== Version Info ==========
__version__ = "1.1.0"
__updated__ = "2026-01-28"


# ========== Cache Settings ==========
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_VALIDITY_HOURS = 12


# ========== Retry Settings ==========
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0
RETRY_BACKOFF_MULTIPLIER = 1.5


# ========== Ticker Name Mapping ==========
TICKER_NAMES = {
    # Indices
    "^SOX": "Philadelphia Semiconductor (SOX)",
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ Composite",
    "^DJI": "Dow Jones Industrial (DJIA)",
    "^NDX": "Nasdaq 100 (NDX)",
    # Tech Stocks
    "GOOGL": "Google (GOOGL)",
    "GOOG": "Google (GOOG)",
    "AAPL": "Apple (AAPL)",
    "MSFT": "Microsoft (MSFT)",
    "NVDA": "NVIDIA (NVDA)",
    "TSLA": "Tesla (TSLA)",
    "AMZN": "Amazon (AMZN)",
    "META": "Meta (META)",
    "NFLX": "Netflix (NFLX)",
    # Semiconductors
    "TSM": "TSMC ADR (TSM)",
    "AMD": "AMD (AMD)",
    "INTC": "Intel (INTC)",
    "AVGO": "Broadcom (AVGO)",
    "QCOM": "Qualcomm (QCOM)",
    "TXN": "Texas Instruments (TXN)",
    "MU": "Micron (MU)",
    "AMAT": "Applied Materials (AMAT)",
    "LRCX": "Lam Research (LRCX)",
    "KLAC": "KLA Corp (KLAC)",
    "ADI": "Analog Devices (ADI)",
    "MRVL": "Marvell (MRVL)",
    "NXPI": "NXP Semi (NXPI)",
    "ON": "ON Semi (ON)",
    "MCHP": "Microchip (MCHP)",
    "ASML": "ASML (ASML)",
    "ARM": "ARM Holdings (ARM)",
    # Other Large Caps
    "JPM": "JPMorgan (JPM)",
    "V": "Visa (V)",
    "UNH": "UnitedHealth (UNH)",
    "JNJ": "Johnson & Johnson (JNJ)",
    "WMT": "Walmart (WMT)",
    "PG": "Procter & Gamble (PG)",
    "XOM": "Exxon Mobil (XOM)",
    "CVX": "Chevron (CVX)",
    "HD": "Home Depot (HD)",
    "KO": "Coca-Cola (KO)",
}


def get_ticker_name(ticker: str) -> str:
    """
    Get display name for ticker

    Parameters
    ----------
    ticker : str
        Ticker symbol

    Returns
    -------
    str
        Display name
    """
    return TICKER_NAMES.get(ticker.upper(), ticker)


def get_cache_path(ticker: str, start_date: str, end_date: str) -> Path:
    """
    Generate cache file path

    Parameters
    ----------
    ticker : str
        Ticker symbol
    start_date : str
        Start date
    end_date : str
        End date

    Returns
    -------
    Path
        Cache file path
    """
    cache_key = hashlib.md5(f"{ticker}_{start_date}_{end_date}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"{ticker}_{cache_key}.parquet"


def is_cache_valid(cache_path: Path) -> bool:
    """
    Check if cache is valid (not expired)

    Parameters
    ----------
    cache_path : Path
        Cache file path

    Returns
    -------
    bool
        Whether valid
    """
    if not cache_path.exists():
        return False

    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600
    return age_hours < CACHE_VALIDITY_HOURS


def fetch_price_data(
    ticker: str,
    start_date: str,
    end_date: Optional[str] = None,
    use_cache: bool = True,
    max_retries: int = MAX_RETRIES,
    validate_data: bool = True,
) -> pd.DataFrame:
    """
    Fetch single ticker historical price from Yahoo Finance

    Parameters
    ----------
    ticker : str
        Ticker symbol (e.g., NVDA, ^GSPC)
    start_date : str
        Start date (YYYY-MM-DD)
    end_date : str, optional
        End date (YYYY-MM-DD), defaults to today
    use_cache : bool
        Whether to use cache, default True
    max_retries : int
        Maximum retry attempts for network failures
    validate_data : bool
        Whether to validate data quality

    Returns
    -------
    pd.DataFrame
        DataFrame with Close column, index is DatetimeIndex

    Raises
    ------
    ValueError
        Raised when unable to fetch data
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Check cache
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = get_cache_path(ticker, start_date, end_date)

        if is_cache_valid(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                print(f"  [Cache] {ticker}: using cache ({len(df)} rows)")
                return df
            except Exception:
                pass  # Cache corrupted, re-fetch

    # Fetch from Yahoo Finance with retry logic
    last_error = None
    delay = RETRY_DELAY_SECONDS

    for attempt in range(1, max_retries + 1):
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if data.empty:
                raise ValueError(f"No data returned for {ticker}")

            # Keep only Close price
            df = data[["Close"]].copy()

            # Handle multi-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            # Validate data quality
            if validate_data:
                # Check for minimum data points
                if len(df) < 5:
                    raise ValueError(f"Insufficient data for {ticker}: only {len(df)} rows")

                # Check for NaN values
                nan_pct = df["Close"].isna().sum() / len(df)
                if nan_pct > 0.1:  # More than 10% NaN
                    print(f"  [Warning] {ticker}: {nan_pct:.1%} NaN values, cleaning...")
                    df = df.dropna()

                # Check for invalid prices
                close_col = df["Close"]
                if isinstance(close_col, pd.DataFrame):
                    close_col = close_col.iloc[:, 0]
                if (close_col <= 0).any():
                    invalid_count = (close_col <= 0).sum()
                    print(f"  [Warning] {ticker}: {invalid_count} invalid prices removed")
                    df = df[close_col > 0]

            # Save to cache
            if use_cache and not df.empty:
                df.to_parquet(cache_path)

            print(f"  [Fetch] {ticker}: {len(df)} rows ({df.index.min().date()} ~ {df.index.max().date()})")
            return df

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"  [Retry] {ticker}: Attempt {attempt}/{max_retries} failed ({e}), retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= RETRY_BACKOFF_MULTIPLIER
            else:
                break

    raise ValueError(f"Unable to fetch data for {ticker} after {max_retries} attempts: {last_error}")


def fetch_multiple_prices(
    tickers: List[str],
    start_date: str,
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Batch fetch historical prices for multiple tickers

    Parameters
    ----------
    tickers : List[str]
        List of ticker symbols
    start_date : str
        Start date (YYYY-MM-DD)
    end_date : str, optional
        End date (YYYY-MM-DD)
    use_cache : bool
        Whether to use cache

    Returns
    -------
    Dict[str, pd.DataFrame]
        {ticker: DataFrame} dictionary
    """
    result = {}

    for ticker in tickers:
        try:
            df = fetch_price_data(ticker, start_date, end_date, use_cache)
            result[ticker] = df
        except ValueError as e:
            print(f"  [Warning] {ticker}: {e}")

    return result


def clear_cache() -> int:
    """
    Clear all cache files

    Returns
    -------
    int
        Number of files cleared
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for f in CACHE_DIR.glob("*.parquet"):
        f.unlink()
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Fetch historical stock/index prices from Yahoo Finance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_price_data.py --ticker NVDA --start 2022-01-01
  python fetch_price_data.py --ticker NVDA AMD GOOGL --start 2022-01-01
  python fetch_price_data.py --ticker ^GSPC --start 2020-01-01 --no-cache
  python fetch_price_data.py --clear-cache
        """,
    )
    parser.add_argument(
        "--ticker", "-t", type=str, nargs="+", default=["NVDA"], help="Ticker symbol(s)"
    )
    parser.add_argument(
        "--start", "-s", type=str, default="2022-01-01", help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", "-e", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today"
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cache files")
    parser.add_argument("--summary", action="store_true", help="Show summary")

    args = parser.parse_args()

    if args.clear_cache:
        count = clear_cache()
        print(f"Cleared {count} cache files")
        return

    print("\n" + "=" * 60)
    print("Yahoo Finance Price Data Fetcher")
    print("=" * 60)
    print(f"Tickers: {', '.join(args.ticker)}")
    print(f"Start: {args.start}")
    print(f"End: {args.end or 'Today'}")
    print("=" * 60 + "\n")

    data = fetch_multiple_prices(
        args.ticker, args.start, args.end, use_cache=not args.no_cache
    )

    if args.summary and data:
        print("\n" + "=" * 60)
        print("Data Summary")
        print("=" * 60)
        for ticker, df in data.items():
            name = get_ticker_name(ticker)
            print(f"\n{name}:")
            print(f"  Data points: {len(df)}")
            print(f"  Start date: {df.index.min().date()}")
            print(f"  End date: {df.index.max().date()}")
            print(f"  Start price: {df['Close'].iloc[0]:.2f}")
            print(f"  End price: {df['Close'].iloc[-1]:.2f}")
            pct_change = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
            print(f"  Price change: {pct_change:+.2f}%")

    return data


if __name__ == "__main__":
    import sys
    import warnings

    warnings.filterwarnings("ignore")
    main()
