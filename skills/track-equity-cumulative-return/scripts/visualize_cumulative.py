#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cumulative Return Visualization Module

Generate cumulative return comparison charts.

Usage:
    # Year to today (default)
    python visualize_cumulative.py --ticker NVDA AMD --year 2022

    # Year only (full year)
    python visualize_cumulative.py --ticker NVDA AMD --year 2024 --year-only

    # Index Top N to today
    python visualize_cumulative.py --mode top20 --index nasdaq100 --year 2022

    # Index Top N year only
    python visualize_cumulative.py --mode top20 --index nasdaq100 --year 2024 --year-only
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from fetch_price_data import get_ticker_name
from cumulative_return_analyzer import analyze_returns
from index_component_analyzer import (
    analyze_index_components,
    create_comparison_dataframe,
    get_index_config,
    INDEX_CONFIG,
)


# ========== Bloomberg Style Color Scheme (per bloomberg-style-chart-guide.md) ==========
COLORS = {
    # Background and grid
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    # Text
    "text": "#ffffff",
    "text_dim": "#888888",
    # Primary data lines
    "primary": "#ff6b35",      # Orange-red
    "secondary": "#ffaa00",    # Orange-yellow
    # Auxiliary lines
    "zero_line": "#666666",
    "benchmark": "#004E89",    # Deep blue (benchmark line)
}

# Multi-ticker color palette (cycle through)
LINE_COLORS = [
    "#ff6b35",  # Orange-red
    "#ffaa00",  # Orange-yellow
    "#00ff88",  # Green
    "#00bfff",  # Blue
    "#cc66ff",  # Purple
    "#ff66b2",  # Pink
    "#ffff00",  # Yellow
    "#00ffff",  # Cyan
    "#ff4444",  # Red
    "#88ff88",  # Light green
    "#8888ff",  # Light blue
    "#ff88ff",  # Light purple
    "#ffcc00",  # Gold
    "#00ff00",  # Bright green
    "#ff8800",  # Orange
    "#0088ff",  # Sky blue
    "#ff0088",  # Magenta
    "#88ffff",  # Light cyan
    "#ffff88",  # Light yellow
    "#ff8888",  # Light red
]

# Font settings (with CJK fallback for compatibility)
plt.rcParams["font.sans-serif"] = [
    "Microsoft JhengHei",
    "SimHei",
    "Microsoft YaHei",
    "PingFang TC",
    "Noto Sans CJK TC",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def setup_bloomberg_style():
    """Set up Bloomberg style"""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"],
        "axes.facecolor": COLORS["background"],
        "axes.edgecolor": COLORS["grid"],
        "axes.labelcolor": COLORS["text"],
        "axes.grid": True,
        "grid.color": COLORS["grid"],
        "grid.alpha": 0.3,
        "grid.linestyle": "-",
        "grid.linewidth": 0.5,
        "text.color": COLORS["text"],
        "xtick.color": COLORS["text_dim"],
        "ytick.color": COLORS["text_dim"],
        "legend.facecolor": COLORS["background"],
        "legend.edgecolor": COLORS["grid"],
        "legend.labelcolor": COLORS["text"],
        "font.size": 10,
    })


def format_percent(x, pos):
    """Format percentage values"""
    return f"{x:+.0f}%"


def format_date_axis(x, pos):
    """
    Format date axis: show year in January, month number (2-12) for other months
    """
    try:
        date = mdates.num2date(x)
        if date.month == 1:
            return date.strftime("%Y")
        else:
            return str(date.month)
    except Exception:
        return ""


