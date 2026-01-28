#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Index Component Analyzer

Analyze cumulative returns of index components and find Top N performers.

Usage:
    # Year to today (mode 2.b)
    python index_component_analyzer.py --index nasdaq100 --year 2022

    # Specific year only (mode 2.a)
    python index_component_analyzer.py --index nasdaq100 --year 2024 --year-only

    # Custom top N
    python index_component_analyzer.py --index sp100 --year 2022 --top 20

Version: 1.1.0
Last Updated: 2026-01-28
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from fetch_price_data import fetch_price_data, get_ticker_name


# ========== Version Info ==========
__version__ = "1.1.0"
__updated__ = "2026-01-28"


# ========== Index Component Lists ==========
# Note: Component lists should be updated periodically as indices rebalance
# Last verified: 2026-01-28

# S&P 100 Components
SP100_COMPONENTS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMZN", "AVGO",
    "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C", "CAT",
    "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX",
    "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX", "GD",
    "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC",
    "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW", "MA", "MCD",
    "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS", "MSFT", "NEE",
    "NFLX", "NKE", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM", "PYPL", "QCOM",
    "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO", "TMUS", "TSLA",
    "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT", "XOM",
]

# Nasdaq 100 Components
NASDAQ100_COMPONENTS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "PEP", "ADBE", "CSCO", "TMUS", "INTC", "CMCSA", "INTU", "QCOM",
    "TXN", "AMGN", "HON", "AMAT", "ISRG", "BKNG", "SBUX", "LRCX", "VRTX", "ADP",
    "MDLZ", "GILD", "ADI", "REGN", "PANW", "KLAC", "MU", "SNPS", "CDNS", "PYPL",
    "MELI", "CSX", "ASML", "CRWD", "MAR", "ORLY", "ABNB", "MRVL", "CTAS", "NXPI",
    "PCAR", "WDAY", "CPRT", "ROP", "MNST", "FTNT", "DXCM", "PAYX", "ROST", "KDP",
    "ODFL", "MCHP", "KHC", "AEP", "IDXX", "GEHC", "FAST", "AZN", "LULU", "EXC",
    "VRSK", "EA", "CTSH", "CSGP", "XEL", "DLTR", "BKR", "FANG", "TTWO",
    "TEAM", "ON", "CDW", "BIIB", "ZS", "DDOG", "GFS", "ILMN", "MDB", "WBD",
    "CEG", "LCID", "RIVN", "SIRI", "JD", "PDD", "BIDU", "NTES", "ZM",
]

# Dow Jones 30 Components
DOW30_COMPONENTS = [
    "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
    "DOW", "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO", "MCD",
    "MMM", "MRK", "MSFT", "NKE", "PG", "TRV", "UNH", "V", "VZ", "WMT",
]

# Philadelphia Semiconductor Components
SOX_COMPONENTS = [
    "NVDA", "AVGO", "AMD", "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "KLAC",
    "ADI", "MRVL", "NXPI", "ON", "MCHP", "MPWR", "SWKS", "QRVO", "TER", "ENTG",
    "TSM", "ASML", "ARM", "WOLF", "ACLS", "ALGM", "AMKR", "COHR", "CRUS", "FORM",
]

# Index Configuration
# Note: All indices use S&P 500 (^GSPC) as benchmark - core methodology decision
INDEX_CONFIG = {
    "nasdaq100": {
        "name": "Nasdaq 100",
        "components": NASDAQ100_COMPONENTS,
        "description": "Nasdaq 100 Index Components",
    },
    "sp100": {
        "name": "S&P 100",
        "components": SP100_COMPONENTS,
        "description": "S&P 100 Index Components",
    },
    "dow30": {
        "name": "Dow Jones 30",
        "components": DOW30_COMPONENTS,
        "description": "Dow Jones Industrial Average Components",
    },
    "sox": {
        "name": "Philadelphia Semiconductor (SOX)",
        "components": SOX_COMPONENTS,
        "description": "Philadelphia Semiconductor Index Components",
    },
}

