#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上海白銀庫存耗盡視覺化報告生成器

根據分析結果生成視覺化圖表和報告。

Usage:
    python visualize_drain.py --result result.json --output ../../../output/
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.gridspec import GridSpec
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    plt = None
    print("警告: matplotlib 未安裝，視覺化功能不可用")
    print("請執行: pip install matplotlib")

# 設定目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"


def load_combined_stock() -> pd.DataFrame:
    """
    載入合併庫存時間序列

    Returns
    -------
    pd.DataFrame
        庫存時間序列
    """
    # 嘗試從快取載入
    cache_path = DATA_DIR / "combined_stock.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, parse_dates=["date"])

    # 合併 SGE + SHFE
    dfs = []

    sge_path = DATA_DIR / "sge_stock.csv"
    if sge_path.exists():
        df_sge = pd.read_csv(sge_path, parse_dates=["date"])
        df_sge = df_sge.rename(columns={"stock_kg": "sge_kg"})
        dfs.append(df_sge)

    shfe_path = DATA_DIR / "shfe_stock.csv"
    if shfe_path.exists():
        df_shfe = pd.read_csv(shfe_path, parse_dates=["date"])
        df_shfe = df_shfe.rename(columns={"stock_kg": "shfe_kg"})
        dfs.append(df_shfe)

    if not dfs:
        raise FileNotFoundError("找不到庫存數據檔案")

    if len(dfs) == 1:
        df = dfs[0]
        if "sge_kg" in df.columns:
            df["combined_kg"] = df["sge_kg"]
        else:
            df["combined_kg"] = df["shfe_kg"]
    else:
        df = pd.merge(dfs[0], dfs[1], on="date", how="outer")
        df["combined_kg"] = df["sge_kg"].fillna(0) + df["shfe_kg"].fillna(0)

    df["combined_tonnes"] = df["combined_kg"] / 1000.0
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


