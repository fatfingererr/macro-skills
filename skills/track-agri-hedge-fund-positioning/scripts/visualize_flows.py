#!/usr/bin/env python3
"""
資金流視覺化腳本

生成分組柱狀圖與火力時序圖。
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed, visualization disabled")


def plot_weekly_flows(
    flows_df: pd.DataFrame,
    output_path: str,
    title: str = "Hedge Fund Positioning: Weekly Flows by Group",
) -> None:
    """生成分組柱狀圖"""
    if not HAS_MATPLOTLIB:
        print("matplotlib not available, skipping visualization")
        return

    fig, ax = plt.subplots(figsize=(14, 7))

    # 準備資料
    if "date" in flows_df.columns:
        flows_df = flows_df.set_index("date")

    dates = flows_df.index
    x = np.arange(len(dates))
    width = 0.18

    # 顏色設定
    colors = {
        "grains": "#F4A460",     # Sandy Brown
        "oilseeds": "#32CD32",   # Lime Green
        "meats": "#DC143C",      # Crimson
        "softs": "#8B4513",      # Saddle Brown
    }

    # 繪製分組柱狀
    groups = ["grains", "oilseeds", "meats", "softs"]
    for i, (group, color) in enumerate([(g, colors[g]) for g in groups if g in flows_df.columns]):
        ax.bar(
            x + i * width,
            flows_df[group] / 1000,  # 轉為千合約
            width,
            label=group.capitalize(),
            color=color,
            alpha=0.8,
        )

    # 繪製總和線
    if "total" in flows_df.columns:
        ax.plot(
            x + 1.5 * width,
            flows_df["total"] / 1000,
            "k-o",
            label="Total",
            linewidth=2,
            markersize=4,
        )

    # 零線
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

    # 設定
    ax.set_xlabel("Week", fontsize=12)
    ax.set_ylabel("Net Flow (K contracts)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")

    # X 軸標籤
    if len(dates) <= 20:
        ax.set_xticks(x + 1.5 * width)
        ax.set_xticklabels([d.strftime("%m/%d") if hasattr(d, "strftime") else str(d)[:10] for d in dates], rotation=45)
    else:
        # 太多資料點時只顯示部分
        step = len(dates) // 10
        ax.set_xticks(x[::step] + 1.5 * width)
        ax.set_xticklabels([dates[i].strftime("%m/%d") if hasattr(dates[i], "strftime") else str(dates[i])[:10] for i in range(0, len(dates), step)], rotation=45)

    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Chart saved to {output_path}")


def plot_firepower_gauge(
    firepower: Dict[str, float],
    output_path: str,
) -> None:
    """生成火力儀表圖"""
    if not HAS_MATPLOTLIB:
        return

    fig, axes = plt.subplots(1, 5, figsize=(15, 3))

    groups = ["total", "grains", "oilseeds", "meats", "softs"]
    colors = ["#4169E1", "#F4A460", "#32CD32", "#DC143C", "#8B4513"]

    for ax, group, color in zip(axes, groups, colors):
        value = firepower.get(group, 0) or 0

        # 繪製半圓儀表
        theta = np.linspace(0, np.pi, 100)
        r = 1

        # 背景
        ax.fill_between(theta, 0, r, alpha=0.1, color="gray")

        # 區間著色
        ax.fill_between(theta[:30], 0, r, alpha=0.3, color="red")      # 0-0.3 危險
        ax.fill_between(theta[30:60], 0, r, alpha=0.3, color="yellow") # 0.3-0.6 中性
        ax.fill_between(theta[60:], 0, r, alpha=0.3, color="green")    # 0.6-1.0 安全

        # 指針
        needle_theta = value * np.pi
        ax.annotate(
            "",
            xy=(needle_theta, 0.9),
            xytext=(np.pi / 2, 0),
            arrowprops=dict(arrowstyle="->", color=color, lw=2),
        )

        # 數值
        ax.text(np.pi / 2, 0.5, f"{value:.0%}", ha="center", va="center", fontsize=14, fontweight="bold")
        ax.text(np.pi / 2, -0.3, group.capitalize(), ha="center", va="center", fontsize=10)

        ax.set_xlim(0, np.pi)
        ax.set_ylim(-0.5, 1.2)
        ax.set_aspect("equal")
        ax.axis("off")

    plt.suptitle("Buying Firepower", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Gauge saved to {output_path}")


def create_dashboard(result: Dict, output_path: str) -> None:
    """生成綜合儀表板"""
    if not HAS_MATPLOTLIB:
        return

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 左上：週流量
    ax1 = fig.add_subplot(gs[0, 0])
    flows = result.get("weekly_flows", [])
    if flows:
        df = pd.DataFrame(flows[-12:])  # 最近 12 週
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

        groups = ["grains", "oilseeds", "meats", "softs"]
        bottom = np.zeros(len(df))

        colors = ["#F4A460", "#32CD32", "#DC143C", "#8B4513"]
        for group, color in zip(groups, colors):
            if group in df.columns:
                values = df[group].values / 1000
                ax1.bar(range(len(df)), values, bottom=bottom, label=group.capitalize(), color=color, alpha=0.8)
                bottom = np.where(values > 0, bottom + values, bottom)

        ax1.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax1.set_title("Weekly Flows (K contracts)", fontweight="bold")
        ax1.legend(loc="upper left", fontsize=8)

    # 右上：火力
    ax2 = fig.add_subplot(gs[0, 1])
    firepower = result.get("latest_metrics", {}).get("buying_firepower", {})
    groups = ["total", "grains", "oilseeds", "meats", "softs"]
    values = [firepower.get(g, 0) or 0 for g in groups]
    colors = ["#4169E1", "#F4A460", "#32CD32", "#DC143C", "#8B4513"]

    bars = ax2.barh(groups, values, color=colors)
    ax2.axvline(x=0.3, color="red", linestyle="--", alpha=0.5, label="Crowded")
    ax2.axvline(x=0.6, color="green", linestyle="--", alpha=0.5, label="Room to buy")
    ax2.set_xlim(0, 1)
    ax2.set_title("Buying Firepower", fontweight="bold")

    # 左下：宏觀順風
    ax3 = fig.add_subplot(gs[1, 0])
    macro_score = result.get("latest_metrics", {}).get("macro_tailwind_score", 0) or 0

    # 簡單的儀表顯示
    ax3.pie(
        [macro_score, 1 - macro_score],
        colors=["#4CAF50", "#E0E0E0"],
        startangle=90,
        counterclock=False,
    )
    ax3.text(0, 0, f"{macro_score:.0%}", ha="center", va="center", fontsize=24, fontweight="bold")
    ax3.set_title("Macro Tailwind Score", fontweight="bold")

    # 右下：摘要
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")

    summary = result.get("summary", {})
    text = f"""
    Call: {summary.get('call', 'N/A')}
    Confidence: {summary.get('confidence', 0):.0%}

    Why:
    """ + "\n    ".join([f"• {w}" for w in summary.get("why", [])])

    ax4.text(0.1, 0.9, text, transform=ax4.transAxes, fontsize=11,
             verticalalignment="top", fontfamily="monospace")

    plt.suptitle(f"Agricultural Hedge Fund Positioning - {result.get('as_of', 'N/A')}", fontsize=14, fontweight="bold")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Dashboard saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize positioning flows")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input JSON file")
    parser.add_argument("-o", "--output", type=str, default="output/chart.png", help="Output file")
    parser.add_argument("--type", type=str, default="dashboard", choices=["flows", "firepower", "dashboard"], help="Chart type")

    args = parser.parse_args()

    # 載入資料
    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 生成圖表
    if args.type == "flows":
        flows_df = pd.DataFrame(result.get("weekly_flows", []))
        plot_weekly_flows(flows_df, str(output_path))
    elif args.type == "firepower":
        firepower = result.get("latest_metrics", {}).get("buying_firepower", {})
        plot_firepower_gauge(firepower, str(output_path))
    else:
        create_dashboard(result, str(output_path))


if __name__ == "__main__":
    main()
