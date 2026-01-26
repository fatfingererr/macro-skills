#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRE-COVID 形狀比對與推估走勢視覺化
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'PingFang TC', 'Noto Sans CJK TC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from fetch_data import fetch_all_indicators
from pattern_detector import normalize, find_best_match, BaselineWindow

# Bloomberg 風格配色
COLORS = {
    'background': '#1a1a2e',
    'grid': '#2d2d44',
    'text': '#ffffff',
    'text_dim': '#888888',
    'primary': '#ff6b35',
    'secondary': '#ffaa00',
    'tertiary': '#ffff00',
    'recent': '#00d4ff',
    'baseline': '#ff6b35',
    'box_bg': '#2d2d44',
    'stress': '#ff4444',
    'mild_risk_on': '#00ff88',
}

def format_millions(x, pos):
    if abs(x) >= 1e9:
        return f'{x/1e9:.1f}B'
    elif abs(x) >= 1e6:
        return f'{x/1e6:.0f}M'
    elif abs(x) >= 1e3:
        return f'{x/1e3:.0f}K'
    else:
        return f'{x:.0f}'


def main():
    # 抓取資料
    print('[Step 1] 抓取資料...')
    all_data = fetch_all_indicators('2015-01-01', datetime.now().strftime('%Y-%m-%d'))
    wudsho = all_data.get('WUDSHO', pd.Series())
    wudsho = wudsho.resample('W-FRI').last().dropna()

    # 定義 PRE_COVID 窗口
    pre_covid_start = '2019-09-01'
    pre_covid_end = '2020-02-15'

    # 近期窗口
    recent_start = datetime.now() - timedelta(days=120)
    recent = wudsho[wudsho.index >= recent_start]

    # PRE_COVID 資料
    pre_covid_data = wudsho[(wudsho.index >= pre_covid_start) & (wudsho.index <= pre_covid_end)]

    # 形狀比對
    print('[Step 2] 形狀比對...')
    match = find_best_match(recent, pre_covid_data, 'zscore', {'corr': 0.4, 'dtw': 0.3, 'shape_features': 0.3})
    match['baseline'] = 'PRE_COVID'
    print(f"  相關係數: {match['corr']:.2f}")
    print(f"  形狀相似度: {match['pattern_similarity_score']:.2f}")

    seg_start = pd.Timestamp(match['segment_start'])
    seg_end = pd.Timestamp(match['segment_end'])

    # 計算推估走勢（基於 COVID 後實際發生的情況）
    print('[Step 3] 計算推估走勢...')

    projection_values = []
    projection_dates = []

    # 找到匹配片段在完整資料中的位置
    seg_end_idx = None
    for i, idx in enumerate(wudsho.index):
        if idx >= seg_end:
            seg_end_idx = i
            break

    latest_value = wudsho.iloc[-1]
    latest_date = wudsho.index[-1]

    if seg_end_idx is not None:
        # 取 COVID 爆發後的完整走勢（先大漲再下跌）
        # 需要足夠長的時間來捕捉完整週期：上漲 + 下跌
        lookahead_weeks = 156  # 約 3 年，足以涵蓋完整的 COVID 週期

        # 確保不超出可用資料
        max_available = len(wudsho) - seg_end_idx - 1
        lookahead_weeks = min(lookahead_weeks, max_available)

        subsequent = wudsho.iloc[seg_end_idx + 1:seg_end_idx + 1 + lookahead_weeks]

        if len(subsequent) > 0:
            # 使用匹配片段結束點的值作為基準
            baseline_end_value = wudsho.iloc[seg_end_idx]

            print(f"  匹配片段結束值: {baseline_end_value:.0f}")
            print(f"  後續走勢最高點: {subsequent.max():.0f}")
            print(f"  後續走勢最低點: {subsequent.min():.0f}")
            print(f"  後續走勢長度: {len(subsequent)} 週")

            # 計算歷史走勢的「絕對變化量」，然後按比例縮放到當前值
            # 這樣可以保持走勢的形狀（先漲後跌）
            historical_changes = subsequent.values - baseline_end_value

            # 計算縮放比例：讓變化幅度與當前值成比例
            # 使用歷史最大變化幅度來計算比例
            max_historical_change = np.max(np.abs(historical_changes))
            if max_historical_change > 0:
                # 縮放因子：讓推估的最大變化與當前值的絕對值成正比
                scale_factor = abs(latest_value) / abs(baseline_end_value) if baseline_end_value != 0 else 1.0
            else:
                scale_factor = 1.0

            projection_values = [latest_value]
            projection_dates = [latest_date]

            for i, hist_change in enumerate(historical_changes):
                proj_date = latest_date + pd.Timedelta(weeks=i+1)
                # 將歷史變化按比例應用到當前值
                proj_value = latest_value + (hist_change * scale_factor)
                projection_dates.append(proj_date)
                projection_values.append(proj_value)

            print(f"  推估起點: {projection_values[0]:.0f}")
            print(f"  推估最高點: {max(projection_values):.0f}")
            print(f"  推估終點: {projection_values[-1]:.0f}")

    # 繪圖
    print('[Step 4] 生成圖表...')
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=COLORS['background'])
    ax.set_facecolor(COLORS['background'])

    # 繪製歷史走勢
    ax.plot(wudsho.index, wudsho.values,
            color=COLORS['primary'],
            linewidth=2,
            alpha=0.9,
            label='WUDSHO 實際走勢',
            zorder=3)

    # 繪製推估走勢
    if len(projection_dates) > 1:
        ax.plot(projection_dates, projection_values,
                color=COLORS['tertiary'],
                linewidth=2.5,
                linestyle='--',
                alpha=0.9,
                label='推估走勢（若重演 COVID 前後模式）',
                zorder=4)

        # 不確定性區間
        proj_upper = [v * 1.15 for v in projection_values]
        proj_lower = [v * 0.85 for v in projection_values]
        ax.fill_between(projection_dates, proj_lower, proj_upper,
                        color=COLORS['tertiary'],
                        alpha=0.15,
                        zorder=2)

    # 標記 PRE_COVID 匹配片段
    ax.axvspan(seg_start, seg_end,
               alpha=0.3,
               color=COLORS['secondary'],
               hatch='///',
               label=f'歷史類比片段 ({seg_start.strftime("%Y-%m")} ~ {seg_end.strftime("%Y-%m")})',
               zorder=1)

    # 標記近期窗口
    ax.axvspan(recent_start, wudsho.index[-1],
               alpha=0.25,
               color=COLORS['recent'],
               label='近期走勢',
               zorder=1)

    # 標記 COVID 爆發點
    covid_crash_start = pd.Timestamp('2020-02-20')
    ax.axvline(covid_crash_start, color=COLORS['stress'], linestyle=':', linewidth=2, alpha=0.8)
    ax.text(covid_crash_start, wudsho.max() * 0.95, 'COVID\n爆發',
            color=COLORS['stress'], fontsize=10, fontweight='bold',
            ha='center', va='top')

    # 資訊框
    if len(projection_values) > 1:
        peak_value = max(projection_values)
        peak_idx = projection_values.index(peak_value)
        peak_weeks = peak_idx  # 幾週後達到高點

        info_text = (
            f"【PRE_COVID 比對分析】\n"
            f"─────────────\n"
            f"匹配片段: {seg_start.strftime('%Y-%m-%d')} ~\n"
            f"          {seg_end.strftime('%Y-%m-%d')}\n"
            f"相關係數: {match['corr']:.2f}\n"
            f"形狀相似度: {match['pattern_similarity_score']:.2f}\n"
            f"─────────────\n"
            f"若歷史重演：\n"
            f"  當前值: {latest_value/1e3:.0f}K\n"
            f"  高點({peak_weeks}週後): {peak_value/1e3:.0f}K\n"
            f"  終點: {projection_values[-1]/1e3:.0f}K\n"
            f"─────────────\n"
            f"注意：壓力指標偏中性\n"
            f"   形狀相似 ≠ 事件重演"
        )
    else:
        info_text = (
            f"【PRE_COVID 比對分析】\n"
            f"─────────────\n"
            f"匹配片段: {seg_start.strftime('%Y-%m-%d')} ~\n"
            f"          {seg_end.strftime('%Y-%m-%d')}\n"
            f"相關係數: {match['corr']:.2f}\n"
            f"形狀相似度: {match['pattern_similarity_score']:.2f}\n"
            f"─────────────\n"
            f"注意：壓力指標偏中性\n"
            f"   形狀相似 ≠ 事件重演"
        )

    ax.text(0.02, 0.98, info_text,
            transform=ax.transAxes,
            fontsize=10,
            color=COLORS['text'],
            verticalalignment='top',
            horizontalalignment='left',
            fontfamily='Microsoft JhengHei',
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor=COLORS['box_bg'],
                      edgecolor=COLORS['secondary'],
                      linewidth=2,
                      alpha=0.95))

    # 標註最新值
    ax.annotate(
        f'當前: {latest_value/1e3:.0f}K',
        xy=(latest_date, latest_value),
        xytext=(-80, 20),
        textcoords='offset points',
        color=COLORS['primary'],
        fontsize=11,
        fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=COLORS['primary'], lw=1.5))

    # 標註推估高點和終點
    if len(projection_values) > 1:
        # 找高點
        peak_value = max(projection_values)
        peak_idx = projection_values.index(peak_value)
        peak_date = projection_dates[peak_idx]

        # 標註高點
        if peak_idx > 0 and peak_idx < len(projection_values) - 1:
            ax.annotate(
                f'推估高點 ({peak_idx}週後)\n{peak_value/1e3:.0f}K',
                xy=(peak_date, peak_value),
                xytext=(0, 40),
                textcoords='offset points',
                color=COLORS['mild_risk_on'],
                fontsize=10,
                fontweight='bold',
                ha='center',
                arrowprops=dict(arrowstyle='->', color=COLORS['mild_risk_on'], lw=1.5))

        # 標註終點
        final_date = projection_dates[-1]
        final_value = projection_values[-1]
        total_weeks = len(projection_values) - 1
        ax.annotate(
            f'推估終點 ({total_weeks}週後)\n{final_value/1e3:.0f}K',
            xy=(final_date, final_value),
            xytext=(10, -30),
            textcoords='offset points',
            color=COLORS['tertiary'],
            fontsize=10,
            fontweight='bold',
            ha='left',
            arrowprops=dict(arrowstyle='->', color=COLORS['tertiary'], lw=1.5))

    # 軸設定
    ax.grid(True, color=COLORS['grid'], alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlabel('日期', color=COLORS['text_dim'], fontsize=11)
    ax.set_ylabel('WUDSHO (Millions USD)', color=COLORS['text_dim'], fontsize=11)
    ax.tick_params(axis='both', colors=COLORS['text_dim'], labelsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(format_millions))

    # 圖例
    ax.legend(loc='lower right', fontsize=9,
              facecolor=COLORS['box_bg'],
              edgecolor=COLORS['grid'],
              labelcolor=COLORS['text'])

    # 標題
    fig.suptitle('聯準會未攤銷折價（WUDSHO）：PRE-COVID 形狀比對與推估',
                 color=COLORS['text'],
                 fontsize=15,
                 fontweight='bold',
                 y=0.98)

    # 頁尾
    fig.text(0.02, 0.02,
             '資料來源: FRED',
             color=COLORS['text_dim'],
             fontsize=9)
    fig.text(0.98, 0.02,
             f'截至: {latest_date.strftime("%Y-%m-%d")}',
             color=COLORS['text_dim'],
             fontsize=9,
             ha='right')

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    # 儲存
    script_dir = Path(__file__).parent
    output_path = script_dir.parent.parent.parent.parent / 'output' / f'wudsho_pre_covid_projection_{datetime.now().strftime("%Y-%m-%d")}.png'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()

    print(f'[Saved] {output_path}')


if __name__ == "__main__":
    main()
