#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本保險公司超長期 JGB 淨買賣流量視覺化

Bloomberg 風格圖表，顯示：
1. 月度流入/流出柱狀圖（正值綠色=流入/淨買入，負值紅色=流出/淨賣出）
2. 12 個月滾動累積線
3. 統計摘要面板
4. 創紀錄月份標註

符號慣例（視覺化用）：
- 正值（向上）= 流入 = 淨買入 = 需求增加
- 負值（向下）= 流出 = 淨賣出 = 需求減少

注意：JSDA 原始數據符號相反（正值=淨賣出），此腳本會反轉以符合直觀。

依據 thoughts/shared/guide/bloomberg-style-chart-guide.md 設計
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前設定

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# 專案路徑
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "output"

# 確保輸出目錄存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Bloomberg 風格配色（來自 bloomberg-style-chart-guide.md）
# ============================================================

COLORS = {
    "background": "#1a1a2e",      # 深藍黑色背景
    "grid": "#2d2d44",            # 暗灰紫網格線
    "text": "#ffffff",            # 主要文字（白色）
    "text_dim": "#888888",        # 次要文字（灰色）
    "primary": "#ff6b35",         # 橙紅色（主要指標）
    "secondary": "#ffaa00",       # 橙黃色（次要指標/均線）
    "tertiary": "#ffff00",        # 黃色（第三指標）
    "inflow": "#00ff88",          # 綠色（流入 = 淨買入 = 需求增加）
    "outflow": "#ff4444",         # 紅色（流出 = 淨賣出 = 需求減少）
    "area_fill": "#ff8c00",       # 橙色面積填充
    "area_alpha": 0.4,
    "level_line": "#666666",      # 關卡/水平線
    "annotation": "#ffffff",
    "record_marker": "#ff00ff",   # 品紅色（創紀錄標記）
}

# 中文字體設定
plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',  # Windows 正黑體
    'SimHei',              # Windows 黑體
    'Microsoft YaHei',     # Windows 微軟雅黑
    'PingFang TC',         # macOS 蘋方
    'Noto Sans CJK TC',    # Linux/通用
    'DejaVu Sans'          # 備用
]
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 數據載入
# ============================================================

def load_data_from_analyzer(start_year: int = 2018, refresh: bool = False) -> pd.DataFrame:
    """從 jsda_flow_analyzer 載入數據"""
    # 動態 import
    sys.path.insert(0, str(SCRIPT_DIR))
    from jsda_flow_analyzer import fetch_jsda_data
    return fetch_jsda_data(start_year=start_year, refresh=refresh)


# ============================================================
# 格式化函數
# ============================================================

def format_billion(x, pos):
    """億日圓格式化"""
    if abs(x) >= 10000:
        return f'{x/10000:.1f}兆'
    elif abs(x) >= 1000:
        return f'{x/1000:.1f}K'
    return f'{x:,.0f}'


# ============================================================
# 圖表繪製
# ============================================================

