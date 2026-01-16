#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nickel Concentration Risk Visualization
生成全球鎳供給集中度分析圖表

Author: Ricky Wang
License: MIT
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非GUI後端
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams

# 設置中文字體
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 設置配色方案
COLORS = {
    'indonesia': '#E74C3C',  # 紅色
    'philippines': '#3498DB',  # 藍色
    'russia': '#2ECC71',  # 綠色
    'canada': '#F39C12',  # 橙色
    'australia': '#9B59B6',  # 紫色
    'other': '#95A5A6',  # 灰色
    'risk_high': '#E74C3C',
    'risk_medium': '#F39C12',
    'risk_low': '#2ECC71',
}


def setup_output_dir(base_dir: str = "./output") -> Path:
    """
    設置輸出目錄

    Args:
        base_dir: 基礎輸出目錄

    Returns:
        輸出目錄路徑
    """
    output_dir = Path(base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def plot_indonesia_share_trend(
    df: pd.DataFrame,
    output_dir: Path,
    date_str: str
) -> str:
    """
    繪製印尼市佔率時序圖

    Args:
        df: 時序數據
        output_dir: 輸出目錄
        date_str: 日期字串

    Returns:
        輸出檔案路徑
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 印尼市佔率
    ax1.plot(df['year'], df['indonesia_share'] * 100,
             marker='o', linewidth=2.5, markersize=8,
             color=COLORS['indonesia'], label='印尼市佔率')
    ax1.set_xlabel('年份', fontsize=12, fontweight='bold')
    ax1.set_ylabel('印尼市佔率 (%)', fontsize=12, fontweight='bold', color=COLORS['indonesia'])
    ax1.tick_params(axis='y', labelcolor=COLORS['indonesia'])
    ax1.grid(True, alpha=0.3, linestyle='--')

    # 標記關鍵事件
    ax1.axvline(x=2020, color='gray', linestyle='--', alpha=0.5, linewidth=1.5)
    ax1.text(2020, 65, '2020: 礦石出口禁令',
             rotation=0, fontsize=9, ha='left', va='bottom',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    ax1.axvline(x=2022, color='gray', linestyle='--', alpha=0.5, linewidth=1.5)
    ax1.text(2022, 65, '2022: 突破50%',
             rotation=0, fontsize=9, ha='left', va='bottom',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    # 添加HHI（第二y軸）
    ax2 = ax1.twinx()
    ax2.plot(df['year'], df['hhi'],
             marker='s', linewidth=2, markersize=6,
             color='#34495E', alpha=0.6, label='HHI', linestyle='--')
    ax2.set_ylabel('HHI (Herfindahl-Hirschman Index)',
                   fontsize=12, fontweight='bold', color='#34495E')
    ax2.tick_params(axis='y', labelcolor='#34495E')

    # HHI臨界線
    ax2.axhline(y=2500, color=COLORS['risk_medium'], linestyle=':', alpha=0.5)
    ax2.text(2024.5, 2500, 'HHI=2500\n(高集中門檻)',
             fontsize=8, ha='left', va='center',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

    # 標題
    plt.title('全球鎳供給集中度趨勢 (2015-2024)\nIndonesia Share & HHI',
              fontsize=14, fontweight='bold', pad=20)

    # 圖例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

    plt.tight_layout()

    output_path = output_dir / f'nickel_indonesia_share_trend_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_country_share_pie(
    df: pd.DataFrame,
    output_dir: Path,
    date_str: str
) -> str:
    """
    繪製2024年國家份額餅圖

    Args:
        df: 2024年國家數據
        output_dir: 輸出目錄
        date_str: 日期字串

    Returns:
        輸出檔案路徑
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # 準備數據
    countries = df['country'].tolist()
    shares = df['share'].tolist()

    # 顏色映射
    colors_list = [
        COLORS.get(c.lower(), '#95A5A6') for c in countries
    ]

    # 突出印尼
    explode = [0.1 if c == 'Indonesia' else 0 for c in countries]

    # 繪製餅圖
    wedges, texts, autotexts = ax.pie(
        shares,
        labels=countries,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        explode=explode,
        textprops={'fontsize': 11, 'fontweight': 'bold'},
        pctdistance=0.85
    )

    # 美化百分比文字
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')

    # 添加圖例（包含產量）
    legend_labels = [
        f"{row['country']}: {row['share']:.1%} ({row['value']/1000:,.0f} kt Ni)"
        for _, row in df.iterrows()
    ]
    ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=9)

    plt.title('2024年全球鎳產量國家分布\nGlobal Nickel Production by Country',
              fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_path = output_dir / f'nickel_country_share_pie_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_concentration_metrics(
    df: pd.DataFrame,
    output_dir: Path,
    date_str: str
) -> str:
    """
    繪製集中度指標演進圖（CR1, CR3, CR5）

    Args:
        df: 時序數據
        output_dir: 輸出目錄
        date_str: 日期字串

    Returns:
        輸出檔案路徑
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # 繪製CR指標
    ax.plot(df['year'], df['cr1'] * 100,
            marker='o', linewidth=2.5, markersize=7,
            color=COLORS['indonesia'], label='CR1 (最大國)')

    ax.plot(df['year'], df['cr3'] * 100,
            marker='s', linewidth=2.5, markersize=7,
            color=COLORS['philippines'], label='CR3 (前三國)')

    ax.plot(df['year'], df['cr5'] * 100,
            marker='^', linewidth=2.5, markersize=7,
            color=COLORS['russia'], label='CR5 (前五國)')

    # 臨界線
    ax.axhline(y=50, color=COLORS['risk_medium'], linestyle='--', alpha=0.5, linewidth=1.5)
    ax.text(2024.5, 50, '50%', fontsize=9, ha='left', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

    ax.axhline(y=80, color=COLORS['risk_high'], linestyle='--', alpha=0.5, linewidth=1.5)
    ax.text(2024.5, 80, '80%', fontsize=9, ha='left', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.2))

    # 設置
    ax.set_xlabel('年份', fontsize=12, fontweight='bold')
    ax.set_ylabel('集中度 (%)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=11)

    plt.title('全球鎳供給集中度指標演進 (2015-2024)\nConcentration Ratios (CR1, CR3, CR5)',
              fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_path = output_dir / f'nickel_concentration_metrics_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_production_volume(
    df: pd.DataFrame,
    output_dir: Path,
    date_str: str
) -> str:
    """
    繪製印尼vs全球產量對比圖

    Args:
        df: 時序數據
        output_dir: 輸出目錄
        date_str: 日期字串

    Returns:
        輸出檔案路徑
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # 堆疊柱狀圖
    other_prod = df['global_prod'] - df['indonesia_prod']

    ax.bar(df['year'], df['indonesia_prod'],
           label='印尼產量', color=COLORS['indonesia'], alpha=0.9)
    ax.bar(df['year'], other_prod, bottom=df['indonesia_prod'],
           label='其他國家產量', color=COLORS['other'], alpha=0.6)

    # 添加總產量趨勢線
    ax.plot(df['year'], df['global_prod'],
            marker='o', color='black', linewidth=2, markersize=6,
            label='全球總產量', linestyle='--')

    # 設置
    ax.set_xlabel('年份', fontsize=12, fontweight='bold')
    ax.set_ylabel('產量 (千噸 Ni)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(loc='upper left', fontsize=11)

    # 添加2024年數據標籤
    latest = df.iloc[-1]
    ax.text(latest['year'], latest['global_prod'],
            f"{latest['global_prod']:,.0f} kt\n({latest['indonesia_share']:.1%} 印尼)",
            ha='center', va='bottom', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    plt.title('印尼 vs 全球鎳產量對比 (2015-2024)\nIndonesia vs Global Nickel Production',
              fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    output_path = output_dir / f'nickel_production_volume_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_risk_matrix(
    output_dir: Path,
    date_str: str,
    cr1_2024: float,
    hhi_2024: float
) -> str:
    """
    繪製集中度風險矩陣

    Args:
        output_dir: 輸出目錄
        date_str: 日期字串
        cr1_2024: 2024年CR1值
        hhi_2024: 2024年HHI值

    Returns:
        輸出檔案路徑
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # 定義風險矩陣
    risk_matrix = np.array([
        [1, 2, 3],  # CR1 < 30%
        [2, 3, 4],  # CR1 30-50%
        [3, 4, 5],  # CR1 > 50%
    ])

    # 顏色映射
    colors_matrix = np.array([
        ['#2ECC71', '#F39C12', '#E67E22'],
        ['#F39C12', '#E67E22', '#E74C3C'],
        ['#E67E22', '#E74C3C', '#C0392B'],
    ])

    # 繪製矩陣
    for i in range(3):
        for j in range(3):
            rect = mpatches.Rectangle((j, 2-i), 1, 1,
                                     facecolor=colors_matrix[i, j],
                                     edgecolor='white', linewidth=2)
            ax.add_patch(rect)

            # 添加風險等級文字
            risk_labels = {1: '低風險', 2: '中風險', 3: '中高風險', 4: '高風險', 5: '極高風險'}
            ax.text(j + 0.5, 2 - i + 0.5, risk_labels[risk_matrix[i, j]],
                   ha='center', va='center', fontsize=11, fontweight='bold',
                   color='white')

    # 標記2024年位置
    # HHI: > 2500 → j=2, CR1: > 50% → i=2
    hhi_idx = 2 if hhi_2024 > 2500 else (1 if hhi_2024 > 1500 else 0)
    cr1_idx = 2 if cr1_2024 > 0.5 else (1 if cr1_2024 > 0.3 else 0)

    ax.plot(hhi_idx + 0.5, 2 - cr1_idx + 0.5,
           marker='*', markersize=30, color='yellow',
           markeredgecolor='black', markeredgewidth=2)
    ax.text(hhi_idx + 0.5, 2 - cr1_idx + 0.2, '2024',
           ha='center', va='top', fontsize=10, fontweight='bold',
           color='black')

    # 設置軸標籤
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_xticks([0.5, 1.5, 2.5])
    ax.set_xticklabels(['HHI < 1500\n(低集中)', 'HHI 1500-2500\n(中等集中)', 'HHI > 2500\n(高集中)'],
                       fontsize=10)
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(['CR1 > 50%\n(主導)', 'CR1 30-50%\n(主要)', 'CR1 < 30%\n(分散)'],
                       fontsize=10)

    ax.set_xlabel('HHI (市場集中度指數)', fontsize=12, fontweight='bold')
    ax.set_ylabel('CR1 (最大國市佔率)', fontsize=12, fontweight='bold')

    plt.title('全球鎳供給集中度風險矩陣\nNickel Supply Concentration Risk Matrix',
              fontsize=14, fontweight='bold', pad=20)

    # 添加說明
    info_text = f'2024年定位: CR1={cr1_2024:.1%}, HHI={hhi_2024:.0f}\n風險評級: 極高風險'
    ax.text(1.5, -0.3, info_text, ha='center', va='top', fontsize=11,
           bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.3))

    plt.tight_layout()

    output_path = output_dir / f'nickel_risk_matrix_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def generate_all_charts(output_base_dir: str = "../../../../output") -> List[str]:
    """
    生成所有圖表

    Args:
        output_base_dir: 輸出基礎目錄

    Returns:
        生成的圖表路徑列表
    """
    # 設置輸出目錄
    script_dir = Path(__file__).parent
    output_dir = (script_dir / output_base_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 日期字串
    date_str = datetime.now().strftime("%Y%m%d")

    # 載入數據
    from ingest_sources import ingest_all_sources
    from compute_concentration import (
        calculate_country_share, calculate_CRn, calculate_HHI
    )

    df_all = ingest_all_sources(data_level='free_nolimit')

    # 準備時序數據
    time_series_data = []
    for year in range(2015, 2025):
        df_year = df_all[(df_all['year'] == year) &
                         (df_all['country'] != 'World') &
                         (df_all['supply_type'] == 'mined')]

        if len(df_year) == 0:
            continue

        indonesia_prod = df_year[df_year['country'] == 'Indonesia']['value'].sum() / 1000
        global_prod = df_year['value'].sum() / 1000
        indonesia_share = calculate_country_share(df_year, 'Indonesia')
        cr_metrics = calculate_CRn(df_year, n=5)
        hhi = calculate_HHI(df_year)

        time_series_data.append({
            'year': year,
            'indonesia_prod': indonesia_prod,
            'global_prod': global_prod,
            'indonesia_share': indonesia_share,
            'cr1': cr_metrics['CR1'],
            'cr3': cr_metrics['CR3'],
            'cr5': cr_metrics['CR5'],
            'hhi': hhi
        })

    df_ts = pd.DataFrame(time_series_data)

    # 準備2024年國家數據
    df_2024 = df_all[(df_all['year'] == 2024) &
                     (df_all['country'] != 'World') &
                     (df_all['supply_type'] == 'mined')]

    country_data = []
    for country in ['Indonesia', 'Philippines', 'Russia', 'Canada', 'Australia', 'Other', 'New Caledonia']:
        value = df_2024[df_2024['country'] == country]['value'].sum()
        if value > 0:
            country_data.append({
                'country': country,
                'value': value,
                'share': value / df_2024['value'].sum()
            })

    df_country = pd.DataFrame(country_data).sort_values('share', ascending=False)

    # 生成圖表
    output_files = []

    print("生成圖表 1/5: 印尼市佔率趨勢圖...")
    output_files.append(plot_indonesia_share_trend(df_ts, output_dir, date_str))

    print("生成圖表 2/5: 國家份額餅圖...")
    output_files.append(plot_country_share_pie(df_country, output_dir, date_str))

    print("生成圖表 3/5: 集中度指標演進圖...")
    output_files.append(plot_concentration_metrics(df_ts, output_dir, date_str))

    print("生成圖表 4/5: 產量對比圖...")
    output_files.append(plot_production_volume(df_ts, output_dir, date_str))

    print("生成圖表 5/5: 風險矩陣圖...")
    row_2024 = df_ts[df_ts['year'] == 2024].iloc[0]
    cr1_2024 = row_2024['cr1']
    hhi_2024 = row_2024['hhi']
    output_files.append(plot_risk_matrix(output_dir, date_str, cr1_2024, hhi_2024))

    return output_files


if __name__ == '__main__':
    print("=" * 60)
    print("全球鎳供給集中度分析 - 圖表生成")
    print("=" * 60)
    print()

    output_files = generate_all_charts()

    print()
    print("=" * 60)
    print("✅ 所有圖表生成完成！")
    print("=" * 60)
    print()
    print("生成的圖表:")
    for i, path in enumerate(output_files, 1):
        print(f"{i}. {path}")
    print()
