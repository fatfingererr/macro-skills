#!/usr/bin/env python3
"""
visualize.py - 視覺化工具

生成利率波動率領先落後分析的多面板圖表。
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed, visualization not available")

from fetch_data import fetch_all_data
from analyze import rolling_zscore, crosscorr_leadlag, identify_shock_events


# =============================================================================
# Visualization Functions
# =============================================================================

def create_analysis_chart(
    df: pd.DataFrame,
    result: dict,
    output_path: str,
    dpi: int = 150
):
    """
    生成 4 面板分析圖表

    Parameters:
    -----------
    df : pd.DataFrame
        原始數據
    result : dict
        分析結果
    output_path : str
        輸出路徑
    dpi : int
        解析度
    """
    if not HAS_MATPLOTLIB:
        print("Error: matplotlib required for visualization")
        return

    # 獲取參數
    params = result.get("params", {})
    smooth_window = params.get("smooth_window", 5)
    zscore_window = params.get("zscore_window", 60)
    lead_lag_max_days = params.get("lead_lag_max_days", 20)
    shock_window_days = params.get("shock_window_days", 5)
    shock_threshold_bps = params.get("shock_threshold_bps", 15.0)

    # 準備數據
    df = df.sort_index()
    df_smooth = df.rolling(smooth_window).mean() if smooth_window > 0 else df.copy()
    df_z = df_smooth.apply(lambda c: rolling_zscore(c, zscore_window))

    # 識別衝擊事件
    shock = identify_shock_events(df_smooth["JGB10Y"], shock_window_days, shock_threshold_bps)
    shock_dates = df_smooth.index[shock]

    # 計算交叉相關曲線
    lags = list(range(-lead_lag_max_days, lead_lag_max_days + 1))
    corr_vix_all = [df_smooth["MOVE"].shift(lag).corr(df_smooth["VIX"]) for lag in lags]
    corr_credit_all = [df_smooth["MOVE"].shift(lag).corr(df_smooth["CREDIT"]) for lag in lags]

    # 創建圖表
    fig, axes = plt.subplots(4, 1, figsize=(14, 16))
    fig.suptitle("Rates Vol Lead/Lag Analysis (MOVE vs VIX vs Credit)", fontsize=14, fontweight="bold")

    # =========================================================================
    # Panel 1: Raw Time Series
    # =========================================================================
    ax1 = axes[0]

    # MOVE on left axis
    color_move = "#1f77b4"
    ax1.plot(df.index, df["MOVE"], label="MOVE", color=color_move, linewidth=1.5)
    ax1.set_ylabel("MOVE Index", color=color_move)
    ax1.tick_params(axis="y", labelcolor=color_move)

    # VIX and Credit on right axis
    ax1_right = ax1.twinx()
    color_vix = "#ff7f0e"
    color_credit = "#2ca02c"
    ax1_right.plot(df.index, df["VIX"], label="VIX", color=color_vix, alpha=0.7, linewidth=1)
    ax1_right.plot(df.index, df["CREDIT"], label="Credit Spread", color=color_credit, alpha=0.7, linewidth=1)
    ax1_right.set_ylabel("VIX / Credit Spread (OAS)")

    # Mark shock events
    for shock_date in shock_dates:
        ax1.axvline(shock_date, color="red", linestyle="--", alpha=0.3, linewidth=0.8)

    ax1.set_title("Panel 1: Raw Time Series")
    ax1.legend(loc="upper left")
    ax1_right.legend(loc="upper right")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    # =========================================================================
    # Panel 2: Z-Scores
    # =========================================================================
    ax2 = axes[1]

    ax2.plot(df_z.index, df_z["MOVE"], label="MOVE Z", color="#1f77b4", linewidth=1.5)
    ax2.plot(df_z.index, df_z["VIX"], label="VIX Z", color="#ff7f0e", alpha=0.7, linewidth=1)
    ax2.plot(df_z.index, df_z["CREDIT"], label="Credit Z", color="#2ca02c", alpha=0.7, linewidth=1)

    # Reference lines
    ax2.axhline(0, color="gray", linestyle="-", alpha=0.5, linewidth=0.8)
    ax2.axhline(1, color="gray", linestyle="--", alpha=0.3, linewidth=0.5)
    ax2.axhline(-1, color="gray", linestyle="--", alpha=0.3, linewidth=0.5)
    ax2.axhline(2, color="red", linestyle="--", alpha=0.3, linewidth=0.5)
    ax2.axhline(-2, color="red", linestyle="--", alpha=0.3, linewidth=0.5)

    # Mark current MOVE Z
    move_z_now = result.get("spooked_check", {}).get("MOVE_zscore_now")
    if move_z_now is not None:
        ax2.scatter([df_z.index[-1]], [move_z_now], color="blue", s=100, zorder=5, label=f"Current: {move_z_now:.2f}")

    ax2.set_ylabel("Z-Score")
    ax2.set_title("Panel 2: Standardized Series (Z-Score)")
    ax2.legend(loc="upper left")
    ax2.set_ylim(-4, 4)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    # =========================================================================
    # Panel 3: Cross-Correlation
    # =========================================================================
    ax3 = axes[2]

    ax3.plot(lags, corr_vix_all, label="MOVE vs VIX", color="#ff7f0e", linewidth=1.5)
    ax3.plot(lags, corr_credit_all, label="MOVE vs Credit", color="#2ca02c", linewidth=1.5)
    ax3.axvline(0, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    ax3.axhline(0, color="gray", linestyle="-", alpha=0.3, linewidth=0.5)

    # Mark best lags
    leadlag = result.get("leadlag", {})
    best_lag_vix = leadlag.get("MOVE_vs_VIX", {}).get("best_lag_days", 0)
    best_lag_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("best_lag_days", 0)
    best_corr_vix = leadlag.get("MOVE_vs_VIX", {}).get("corr", 0)
    best_corr_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("corr", 0)

    ax3.scatter([best_lag_vix], [best_corr_vix], color="#ff7f0e", s=100, zorder=5)
    ax3.scatter([best_lag_credit], [best_corr_credit], color="#2ca02c", s=100, zorder=5)
    ax3.annotate(f"VIX: lag={best_lag_vix}, r={best_corr_vix:.2f}",
                 xy=(best_lag_vix, best_corr_vix), xytext=(best_lag_vix + 2, best_corr_vix + 0.1),
                 fontsize=9, color="#ff7f0e")
    ax3.annotate(f"Credit: lag={best_lag_credit}, r={best_corr_credit:.2f}",
                 xy=(best_lag_credit, best_corr_credit), xytext=(best_lag_credit + 2, best_corr_credit - 0.1),
                 fontsize=9, color="#2ca02c")

    ax3.set_xlabel("Lag (days, positive = MOVE leads)")
    ax3.set_ylabel("Correlation")
    ax3.set_title("Panel 3: Cross-Correlation Function")
    ax3.legend(loc="upper right")
    ax3.set_xlim(-lead_lag_max_days - 2, lead_lag_max_days + 2)

    # =========================================================================
    # Panel 4: Event Window Reactions
    # =========================================================================
    ax4 = axes[3]

    # Calculate reactions
    move_change = df_smooth["MOVE"] - df_smooth["MOVE"].shift(shock_window_days)
    reactions = move_change[shock].dropna()

    if len(reactions) > 0:
        ax4.hist(reactions, bins=min(10, len(reactions)), alpha=0.7, color="#1f77b4", edgecolor="black")
        ax4.axvline(reactions.mean(), color="red", linestyle="--", linewidth=2, label=f"Mean: {reactions.mean():.2f}")
        ax4.axvline(0, color="gray", linestyle="-", alpha=0.5, linewidth=0.8)

        ax4.set_xlabel("MOVE Reaction to JGB Shock (change over event window)")
        ax4.set_ylabel("Frequency")
        ax4.set_title(f"Panel 4: MOVE Reaction Distribution ({len(reactions)} shock events)")
        ax4.legend()
    else:
        ax4.text(0.5, 0.5, "No shock events identified",
                 ha="center", va="center", transform=ax4.transAxes, fontsize=12)
        ax4.set_title("Panel 4: MOVE Reaction Distribution (No events)")

    # =========================================================================
    # Finalize
    # =========================================================================
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to {output_path}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Visualize rates vol leadlag analysis")
    parser.add_argument("-i", "--input", required=True, help="Input JSON result file")
    parser.add_argument("-o", "--output", required=True, help="Output image path")
    parser.add_argument("--dpi", type=int, default=150, help="Resolution (DPI)")
    parser.add_argument("--interactive", action="store_true", help="Create interactive HTML (plotly)")

    args = parser.parse_args()

    # Load result
    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    # Get date range from result
    params = result.get("params", {})
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    if not start_date or not end_date:
        print("Error: Result file missing date range in params")
        return

    # Fetch data
    df = fetch_all_data(start_date, end_date)

    if df.empty:
        print("Error: No data fetched")
        return

    # Create chart
    if args.interactive:
        print("Interactive mode not implemented yet")
        # TODO: Implement plotly version
    else:
        create_analysis_chart(df, result, args.output, dpi=args.dpi)


if __name__ == "__main__":
    main()
