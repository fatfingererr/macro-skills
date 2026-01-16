#!/usr/bin/env python3
"""
Palladium-Silver Visualization

Generates visual charts for palladium-silver cross-metal analysis.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import yfinance as yf
except ImportError:
    yf = None


def fetch_data(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    interval: str = "1h",
) -> pd.DataFrame:
    """Fetch OHLCV data."""
    if yf is None:
        raise ImportError("yfinance is required")

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365)
        start_date = start_dt.strftime("%Y-%m-%d")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    return df


def align_data(ag_df: pd.DataFrame, pd_df: pd.DataFrame) -> pd.DataFrame:
    """Align silver and palladium time series."""
    common_index = ag_df.index.intersection(pd_df.index)
    ag_aligned = ag_df.reindex(common_index).ffill()
    pd_aligned = pd_df.reindex(common_index).ffill()

    df = pd.DataFrame(
        {
            "ag_close": ag_aligned["Close"],
            "pd_close": pd_aligned["Close"],
        }
    )
    df["ag_ret"] = np.log(df["ag_close"]).diff()
    df["pd_ret"] = np.log(df["pd_close"]).diff()

    return df.dropna()


def detect_pivots(prices: pd.Series, left: int = 3, right: int = 3) -> list[dict]:
    """Detect pivot highs and lows."""
    turns = []
    prices_arr = prices.values

    for i in range(left, len(prices) - right):
        window = prices_arr[i - left : i + right + 1]
        current = prices_arr[i]

        if current == window.max():
            turns.append({"idx": i, "ts": prices.index[i], "type": "top", "price": float(current)})
        elif current == window.min():
            turns.append({"idx": i, "ts": prices.index[i], "type": "bottom", "price": float(current)})

    return turns


def check_confirmation(ag_turn: dict, pd_turns: list[dict], window_bars: int = 6) -> tuple[bool, int | None]:
    """Check if silver turn is confirmed by palladium."""
    ag_idx = ag_turn["idx"]
    ag_type = ag_turn["type"]

    for pd_turn in pd_turns:
        if pd_turn["type"] != ag_type:
            continue
        lag = ag_idx - pd_turn["idx"]
        if abs(lag) <= window_bars:
            return True, lag

    return False, None


def plot_price_overlay(
    df: pd.DataFrame,
    ag_turns: list[dict],
    pd_turns: list[dict],
    confirmed_turns: list[dict],
    output_path: str,
    silver_symbol: str = "SI=F",
    palladium_symbol: str = "PA=F",
):
    """
    Plot price overlay with turning points.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])

    # Price overlay
    ax1.set_title(f"{silver_symbol} vs {palladium_symbol} - Price Overlay with Turning Points", fontsize=14)

    # Silver price
    ax1.plot(df.index, df["ag_close"], label=f"Silver ({silver_symbol})", color="silver", linewidth=1.5)

    # Palladium on secondary axis
    ax1_twin = ax1.twinx()
    ax1_twin.plot(df.index, df["pd_close"], label=f"Palladium ({palladium_symbol})", color="orange", linewidth=1.5, alpha=0.7)

    # Mark silver turning points
    for turn in ag_turns:
        idx = turn["idx"]
        if idx < len(df):
            is_confirmed = any(t["idx"] == idx for t in confirmed_turns)
            color = "green" if is_confirmed else "red"
            marker = "^" if turn["type"] == "bottom" else "v"
            ax1.scatter(df.index[idx], df["ag_close"].iloc[idx], color=color, marker=marker, s=100, zorder=5)

    ax1.set_ylabel(f"Silver Price", color="gray")
    ax1_twin.set_ylabel(f"Palladium Price", color="orange")
    ax1.legend(loc="upper left")
    ax1_twin.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Rolling correlation
    rolling_corr = df["ag_ret"].rolling(50).corr(df["pd_ret"])
    ax2.plot(df.index, rolling_corr, label="50-bar Rolling Correlation", color="blue", linewidth=1)
    ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax2.axhline(y=0.5, color="green", linestyle="--", alpha=0.5, label="Strong correlation (0.5)")
    ax2.axhline(y=-0.5, color="red", linestyle="--", alpha=0.5)
    ax2.set_ylabel("Correlation")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved to {output_path}")


