#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上海白銀庫存耗盡視覺化報告生成器 (Bloomberg 風格)

根據分析結果生成視覺化圖表和報告。

Usage:
    python visualize_drain.py --result result.json --output ../../../output/
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前設定

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter

    # 中文字體設定
    plt.rcParams['font.sans-serif'] = [
        'Microsoft JhengHei',
        'SimHei',
        'Microsoft YaHei',
        'PingFang TC',
        'Noto Sans CJK TC',
        'DejaVu Sans'
    ]
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    plt = None
    print("警告: matplotlib 未安裝，視覺化功能不可用")
    print("請執行: pip install matplotlib")

# Bloomberg 風格配色
COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "primary": "#ff6b35",
    "secondary": "#ffaa00",
    "tertiary": "#ffff00",
    "area_fill": "#ff8c00",
    "area_alpha": 0.4,
    "level_line": "#666666",
    "signal_high": "#ff4444",
    "signal_medium": "#ffaa00",
    "signal_watch": "#ffff00",
    "signal_none": "#00ff88",
}

# 設定目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"


def load_combined_stock() -> pd.DataFrame:
    """
    載入庫存時間序列（主要從 CEIC/SHFE 數據）

    Returns
    -------
    pd.DataFrame
        庫存時間序列
    """
    # 主要使用 SHFE 數據（來自 CEIC）
    shfe_path = DATA_DIR / "shfe_stock.csv"

    if not shfe_path.exists():
        raise FileNotFoundError(
            f"找不到數據檔案: {shfe_path}\n"
            "請先執行: python fetch_shfe_stock.py --force-update"
        )

    df = pd.read_csv(shfe_path, parse_dates=["date"])

    # 轉換單位
    if "stock_kg" in df.columns:
        df["combined_kg"] = df["stock_kg"]
        df["combined_tonnes"] = df["stock_kg"] / 1000.0
    elif "stock_tonnes" in df.columns:
        df["combined_tonnes"] = df["stock_tonnes"]
        df["combined_kg"] = df["stock_tonnes"] * 1000

    df = df.sort_values("date").reset_index(drop=True)

    # 計算指標
    df["delta1"] = df["combined_tonnes"].diff(1)
    df["drain_rate"] = -df["delta1"]
    df["drain_rate_sm"] = df["drain_rate"].rolling(4, min_periods=1).mean()

    # Z 分數
    z_window = 156
    rolling_mean = df["drain_rate_sm"].rolling(z_window, min_periods=20).mean()
    rolling_std = df["drain_rate_sm"].rolling(z_window, min_periods=20).std()
    df["z_drain_rate"] = (df["drain_rate_sm"] - rolling_mean) / rolling_std

    return df


def format_tonnes(x, pos):
    """噸數格式化"""
    if x >= 1000:
        return f'{x/1000:.1f}K'
    return f'{x:.0f}'


