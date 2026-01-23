#!/usr/bin/env python3
"""
visualize.py - Bloomberg 風格視覺化工具

生成利率波動率領先落後分析的多面板圖表。
遵循 Bloomberg Intelligence 風格指南。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator

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

from fetch_data import fetch_all_data
from analyze import rolling_zscore, identify_shock_events


# =============================================================================
# Bloomberg 配色定義
# =============================================================================

COLORS = {
    # 背景與網格
    "background": "#1a1a2e",
    "grid": "#2d2d44",

    # 文字
    "text": "#ffffff",
    "text_dim": "#888888",

    # 主要數據線
    "primary": "#ff6b35",       # 橙紅色（MOVE）
    "secondary": "#ffaa00",     # 橙黃色（VIX）
    "tertiary": "#ffff00",      # 黃色（Credit）
    "jgb": "#00ff88",           # 綠色（JGB）

    # 輔助元素
    "shock_line": "#ff4444",    # 紅色（衝擊事件）
    "level_line": "#666666",
    "zero_line": "#555555",
    "annotation": "#ffffff",

    # 面積圖
    "area_fill": "#ff8c00",
    "area_alpha": 0.3,

    # Cross-correlation
    "corr_vix": "#ffaa00",
    "corr_credit": "#00ff88",
}


# =============================================================================
# 視覺化函數
# =============================================================================

def create_bloomberg_chart(
    df: pd.DataFrame,
    result: dict,
    output_path: str,
    dpi: int = 150
):
    """
    生成 Bloomberg 風格 2x3 面板分析圖表

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

    佈局:
    ┌──────────┬──────────────────────────┐
    │ 交叉相關  │ 波動率指標時間序列        │
    │  (1,1)   │    (1,2) + (1,3)         │
    ├──────────┼──────────────────────────┤
    │ 事件反應  │ 標準化序列（Z 分數）      │
    │  (2,1)   │    (2,2) + (2,3)         │
    └──────────┴──────────────────────────┘
    """
    plt.style.use('dark_background')

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

    # 創建圖表（2x3 佈局）
    fig = plt.figure(figsize=(18, 10), facecolor=COLORS["background"])

    # 使用 GridSpec 建立 2x3 佈局
    gs = fig.add_gridspec(2, 3, hspace=0.28, wspace=0.15,
                          left=0.06, right=0.94, top=0.91, bottom=0.08,
                          width_ratios=[1, 1, 1])

    # =========================================================================
    # Panel 1: Cross-Correlation（左上 1,1）
    # =========================================================================
    ax_corr = fig.add_subplot(gs[0, 0])
    ax_corr.set_facecolor(COLORS["background"])

    ax_corr.plot(lags, corr_vix_all, label="MOVE vs VIX",
                 color=COLORS["corr_vix"], linewidth=2, zorder=5)
    ax_corr.plot(lags, corr_credit_all, label="MOVE vs Credit",
                 color=COLORS["corr_credit"], linewidth=2, zorder=4)

    ax_corr.axvline(0, color=COLORS["level_line"], linestyle="--", alpha=0.6, linewidth=1)
    ax_corr.axhline(0, color=COLORS["zero_line"], linestyle="-", alpha=0.4, linewidth=0.8)

    # Mark best lags
    leadlag = result.get("leadlag", {})
    best_lag_vix = leadlag.get("MOVE_vs_VIX", {}).get("best_lag_days", 0)
    best_lag_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("best_lag_days", 0)
    best_corr_vix = leadlag.get("MOVE_vs_VIX", {}).get("corr", 0)
    best_corr_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("corr", 0)

    ax_corr.scatter([best_lag_vix], [best_corr_vix], color=COLORS["corr_vix"],
                    s=100, zorder=6, edgecolor=COLORS["text"], linewidth=2)
    ax_corr.scatter([best_lag_credit], [best_corr_credit], color=COLORS["corr_credit"],
                    s=100, zorder=6, edgecolor=COLORS["text"], linewidth=2)

    # Annotations
    ax_corr.annotate(f"lag={best_lag_vix:+d}, r={best_corr_vix:.2f}",
                     xy=(best_lag_vix, best_corr_vix),
                     xytext=(best_lag_vix + 2, best_corr_vix + 0.06),
                     fontsize=8, color=COLORS["corr_vix"], fontweight="bold")
    ax_corr.annotate(f"lag={best_lag_credit:+d}, r={best_corr_credit:.2f}",
                     xy=(best_lag_credit, best_corr_credit),
                     xytext=(best_lag_credit + 2, best_corr_credit - 0.06),
                     fontsize=8, color=COLORS["corr_credit"], fontweight="bold")

    ax_corr.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_corr.set_axisbelow(True)
    ax_corr.set_xlabel("Lag (天數，正值 = MOVE 領先)", color=COLORS["text_dim"], fontsize=9)
    ax_corr.set_ylabel("相關係數", color=COLORS["text"], fontsize=9)
    ax_corr.set_xlim(-lead_lag_max_days - 2, lead_lag_max_days + 2)
    ax_corr.tick_params(axis='both', colors=COLORS["text_dim"], labelsize=8)

    ax_corr.set_title("交叉相關分析", color=COLORS["text"],
                      fontsize=11, fontweight="bold", pad=8)
    ax_corr.legend(loc="upper right", fontsize=7,
                   facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                   labelcolor=COLORS["text"])

    # =========================================================================
    # Panel 2: Event Window Reactions（左下 2,1）
    # =========================================================================
    ax_hist = fig.add_subplot(gs[1, 0])
    ax_hist.set_facecolor(COLORS["background"])

    move_change = df_smooth["MOVE"] - df_smooth["MOVE"].shift(shock_window_days)
    reactions = move_change[shock].dropna()

    if len(reactions) > 0:
        n, bins, patches = ax_hist.hist(reactions, bins=min(12, max(5, len(reactions))),
                                         alpha=0.8, color=COLORS["primary"],
                                         edgecolor=COLORS["text"], linewidth=0.8)

        mean_reaction = reactions.mean()
        ax_hist.axvline(mean_reaction, color=COLORS["secondary"],
                        linestyle="--", linewidth=2.5,
                        label=f"平均: {mean_reaction:.1f}", zorder=10)
        ax_hist.axvline(0, color=COLORS["zero_line"], linestyle="-",
                        alpha=0.6, linewidth=1.2)

        ax_hist.set_xlabel("MOVE 反應（事件窗內變化）", color=COLORS["text_dim"], fontsize=9)
        ax_hist.set_ylabel("頻率", color=COLORS["text"], fontsize=9)

        spooked = result.get("spooked_check", {})
        verdict = spooked.get("spooked_verdict", "")
        verdict_color = COLORS["shock_line"] if verdict == "SPOOKED" else COLORS["jgb"]
        verdict_text = "恐慌" if verdict == "SPOOKED" else "未恐慌"

        ax_hist.text(0.95, 0.95, f"判定: {verdict_text}",
                     transform=ax_hist.transAxes,
                     fontsize=10, fontweight="bold",
                     color=verdict_color,
                     ha="right", va="top",
                     bbox=dict(boxstyle="round,pad=0.3",
                              facecolor=COLORS["background"],
                              edgecolor=verdict_color, linewidth=2))

        ax_hist.set_title(f"MOVE 事件反應分布（{len(reactions)} 次衝擊）",
                          color=COLORS["text"], fontsize=11, fontweight="bold", pad=8)
        ax_hist.legend(loc="upper left", fontsize=7,
                       facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                       labelcolor=COLORS["text"])
    else:
        ax_hist.text(0.5, 0.5, "無衝擊事件",
                     ha="center", va="center", transform=ax_hist.transAxes,
                     fontsize=12, color=COLORS["text_dim"])
        ax_hist.set_title("MOVE 事件反應分布（無事件）",
                          color=COLORS["text"], fontsize=11, fontweight="bold", pad=8)

    ax_hist.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_hist.set_axisbelow(True)
    ax_hist.tick_params(axis='both', colors=COLORS["text_dim"], labelsize=8)

    # =========================================================================
    # Panel 3: 時間序列（上方跨兩格 1,2 + 1,3）
    # =========================================================================
    ax_ts = fig.add_subplot(gs[0, 1:])
    ax_ts.set_facecolor(COLORS["background"])

    line_move, = ax_ts.plot(df.index, df["MOVE"], label="MOVE Index",
                            color=COLORS["primary"], linewidth=2, zorder=5)
    ax_ts.set_ylabel("MOVE Index", color=COLORS["primary"], fontsize=10)
    ax_ts.tick_params(axis="y", labelcolor=COLORS["primary"])

    ax_ts_r = ax_ts.twinx()
    line_vix, = ax_ts_r.plot(df.index, df["VIX"], label="VIX",
                             color=COLORS["secondary"], linewidth=1.5, alpha=0.8, zorder=4)
    ax_ts_r.set_ylabel("VIX", color=COLORS["secondary"], fontsize=10)
    ax_ts_r.tick_params(axis="y", labelcolor=COLORS["secondary"])

    for shock_date in shock_dates:
        ax_ts.axvline(shock_date, color=COLORS["shock_line"],
                      linestyle="--", alpha=0.4, linewidth=1, zorder=2)

    ax_ts.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_ts.set_axisbelow(True)
    ax_ts.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax_ts.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_ts.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0, labelsize=8)
    ax_ts.tick_params(axis='y', colors=COLORS["primary"], labelsize=8)
    ax_ts_r.tick_params(axis='y', labelsize=8)

    ax_ts.set_title("波動率指標時間序列", color=COLORS["text"],
                    fontsize=11, fontweight="bold", pad=8)

    lines = [line_move, line_vix]
    labels = ["MOVE", "VIX"]
    ax_ts.legend(lines, labels, loc="upper left", fontsize=8,
                 facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                 labelcolor=COLORS["text"])

    latest_move = df["MOVE"].iloc[-1]
    ax_ts.annotate(f'{latest_move:.1f}',
                   xy=(df.index[-1], latest_move),
                   xytext=(8, 0), textcoords='offset points',
                   color=COLORS["primary"], fontsize=10, fontweight='bold',
                   va='center')

    # =========================================================================
    # Panel 4: Z-Scores（下方跨兩格 2,2 + 2,3）
    # =========================================================================
    ax_z = fig.add_subplot(gs[1, 1:])
    ax_z.set_facecolor(COLORS["background"])

    ax_z.plot(df_z.index, df_z["MOVE"], label="MOVE Z",
              color=COLORS["primary"], linewidth=2, zorder=5)
    ax_z.plot(df_z.index, df_z["VIX"], label="VIX Z",
              color=COLORS["secondary"], linewidth=1.5, alpha=0.7, zorder=4)
    ax_z.plot(df_z.index, df_z["CREDIT"], label="Credit Z",
              color=COLORS["tertiary"], linewidth=1.5, alpha=0.7, zorder=3)

    ax_z.axhline(0, color=COLORS["zero_line"], linestyle="-", alpha=0.6, linewidth=1)
    ax_z.axhline(1, color=COLORS["level_line"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(-1, color=COLORS["level_line"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(2, color=COLORS["shock_line"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(-2, color=COLORS["shock_line"], linestyle="--", alpha=0.4, linewidth=0.8)

    move_z_now = result.get("spooked_check", {}).get("MOVE_zscore_now")
    if move_z_now is not None:
        ax_z.scatter([df_z.index[-1]], [move_z_now], color=COLORS["primary"],
                     s=100, zorder=6, edgecolor=COLORS["text"], linewidth=2)
        ax_z.annotate(f'Now: {move_z_now:.2f}',
                      xy=(df_z.index[-1], move_z_now),
                      xytext=(10, 5), textcoords='offset points',
                      color=COLORS["primary"], fontsize=9, fontweight='bold')

    ax_z.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_z.set_axisbelow(True)
    ax_z.set_ylabel("Z-Score", color=COLORS["text"], fontsize=10)
    ax_z.set_ylim(-4, 4)
    ax_z.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax_z.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_z.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0, labelsize=8)
    ax_z.tick_params(axis='y', colors=COLORS["text_dim"], labelsize=8)

    ax_z.set_title("標準化序列（Z 分數）", color=COLORS["text"],
                   fontsize=11, fontweight="bold", pad=8)
    ax_z.legend(loc="upper left", fontsize=8,
                facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                labelcolor=COLORS["text"])

    # =========================================================================
    # 主標題
    # =========================================================================
    fig.suptitle("利率波動率領先落後分析 (MOVE vs VIX vs Credit)",
                 color=COLORS["text"], fontsize=14, fontweight="bold", y=0.97)

    # =========================================================================
    # 頁尾（移除左下資料來源）
    # =========================================================================
    # 日期（右下）
    as_of = result.get("as_of", datetime.now().strftime("%Y-%m-%d"))
    fig.text(0.94, 0.02, f'截至: {as_of}',
             color=COLORS["text_dim"], fontsize=8, ha='right')

    # 結論（中央偏左）
    headline = result.get("headline", "")
    if headline:
        fig.text(0.40, 0.02, headline,
                 color=COLORS["secondary"], fontsize=9, fontweight="bold",
                 ha='center')

    # =========================================================================
    # 輸出
    # =========================================================================
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor=COLORS["background"])
    plt.close()

    print(f"Chart saved to {output_path}")
    return str(output_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Visualize rates vol leadlag analysis (Bloomberg style)")
    parser.add_argument("-i", "--input", help="Input JSON result file")
    parser.add_argument("-o", "--output", help="Output image path (default: output/move-leadlag-YYYY-MM-DD.png)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--dpi", type=int, default=150, help="Resolution (DPI)")

    args = parser.parse_args()

    # Determine output path
    today = datetime.now().strftime("%Y-%m-%d")
    if args.output:
        output_path = args.output
    else:
        # 使用專案根目錄的 output/
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        output_path = project_root / "output" / f"move-leadlag-{today}.png"

    # Load result or run analysis
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            result = json.load(f)
        params = result.get("params", {})
        start_date = params.get("start_date")
        end_date = params.get("end_date")
    else:
        if not args.start or not args.end:
            # Default to last 2 years
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - pd.DateOffset(years=2)).strftime("%Y-%m-%d")
        else:
            start_date = args.start
            end_date = args.end

        # Run analysis
        from analyze import analyze
        df = fetch_all_data(start_date, end_date)
        if df.empty:
            print("Error: No data fetched")
            return

        result = analyze(df)
        result["params"] = {
            "start_date": start_date,
            "end_date": end_date,
            "smooth_window": 5,
            "zscore_window": 60,
            "lead_lag_max_days": 20,
            "shock_window_days": 5,
            "shock_threshold_bps": 15.0
        }

    if not start_date or not end_date:
        print("Error: Missing date range")
        return

    # Fetch data
    df = fetch_all_data(start_date, end_date)

    if df.empty:
        print("Error: No data fetched")
        return

    # Create chart
    create_bloomberg_chart(df, result, output_path, dpi=args.dpi)


if __name__ == "__main__":
    main()
