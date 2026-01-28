#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cumulative Return Analyzer

Calculate cumulative returns and CAGR for stocks/indices, with multi-ticker comparison.

Usage:
    # Year to today (1.b mode)
    python cumulative_return_analyzer.py --ticker NVDA --year 2022

    # Specific year only (1.a mode)
    python cumulative_return_analyzer.py --ticker NVDA --year 2024 --year-only

    # Multiple tickers
    python cumulative_return_analyzer.py --ticker NVDA AMD GOOGL --year 2022

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

from fetch_price_data import fetch_price_data, fetch_multiple_prices, get_ticker_name


# ========== Version Info ==========
__version__ = "1.1.0"
__updated__ = "2026-01-28"


def calculate_cumulative_return_series(prices: pd.Series) -> pd.Series:
    """
    Calculate cumulative return time series (percentage)

    Parameters
    ----------
    prices : pd.Series
        Price time series

    Returns
    -------
    pd.Series
        Cumulative return time series (%)
    """
    base_price = prices.iloc[0]
    return ((prices / base_price) - 1) * 100


def calculate_cumulative_return(prices: pd.Series) -> float:
    """
    Calculate final cumulative return (percentage)

    Parameters
    ----------
    prices : pd.Series
        Price time series

    Returns
    -------
    float
        Cumulative return (%)
    """
    if len(prices) < 2:
        return np.nan
    return ((prices.iloc[-1] / prices.iloc[0]) - 1) * 100


