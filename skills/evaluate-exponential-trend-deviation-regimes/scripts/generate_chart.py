#!/usr/bin/env python3
"""
Generate Gold Deviation Analysis Chart

Visualizes gold price deviation from exponential trend with historical peak comparisons.

Usage:
    python generate_chart.py --output ./output/
    python generate_chart.py --output ./output/ --symbol xauusd
"""

import argparse
import json
import os
import sys
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def fetch_gold_data(symbol: str = "xauusd", start_date: str = "19700101") -> pd.Series:
    """Fetch gold price data from Stooq."""
    end_date = datetime.now().strftime("%Y%m%d")
    url = f"https://stooq.com/q/d/l/?s={symbol}&d1={start_date}&d2={end_date}&i=m"

    print(f"Fetching data from Stooq ({symbol})...")
    gold = pd.read_csv(url)
    gold["Date"] = pd.to_datetime(gold["Date"])
    gold = gold.set_index("Date").sort_index()
    return gold["Close"].dropna()


def fit_exponential_trend(prices: pd.Series) -> tuple[pd.Series, tuple[float, float]]:
    """Fit exponential trend line to price series."""
    t = np.arange(len(prices))
    y = np.log(prices.values)
    X = np.vstack([np.ones_like(t), t]).T
    params, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a, b = params
    trend = np.exp(a + b * t)
    return pd.Series(trend, index=prices.index), (float(a), float(b))


