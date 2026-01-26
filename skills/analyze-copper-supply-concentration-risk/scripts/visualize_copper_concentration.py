#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
銅供應集中度視覺化（Bloomberg 風格）

生成兩張圖表（上下排列）：
1. 主要產銅國份額堆疊面積圖
2. 智利 vs 新興替代國（Peru + DRC）對比

Usage:
    python visualize_copper_concentration.py
    python visualize_copper_concentration.py --cache cache/copper_production.csv
    python visualize_copper_concentration.py --output ../../output/copper_concentration.png
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# ==================== Bloomberg 配色 ====================
COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "primary": "#ff6b35",
    "secondary": "#ffaa00",
    "tertiary": "#ffff00",
}

# 國家配色（鮮明對比）
COUNTRY_COLORS = {
    "Chile": "#ff6b35",                         # 橙紅（主要）
    "Peru": "#00bfff",                          # 天藍
    "Democratic Republic of Congo": "#00ff88",  # 綠色
    "China": "#ff4444",                         # 紅色
    "US": "#ffaa00",                            # 橙黃
    "Others": "#666666",                        # 灰色
}

# ==================== 字體設定 ====================
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def prepare_concentration_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    準備集中度分析數據

    計算各國份額，並加入 Others 類別
    """
    results = []

    for year in sorted(df['year'].unique()):
        year_data = df[df.year == year].copy()

        # 取得世界總量
        world_row = year_data[year_data.country == 'World']
        if world_row.empty:
            continue
        world_total = world_row.production.values[0]

        if world_total <= 0:
            continue

        # 排除 World
        countries = year_data[year_data.country != 'World'].copy()
        known_total = countries.production.sum()

        # 加入 Others
        others_prod = world_total - known_total

        # 計算各國份額
        def get_share(country: str) -> float:
            row = countries[countries.country == country]
            return float(row.production.values[0] / world_total) if not row.empty else 0.0

        results.append({
            'year': int(year),
            'chile_share': get_share('Chile'),
            'peru_share': get_share('Peru'),
            'drc_share': get_share('Democratic Republic of Congo'),
            'china_share': get_share('China'),
            'us_share': get_share('US'),
            'others_share': others_prod / world_total if others_prod > 0 else 0.0,
            'world_mt': world_total / 1e6
        })

    return pd.DataFrame(results)


def plot_bloomberg_copper_concentration(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Global Copper Mine Production by Country"
):
    """
    繪製 Bloomberg 風格的銅供應集中度圖表

    兩張圖上下排列：
    1. 國家份額堆疊面積圖
    2. 智利 vs 新興替代國對比
    """
    plt.style.use('dark_background')

    # 準備數據
    df_conc = prepare_concentration_data(df)

    if df_conc.empty:
        print("[Error] 無法計算集中度數據")
        return

    # 創建上下兩個子圖
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor=COLORS["background"])

    years = df_conc['year'].values

    # ==================== 圖1: 國家份額堆疊面積圖 ====================
    ax1.set_facecolor(COLORS["background"])

    # 堆疊數據（從下到上）
    stack_data = [
        df_conc['chile_share'].values * 100,
        df_conc['peru_share'].values * 100,
        df_conc['drc_share'].values * 100,
        df_conc['china_share'].values * 100,
        df_conc['us_share'].values * 100,
        df_conc['others_share'].values * 100,
    ]
    labels = ['Chile', 'Peru', 'DRC', 'China', 'US', 'Others']
    colors = [
        COUNTRY_COLORS["Chile"],
        COUNTRY_COLORS["Peru"],
        COUNTRY_COLORS["Democratic Republic of Congo"],
        COUNTRY_COLORS["China"],
        COUNTRY_COLORS["US"],
        COUNTRY_COLORS["Others"],
    ]

    ax1.stackplot(years, stack_data, labels=labels, colors=colors, alpha=0.85)

    # 網格
    ax1.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)

    # Y 軸
    ax1.set_ylim(0, 100)
    ax1.set_ylabel('Share (%)', color=COLORS["text"], fontsize=10)
    ax1.tick_params(axis='y', colors=COLORS["text_dim"])

    # X 軸
    ax1.set_xlim(years.min(), years.max())
    ax1.tick_params(axis='x', colors=COLORS["text_dim"])

    # 標題
    ax1.set_title('Major Copper Producers Share Evolution', color=COLORS["text"],
                  fontsize=12, fontweight='bold', pad=10)

    # 圖例
    ax1.legend(
        loc='upper left',
        fontsize=9,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"],
        ncol=3
    )

    # 標註最新值
    latest_year = years[-1]
    latest_chile = df_conc['chile_share'].iloc[-1] * 100

    ax1.annotate(
        f'Chile: {latest_chile:.1f}%',
        xy=(latest_year, latest_chile / 2),
        xytext=(5, 0),
        textcoords='offset points',
        color=COLORS["text"],
        fontsize=9,
        fontweight='bold',
        va='center'
    )

    # ==================== 圖2: 智利 vs 新興替代國 ====================
    ax2.set_facecolor(COLORS["background"])

    # 智利
    chile_pct = df_conc['chile_share'].values * 100
    ax2.plot(years, chile_pct, color=COUNTRY_COLORS["Chile"], linewidth=2.5, label='Chile')

    # 秘魯 + DRC
    replacers_pct = (df_conc['peru_share'].values + df_conc['drc_share'].values) * 100
    ax2.plot(years, replacers_pct, color='#00d4aa', linewidth=2.5, label='Peru + DRC')

    # 填充區域
    ax2.fill_between(years, chile_pct, alpha=0.2, color=COUNTRY_COLORS["Chile"])
    ax2.fill_between(years, replacers_pct, alpha=0.2, color='#00d4aa')

    # 找到交叉點
    for i in range(1, len(years)):
        if (chile_pct[i-1] > replacers_pct[i-1]) and (chile_pct[i] <= replacers_pct[i]):
            cross_year = years[i]
            cross_value = chile_pct[i]
            ax2.axvline(x=cross_year, color=COLORS["text_dim"], linestyle='--', alpha=0.7)
            ax2.annotate(
                f'Crossover\n{cross_year}',
                xy=(cross_year, cross_value),
                xytext=(10, 20),
                textcoords='offset points',
                color=COLORS["text"],
                fontsize=9,
                fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=COLORS["text_dim"], lw=1)
            )

    # 網格
    ax2.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax2.set_axisbelow(True)

    # Y 軸
    ax2.set_ylim(0, max(chile_pct.max(), replacers_pct.max()) * 1.15)
    ax2.set_ylabel('Share (%)', color=COLORS["text"], fontsize=10)
    ax2.tick_params(axis='y', colors=COLORS["text_dim"])

    # X 軸
    ax2.set_xlim(years.min(), years.max())
    ax2.set_xlabel('Year', color=COLORS["text_dim"], fontsize=10)
    ax2.tick_params(axis='x', colors=COLORS["text_dim"])

    # 標題
    ax2.set_title('Chile vs Emerging Replacers (Peru + DRC)', color=COLORS["text"],
                  fontsize=12, fontweight='bold', pad=10)

    # 圖例
    ax2.legend(
        loc='upper left',
        fontsize=9,
        facecolor=COLORS["background"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"]
    )

    # 最新值標註
    ax2.annotate(
        f'{chile_pct[-1]:.1f}%',
        xy=(years[-1], chile_pct[-1]),
        xytext=(8, 0),
        textcoords='offset points',
        color=COUNTRY_COLORS["Chile"],
        fontsize=11,
        fontweight='bold',
        va='center'
    )
    ax2.annotate(
        f'{replacers_pct[-1]:.1f}%',
        xy=(years[-1], replacers_pct[-1]),
        xytext=(8, 0),
        textcoords='offset points',
        color='#00d4aa',
        fontsize=11,
        fontweight='bold',
        va='center'
    )

    # ==================== 全圖設定 ====================
    # 主標題
    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight='bold', y=0.98)

    # 佈局
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.06, hspace=0.25)

    # 儲存
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS["background"])
    plt.close()

    print(f"[Chart] 已儲存: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="生成 Bloomberg 風格銅供應集中度圖表"
    )
    parser.add_argument(
        "--cache",
        type=str,
        default="cache/copper_production.csv",
        help="數據 CSV 路徑"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="../../output/copper_concentration.png",
        help="輸出圖表路徑"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Global Copper Mine Production by Country (1970-2023)",
        help="圖表標題"
    )

    args = parser.parse_args()

    # 讀取數據
    cache_path = Path(args.cache)
    if not cache_path.exists():
        print(f"[Error] 找不到數據檔案: {cache_path}")
        print("請先執行: python fetch_copper_production.py")
        return 1

    df = pd.read_csv(cache_path)
    print(f"[Data] 載入 {len(df)} 筆記錄")

    # 生成圖表
    plot_bloomberg_copper_concentration(df, args.output, args.title)

    return 0


if __name__ == "__main__":
    sys.exit(main())