# S&P 500 is the fixed benchmark for all analyses - core methodology decision
BENCHMARK_TICKER = "^GSPC"
BENCHMARK_NAME = "S&P 500"


def get_index_config(index_key: str) -> Dict[str, Any]:
    """
    Get index configuration

    Parameters
    ----------
    index_key : str
        Index code

    Returns
    -------
    Dict
        Index configuration
    """
    if index_key not in INDEX_CONFIG:
        raise ValueError(f"Unsupported index: {index_key}. Supported: {', '.join(INDEX_CONFIG.keys())}")
    return INDEX_CONFIG[index_key]


def analyze_single_stock(
    ticker: str,
    start_date: str,
    end_date: str,
    base_date: pd.Timestamp,
) -> Optional[Dict[str, Any]]:
    """
    Analyze single stock performance

    Parameters
    ----------
    ticker : str
        Stock ticker
    start_date : str
        Data start date
    end_date : str
        Data end date
    base_date : pd.Timestamp
        Base date for return calculation (last trading day of previous year)

    Returns
    -------
    Dict or None
        Analysis result, None if unable to analyze
    """
    try:
        data = fetch_price_data(ticker, start_date, end_date, use_cache=True)

        if data is None or data.empty:
            return None

        # Filter data from base_date onward (include the base date)
        data = data[data.index >= base_date]

        if len(data) < 10:
            return None

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Calculate cumulative return
        start_price = close.iloc[0]
        end_price = close.iloc[-1]
        cumulative_return = ((end_price / start_price) - 1) * 100

        return {
            "ticker": ticker,
            "name": get_ticker_name(ticker),
            "data": data,
            "cumulative_return": cumulative_return,
            "start_price": start_price,
            "end_price": end_price,
        }

    except Exception as e:
        print(f"  [Error] {ticker}: {e}")
        return None


