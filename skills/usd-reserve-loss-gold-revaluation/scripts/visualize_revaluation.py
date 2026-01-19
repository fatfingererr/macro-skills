#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gold Revaluation Visualization Script

生成黃金重估壓力測試的視覺化圖表。
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as mpatches
import numpy as np

# 設置中文字體支援
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 添加當前目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from gold_revaluation import (
    GoldRevaluationInput,
    compute_gold_anchor_stress,
    get_gold_price,
    GOLD_RESERVES_TONNES,
    M0_LOCAL,
    M2_LOCAL,
    TONNE_TO_TROY_OZ
)


def create_usd_revaluation_chart(
    output_dir: str = "output",
    filename_prefix: str = "gold_revaluation"
) -> str:
    """
    創建美元黃金重估分析圖表

    Returns:
        str: 輸出檔案路徑
    """
    # 獲取數據
    gold_spot = get_gold_price()

    # 計算 M0 結果
    params_m0 = GoldRevaluationInput(
        entities=["USD"],
        monetary_aggregate="M0",
        weighting_method="fx_turnover"
    )
    result_m0 = compute_gold_anchor_stress(params_m0)

    # 計算 M2 結果
    params_m2 = GoldRevaluationInput(
        entities=["USD"],
        monetary_aggregate="M2",
        weighting_method="fx_turnover"
    )
    result_m2 = compute_gold_anchor_stress(params_m2)

    # 提取數據
    implied_m0 = result_m0["headline"]["implied_gold_price_weighted_usd_per_oz"]
    implied_m2 = result_m2["headline"]["implied_gold_price_weighted_usd_per_oz"]
    backing_m0 = result_m0["table"][0]["backing_ratio_at_spot"]
    backing_m2 = result_m2["table"][0]["backing_ratio_at_spot"]
    lever_m0 = result_m0["headline"]["vs_spot_multiple"]
    lever_m2 = result_m2["headline"]["vs_spot_multiple"]

    # 美元相關數據
    usd_gold_tonnes = GOLD_RESERVES_TONNES["USD"]
    usd_gold_oz = usd_gold_tonnes * TONNE_TO_TROY_OZ
    usd_m0 = M0_LOCAL["USD"]
    usd_m2 = M2_LOCAL["USD"]
    credit_multiplier = lever_m2 / lever_m0

    # 創建圖表
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(
        '美元失去儲備地位：黃金重估壓力測試',
        fontsize=18,
        fontweight='bold',
        y=0.98
    )

    # 設置網格佈局
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3,
                          left=0.08, right=0.92, top=0.90, bottom=0.08)

    # ========================================
    # Panel 1: 金價比較（現價 vs 隱含金價）
    # ========================================
    ax1 = fig.add_subplot(gs[0, 0])

    categories = ['現價', 'M0 隱含', 'M2 隱含']
    prices = [gold_spot, implied_m0, implied_m2]
    colors = ['#2E86AB', '#A23B72', '#F18F01']

    bars = ax1.bar(categories, prices, color=colors, edgecolor='black', linewidth=1.2)

    # 添加數值標籤
    for bar, price in zip(bars, prices):
        height = bar.get_height()
        ax1.annotate(f'${price:,.0f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold')

    ax1.set_ylabel('金價 (USD/oz)', fontsize=12)
    ax1.set_title('金價比較', fontsize=14, fontweight='bold', pad=10)
    ax1.set_ylim(0, max(prices) * 1.15)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x/1000:.0f}k'))
    ax1.grid(axis='y', alpha=0.3)

    # ========================================
    # Panel 2: 重估倍數
    # ========================================
    ax2 = fig.add_subplot(gs[0, 1])

    multiples = [1.0, lever_m0, lever_m2]
    labels = ['現價\n(基準)', f'M0\n({lever_m0:.1f}x)', f'M2\n({lever_m2:.1f}x)']
    colors_mult = ['#2E86AB', '#A23B72', '#F18F01']

    ax2.bar(labels, multiples, color=colors_mult, edgecolor='black', linewidth=1.2)

    # 添加參考線
    ax2.axhline(y=1, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.text(2.4, 1.1, '現價基準', fontsize=9, color='gray')

    ax2.set_ylabel('相對現價倍數', fontsize=12)
    ax2.set_title('黃金需重估倍數', fontsize=14, fontweight='bold', pad=10)
    ax2.set_ylim(0, max(multiples) * 1.15)
    ax2.grid(axis='y', alpha=0.3)

    # ========================================
    # Panel 3: 黃金支撐率（Backing Ratio）- 簡化版本
    # ========================================
    ax3 = fig.add_subplot(gs[0, 2])

    # 使用條形圖代替圓環圖
    ratios = [backing_m0 * 100, backing_m2 * 100]
    labels_br = ['M0', 'M2']
    colors_br = ['#A23B72', '#F18F01']

    bars3 = ax3.bar(labels_br, ratios, color=colors_br, edgecolor='black', linewidth=1.2)

    for bar, ratio in zip(bars3, ratios):
        ax3.annotate(f'{ratio:.1f}%',
                    xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    ax3.set_ylabel('支撐率 (%)', fontsize=12)
    ax3.set_title('黃金支撐率\n(現價下黃金可支撐的貨幣比例)', fontsize=14, fontweight='bold', pad=10)
    ax3.set_ylim(0, max(ratios) * 1.3)
    ax3.grid(axis='y', alpha=0.3)

    # ========================================
    # Panel 4: 貨幣供給 vs 黃金價值
    # ========================================
    ax4 = fig.add_subplot(gs[1, 0])

    gold_value_spot = usd_gold_oz * gold_spot

    categories4 = ['黃金儲備\n(現價計)', 'M0', 'M2']
    values4 = [gold_value_spot / 1e12, usd_m0 / 1e12, usd_m2 / 1e12]
    colors4 = ['#F4D03F', '#A23B72', '#F18F01']

    bars4 = ax4.barh(categories4, values4, color=colors4, edgecolor='black', linewidth=1.2)

    for bar, val in zip(bars4, values4):
        width = bar.get_width()
        ax4.annotate(f'${val:.1f}T',
                    xy=(width, bar.get_y() + bar.get_height()/2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center',
                    fontsize=11, fontweight='bold')

    ax4.set_xlabel('金額 (兆美元)', fontsize=12)
    ax4.set_title('美國貨幣供給 vs 黃金儲備價值', fontsize=14, fontweight='bold', pad=10)
    ax4.set_xlim(0, max(values4) * 1.25)
    ax4.grid(axis='x', alpha=0.3)

    # ========================================
    # Panel 5: 信用乘數視覺化
    # ========================================
    ax5 = fig.add_subplot(gs[1, 1])

    # 階梯圖顯示槓桿放大
    stages = ['央行負債\n(M0)', '銀行信用\n擴張', '廣義貨幣\n(M2)']
    stage_values = [lever_m0, (lever_m0 + lever_m2) / 2, lever_m2]

    ax5.fill_between(range(3), stage_values, alpha=0.3, color='#E74C3C')
    ax5.plot(range(3), stage_values, 'o-', color='#E74C3C', linewidth=3, markersize=12)

    for i, val in enumerate(stage_values):
        ax5.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 10),
                    textcoords="offset points", ha='center',
                    fontsize=11, fontweight='bold')

    ax5.set_xticks(range(3))
    ax5.set_xticklabels(stages)
    ax5.set_ylabel('隱含金價倍數', fontsize=12)
    ax5.set_title(f'信用乘數效應 ({credit_multiplier:.1f}x)', fontsize=14, fontweight='bold', pad=10)
    ax5.set_ylim(0, lever_m2 * 1.2)
    ax5.grid(axis='y', alpha=0.3)

    # ========================================
    # Panel 6: 關鍵數據摘要
    # ========================================
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')

    summary_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        關鍵數據摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ 現價金價
   ${gold_spot:,.0f} / oz

◆ M0 壓力測試
   隱含金價: ${implied_m0:,.0f} / oz
   重估倍數: {lever_m0:.2f}x
   支撐率: {backing_m0:.1%}

◆ M2 壓力測試
   隱含金價: ${implied_m2:,.0f} / oz
   重估倍數: {lever_m2:.2f}x
   支撐率: {backing_m2:.1%}

◆ 美國黃金儲備
   {usd_gold_tonnes:,.1f} 噸
   ({usd_gold_oz/1e6:.1f} 百萬盎司)

◆ 信用乘數
   M2/M0 = {credit_multiplier:.1f}x

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top',
             fontfamily='Microsoft JhengHei',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA',
                      edgecolor='#DEE2E6', linewidth=2))

    # 添加底部註解
    fig.text(0.5, 0.02,
             f'數據來源: WGC (黃金儲備), FRED/Yahoo (金價), BIS (FX權重) | 生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
             ha='center', fontsize=9, color='gray', style='italic')

    fig.text(0.5, 0.005,
             '【注意】此為壓力測試模型，非價格預測。基於「黃金成為唯一貨幣錨定」之極端假設。',
             ha='center', fontsize=9, color='#E74C3C', fontweight='bold')

    # 確保輸出目錄存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成檔名
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{filename_prefix}_usd_{date_str}.png"
    filepath = output_path / filename

    # 儲存圖表
    plt.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    print(f"圖表已儲存至: {filepath}")
    return str(filepath)


