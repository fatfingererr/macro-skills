#!/usr/bin/env python3
"""
銀行信貸-存款脫鉤視覺化

生成 Bloomberg 風格的脫鉤分析圖表。

Usage:
    python visualize_decoupling.py --start 2022-06-01
    python visualize_decoupling.py --start 2022-06-01 --output chart.png
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Patch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Run: pip install matplotlib")


# ============================================================================
# Configuration
# ============================================================================

STYLE_CONFIG = {
    # Bloomberg-style dark theme
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#4a4a6a",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#a0a0a0",
    "ytick.color": "#a0a0a0",
    "grid.color": "#2a2a4a",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
}

COLORS = {
    "loans": "#4fc3f7",      # Light blue
    "deposits": "#81c784",   # Light green
    "rrp": "#ef5350",        # Red
    "gap": "#ffa726",        # Orange
    "stress": "#ba68c8",     # Purple
}


# ============================================================================
# Data Loading
# ============================================================================

def load_analysis_data(cache_dir: Path) -> Dict[str, pd.Series]:
    """Load data from cache files."""
    data = {}

    series_map = {
        "loans": "TOTLL",
        "deposits": "DPSACBW027SBOG",
        "rrp": "RRPONTSYD"
    }

    for name, series_id in series_map.items():
        cache_file = cache_dir / f"{series_id}.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                cached = json.load(f)
            series = pd.Series(cached["data"])
            series.index = pd.to_datetime(series.index)
            data[name] = series
        else:
            print(f"Warning: Cache file not found for {series_id}")

    return data


def calculate_plot_data(
    data: Dict[str, pd.Series],
    start_date: str
) -> Dict[str, pd.Series]:
    """Calculate cumulative changes and metrics for plotting."""
    loans = data["loans"]
    deposits = data["deposits"]
    rrp = data["rrp"]

    # Filter by start date
    start = pd.to_datetime(start_date)
    loans = loans[loans.index >= start]
    deposits = deposits[deposits.index >= start]
    rrp = rrp[rrp.index >= start]

    # Resample RRP to weekly if needed
    if len(rrp) > len(loans) * 2:
        rrp = rrp.resample("W-WED").last()

    # Align to common dates
    common_idx = loans.index.intersection(deposits.index).intersection(rrp.index)
    loans = loans.loc[common_idx]
    deposits = deposits.loc[common_idx]
    rrp = rrp.loc[common_idx]

    # Calculate cumulative changes
    loan_change = loans - loans.iloc[0]
    deposit_change = deposits - deposits.iloc[0]
    rrp_change = rrp - rrp.iloc[0]
    gap = loan_change - deposit_change

    # Calculate stress ratio
    with np.errstate(divide='ignore', invalid='ignore'):
        stress_ratio = gap / loan_change
        stress_ratio = stress_ratio.replace([np.inf, -np.inf], np.nan)

    return {
        "dates": common_idx,
        "loan_change": loan_change,
        "deposit_change": deposit_change,
        "rrp_change": rrp_change,
        "gap": gap,
        "stress_ratio": stress_ratio
    }


# ============================================================================
# Plotting
# ============================================================================

def create_decoupling_chart(
    plot_data: Dict[str, pd.Series],
    output_path: Optional[str] = None,
    title: str = "Bank Credit-Deposit Decoupling Analysis"
) -> None:
    """Create the decoupling analysis chart."""
    if not HAS_MATPLOTLIB:
        print("Cannot create chart: matplotlib not installed")
        return

    # Apply style
    plt.rcParams.update(STYLE_CONFIG)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(14, 10),
        gridspec_kw={"height_ratios": [2, 1]},
        sharex=True
    )

    dates = plot_data["dates"]

    # =========================================================================
    # Top panel: Cumulative changes
    # =========================================================================

    # Plot lines
    ax1.plot(
        dates, plot_data["loan_change"],
        color=COLORS["loans"], linewidth=2, label="累積新增貸款"
    )
    ax1.plot(
        dates, plot_data["deposit_change"],
        color=COLORS["deposits"], linewidth=2, label="累積新增存款"
    )
    ax1.plot(
        dates, plot_data["rrp_change"],
        color=COLORS["rrp"], linewidth=1.5, linestyle="--", label="累積 RRP 變化"
    )

    # Fill gap area
    ax1.fill_between(
        dates,
        plot_data["deposit_change"],
        plot_data["loan_change"],
        where=plot_data["loan_change"] > plot_data["deposit_change"],
        alpha=0.3,
        color=COLORS["gap"],
        label="Decoupling Gap"
    )

    # Formatting
    ax1.set_ylabel("累積變化 (Billions USD)", fontsize=11)
    ax1.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Title
    ax1.set_title(
        f"{title}\n銀行信貸-存款脫鉤分析",
        fontsize=14,
        fontweight="bold",
        pad=10
    )

    # Add annotation for latest gap
    latest_gap = plot_data["gap"].iloc[-1]
    latest_date = dates[-1]
    ax1.annotate(
        f"Gap: ${latest_gap/1000:.2f}T",
        xy=(latest_date, latest_gap + plot_data["deposit_change"].iloc[-1]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=10,
        color=COLORS["gap"],
        fontweight="bold"
    )

    # =========================================================================
    # Bottom panel: Stress ratio
    # =========================================================================

    ax2.plot(
        dates, plot_data["stress_ratio"],
        color=COLORS["stress"], linewidth=2, label="Deposit Stress Ratio"
    )

    # Threshold lines
    thresholds = [
        (0.3, "Low", "#4caf50"),
        (0.5, "Medium", "#ffeb3b"),
        (0.7, "High", "#ff9800"),
        (0.85, "Extreme", "#f44336")
    ]

    for thresh, label, color in thresholds:
        ax2.axhline(y=thresh, color=color, linestyle=":", alpha=0.7, linewidth=1)
        ax2.text(
            dates[0], thresh + 0.02, label,
            fontsize=8, color=color, alpha=0.8
        )

    # Fill zones
    y_max = max(1.0, plot_data["stress_ratio"].max() * 1.1)
    ax2.fill_between(dates, 0, 0.3, alpha=0.1, color="#4caf50")
    ax2.fill_between(dates, 0.3, 0.5, alpha=0.1, color="#ffeb3b")
    ax2.fill_between(dates, 0.5, 0.7, alpha=0.1, color="#ff9800")
    ax2.fill_between(dates, 0.7, y_max, alpha=0.1, color="#f44336")

    # Formatting
    ax2.set_ylabel("Stress Ratio", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.set_ylim(0, y_max)
    ax2.grid(True, alpha=0.3)

    # Latest value annotation
    latest_stress = plot_data["stress_ratio"].iloc[-1]
    ax2.annotate(
        f"Current: {latest_stress:.2f}",
        xy=(latest_date, latest_stress),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=10,
        color=COLORS["stress"],
        fontweight="bold"
    )

    # =========================================================================
    # Common formatting
    # =========================================================================

    # X-axis date formatting
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    # Footer
    fig.text(
        0.99, 0.01,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data: FRED",
        ha="right",
        fontsize=8,
        color="#808080"
    )

    fig.text(
        0.01, 0.01,
        "analyze-us-bank-credit-deposit-decoupling skill",
        ha="left",
        fontsize=8,
        color="#808080"
    )

    # Tight layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)

    # Save or show
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()

    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="銀行信貸-存款脫鉤視覺化"
    )
    parser.add_argument(
        "--start", "-s",
        default="2022-06-01",
        help="分析起始日期 (預設: 2022-06-01)"
    )
    parser.add_argument(
        "--cache-dir",
        default=str(Path(__file__).parent / "cache"),
        help="快取目錄路徑"
    )
    parser.add_argument(
        "--output", "-o",
        help="輸出圖表路徑 (PNG)"
    )
    parser.add_argument(
        "--title", "-t",
        default="Bank Credit-Deposit Decoupling Analysis",
        help="圖表標題"
    )

    args = parser.parse_args()

    if not HAS_MATPLOTLIB:
        print("Error: matplotlib is required for visualization")
        print("Install with: pip install matplotlib")
        return

    print(f"Loading data from: {args.cache_dir}")
    data = load_analysis_data(Path(args.cache_dir))

    if not data:
        print("Error: No data found. Run decoupling_analyzer.py first to fetch data.")
        return

    print(f"Calculating plot data from {args.start}...")
    plot_data = calculate_plot_data(data, args.start)

    print("Creating chart...")
    create_decoupling_chart(
        plot_data,
        output_path=args.output,
        title=args.title
    )

    print("Done!")


if __name__ == "__main__":
    main()
