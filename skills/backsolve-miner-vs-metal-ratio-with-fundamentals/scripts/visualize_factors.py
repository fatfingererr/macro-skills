#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
礦業股/金屬比率因子拆解視覺化

生成四面板儀表板：
1. 比率時間序列 + 分位數區間
2. 四大因子儀表板（雷達圖）
3. 因子健康度長條圖
4. 反推情境熱力圖

Usage:
    python visualize_factors.py --quick
    python visualize_factors.py --input result.json --output output/
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use('Agg')  # 無頭模式，避免 GUI 問題
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配色方案
COLORS = {
    'primary': '#2E86AB',      # 藍
    'secondary': '#A23B72',    # 紫紅
    'success': '#28A745',      # 綠
    'warning': '#F18F01',      # 橙
    'danger': '#C73E1D',       # 紅
    'neutral': '#6C757D',      # 灰
    'background': '#F8F9FA',
    'grid': '#E9ECEF',
    'text': '#212529',
    'bottom_zone': '#FFEBEE',  # 淡紅
    'top_zone': '#E8F5E9',     # 淡綠
    'neutral_zone': '#FFF8E1', # 淡黃
}


def fetch_ratio_history(
    metal_symbol: str = "SI=F",
    miner_symbol: str = "SIL",
    start_date: str = "",
    end_date: str = ""
) -> pd.DataFrame:
    """取得比率歷史數據"""
    if yf is None:
        raise ImportError("yfinance is required")

    if not start_date:
        start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 下載數據（分開下載避免批次問題）
    metal = yf.download(metal_symbol, start=start_date, end=end_date, interval="1wk", progress=False)
    miner = yf.download(miner_symbol, start=start_date, end=end_date, interval="1wk", progress=False)

    if metal.empty or miner.empty:
        raise ValueError(f"無法取得數據: metal={metal_symbol}, miner={miner_symbol}")

    # 處理 MultiIndex
    if isinstance(metal.columns, pd.MultiIndex):
        metal_close = metal['Close'].iloc[:, 0] if isinstance(metal['Close'], pd.DataFrame) else metal['Close']
    else:
        metal_close = metal['Close']

    if isinstance(miner.columns, pd.MultiIndex):
        miner_close = miner['Close'].iloc[:, 0] if isinstance(miner['Close'], pd.DataFrame) else miner['Close']
    else:
        miner_close = miner['Close']

    common = metal_close.index.intersection(miner_close.index)
    if len(common) == 0:
        raise ValueError("金屬與礦業股日期無交集")

    df = pd.DataFrame({
        'metal': metal_close.loc[common],
        'miner': miner_close.loc[common],
    })
    df['ratio'] = df['miner'] / df['metal']
    df = df.dropna()

    return df


def plot_ratio_timeseries(ax, df: pd.DataFrame, thresholds: dict, current: dict):
    """繪製比率時間序列圖"""
    ratio = df['ratio']
    dates = df.index

    # 填充區間
    ax.fill_between(dates, 0, thresholds['bottom_ratio'],
                    color=COLORS['bottom_zone'], alpha=0.5, label='底部區間')
    ax.fill_between(dates, thresholds['bottom_ratio'], thresholds['top_ratio'],
                    color=COLORS['neutral_zone'], alpha=0.3, label='中性區間')
    ax.fill_between(dates, thresholds['top_ratio'], ratio.max() * 1.1,
                    color=COLORS['top_zone'], alpha=0.5, label='頂部區間')

    # 比率線
    ax.plot(dates, ratio, color=COLORS['primary'], linewidth=1.5, label='比率')

    # 門檻線
    ax.axhline(thresholds['bottom_ratio'], color=COLORS['danger'], linestyle='--',
               linewidth=1, alpha=0.7)
    ax.axhline(thresholds['median_ratio'], color=COLORS['neutral'], linestyle=':',
               linewidth=1, alpha=0.7)
    ax.axhline(thresholds['top_ratio'], color=COLORS['success'], linestyle='--',
               linewidth=1, alpha=0.7)

    # 當前點
    ax.scatter([dates[-1]], [current['ratio']], color=COLORS['danger'],
               s=100, zorder=5, edgecolors='white', linewidths=2)
    ax.annotate(f"{current['ratio']:.2f}\n({current['ratio_percentile']:.0%})",
                xy=(dates[-1], current['ratio']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=9, fontweight='bold', color=COLORS['danger'])

    # 標註門檻值
    ax.text(dates[0], thresholds['bottom_ratio'], f" 底部 {thresholds['bottom_ratio']:.2f}",
            va='center', fontsize=8, color=COLORS['danger'])
    ax.text(dates[0], thresholds['top_ratio'], f" 頂部 {thresholds['top_ratio']:.2f}",
            va='center', fontsize=8, color=COLORS['success'])

    ax.set_title('SIL / 白銀價格比率', fontsize=12, fontweight='bold')
    ax.set_ylabel('比率')
    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(ratio.min() * 0.95, ratio.max() * 1.05)
    ax.grid(True, alpha=0.3)


def plot_factor_radar(ax, factors: dict):
    """繪製四大因子雷達圖"""
    categories = ['成本因子\n(C)', '槓桿因子\n(1-L)', '倍數因子\n(M)', '稀釋因子\n(D)']

    # 正規化因子值到 0-1 範圍
    # C: 0-1 直接使用
    # 1-L: 0-1.5 正規化
    # M: 4-12 正規化 (反向，越低越好要反轉)
    # D: 0.7-1.3 正規化

    C_norm = min(1, max(0, factors['cost_factor_C']))
    L_norm = min(1, max(0, factors['leverage_factor_1_minus_L'] / 1.2))
    M_norm = min(1, max(0, (12 - factors['multiple_M']) / 8))  # 反向：M 越低，正規化值越高
    D_norm = min(1, max(0, (factors['dilution_discount_D'] - 0.7) / 0.6))

    values = [C_norm, L_norm, M_norm, D_norm]
    values += values[:1]  # 閉合

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    # 繪製雷達圖
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 背景圓環
    for i in [0.25, 0.5, 0.75, 1.0]:
        ax.plot(angles, [i] * len(angles), color=COLORS['grid'], linewidth=0.5)

    # 數據區域
    ax.fill(angles, values, color=COLORS['primary'], alpha=0.25)
    ax.plot(angles, values, color=COLORS['primary'], linewidth=2)

    # 數據點
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.scatter(angle, value, color=COLORS['primary'], s=60, zorder=5)

    # 標籤
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['差', '中', '良', '優'], fontsize=7)

    ax.set_title('四大因子健康度', fontsize=12, fontweight='bold', pad=15)