def calculate_cagr(prices: pd.Series) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR)

    Parameters
    ----------
    prices : pd.Series
        Price time series with DatetimeIndex

    Returns
    -------
    float
        CAGR (%)
    """
    if len(prices) < 2:
        return np.nan

    # Calculate holding period in years
    days = (prices.index[-1] - prices.index[0]).days
    years = days / 365.25

    if years <= 0:
        return np.nan

    # Calculate total return
    total_return = prices.iloc[-1] / prices.iloc[0]

    # CAGR = (ending/beginning)^(1/years) - 1
    cagr = (total_return ** (1 / years) - 1) * 100
    return cagr


def create_cumulative_dataframe(
    all_data: Dict[str, pd.DataFrame],
    benchmark_data: pd.DataFrame,
    benchmark_ticker: str = "^GSPC",
) -> pd.DataFrame:
    """
    Create merged cumulative return DataFrame

    Parameters
    ----------
    all_data : Dict[str, pd.DataFrame]
        {ticker: DataFrame} dictionary
    benchmark_data : pd.DataFrame
        Benchmark index data
    benchmark_ticker : str
        Benchmark ticker name

    Returns
    -------
    pd.DataFrame
        Merged return DataFrame
    """
    combined = pd.DataFrame()

    # Add benchmark index
    benchmark_close = benchmark_data["Close"]
    if isinstance(benchmark_close, pd.DataFrame):
        benchmark_close = benchmark_close.iloc[:, 0]
    combined[f"{benchmark_ticker}_Price"] = benchmark_close

    # Add all tickers
    for ticker, data in all_data.items():
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        combined[f"{ticker}_Price"] = close

    # Align dates (keep only dates with data for all tickers)
    combined = combined.dropna()

    # Calculate returns
    combined[f"{benchmark_ticker}_Return%"] = calculate_cumulative_return_series(
        combined[f"{benchmark_ticker}_Price"]
    )

    for ticker in all_data.keys():
        combined[f"{ticker}_Return%"] = calculate_cumulative_return_series(
            combined[f"{ticker}_Price"]
        )

    return combined


def analyze_returns(
    tickers: List[str],
    start_year: int,
    year_only: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Analyze cumulative returns for multiple tickers

    Parameters
    ----------
    tickers : List[str]
        List of ticker symbols
    start_year : int
        Start year
    year_only : bool
        If True, analyze only the specified year (not to today)

    Note
    ----
    Benchmark is hardcoded to S&P 500 (^GSPC) - this is a core methodology decision.
    All comparisons use S&P 500 as the reference benchmark.

    Returns
    -------
    Tuple[pd.DataFrame, Dict]
        (Cumulative return DataFrame, analysis result dictionary)
    """
    # S&P 500 is the fixed benchmark - core methodology decision
    benchmark = "^GSPC"

    # Fetch from previous year December to get the last trading day of previous year
    start_date = f"{start_year - 1}-12-01"

    if year_only:
        # Year only mode: end at Dec 31 of the specified year
        end_date = f"{start_year}-12-31"
        mode_label = "year_only"
    else:
        # Year to today mode: end at today
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        mode_label = "year_to_today"

    print(f"\nFetching data...")

    # Fetch all ticker data
    all_data = fetch_multiple_prices(tickers, start_date, end_date)

    # Fetch benchmark data
    print(f"  [Fetch] {get_ticker_name(benchmark)} (benchmark)...")
    benchmark_data = fetch_price_data(benchmark, start_date, end_date)

    # Find the last trading day of the previous year (base date for return calculation)
    # This is the last day BEFORE the specified year starts
    year_start = f"{start_year}-01-01"

    # Get the last trading day of previous year from benchmark data
    prev_year_data = benchmark_data[benchmark_data.index < year_start]
    if prev_year_data.empty:
        raise ValueError(f"No data found for the last trading day of {start_year - 1}")

    base_date = prev_year_data.index[-1]  # Last trading day of previous year
    print(f"  [Base] Using {base_date.strftime('%Y-%m-%d')} as base date (last trading day of {start_year - 1})")

    # Filter data from base_date onward (include the base date)
    for ticker in list(all_data.keys()):
        all_data[ticker] = all_data[ticker][all_data[ticker].index >= base_date]
    benchmark_data = benchmark_data[benchmark_data.index >= base_date]

    # Create cumulative return DataFrame
    print("\nCalculating cumulative returns...")
    df = create_cumulative_dataframe(all_data, benchmark_data, benchmark)

    # Calculate statistics
    latest = df.iloc[-1]
    first = df.iloc[0]
    days_held = (df.index[-1] - df.index[0]).days
    years_held = days_held / 365.25

    # Build results list
    results = []
    for ticker in tickers:
        if f"{ticker}_Return%" not in df.columns:
            continue

        cum_return = latest[f"{ticker}_Return%"]
        price_start = first[f"{ticker}_Price"]
        price_end = latest[f"{ticker}_Price"]
        cagr = calculate_cagr(df[f"{ticker}_Price"])
        vs_benchmark = cum_return - latest[f"{benchmark}_Return%"]

        results.append(
            {
                "ticker": ticker,
                "name": get_ticker_name(ticker),
                "cumulative_return_pct": round(cum_return, 2),
                "cagr_pct": round(cagr, 2),
                "vs_benchmark": round(vs_benchmark, 2),
                "price_start": round(price_start, 2),
                "price_end": round(price_end, 2),
            }
        )

    # Sort by return (descending)
    results.sort(key=lambda x: x["cumulative_return_pct"], reverse=True)

    # Benchmark data
    benchmark_return = latest[f"{benchmark}_Return%"]
    benchmark_cagr = calculate_cagr(df[f"{benchmark}_Price"])

    # Summary statistics
    beat_benchmark_count = sum(1 for r in results if r["cumulative_return_pct"] > benchmark_return)
    best = results[0] if results else None

    summary = {
        "skill": "track-equity-cumulative-return",
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "mode": mode_label,
        "parameters": {
            "tickers": tickers,
            "start_year": start_year,
            "year_only": year_only,
            "benchmark": benchmark,
        },
        "period": {
            "start_date": df.index[0].strftime("%Y-%m-%d"),
            "end_date": df.index[-1].strftime("%Y-%m-%d"),
            "days_held": days_held,
            "years_held": round(years_held, 2),
        },
        "benchmark": {
            "ticker": benchmark,
            "name": get_ticker_name(benchmark),
            "cumulative_return_pct": round(benchmark_return, 2),
            "cagr_pct": round(benchmark_cagr, 2),
        },
        "summary": {
            "best_performer": best["ticker"] if best else None,
            "best_return": best["cumulative_return_pct"] if best else None,
            "benchmark_return": round(benchmark_return, 2),
            "beat_benchmark_count": beat_benchmark_count,
            "total_count": len(results),
        },
        "results": results,
    }

    return df, summary


