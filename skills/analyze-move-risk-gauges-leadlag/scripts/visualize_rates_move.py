#!/usr/bin/env python3
"""
visualize_rates_move.py - 利率 vs MOVE 恐慌關係專題圖表

通用的利率波動率恐慌分析圖表，可帶入任何國家/地區的債券殖利率。
專注於回答：「MOVE 是否對 [指定債券] 殖利率變動感到恐慌？」

遵循 Bloomberg Intelligence 風格指南。

Usage:
    # 分析 JGB 10Y vs MOVE
    python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31 --rates-col JGB10Y --rates-name "JGB 10Y"

    # 分析 UST 10Y vs MOVE（如果數據中有）
    python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31 --rates-col UST10Y --rates-name "UST 10Y"

    # 分析 Bund 10Y vs MOVE
    python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31 --rates-col BUND10Y --rates-name "Bund 10Y"
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

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
    "panel_bg": "#16213e",
    "grid": "#2d2d44",

    # 文字
    "text": "#ffffff",
    "text_dim": "#888888",
    "text_highlight": "#ffcc00",

    # 主要數據線
    "move": "#ff6b35",          # 橙紅色（MOVE）
    "rates": "#00ff88",         # 綠色（利率）
    "rates_dim": "#00aa55",     # 暗綠色

    # 判定顏色
    "spooked": "#ff4444",       # 紅色（恐慌）
    "not_spooked": "#00ff88",   # 綠色（未恐慌）

    # 輔助元素
    "shock_marker": "#ffff00",  # 黃色（衝擊標記）
    "regression": "#ffaa00",    # 橙黃色（回歸線）
    "zero_line": "#555555",
    "threshold": "#666666",
}


# =============================================================================
# 視覺化函數
# =============================================================================

def create_rates_move_chart(
    df: pd.DataFrame,
    result: dict,
    output_path: str,
    rates_col: str = "JGB10Y",
    rates_name: str = "JGB 10Y",
    dpi: int = 150
):
    """
    生成利率 vs MOVE 恐慌關係專題圖表

    Parameters:
    -----------
    df : pd.DataFrame
        原始數據（需包含 MOVE 和指定的利率欄位）
    result : dict
        分析結果
    output_path : str
        輸出路徑
    rates_col : str
        利率數據欄位名稱（如 "JGB10Y", "UST10Y", "BUND10Y"）
    rates_name : str
        利率顯示名稱（如 "JGB 10Y", "UST 10Y", "Bund 10Y"）
    dpi : int
        解析度

    佈局（3 行）:
    ┌─────────────────────────────────────────────────┐
    │     [利率名稱] vs MOVE 時序圖（利率軸翻轉）       │
    │                    (Row 1)                       │
    ├─────────────────────────────────────────────────┤
    │           Z 分數時間序列（利率 + MOVE）          │
    │                    (Row 2)                       │
    ├───────────────────────┬─────────────────────────┤
    │   利率變化 vs MOVE    │     恐慌判定儀表板       │
    │   變化散點圖 (左下)    │        (右下)           │
    │                    (Row 3)                       │
    └───────────────────────┴─────────────────────────┘
    """
    plt.style.use('dark_background')

    # 檢查數據欄位
    if rates_col not in df.columns:
        raise ValueError(f"Column '{rates_col}' not found in DataFrame. Available: {list(df.columns)}")
    if "MOVE" not in df.columns:
        raise ValueError("Column 'MOVE' not found in DataFrame")

    # 獲取參數
    params = result.get("params", {})
    smooth_window = params.get("smooth_window", 5)
    zscore_window = params.get("zscore_window", 60)
    shock_window_days = params.get("shock_window_days", 5)
    shock_threshold_bps = params.get("shock_threshold_bps", 15.0)

    # 準備數據
    df = df.sort_index()
    df_smooth = df.rolling(smooth_window).mean() if smooth_window > 0 else df.copy()

    # 計算 Z 分數
    df_z = df_smooth.apply(lambda c: rolling_zscore(c, zscore_window))

    # 將利率 Z 分數反轉（與上方圖表軸翻轉一致）
    # 這樣當利率上升（Z 為正）→ 翻轉後為負，與 MOVE 下降（風險緩和）同向
    df_z[rates_col] = -df_z[rates_col]

    # 識別衝擊事件
    shock = identify_shock_events(df_smooth[rates_col], shock_window_days, shock_threshold_bps)
    shock_dates = df_smooth.index[shock]

    # 計算變化
    rates_change = (df_smooth[rates_col] - df_smooth[rates_col].shift(shock_window_days)) * 100  # bps
    move_change = df_smooth["MOVE"] - df_smooth["MOVE"].shift(shock_window_days)

    # 創建圖表 - 3 行佈局
    fig = plt.figure(figsize=(16, 14), facecolor=COLORS["background"])

    # GridSpec: 3 行佈局
    # Row 1: 走勢圖（跨兩格）
    # Row 2: Z 分數（跨兩格）
    # Row 3: 散點圖（左）+ 儀表板（右）
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 0.8, 1],
                          hspace=0.28, wspace=0.15,
                          left=0.08, right=0.92, top=0.92, bottom=0.06)

    # =========================================================================
    # Panel 1: 利率 vs MOVE 時間序列（上方跨兩格）
    # 利率軸翻轉（inverted）：利率下降在上、上升在下，方便與 MOVE 走勢比較
    # =========================================================================
    ax_ts = fig.add_subplot(gs[0, :])
    ax_ts.set_facecolor(COLORS["background"])

    # 利率（左軸）- 繪製後翻轉 Y 軸
    line_rates, = ax_ts.plot(df.index, df[rates_col], label=f"{rates_name} 殖利率",
                             color=COLORS["rates"], linewidth=2, zorder=4)
    ax_ts.set_ylabel(f"{rates_name} 殖利率 (%, 軸翻轉)", color=COLORS["rates"], fontsize=11)
    ax_ts.tick_params(axis="y", labelcolor=COLORS["rates"], labelsize=9)

    # 翻轉利率 Y 軸：高值在下、低值在上
    ax_ts.invert_yaxis()

    # MOVE（右軸）- 正常方向
    ax_ts_r = ax_ts.twinx()
    line_move, = ax_ts_r.plot(df.index, df["MOVE"], label="MOVE Index",
                              color=COLORS["move"], linewidth=2.5, zorder=5)
    ax_ts_r.set_ylabel("MOVE Index", color=COLORS["move"], fontsize=11)
    ax_ts_r.tick_params(axis="y", labelcolor=COLORS["move"], labelsize=9)

    # 標記衝擊事件
    for i, shock_date in enumerate(shock_dates):
        ax_ts.axvline(shock_date, color=COLORS["shock_marker"],
                      linestyle="--", alpha=0.6, linewidth=1.5, zorder=2)
        # 只標記前幾個避免過於擁擠
        if i < 5:
            ax_ts.annotate("衝擊", xy=(shock_date, df[rates_col].loc[shock_date]),
                           xytext=(0, -15), textcoords='offset points',
                           fontsize=7, color=COLORS["shock_marker"],
                           ha='center', alpha=0.8)

    # 網格與格式
    ax_ts.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_ts.set_axisbelow(True)
    ax_ts.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax_ts.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_ts.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0, labelsize=9)

    ax_ts.set_title(f"{rates_name} 殖利率（軸翻轉）vs MOVE Index 走勢對比", color=COLORS["text"],
                    fontsize=13, fontweight="bold", pad=12)

    # 圖例 - 加入說明
    lines = [line_rates, line_move]
    labels = [f"{rates_name} 殖利率 (軸翻轉)", "MOVE Index"]
    ax_ts.legend(lines, labels, loc="upper left", fontsize=9,
                 facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                 labelcolor=COLORS["text"])

    # 最新值標註
    latest_rates = df[rates_col].iloc[-1]
    latest_move = df["MOVE"].iloc[-1]
    ax_ts.annotate(f'{latest_rates:.2f}%',
                   xy=(df.index[-1], latest_rates),
                   xytext=(8, 0), textcoords='offset points',
                   color=COLORS["rates"], fontsize=10, fontweight='bold', va='center')
    ax_ts_r.annotate(f'{latest_move:.1f}',
                     xy=(df.index[-1], latest_move),
                     xytext=(8, 0), textcoords='offset points',
                     color=COLORS["move"], fontsize=10, fontweight='bold', va='center')

    # =========================================================================
    # Panel 2: Z 分數時間序列（中間跨兩格）
    # 與 Panel 1 共享 X 軸，確保時間範圍對齊
    # =========================================================================
    ax_z = fig.add_subplot(gs[1, :], sharex=ax_ts)
    ax_z.set_facecolor(COLORS["background"])

    # 繪製利率和 MOVE 的 Z 分數（利率 Z 已翻轉，與上方軸翻轉一致）
    ax_z.plot(df_z.index, df_z[rates_col], label=f"{rates_name} Z (inverted)",
              color=COLORS["rates"], linewidth=1.8, zorder=4)
    ax_z.plot(df_z.index, df_z["MOVE"], label="MOVE Z",
              color=COLORS["move"], linewidth=1.8, zorder=5)

    # 參考線
    ax_z.axhline(0, color=COLORS["zero_line"], linestyle="-", alpha=0.6, linewidth=1)
    ax_z.axhline(1, color=COLORS["threshold"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(-1, color=COLORS["threshold"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(2, color=COLORS["spooked"], linestyle="--", alpha=0.4, linewidth=0.8)
    ax_z.axhline(-2, color=COLORS["spooked"], linestyle="--", alpha=0.4, linewidth=0.8)

    # 標記當前 MOVE Z 分數
    move_z_now = result.get("spooked_check", {}).get("MOVE_zscore_now")
    if move_z_now is not None:
        ax_z.scatter([df_z.index[-1]], [move_z_now], color=COLORS["move"],
                     s=80, zorder=6, edgecolor=COLORS["text"], linewidth=2)
        ax_z.annotate(f'MOVE: {move_z_now:+.2f}',
                      xy=(df_z.index[-1], move_z_now),
                      xytext=(10, 5), textcoords='offset points',
                      color=COLORS["move"], fontsize=9, fontweight='bold')

    # 標記當前利率 Z 分數（已翻轉）
    rates_z_now = df_z[rates_col].iloc[-1]
    if not np.isnan(rates_z_now):
        ax_z.scatter([df_z.index[-1]], [rates_z_now], color=COLORS["rates"],
                     s=80, zorder=6, edgecolor=COLORS["text"], linewidth=2)
        ax_z.annotate(f'{rates_name} (inv): {rates_z_now:+.2f}',
                      xy=(df_z.index[-1], rates_z_now),
                      xytext=(10, -10), textcoords='offset points',
                      color=COLORS["rates"], fontsize=9, fontweight='bold')

    ax_z.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_z.set_axisbelow(True)
    ax_z.set_ylabel("Z-Score", color=COLORS["text"], fontsize=10)
    ax_z.set_ylim(-4, 4)
    ax_z.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax_z.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_z.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0, labelsize=8)
    ax_z.tick_params(axis='y', colors=COLORS["text_dim"], labelsize=8)

    ax_z.set_title(f"標準化序列（Z 分數）- {rates_name} vs MOVE", color=COLORS["text"],
                   fontsize=11, fontweight="bold", pad=8)
    ax_z.legend(loc="upper left", fontsize=8,
                facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                labelcolor=COLORS["text"])

    # =========================================================================
    # Panel 3: 利率變化 vs MOVE 變化散點圖（左下）
    # =========================================================================
    ax_scatter = fig.add_subplot(gs[2, 0])
    ax_scatter.set_facecolor(COLORS["background"])

    # 只取衝擊事件的數據點
    shock_rates = rates_change[shock].dropna()
    shock_move = move_change[shock].dropna()

    # 確保索引對齊
    common_idx = shock_rates.index.intersection(shock_move.index)
    shock_rates = shock_rates.loc[common_idx]
    shock_move = shock_move.loc[common_idx]

    if len(shock_rates) > 0:
        # 散點圖
        ax_scatter.scatter(shock_rates, shock_move,
                          c=COLORS["shock_marker"], s=80, alpha=0.8,
                          edgecolor=COLORS["text"], linewidth=1, zorder=5)

        # 回歸線
        if len(shock_rates) > 2:
            z = np.polyfit(shock_rates, shock_move, 1)
            p = np.poly1d(z)
            x_line = np.linspace(shock_rates.min(), shock_rates.max(), 100)
            ax_scatter.plot(x_line, p(x_line), color=COLORS["regression"],
                           linewidth=2, linestyle="--", label=f"回歸線 (斜率={z[0]:.2f})", zorder=4)

            # 相關係數
            corr = shock_rates.corr(shock_move)
            ax_scatter.text(0.95, 0.05, f"r = {corr:.2f}",
                           transform=ax_scatter.transAxes,
                           fontsize=10, color=COLORS["text_highlight"],
                           ha="right", va="bottom", fontweight="bold")

        ax_scatter.legend(loc="upper left", fontsize=8,
                         facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                         labelcolor=COLORS["text"])

    # 參考線
    ax_scatter.axhline(0, color=COLORS["zero_line"], linestyle="-", alpha=0.5, linewidth=1)
    ax_scatter.axvline(0, color=COLORS["zero_line"], linestyle="-", alpha=0.5, linewidth=1)

    # 標註區域
    ax_scatter.text(0.02, 0.98, f"{rates_name}+ MOVE+\n(同向恐慌)", transform=ax_scatter.transAxes,
                   fontsize=8, color=COLORS["spooked"], ha="left", va="top", alpha=0.7)
    ax_scatter.text(0.98, 0.02, f"{rates_name}- MOVE-\n(同向緩和)", transform=ax_scatter.transAxes,
                   fontsize=8, color=COLORS["not_spooked"], ha="right", va="bottom", alpha=0.7)

    ax_scatter.set_xlabel(f"{rates_name} 變化 (bps)", color=COLORS["text_dim"], fontsize=10)
    ax_scatter.set_ylabel("MOVE 變化", color=COLORS["text_dim"], fontsize=10)
    ax_scatter.grid(True, color=COLORS["grid"], alpha=0.3, linestyle="-", linewidth=0.5)
    ax_scatter.set_axisbelow(True)
    ax_scatter.tick_params(axis='both', colors=COLORS["text_dim"], labelsize=9)
    ax_scatter.set_title(f"衝擊事件：{rates_name} 變化 vs MOVE 反應", color=COLORS["text"],
                        fontsize=11, fontweight="bold", pad=10)

    # =========================================================================
    # Panel 4: 恐慌判定儀表板（右下）
    # =========================================================================
    ax_gauge = fig.add_subplot(gs[2, 1])
    ax_gauge.set_facecolor(COLORS["panel_bg"])
    ax_gauge.set_xlim(0, 10)
    ax_gauge.set_ylim(0, 10)
    ax_gauge.axis('off')

    # 獲取分析結果
    spooked_check = result.get("spooked_check", {})
    verdict = spooked_check.get("spooked_verdict", "UNKNOWN")
    shock_count = spooked_check.get("shock_count", 0)
    mean_reaction = spooked_check.get("mean_MOVE_reaction_on_shocks")
    move_z_now = spooked_check.get("MOVE_zscore_now")

    # 判定顏色
    verdict_color = COLORS["spooked"] if verdict == "SPOOKED" else COLORS["not_spooked"]
    verdict_text = "恐慌" if verdict == "SPOOKED" else "未恐慌"
    verdict_emoji = "!" if verdict == "SPOOKED" else "OK"

    # 標題
    ax_gauge.text(5, 9.2, f"MOVE 對 {rates_name} 衝擊的反應判定", fontsize=12, fontweight="bold",
                 color=COLORS["text"], ha="center", va="top")

    # 主要判定結果（大字）
    ax_gauge.add_patch(FancyBboxPatch((1.5, 5.5), 7, 2.8,
                                       boxstyle="round,pad=0.1,rounding_size=0.3",
                                       facecolor=COLORS["background"],
                                       edgecolor=verdict_color, linewidth=3))
    ax_gauge.text(5, 7.2, verdict_emoji, fontsize=28, color=verdict_color,
                 ha="center", va="center", fontweight="bold")
    ax_gauge.text(5, 6.0, verdict_text.upper(), fontsize=20, color=verdict_color,
                 ha="center", va="center", fontweight="bold")

    # 統計數據
    stats_y = 4.5
    ax_gauge.text(1, stats_y, "衝擊事件數：", fontsize=10, color=COLORS["text_dim"],
                 ha="left", va="center")
    ax_gauge.text(9, stats_y, f"{shock_count} 次", fontsize=10, color=COLORS["text_highlight"],
                 ha="right", va="center", fontweight="bold")

    stats_y -= 0.8
    ax_gauge.text(1, stats_y, "MOVE 平均反應：", fontsize=10, color=COLORS["text_dim"],
                 ha="left", va="center")
    if mean_reaction is not None:
        reaction_color = COLORS["spooked"] if mean_reaction > 5 else COLORS["not_spooked"]
        ax_gauge.text(9, stats_y, f"{mean_reaction:+.1f}", fontsize=10, color=reaction_color,
                     ha="right", va="center", fontweight="bold")
    else:
        ax_gauge.text(9, stats_y, "N/A", fontsize=10, color=COLORS["text_dim"],
                     ha="right", va="center")

    stats_y -= 0.8
    ax_gauge.text(1, stats_y, "MOVE 當前 Z 分數：", fontsize=10, color=COLORS["text_dim"],
                 ha="left", va="center")
    if move_z_now is not None:
        z_color = COLORS["spooked"] if move_z_now > 1 else (COLORS["not_spooked"] if move_z_now < -1 else COLORS["text"])
        ax_gauge.text(9, stats_y, f"{move_z_now:+.2f}", fontsize=10, color=z_color,
                     ha="right", va="center", fontweight="bold")
    else:
        ax_gauge.text(9, stats_y, "N/A", fontsize=10, color=COLORS["text_dim"],
                     ha="right", va="center")

    stats_y -= 0.8
    ax_gauge.text(1, stats_y, "衝擊定義：", fontsize=10, color=COLORS["text_dim"],
                 ha="left", va="center")
    ax_gauge.text(9, stats_y, f"|d{rates_name}| >= {shock_threshold_bps:.0f}bp / {shock_window_days}d",
                 fontsize=9, color=COLORS["text"], ha="right", va="center")

    # 解讀說明
    if verdict == "SPOOKED":
        interpretation = f"MOVE 對 {rates_name} 殖利率衝擊有明顯反應，\n顯示利率波動率市場對該利率變化敏感"
    else:
        interpretation = f"MOVE 對 {rates_name} 殖利率衝擊反應平淡，\n顯示利率波動率市場未被該利率變化驚擾"

    ax_gauge.text(5, 1.0, interpretation, fontsize=9, color=COLORS["text_dim"],
                 ha="center", va="center", style="italic",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["background"],
                          edgecolor=COLORS["grid"], alpha=0.8))

    # =========================================================================
    # 主標題
    # =========================================================================
    fig.suptitle(f"MOVE 對 {rates_name} 殖利率衝擊的恐慌程度分析",
                 color=COLORS["text"], fontsize=15, fontweight="bold", y=0.96)

    # =========================================================================
    # 頁尾
    # =========================================================================
    as_of = result.get("as_of", datetime.now().strftime("%Y-%m-%d"))
    fig.text(0.92, 0.02, f'截至: {as_of}',
             color=COLORS["text_dim"], fontsize=8, ha='right')

    # 結論
    headline = result.get("headline", "")
    if headline:
        # 只取恐慌相關部分
        spooked_part = headline.split(" and ")[0] if " and " in headline else headline
        fig.text(0.50, 0.02, spooked_part,
                 color=COLORS["text_highlight"], fontsize=10, fontweight="bold",
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
    parser = argparse.ArgumentParser(
        description="Visualize rates vs MOVE panic relationship (Bloomberg style)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze JGB 10Y vs MOVE (default)
  python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31

  # Analyze with custom rates column
  python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31 --rates-col UST10Y --rates-name "UST 10Y"

  # Analyze German Bund
  python visualize_rates_move.py --start 2024-01-01 --end 2026-01-31 --rates-col BUND10Y --rates-name "Bund 10Y"
        """
    )
    parser.add_argument("-i", "--input", help="Input JSON result file")
    parser.add_argument("-o", "--output", help="Output image path")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--rates-col", default="JGB10Y",
                        help="Column name for rates data (default: JGB10Y)")
    parser.add_argument("--rates-name", default="JGB 10Y",
                        help="Display name for rates (default: JGB 10Y)")
    parser.add_argument("--dpi", type=int, default=150, help="Resolution (DPI)")

    args = parser.parse_args()

    # Generate safe filename from rates name
    safe_rates_name = args.rates_name.lower().replace(" ", "-").replace("/", "-")

    # Determine output path
    today = datetime.now().strftime("%Y-%m-%d")
    if args.output:
        output_path = args.output
    else:
        # 使用專案根目錄的 output/
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        output_path = project_root / "output" / f"{safe_rates_name}-move-panic-{today}.png"

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
    create_rates_move_chart(
        df, result, str(output_path),
        rates_col=args.rates_col,
        rates_name=args.rates_name,
        dpi=args.dpi
    )


if __name__ == "__main__":
    main()
