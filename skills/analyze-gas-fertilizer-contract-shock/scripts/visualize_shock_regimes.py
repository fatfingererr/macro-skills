#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Natural Gas → Fertilizer Shock Regime Visualization (Bloomberg Style)

Dual-axis overlay chart (DXY-adjusted) + USD Index bottom panel.

Usage:
    python visualize_shock_regimes.py
    python visualize_shock_regimes.py --lead-lag 0
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np


# ============================================================================
# Bloomberg Style Configuration
# ============================================================================

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "gas_line": "#00bcd4",
    "fert_line": "#ff9800",
    "dxy_line": "#66bb6a",
    "divider": "#ffffff",
}


# ============================================================================
# Data Loading
# ============================================================================

def load_analysis_result(file_path: str) -> Dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_price_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    for col in ["date", "DATE", "Date", "datetime"]:
        if col in df.columns:
            df["date"] = pd.to_datetime(df[col])
            break
    for col in ["value", "VALUE", "Value", "close", "Close"]:
        if col in df.columns:
            df["value"] = df[col].astype(float)
            break
    return df[["date", "value"]].dropna().sort_values("date").reset_index(drop=True)


def find_daily_start(df: pd.DataFrame) -> pd.Timestamp:
    """Find where data switches from weekly to daily frequency"""
    gaps = df["date"].diff().dt.days
    daily_mask = gaps <= 2
    if daily_mask.any():
        return df.loc[daily_mask.idxmax(), "date"]
    return df["date"].iloc[-1]


def dxy_adjust(price_df: pd.DataFrame, dxy_df: pd.DataFrame) -> pd.DataFrame:
    """Divide price by DXY (merge on nearest date, then divide)"""
    price = price_df.copy()
    dxy = dxy_df.copy().rename(columns={"value": "dxy"})

    # Merge on exact date first
    merged = pd.merge(price, dxy[["date", "dxy"]], on="date", how="left")

    # Forward-fill missing DXY values (weekends/holidays)
    merged = merged.sort_values("date")
    merged["dxy"] = merged["dxy"].ffill().bfill()

    # If still missing, interpolate from dxy_df
    if merged["dxy"].isna().any():
        dxy_interp = dxy.set_index("date").resample("D").interpolate().reset_index()
        merged = merged.drop(columns=["dxy"])
        merged = pd.merge(merged, dxy_interp[["date", "dxy"]], on="date", how="left")
        merged["dxy"] = merged["dxy"].ffill().bfill()

    merged["value"] = merged["value"] / merged["dxy"] * 100  # scale x100 for readability
    return merged[["date", "value"]].dropna().reset_index(drop=True)


# ============================================================================
# X-Axis Helpers
# ============================================================================

def custom_date_formatter(x, pos):
    date = mdates.num2date(x)
    if date.month == 1:
        return date.strftime('%Y/1')
    return str(date.month)


def apply_xaxis_format(ax, x_min, x_max, show_labels=True):
    ax.xaxis.set_major_formatter(FuncFormatter(custom_date_formatter))
    span_years = (x_max - x_min).days / 365.25
    if span_years > 3:
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    elif span_years > 1.5:
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 3, 5, 7, 9, 11]))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    if show_labels:
        ax.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0, labelsize=9)
    else:
        ax.tick_params(axis='x', labelbottom=False)


# ============================================================================
# Plotting
# ============================================================================

