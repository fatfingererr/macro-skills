#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
銅庫存回補訊號視覺化

生成 Bloomberg 風格的銅庫存回補訊號分析圖表。

Usage:
    python visualize_inventory_signal.py
    python visualize_inventory_signal.py --output path/to/output.png
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
except ImportError:
    print("[Error] 需要 matplotlib 套件: pip install matplotlib")
    exit(1)

from inventory_signal_analyzer import CopperInventorySignalAnalyzer


# ========== Bloomberg 風格配色 ==========
COLORS = {
    'background': '#1a1a2e',
    'grid': '#2a2a4e',
    'text': '#e0e0e0',
    'text_dim': '#888888',
    'copper_price': '#ffa500',
    'inventory': '#00bfff',
    'caution': '#ff4444',
    'supportive': '#00ff88',
    'neutral': '#888888',
    'z_positive': '#ff6b6b',
    'z_negative': '#4ecdc4',
}


def setup_bloomberg_style():
    """設定 Bloomberg 風格"""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': COLORS['background'],
        'axes.facecolor': COLORS['background'],
        'axes.edgecolor': COLORS['grid'],
        'axes.labelcolor': COLORS['text'],
        'axes.grid': True,
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.3,
        'text.color': COLORS['text'],
        'xtick.color': COLORS['text_dim'],
        'ytick.color': COLORS['text_dim'],
        'legend.facecolor': COLORS['background'],
        'legend.edgecolor': COLORS['grid'],
        'font.family': 'sans-serif',
        'font.size': 10,
    })


def create_signal_chart(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    title: str = "銅庫存回補訊號分析"
) -> None:
    """
    創建銅庫存回補訊號分析圖表

    Parameters
    ----------
    df : pd.DataFrame
        包含 date, inventory_tonnes, close, rebuild_z, near_term_signal 等欄位
    output_path : str, optional
        輸出路徑
    title : str
        圖表標題
    """
    setup_bloomberg_style()

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [2, 1, 0.5]})
    fig.suptitle(title, fontsize=16, fontweight='bold', color=COLORS['text'], y=0.98)

    # ========== 圖 1: 銅價 + SHFE 庫存對照 ==========
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    # 銅價
    ax1.plot(df['date'], df['close'], color=COLORS['copper_price'],
             linewidth=1.5, label='銅價 (USD/lb)', alpha=0.9)

    # SHFE 庫存
    ax1_twin.fill_between(df['date'], df['inventory_tonnes'] / 1000, 0,
                          color=COLORS['inventory'], alpha=0.3, label='SHFE 庫存')
    ax1_twin.plot(df['date'], df['inventory_tonnes'] / 1000,
                  color=COLORS['inventory'], linewidth=1, alpha=0.7)

    # 標記訊號觸發點
    caution_df = df[df['near_term_signal'] == 'CAUTION']
    if len(caution_df) > 0:
        ax1.scatter(caution_df['date'], caution_df['close'],
                    color=COLORS['caution'], s=50, marker='v', label='CAUTION 訊號', zorder=5)

    ax1.set_ylabel('銅價 (USD/lb)', color=COLORS['copper_price'])
    ax1_twin.set_ylabel('SHFE 庫存 (千噸)', color=COLORS['inventory'])
    ax1.legend(loc='upper left', fontsize=9)
    ax1_twin.legend(loc='upper right', fontsize=9)
    ax1.set_title('銅價 vs SHFE 庫存', fontsize=12, color=COLORS['text'], pad=10)

    # ========== 圖 2: 回補速度 z-score ==========
    ax2 = axes[1]

    # z-score 時序
    z_positive = df['rebuild_z'].clip(lower=0)
    z_negative = df['rebuild_z'].clip(upper=0)

    ax2.fill_between(df['date'], z_positive, 0, color=COLORS['z_positive'], alpha=0.5, label='回補')
    ax2.fill_between(df['date'], z_negative, 0, color=COLORS['z_negative'], alpha=0.5, label='去庫存')
    ax2.plot(df['date'], df['rebuild_z'], color=COLORS['text'], linewidth=0.8)

    # 門檻線
    ax2.axhline(y=1.5, color=COLORS['caution'], linestyle='--', linewidth=1, alpha=0.7, label='z = 1.5')
    ax2.axhline(y=-1.5, color=COLORS['supportive'], linestyle='--', linewidth=1, alpha=0.7, label='z = -1.5')
    ax2.axhline(y=0, color=COLORS['text_dim'], linestyle='-', linewidth=0.5, alpha=0.5)

    ax2.set_ylabel('4週回補速度 z-score')
    ax2.set_ylim(-4, 4)
    ax2.legend(loc='upper left', fontsize=9, ncol=4)
    ax2.set_title('回補速度標準化分數', fontsize=12, color=COLORS['text'], pad=10)

    # ========== 圖 3: 庫存水位分位數熱力條 ==========
    ax3 = axes[2]

    # 取最近 100 週的數據
    recent_df = df.tail(100).copy()

    # 創建漸層色彩
    percentiles = recent_df['inventory_percentile'].values
    dates = recent_df['date'].values

    for i in range(len(dates) - 1):
        pct = percentiles[i]
        if pd.isna(pct):
            color = COLORS['neutral']
        elif pct >= 0.85:
            color = COLORS['caution']
        elif pct <= 0.35:
            color = COLORS['supportive']
        else:
            # 漸層色
            if pct > 0.5:
                # 偏紅
                intensity = (pct - 0.5) / 0.5
                color = plt.cm.RdYlGn_r(0.3 + intensity * 0.4)
            else:
                # 偏綠
                intensity = (0.5 - pct) / 0.5
                color = plt.cm.RdYlGn(0.3 + intensity * 0.4)

        ax3.axvspan(dates[i], dates[i + 1], color=color, alpha=0.8)

    ax3.set_xlim(dates[0], dates[-1])
    ax3.set_ylim(0, 1)
    ax3.set_yticks([])
    ax3.set_title('庫存水位分位數（過去 100 週）', fontsize=12, color=COLORS['text'], pad=10)

    # 添加色標說明
    ax3.text(0.02, 0.5, '低 ← 庫存水位 → 高', transform=ax3.transAxes,
             fontsize=9, color=COLORS['text_dim'], va='center')

    # 格式化 x 軸
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)

    # 添加數據來源標註
    fig.text(0.99, 0.01, f'數據來源: MacroMicro (SHFE), Yahoo Finance | 更新時間: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
             fontsize=8, color=COLORS['text_dim'], ha='right', va='bottom')

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    # 保存或顯示
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, facecolor=COLORS['background'],
                    edgecolor='none', bbox_inches='tight')
        print(f"[Chart] 已保存到: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="生成銅庫存回補訊號視覺化圖表"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output/copper_inventory_signal.png",
        help="輸出路徑 (預設: output/copper_inventory_signal.png)"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="快取目錄"
    )

    args = parser.parse_args()

    try:
        print("\n" + "=" * 60)
        print("銅庫存回補訊號視覺化")
        print("=" * 60 + "\n")

        # 載入並分析數據
        analyzer = CopperInventorySignalAnalyzer()
        analyzer.load_inventory(cache_dir=args.cache_dir)
        analyzer.fetch_price()
        df = analyzer.generate_signals()

        # 生成圖表
        create_signal_chart(df, output_path=args.output)

        return 0

    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
