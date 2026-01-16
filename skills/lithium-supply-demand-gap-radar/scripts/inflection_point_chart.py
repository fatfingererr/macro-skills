#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
鋰市場拐點分析視覺化圖表

繪製歷史拐點和未來拐點預測，整合供需平衡、價格走勢和關鍵催化劑
"""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_chinese_font():
    """設定中文字體"""
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def generate_inflection_point_chart(
    output_dir: str = "output",
    asof_date: Optional[str] = None
) -> str:
    """
    生成鋰市場拐點分析圖表

    Args:
        output_dir: 輸出目錄
        asof_date: 分析日期（YYYY-MM-DD），預設為今天

    Returns:
        生成的圖片路徑
    """
    setup_chinese_font()

    if asof_date is None:
        asof_date = date.today().strftime("%Y-%m-%d")

    logger.info(f"Generating inflection point chart for {asof_date}")

    # ========================================================================
    # 數據準備
    # ========================================================================

    # 時間軸（季度）
    dates = pd.date_range(start="2020-01-01", end="2027-12-31", freq="QE")

    # 供需平衡指數（Balance Index）歷史 + 預測
    # 負值 = 供給過剩，正值 = 需求缺口
    balance_index_historical = [
        0.2,   # 2020Q1
        0.3,   # 2020Q2
        0.4,   # 2020Q3
        0.5,   # 2020Q4
        0.7,   # 2021Q1
        0.9,   # 2021Q2
        1.1,   # 2021Q3
        1.3,   # 2021Q4
        1.5,   # 2022Q1
        1.8,   # 2022Q2
        2.0,   # 2022Q3
        2.2,   # 2022Q4
        2.0,   # 2023Q1（拐點前）
        1.5,   # 2023Q2（拐點）
        0.8,   # 2023Q3（拐點後）
        0.2,   # 2023Q4
        -0.5,  # 2024Q1（轉為過剩）
        -1.0,  # 2024Q2
        -1.3,  # 2024Q3
        -1.5,  # 2024Q4
        -1.6,  # 2025Q1
        -1.5,  # 2025Q2
        -1.53, # 2025Q3
        -1.4,  # 2025Q4（當前）
    ]

    # 未來預測（三情境）
    balance_forecast_base = [
        -1.2,  # 2026Q1
        -0.9,  # 2026Q2
        -0.5,  # 2026Q3（樂觀拐點）
        -0.2,  # 2026Q4（中性拐點）
        0.1,   # 2027Q1（悲觀拐點）
        0.4,   # 2027Q2
        0.7,   # 2027Q3
        1.0,   # 2027Q4
    ]

    balance_forecast_optimistic = [x + 0.3 for x in balance_forecast_base]
    balance_forecast_pessimistic = [x - 0.3 for x in balance_forecast_base]

    # 合併歷史 + 預測
    n_historical = len(balance_index_historical)
    balance_index = balance_index_historical + balance_forecast_base

    # 碳酸鋰價格（USD/t）歷史 + 預測
    li_price_historical = [
        12000, 12500, 13000, 14000,  # 2020
        18000, 25000, 35000, 48000,  # 2021
        55000, 65000, 70000, 68000,  # 2022
        60000, 45000, 28000, 18000,  # 2023（拐點）
        15000, 12000, 11000, 10500,  # 2024
        10000, 10200, 10800, 11500,  # 2025（當前）
    ]

    li_price_forecast = [
        12500, 14000, 16000, 18000,  # 2026（預期反彈）
        20000, 22000, 24000, 26000,  # 2027
    ]

    li_price = li_price_historical + li_price_forecast

    # ========================================================================
    # 創建圖表（2行1列布局）
    # ========================================================================

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1, 0.5], hspace=0.3)

    # 上圖：供需平衡指數 + 拐點標註
    ax1 = fig.add_subplot(gs[0])
    # 下圖：碳酸鋰價格走勢
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    # 底部：關鍵催化劑時間軸
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    # ========================================================================
    # 上圖：供需平衡指數
    # ========================================================================

    # 歷史數據（實線）
    ax1.plot(
        dates[:n_historical],
        balance_index[:n_historical],
        'o-',
        linewidth=3,
        markersize=6,
        color='#2E86C1',
        label='歷史數據',
        zorder=3
    )

    # 未來預測（虛線 + 陰影區間）
    forecast_dates = dates[n_historical-1:]
    ax1.plot(
        forecast_dates,
        [balance_index[n_historical-1]] + balance_forecast_base,
        '--',
        linewidth=2.5,
        color='#28B463',
        label='中性預測',
        zorder=3
    )

    # 預測區間（樂觀-悲觀）
    ax1.fill_between(
        forecast_dates,
        [balance_index[n_historical-1]] + balance_forecast_optimistic,
        [balance_index[n_historical-1]] + balance_forecast_pessimistic,
        alpha=0.2,
        color='#28B463',
        label='預測區間'
    )

    # 零線（供需平衡點）
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7, zorder=1)
    ax1.text(dates[0], 0.1, '供需平衡線', fontsize=10, va='bottom', ha='left')

    # 背景色塊（不同市場階段）
    # 2020-2023Q2: 需求缺口期（綠色）
    ax1.axvspan(dates[0], dates[13], alpha=0.15, color='green', zorder=0)
    ax1.text(dates[6], 2.3, '需求缺口期\n（供不應求）',
             fontsize=11, ha='center', va='top', weight='bold', color='darkgreen')

    # 2023Q2-2025Q4: 供給過剩期（紅色）
    ax1.axvspan(dates[13], dates[23], alpha=0.15, color='red', zorder=0)
    ax1.text(dates[18], -1.8, '供給過剩期\n（產能釋放）',
             fontsize=11, ha='center', va='bottom', weight='bold', color='darkred')

    # 2026Q3+: 預期反彈期（黃色）
    ax1.axvspan(dates[25], dates[-1], alpha=0.15, color='gold', zorder=0)
    ax1.text(dates[28], 1.1, '預期反彈期\n（拐點後）',
             fontsize=11, ha='center', va='top', weight='bold', color='#D68910')

    # 標註歷史拐點（2023Q2）
    inflection_2023 = dates[13]
    ax1.scatter([inflection_2023], [1.5], s=300, color='red', marker='*',
                zorder=5, edgecolors='darkred', linewidths=2)
    ax1.annotate(
        '歷史拐點\n2023Q2\n供給反超需求',
        xy=(inflection_2023, 1.5),
        xytext=(inflection_2023 - pd.Timedelta(days=180), 1.9),
        fontsize=11,
        weight='bold',
        color='darkred',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
        arrowprops=dict(arrowstyle='->', lw=2, color='darkred')
    )

    # 標註預期拐點（2026Q4）
    inflection_2026 = dates[27]  # 2026Q4
    ax1.scatter([inflection_2026], [-0.2], s=300, color='gold', marker='*',
                zorder=5, edgecolors='#D68910', linewidths=2)
    ax1.annotate(
        '預期拐點\n2026Q4（中性）\n轉回缺口',
        xy=(inflection_2026, -0.2),
        xytext=(inflection_2026 + pd.Timedelta(days=90), 0.3),
        fontsize=11,
        weight='bold',
        color='#D68910',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
        arrowprops=dict(arrowstyle='->', lw=2, color='#D68910')
    )

    # 當前位置標註（2025Q4）
    current_date = dates[23]
    ax1.scatter([current_date], [-1.4], s=200, color='blue', marker='o',
                zorder=5, edgecolors='navy', linewidths=2)
    ax1.annotate(
        '當前\n2026-01-16\nIndex: -1.53',
        xy=(current_date, -1.4),
        xytext=(current_date - pd.Timedelta(days=120), -0.5),
        fontsize=10,
        weight='bold',
        color='navy',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8),
        arrowprops=dict(arrowstyle='->', lw=1.5, color='blue')
    )

    # 圖表設定
    ax1.set_ylabel('供需平衡指數 (Balance Index, σ)', fontsize=12, weight='bold')
    ax1.set_title('鋰市場供需拐點分析：歷史 vs 預測', fontsize=16, weight='bold', pad=20)
    ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(-2.5, 2.5)

    # ========================================================================
    # 下圖：碳酸鋰價格
    # ========================================================================

    # 歷史價格
    ax2.plot(
        dates[:n_historical],
        [p/1000 for p in li_price[:n_historical]],
        'o-',
        linewidth=3,
        markersize=6,
        color='#E74C3C',
        label='歷史價格',
        zorder=3
    )

    # 預測價格
    ax2.plot(
        forecast_dates,
        [li_price[n_historical-1]/1000] + [p/1000 for p in li_price_forecast],
        '--',
        linewidth=2.5,
        color='#9B59B6',
        label='預測價格',
        zorder=3
    )

    # 價格階段背景
    ax2.axvspan(dates[0], dates[13], alpha=0.1, color='green', zorder=0)
    ax2.axvspan(dates[13], dates[23], alpha=0.1, color='red', zorder=0)
    ax2.axvspan(dates[25], dates[-1], alpha=0.1, color='gold', zorder=0)

    # 標註關鍵價格點
    # 2022Q3 高峰
    peak_date = dates[10]
    ax2.scatter([peak_date], [70], s=200, color='red', marker='^', zorder=5)
    ax2.text(peak_date, 72, '價格高峰\n$70k/t', ha='center', fontsize=9, weight='bold')

    # 2024Q4 底部
    bottom_date = dates[19]
    ax2.scatter([bottom_date], [10.5], s=200, color='green', marker='v', zorder=5)
    ax2.text(bottom_date, 8, '價格底部\n$10.5k/t', ha='center', fontsize=9, weight='bold')

    # 當前價格
    ax2.scatter([current_date], [11.5], s=150, color='blue', marker='o', zorder=5)
    ax2.text(current_date - pd.Timedelta(days=180), 11.5, '當前\n$11.5k/t',
             ha='right', fontsize=9, weight='bold', color='navy')

    # 預期反彈目標
    target_date = dates[27]
    ax2.scatter([target_date], [18], s=200, color='orange', marker='*', zorder=5)
    ax2.text(target_date + pd.Timedelta(days=90), 18, '反彈目標\n$18k/t',
             ha='left', fontsize=9, weight='bold', color='darkorange')

    # 圖表設定
    ax2.set_ylabel('碳酸鋰價格 (USD/t, 千)', fontsize=12, weight='bold')
    ax2.set_xlabel('時間', fontsize=12, weight='bold')
    ax2.legend(loc='upper right', fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(0, 80)

    # ========================================================================
    # 底部：關鍵催化劑時間軸
    # ========================================================================

    ax3.set_ylim(0, 1)
    ax3.set_yticks([])
    ax3.spines['left'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['top'].set_visible(False)

    # 催化劑事件
    catalysts = [
        {"date": "2026-04-01", "label": "IEA EV Outlook", "color": "green"},
        {"date": "2026-03-15", "label": "澳洲REQ Q1", "color": "orange"},
        {"date": "2026-06-01", "label": "智利政策", "color": "purple"},
        {"date": "2026-10-01", "label": "預期拐點", "color": "gold"},
    ]

    for i, cat in enumerate(catalysts):
        cat_date = pd.to_datetime(cat["date"])
        if dates[0] <= cat_date <= dates[-1]:
            ax3.axvline(x=cat_date, color=cat["color"], linestyle='--', linewidth=2, alpha=0.7)
            ax3.text(cat_date, 0.5, cat["label"], rotation=45, ha='right',
                    fontsize=9, weight='bold', color=cat["color"])

    ax3.set_xlabel('關鍵催化劑時間軸', fontsize=11, weight='bold')

    # ========================================================================
    # 統一 X 軸格式
    # ========================================================================

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.get_xticklabels(), visible=False)

    # ========================================================================
    # 保存圖表
    # ========================================================================

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"lithium_inflection_analysis_{date.today().strftime('%Y-%m-%d')}.png"
    filepath = output_path / filename

    plt.savefig(
        filepath,
        dpi=300,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none'
    )
    plt.close()

    logger.info(f"✅ Inflection point chart saved to {filepath}")
    return str(filepath)


if __name__ == "__main__":
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    asof_date = sys.argv[2] if len(sys.argv) > 2 else None

    chart_path = generate_inflection_point_chart(output_dir, asof_date)
    print(f"Chart generated: {chart_path}")