def plot_cumulative_comparison(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    output_path: Optional[str] = None,
    figsize: tuple = (14, 8),
) -> None:
    """
    Plot multi-ticker cumulative return comparison chart (Bloomberg style)

    Parameters
    ----------
    df : pd.DataFrame
        Cumulative return DataFrame
    summary : Dict
        Analysis result summary
    output_path : str, optional
        Output path
    figsize : tuple
        Chart size
    """
    setup_bloomberg_style()

    params = summary["parameters"]
    period = summary["period"]
    benchmark = summary["benchmark"]
    results = summary["results"]
    tickers = params["tickers"]

    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])

    # Plot all tickers
    for i, ticker in enumerate(tickers):
        col = f"{ticker}_Return%"
        if col not in df.columns:
            continue

        color = LINE_COLORS[i % len(LINE_COLORS)]
        label = get_ticker_name(ticker)

        # Get final return value for this ticker
        final_return = df[col].iloc[-1]

        ax.plot(
            df.index,
            df[col],
            color=color,
            linewidth=2,
            label=f"{label} ({final_return:+.1f}%)",
            zorder=4,
        )

        # Annotate final value
        ax.annotate(
            f"{final_return:+.1f}%",
            xy=(df.index[-1], final_return),
            xytext=(10, 0),
            textcoords="offset points",
            color=color,
            fontsize=10,
            fontweight="bold",
            va="center",
        )

    # Plot benchmark line (dashed)
    benchmark_col = f"{benchmark['ticker']}_Return%"
    if benchmark_col in df.columns:
        benchmark_return = df[benchmark_col].iloc[-1]
        ax.plot(
            df.index,
            df[benchmark_col],
            color=COLORS["benchmark"],
            linewidth=2.5,
            linestyle="--",
            label=f"{benchmark['name']} Benchmark ({benchmark_return:+.1f}%)",
            zorder=3,
        )

    # Zero line
    ax.axhline(y=0, color=COLORS["zero_line"], linewidth=1, linestyle=":", alpha=0.7, zorder=2)

    # Grid
    ax.grid(True, color=COLORS["grid"], alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)

    # X-axis settings: year in January, month number (2-12) for other months
    ax.xaxis.set_major_formatter(FuncFormatter(format_date_axis))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.tick_params(axis="x", colors=COLORS["text_dim"], rotation=0)

    # Y-axis settings
    ax.yaxis.set_major_formatter(FuncFormatter(format_percent))
    ax.tick_params(axis="y", colors=COLORS["text_dim"])
    ax.set_ylabel("Cumulative Return", color=COLORS["text"], fontsize=11)

    # Legend
    ax.legend(
        loc="upper left",
        fontsize=9,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"],
    )

    # Title - check if year_only mode
    year_only = params.get("year_only", False)
    if year_only:
        title = f"{params['start_year']} Full Year Cumulative Return Comparison"
        subtitle = f"{period['start_date']} ~ {period['end_date']} (Full Year)"
    else:
        title = f"Cumulative Return Comparison Since {params['start_year']}"
        subtitle = f"{period['start_date']} ~ {period['end_date']} ({period['years_held']:.1f} years)"
    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight="bold", y=0.98)
    ax.set_title(subtitle, color=COLORS["text_dim"], fontsize=10, pad=10)

    # Footer
    fig.text(
        0.02, 0.02,
        "Source: Yahoo Finance",
        color=COLORS["text_dim"],
        fontsize=8,
        ha="left",
    )
    fig.text(
        0.98, 0.02,
        f"As of: {period['end_date']}",
        color=COLORS["text_dim"],
        fontsize=8,
        ha="right",
    )

    # Output
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, bottom=0.08)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(
            output_path,
            dpi=150,
            facecolor=COLORS["background"],
            edgecolor="none",
            bbox_inches="tight",
        )
        print(f"\n[Chart] Saved to: {output_path}")
    else:
        plt.show()

    plt.close()