def create_multi_currency_chart(
    entities: List[str],
    output_dir: str = "output",
    filename_prefix: str = "gold_revaluation"
) -> str:
    """
    創建多貨幣比較圖表
    """
    gold_spot = get_gold_price()

    # 計算所有實體的結果
    params = GoldRevaluationInput(
        entities=entities,
        monetary_aggregate="M0",
        weighting_method="fx_turnover"
    )
    result = compute_gold_anchor_stress(params)

    # 提取數據
    table = result["table"]

    # 按槓桿倍數排序
    table_sorted = sorted(table, key=lambda x: x["lever_multiple_vs_spot"], reverse=True)

    # 創建圖表
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle('多貨幣黃金重估壓力測試比較 (M0)', fontsize=16, fontweight='bold', y=0.98)

    # Panel 1: 槓桿倍數比較
    ax1 = axes[0]
    entities_sorted = [row["entity"] for row in table_sorted]
    levers = [row["lever_multiple_vs_spot"] for row in table_sorted]

    cmap = plt.cm.get_cmap('RdYlGn_r')
    colors = [cmap(i / len(entities_sorted)) for i in range(len(entities_sorted))]

    bars = ax1.barh(entities_sorted, levers, color=colors, edgecolor='black')
    ax1.axvline(x=1, color='gray', linestyle='--', linewidth=1.5)

    for bar, lever in zip(bars, levers):
        ax1.text(lever + 0.1, bar.get_y() + bar.get_height()/2,
                f'{lever:.1f}x', va='center', fontsize=10, fontweight='bold')

    ax1.set_xlabel('槓桿倍數 (隱含金價 / 現價)', fontsize=12)
    ax1.set_title('各貨幣槓桿程度排名', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    ax1.invert_yaxis()

    # Panel 2: 支撐率比較
    ax2 = axes[1]
    backings = [row["backing_ratio_at_spot"] for row in table_sorted]

    bars2 = ax2.barh(entities_sorted, [b * 100 for b in backings],
                     color=colors, edgecolor='black')

    for bar, backing in zip(bars2, backings):
        ax2.text(backing * 100 + 1, bar.get_y() + bar.get_height()/2,
                f'{backing:.1%}', va='center', fontsize=10, fontweight='bold')

    ax2.set_xlabel('黃金支撐率 (%)', fontsize=12)
    ax2.set_title('各貨幣黃金支撐率', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()

    plt.tight_layout()

    # 儲存
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{filename_prefix}_multi_{date_str}.png"
    filepath = output_path / filename

    plt.savefig(filepath, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    print(f"圖表已儲存至: {filepath}")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Gold Revaluation Visualization")
    parser.add_argument("--mode", default="usd", choices=["usd", "multi", "all"],
                       help="圖表模式: usd=美元單一, multi=多貨幣, all=全部")
    parser.add_argument("--output-dir", default="output", help="輸出目錄")
    parser.add_argument("--prefix", default="gold_revaluation", help="檔名前綴")
    parser.add_argument("--entities", default="USD,EUR,CNY,JPY,GBP,CHF",
                       help="多貨幣模式的實體清單")

    args = parser.parse_args()

    if args.mode in ["usd", "all"]:
        create_usd_revaluation_chart(args.output_dir, args.prefix)

    if args.mode in ["multi", "all"]:
        entities = args.entities.split(",")
        create_multi_currency_chart(entities, args.output_dir, args.prefix)


if __name__ == "__main__":
    main()
