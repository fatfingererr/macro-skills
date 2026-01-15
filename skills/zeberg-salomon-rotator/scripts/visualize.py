#!/usr/bin/env python3
"""
Zeberg-Salomon Rotator - Visualization
生成回測結果的多面板視覺化圖表
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd


# 設定中文字體（如果可用）
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def parse_backtest_result(result: Dict) -> Dict:
    """解析回測結果為繪圖所需格式"""
    # 累積報酬序列
    cum_series = result.get("backtest_summary", {}).get("cumulative_series", {})
    cum_df = pd.Series(cum_series)
    cum_df.index = pd.to_datetime(cum_df.index)
    cum_df = cum_df.sort_index()

    # 切換事件
    switch_events = result.get("switch_events", [])

    # 建立狀態時間序列
    states = []
    current_state = "RISK_ON"
    switch_dates = {pd.to_datetime(s["date"]): s["to_state"] for s in switch_events}

    for t in cum_df.index:
        if t in switch_dates:
            current_state = switch_dates[t]
        states.append(current_state)

    state_series = pd.Series(states, index=cum_df.index)

    # 指標時間序列
    index_series = result.get("index_series", {})
    leading_series = None
    coincident_series = None

    if "leading" in index_series:
        leading_series = pd.Series(index_series["leading"])
        leading_series.index = pd.to_datetime(leading_series.index)
        leading_series = leading_series.sort_index()

    if "coincident" in index_series:
        coincident_series = pd.Series(index_series["coincident"])
        coincident_series.index = pd.to_datetime(coincident_series.index)
        coincident_series = coincident_series.sort_index()

    # 從切換事件提取指標值
    leading_values = {}
    coincident_values = {}
    for event in switch_events:
        dt = pd.to_datetime(event["date"])
        reason = event.get("reason", {})
        leading_values[dt] = reason.get("LeadingIndex")
        coincident_values[dt] = reason.get("CoincidentIndex")

    return {
        "cumulative": cum_df,
        "states": state_series,
        "switch_events": switch_events,
        "leading_series": leading_series,
        "coincident_series": coincident_series,
        "leading_at_switch": leading_values,
        "coincident_at_switch": coincident_values,
        "params": result.get("params_used", {}),
        "benchmarks": result.get("benchmarks", {}),
        "current_state": result.get("current_state", {}),
        "latest_indices": result.get("latest_indices", {}),
        "backtest_summary": result.get("backtest_summary", {}),
    }


def create_visualization(
    data: Dict,
    output_path: Optional[str] = None,
    show: bool = False,
) -> str:
    """
    創建多面板視覺化圖表

    佈局設計：
    - Panel 1 (上): 領先指標 & 同時指標 + 門檻線 + 狀態背景
    - Panel 2 (中): 累積報酬曲線 (策略 vs benchmarks)
    - Panel 3 (下): 狀態條帶圖
    """
    # 設定圖表
    fig = plt.figure(figsize=(16, 12))

    # 使用 GridSpec 進行更靈活的佈局
    gs = fig.add_gridspec(4, 1, height_ratios=[2, 2, 0.5, 0.3], hspace=0.15)

    ax1 = fig.add_subplot(gs[0])  # 指標面板
    ax2 = fig.add_subplot(gs[1], sharex=ax1)  # 報酬面板
    ax3 = fig.add_subplot(gs[2], sharex=ax1)  # 狀態條帶
    ax4 = fig.add_subplot(gs[3])  # 圖例與統計

    # 提取數據
    cum_df = data["cumulative"]
    states = data["states"]
    params = data["params"]
    benchmarks = data["benchmarks"]
    switch_events = data["switch_events"]
    leading_series = data.get("leading_series")
    coincident_series = data.get("coincident_series")

    iceberg_threshold = params.get("iceberg_threshold", -0.3)
    sinking_threshold = params.get("sinking_threshold", -0.5)

    # ========== Panel 1: 指標面板 ==========
    ax1.set_title("Zeberg-Salomon Business Cycle Indicators", fontsize=14, fontweight='bold')

    # 繪製狀態背景
    _draw_state_background(ax1, states)

    # 如果有完整的指標序列，繪製它們
    if leading_series is not None and not leading_series.empty:
        ax1.plot(leading_series.index, leading_series.values,
                 color='#2E86AB', linewidth=2, label='Leading Index', zorder=3)
    if coincident_series is not None and not coincident_series.empty:
        ax1.plot(coincident_series.index, coincident_series.values,
                 color='#A23B72', linewidth=2, label='Coincident Index', zorder=3)

    # 繪製門檻線
    ax1.axhline(y=iceberg_threshold, color='#E8871E', linestyle='--',
                linewidth=1.5, label=f'Iceberg Threshold ({iceberg_threshold})', zorder=2)
    ax1.axhline(y=sinking_threshold, color='#D62839', linestyle='--',
                linewidth=1.5, label=f'Sinking Threshold ({sinking_threshold})', zorder=2)
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5, zorder=1)

    # 標記切換事件
    for event in switch_events:
        dt = pd.to_datetime(event["date"])
        reason = event.get("reason", {})
        L_val = reason.get("LeadingIndex")
        if L_val is not None:
            color = '#D62839' if event["to_state"] == "RISK_OFF" else '#2E7D32'
            ax1.scatter(dt, L_val, color=color, s=100, zorder=5, edgecolors='white', linewidth=1.5)

    ax1.set_ylabel("Z-Score", fontsize=11)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(cum_df.index[0], cum_df.index[-1])
    plt.setp(ax1.get_xticklabels(), visible=False)

    # ========== Panel 2: 報酬面板 ==========
    ax2.set_title("Cumulative Returns: Strategy vs Benchmarks", fontsize=14, fontweight='bold')

    # 繪製狀態背景
    _draw_state_background(ax2, states)

    # 策略報酬
    ax2.plot(cum_df.index, cum_df.values, color='#1A1A2E', linewidth=2.5,
             label='Zeberg-Salomon Strategy', zorder=4)

    # 計算 benchmark 累積報酬（假設從 1 開始）
    # 這裡使用策略的累積報酬來推算 benchmark
    equity_cagr = benchmarks.get("equity_buy_hold", {}).get("cagr", 0)
    bond_cagr = benchmarks.get("bond_buy_hold", {}).get("cagr", 0)

    # 簡化：用 CAGR 來估算累積曲線
    years = np.array([(t - cum_df.index[0]).days / 365.25 for t in cum_df.index])
    equity_cum = (1 + equity_cagr) ** years
    bond_cum = (1 + bond_cagr) ** years

    ax2.plot(cum_df.index, equity_cum, color='#2E86AB', linewidth=1.5, linestyle='--',
             alpha=0.7, label=f'SPY Buy & Hold (CAGR: {equity_cagr:.1%})', zorder=3)
    ax2.plot(cum_df.index, bond_cum, color='#A23B72', linewidth=1.5, linestyle='--',
             alpha=0.7, label=f'TLT Buy & Hold (CAGR: {bond_cagr:.1%})', zorder=3)

    # 標記切換事件
    for event in switch_events:
        dt = pd.to_datetime(event["date"])
        if dt in cum_df.index:
            val = cum_df.loc[dt]
        else:
            # 找最近的日期
            idx = cum_df.index.get_indexer([dt], method='nearest')[0]
            val = cum_df.iloc[idx]

        color = '#D62839' if event["to_state"] == "RISK_OFF" else '#2E7D32'
        marker = 'v' if event["to_state"] == "RISK_OFF" else '^'
        ax2.scatter(dt, val, color=color, s=120, marker=marker, zorder=5,
                   edgecolors='white', linewidth=1.5)

    ax2.set_ylabel("Cumulative Return (1 = Initial)", fontsize=11)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    plt.setp(ax2.get_xticklabels(), visible=False)

    # ========== Panel 3: 狀態條帶 ==========
    _draw_state_bar(ax3, states)
    ax3.set_ylabel("State", fontsize=10)
    ax3.set_yticks([])
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.setp(ax3.get_xticklabels(), rotation=0, ha='center')

    # ========== Panel 4: 統計摘要 ==========
    ax4.axis('off')

    # 建立統計文字
    strategy_perf = data.get("backtest_summary", {}).get("performance", {})
    if not strategy_perf:
        # 從 cumulative series 計算
        total_ret = cum_df.iloc[-1] - 1
        years_total = len(cum_df) / 12
        cagr = (1 + total_ret) ** (1 / years_total) - 1 if years_total > 0 else 0
        strategy_perf = {"cumulative_return": total_ret, "cagr": cagr}

    current = data.get("current_state", {})
    latest = data.get("latest_indices", {})

    summary_text = (
        f"Strategy Performance (2000-2025)  |  "
        f"CAGR: {strategy_perf.get('cagr', 0):.1%}  |  "
        f"Total Switches: {len(switch_events)}  |  "
        f"Current State: {current.get('state', 'N/A')} (since {current.get('since', 'N/A')})  |  "
        f"Leading Index: {latest.get('LeadingIndex', 0):.2f}  |  "
        f"Coincident Index: {latest.get('CoincidentIndex', 0):.2f}"
    )

    ax4.text(0.5, 0.5, summary_text, ha='center', va='center', fontsize=10,
             transform=ax4.transAxes,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0F0F0', edgecolor='gray'))

    # 調整佈局
    plt.tight_layout()

    # 儲存或顯示
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Chart saved to: {output_path}", file=sys.stderr)

    if show:
        plt.show()
    else:
        plt.close()

    return output_path or ""


def _draw_state_background(ax, states: pd.Series):
    """繪製狀態背景色"""
    if states.empty:
        return

    current_state = states.iloc[0]
    start_idx = states.index[0]

    for i, (t, state) in enumerate(states.items()):
        if state != current_state or i == len(states) - 1:
            end_idx = t if i == len(states) - 1 else states.index[i]
            color = '#C8E6C9' if current_state == "RISK_ON" else '#FFCDD2'
            ax.axvspan(start_idx, end_idx, alpha=0.3, color=color, zorder=0)
            current_state = state
            start_idx = t


def _draw_state_bar(ax, states: pd.Series):
    """繪製狀態條帶圖"""
    if states.empty:
        return

    current_state = states.iloc[0]
    start_idx = states.index[0]

    for i, (t, state) in enumerate(states.items()):
        if state != current_state or i == len(states) - 1:
            end_idx = states.index[-1] if i == len(states) - 1 else states.index[i]
            color = '#4CAF50' if current_state == "RISK_ON" else '#F44336'
            ax.axvspan(start_idx, end_idx, alpha=0.8, color=color)
            current_state = state
            start_idx = t

    # 添加圖例
    risk_on_patch = mpatches.Patch(color='#4CAF50', alpha=0.8, label='RISK_ON (Equity)')
    risk_off_patch = mpatches.Patch(color='#F44336', alpha=0.8, label='RISK_OFF (Bonds)')
    ax.legend(handles=[risk_on_patch, risk_off_patch], loc='center left',
              bbox_to_anchor=(1.01, 0.5), fontsize=9)


def main():
    parser = argparse.ArgumentParser(
        description="Generate visualization for Zeberg-Salomon backtest results"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Input JSON file with backtest results"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: output/zeberg-salomon-YYYY-MM-DD.png)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the plot interactively"
    )

    args = parser.parse_args()

    # 讀取回測結果
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            result = json.load(f)
    else:
        # 從 stdin 讀取
        result = json.load(sys.stdin)

    # 解析數據
    data = parse_backtest_result(result)

    # 設定輸出路徑
    if args.output:
        output_path = args.output
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = f"output/zeberg-salomon-{today}.png"

    # 生成圖表
    create_visualization(data, output_path=output_path, show=args.show)
    print(output_path)


if __name__ == "__main__":
    main()