def plot_confirmation_analysis(
    events: list[dict],
    output_path: str,
):
    """
    Plot confirmation analysis charts.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required")

    confirmed = [e for e in events if e.get("confirmed", False)]
    unconfirmed = [e for e in events if not e.get("confirmed", False)]
    failed = [e for e in events if e.get("failed_move", False)]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Pie chart: Confirmation status
    ax1 = axes[0]
    sizes = [len(confirmed), len(unconfirmed)]
    labels = [f"Confirmed\n({len(confirmed)})", f"Unconfirmed\n({len(unconfirmed)})"]
    colors = ["green", "red"]
    ax1.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    ax1.set_title("Silver Turns: Confirmation Status")

    # Bar chart: By turn type
    ax2 = axes[1]
    top_conf = len([e for e in confirmed if e.get("turn") == "top"])
    top_unconf = len([e for e in unconfirmed if e.get("turn") == "top"])
    bottom_conf = len([e for e in confirmed if e.get("turn") == "bottom"])
    bottom_unconf = len([e for e in unconfirmed if e.get("turn") == "bottom"])

    x = np.arange(2)
    width = 0.35
    ax2.bar(x - width / 2, [top_conf, bottom_conf], width, label="Confirmed", color="green")
    ax2.bar(x + width / 2, [top_unconf, bottom_unconf], width, label="Unconfirmed", color="red")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["Top", "Bottom"])
    ax2.set_ylabel("Count")
    ax2.set_title("Confirmation by Turn Type")
    ax2.legend()

    # Failure rate comparison
    ax3 = axes[2]
    unconf_failed = len([e for e in unconfirmed if e.get("failed_move", False)])
    conf_failed = len([e for e in confirmed if e.get("failed_move", False)])
    unconf_rate = unconf_failed / len(unconfirmed) * 100 if unconfirmed else 0
    conf_rate = conf_failed / len(confirmed) * 100 if confirmed else 0

    bars = ax3.bar(["Unconfirmed", "Confirmed"], [unconf_rate, conf_rate], color=["red", "green"])
    ax3.set_ylabel("Failure Rate (%)")
    ax3.set_title("Failure Rate: Unconfirmed vs Confirmed")
    for bar, rate in zip(bars, [unconf_rate, conf_rate]):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{rate:.1f}%", ha="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved to {output_path}")


def plot_lead_lag_analysis(
    df: pd.DataFrame,
    max_lag: int = 24,
    output_path: str = "lead_lag.png",
):
    """
    Plot lead-lag cross-correlation.
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib is required")

    from scipy import signal

    pd_ret = df["pd_ret"].values
    ag_ret = df["ag_ret"].values

    correlation = signal.correlate(ag_ret, pd_ret, mode="full")
    lags = signal.correlation_lags(len(ag_ret), len(pd_ret), mode="full")
    correlation = correlation / len(ag_ret)

    # Restrict range
    mask = (lags >= -max_lag) & (lags <= max_lag)
    correlation = correlation[mask]
    lags = lags[mask]

    best_idx = np.argmax(np.abs(correlation))
    best_lag = lags[best_idx]
    best_corr = correlation[best_idx]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(lags, correlation, color="steelblue", alpha=0.7)
    ax.axvline(x=best_lag, color="red", linestyle="--", label=f"Best lag: {best_lag} (corr: {best_corr:.3f})")
    ax.axhline(y=0, color="gray", linestyle="-", alpha=0.5)
    ax.set_xlabel("Lag (bars) - Positive = Palladium leads")
    ax.set_ylabel("Cross-Correlation")
    ax.set_title("Lead-Lag Cross-Correlation: Palladium vs Silver")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Plot Palladium-Silver Analysis")
    parser.add_argument("--silver", type=str, default="SI=F", help="Silver symbol")
    parser.add_argument("--palladium", type=str, default="PA=F", help="Palladium symbol")
    parser.add_argument("--timeframe", type=str, default="1h", help="Timeframe")
    parser.add_argument("--lookback", type=int, default=500, help="Lookback bars")
    parser.add_argument("--start", type=str, help="Start date")
    parser.add_argument("--end", type=str, help="End date")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--pivot-left", type=int, default=3, help="Pivot left")
    parser.add_argument("--pivot-right", type=int, default=3, help="Pivot right")
    parser.add_argument("--confirm-window", type=int, default=6, help="Confirmation window")

    args = parser.parse_args()

    if not HAS_MATPLOTLIB:
        print("Error: matplotlib is required. Install with: pip install matplotlib")
        return

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Fetch data
    print(f"Fetching {args.silver} data...")
    ag_df = fetch_data(args.silver, args.start, args.end, args.timeframe)
    print(f"Fetching {args.palladium} data...")
    pd_df = fetch_data(args.palladium, args.start, args.end, args.timeframe)

    # Limit to lookback
    if len(ag_df) > args.lookback:
        ag_df = ag_df.iloc[-args.lookback :]
    if len(pd_df) > args.lookback:
        pd_df = pd_df.iloc[-args.lookback :]

    # Align
    df = align_data(ag_df, pd_df)
    print(f"Aligned data: {len(df)} bars")

    # Detect turns
    ag_turns = detect_pivots(df["ag_close"], args.pivot_left, args.pivot_right)
    pd_turns = detect_pivots(df["pd_close"], args.pivot_left, args.pivot_right)
    print(f"Silver turns: {len(ag_turns)}, Palladium turns: {len(pd_turns)}")

    # Check confirmations
    confirmed_turns = []
    events = []
    for turn in ag_turns:
        confirmed, lag = check_confirmation(turn, pd_turns, args.confirm_window)
        if confirmed:
            confirmed_turns.append(turn)
        events.append({"idx": turn["idx"], "turn": turn["type"], "confirmed": confirmed, "failed_move": not confirmed})

    print(f"Confirmed: {len(confirmed_turns)}/{len(ag_turns)}")

    # Generate plots
    plot_price_overlay(
        df, ag_turns, pd_turns, confirmed_turns,
        os.path.join(args.output, "price_overlay.png"),
        args.silver, args.palladium
    )

    plot_confirmation_analysis(
        events,
        os.path.join(args.output, "confirmation_analysis.png")
    )

    plot_lead_lag_analysis(
        df,
        max_lag=24,
        output_path=os.path.join(args.output, "lead_lag.png")
    )

    print(f"\nAll charts saved to {args.output}/")


if __name__ == "__main__":
    main()
