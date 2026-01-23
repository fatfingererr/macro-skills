#!/usr/bin/env python3
"""
銀行信貸-存款脫鉤視覺化

生成 Bloomberg Intelligence 風格的面積圖，
參考 FRED 原生圖表設計（藍色貸款、紅色存款）。

Usage:
    python visualize_decoupling.py --start 2022-06-01
    python visualize_decoupling.py --start 2022-06-01 --output chart.png

Data Sources:
    - TOTLL: Loans and Leases in Bank Credit, All Commercial Banks
    - DPSACBW027SBOG: Deposits, All Commercial Banks
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

# Matplotlib setup - must be before importing pyplot
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# ============================================================================
# Font Configuration (中文字體)
# ============================================================================

plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',  # Windows 正黑體
    'SimHei',              # Windows 黑體
    'Microsoft YaHei',     # Windows 微軟雅黑
    'PingFang TC',         # macOS 蘋方
    'Noto Sans CJK TC',    # Linux/通用
    'DejaVu Sans'          # 備用
]
plt.rcParams['axes.unicode_minus'] = False

# ============================================================================
# Bloomberg Style Configuration
# ============================================================================

COLORS = {
    # 背景與網格
    "background": "#1a1a2e",
    "grid": "#2d2d44",

    # 文字
    "text": "#ffffff",
    "text_dim": "#888888",

    # 面積圖配色（參考 FRED 原生圖表）
    "loans": "#4a90d9",      # 藍色 - 貸款
    "deposits": "#d94a4a",   # 紅色 - 存款

    # 輔助元素
    "zero_line": "#666666",
    "annotation_bg": "#2a2a4a",
}


# ============================================================================
# Data Loading
# ============================================================================

def load_analysis_data(cache_dir: Path) -> Dict[str, pd.Series]:
    """Load data from cache files."""
    data = {}

    series_map = {
        "loans": "TOTLL",
        "deposits": "DPSACBW027SBOG"
    }

    for name, series_id in series_map.items():
        cache_file = cache_dir / f"{series_id}.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                cached = json.load(f)
            series = pd.Series(cached["data"])
            series.index = pd.to_datetime(series.index)
            series = series.sort_index()
            data[name] = series
            print(f"Loaded {series_id}: {len(series)} data points")
        else:
            print(f"Warning: Cache file not found for {series_id}")
            print(f"  Please run: python decoupling_analyzer.py --start 2022-06-01")

    return data


def calculate_plot_data(
    data: Dict[str, pd.Series],
    start_date: str
) -> Dict[str, pd.Series]:
    """Calculate cumulative changes for plotting."""
    loans = data["loans"]
    deposits = data["deposits"]

    # Filter by start date
    start = pd.to_datetime(start_date)
    loans = loans[loans.index >= start]
    deposits = deposits[deposits.index >= start]

    # Align to common dates
    common_idx = loans.index.intersection(deposits.index)
    loans = loans.loc[common_idx]
    deposits = deposits.loc[common_idx]

    # Calculate cumulative changes from base date
    loan_change = loans - loans.iloc[0]
    deposit_change = deposits - deposits.iloc[0]

    # Find deposit minimum (maximum drawdown)
    deposit_min = deposit_change.min()
    deposit_min_idx = deposit_change.idxmin()

    return {
        "dates": common_idx,
        "loan_change": loan_change,
        "deposit_change": deposit_change,
        "deposit_min": deposit_min,
        "deposit_min_date": deposit_min_idx,
        "base_date": loans.index[0],
        "end_date": loans.index[-1]
    }


# ============================================================================
# Plotting
# ============================================================================

def format_billions(x, pos):
    """Format y-axis values as billions with comma separator."""
    if x >= 0:
        return f'{x:,.0f}'
    else:
        return f'{x:,.0f}'


def create_decoupling_chart(
    plot_data: Dict[str, pd.Series],
    output_path: Optional[str] = None,
    title: str = "US Bank Credit-Deposit Decoupling"
) -> None:
    """
    Create Bloomberg-style area chart showing credit-deposit decoupling.

    Features:
    - Area chart (not line chart)
    - Blue area for loans, red area for deposits
    - Clear zero line
    - Latest values annotated on right side
    """
    plt.style.use('dark_background')

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8), facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])

    dates = plot_data["dates"]
    loan_change = plot_data["loan_change"]
    deposit_change = plot_data["deposit_change"]

    # =========================================================================
    # Plot Area Charts
    # =========================================================================

    # Loans area (blue) - always positive, draw first
    ax.fill_between(
        dates, 0, loan_change,
        color=COLORS["loans"],
        alpha=0.7,
        label='Loans and Leases in Bank Credit, All Commercial Banks',
        zorder=2
    )

    # Deposits area (red) - can be negative
    ax.fill_between(
        dates, 0, deposit_change,
        color=COLORS["deposits"],
        alpha=0.7,
        label='Deposits, All Commercial Banks',
        zorder=3
    )

    # =========================================================================
    # Zero Line
    # =========================================================================
    ax.axhline(y=0, color=COLORS["zero_line"], linewidth=1, zorder=1)

    # =========================================================================
    # Latest Value Annotations (右側標註)
    # =========================================================================
    latest_date = dates[-1]
    latest_loan = loan_change.iloc[-1]
    latest_deposit = deposit_change.iloc[-1]

    # Loan annotation
    ax.annotate(
        f'Loans and Leases in Bank\nCredit, All Commercial\nBanks: {latest_date.strftime("%b %d, %Y")}\n{latest_loan:,.2f}',
        xy=(latest_date, latest_loan),
        xytext=(15, 0),
        textcoords='offset points',
        fontsize=9,
        color=COLORS["loans"],
        fontweight='bold',
        va='center',
        bbox=dict(
            boxstyle='round,pad=0.4',
            facecolor=COLORS["background"],
            edgecolor=COLORS["loans"],
            alpha=0.9
        )
    )

    # Deposit annotation
    ax.annotate(
        f'Deposits, All Commercial\nBanks: {latest_date.strftime("%b %d, %Y")}\n{latest_deposit:,.2f}',
        xy=(latest_date, latest_deposit),
        xytext=(15, 0),
        textcoords='offset points',
        fontsize=9,
        color=COLORS["deposits"],
        fontweight='bold',
        va='center',
        bbox=dict(
            boxstyle='round,pad=0.4',
            facecolor=COLORS["background"],
            edgecolor=COLORS["deposits"],
            alpha=0.9
        )
    )

    # =========================================================================
    # Mark Maximum Drawdown Point (橫向標註，在資料點上方)
    # =========================================================================
    deposit_min = plot_data["deposit_min"]
    deposit_min_date = plot_data["deposit_min_date"]

    if deposit_min < 0:
        ax.scatter([deposit_min_date], [deposit_min], color=COLORS["deposits"],
                   s=60, zorder=5, marker='v')
        ax.annotate(
            f'Max Drawdown: {deposit_min:,.0f}B ({deposit_min_date.strftime("%Y-%m-%d")})',
            xy=(deposit_min_date, deposit_min),
            xytext=(10, -18),
            textcoords='offset points',
            fontsize=9,
            color=COLORS["text"],  # 改用白色文字更清楚
            fontweight='bold',
            ha='left',
            va='top'
        )

    # =========================================================================
    # Grid & Axes
    # =========================================================================
    ax.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # Y-axis formatting
    ax.yaxis.set_major_formatter(FuncFormatter(format_billions))
    ax.tick_params(axis='y', colors=COLORS["text_dim"])
    ax.set_ylabel("Cumulative Change (Billions USD)", color=COLORS["text_dim"], fontsize=10)

    # X-axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.tick_params(axis='x', colors=COLORS["text_dim"], rotation=45)

    # Expand x-axis to make room for annotations
    x_min, x_max = ax.get_xlim()
    ax.set_xlim(x_min, x_max + (x_max - x_min) * 0.15)

    # =========================================================================
    # Legend
    # =========================================================================
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, fc=COLORS["loans"], alpha=0.7,
                       label='Loans and Leases in Bank Credit'),
        plt.Rectangle((0, 0), 1, 1, fc=COLORS["deposits"], alpha=0.7,
                       label='Deposits, All Commercial Banks'),
    ]

    ax.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=9,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"]
    )

    # =========================================================================
    # Title
    # =========================================================================
    base_date = plot_data["base_date"]
    end_date = plot_data["end_date"]
    fig.suptitle(
        f"{title}\nCumulative Change Since {base_date.strftime('%Y-%m-%d')}",
        color=COLORS["text"],
        fontsize=14,
        fontweight='bold',
        x=0.38,
        y=0.98,
        ha='center'
    )

    # =========================================================================
    # Footer
    # =========================================================================
    fig.text(
        0.02, 0.02,
        "Source: FRED",
        color=COLORS["text_dim"],
        fontsize=8,
        ha='left'
    )

    fig.text(
        0.70, 0.02,
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        color=COLORS["text_dim"],
        fontsize=8,
        ha='right'
    )

    # =========================================================================
    # Layout & Save
    # =========================================================================
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.12, right=0.72)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches='tight',
            facecolor=COLORS["background"]
        )
        print(f"Chart saved to: {output_path}")
    else:
        plt.show()

    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="銀行信貸-存款脫鉤視覺化 (Bloomberg 風格面積圖)"
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
        default="US Bank Credit-Deposit Decoupling",
        help="圖表標題"
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  銀行信貸-存款脫鉤視覺化")
    print("  Bloomberg Style Area Chart")
    print(f"{'='*60}")
    print(f"Loading data from: {args.cache_dir}")

    data = load_analysis_data(Path(args.cache_dir))

    if len(data) < 2:
        print("\nError: Missing data. Please run the analyzer first:")
        print("  python decoupling_analyzer.py --start 2022-06-01")
        return

    print(f"\nCalculating plot data from {args.start}...")
    plot_data = calculate_plot_data(data, args.start)

    print(f"Data points: {len(plot_data['dates'])}")
    print(f"Date range: {plot_data['base_date'].date()} to {plot_data['end_date'].date()}")
    print(f"Latest loan change: {plot_data['loan_change'].iloc[-1]:,.0f} B")
    print(f"Latest deposit change: {plot_data['deposit_change'].iloc[-1]:,.0f} B")
    print(f"Deposit max drawdown: {plot_data['deposit_min']:,.0f} B on {plot_data['deposit_min_date'].date()}")

    print("\nCreating Bloomberg-style area chart...")
    create_decoupling_chart(
        plot_data,
        output_path=args.output,
        title=args.title
    )

    print("Done!")


if __name__ == "__main__":
    main()