def plot_top20_chart(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    top_stocks: List[Dict],
    output_path: Optional[str] = None,
    figsize: tuple = (16, 10),
) -> None:
    """
    Plot index Top N performance chart (Bloomberg style)

    Parameters
    ----------
    df : pd.DataFrame
        Comparison DataFrame
    summary : Dict
        Analysis result summary
    top_stocks : List[Dict]
        Top N stock list
    output_path : str, optional
        Output path
    figsize : tuple
        Chart size
    """
    setup_bloomberg_style()

    params = summary["parameters"]
    period = summary["period"]
    benchmark = summary["benchmark"]
    top_performers = summary["top_performers"]

    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])

    # Plot all Top N tickers
    for i, stock in enumerate(top_stocks):
        ticker = stock["ticker"]
        col = f"{ticker}_Return%"
        if col not in df.columns:
            continue

        color = LINE_COLORS[i % len(LINE_COLORS)]
        final_return = df[col].iloc[-1]

        ax.plot(
            df.index,
            df[col],
            color=color,
            linewidth=1.5,
            alpha=0.85,
            label=f"{ticker} ({final_return:+.1f}%)",
            zorder=4,
        )

    # Plot benchmark line (thick dashed)
    benchmark_ticker = benchmark["ticker"]
    benchmark_col = f"{benchmark_ticker}_Return%"
    if benchmark_col in df.columns:
        benchmark_return = df[benchmark_col].iloc[-1]
        ax.plot(
            df.index,
            df[benchmark_col],
            color=COLORS["benchmark"],
            linewidth=3,
            linestyle="--",
            label=f"{benchmark['name']} Benchmark ({benchmark_return:+.1f}%)",
            zorder=5,
        )

    # Zero line
    ax.axhline(y=0, color=COLORS["zero_line"], linewidth=1, linestyle=":", alpha=0.7, zorder=2)

    # Grid
    ax.grid(True, color=COLORS["grid"], alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)

    # X-axis settings: year in January, month number (2-12) for other months
    ax.xaxis.set_major_formatter(FuncFormatter(format_date_axis))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.tick_params(axis="x", colors=COLORS["text_dim"], rotation=0)

    # Y-axis settings
    ax.yaxis.set_major_formatter(FuncFormatter(format_percent))
    ax.tick_params(axis="y", colors=COLORS["text_dim"])
    ax.set_ylabel("Cumulative Return", color=COLORS["text"], fontsize=11)

    # Legend (on right side)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        fontsize=8,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"],
    )

    # Title - check if year_only mode
    index_name = params["index_name"]
    year_only = params.get("year_only", False)
    if year_only:
        title = f"{index_name} Top {params['top_n']} Performance ({params['start_year']} Full Year)"
        subtitle = f"{period['start_date']} ~ {period['end_date']} | Best: {top_performers[0]['ticker']} {top_performers[0]['cumulative_return_pct']:+.1f}%"
    else:
        title = f"{index_name} Top {params['top_n']} Performance vs {benchmark['name']}"
        subtitle = f"{period['start_date']} ~ {period['end_date']} ({period['years_held']:.1f} years) | Best: {top_performers[0]['ticker']} {top_performers[0]['cumulative_return_pct']:+.1f}%"
    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight="bold", y=0.98)
    ax.set_title(subtitle, color=COLORS["text_dim"], fontsize=10, pad=10)

    # Footer
    fig.text(
        0.02, 0.02,
        "Source: Yahoo Finance",
        color=COLORS["text_dim"],
        fontsize=8,
        ha="left",
    )
    fig.text(
        0.98, 0.02,
        f"As of: {period['end_date']}",
        color=COLORS["text_dim"],
        fontsize=8,
        ha="right",
    )

    # Output
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, bottom=0.08, right=0.85)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(
            output_path,
            dpi=150,
            facecolor=COLORS["background"],
            edgecolor="none",
            bbox_inches="tight",
        )
        print(f"\n[Chart] Saved to: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate cumulative return visualization (Bloomberg style)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Multi-ticker comparison (year to today)
  python visualize_cumulative.py --ticker NVDA AMD --year 2022

  # Multi-ticker comparison (year only)
  python visualize_cumulative.py --ticker NVDA AMD --year 2024 --year-only

  # Index Top N analysis (year to today)
  python visualize_cumulative.py --mode top20 --index nasdaq100 --year 2022

  # Index Top N analysis (year only)
  python visualize_cumulative.py --mode top20 --index sox --year 2024 --year-only
        """,
    )
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        default="compare",
        choices=["compare", "top20"],
        help="Mode: compare (multi-ticker) or top20 (index Top N)",
    )
    parser.add_argument(
        "--ticker",
        "-t",
        type=str,
        nargs="+",
        default=["NVDA", "AMD"],
        help="Ticker symbol(s) (for compare mode)",
    )
    parser.add_argument(
        "--index",
        "-i",
        type=str,
        default="nasdaq100",
        choices=list(INDEX_CONFIG.keys()),
        help="Index type (for top20 mode)",
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
        "--output", "-o", type=str, default=None, help="Output PNG file path"
    )
    parser.add_argument(
        "--top", type=int, default=20, help="Top N (for top20 mode)"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Cumulative Return Visualization (Bloomberg Style)")
    print("=" * 60)

    if args.mode == "compare":
        # Multi-ticker comparison mode
        print(f"Mode: Multi-ticker comparison")
        print(f"Tickers: {', '.join(args.ticker)}")
        if args.year_only:
            print(f"Period: {args.year} Full Year")
        else:
            print(f"Period: From {args.year} to Today")
        print(f"Benchmark: S&P 500 (^GSPC) [Fixed]")
        print("=" * 60)

        df, summary = analyze_returns(args.ticker, args.year, args.year_only)

        # Determine output path - use current working directory, not skill folder
        if args.output:
            output_path = args.output
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            suffix = f"_{args.year}_only" if args.year_only else ""
            output_path = Path.cwd() / "output" / f"cumulative_return{suffix}_{today}.png"

        plot_cumulative_comparison(df, summary, str(output_path))

    else:
        # Top N mode
        config = get_index_config(args.index)
        print(f"Mode: Index Top {args.top}")
        print(f"Index: {config['name']}")
        if args.year_only:
            print(f"Period: {args.year} Full Year")
        else:
            print(f"Period: From {args.year} to Today")
        print("=" * 60)

        top_stocks, all_results, summary = analyze_index_components(
            args.index, args.year, args.top, args.year_only
        )

        # Build comparison DataFrame
        from fetch_price_data import fetch_price_data
        from datetime import timedelta

        benchmark_ticker = summary["benchmark"]["ticker"]
        start_date = f"{args.year - 1}-12-01"

        if args.year_only:
            end_date = f"{args.year}-12-31"
        else:
            end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Use the base_date from summary (last trading day of previous year)
        base_date_str = summary["period"]["start_date"]

        benchmark_data = fetch_price_data(benchmark_ticker, start_date, end_date)
        benchmark_data = benchmark_data[benchmark_data.index >= base_date_str]

        comparison_df = create_comparison_dataframe(top_stocks, benchmark_data, benchmark_ticker)

        # Determine output path - use current working directory, not skill folder
        if args.output:
            output_path = args.output
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            safe_name = args.index.replace(" ", "_")
            suffix = f"_{args.year}_only" if args.year_only else ""
            output_path = Path.cwd() / "output" / f"{safe_name}_top{args.top}{suffix}_{today}.png"

        plot_top20_chart(comparison_df, summary, top_stocks, str(output_path))

    print("\nDone!")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    main()
