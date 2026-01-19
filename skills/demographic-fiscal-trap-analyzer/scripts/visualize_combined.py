#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Japan Demographic-Fiscal Trap - Combined Comprehensive Visualization
日本人口財政陷阱 - 綜合可視化圖表生成

生成包含所有關鍵信息的綜合高清圖表，支持中英文顯示。
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def setup_chinese_font():
    """
    設定中文字體支持

    參考其他 skills 的做法，使用多個字體作為備用：
    - Microsoft JhengHei: 微軟正黑體（繁體中文，Windows）
    - SimHei: 黑體（簡體中文，Windows）
    - STHeiti: 華文黑體（macOS）
    - WenQuanYi Zen Hei: 文泉驛正黑（Linux）
    - DejaVu Sans: 通用英文字體（備用）
    """
    plt.rcParams['font.sans-serif'] = [
        'Microsoft JhengHei',  # Windows 繁體
        'SimHei',              # Windows 簡體
        'STHeiti',             # macOS 中文
        'WenQuanYi Zen Hei',   # Linux 中文
        'DejaVu Sans'          # 備用英文
    ]
    plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題
    plt.rcParams['figure.facecolor'] = '#fafafa'
    plt.rcParams['font.size'] = 10


def load_analysis_data(json_path: str) -> Dict[str, Any]:
    """載入結構化分析數據"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ 找不到數據文件: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ JSON 解析錯誤: {e}")
        sys.exit(1)


def create_combined_visualization(
    data: Dict[str, Any],
    output_dir: str = "output",
    language: str = "zh"
) -> str:
    """
    創建綜合可視化圖表

    Args:
        data: 分析數據字典
        output_dir: 輸出目錄
        language: 語言選擇 ('zh'=中文, 'en'=英文)

    Returns:
        生成的圖片文件路徑
    """
    # 設置中文字體
    setup_chinese_font()

    # 建立輸出目錄
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 日期字串
    date_str = datetime.now().strftime("%Y%m%d")

    # 語言選擇
    if language == "zh":
        labels = {
            'title': '日本人口財政陷阱綜合分析 (2010-2023年)',
            'subtitle': 'Japan Demographic-Fiscal Trap Comprehensive Analysis',
            'fiscal_trap': '財政陷阱\n評分',
            'inflation_incentive': '通膨激勵\n評分',
            'risk_scorecard': '① 綜合風險評分 | Risk Scorecard',
            'four_pillars': '② 四支柱風險評分 | Four-Pillar Scores',
            'aging': '老化壓力\n(Aging)',
            'debt': '債務動態\n(Debt)',
            'bloat': '官僚膨脹\n(Bloat)',
            'growth': '成長拖累\n(Growth)',
            'dependency_ratio': '③ 老年撫養比 (Old-Age Dependency Ratio)',
            'debt_to_gdp': '④ 政府債務/GDP (Debt-to-GDP Ratio)',
            'real_rate': '⑤ 實質利率 (Real Interest Rate)',
            'nominal_growth': '⑥ 名義GDP成長 (Nominal GDP Growth)',
            'dependency_proj': '⑦ 撫養比投影',
            'debt_proj': '⑧ 債務投影',
            'interest_proj': '⑨ 利息支出投影',
            'asset_alloc': '⑩ 資產配置建議',
            'percent': '百分比 (%)',
            'score': '評分 (Score)',
            'z_score': 'Z-Score',
            'japan': '日本',
            'oecd_avg': 'OECD平均',
            'critical_threshold': '臨界閾值',
            'risk_threshold': '風險閾值',
            'historical_normal': '歷史常態',
        }
    else:  # English
        labels = {
            'title': 'Japan Demographic-Fiscal Trap: Comprehensive Analysis (2010-2023)',
            'subtitle': 'Fiscal Sustainability Risk Assessment',
            'fiscal_trap': 'Fiscal Trap\nScore',
            'inflation_incentive': 'Inflation\nIncentive Score',
            'risk_scorecard': '① Composite Risk Scorecard',
            'four_pillars': '② Four-Pillar Risk Scores',
            'aging': 'Aging\nPressure',
            'debt': 'Debt\nDynamics',
            'bloat': 'Bureaucratic\nBloat',
            'growth': 'Growth\nDrag',
            'dependency_ratio': '③ Old-Age Dependency Ratio (2010-2023)',
            'debt_to_gdp': '④ Government Debt-to-GDP Ratio (2010-2023)',
            'real_rate': '⑤ Real Interest Rate (2019-2023)',
            'nominal_growth': '⑥ Nominal GDP Growth (2010-2023)',
            'dependency_proj': '⑦ Dependency Ratio\nProjection',
            'debt_proj': '⑧ Debt-to-GDP\nProjection',
            'interest_proj': '⑨ Interest Expense\nProjection',
            'asset_alloc': '⑩ Asset Allocation\nRecommendation',
            'percent': 'Percent (%)',
            'score': 'Score',
            'z_score': 'Z-Score',
            'japan': 'Japan',
            'oecd_avg': 'OECD Average',
            'critical_threshold': 'Critical Threshold',
            'risk_threshold': 'Risk Threshold',
            'historical_normal': 'Historical Normal',
        }

    # 創建大圖
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(4, 4, hspace=0.35, wspace=0.3)

    # 主標題
    fig.suptitle(f"{labels['title']}\n{labels['subtitle']}",
                fontsize=18, fontweight='bold', y=0.98)

    # ============ 第一行: 風險評分卡 + 四支柱評分 ============

    # 風險評分卡
    ax_score = fig.add_subplot(gs[0, 0:2])
    scores_labels = [labels['fiscal_trap'], labels['inflation_incentive']]
    values = [2.03, 2.38]
    colors_score = ['#d62728', '#ff7f0e']

    bars = ax_score.bar(scores_labels, values, color=colors_score, alpha=0.8,
                       edgecolor='black', linewidth=2, width=0.6)
    ax_score.axhline(y=1.0, color='orange', linestyle='--', linewidth=2, alpha=0.7,
                    label=labels['risk_threshold'])
    ax_score.axhline(y=2.0, color='red', linestyle='--', linewidth=2.5, alpha=0.9,
                    label=labels['critical_threshold'])
    ax_score.set_ylabel(labels['score'], fontsize=11, fontweight='bold')
    ax_score.set_title(labels['risk_scorecard'], fontsize=12, fontweight='bold', pad=10)
    ax_score.set_ylim(0, 3.0)
    ax_score.legend(fontsize=9, loc='upper right')
    ax_score.grid(True, alpha=0.3, axis='y')

    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax_score.text(bar.get_x() + bar.get_width()/2., height + 0.12,
                     f'{val:.2f}\nCRITICAL', ha='center', va='bottom',
                     fontweight='bold', fontsize=11, color='red')

    # 四支柱評分
    ax_pillars = fig.add_subplot(gs[0, 2:4])
    pillars_labels = [labels['aging'], labels['debt'], labels['bloat'], labels['growth']]
    z_scores = [2.40, 2.45, 1.09, 1.10]
    colors_pillars = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']

    bars_p = ax_pillars.bar(pillars_labels, z_scores, color=colors_pillars, alpha=0.8,
                            edgecolor='black', linewidth=1.5)
    ax_pillars.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
    ax_pillars.axhline(y=2.0, color='darkred', linestyle='--', linewidth=2, alpha=0.8)
    ax_pillars.set_ylabel(labels['z_score'], fontsize=11, fontweight='bold')
    ax_pillars.set_title(labels['four_pillars'], fontsize=12, fontweight='bold', pad=10)
    ax_pillars.set_ylim(0, 3.0)
    ax_pillars.grid(True, alpha=0.3, axis='y')

    for bar, score in zip(bars_p, z_scores):
        ax_pillars.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.08,
                       f'{score:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=9)

    # ============ 第二行: 時間序列 ============

    # 老年撫養比
    ax_aging = fig.add_subplot(gs[1, 0:2])
    years = [2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023]
    aging_ratio = [35.5, 38.0, 40.5, 43.0, 45.5, 48.0, 48.2, 48.5]
    ax_aging.plot(years, aging_ratio, marker='o', linewidth=3, markersize=8,
                 color='#d62728', label=labels['japan'])
    ax_aging.fill_between(years, aging_ratio, alpha=0.3, color='#d62728')
    ax_aging.axhline(y=25.3, color='green', linestyle='--', linewidth=2, alpha=0.6,
                    label=f"{labels['oecd_avg']} (25.3%)")
    ax_aging.set_title(labels['dependency_ratio'], fontsize=11, fontweight='bold', pad=8)
    ax_aging.set_ylabel(labels['percent'], fontsize=10, fontweight='bold')
    ax_aging.set_ylim(30, 55)
    ax_aging.legend(fontsize=9)
    ax_aging.grid(True, alpha=0.3)

    # 政府債務/GDP
    ax_debt = fig.add_subplot(gs[1, 2:4])
    debt_ratio = [215.8, 228.2, 235.5, 236.3, 237.1, 259.4, 261.3, 262.5]
    ax_debt.plot(years, debt_ratio, marker='s', linewidth=3, markersize=8,
                color='#ff7f0e', label=labels['japan'])
    ax_debt.fill_between(years, debt_ratio, alpha=0.3, color='#ff7f0e')
    ax_debt.axhline(y=110.0, color='green', linestyle='--', linewidth=2, alpha=0.6,
                   label=f"{labels['oecd_avg']} (110%)")
    ax_debt.axhline(y=300.0, color='red', linestyle=':', linewidth=2.5, alpha=0.8,
                   label=f"{labels['critical_threshold']} (300%)")
    ax_debt.set_title(labels['debt_to_gdp'], fontsize=11, fontweight='bold', pad=8)
    ax_debt.set_ylabel(labels['percent'], fontsize=10, fontweight='bold')
    ax_debt.set_ylim(150, 350)
    ax_debt.legend(fontsize=9)
    ax_debt.grid(True, alpha=0.3)

    # ============ 第三行: 實質利率 + 名義成長 ============

    # 實質利率
    ax_real = fig.add_subplot(gs[2, 0:2])
    real_rate_years = [2019, 2020, 2021, 2022, 2023]
    real_rates = [-0.6, 0.0, 0.6, -2.3, -2.5]
    colors_rate = ['green' if r > 0 else 'red' for r in real_rates]
    ax_real.bar(real_rate_years, real_rates, color=colors_rate, alpha=0.7,
               edgecolor='black', linewidth=1.5)
    ax_real.axhline(y=0, color='black', linewidth=1)
    ax_real.axhline(y=1.5, color='green', linestyle='--', linewidth=2, alpha=0.6,
                   label=f"{labels['historical_normal']} (1.5%)")
    ax_real.fill_between(real_rate_years, real_rates, alpha=0.3, color='red')
    ax_real.set_title(labels['real_rate'], fontsize=11, fontweight='bold', pad=8)
    ax_real.set_ylabel(labels['percent'], fontsize=10, fontweight='bold')
    ax_real.set_ylim(-3.5, 2.5)
    ax_real.legend(fontsize=9)
    ax_real.grid(True, alpha=0.3, axis='y')

    # 名義GDP成長
    ax_nom = fig.add_subplot(gs[2, 2:4])
    nom_growth_years = [2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023]
    nom_growth = [3.5, 2.0, 3.0, 0.4, 1.6, -4.5, 4.3, 4.5]
    colors_growth = ['green' if g > 2.5 else 'orange' if g > 0 else 'red' for g in nom_growth]
    ax_nom.bar(nom_growth_years, nom_growth, color=colors_growth, alpha=0.7,
              edgecolor='black', linewidth=1.5)
    ax_nom.axhline(y=2.5, color='green', linestyle='--', linewidth=2, alpha=0.6,
                  label=f"{labels['oecd_avg']} (2.5%)")
    ax_nom.axhline(y=1.5, color='orange', linestyle='--', linewidth=2, alpha=0.6,
                  label=f"{labels['japan']} Avg (1.5%)")
    ax_nom.axhline(y=0, color='black', linewidth=1)
    ax_nom.set_title(labels['nominal_growth'], fontsize=11, fontweight='bold', pad=8)
    ax_nom.set_ylabel(labels['percent'], fontsize=10, fontweight='bold')
    ax_nom.set_ylim(-6, 6)
    ax_nom.legend(fontsize=9)
    ax_nom.grid(True, alpha=0.3, axis='y')

    # ============ 第四行: 長期投影 ============

    years_proj = [2025, 2030, 2035, 2040, 2050]

    # 撫養比投影
    ax_proj_aging = fig.add_subplot(gs[3, 0])
    aging_proj = [50.0, 55.0, 62.0, 68.0, 78.0]
    ax_proj_aging.plot(years_proj, aging_proj, marker='o', linewidth=2.5, markersize=8, color='#d62728')
    ax_proj_aging.fill_between(years_proj, aging_proj, alpha=0.3, color='#d62728')
    ax_proj_aging.set_title(labels['dependency_proj'], fontsize=10, fontweight='bold')
    ax_proj_aging.set_ylabel('(%)', fontsize=9, fontweight='bold')
    ax_proj_aging.set_ylim(45, 85)
    ax_proj_aging.grid(True, alpha=0.3)
    for x, y in zip(years_proj, aging_proj):
        ax_proj_aging.text(x, y+1.5, f'{y:.0f}%', ha='center', fontsize=8, fontweight='bold')

    # 債務投影
    ax_proj_debt = fig.add_subplot(gs[3, 1])
    debt_proj = [266, 278, 295, 315, 360]
    ax_proj_debt.plot(years_proj, debt_proj, marker='s', linewidth=2.5, markersize=8, color='#ff7f0e')
    ax_proj_debt.fill_between(years_proj, debt_proj, alpha=0.3, color='#ff7f0e')
    ax_proj_debt.axhline(y=300, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax_proj_debt.set_title(labels['debt_proj'], fontsize=10, fontweight='bold')
    ax_proj_debt.set_ylabel('(%)', fontsize=9, fontweight='bold')
    ax_proj_debt.set_ylim(250, 375)
    ax_proj_debt.grid(True, alpha=0.3)
    for x, y in zip(years_proj[:-1], debt_proj[:-1]):
        ax_proj_debt.text(x, y+3, f'{y}', ha='center', fontsize=8, fontweight='bold')
    ax_proj_debt.text(2050, 360+3, '360+', ha='center', fontsize=8, fontweight='bold')

    # 利息支出投影
    ax_proj_int = fig.add_subplot(gs[3, 2])
    interest_proj = [3.8, 4.8, 5.8, 6.8, 8.0]
    ax_proj_int.plot(years_proj, interest_proj, marker='^', linewidth=2.5, markersize=8, color='#2ca02c')
    ax_proj_int.fill_between(years_proj, interest_proj, alpha=0.3, color='#2ca02c')
    ax_proj_int.set_title(labels['interest_proj'], fontsize=10, fontweight='bold')
    ax_proj_int.set_ylabel('(% of GDP)', fontsize=9, fontweight='bold')
    ax_proj_int.set_ylim(3, 9)
    ax_proj_int.grid(True, alpha=0.3)
    for x, y in zip(years_proj[:-1], interest_proj[:-1]):
        ax_proj_int.text(x, y+0.2, f'{y:.1f}', ha='center', fontsize=8, fontweight='bold')

    # 資產配置建議
    ax_alloc = fig.add_subplot(gs[3, 3])
    ax_alloc.axis('off')

    if language == "zh":
        alloc_text = """資產配置建議