def generate_chart(
    monthly_prices: pd.Series,
    trend_series: pd.Series,
    distance_pct: pd.Series,
    output_dir: str,
) -> tuple[str, str]:
    """Generate and save the deviation chart."""

    # Set style
    plt.style.use("ggplot")
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["figure.facecolor"] = "white"

    # Find key dates
    peak_1980_date = distance_pct.loc["1980-01":"1980-02"].idxmax()
    peak_1980_val = distance_pct.loc[peak_1980_date]
    peak_2011_date = distance_pct.loc["2011-08":"2011-10"].idxmax()
    peak_2011_val = distance_pct.loc[peak_2011_date]
    current_date = distance_pct.index[-1]
    current_val = distance_pct.iloc[-1]

    # Create figure
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[1.2, 1])
    fig.suptitle("Gold Exponential Trend Deviation Analysis", fontsize=16, fontweight="bold", y=0.98)

    # ===== Panel 1: Gold Price with Trend =====
    ax1 = axes[0]
    ax1.semilogy(monthly_prices.index, monthly_prices.values, "goldenrod", linewidth=1.5, label="Gold Price (USD)", alpha=0.9)
    ax1.semilogy(trend_series.index, trend_series.values, "navy", linewidth=2, linestyle="--", label="Exponential Trend", alpha=0.8)

    ax1.axvline(peak_1980_date, color="red", alpha=0.3, linestyle=":")
    ax1.axvline(peak_2011_date, color="orange", alpha=0.3, linestyle=":")

    ax1.set_ylabel("Gold Price (USD, log scale)")
    ax1.set_title("Gold Price vs Long-term Exponential Trend (1970-present)")
    ax1.legend(loc="upper left")
    ax1.set_xlim(monthly_prices.index[0], monthly_prices.index[-1])
    ax1.xaxis.set_major_locator(mdates.YearLocator(5))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax1.annotate(
        f"Current: ${monthly_prices.iloc[-1]:,.0f}",
        xy=(current_date, monthly_prices.iloc[-1]),
        xytext=(10, 0), textcoords="offset points",
        fontsize=10, color="goldenrod", fontweight="bold"
    )

    # ===== Panel 2: Deviation Percentage =====
    ax2 = axes[1]

    ax2.fill_between(distance_pct.index, 0, distance_pct.values,
                      where=(distance_pct.values > 0), color="green", alpha=0.3, label="Above trend")
    ax2.fill_between(distance_pct.index, 0, distance_pct.values,
                      where=(distance_pct.values <= 0), color="red", alpha=0.3, label="Below trend")
    ax2.plot(distance_pct.index, distance_pct.values, "black", linewidth=1.2)

    ax2.axhline(y=peak_2011_val, color="orange", linestyle="--", alpha=0.7, linewidth=1.5)
    ax2.axhline(y=0, color="gray", linestyle="-", alpha=0.5, linewidth=1)

    ax2.scatter([peak_1980_date], [peak_1980_val], color="red", s=100, zorder=5, marker="o")
    ax2.scatter([peak_2011_date], [peak_2011_val], color="orange", s=100, zorder=5, marker="o")
    ax2.scatter([current_date], [current_val], color="blue", s=120, zorder=5, marker="D")

    ax2.annotate(f"1980 Peak\n{peak_1980_val:.0f}%",
                 xy=(peak_1980_date, peak_1980_val),
                 xytext=(-60, -30), textcoords="offset points",
                 fontsize=10, color="red", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="red", alpha=0.7))

    ax2.annotate(f"2011 Peak\n{peak_2011_val:.0f}%",
                 xy=(peak_2011_date, peak_2011_val),
                 xytext=(30, 30), textcoords="offset points",
                 fontsize=10, color="orange", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="orange", alpha=0.7))

    ax2.annotate(f"Current\n{current_val:.0f}%",
                 xy=(current_date, current_val),
                 xytext=(-80, 30), textcoords="offset points",
                 fontsize=11, color="blue", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="blue", alpha=0.7))

    # Text box with verdict
    surpassed = current_val > peak_2011_val
    diff = current_val - peak_2011_val
    textstr = f"Current Deviation: {current_val:.1f}%\n2011 Peak: {peak_2011_val:.1f}%\nSurpassed 2011: {'YES' if surpassed else 'NO'} ({diff:+.1f} ppt)"
    props = dict(boxstyle="round", facecolor="lightyellow", alpha=0.9, edgecolor="orange")
    ax2.text(0.02, 0.97, textstr, transform=ax2.transAxes, fontsize=10,
             verticalalignment="top", bbox=props, fontweight="bold")

    ax2.set_ylabel("Deviation from Trend (%)")
    ax2.set_xlabel("Date")
    ax2.set_title("Gold % Distance from Exponential Growth Trendline")
    ax2.set_xlim(monthly_prices.index[0], monthly_prices.index[-1])
    ax2.xaxis.set_major_locator(mdates.YearLocator(5))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()

    # Save chart
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(output_dir, exist_ok=True)

    chart_path = os.path.join(output_dir, f"gold-deviation-analysis_{today}.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    return chart_path, (peak_1980_date, peak_1980_val, peak_2011_date, peak_2011_val, current_date, current_val)


def save_json_summary(
    monthly_prices: pd.Series,
    trend_series: pd.Series,
    distance_pct: pd.Series,
    trend_params: tuple[float, float],
    peaks: tuple,
    output_dir: str,
) -> str:
    """Save JSON summary of the analysis."""
    peak_1980_date, peak_1980_val, peak_2011_date, peak_2011_val, current_date, current_val = peaks
    a, b = trend_params

    summary = {
        "skill": "evaluate-exponential-trend-deviation-regimes",
        "asset": "Gold (XAU/USD)",
        "as_of": current_date.strftime("%Y-%m-%d"),
        "metrics": {
            "current_price_usd": round(float(monthly_prices.iloc[-1]), 2),
            "trend_price_usd": round(float(trend_series.iloc[-1]), 2),
            "current_deviation_pct": round(float(current_val), 1),
            "historical_percentile": round((distance_pct < current_val).sum() / len(distance_pct) * 100, 1),
        },
        "reference_peaks": {
            "1980_peak": {
                "date": peak_1980_date.strftime("%Y-%m-%d"),
                "deviation_pct": round(float(peak_1980_val), 1)
            },
            "2011_peak": {
                "date": peak_2011_date.strftime("%Y-%m-%d"),
                "deviation_pct": round(float(peak_2011_val), 1)
            }
        },
        "verdict": {
            "surpassed_2011": bool(current_val > peak_2011_val),
            "difference_from_2011_ppt": round(float(current_val - peak_2011_val), 1),
            "remaining_to_1980_ppt": round(float(peak_1980_val - current_val), 1)
        },
        "trend_parameters": {
            "a": round(float(a), 4),
            "b": round(float(b), 6),
            "annualized_growth_rate_pct": round((np.exp(b * 12) - 1) * 100, 2)
        }
    }

    today = datetime.now().strftime("%Y-%m-%d")
    json_path = os.path.join(output_dir, f"gold-deviation-analysis_{today}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return json_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Gold Deviation Analysis Chart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_chart.py --output ./output/
  python generate_chart.py --output ./output/ --symbol xauusd
        """,
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="Output directory for chart and JSON (default: ./output)",
    )
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        default="xauusd",
        help="Stooq symbol for gold (default: xauusd)",
    )

    args = parser.parse_args()

    try:
        # Fetch data
        monthly_prices = fetch_gold_data(args.symbol)
        print(f"Data range: {monthly_prices.index[0].date()} to {monthly_prices.index[-1].date()}")
        print(f"Data points: {len(monthly_prices)}")

        # Fit trend
        trend_series, trend_params = fit_exponential_trend(monthly_prices)

        # Calculate deviation
        distance_pct = (monthly_prices / trend_series - 1.0) * 100.0

        # Generate chart
        chart_path, peaks = generate_chart(monthly_prices, trend_series, distance_pct, args.output)
        print(f"Chart saved to: {chart_path}")

        # Save JSON
        json_path = save_json_summary(monthly_prices, trend_series, distance_pct, trend_params, peaks, args.output)
        print(f"JSON saved to: {json_path}")

        # Print summary
        current_val = distance_pct.iloc[-1]
        peak_2011_val = peaks[3]
        print()
        print(f"Current deviation: {current_val:.1f}%")
        print(f"2011 peak: {peak_2011_val:.1f}%")
        print(f"Surpassed 2011: {'YES' if current_val > peak_2011_val else 'NO'}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