def create_drain_report_figure(
    result: Dict[str, Any],
    df: pd.DataFrame,
    figsize: tuple = (14, 10)
) -> plt.Figure:
    """
    建立耗盡報告圖表

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

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.5, 1, 1])

    # 顏色配置
    colors = {
        "stock": "#1f77b4",
        "drain_rate": "#ff7f0e",
        "z_score": "#2ca02c",
        "threshold": "#d62728",
        "signal_high": "#d62728",
        "signal_medium": "#ff7f0e",
        "signal_watch": "#ffbb00",
        "signal_none": "#2ca02c"
    }

    # 訊號顏色
    signal = result.get("result", {}).get("signal", "NO_SIGNAL")
    signal_color = {
        "HIGH_LATE_STAGE_SUPPLY_SIGNAL": colors["signal_high"],
        "MEDIUM_SUPPLY_TIGHTENING": colors["signal_medium"],
        "WATCH": colors["signal_watch"],
        "NO_SIGNAL": colors["signal_none"]
    }.get(signal, colors["signal_none"])

    # ==================== 圖表 1：庫存走勢 ====================
    ax1 = fig.add_subplot(gs[0, :])

    ax1.plot(df["date"], df["combined_tonnes"], color=colors["stock"], linewidth=2, label="合併庫存 (噸)")
    ax1.fill_between(df["date"], df["combined_tonnes"], alpha=0.3, color=colors["stock"])

    # 標記當前位置
    latest_stock = result.get("result", {}).get("latest_combined_stock", df["combined_tonnes"].iloc[-1])
    ax1.axhline(y=latest_stock, color=signal_color, linestyle="--", alpha=0.7, label=f"當前: {latest_stock:.1f} 噸")

    ax1.set_title("上海白銀庫存走勢（SGE + SHFE）", fontsize=14, fontweight="bold")
    ax1.set_ylabel("庫存 (噸)", fontsize=12)
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

    # ==================== 圖表 2：耗盡速度 ====================
    ax2 = fig.add_subplot(gs[1, 0])

    ax2.bar(df["date"], df["drain_rate_sm"], color=colors["drain_rate"], alpha=0.7, width=5, label="耗盡速度 (4週平滑)")
    ax2.axhline(y=0, color="black", linewidth=1)

    ax2.set_title("耗盡速度（正值=流出）", fontsize=12, fontweight="bold")
    ax2.set_ylabel("噸/週", fontsize=10)
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # ==================== 圖表 3：Z 分數 ====================
    ax3 = fig.add_subplot(gs[1, 1])

    ax3.plot(df["date"], df["z_drain_rate"], color=colors["z_score"], linewidth=1.5, label="耗盡速度 Z 分數")

    # 門檻線
    ax3.axhline(y=-1.5, color=colors["threshold"], linestyle="--", alpha=0.7, label="異常門檻 (-1.5)")
    ax3.axhline(y=0, color="gray", linewidth=1)

    # 標記當前值
    z_drain = result.get("result", {}).get("z_scores", {}).get("z_drain_rate", 0)
    ax3.scatter([df["date"].iloc[-1]], [z_drain], color=signal_color, s=100, zorder=5)
    ax3.annotate(f"Z = {z_drain:.2f}", xy=(df["date"].iloc[-1], z_drain),
                 xytext=(10, 10), textcoords="offset points", fontsize=10)

    ax3.set_title("耗盡速度 Z 分數", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Z 分數", fontsize=10)
    ax3.legend(loc="upper right")
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # ==================== 圖表 4：訊號摘要 ====================
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis("off")

    # 訊號文字
    signal_text = {
        "HIGH_LATE_STAGE_SUPPLY_SIGNAL": "🔴 HIGH：晚期供給訊號",
        "MEDIUM_SUPPLY_TIGHTENING": "🟡 MEDIUM：供給趨緊",
        "WATCH": "🟠 WATCH：單一異常",
        "NO_SIGNAL": "🟢 NO_SIGNAL：正常"
    }.get(signal, signal)

    # 建立摘要表格
    summary_data = [
        ["訊號等級", signal_text],
        ["合併庫存", f"{latest_stock:.1f} 噸"],
        ["庫存分位數", f"{result.get('result', {}).get('level_percentile', 0)*100:.1f}%"],
        ["耗盡速度 Z", f"{z_drain:.2f}"],
        ["加速度 Z", f"+{result.get('result', {}).get('z_scores', {}).get('z_acceleration', 0):.2f}"],
    ]

    # 條件判定
    conditions = result.get("result", {}).get("signal_conditions", {})
    cond_text = []
    cond_text.append(f"{'✅' if conditions.get('A_level_low') else '❌'} A. 庫存水位偏低")
    cond_text.append(f"{'✅' if conditions.get('B_drain_abnormal') else '❌'} B. 耗盡速度異常")
    cond_text.append(f"{'✅' if conditions.get('C_acceleration') else '❌'} C. 耗盡加速")

    # 繪製文字
    y_pos = 0.9
    ax4.text(0.1, y_pos, "分析摘要", fontsize=14, fontweight="bold", transform=ax4.transAxes)
    y_pos -= 0.15

    for item in summary_data:
        ax4.text(0.1, y_pos, f"{item[0]}：", fontsize=11, transform=ax4.transAxes)
        ax4.text(0.35, y_pos, item[1], fontsize=11, fontweight="bold",
                 color=signal_color if item[0] == "訊號等級" else "black",
                 transform=ax4.transAxes)
        y_pos -= 0.12

    # 條件判定
    ax4.text(0.55, 0.9, "訊號條件判定", fontsize=14, fontweight="bold", transform=ax4.transAxes)
    y_pos = 0.75
    for cond in cond_text:
        ax4.text(0.55, y_pos, cond, fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.12

    # 數據來源
    ax4.text(0.55, 0.3, f"數據來源：{', '.join(result.get('sources', ['SGE', 'SHFE']))}",
             fontsize=10, style="italic", transform=ax4.transAxes)
    ax4.text(0.55, 0.15, f"分析日期：{result.get('as_of', datetime.now().strftime('%Y-%m-%d'))}",
             fontsize=10, style="italic", transform=ax4.transAxes)

    plt.tight_layout()
    return fig


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="上海白銀庫存耗盡視覺化報告")
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
        fig.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
        print(f"PNG 圖表已儲存至: {png_path}")

    if args.format in ["pdf", "both"]:
        pdf_path = output_dir / f"{base_name}.pdf"
        fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
        print(f"PDF 報告已儲存至: {pdf_path}")

    plt.close(fig)


if __name__ == "__main__":
    main()
