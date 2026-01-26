#!/usr/bin/env python3
"""
淨買賣流量視覺化圖表生成腳本

生成日本保險公司超長債淨買賣的歷史走勢圖。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 專案路徑設定
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = SKILL_DIR.parent.parent / "output"

# 確保目錄存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data(cache_file: Optional[Path] = None) -> pd.DataFrame:
    """載入數據"""
    if cache_file is None:
        cache_file = CACHE_DIR / "jsda_data.json"

    if not cache_file.exists():
        print(f"錯誤：找不到數據檔案 {cache_file}")
        print("請先執行 jsda_flow_analyzer.py 生成數據")
        return pd.DataFrame()

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    return df


def create_flow_chart(
    df: pd.DataFrame,
    title: str = "日本保險公司超長端 JGB 淨買賣走勢",
    output_path: Optional[Path] = None,
    style: str = "default"
) -> None:
    """
    生成淨買賣走勢圖

    Args:
        df: 包含 net_purchases_billion_jpy 的 DataFrame
        title: 圖表標題
        output_path: 輸出路徑
        style: 圖表風格 (default/bloomberg/minimal)
    """
    if df.empty:
        print("錯誤：數據為空")
        return

    # 設定風格
    if style == "bloomberg":
        plt.style.use('dark_background')
        bg_color = '#1a1a2e'
        text_color = '#ffffff'
        positive_color = '#00ff88'
        negative_color = '#ff4444'
    else:
        plt.style.use('seaborn-v0_8-whitegrid')
        bg_color = '#ffffff'
        text_color = '#333333'
        positive_color = '#2ecc71'
        negative_color = '#e74c3c'

    # 創建圖表
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    fig.patch.set_facecolor(bg_color)

    # 主圖：淨買賣柱狀圖
    ax1 = axes[0]
    ax1.set_facecolor(bg_color)

    values = df["net_purchases_billion_jpy"].values
    dates = df.index

    # 分開正負值
    colors = [positive_color if v >= 0 else negative_color for v in values]

    ax1.bar(dates, values, color=colors, width=25, alpha=0.8)
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

    # 標記極值
    min_idx = df["net_purchases_billion_jpy"].idxmin()
    max_idx = df["net_purchases_billion_jpy"].idxmax()
    min_val = df["net_purchases_billion_jpy"].min()
    max_val = df["net_purchases_billion_jpy"].max()

    ax1.scatter([min_idx], [min_val], color='red', s=100, zorder=5, marker='v')
    ax1.scatter([max_idx], [max_val], color='green', s=100, zorder=5, marker='^')

    ax1.annotate(
        f'歷史低點\n{min_val:.0f}億',
        xy=(min_idx, min_val),
        xytext=(min_idx, min_val - 150),
        ha='center',
        fontsize=9,
        color=text_color,
        arrowprops=dict(arrowstyle='->', color=text_color)
    )

    ax1.set_title(title, fontsize=16, fontweight='bold', color=text_color, pad=20)
    ax1.set_ylabel('淨買入（十億日圓）', fontsize=12, color=text_color)
    ax1.tick_params(colors=text_color)

    # 格式化 X 軸日期
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # 添加網格
    ax1.grid(True, alpha=0.3)

    # 副圖：累積走勢
    ax2 = axes[1]
    ax2.set_facecolor(bg_color)

    # 計算 12 個月滾動累積
    rolling_cum = df["net_purchases_billion_jpy"].rolling(window=12, min_periods=1).sum()
    ax2.fill_between(
        dates, rolling_cum, 0,
        where=rolling_cum >= 0,
        color=positive_color,
        alpha=0.5,
        label='淨買入'
    )
    ax2.fill_between(
        dates, rolling_cum, 0,
        where=rolling_cum < 0,
        color=negative_color,
        alpha=0.5,
        label='淨賣出'
    )
    ax2.plot(dates, rolling_cum, color='white' if style == 'bloomberg' else 'black', linewidth=1)

    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax2.set_ylabel('12M 滾動累積（十億日圓）', fontsize=10, color=text_color)
    ax2.set_xlabel('日期', fontsize=10, color=text_color)
    ax2.tick_params(colors=text_color)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=9)

    # 添加資料來源標註
    fig.text(
        0.99, 0.01,
        f'資料來源: JSDA | 生成日期: {datetime.now().strftime("%Y-%m-%d")}',
        ha='right',
        fontsize=8,
        color='gray'
    )

    # 添加統計摘要
    stats_text = f"""統計摘要
─────────
最新月份: {df.index[-1].strftime('%Y-%m')}
最新值: {values[-1]:.0f}億
歷史均值: {values.mean():.0f}億
標準差: {values.std():.0f}億"""

    fig.text(
        0.02, 0.98,
        stats_text,
        transform=fig.transFigure,
        fontsize=9,
        verticalalignment='top',
        fontfamily='monospace',
        color=text_color,
        bbox=dict(
            boxstyle='round',
            facecolor=bg_color,
            edgecolor='gray',
            alpha=0.8
        )
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.98)

    # 保存圖表
    if output_path is None:
        output_path = OUTPUT_DIR / f"jgb_insurer_flow_{datetime.now().strftime('%Y%m%d')}.png"

    plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"圖表已保存至: {output_path}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="生成日本保險公司超長債淨買賣走勢圖"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        help="數據檔案路徑（JSON）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="輸出目錄"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="default",
        choices=["default", "bloomberg", "minimal"],
        help="圖表風格"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "svg"],
        help="輸出格式"
    )

    args = parser.parse_args()

    # 載入數據
    cache_file = Path(args.data_file) if args.data_file else None
    df = load_data(cache_file)

    if df.empty:
        return

    # 設定輸出路徑
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"jgb_insurer_flow_{datetime.now().strftime('%Y%m%d')}.{args.format}"

    # 生成圖表
    create_flow_chart(
        df=df,
        output_path=output_path,
        style=args.style
    )


if __name__ == "__main__":
    main()
