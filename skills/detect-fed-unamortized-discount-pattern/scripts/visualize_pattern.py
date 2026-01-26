#!/usr/bin/env python3
"""
形狀比對視覺化腳本

生成形狀比對圖表和壓力指標儀表板。
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[Warning] matplotlib 未安裝，無法生成圖表")

from fetch_data import fetch_fred_series, fetch_all_indicators
from pattern_detector import (
    Config, DEFAULT_BASELINE_WINDOWS, DEFAULT_CONFIRMATORY_INDICATORS,
    normalize, pearson_correlation, dtw_distance, extract_shape_features,
    feature_similarity, combine_similarity, calculate_stress_signal
)


def plot_pattern_comparison(
    recent: pd.Series,
    baseline: pd.Series,
    baseline_name: str,
    similarity_scores: Dict,
    output_path: Path
) -> None:
    """繪製形狀比對圖"""
    if not HAS_MATPLOTLIB:
        print("[Skip] matplotlib 未安裝")
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # 上圖：正規化後的形狀對比
    ax1 = axes[0]

    recent_n = normalize(recent, "zscore")
    baseline_n = normalize(baseline, "zscore")

    # 對齊 x 軸（使用相對週數）
    recent_x = np.arange(len(recent_n))
    baseline_x = np.arange(len(baseline_n))

    ax1.plot(recent_x, recent_n.values, 'b-', linewidth=2, label=f'近期 ({recent.index[0].strftime("%Y-%m-%d")} ~)')
    ax1.plot(baseline_x[:len(recent_x)], baseline_n.values[:len(recent_x)], 'r--', linewidth=2, alpha=0.7, label=f'{baseline_name}')

    ax1.set_xlabel('週數')
    ax1.set_ylabel('Z-Score (正規化)')
    ax1.set_title('形狀比對：近期 vs. 歷史基準（正規化後）')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 添加相似度標註
    score_text = f"相關係數: {similarity_scores.get('corr', 0):.2f}\n"
    score_text += f"DTW 距離: {similarity_scores.get('dtw', 0):.2f}\n"
    score_text += f"形狀特徵: {similarity_scores.get('feature_sim', 0):.2f}\n"
    score_text += f"綜合分數: {similarity_scores.get('pattern_similarity_score', 0):.2f}"

    ax1.text(0.98, 0.98, score_text, transform=ax1.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # 下圖：原始數值走勢
    ax2 = axes[1]

    ax2.plot(recent.index, recent.values, 'b-', linewidth=2, label='近期 (WUDSHO)')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('WUDSHO (Millions USD)', color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Saved] {output_path}")


def plot_stress_dashboard(
    stress_details: list,
    output_path: Path
) -> None:
    """繪製壓力指標儀表板"""
    if not HAS_MATPLOTLIB:
        print("[Skip] matplotlib 未安裝")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    names = [d['name'] for d in stress_details if d['signal'] != 'no_data']
    z_scores = [d['z'] for d in stress_details if d['signal'] != 'no_data']
    signals = [d['signal'] for d in stress_details if d['signal'] != 'no_data']

    # 顏色映射
    color_map = {
        'extreme_stress': 'darkred',
        'stress': 'red',
        'mild_stress': 'orange',
        'neutral': 'gray',
        'mild_risk_on': 'lightgreen'
    }
    colors = [color_map.get(s, 'gray') for s in signals]

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, z_scores, color=colors, alpha=0.8)

    # 添加門檻線
    ax.axvline(x=1.5, color='red', linestyle='--', linewidth=1, label='壓力門檻 (+1.5)')
    ax.axvline(x=-1.5, color='red', linestyle='--', linewidth=1)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel('Z-Score')
    ax.set_title('壓力驗證指標儀表板')
    ax.legend(loc='lower right')
    ax.grid(True, axis='x', alpha=0.3)

    # 添加數值標籤
    for i, (bar, z) in enumerate(zip(bars, z_scores)):
        width = bar.get_width()
        ax.text(width + 0.1 if width >= 0 else width - 0.1,
                bar.get_y() + bar.get_height()/2,
                f'{z:.2f}',
                ha='left' if width >= 0 else 'right',
                va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Saved] {output_path}")


def plot_historical_overlay(
    full_series: pd.Series,
    baseline_windows: list,
    recent_start: datetime,
    output_path: Path
) -> None:
    """繪製歷史走勢對照圖"""
    if not HAS_MATPLOTLIB:
        print("[Skip] matplotlib 未安裝")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # 繪製完整走勢
    ax.plot(full_series.index, full_series.values, 'b-', linewidth=1, alpha=0.8, label='WUDSHO')

    # 標記基準窗口
    colors = ['red', 'orange', 'green', 'purple']
    for i, win in enumerate(baseline_windows):
        start = pd.Timestamp(win.start)
        end = pd.Timestamp(win.end)
        ax.axvspan(start, end, alpha=0.2, color=colors[i % len(colors)], label=win.name)

    # 標記近期窗口
    ax.axvspan(recent_start, full_series.index[-1], alpha=0.3, color='yellow', label='近期窗口')

    ax.set_xlabel('日期')
    ax.set_ylabel('WUDSHO (Millions USD)')
    ax.set_title('WUDSHO 歷史走勢與基準窗口標記')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Saved] {output_path}")


def main():
    parser = argparse.ArgumentParser(description="形狀比對視覺化腳本")
    parser.add_argument("-o", "--output", type=str, default="output",
                        help="輸出目錄")
    parser.add_argument("--target_series", type=str, default="WUDSHO",
                        help="目標序列")
    parser.add_argument("--recent_days", type=int, default=120,
                        help="近期窗口天數")
    parser.add_argument("--baseline", type=str, default="COVID_2020",
                        help="基準窗口名稱")

    args = parser.parse_args()

    if not HAS_MATPLOTLIB:
        print("[Error] matplotlib 未安裝，無法生成圖表")
        print("請執行: pip install matplotlib")
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")

    # 抓取資料
    print("[Step 1] 抓取資料...")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2015-01-01"

    all_data = fetch_all_indicators(start_date, end_date)
    target_data = all_data.get(args.target_series, pd.Series())

    if target_data.empty:
        print(f"[Error] 無法取得 {args.target_series} 資料")
        return

    # 重採樣至週頻
    target_data = target_data.resample("W-FRI").last().dropna()

    # 切出窗口
    recent_start = datetime.now() - timedelta(days=args.recent_days)
    recent = target_data[target_data.index >= recent_start]

    # 找出基準窗口
    baseline_win = None
    for win in DEFAULT_BASELINE_WINDOWS:
        if win.name == args.baseline:
            baseline_win = win
            break

    if baseline_win is None:
        print(f"[Error] 找不到基準窗口: {args.baseline}")
        return

    baseline_data = target_data[(target_data.index >= baseline_win.start) & (target_data.index <= baseline_win.end)]

    # 計算相似度
    print("[Step 2] 計算相似度...")
    recent_n = normalize(recent, "zscore")
    baseline_n = normalize(baseline_data[:len(recent)], "zscore")

    corr = pearson_correlation(recent_n.values, baseline_n.values)
    dtw_dist = dtw_distance(recent_n.values, baseline_n.values)
    feat_recent = extract_shape_features(recent_n.values)
    feat_baseline = extract_shape_features(baseline_n.values)
    feat_sim = feature_similarity(feat_recent, feat_baseline)
    pattern_score = combine_similarity(corr, dtw_dist, feat_sim, {"corr": 0.4, "dtw": 0.3, "shape_features": 0.3})

    similarity_scores = {
        "corr": corr,
        "dtw": dtw_dist,
        "feature_sim": feat_sim,
        "pattern_similarity_score": pattern_score
    }

    # 生成圖表
    print("[Step 3] 生成圖表...")

    # 形狀比對圖
    plot_pattern_comparison(
        recent, baseline_data[:len(recent)], args.baseline,
        similarity_scores,
        output_dir / f"pattern_comparison_{date_str}.png"
    )

    # 壓力指標儀表板
    stress_details = []
    for indicator in DEFAULT_CONFIRMATORY_INDICATORS:
        if indicator.series == "yield_curve":
            ind_data = all_data.get("yield_curve", pd.Series())
        else:
            ind_data = all_data.get(indicator.series, pd.Series())
        result = calculate_stress_signal(ind_data, indicator)
        stress_details.append(result)

    plot_stress_dashboard(
        stress_details,
        output_dir / f"stress_dashboard_{date_str}.png"
    )

    # 歷史走勢對照
    plot_historical_overlay(
        target_data, DEFAULT_BASELINE_WINDOWS, recent_start,
        output_dir / f"historical_overlay_{date_str}.png"
    )

    # 儲存分析結果
    result = {
        "as_of_date": date_str,
        "target_series": args.target_series,
        "baseline": args.baseline,
        "similarity_scores": similarity_scores,
        "stress_details": stress_details
    }

    with open(output_dir / f"pattern_analysis_{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[Done] 所有圖表已儲存至: {output_dir}")


if __name__ == "__main__":
    main()