def analyze_index_components(
    index_key: str,
    start_year: int,
    top_n: int = 20,
    year_only: bool = False,
) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
    """
    Analyze all index components and find Top N performers

    Parameters
    ----------
    index_key : str
        Index code
    start_year : int
        Start year
    top_n : int
        Top N to select
    year_only : bool
        If True, analyze only the specified year

    Returns
    -------
    Tuple[List, List, Dict]
        (top_stocks, all_results, summary)
    """
    config = get_index_config(index_key)
    components = config["components"]
    index_name = config["name"]

    print(f"\nAnalyzing {index_name} components ({len(components)} stocks)...")
    print("This may take a while, please wait...\n")

    # Date settings
    start_date = f"{start_year - 1}-12-01"

    if year_only:
        end_date = f"{start_year}-12-31"
        mode_label = "year_only"
    else:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        mode_label = "year_to_today"

    year_start = f"{start_year}-01-01"

    # Find the base_date (last trading day of previous year) using S&P 500 benchmark
    # S&P 500 is the fixed benchmark - core methodology decision
    benchmark_ticker = BENCHMARK_TICKER
    print(f"  [Fetch] Fetching benchmark ({benchmark_ticker}) to determine base date...")
    benchmark_data = fetch_price_data(benchmark_ticker, start_date, end_date)

    prev_year_data = benchmark_data[benchmark_data.index < year_start]
    if prev_year_data.empty:
        raise ValueError(f"No data found for the last trading day of {start_year - 1}")

    base_date = prev_year_data.index[-1]  # Last trading day of previous year
    print(f"  [Base] Using {base_date.strftime('%Y-%m-%d')} as base date (last trading day of {start_year - 1})\n")

    results = []
    failed = []

    for i, ticker in enumerate(components, 1):
        result = analyze_single_stock(ticker, start_date, end_date, base_date)
        if result:
            results.append(result)
            print(f"  [{i:3d}/{len(components)}] {ticker}: {result['cumulative_return']:.2f}%")
        else:
            failed.append(ticker)
            print(f"  [{i:3d}/{len(components)}] {ticker}: Insufficient data, skipped")

    # Sort by return (descending)
    results.sort(key=lambda x: x["cumulative_return"], reverse=True)

    print(f"\nSuccessfully analyzed: {len(results)} stocks")
    print(f"Skipped: {len(failed)} stocks")

    # Use benchmark data already fetched (filter from base_date)
    benchmark_data = benchmark_data[benchmark_data.index >= base_date]
    benchmark_close = benchmark_data["Close"]
    if isinstance(benchmark_close, pd.DataFrame):
        benchmark_close = benchmark_close.iloc[:, 0]
    benchmark_return = ((benchmark_close.iloc[-1] / benchmark_close.iloc[0]) - 1) * 100

    # Calculate time
    days_held = (benchmark_data.index[-1] - benchmark_data.index[0]).days
    years_held = days_held / 365.25

    # Statistics
    beat_benchmark = sum(1 for r in results if r["cumulative_return"] > benchmark_return)
    top_stocks = results[:top_n]

    summary = {
        "skill": "track-equity-cumulative-return",
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "mode": mode_label,
        "parameters": {
            "index": index_key,
            "index_name": index_name,
            "start_year": start_year,
            "year_only": year_only,
            "top_n": top_n,
        },
        "period": {
            "start_date": benchmark_data.index[0].strftime("%Y-%m-%d"),
            "end_date": benchmark_data.index[-1].strftime("%Y-%m-%d"),
            "days_held": days_held,
            "years_held": round(years_held, 2),
        },
        "benchmark": {
            "ticker": BENCHMARK_TICKER,
            "name": BENCHMARK_NAME,
            "cumulative_return_pct": round(benchmark_return, 2),
        },
        "summary": {
            "total_components": len(components),
            "analyzed": len(results),
            "failed": len(failed),
            "beat_benchmark": beat_benchmark,
            "beat_benchmark_pct": round(beat_benchmark / len(results) * 100, 1) if results else 0,
            "top_n_avg_return": round(
                sum(r["cumulative_return"] for r in top_stocks) / len(top_stocks), 2
            ) if top_stocks else 0,
            "all_avg_return": round(
                sum(r["cumulative_return"] for r in results) / len(results), 2
            ) if results else 0,
        },
        "top_performers": [
            {
                "rank": i + 1,
                "ticker": r["ticker"],
                "name": r["name"],
                "cumulative_return_pct": round(r["cumulative_return"], 2),
                "vs_benchmark": round(r["cumulative_return"] - benchmark_return, 2),
            }
            for i, r in enumerate(top_stocks)
        ],
    }

    return top_stocks, results, summary