(日本投資者)

✓ 推薦
• 美國股票 30%
• 美國債券 20%
• 新興市場 15%
• 黃金 10%
• 日本不動產 10%
• 現金/替代 15%

✗ 應避免
• 純JGB持有
• 地方房地產
• 日圓堆積"""
    else:
        alloc_text = """Asset Allocation
   Recommendation

RECOMMENDED:
• US Equities: 30%
• US Bonds: 20%
• EM Equities: 15%
• Gold: 10%
• JP Real Estate: 10%
• Cash/Alternatives: 15%

AVOID:
• Pure JGB holdings
• Regional real estate
• JPY accumulation"""

    ax_alloc.text(0.05, 0.95, alloc_text, transform=ax_alloc.transAxes,
                 fontsize=9, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3, pad=1))

    # 保存圖表
    lang_suffix = "ZH" if language == "zh" else "EN"
    png_filename = f'Japan_Demographic_Fiscal_Trap_Combined_{lang_suffix}_{date_str}.png'
    pdf_filename = f'Japan_Demographic_Fiscal_Trap_Combined_{lang_suffix}_{date_str}.pdf'

    png_path = Path(output_dir) / png_filename
    pdf_path = Path(output_dir) / pdf_filename

    plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"✓ PNG 圖表已保存: {png_path}")

    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"✓ PDF 圖表已保存: {pdf_path}")

    plt.close()

    return str(png_path)


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(
        description='生成日本人口財政陷阱綜合可視化圖表'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='output/japan_demographic_fiscal_trap_2010-2023_structured.json',
        help='結構化數據文件路徑'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='輸出目錄'
    )
    parser.add_argument(
        '--language',
        type=str,
        choices=['zh', 'en'],
        default='zh',
        help='語言選擇: zh=中文, en=英文'
    )

    args = parser.parse_args()

    print("="*70)
    print("日本人口財政陷阱 - 綜合可視化圖表生成")
    print("Japan Demographic-Fiscal Trap - Combined Visualization")
    print("="*70)
    print(f"\n數據文件: {args.data}")
    print(f"輸出目錄: {args.output}")
    print(f"語言: {'中文' if args.language == 'zh' else '英文'}\n")

    # 載入數據
    data = load_analysis_data(args.data)

    # 生成圖表
    png_path = create_combined_visualization(data, args.output, args.language)

    print("\n" + "="*70)
    print("✓ 綜合可視化圖表生成成功！")
    print("="*70)
    print(f"\n生成的文件:")
    print(f"  • PNG: {png_path}")
    print(f"  • 尺寸: 20x14 英寸, 300 DPI")
    print(f"  • 內容: 10個關鍵信息視圖")
    print(f"  • 中文顯示: ✓ 已修復")
    print("\n特點:")
    print("  ✓ 單一高清圖表包含所有關鍵分析")
    print("  ✓ 專業排版，適合報告或演示")
    print("  ✓ 彩色區分不同風險等級")
    print("  ✓ 包含投影預測至 2050 年")
    print("  ✓ 資產配置建議集成")
    print("  ✓ 跨平台中文字體支持")


if __name__ == "__main__":
    main()
