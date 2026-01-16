#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情境衝擊視覺化
生成印尼減產情境的視覺化圖表

Author: Ricky Wang
License: MIT
"""

from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
import numpy as np

# 設置中文字體
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

COLORS = {
    'hard': '#E74C3C',
    'half': '#F39C12',
    'soft': '#2ECC71',
    'baseline': '#3498DB',
}


def plot_scenario_impact(output_dir: Path, date_str: str):
    """繪製情境衝擊對比圖"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 數據
    scenarios = ['完全執行\n(100%)', '半成功\n(50%)', '軟著陸\n(25%)', '無政策\n(0%)']
    cut_amounts = [456, 228, 114, 0]
    global_hits = [12.1, 6.0, 3.0, 0]
    equivalent_days = [44, 22, 11, 0]
    colors = [COLORS['hard'], COLORS['half'], COLORS['soft'], COLORS['baseline']]

    # 圖1: 減產量與全球衝擊
    x = np.arange(len(scenarios))
    width = 0.35

    bars1 = ax1.bar(x - width/2, cut_amounts, width, label='減產量 (kt Ni)',
                    color=[c + '80' for c in colors], edgecolor=colors, linewidth=2)
    ax1.set_ylabel('減產量 (千噸 Ni)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('政策執行情境', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, fontsize=10)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')

    # 添加數值標籤
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f} kt',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax2_twin = ax1.twinx()
    bars2 = ax2_twin.bar(x + width/2, global_hits, width, label='全球供給衝擊 (%)',
                         color=colors, alpha=0.7)
    ax2_twin.set_ylabel('全球供給衝擊 (%)', fontsize=11, fontweight='bold')
    ax2_twin.legend(loc='upper right', fontsize=10)

    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax2_twin.text(bar.get_x() + bar.get_width()/2., height,
                         f'{height:.1f}%',
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax1.set_title('印尼減產20% - 供給衝擊量化', fontsize=12, fontweight='bold', pad=15)

    # 圖2: 風險等級與消費天數
    risk_levels = ['極高風險', '高風險', '中等風險', '無風險']

    bars3 = ax2.barh(scenarios, equivalent_days, color=colors, alpha=0.8)
    ax2.set_xlabel('相當於全球消費天數', fontsize=11, fontweight='bold')
    ax2.set_ylabel('政策執行情境', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # 添加風險等級標籤
    for i, (bar, risk) in enumerate(zip(bars3, risk_levels)):
        width_val = bar.get_width()
        if width_val > 0:
            ax2.text(width_val, bar.get_y() + bar.get_height()/2.,
                    f'  {width_val:.0f}天 ({risk})',
                    ha='left', va='center', fontsize=10, fontweight='bold')

    ax2.set_title('供給缺口 - 消費天數等效', fontsize=12, fontweight='bold', pad=15)

    plt.tight_layout()

    output_path = output_dir / f'nickel_scenario_impact_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_sensitivity_analysis(output_dir: Path, date_str: str):
    """繪製敏感度分析圖"""
    fig, ax = plt.subplots(figsize=(10, 6))

    # 敏感度數據
    execution_rates = [0, 0.25, 0.5, 0.75, 1.0]
    cut_amounts = [0, 114, 228, 342, 456]
    global_hits = [0, 3.0, 6.0, 9.0, 12.1]

    # 繪製曲線
    ax.plot(execution_rates, global_hits, marker='o', linewidth=3,
            markersize=10, color=COLORS['hard'], label='全球供給衝擊')

    # 標記關鍵點
    key_points = [
        (0.25, 3.0, '軟著陸\n3.0%', COLORS['soft']),
        (0.50, 6.0, '半成功\n6.0%', COLORS['half']),
        (1.00, 12.1, '完全執行\n12.1%', COLORS['hard']),
    ]

    for x, y, label, color in key_points:
        ax.scatter(x, y, s=200, color=color, zorder=5, alpha=0.7, edgecolor='black', linewidth=2)
        ax.text(x, y + 0.5, label, ha='center', va='bottom',
               fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.3))

    # 風險區域著色
    ax.axhspan(0, 2, alpha=0.1, color=COLORS['soft'], label='低風險區 (< 2%)')
    ax.axhspan(2, 5, alpha=0.1, color=COLORS['half'], label='中風險區 (2-5%)')
    ax.axhspan(5, 10, alpha=0.1, color=COLORS['hard'], label='高風險區 (5-10%)')
    ax.axhspan(10, 15, alpha=0.2, color=COLORS['hard'], label='極高風險區 (> 10%)')

    ax.set_xlabel('政策執行率', fontsize=12, fontweight='bold')
    ax.set_ylabel('全球供給衝擊 (%)', fontsize=12, fontweight='bold')
    ax.set_title('印尼減產20% - 執行率敏感度分析', fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=9)

    # 設置x軸為百分比
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])

    plt.tight_layout()

    output_path = output_dir / f'nickel_scenario_sensitivity_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def plot_supply_deficit_timeline(output_dir: Path, date_str: str):
    """繪製供給缺口時間線"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # 假設數據：展示供給缺口如何影響庫存
    months = np.arange(0, 13)
    baseline_inventory = 100 - months * 2  # 基準情境：正常消耗
    hard_cut = 100 - months * 8  # 完全執行：快速消耗
    half_cut = 100 - months * 5  # 半成功：中速消耗
    soft_cut = 100 - months * 3  # 軟著陸：慢速消耗

    ax.plot(months, baseline_inventory, linewidth=2.5,
            color=COLORS['baseline'], label='無政策 (基準)', linestyle='--')
    ax.plot(months, soft_cut, linewidth=2.5,
            color=COLORS['soft'], label='軟著陸 (25%執行)')
    ax.plot(months, half_cut, linewidth=2.5,
            color=COLORS['half'], label='半成功 (50%執行)')
    ax.plot(months, hard_cut, linewidth=2.5,
            color=COLORS['hard'], label='完全執行 (100%)')

    # 臨界線
    ax.axhline(y=20, color='red', linestyle=':', alpha=0.5, linewidth=2)
    ax.text(12.5, 20, '警戒線', fontsize=9, ha='left', va='center',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.2))

    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    # 標註耗盡時間
    for data, label, color in [
        (hard_cut, '完全執行\n13個月耗盡', COLORS['hard']),
        (half_cut, '半成功\n20個月耗盡', COLORS['half'])
    ]:
        if (data < 0).any():
            month_zero = np.where(data < 0)[0][0]
            ax.scatter(month_zero, 0, s=150, color=color, zorder=5,
                      edgecolor='black', linewidth=2)

    ax.set_xlabel('時間 (月)', fontsize=12, fontweight='bold')
    ax.set_ylabel('相對庫存水平 (%)', fontsize=12, fontweight='bold')
    ax.set_title('印尼減產情境 - 庫存消耗時間線（示意圖）', fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=10)
    ax.set_xlim(-0.5, 13)
    ax.set_ylim(-20, 110)

    plt.tight_layout()

    output_path = output_dir / f'nickel_scenario_timeline_{date_str}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return str(output_path)


def generate_scenario_charts(output_base_dir: str = "../../../../output"):
    """生成所有情境分析圖表"""
    script_dir = Path(__file__).parent
    output_dir = (script_dir / output_base_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")

    output_files = []

    print("生成情境圖表 1/3: 衝擊對比圖...")
    output_files.append(plot_scenario_impact(output_dir, date_str))

    print("生成情境圖表 2/3: 敏感度分析圖...")
    output_files.append(plot_sensitivity_analysis(output_dir, date_str))

    print("生成情境圖表 3/3: 庫存時間線圖...")
    output_files.append(plot_supply_deficit_timeline(output_dir, date_str))

    return output_files


if __name__ == '__main__':
    print("=" * 60)
    print("印尼減產20%情境分析 - 圖表生成")
    print("=" * 60)
    print()

    output_files = generate_scenario_charts()

    print()
    print("=" * 60)
    print("✅ 情境分析圖表生成完成！")
    print("=" * 60)
    print()
    print("生成的圖表:")
    for i, path in enumerate(output_files, 1):
        print(f"{i}. {path}")