def create_drain_report_figure(
    result: Dict[str, Any],
    df: pd.DataFrame,
    figsize: tuple = (14, 8)
) -> plt.Figure:
    """
    建立 Bloomberg 風格耗盡報告圖表

    Parameters
    ----------
    result : dict
        分析結果
    df : pd.DataFrame
        庫存時間序列
    figsize : tuple
        圖表大小

    Returns
    -------
    plt.Figure
        圖表物件
    """
    if plt is None:
        raise ImportError("matplotlib 未安裝")

    plt.style.use('dark_background')

    # 2/3 上方庫存走勢，1/3 下方耗盡速度
    fig, axes = plt.subplots(2, 1, figsize=figsize, facecolor=COLORS["background"],
                             gridspec_kw={'height_ratios': [2, 1]})
    fig.set_facecolor(COLORS["background"])

    # 訊號顏色
    signal = result.get("result", {}).get("signal", "NO_SIGNAL")
    signal_color = {
        "HIGH_LATE_STAGE_SUPPLY_SIGNAL": COLORS["signal_high"],
        "MEDIUM_SUPPLY_TIGHTENING": COLORS["signal_medium"],
        "WATCH": COLORS["signal_watch"],
        "NO_SIGNAL": COLORS["signal_none"]
    }.get(signal, COLORS["signal_none"])

    latest_stock = result.get("result", {}).get("latest_combined_stock", df["combined_tonnes"].iloc[-1])

    # 計算 50 EMA
    df["ema50"] = df["combined_tonnes"].ewm(span=50, adjust=False).mean()

    # ==================== 圖表 1：庫存走勢 (上方 2/3) ====================
    ax1 = axes[0]
    ax1.set_facecolor(COLORS["background"])

    ax1.fill_between(df["date"], df["combined_tonnes"], alpha=COLORS["area_alpha"],
                     color=COLORS["area_fill"], zorder=1)
    ax1.plot(df["date"], df["combined_tonnes"], color=COLORS["primary"],
             linewidth=2, label="合併庫存", zorder=5)

    # 50 周 EMA 趨勢線
    ax1.plot(df["date"], df["ema50"], color=COLORS["secondary"],
             linewidth=1.5, linestyle="--", label="50 周 EMA", zorder=4)

    # 標記當前位置
    ax1.axhline(y=latest_stock, color=signal_color, linestyle="--",
                alpha=0.7, linewidth=1.5, zorder=2)

    # 最新值標註
    ax1.annotate(
        f'{latest_stock:.0f}',
        xy=(df["date"].iloc[-1], latest_stock),
        xytext=(10, 0),
        textcoords='offset points',
        color=signal_color,
        fontsize=11,
        fontweight='bold',
        va='center'
    )

    ax1.set_title("上海白銀庫存走勢", fontsize=12, fontweight="bold", color=COLORS["text"])
    ax1.set_ylabel("庫存 (噸)", fontsize=10, color=COLORS["text_dim"])
    ax1.yaxis.set_major_formatter(FuncFormatter(format_tonnes))
    ax1.tick_params(axis='y', colors=COLORS["text_dim"])
    ax1.tick_params(axis='x', colors=COLORS["text_dim"])
    ax1.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())

    # 圖例
    ax1.legend(loc='upper right', fontsize=8,
               facecolor=COLORS["background"], edgecolor=COLORS["grid"],
               labelcolor=COLORS["text"])

    # ==================== 圖表 2：耗盡速度 (下方 1/3) ====================
    ax2 = axes[1]
    ax2.set_facecolor(COLORS["background"])

    # 正負色彩
    colors_bar = [COLORS["signal_high"] if v > 0 else COLORS["signal_none"]
                  for v in df["drain_rate_sm"].fillna(0)]

    ax2.bar(df["date"], df["drain_rate_sm"], color=colors_bar, alpha=0.7, width=5, zorder=3)
    ax2.axhline(y=0, color=COLORS["level_line"], linewidth=1, zorder=2)

    ax2.set_title("耗盡速度 (正值=流出)", fontsize=12, fontweight="bold", color=COLORS["text"])
    ax2.set_ylabel("噸/週 (4週平滑)", fontsize=10, color=COLORS["text_dim"])
    ax2.tick_params(axis='y', colors=COLORS["text_dim"])
    ax2.tick_params(axis='x', colors=COLORS["text_dim"])
    ax2.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax2.set_axisbelow(True)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())

    # ==================== 標題 ====================
    signal_label = {
        "HIGH_LATE_STAGE_SUPPLY_SIGNAL": "HIGH",
        "MEDIUM_SUPPLY_TIGHTENING": "MEDIUM",
        "WATCH": "WATCH",
        "NO_SIGNAL": "NO_SIGNAL"
    }.get(signal, signal)

    fig.suptitle(
        f"上海白銀庫存消耗趨勢",
        color=COLORS["text"],
        fontsize=14,
        fontweight='bold',
        y=0.98
    )

    # ==================== 頁尾 ====================
    sources = result.get("sources", ["SGE", "SHFE"])
    as_of = result.get("as_of", datetime.now().strftime("%Y-%m-%d"))

    fig.text(
        0.02, 0.02,
        f"資料來源: CEIC ({', '.join(sources)})",
        color=COLORS["text_dim"],
        fontsize=8,
        ha='left'
    )

    fig.text(
        0.98, 0.02,
        f'截至: {as_of}',
        color=COLORS["text_dim"],
        fontsize=8,
        ha='right'
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    return fig


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="上海白銀庫存耗盡視覺化報告 (Bloomberg 風格)")
    parser.add_argument(
        "--result",
        type=str,
        required=True,
        help="分析結果 JSON 檔案路徑"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="輸出目錄"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "both"],
        help="輸出格式"
    )

    args = parser.parse_args()

    if plt is None:
        print("錯誤: matplotlib 未安裝，無法生成圖表")
        return

    # 載入分析結果
    result_path = Path(args.result)
    if not result_path.exists():
        print(f"錯誤: 找不到結果檔案 {result_path}")
        return

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    # 載入庫存數據
    try:
        df = load_combined_stock()
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
        print("請先執行數據抓取腳本")
        return

    # 建立圖表
    fig = create_drain_report_figure(result, df)

    # 儲存
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    as_of = result.get("as_of", datetime.now().strftime("%Y%m%d")).replace("-", "")
    base_name = f"shanghai_silver_drain_report_{as_of}"

    if args.format in ["png", "both"]:
        png_path = output_dir / f"{base_name}.png"
        fig.savefig(png_path, dpi=150, bbox_inches="tight", facecolor=COLORS["background"])
        print(f"PNG 圖表已儲存至: {png_path}")

    if args.format in ["pdf", "both"]:
        pdf_path = output_dir / f"{base_name}.pdf"
        fig.savefig(pdf_path, bbox_inches="tight", facecolor=COLORS["background"])
        print(f"PDF 報告已儲存至: {pdf_path}")

    plt.close(fig)


if __name__ == "__main__":
    main()