def plot_gas_fertilizer_overlay(
    gas_df: pd.DataFrame,
    fert_df: pd.DataFrame,
    dxy_df: pd.DataFrame,
    result: Dict,
    output_path: str,
    lead_lag_days: int = 0,
    daily_boundary: pd.Timestamp = None
):
    plt.style.use('dark_background')

    fig = plt.figure(figsize=(14, 10), facecolor=COLORS["background"])
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax_dxy = fig.add_subplot(gs[1], sharex=ax1)
    ax1.set_facecolor(COLORS["background"])

    # ========== DXY-adjust prices ==========
    gas_adj = dxy_adjust(gas_df, dxy_df)
    fert_adj = dxy_adjust(fert_df, dxy_df)

    # ========== Shift Gas ==========
    gas_shifted = gas_adj.copy()
    if lead_lag_days > 0:
        gas_shifted["date"] = gas_shifted["date"] + timedelta(days=lead_lag_days)
    gas_shifted = gas_shifted.sort_values("date").reset_index(drop=True)
    fert_adj = fert_adj.sort_values("date").reset_index(drop=True)

    # ========== Left Axis: Gas / DXY ==========
    label_gas = f"Natural Gas / DXY" + (f" (shifted +{lead_lag_days}d)" if lead_lag_days > 0 else "")
    line1, = ax1.plot(
        gas_shifted["date"], gas_shifted["value"],
        color=COLORS["gas_line"], linewidth=1.8, linestyle='-',
        solid_capstyle='round', solid_joinstyle='round',
        label=label_gas, zorder=5
    )
    ax1.set_ylabel("Gas / DXY (\u00d7100)", color=COLORS["gas_line"], fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', colors=COLORS["gas_line"])

    # X limits
    x_min = min(gas_shifted["date"].min(), fert_adj["date"].min())
    x_max = max(gas_shifted["date"].max(), fert_adj["date"].max())
    ax1.set_xlim(x_min - timedelta(days=5), x_max + timedelta(days=10))

    # Latest gas value
    latest_gas = gas_shifted.iloc[-1]
    ax1.annotate(
        f'{latest_gas["value"]:.2f}',
        xy=(latest_gas["date"], latest_gas["value"]),
        xytext=(10, 0), textcoords='offset points',
        color=COLORS["gas_line"], fontsize=11, fontweight='bold', va='center'
    )

    # ========== Right Axis: Fert / DXY ==========
    ax2 = ax1.twinx()
    ax2.set_facecolor(COLORS["background"])

    line2, = ax2.plot(
        fert_adj["date"], fert_adj["value"],
        color=COLORS["fert_line"], linewidth=1.8, linestyle='-',
        solid_capstyle='round', solid_joinstyle='round',
        label="Urea / DXY", zorder=4
    )
    ax2.set_ylabel("Urea / DXY (\u00d7100)", color=COLORS["fert_line"], fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', colors=COLORS["fert_line"])

    # Latest fert value
    latest_fert = fert_adj.iloc[-1]
    ax2.annotate(
        f'{latest_fert["value"]:.1f}',
        xy=(latest_fert["date"], latest_fert["value"]),
        xytext=(10, 0), textcoords='offset points',
        color=COLORS["fert_line"], fontsize=11, fontweight='bold', va='center'
    )

    # ========== Daily/Weekly Divider ==========
    if daily_boundary is not None:
        for ax in [ax1, ax_dxy]:
            ax.axvline(x=daily_boundary, color=COLORS["divider"], linewidth=1, linestyle='-', alpha=0.6, zorder=8)

        # Labels on main chart
        y_top = ax1.get_ylim()[1]
        ax1.text(
            daily_boundary - timedelta(days=15), y_top * 0.97,
            "weekly", color=COLORS["text_dim"], fontsize=9, fontstyle='italic',
            ha='right', va='top', zorder=9
        )
        ax1.text(
            daily_boundary + timedelta(days=15), y_top * 0.97,
            "daily", color=COLORS["text_dim"], fontsize=9, fontstyle='italic',
            ha='left', va='top', zorder=9
        )

    # ========== Grid (main) ==========
    ax1.grid(True, linestyle='-', alpha=0.3, color=COLORS["grid"], linewidth=0.5)
    ax1.set_axisbelow(True)
    apply_xaxis_format(ax1, x_min, x_max, show_labels=False)

    # ========== Legend ==========
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(
        lines, labels, loc="upper left",
        facecolor=COLORS["background"], edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"], fontsize=10
    )

    # ========== DXY Bottom Panel ==========
    ax_dxy.set_facecolor(COLORS["background"])
    dxy_sorted = dxy_df.sort_values("date").reset_index(drop=True)
    ax_dxy.plot(
        dxy_sorted["date"], dxy_sorted["value"],
        color=COLORS["dxy_line"], linewidth=1.4, linestyle='-',
        solid_capstyle='round', solid_joinstyle='round', zorder=5
    )
    ax_dxy.set_ylabel("DXY", color=COLORS["dxy_line"], fontsize=11, fontweight='bold')
    ax_dxy.tick_params(axis='y', colors=COLORS["dxy_line"], labelsize=9)

    latest_dxy = dxy_sorted.iloc[-1]
    ax_dxy.annotate(
        f'{latest_dxy["value"]:.1f}',
        xy=(latest_dxy["date"], latest_dxy["value"]),
        xytext=(10, 0), textcoords='offset points',
        color=COLORS["dxy_line"], fontsize=10, fontweight='bold', va='center'
    )

    ax_dxy.grid(True, linestyle='-', alpha=0.3, color=COLORS["grid"], linewidth=0.5)
    ax_dxy.set_axisbelow(True)
    apply_xaxis_format(ax_dxy, x_min, x_max, show_labels=True)

    # ========== Title ==========
    title = "Natural Gas \u2192 Fertilizer (DXY-Adjusted)"
    fig.suptitle(title, color=COLORS["text"], fontsize=16, fontweight='bold', y=0.98)

    # ========== Footer ==========
    fig.text(0.02, 0.01, "Source: Trading Economics", color=COLORS["text_dim"], fontsize=8, ha='left')
    latest_date = max(gas_df["date"].max(), fert_adj["date"].max())
    fig.text(0.98, 0.01, f'As of: {latest_date.strftime("%Y-%m-%d")}', color=COLORS["text_dim"], fontsize=8, ha='right')

    plt.subplots_adjust(top=0.90, bottom=0.08, left=0.08, right=0.92)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, facecolor=COLORS["background"], edgecolor='none', bbox_inches='tight')
    plt.close()

    print(f"[OK] Chart saved to: {output_file}")
    return str(output_file)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Gas-Fert DXY-Adjusted Visualization")
    parser.add_argument("--data", default="../data/analysis_result.json")
    parser.add_argument("--gas-file", default=None)
    parser.add_argument("--fert-file", default=None)
    parser.add_argument("--dxy-file", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--lead-lag", type=int, default=0)

    args = parser.parse_args()

    if args.output is None:
        today = datetime.now().strftime("%Y-%m-%d")
        args.output = f"../../../../output/gas_fert_shock_{today}.png"

    try:
        print(f"[Load] Reading analysis result: {args.data}")
        result = load_analysis_result(args.data)

        lead_lag_days = args.lead_lag

        gas_file = args.gas_file or f"../data/cache/{result.get('series', {}).get('natural_gas', {}).get('symbol', 'natural-gas')}.csv"
        fert_file = args.fert_file or f"../data/cache/{result.get('series', {}).get('fertilizer', {}).get('symbol', 'urea')}.csv"
        dxy_file = args.dxy_file or "../data/cache/dollar-index.csv"

        print(f"[Load] Gas: {gas_file}")
        gas_df = load_price_data(gas_file)

        print(f"[Load] Fert: {fert_file}")
        fert_df = load_price_data(fert_file)

        print(f"[Load] DXY: {dxy_file}")
        dxy_df = load_price_data(dxy_file)

        # Detect daily boundary (use gas as reference)
        daily_boundary = find_daily_start(gas_df)
        print(f"[Info] Daily data starts: {daily_boundary.strftime('%Y-%m-%d')}")
        print(f"[Info] Lead-lag shift: {lead_lag_days} days")

        plot_gas_fertilizer_overlay(
            gas_df, fert_df, dxy_df,
            result, args.output,
            lead_lag_days=lead_lag_days,
            daily_boundary=daily_boundary
        )

        return 0

    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
