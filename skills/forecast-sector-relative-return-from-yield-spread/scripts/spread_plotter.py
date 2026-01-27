#!/usr/bin/env python3
"""
視覺化圖表腳本

生成美國公債利差與相對報酬的對齊圖表。
"""

import argparse
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    import yfinance as yf
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError as e:
    print(f"請安裝必要套件: pip install yfinance matplotlib")
    print(f"Missing: {e}")
    sys.exit(1)


# =============================================================================
# Constants
# =============================================================================

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

TENOR_TO_FRED = {
    "3M": "DGS3MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "30Y": "DGS30",
}


# =============================================================================
# Data Fetching (simplified)
# =============================================================================

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取時間序列"""
    params = {"id": series_id, "cosd": start_date, "coed": end_date}
    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
        df = df.dropna().set_index("DATE")
        return df[series_id]
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return pd.Series(dtype=float)


def fetch_price_series(ticker: str, start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 抓取價格"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return pd.Series(dtype=float)

        # Handle different yfinance versions (MultiIndex vs single-level)
        if isinstance(data.columns, pd.MultiIndex):
            if ("Close", ticker) in data.columns:
                return data[("Close", ticker)]
            elif ("Adj Close", ticker) in data.columns:
                return data[("Adj Close", ticker)]
            else:
                close_cols = [c for c in data.columns if c[0] in ["Close", "Adj Close"]]
                if close_cols:
                    return data[close_cols[0]]
        else:
            if "Adj Close" in data.columns:
                return data["Adj Close"]
            elif "Close" in data.columns:
                return data["Close"]

        return pd.Series(dtype=float)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.Series(dtype=float)


def to_weekly(series: pd.Series) -> pd.Series:
    """轉換為週頻"""
    return series.resample("W-FRI").last().dropna()


# =============================================================================
# Plotting
# =============================================================================

def plot_basic(spread: pd.Series, ratio: pd.Series, lead_months: int,
               risk_ticker: str, defensive_ticker: str, output_path: str):
    """基本版圖表：利差與相對報酬對齊"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Shift spread for visual alignment
    periods_shift = int(lead_months * 4.345)  # weeks
    spread_shifted = spread.shift(periods_shift)

    # Plot 1: Spread (shifted)
    ax1 = axes[0]
    ax1.plot(spread_shifted.index, spread_shifted.values, 'b-', linewidth=1.5, label=f'2Y-10Y Spread (shifted {lead_months}m)')
    ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax1.fill_between(spread_shifted.index, spread_shifted.values, 0,
                     where=spread_shifted.values > 0, alpha=0.3, color='red', label='Inverted')
    ax1.fill_between(spread_shifted.index, spread_shifted.values, 0,
                     where=spread_shifted.values <= 0, alpha=0.3, color='green', label='Normal')
    ax1.set_ylabel('Yield Spread (%)', fontsize=10)
    ax1.legend(loc='upper left', fontsize=8)
    ax1.set_title(f'Yield Spread (2Y-10Y) Leading {risk_ticker}/{defensive_ticker} by {lead_months} Months', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Ratio
    ax2 = axes[1]
    ax2.plot(ratio.index, ratio.values, 'purple', linewidth=1.5, label=f'{risk_ticker}/{defensive_ticker} Ratio')
    ax2.set_ylabel('Relative Ratio', fontsize=10)
    ax2.set_xlabel('Date', fontsize=10)
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Format x-axis
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart saved to {output_path}")


def plot_comprehensive(spread: pd.Series, ratio: pd.Series, lead_months: int,
                       risk_ticker: str, defensive_ticker: str,
                       lead_scan_results: dict, model_result: dict,
                       output_path: str):
    """完整版圖表：含領先掃描、預測區間"""
    fig = plt.figure(figsize=(14, 10))

    # Create grid
    gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1], hspace=0.3, wspace=0.3)

    # Top: Spread vs Ratio alignment (spans both columns)
    ax_main = fig.add_subplot(gs[0, :])

    periods_shift = int(lead_months * 4.345)
    spread_shifted = spread.shift(periods_shift)

    # Dual y-axis
    ax_main.plot(spread_shifted.index, spread_shifted.values, 'b-', linewidth=1.5,
                 label=f'2Y-10Y Spread (shifted {lead_months}m)', alpha=0.8)
    ax_main.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax_main.set_ylabel('Yield Spread (%)', color='blue', fontsize=10)
    ax_main.tick_params(axis='y', labelcolor='blue')

    ax_ratio = ax_main.twinx()
    ax_ratio.plot(ratio.index, ratio.values, 'purple', linewidth=1.5,
                  label=f'{risk_ticker}/{defensive_ticker}', alpha=0.8)
    ax_ratio.set_ylabel('Relative Ratio', color='purple', fontsize=10)
    ax_ratio.tick_params(axis='y', labelcolor='purple')

    ax_main.set_title(f'Yield Spread Leading {risk_ticker}/{defensive_ticker} by {lead_months} Months', fontsize=12)
    ax_main.grid(True, alpha=0.3)

    # Add legends
    lines1, labels1 = ax_main.get_legend_handles_labels()
    lines2, labels2 = ax_ratio.get_legend_handles_labels()
    ax_main.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)

    # Bottom left: Lead scan bar chart
    ax_scan = fig.add_subplot(gs[1, 0])
    if lead_scan_results:
        leads = list(lead_scan_results.keys())
        corrs = [lead_scan_results[l] if lead_scan_results[l] else 0 for l in leads]
        colors = ['green' if c < 0 else 'red' for c in corrs]
        bars = ax_scan.bar([str(l) for l in leads], corrs, color=colors, alpha=0.7)
        ax_scan.axhline(0, color='black', linewidth=0.5)
        ax_scan.set_xlabel('Lead Months', fontsize=10)
        ax_scan.set_ylabel('Correlation', fontsize=10)
        ax_scan.set_title('Lead Scan: Correlation by Lead Period', fontsize=10)

        # Highlight best
        best_idx = np.argmin([abs(c) for c in corrs])
        if corrs:
            best_idx = corrs.index(min(corrs, key=lambda x: -abs(x)))
            bars[best_idx].set_edgecolor('black')
            bars[best_idx].set_linewidth(2)

    # Bottom right: Model statistics
    ax_stats = fig.add_subplot(gs[1, 1])
    ax_stats.axis('off')

    if model_result:
        stats_text = f"""
Model Statistics

Correlation: {model_result.get('corr_x_y', 'N/A'):.3f}
R-squared: {model_result.get('r_squared', 'N/A'):.3f}
Beta: {model_result.get('beta', 'N/A'):.4f}
Alpha: {model_result.get('alpha', 'N/A'):.4f}
Observations: {model_result.get('n_observations', 'N/A')}

Interpretation:
Negative beta means higher spread
(inverted curve) → weaker growth
relative to defensive stocks.
"""
        ax_stats.text(0.1, 0.9, stats_text, transform=ax_stats.transAxes,
                      fontsize=9, verticalalignment='top', fontfamily='monospace',
                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Third row: Price comparison (normalized)
    ax_price = fig.add_subplot(gs[2, :])

    # Normalize prices to start at 100
    risk_price = ratio * 100  # Using ratio as proxy
    start_idx = max(0, len(risk_price) - 520)  # Last 10 years
    risk_norm = risk_price.iloc[start_idx:] / risk_price.iloc[start_idx] * 100

    ax_price.plot(risk_norm.index, risk_norm.values, 'purple', linewidth=1.5,
                  label=f'{risk_ticker}/{defensive_ticker} Ratio (Normalized)')
    ax_price.axhline(100, color='gray', linestyle='--', alpha=0.5)
    ax_price.set_ylabel('Normalized (Start=100)', fontsize=10)
    ax_price.set_xlabel('Date', fontsize=10)
    ax_price.legend(loc='upper left', fontsize=8)
    ax_price.set_title(f'Relative Performance: {risk_ticker} vs {defensive_ticker}', fontsize=10)
    ax_price.grid(True, alpha=0.3)

    # Format x-axis
    ax_price.xaxis.set_major_locator(mdates.YearLocator())
    ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Comprehensive chart saved to {output_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="生成美國公債利差預測圖表")
    parser.add_argument("--quick", action="store_true", help="快速生成基本版")
    parser.add_argument("--comprehensive", action="store_true", help="生成完整版")
    parser.add_argument("--risk-ticker", default="QQQ")
    parser.add_argument("--defensive-ticker", default="XLV")
    parser.add_argument("--lead-months", type=int, default=24)
    parser.add_argument("--lookback-years", type=int, default=12)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--output-dir", default=".")

    args = parser.parse_args()

    # Date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    if args.start_date:
        start_date = args.start_date
    else:
        start_date = (datetime.now() - timedelta(days=args.lookback_years * 365)).strftime("%Y-%m-%d")

    # Fetch data
    print("Fetching data...")
    dgs2 = fetch_fred_series("DGS2", start_date, end_date)
    dgs10 = fetch_fred_series("DGS10", start_date, end_date)
    risk_price = fetch_price_series(args.risk_ticker, start_date, end_date)
    defensive_price = fetch_price_series(args.defensive_ticker, start_date, end_date)

    if dgs2.empty or dgs10.empty or risk_price.empty or defensive_price.empty:
        print("Error: Failed to fetch required data")
        sys.exit(1)

    # Compute
    spread = to_weekly(dgs2 - dgs10)
    ratio = to_weekly(risk_price / defensive_price)

    # Align
    aligned = pd.concat({"spread": spread, "ratio": ratio}, axis=1).dropna()
    spread = aligned["spread"]
    ratio = aligned["ratio"]

    # Output path
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    if args.comprehensive:
        # Need to run lead scan
        from spread_forecaster import lead_scan, fit_lagged_regression, compute_future_rel_return

        print("Running lead scan...")
        scan_results = lead_scan(spread, ratio, [6, 12, 18, 24, 30], "weekly")

        print("Fitting model...")
        horizon_periods = int(args.lead_months * 4.345)
        y = compute_future_rel_return(ratio, horizon_periods)
        model_data = pd.concat({"x": spread, "y": y}, axis=1).dropna()
        model_result = fit_lagged_regression(model_data["x"], model_data["y"])

        output_path = output_dir / f"spread_forecast_comprehensive_{date_str}.png"
        plot_comprehensive(spread, ratio, args.lead_months,
                          args.risk_ticker, args.defensive_ticker,
                          scan_results, model_result, str(output_path))
    else:
        output_path = output_dir / f"spread_forecast_{date_str}.png"
        plot_basic(spread, ratio, args.lead_months,
                  args.risk_ticker, args.defensive_ticker, str(output_path))


if __name__ == "__main__":
    main()