def print_summary_table(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    last_n_days: int = 5,
) -> None:
    """
    Print summary report

    Parameters
    ----------
    df : pd.DataFrame
        Cumulative return DataFrame
    summary : Dict
        Analysis result dictionary
    last_n_days : int
        Show last N days
    """
    params = summary["parameters"]
    period = summary["period"]
    benchmark = summary["benchmark"]
    results = summary["results"]
    year_only = params.get("year_only", False)

    print("\n" + "=" * 90)
    print(f"Cumulative Return Analysis Report")
    print("=" * 90)

    if year_only:
        print(f"Period: {params['start_year']} Full Year ({period['start_date']} ~ {period['end_date']})")
    else:
        print(f"Period: {period['start_date']} ~ {period['end_date']} ({period['years_held']:.1f} years)")

    print(f"Benchmark: {benchmark['name']}")
    print("=" * 90)

    # Ranking table
    print(f"\n{'Rank':<5} {'Ticker':<8} {'Name':<20} {'Cum. Return':>12} {'CAGR':>12} {'vs Bench':>10}")
    print("-" * 90)

    for i, r in enumerate(results, 1):
        beat = "✓" if r["cumulative_return_pct"] > benchmark["cumulative_return_pct"] else ""
        print(
            f"{i:<5} {r['ticker']:<8} {r['name']:<20} "
            f"{r['cumulative_return_pct']:>+11.2f}% {r['cagr_pct']:>+11.2f}% "
            f"{r['vs_benchmark']:>+9.2f}% {beat}"
        )

    print("-" * 90)
    print(
        f"{'Bench':<5} {benchmark['ticker']:<8} {benchmark['name']:<20} "
        f"{benchmark['cumulative_return_pct']:>+11.2f}% {benchmark['cagr_pct']:>+11.2f}%"
    )
    print("=" * 90)

    # Statistics
    s = summary["summary"]
    print(f"\nStatistics:")
    print(f"  - Best performer: {s['best_performer']} ({s['best_return']:+.2f}%)")
    print(f"  - Beat benchmark: {s['beat_benchmark_count']} / {s['total_count']}")
    if results:
        avg_return = sum(r["cumulative_return_pct"] for r in results) / len(results)
        print(f"  - Average return: {avg_return:+.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate cumulative returns and CAGR for stocks/indices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ticker, year to today (mode 1.b)
  python cumulative_return_analyzer.py --ticker NVDA --year 2022

  # Single ticker, specific year only (mode 1.a)
  python cumulative_return_analyzer.py --ticker NVDA --year 2024 --year-only

  # Multiple tickers, year to today
  python cumulative_return_analyzer.py --ticker NVDA AMD GOOGL --year 2022

  # Multiple tickers, specific year only
  python cumulative_return_analyzer.py --ticker NVDA AMD --year 2024 --year-only
        """,
    )
    parser.add_argument(
        "--ticker",
        "-t",
        type=str,
        nargs="+",
        default=["NVDA"],
        help="Ticker symbol(s)",
    )
    parser.add_argument(
        "--year", "-y", type=int, default=2022, help="Start year (default: 2022)"
    )
    parser.add_argument(
        "--year-only",
        action="store_true",
        help="Analyze only the specified year (not to today)",
    )
    # Note: Benchmark is hardcoded to S&P 500 (^GSPC) - core methodology decision
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    print("\n" + "=" * 90)
    print("Cumulative Return Tracker")
    print(f"Tickers: {', '.join(args.ticker)}")
    print(f"Benchmark: S&P 500 (^GSPC) [Fixed]")
    if args.year_only:
        print(f"Period: {args.year} Full Year")
    else:
        print(f"Period: From {args.year} to Today")
    print("=" * 90)

    # Analyze (benchmark is hardcoded to S&P 500)
    df, summary = analyze_returns(args.ticker, args.year, args.year_only)

    # Print report
    print_summary_table(df, summary)

    # Output JSON
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_path}")

    return df, summary


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    df, summary = main()