def generate_flow_chart(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "日本保險公司超長期 JGB 淨買賣流量",
    start_date: str | None = None,
    show_rolling: bool = True,
    show_stats: bool = True,
    show_record: bool = True
) -> None:
    """
    生成 Bloomberg 風格的淨買賣流量圖表

    Parameters
    ----------
    df : pd.DataFrame
        包含 net_sale_100m_yen 欄位的 DataFrame（index 為日期）
    output_path : Path
        輸出路徑
    title : str
        圖表標題
    show_rolling : bool
        是否顯示 12M 滾動累積線
    show_stats : bool
        是否顯示統計摘要面板
    show_record : bool
        是否標記創紀錄月份
    """
    plt.style.use('dark_background')

    # 過濾起始日期
    if start_date:
        df = df[df.index >= start_date]

    # 數據準備
    # JSDA 原始：正值 = 淨賣出（流出），負值 = 淨買入（流入）
    # 視覺化：反轉符號，正值向上 = 流入，負值向下 = 流出
    raw_series = df['net_sale_100m_yen']
    series = -raw_series  # 反轉符號
    dates = series.index
    values = series.values

    # 計算 12M 滾動累積（已反轉，負值累積 = 累積流出）
    rolling_12m = series.rolling(window=12).sum()

    # 找出創紀錄流出月份（反轉後的最小值 = 原始最大淨賣出）
    record_outflow_idx = series.idxmin()
    record_outflow_value = series.min()  # 負值 = 流出
    # 同時記錄原始值用於顯示
    record_outflow_raw = -record_outflow_value  # 轉回正值顯示

    # 計算統計
    latest_date = dates[-1]
    latest_value = values[-1]
    latest_raw = -latest_value  # 原始值（正 = 淨賣出）

    # 連續流出月數（反轉後 < 0 = 流出）
    streak = 0
    for v in reversed(values):
        if v < 0:  # 負值 = 流出
            streak += 1
        else:
            break

    # 本輪累積流出（反轉後為負值）
    cumulative = series.tail(streak).sum() if streak > 0 else 0
    cumulative_raw = -cumulative  # 轉回正值顯示

    # Z-score（基於原始數據計算）
    mean_val = raw_series.mean()
    std_val = raw_series.std()
    zscore = (latest_raw - mean_val) / std_val if std_val > 0 else 0

    # ============================================================
    # 建立圖表
    # ============================================================

    fig, ax1 = plt.subplots(figsize=(14, 8), facecolor=COLORS["background"])
    ax1.set_facecolor(COLORS["background"])

    # ============================================================
    # 主圖：流入/流出柱狀圖（正值向上=流入，負值向下=流出）
    # ============================================================

    # 分離正負值
    positive_mask = values > 0
    negative_mask = values <= 0

    # 繪製柱狀圖
    bar_width = 20  # 天數

    # 流入（正值）- 綠色（向上）
    ax1.bar(
        dates[positive_mask],
        values[positive_mask],
        width=bar_width,
        color=COLORS["inflow"],
        alpha=0.8,
        label='流入（淨買入）',
        zorder=3
    )

    # 流出（負值）- 紅色（向下）
    ax1.bar(
        dates[negative_mask],
        values[negative_mask],
        width=bar_width,
        color=COLORS["outflow"],
        alpha=0.8,
        label='流出（淨賣出）',
        zorder=3
    )

    # 零線
    ax1.axhline(y=0, color=COLORS["level_line"], linewidth=1.5, zorder=2)

    # Y 軸設定
    ax1.set_ylabel("資金流向（億日圓）", color=COLORS["text"], fontsize=11)
    ax1.yaxis.set_major_formatter(FuncFormatter(format_billion))
    ax1.tick_params(axis='y', colors=COLORS["text"], labelsize=9)

    # ============================================================
    # 疊加：12M 滾動累積線
    # ============================================================

    if show_rolling:
        ax2 = ax1.twinx()

        ax2.plot(
            rolling_12m.index,
            rolling_12m.values,
            color=COLORS["secondary"],
            linewidth=2.5,
            linestyle='--',
            label='12M 滾動累積',
            zorder=4
        )

        # 標註最新滾動值
        latest_rolling = rolling_12m.iloc[-1]
        ax2.annotate(
            f'{latest_rolling:,.0f}',
            xy=(dates[-1], latest_rolling),
            xytext=(15, 0),
            textcoords='offset points',
            color=COLORS["secondary"],
            fontsize=10,
            fontweight='bold',
            va='center',
            zorder=5
        )

        ax2.set_ylabel("12M 滾動累積（億日圓）", color=COLORS["secondary"], fontsize=11)
        ax2.yaxis.set_major_formatter(FuncFormatter(format_billion))
        ax2.tick_params(axis='y', colors=COLORS["secondary"], labelsize=9)
        ax2.spines['right'].set_color(COLORS["secondary"])

    # ============================================================
    # 標記創紀錄流出月份
    # ============================================================

    if show_record and record_outflow_value < 0:  # 負值 = 流出
        ax1.annotate(
            f'創紀錄流出\n{record_outflow_raw:,.0f}億',
            xy=(record_outflow_idx, record_outflow_value),
            xytext=(0, -35),
            textcoords='offset points',
            color=COLORS["record_marker"],
            fontsize=10,
            fontweight='bold',
            ha='center',
            va='top',
            arrowprops=dict(
                arrowstyle='->',
                color=COLORS["record_marker"],
                lw=2
            ),
            zorder=6
        )

    # ============================================================
    # 最新值標註
    # ============================================================

    latest_color = COLORS["inflow"] if latest_value > 0 else COLORS["outflow"]
    ax1.annotate(
        f'{latest_value:,.0f}',
        xy=(latest_date, latest_value),
        xytext=(15, 0),
        textcoords='offset points',
        color=latest_color,
        fontsize=11,
        fontweight='bold',
        va='center',
        zorder=5
    )

    # ============================================================
    # 網格設定
    # ============================================================

    ax1.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5, zorder=1)
    ax1.set_axisbelow(True)

    # ============================================================
    # X 軸設定
    # ============================================================

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax1.tick_params(axis='x', colors=COLORS["text_dim"], labelsize=9)

    # ============================================================
    # 統計摘要面板
    # ============================================================

    if show_stats:
        direction = "流入" if latest_value > 0 else "流出"
        stats_text = (
            f"━━━ 摘要 ━━━\n"
            f"最新月份: {latest_date.strftime('%Y/%m')}\n"
            f"{direction}: {abs(latest_raw):,.0f} 億日圓\n"
            f"連續流出: {streak} 個月\n"
            f"本輪累積: {cumulative_raw:,.0f} 億日圓\n"
            f"Z-score: {zscore:.2f}\n"
            f"━━━━━━━━━━━\n"
            f"創紀錄流出: {record_outflow_idx.strftime('%Y/%m')}\n"
            f"            {record_outflow_raw:,.0f} 億"
        )

        props = dict(
            boxstyle='round,pad=0.6',
            facecolor=COLORS["background"],
            edgecolor=COLORS["grid"],
            alpha=0.95
        )

        ax1.text(
            0.02, 0.98,
            stats_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment='top',
            color=COLORS["text"],
            bbox=props,
            zorder=7
        )

    # ============================================================
    # 圖例
    # ============================================================

    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, fc=COLORS["inflow"], alpha=0.8, label='流入（需求↑）'),
        plt.Rectangle((0, 0), 1, 1, fc=COLORS["outflow"], alpha=0.8, label='流出（需求↓）'),
    ]

    if show_rolling:
        legend_elements.append(
            plt.Line2D([0], [0], color=COLORS["secondary"], linewidth=2.5, linestyle='--', label='12M 滾動累積 (R1)')
        )

    ax1.legend(
        handles=legend_elements,
        loc='upper right',
        fontsize=9,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"]
    )

    # ============================================================
    # 標題
    # ============================================================

    fig.suptitle(
        title,
        color=COLORS["text"],
        fontsize=14,
        fontweight='bold',
        y=0.98
    )

    # ============================================================
    # 頁尾
    # ============================================================

    fig.text(
        0.02, 0.02,
        "資料來源: JSDA",
        color=COLORS["text_dim"],
        fontsize=8,
        ha='left'
    )

    fig.text(
        0.98, 0.02,
        f"截至: {latest_date.strftime('%Y-%m-%d')}  |  投資人: 生保・損保  |  天期: 超長期(10Y+)",
        color=COLORS["text_dim"],
        fontsize=8,
        ha='right'
    )

    # ============================================================
    # 佈局與輸出
    # ============================================================

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches='tight',
        facecolor=COLORS["background"]
    )
    plt.close()

    print(f"圖表已儲存: {output_path}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="生成日本保險公司超長期 JGB 淨買賣流量圖表（Bloomberg 風格）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="輸出目錄"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="輸出檔名（預設：jgb-insurer-superlong-flow-YYYYMMDD.png）"
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="起始日期（如 2022-01）"
    )
    parser.add_argument(
        "--no-rolling",
        action="store_true",
        help="不顯示 12M 滾動累積線"
    )
    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="不顯示統計摘要面板"
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="不標記創紀錄月份"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="強制重新下載數據"
    )

    args = parser.parse_args()

    # 載入數據
    print("載入數據中...", file=sys.stderr)
    df = load_data_from_analyzer(start_year=2018, refresh=args.refresh)

    if df.empty:
        print("錯誤：無法取得數據", file=sys.stderr)
        sys.exit(1)

    # 生成輸出路徑
    today = datetime.now().strftime("%Y%m%d")
    if args.filename:
        filename = args.filename
    else:
        filename = f"jgb-insurer-superlong-flow-{today}.png"

    output_path = Path(args.output_dir) / filename

    # 生成圖表
    generate_flow_chart(
        df=df,
        output_path=output_path,
        title="日本保險公司超長期 JGB 淨買賣流量",
        start_date=args.start,
        show_rolling=not args.no_rolling,
        show_stats=not args.no_stats,
        show_record=not args.no_record
    )


if __name__ == "__main__":
    main()
