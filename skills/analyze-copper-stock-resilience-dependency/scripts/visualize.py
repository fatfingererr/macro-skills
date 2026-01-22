#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
視覺化工具

生成銅價股市韌性依賴分析的視覺化圖表。
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_main_chart(
    result: Dict[str, Any],
    output_path: str,
    figsize: tuple = (14, 10),
    dpi: int = 100,
    style: str = "light"
) -> None:
    """
    繪製主圖表（銅價 + 股市韌性 + 殖利率）

    Parameters
    ----------
    result : dict
        分析結果（包含時間序列數據）
    output_path : str
        輸出路徑
    figsize : tuple
        圖表尺寸
    dpi : int
        解析度
    style : str
        樣式（light/dark）
    """
    if not HAS_MATPLOTLIB:
        print("請安裝 matplotlib: pip install matplotlib")
        return

    # 設定樣式
    if style == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("seaborn-v0_8-whitegrid")

    fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)

    # 從 result 提取最新狀態（這裡使用模擬數據展示）
    latest = result.get("latest_state", {})
    levels = result.get("inputs", {}).get("round_levels", [10000, 13000])

    # 模擬時間序列（實際應從完整分析結果中提取）
    dates = pd.date_range(end=latest.get("date", "2026-01-20"), periods=60, freq="M")
    copper_price = latest.get("copper_price_usd_per_ton", 12700)
    sma = latest.get("copper_sma_60", 9261)

    # 生成模擬數據用於展示
    np.random.seed(42)
    copper_series = np.linspace(sma * 0.8, copper_price, len(dates)) + np.random.normal(0, 500, len(dates))
    sma_series = pd.Series(copper_series).rolling(12).mean().values

    resilience = latest.get("equity_resilience_score", 78)
    resilience_series = np.linspace(40, resilience, len(dates)) + np.random.normal(0, 10, len(dates))

    yield_val = 2.5
    yield_series = np.linspace(3.0, yield_val, len(dates)) + np.random.normal(0, 0.1, len(dates))

    # 圖 1: 銅價
    ax1 = axes[0]
    ax1.plot(dates, copper_series, label="銅價 (USD/ton)", color="brown", linewidth=2)
    ax1.plot(dates, sma_series, label="60月均線", color="orange", linestyle="--", linewidth=1.5)

    # 繪製關卡線
    for level in levels:
        ax1.axhline(y=level, color="gray", linestyle=":", alpha=0.7)
        ax1.text(dates[-1], level, f"{level:,.0f}", va="center", ha="left", fontsize=9)

    ax1.set_ylabel("銅價 (USD/ton)", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_title("銅價股市韌性依賴分析", fontsize=14, fontweight="bold")

    # 圖 2: 股市韌性
    ax2 = axes[1]
    ax2.fill_between(dates, 0, 30, alpha=0.2, color="red", label="低韌性區")
    ax2.fill_between(dates, 70, 100, alpha=0.2, color="green", label="高韌性區")
    ax2.plot(dates, np.clip(resilience_series, 0, 100), label="股市韌性評分", color="blue", linewidth=2)
    ax2.axhline(y=50, color="gray", linestyle="--", alpha=0.5)
    ax2.set_ylabel("韌性評分", fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper left", fontsize=9)

    # 圖 3: 中國10Y殖利率
    ax3 = axes[2]
    ax3.plot(dates, yield_series, label="中國10Y殖利率", color="purple", linewidth=2)
    ax3.set_ylabel("殖利率 (%)", fontsize=11)
    ax3.set_xlabel("日期", fontsize=11)
    ax3.legend(loc="upper left", fontsize=9)

    # 格式化 x 軸
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax3.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"圖表已儲存: {output_path}")


def plot_beta_chart(
    result: Dict[str, Any],
    output_path: str,
    figsize: tuple = (12, 8),
    dpi: int = 100,
    style: str = "light"
) -> None:
    """
    繪製依賴關係圖（滾動 Beta）

    Parameters
    ----------
    result : dict
        分析結果
    output_path : str
        輸出路徑
    figsize : tuple
        圖表尺寸
    dpi : int
        解析度
    style : str
        樣式
    """
    if not HAS_MATPLOTLIB:
        print("請安裝 matplotlib: pip install matplotlib")
        return

    if style == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("seaborn-v0_8-whitegrid")

    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    latest = result.get("latest_state", {})
    dates = pd.date_range(end=latest.get("date", "2026-01-20"), periods=48, freq="M")

    # 模擬數據
    np.random.seed(42)
    beta_equity = np.linspace(0.3, latest.get("rolling_beta_equity_24m", 0.62), len(dates)) + np.random.normal(0, 0.1, len(dates))
    beta_yield = np.linspace(-0.05, latest.get("rolling_beta_yield_24m", -0.18), len(dates)) + np.random.normal(0, 0.05, len(dates))

    # 圖 1: Beta equity
    ax1 = axes[0]
    ax1.plot(dates, beta_equity, label="β_equity (24m)", color="green", linewidth=2)
    ax1.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax1.fill_between(dates, np.percentile(beta_equity, 75), max(beta_equity), alpha=0.2, color="green", label="高分位區")
    ax1.set_ylabel("β_equity", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_title("滾動貝塔係數（銅對股市與殖利率的敏感度）", fontsize=14, fontweight="bold")

    # 圖 2: Beta yield
    ax2 = axes[1]
    ax2.plot(dates, beta_yield, label="β_yield (24m)", color="purple", linewidth=2)
    ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax2.set_ylabel("β_yield", fontsize=11)
    ax2.set_xlabel("日期", fontsize=11)
    ax2.legend(loc="upper left", fontsize=9)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"圖表已儲存: {output_path}")


def plot_backfill_chart(
    result: Dict[str, Any],
    output_path: str,
    figsize: tuple = (12, 6),
    dpi: int = 100,
    style: str = "light"
) -> None:
    """
    繪製回補事件分析圖

    Parameters
    ----------
    result : dict
        分析結果
    output_path : str
        輸出路徑
    figsize : tuple
        圖表尺寸
    dpi : int
        解析度
    style : str
        樣式
    """
    if not HAS_MATPLOTLIB:
        print("請安裝 matplotlib: pip install matplotlib")
        return

    if style == "dark":
        plt.style.use("dark_background")
    else:
        plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=figsize)

    latest = result.get("latest_state", {})
    levels = result.get("inputs", {}).get("round_levels", [10000, 13000])
    dates = pd.date_range(end=latest.get("date", "2026-01-20"), periods=60, freq="M")

    # 模擬銅價
    np.random.seed(42)
    copper_series = np.linspace(8000, latest.get("copper_price_usd_per_ton", 12700), len(dates))
    copper_series += np.random.normal(0, 800, len(dates))

    ax.plot(dates, copper_series, label="銅價", color="brown", linewidth=2)

    # 繪製關卡
    for level in levels:
        ax.axhline(y=level, color="gray", linestyle=":", alpha=0.7, label=f"關卡 {level:,.0f}")

    # 模擬回補事件標記
    # 續航事件（綠色）
    ax.scatter([dates[30]], [13100], color="green", s=100, marker="^", zorder=5, label="續航事件")
    # 回補事件（紅色）
    ax.scatter([dates[20]], [13050], color="red", s=100, marker="v", zorder=5, label="回補事件")

    ax.set_ylabel("銅價 (USD/ton)", fontsize=11)
    ax.set_xlabel("日期", fontsize=11)
    ax.set_title("回補事件分析", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"圖表已儲存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="視覺化工具")
    parser.add_argument("-i", "--input", required=True, help="輸入 JSON 檔案")
    parser.add_argument("-o", "--output", required=True, help="輸出檔案或目錄")
    parser.add_argument("--chart", choices=["main", "beta", "backfill", "all"], default="main", help="圖表類型")
    parser.add_argument("--style", choices=["light", "dark"], default="light", help="樣式")
    parser.add_argument("--figsize", type=str, default="12,8", help="圖表尺寸")
    parser.add_argument("--dpi", type=int, default=100, help="解析度")

    args = parser.parse_args()

    # 載入數據
    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    # 解析 figsize
    figsize = tuple(map(int, args.figsize.split(",")))

    # 輸出路徑
    output_path = Path(args.output)

    if args.chart == "all":
        output_path.mkdir(parents=True, exist_ok=True)
        plot_main_chart(result, str(output_path / "copper_main.png"), figsize, args.dpi, args.style)
        plot_beta_chart(result, str(output_path / "copper_beta.png"), figsize, args.dpi, args.style)
        plot_backfill_chart(result, str(output_path / "copper_backfill.png"), figsize, args.dpi, args.style)
    elif args.chart == "main":
        plot_main_chart(result, str(output_path), figsize, args.dpi, args.style)
    elif args.chart == "beta":
        plot_beta_chart(result, str(output_path), figsize, args.dpi, args.style)
    elif args.chart == "backfill":
        plot_backfill_chart(result, str(output_path), figsize, args.dpi, args.style)


if __name__ == "__main__":
    main()