def create_comparison_dataframe(
    top_stocks: List[Dict],
    benchmark_data: pd.DataFrame,
    benchmark_ticker: str,
) -> pd.DataFrame:
    """
    Create comparison DataFrame

    Parameters
    ----------
    top_stocks : List[Dict]
        Top N stock list
    benchmark_data : pd.DataFrame
        Benchmark data
    benchmark_ticker : str
        Benchmark ticker

    Returns
    -------
    pd.DataFrame
        Comparison DataFrame
    """
    combined = pd.DataFrame()

    # Add benchmark
    benchmark_close = benchmark_data["Close"]
    if isinstance(benchmark_close, pd.DataFrame):
        benchmark_close = benchmark_close.iloc[:, 0]
    combined[f"{benchmark_ticker}_Price"] = benchmark_close

    # Add all tickers
    for stock in top_stocks:
        ticker = stock["ticker"]
        close = stock["data"]["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        combined[f"{ticker}_Price"] = close

    combined = combined.dropna()

    # Calculate returns
    base_benchmark = combined[f"{benchmark_ticker}_Price"].iloc[0]
    combined[f"{benchmark_ticker}_Return%"] = (
        (combined[f"{benchmark_ticker}_Price"] / base_benchmark) - 1
    ) * 100

    for stock in top_stocks:
        ticker = stock["ticker"]
        base_price = combined[f"{ticker}_Price"].iloc[0]
        combined[f"{ticker}_Return%"] = (
            (combined[f"{ticker}_Price"] / base_price) - 1
        ) * 100

    return combined


def print_ranking_table(summary: Dict[str, Any]) -> None:
    """
    Print ranking table
    """
    params = summary["parameters"]
    period = summary["period"]
    benchmark = summary["benchmark"]
    stats = summary["summary"]
    top = summary["top_performers"]
    year_only = params.get("year_only", False)

    print("\n" + "=" * 80)
    print(f"{params['index_name']} Component Performance Ranking")

    if year_only:
        print(f"Period: {params['start_year']} Full Year ({period['start_date']} ~ {period['end_date']})")
    else:
        print(f"Period: {period['start_date']} ~ {period['end_date']} ({period['years_held']:.1f} years)")

    print("=" * 80)

    print(f"\n{'Rank':<5} {'Ticker':<8} {'Name':<25} {'Cum. Return':>12} {'vs Bench':>10}")
    print("-" * 80)

    for r in top:
        beat = "✓" if r["cumulative_return_pct"] > benchmark["cumulative_return_pct"] else ""
        print(
            f"{r['rank']:<5} {r['ticker']:<8} {r['name']:<25} "
            f"{r['cumulative_return_pct']:>+11.2f}% "
            f"{r['vs_benchmark']:>+9.2f}% {beat}"
        )

    print("-" * 80)
    print(
        f"{'Bench':<5} {benchmark['ticker']:<8} {benchmark['name']:<25} "
        f"{benchmark['cumulative_return_pct']:>+11.2f}%"
    )
    print("=" * 80)

    print(f"\nStatistics:")
    print(f"  - Stocks analyzed: {stats['analyzed']} / {stats['total_components']}")
    print(f"  - Beat benchmark: {stats['beat_benchmark']} ({stats['beat_benchmark_pct']:.1f}%)")
    print(f"  - Top {params['top_n']} avg return: {stats['top_n_avg_return']:+.2f}%")
    print(f"  - All avg return: {stats['all_avg_return']:+.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze index component performance and find Top N",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported indices:
  nasdaq100  - Nasdaq 100 Index
  sp100      - S&P 100 Index
  dow30      - Dow Jones 30 Index
  sox        - Philadelphia Semiconductor Index

Examples:
  # Year to today (mode 2.b)
  python index_component_analyzer.py --index nasdaq100 --year 2022

  # Specific year only (mode 2.a)
  python index_component_analyzer.py --index nasdaq100 --year 2024 --year-only

  # Custom top N
  python index_component_analyzer.py --index sp100 --year 2022 --top 20
  python index_component_analyzer.py --index dow30 --year 2020
  python index_component_analyzer.py --index sox --year 2023
        """,
    )
    parser.add_argument(
        "--index",
        "-i",
        type=str,
        default="nasdaq100",
        choices=list(INDEX_CONFIG.keys()),
        help="Index type (default: nasdaq100)",
    )
    parser.add_argument(
        "--year", "-y", type=int, default=2022, help="Start year (default: 2022)"
    )
    parser.add_argument(
        "--year-only",
        action="store_true",
        help="Analyze only the specified year (not to today)",
    )
    parser.add_argument(
        "--top", "-t", type=int, default=20, help="Top N (default: 20)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    config = INDEX_CONFIG[args.index]

    print("\n" + "=" * 100)
    print(f"{config['name']} Top {args.top} Performance Tracker")
    if args.year_only:
        print(f"Period: {args.year} Full Year")
    else:
        print(f"Period: From {args.year} to Today")
    print(f"Benchmark: {BENCHMARK_NAME} ({BENCHMARK_TICKER}) [Fixed]")
    print("=" * 100)

    # Analyze
    top_stocks, all_results, summary = analyze_index_components(
        args.index, args.year, args.top, args.year_only
    )

    # Print report
    print_ranking_table(summary)

    # Output JSON
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_path}")

    return top_stocks, all_results, summary


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    top_stocks, all_results, summary = main()
