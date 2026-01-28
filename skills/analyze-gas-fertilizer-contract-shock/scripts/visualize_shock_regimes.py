#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shock Regime 視覺化

生成天然氣與化肥的 shock regime 對比圖。

Usage:
    python visualize_shock_regimes.py \
        --data ../data/analysis_result.json \
        --gas-file ../data/natural_gas.csv \
        --fert-file ../data/urea.csv \
        --output ../../output/gas_fert_shock_2026-01-28.png
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


# ============================================================================
# 配置
# ============================================================================

# Bloomberg 風格配色
STYLE = {
    "background": "#1a1a2e",
    "text": "#ffffff",
    "grid": "#2d2d44",
    "gas_line": "#00bcd4",      # 青色
    "gas_fill": "#00bcd4",
    "fert_line": "#ff9800",     # 橙色
    "fert_fill": "#ff9800",
    "shock_region": "#ff5252",  # 紅色
    "spike_region": "#ffeb3b",  # 黃色
}


# ============================================================================
# 數據載入
# ============================================================================

def load_analysis_result(file_path: str) -> Dict:
    """載入分析結果"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_price_data(file_path: str) -> pd.DataFrame:
    """載入價格數據"""
    df = pd.read_csv(file_path)

    # 嘗試多種日期列名
    date_candidates = ["date", "DATE", "Date", "datetime"]
    for col in date_candidates:
        if col in df.columns:
            df["date"] = pd.to_datetime(df[col])
            break

    # 嘗試多種值列名
    value_candidates = ["value", "VALUE", "Value", "close", "Close"]
    for col in value_candidates:
        if col in df.columns:
            df["value"] = df[col].astype(float)
            break

    return df[["date", "value"]].dropna()


# ============================================================================
# 繪圖
# ============================================================================

def plot_shock_regimes(
    gas_df: pd.DataFrame,
    fert_df: pd.DataFrame,
    gas_regimes: List[Dict],
    fert_regimes: List[Dict],
    result: Dict,
    output_path: str
):
    """
    繪製 shock regime 對比圖
    """
    # 設定 Bloomberg 風格
    plt.style.use('dark_background')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.patch.set_facecolor(STYLE["background"])

    for ax in [ax1, ax2]:
        ax.set_facecolor(STYLE["background"])
        ax.grid(True, linestyle='--', alpha=0.3, color=STYLE["grid"])
        ax.tick_params(colors=STYLE["text"])
        for spine in ax.spines.values():
            spine.set_color(STYLE["grid"])

    # ========== 上圖：天然氣 ==========
    ax1.plot(gas_df["date"], gas_df["value"],
             color=STYLE["gas_line"], linewidth=1.5, label="Natural Gas")

    # 標記 shock regimes
    for regime in gas_regimes:
        start = pd.to_datetime(regime["start"])
        end = pd.to_datetime(regime["end"])
        ax1.axvspan(start, end, alpha=0.3, color=STYLE["shock_region"],
                    label="Gas Shock" if regime == gas_regimes[0] else "")

        # 標記峰值
        peak_date = pd.to_datetime(regime["peak_date"])
        ax1.scatter([peak_date], [regime["peak_value"]],
                    color=STYLE["shock_region"], s=100, zorder=5, marker="^")
        ax1.annotate(f'+{regime["regime_return_pct"]:.0f}%',
                     xy=(peak_date, regime["peak_value"]),
                     xytext=(10, 10), textcoords='offset points',
                     color=STYLE["text"], fontsize=10,
                     fontweight='bold')

    ax1.set_ylabel("Natural Gas (USD/MMBtu)", color=STYLE["text"], fontsize=12)
    ax1.legend(loc="upper left", facecolor=STYLE["background"],
               edgecolor=STYLE["grid"], labelcolor=STYLE["text"])

    # ========== 下圖：化肥 ==========
    ax2.plot(fert_df["date"], fert_df["value"],
             color=STYLE["fert_line"], linewidth=1.5, label="Fertilizer (Urea)")

    # 標記 spike regimes
    for regime in fert_regimes:
        start = pd.to_datetime(regime["start"])
        end = pd.to_datetime(regime["end"])
        ax2.axvspan(start, end, alpha=0.3, color=STYLE["spike_region"],
                    label="Fert Spike" if regime == fert_regimes[0] else "")

        # 標記峰值
        peak_date = pd.to_datetime(regime["peak_date"])
        ax2.scatter([peak_date], [regime["peak_value"]],
                    color=STYLE["spike_region"], s=100, zorder=5, marker="^")
        ax2.annotate(f'+{regime["regime_return_pct"]:.0f}%',
                     xy=(peak_date, regime["peak_value"]),
                     xytext=(10, 10), textcoords='offset points',
                     color=STYLE["text"], fontsize=10,
                     fontweight='bold')

    ax2.set_ylabel("Fertilizer (USD/ton)", color=STYLE["text"], fontsize=12)
    ax2.set_xlabel("Date", color=STYLE["text"], fontsize=12)
    ax2.legend(loc="upper left", facecolor=STYLE["background"],
               edgecolor=STYLE["grid"], labelcolor=STYLE["text"])

    # 日期格式
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    # 標題
    signal = result.get("signal", "unknown")
    confidence = result.get("confidence", "unknown")
    lead_lag = result.get("lead_lag_test", {})
    best_lag = lead_lag.get("best_lag_days_gas_leads_fert", 0)
    best_corr = lead_lag.get("best_corr", 0)

    signal_text = {
        "narrative_supported": "Narrative Supported",
        "narrative_weak": "Narrative Weak",
        "inconclusive": "Inconclusive"
    }.get(signal, signal)

    title = f"Natural Gas → Fertilizer Shock Analysis\n"
    title += f"Signal: {signal_text} (Confidence: {confidence.upper()}) | "
    title += f"Lead-Lag: Gas leads by {best_lag} days (r={best_corr:.2f})"

    fig.suptitle(title, color=STYLE["text"], fontsize=14, fontweight='bold', y=0.98)

    # 調整佈局
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)

    # 儲存
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, facecolor=STYLE["background"],
                edgecolor='none', bbox_inches='tight')
    plt.close()

    print(f"圖表已儲存至: {output_file}")


# ============================================================================
# 主程式
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Shock Regime 視覺化")
    parser.add_argument("--data", required=True, help="分析結果 JSON 檔案")
    parser.add_argument("--gas-file", help="天然氣 CSV 檔案（可選，從 result 推斷）")
    parser.add_argument("--fert-file", help="化肥 CSV 檔案（可選，從 result 推斷）")
    parser.add_argument("--output", default="../../output/gas_fert_shock.png", help="輸出圖檔路徑")

    args = parser.parse_args()

    # 載入分析結果
    result = load_analysis_result(args.data)

    # 載入價格數據
    gas_file = args.gas_file
    fert_file = args.fert_file

    if not gas_file:
        # 從 result 推斷
        gas_symbol = result.get("series", {}).get("natural_gas", {}).get("symbol", "natural_gas")
        gas_file = f"../data/{gas_symbol}.csv"

    if not fert_file:
        fert_symbol = result.get("series", {}).get("fertilizer", {}).get("symbol", "urea")
        fert_file = f"../data/{fert_symbol}.csv"

    gas_df = load_price_data(gas_file)
    fert_df = load_price_data(fert_file)

    # 取得 regimes
    gas_regimes = result.get("detections", {}).get("gas_shock_regimes", [])
    fert_regimes = result.get("detections", {}).get("fert_spike_regimes", [])

    # 繪圖
    plot_shock_regimes(gas_df, fert_df, gas_regimes, fert_regimes, result, args.output)


if __name__ == "__main__":
    main()