def plot_factor_bars(ax, factors: dict, fundamentals: dict):
    """繪製因子健康度長條圖"""
    labels = ['成本因子 C', '槓桿因子 (1-L)', '倍數吸引力', '稀釋因子 D']

    # 計算健康度分數 (0-100)
    C_score = factors['cost_factor_C'] * 100
    L_score = min(100, factors['leverage_factor_1_minus_L'] * 100)

    # 倍數：7x 附近最佳，偏離越多分數越低
    M = factors['multiple_M']
    M_score = max(0, 100 - abs(M - 7) * 15)  # 7x 為 100 分

    D_score = min(100, factors['dilution_discount_D'] * 100)

    scores = [C_score, L_score, M_score, D_score]

    # 顏色根據分數
    colors = []
    for s in scores:
        if s >= 70:
            colors.append(COLORS['success'])
        elif s >= 40:
            colors.append(COLORS['warning'])
        else:
            colors.append(COLORS['danger'])

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, scores, color=colors, height=0.6, edgecolor='white', linewidth=1)

    # 標註數值
    details = [
        f"AISC ${fundamentals['aisc_usd_per_oz']:.1f}/oz",
        f"NetDebt/EV {fundamentals['net_debt_to_ev']:.1%}",
        f"EV/EBITDA {factors['multiple_M']:.1f}x",
        f"股數 YoY {fundamentals['shares_yoy_change']:+.1%}"
    ]

    for i, (bar, score, detail) in enumerate(zip(bars, scores, details)):
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2,
                f'{score:.0f}', va='center', fontsize=9, fontweight='bold')
        ax.text(5, bar.get_y() + bar.get_height()/2,
                detail, va='center', fontsize=8, color='white', fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 110)
    ax.set_xlabel('健康度分數')
    ax.axvline(70, color=COLORS['success'], linestyle='--', alpha=0.5, linewidth=1)
    ax.axvline(40, color=COLORS['warning'], linestyle='--', alpha=0.5, linewidth=1)

    # 圖例
    legend_elements = [
        mpatches.Patch(color=COLORS['success'], label='健康 (≥70)'),
        mpatches.Patch(color=COLORS['warning'], label='注意 (40-70)'),
        mpatches.Patch(color=COLORS['danger'], label='警戒 (<40)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

    ax.set_title('因子健康度評分', fontsize=12, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)


def plot_backsolve_heatmap(ax, backsolve: dict, current_ratio: float):
    """繪製反推情境熱力圖"""
    # 從 two_factor_grid 提取數據
    grid = backsolve.get('two_factor_grid', [])

    # 建立網格
    m_changes = sorted(set(g['multiple_change'] for g in grid))
    s_changes = sorted(set(g['metal_change'] for g in grid), reverse=True)

    # 建立矩陣
    matrix = np.zeros((len(s_changes), len(m_changes)))

    for g in grid:
        i = s_changes.index(g['metal_change'])
        j = m_changes.index(g['multiple_change'])
        matrix[i, j] = g['achieved_multiplier']

    # 繪製熱力圖
    target_mult = backsolve['ratio_multiplier']

    # 自定義顏色映射
    cmap = plt.cm.RdYlGn
    im = ax.imshow(matrix, cmap=cmap, aspect='auto',
                   vmin=0.9, vmax=max(1.5, target_mult * 1.1))

    # 標註
    for i in range(len(s_changes)):
        for j in range(len(m_changes)):
            val = matrix[i, j]
            color = 'white' if val >= target_mult else 'black'
            symbol = '✓' if val >= target_mult else ''
            ax.text(j, i, f'{val:.2f}\n{symbol}', ha='center', va='center',
                    fontsize=8, color=color, fontweight='bold')

    # 軸標籤
    ax.set_xticks(np.arange(len(m_changes)))
    ax.set_yticks(np.arange(len(s_changes)))
    ax.set_xticklabels([f'+{int(m*100)}%' for m in m_changes], fontsize=8)
    ax.set_yticklabels([f'{int(s*100):+}%' for s in s_changes], fontsize=8)

    ax.set_xlabel('倍數擴張幅度', fontsize=9)
    ax.set_ylabel('白銀價格變化', fontsize=9)

    # 標題含目標
    target_ratio = backsolve['target_ratio']
    ax.set_title(f'情境分析：達到比率 {target_ratio:.2f} (需 {target_mult:.2f}x)',
                 fontsize=11, fontweight='bold')

    # 色條
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('達成倍數', fontsize=8)

    # 標記目標線
    cbar.ax.axhline(target_mult, color='red', linewidth=2)


def create_dashboard(
    analysis_result: dict,
    ratio_history: pd.DataFrame,
    output_path: str
):
    """創建四面板儀表板"""
    fig = plt.figure(figsize=(16, 12), facecolor=COLORS['background'])
    fig.suptitle(
        f"SIL/白銀比率因子拆解分析 — {analysis_result['now']['date']}",
        fontsize=16, fontweight='bold', y=0.98
    )

    # 2x2 佈局
    gs = fig.add_gridspec(2, 2, hspace=0.25, wspace=0.25,
                          left=0.06, right=0.94, top=0.92, bottom=0.06)

    # 1. 比率時間序列（左上）
    ax1 = fig.add_subplot(gs[0, 0])
    plot_ratio_timeseries(ax1, ratio_history,
                          analysis_result['thresholds'],
                          analysis_result['now'])

    # 2. 因子雷達圖（右上）
    ax2 = fig.add_subplot(gs[0, 1], projection='polar')
    plot_factor_radar(ax2, analysis_result['factors_now'])

    # 3. 因子健康度長條圖（左下）
    ax3 = fig.add_subplot(gs[1, 0])
    plot_factor_bars(ax3, analysis_result['factors_now'],
                     analysis_result['fundamentals_weighted'])

    # 4. 反推情境熱力圖（右下）
    ax4 = fig.add_subplot(gs[1, 1])
    plot_backsolve_heatmap(ax4, analysis_result['backsolve_to_top'],
                           analysis_result['now']['ratio'])

    # 添加摘要文字
    summary = analysis_result.get('summary', '')
    zone = analysis_result['now']['zone']
    percentile = analysis_result['now']['ratio_percentile']

    zone_cn = {'bottom': '底部', 'low': '低位', 'neutral': '中性', 'high': '高位', 'top': '頂部'}
    summary_text = (
        f"當前區間: {zone_cn.get(zone, zone)} ({percentile:.1%} 分位) | "
        f"主要驅動: 倍數壓縮 | "
        f"AISC: ${analysis_result['fundamentals_weighted']['aisc_usd_per_oz']:.1f}/oz | "
        f"EV/EBITDA: {analysis_result['factors_now']['multiple_M']:.1f}x"
    )
    fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10,
             style='italic', color=COLORS['neutral'])

    # 保存
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()

    print(f"圖表已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="礦業股/金屬比率因子視覺化")
    parser.add_argument("--quick", action="store_true", help="快速模式")
    parser.add_argument("--input", type=str, help="分析結果 JSON 檔案")
    parser.add_argument("--output", type=str, default="output/", help="輸出目錄")
    args = parser.parse_args()

    # 確保輸出目錄存在
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 日期標記
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"sil_silver_factor_analysis_{today}.png"

    if args.input and Path(args.input).exists():
        # 從 JSON 載入
        with open(args.input, 'r', encoding='utf-8') as f:
            result = json.load(f)
    else:
        # 快速模式：執行分析
        print("執行快速分析...")
        import sys
        script_dir = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from fundamental_analyzer import run_analysis, AnalyzerConfig
        config = AnalyzerConfig()
        result = run_analysis(config)

    # 取得比率歷史
    print("取得比率歷史數據...")
    ratio_history = fetch_ratio_history(
        result['inputs']['metal_symbol'],
        result['inputs']['miner_universe']['etf_ticker']
    )

    # 創建儀表板
    print("生成視覺化儀表板...")
    create_dashboard(result, ratio_history, str(output_file))


if __name__ == "__main__":
    main()
