#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聯準會未攤銷折價走勢模式偵測 - Bloomberg 風格視覺化

生成形狀比對圖表和壓力指標儀表板。
遵循 Bloomberg Intelligence 風格設計規範。
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前設定

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle

# 中文字體設定
plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',  # Windows 正黑體
    'SimHei',              # Windows 黑體
    'Microsoft YaHei',     # Windows 微軟雅黑
    'PingFang TC',         # macOS 蘋方
    'Noto Sans CJK TC',    # Linux/通用
    'DejaVu Sans'          # 備用
]
plt.rcParams['axes.unicode_minus'] = False

from fetch_data import fetch_all_indicators
from pattern_detector import (
    Config, DEFAULT_BASELINE_WINDOWS, DEFAULT_CONFIRMATORY_INDICATORS,
    normalize, pearson_correlation, dtw_distance, extract_shape_features,
    feature_similarity, combine_similarity, calculate_stress_signal,
    find_best_match, aggregate_stress_scores
)

# ============================================================================
# Bloomberg 風格配色
# ============================================================================

BLOOMBERG_COLORS = {
    # 背景與網格
    "background": "#1a1a2e",      # 深藍黑色背景
    "grid": "#2d2d44",            # 暗灰紫網格線

    # 文字
    "text": "#ffffff",            # 主要文字（白色）
    "text_dim": "#888888",        # 次要文字（灰色）

    # 主要數據線
    "primary": "#ff6b35",         # 橙紅色（主要指標）
    "secondary": "#ffaa00",       # 橙黃色（次要指標/均線）
    "tertiary": "#ffff00",        # 黃色（第三指標）

    # 比對線
    "recent": "#00d4ff",          # 青藍色（近期走勢）
    "baseline": "#ff6b35",        # 橙紅色（歷史基準）

    # 壓力指標顏色
    "extreme_stress": "#ff0000",  # 紅色（極端壓力）
    "stress": "#ff4444",          # 橙紅色（壓力）
    "mild_stress": "#ff8c00",     # 橙色（輕度壓力）
    "neutral": "#666666",         # 灰色（中性）
    "mild_risk_on": "#00ff88",    # 綠色（輕度風險偏好）

    # 輔助元素
    "level_line": "#666666",      # 關卡/水平線
    "annotation": "#ffffff",      # 標註文字
    "box_bg": "#2d2d44",          # 資訊框背景
}


# ============================================================================
# 格式化函數
# ============================================================================

def format_millions(x, pos):
    """百萬格式化"""
    if abs(x) >= 1e9:
        return f'{x/1e9:.1f}B'
    elif abs(x) >= 1e6:
        return f'{x/1e6:.0f}M'
    elif abs(x) >= 1e3:
        return f'{x/1e3:.0f}K'
    else:
        return f'{x:.0f}'


def format_zscore(x, pos):
    """Z-Score 格式化"""
    return f'{x:.1f}'


def get_risk_color(score: float) -> str:
    """根據風險分數取得顏色"""
    if score >= 0.7:
        return BLOOMBERG_COLORS["extreme_stress"]
    elif score >= 0.5:
        return BLOOMBERG_COLORS["stress"]
    elif score >= 0.3:
        return BLOOMBERG_COLORS["mild_stress"]
    else:
        return BLOOMBERG_COLORS["mild_risk_on"]


def get_signal_color(signal: str) -> str:
    """根據訊號取得顏色"""
    return BLOOMBERG_COLORS.get(signal, BLOOMBERG_COLORS["neutral"])


# ============================================================================
# 主圖表：形狀比對與壓力儀表板
# ============================================================================

def plot_pattern_analysis(
    recent: pd.Series,
    baseline_segment: pd.Series,
    best_match: Dict,
    stress_details: List[Dict],
    stress_score: float,
    composite_score: float,
    output_path: Path,
    title: str = "聯準會未攤銷折價走勢模式偵測"
) -> None:
    """
    繪製綜合分析圖表（Bloomberg 風格）

    上半部：形狀比對（近期 vs 最佳匹配歷史片段）
    下半部：壓力指標儀表板
    """
    plt.style.use('dark_background')

    fig = plt.figure(figsize=(14, 10), facecolor=BLOOMBERG_COLORS["background"])

    # 建立 GridSpec 佈局
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[1.2, 1],
        width_ratios=[2, 1],
        hspace=0.25,
        wspace=0.15
    )

    # === 上左：形狀比對圖 ===
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BLOOMBERG_COLORS["background"])

    # 正規化資料
    recent_n = normalize(recent, "zscore")
    baseline_n = normalize(baseline_segment, "zscore")

    # 對齊 x 軸（使用相對週數）
    n_points = min(len(recent_n), len(baseline_n))
    x = np.arange(n_points)

    # 繪製走勢
    ax1.plot(x, recent_n.values[:n_points],
             color=BLOOMBERG_COLORS["recent"],
             linewidth=2.5,
             label=f'近期 ({recent.index[0].strftime("%Y-%m-%d")} ~)',
             zorder=5)
    ax1.plot(x, baseline_n.values[:n_points],
             color=BLOOMBERG_COLORS["baseline"],
             linewidth=2,
             linestyle='--',
             alpha=0.8,
             label=f'{best_match.get("baseline", "歷史基準")} ({best_match.get("segment_start", "")} ~)',
             zorder=4)

    # 網格
    ax1.grid(True, color=BLOOMBERG_COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)

    # 軸設定
    ax1.set_xlabel('週數', color=BLOOMBERG_COLORS["text_dim"], fontsize=10)
    ax1.set_ylabel('Z-Score (正規化)', color=BLOOMBERG_COLORS["text_dim"], fontsize=10)
    ax1.tick_params(axis='both', colors=BLOOMBERG_COLORS["text_dim"])

    # 圖例
    ax1.legend(
        loc='upper left',
        fontsize=9,
        facecolor=BLOOMBERG_COLORS["box_bg"],
        edgecolor=BLOOMBERG_COLORS["grid"],
        labelcolor=BLOOMBERG_COLORS["text"]
    )

    # 子標題
    ax1.set_title('形狀比對：近期 vs. 歷史基準（正規化後）',
                  color=BLOOMBERG_COLORS["text"],
                  fontsize=11,
                  fontweight='bold',
                  pad=10)

    # === 上右：相似度分數面板 ===
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BLOOMBERG_COLORS["background"])
    ax2.axis('off')

    # 相似度分數資訊框
    pattern_score = best_match.get("pattern_similarity_score", 0)
    corr = best_match.get("corr", 0)
    dtw = best_match.get("dtw", 0)
    feature_sim = best_match.get("feature_sim", 0)

    # 風險等級
    if composite_score >= 0.7:
        risk_text = "高風險"
        risk_color = BLOOMBERG_COLORS["extreme_stress"]
    elif composite_score >= 0.5:
        risk_text = "中高風險"
        risk_color = BLOOMBERG_COLORS["stress"]
    elif composite_score >= 0.3:
        risk_text = "中風險"
        risk_color = BLOOMBERG_COLORS["mild_stress"]
    else:
        risk_text = "低風險"
        risk_color = BLOOMBERG_COLORS["mild_risk_on"]

    info_lines = [
        ("最佳匹配", best_match.get("baseline", "N/A"), BLOOMBERG_COLORS["text"]),
        ("", "", ""),
        ("相關係數", f"{corr:.2f}", BLOOMBERG_COLORS["recent"]),
        ("DTW 距離", f"{dtw:.2f}", BLOOMBERG_COLORS["secondary"]),
        ("形狀特徵", f"{feature_sim:.2f}", BLOOMBERG_COLORS["tertiary"]),
        ("", "", ""),
        ("形狀相似度", f"{pattern_score:.2f}", BLOOMBERG_COLORS["primary"]),
        ("壓力驗證", f"{stress_score:.2f}", BLOOMBERG_COLORS["text"]),
        ("", "", ""),
        ("綜合風險", f"{composite_score:.2f}", risk_color),
        ("風險等級", risk_text, risk_color),
    ]

    y_pos = 0.95
    for label, value, color in info_lines:
        if label == "":
            y_pos -= 0.04
            continue
        ax2.text(0.1, y_pos, label + ":",
                 color=BLOOMBERG_COLORS["text_dim"],
                 fontsize=10,
                 transform=ax2.transAxes,
                 va='top')
        ax2.text(0.9, y_pos, value,
                 color=color,
                 fontsize=11 if label in ["綜合風險", "風險等級"] else 10,
                 fontweight='bold' if label in ["綜合風險", "風險等級", "形狀相似度"] else 'normal',
                 transform=ax2.transAxes,
                 va='top',
                 ha='right')
        y_pos -= 0.08

    # === 下左：壓力指標儀表板 ===
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor(BLOOMBERG_COLORS["background"])

    # 過濾有效指標
    valid_details = [d for d in stress_details if d.get("signal") != "no_data"]
    names = [d['name'] for d in valid_details]
    z_scores = [d['z'] for d in valid_details]
    signals = [d['signal'] for d in valid_details]
    colors = [get_signal_color(s) for s in signals]

    y_pos = np.arange(len(names))
    bars = ax3.barh(y_pos, z_scores, color=colors, alpha=0.85, height=0.6)

    # 門檻線
    ax3.axvline(x=1.5, color=BLOOMBERG_COLORS["stress"],
                linestyle='--', linewidth=1.5, alpha=0.7, label='壓力門檻 (±1.5)')
    ax3.axvline(x=-1.5, color=BLOOMBERG_COLORS["stress"],
                linestyle='--', linewidth=1.5, alpha=0.7)
    ax3.axvline(x=0, color=BLOOMBERG_COLORS["text_dim"],
                linestyle='-', linewidth=0.5, alpha=0.5)

    # 軸設定
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(names, color=BLOOMBERG_COLORS["text"], fontsize=10)
    ax3.set_xlabel('Z-Score', color=BLOOMBERG_COLORS["text_dim"], fontsize=10)
    ax3.tick_params(axis='x', colors=BLOOMBERG_COLORS["text_dim"])
    ax3.set_xlim(-3, 3)

    # 網格
    ax3.grid(True, axis='x', color=BLOOMBERG_COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax3.set_axisbelow(True)

    # 數值標籤
    for i, (bar, z) in enumerate(zip(bars, z_scores)):
        width = bar.get_width()
        x_pos = width + 0.1 if width >= 0 else width - 0.1
        ax3.text(x_pos, bar.get_y() + bar.get_height()/2,
                 f'{z:.2f}',
                 ha='left' if width >= 0 else 'right',
                 va='center',
                 fontsize=9,
                 color=BLOOMBERG_COLORS["text"],
                 fontweight='bold')

    # 子標題
    ax3.set_title('壓力驗證指標儀表板',
                  color=BLOOMBERG_COLORS["text"],
                  fontsize=11,
                  fontweight='bold',
                  pad=10)

    # === 下右：解讀說明 ===
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor(BLOOMBERG_COLORS["background"])
    ax4.axis('off')

    # 訊號統計
    stress_count = sum(1 for s in signals if s in ["stress", "extreme_stress"])
    neutral_count = sum(1 for s in signals if s == "neutral")
    risk_on_count = sum(1 for s in signals if s in ["mild_risk_on"])

    interpretation_lines = [
        ("訊號統計", "", BLOOMBERG_COLORS["text"]),
        ("  壓力訊號", f"{stress_count}", BLOOMBERG_COLORS["stress"]),
        ("  中性訊號", f"{neutral_count}", BLOOMBERG_COLORS["neutral"]),
        ("  風險偏好", f"{risk_on_count}", BLOOMBERG_COLORS["mild_risk_on"]),
        ("", "", ""),
        ("解讀", "", BLOOMBERG_COLORS["text"]),
    ]

    # 判斷語句
    if pattern_score > 0.7 and stress_score < 0.3:
        conclusion = "形狀相似但缺乏壓力\n共振，更可能是利率\n/會計效果"
        conclusion_color = BLOOMBERG_COLORS["secondary"]
    elif pattern_score > 0.7 and stress_score > 0.5:
        conclusion = "形狀相似且壓力驗證\n支持，需提高警覺"
        conclusion_color = BLOOMBERG_COLORS["stress"]
    elif pattern_score < 0.5:
        conclusion = "形狀相似度較低，\n圖形類比論述不成立"
        conclusion_color = BLOOMBERG_COLORS["mild_risk_on"]
    else:
        conclusion = "中度相似，建議持續\n觀察後續發展"
        conclusion_color = BLOOMBERG_COLORS["text_dim"]

    interpretation_lines.append(("  結論", conclusion, conclusion_color))

    y_pos = 0.95
    for label, value, color in interpretation_lines:
        if label == "":
            y_pos -= 0.06
            continue
        ax4.text(0.05, y_pos, label,
                 color=BLOOMBERG_COLORS["text_dim"] if label.startswith("  ") else BLOOMBERG_COLORS["text"],
                 fontsize=10 if not label.startswith("  ") else 9,
                 fontweight='bold' if not label.startswith("  ") else 'normal',
                 transform=ax4.transAxes,
                 va='top')
        if value:
            # 處理多行文字
            lines = value.split('\n')
            for i, line in enumerate(lines):
                ax4.text(0.95, y_pos - i * 0.06, line,
                         color=color,
                         fontsize=9,
                         transform=ax4.transAxes,
                         va='top',
                         ha='right')
            y_pos -= 0.06 * len(lines)
        y_pos -= 0.08

    # === 主標題 ===
    fig.suptitle(
        title,
        color=BLOOMBERG_COLORS["text"],
        fontsize=14,
        fontweight='bold',
        y=0.98
    )

    # === 頁尾 ===
    fig.text(0.02, 0.01,
             "資料來源: FRED (Federal Reserve Economic Data)",
             color=BLOOMBERG_COLORS["text_dim"],
             fontsize=8,
             ha='left')
    fig.text(0.98, 0.01,
             f'截至: {recent.index[-1].strftime("%Y-%m-%d")}',
             color=BLOOMBERG_COLORS["text_dim"],
             fontsize=8,
             ha='right')

    # === 輸出 ===
    plt.subplots_adjust(top=0.93, bottom=0.05)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=BLOOMBERG_COLORS["background"])
    plt.close()

    print(f"[Saved] {output_path}")


# ============================================================================
# 歷史走勢 + 推測走勢圖（合併版）
# ============================================================================

def plot_history_with_projection(
    full_series: pd.Series,
    baseline_windows: list,
    recent_start: datetime,
    best_match: Dict,
    stress_score: float,
    composite_score: float,
    output_path: Path
) -> None:
    """
    繪製歷史走勢 + 基於形狀比對的推測走勢（Bloomberg 風格）

    根據最佳匹配的歷史片段後續走勢，外推未來可能路徑
    """
    plt.style.use('dark_background')

    fig, ax = plt.subplots(figsize=(16, 8), facecolor=BLOOMBERG_COLORS["background"])
    ax.set_facecolor(BLOOMBERG_COLORS["background"])

    # ========== 1. 繪製歷史走勢 ==========
    ax.plot(full_series.index, full_series.values,
            color=BLOOMBERG_COLORS["primary"],
            linewidth=2,
            alpha=0.9,
            label='WUDSHO 實際走勢',
            zorder=3)

    # ========== 2. 計算並繪製推測走勢 ==========
    baseline_name = best_match.get("baseline", "")
    seg_start = pd.Timestamp(best_match.get("segment_start"))
    seg_end = pd.Timestamp(best_match.get("segment_end"))
    pattern_score = best_match.get("pattern_similarity_score", 0)
    corr = best_match.get("corr", 0)

    # 找到基準窗口
    baseline_win = None
    baseline_idx = -1
    for idx, win in enumerate(baseline_windows):
        if win.name == baseline_name:
            baseline_win = win
            baseline_idx = idx
            break

    projection_dates = []
    projection_values = []

    # 動態計算推測週數：
    # 1. 找到匹配的 baseline window 的結束時間
    # 2. 計算從匹配片段結束到該事件完全結束的時間長度
    # 3. 預測長度要涵蓋到歷史事件結束後至少 12 週
    lookahead_weeks = 12  # 預設值

    if baseline_win:
        baseline_end_date = pd.Timestamp(baseline_win.end)

        # 找到前一個大幅變動事件（如果有）以獲得完整週期概念
        # 例如：如果匹配 RATE_HIKE_2022，前一個事件可能是 COVID_2020
        prior_event_start = None
        if baseline_idx > 0:
            prior_win = baseline_windows[baseline_idx - 1]
            prior_event_start = pd.Timestamp(prior_win.start)

        # 計算歷史上從匹配片段結束到 baseline window 結束的週數
        if seg_end < baseline_end_date:
            weeks_to_baseline_end = int((baseline_end_date - seg_end).days / 7)
        else:
            weeks_to_baseline_end = 0

        # 如果有前一個事件，嘗試計算完整週期長度
        # 完整週期 = 從前一個事件開始到當前事件結束
        if prior_event_start and seg_start > prior_event_start:
            # 計算從 seg_end 到「完整週期結束」需要多少週
            # 這裡「完整週期結束」定義為 baseline_end + 緩衝期
            buffer_weeks = 12  # 額外緩衝週數
            lookahead_weeks = max(24, weeks_to_baseline_end + buffer_weeks)
        else:
            # 沒有前一個事件，使用 baseline window 長度作為參考
            baseline_start_date = pd.Timestamp(baseline_win.start)
            baseline_duration_weeks = int((baseline_end_date - baseline_start_date).days / 7)
            lookahead_weeks = max(12, weeks_to_baseline_end + baseline_duration_weeks // 2)

        # 確保不超過可用的歷史數據長度
        if seg_end in full_series.index:
            seg_idx_end = full_series.index.get_loc(seg_end)
            available_weeks = len(full_series) - seg_idx_end - 1
            lookahead_weeks = min(lookahead_weeks, available_weeks)

        # 設定上限，避免預測過長
        lookahead_weeks = min(lookahead_weeks, 104)  # 最多 2 年

    print(f"  推測週數: {lookahead_weeks} 週")

    # 使用完整歷史資料（而非僅基準窗口）來外推後續走勢
    if seg_end in full_series.index:
        seg_idx_end = full_series.index.get_loc(seg_end)

        # 取得匹配片段後續的走勢（使用完整歷史）
        if seg_idx_end + 1 < len(full_series):
            subsequent = full_series.iloc[seg_idx_end + 1:seg_idx_end + 1 + lookahead_weeks]

            if len(subsequent) > 0:
                # 計算後續走勢的相對變化率
                baseline_end_value = full_series.iloc[seg_idx_end]
                relative_changes = (subsequent.values - baseline_end_value) / abs(baseline_end_value)

                # 套用到當前最新值
                latest_value = full_series.iloc[-1]
                latest_date = full_series.index[-1]

                projection_values = [latest_value]
                projection_dates = [latest_date]

                for i, rel_change in enumerate(relative_changes):
                    proj_date = latest_date + pd.Timedelta(weeks=i+1)
                    proj_value = latest_value * (1 + rel_change)
                    projection_dates.append(proj_date)
                    projection_values.append(proj_value)

    # 繪製推測走勢
    if len(projection_dates) > 1:
        ax.plot(projection_dates, projection_values,
                color=BLOOMBERG_COLORS["tertiary"],
                linewidth=2.5,
                linestyle='--',
                alpha=0.8,
                label=f'推測走勢（基於 {baseline_name}）',
                zorder=4)

        # 繪製推測區間的不確定性（簡化版：±10%）
        proj_upper = [v * 1.10 for v in projection_values]
        proj_lower = [v * 0.90 for v in projection_values]
        ax.fill_between(projection_dates, proj_lower, proj_upper,
                        color=BLOOMBERG_COLORS["tertiary"],
                        alpha=0.15,
                        zorder=2)

    # ========== 3. 標記關鍵區域 ==========
    # 標記最佳匹配的歷史片段
    ax.axvspan(seg_start, seg_end,
               alpha=0.25,
               color=BLOOMBERG_COLORS["secondary"],
               hatch='///',
               zorder=1)

    # 標記近期窗口
    ax.axvspan(recent_start, full_series.index[-1],
               alpha=0.2,
               color=BLOOMBERG_COLORS["recent"],
               zorder=1)

    # ========== 4. 加入文字註記 ==========

    # 註記 1：最佳匹配片段說明（放在片段上方）
    mid_seg_date = seg_start + (seg_end - seg_start) / 2
    seg_data = full_series[(full_series.index >= seg_start) & (full_series.index <= seg_end)]
    if len(seg_data) > 0:
        seg_min_value = seg_data.min()
        ax.annotate(
            f'歷史類比片段\n{baseline_name}\n{seg_start.strftime("%Y-%m")} ~ {seg_end.strftime("%Y-%m")}',
            xy=(mid_seg_date, seg_min_value),
            xytext=(0, -50),
            textcoords='offset points',
            color=BLOOMBERG_COLORS["secondary"],
            fontsize=8,
            fontweight='bold',
            ha='center',
            va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=BLOOMBERG_COLORS["box_bg"],
                      edgecolor=BLOOMBERG_COLORS["secondary"], alpha=0.9),
            arrowprops=dict(arrowstyle='->', color=BLOOMBERG_COLORS["secondary"], lw=1.5)
        )

    # 註記 2：近期窗口（簡化，放在底部）
    recent_data = full_series[full_series.index >= recent_start]
    if len(recent_data) > 0:
        recent_mid_date = recent_start + (full_series.index[-1] - recent_start) / 3
        recent_min_value = recent_data.min()
        ax.annotate(
            f'近期走勢\ncorr={corr:.2f}',
            xy=(recent_mid_date, recent_min_value),
            xytext=(0, -35),
            textcoords='offset points',
            color=BLOOMBERG_COLORS["recent"],
            fontsize=8,
            fontweight='bold',
            ha='center',
            va='top',
            bbox=dict(boxstyle='round,pad=0.2', facecolor=BLOOMBERG_COLORS["box_bg"],
                      edgecolor=BLOOMBERG_COLORS["recent"], alpha=0.9),
            arrowprops=dict(arrowstyle='->', color=BLOOMBERG_COLORS["recent"], lw=1)
        )

    # 註記 3：推測走勢說明（放在推測線上方）
    if len(projection_dates) > 3:
        # 判斷推測方向
        if projection_values[-1] > projection_values[0]:
            direction = "上行趨勢"
            direction_color = BLOOMBERG_COLORS["mild_risk_on"]
        else:
            direction = "下行趨勢"
            direction_color = BLOOMBERG_COLORS["stress"]

        # 放在推測線的起點上方
        ax.annotate(
            f'若歷史重演 → {direction}',
            xy=(projection_dates[0], projection_values[0]),
            xytext=(10, 50),
            textcoords='offset points',
            color=BLOOMBERG_COLORS["tertiary"],
            fontsize=9,
            fontweight='bold',
            ha='left',
            va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=BLOOMBERG_COLORS["box_bg"],
                      edgecolor=BLOOMBERG_COLORS["tertiary"], alpha=0.9),
            arrowprops=dict(arrowstyle='->', color=BLOOMBERG_COLORS["tertiary"], lw=1.5)
        )

    # ========== 5. 右側資訊面板 ==========
    # 風險等級
    if composite_score >= 0.7:
        risk_text = "高風險"
        risk_color = BLOOMBERG_COLORS["extreme_stress"]
    elif composite_score >= 0.5:
        risk_text = "中高風險"
        risk_color = BLOOMBERG_COLORS["stress"]
    elif composite_score >= 0.3:
        risk_text = "中風險"
        risk_color = BLOOMBERG_COLORS["mild_stress"]
    else:
        risk_text = "低風險"
        risk_color = BLOOMBERG_COLORS["mild_risk_on"]

    # 關鍵結論
    if pattern_score > 0.7 and stress_score < 0.3:
        conclusion = "形狀相似但壓力指標偏中性\n→ 更可能是利率/會計效果"
    elif pattern_score > 0.7 and stress_score > 0.5:
        conclusion = "形狀相似且壓力指標支持\n→ 需提高警覺"
    else:
        conclusion = "持續觀察後續發展"

    # 在圖表右上角加入資訊框
    info_text = (
        f"【分析摘要】\n"
        f"最佳匹配: {baseline_name}\n"
        f"相關係數: {corr:.2f}\n"
        f"形狀相似度: {pattern_score:.2f}\n"
        f"壓力驗證: {stress_score:.2f}\n"
        f"綜合風險: {composite_score:.2f}\n"
        f"風險等級: {risk_text}\n"
        f"─────────────\n"
        f"{conclusion}"
    )

    ax.text(0.98, 0.97, info_text,
            transform=ax.transAxes,
            fontsize=9,
            color=BLOOMBERG_COLORS["text"],
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor=BLOOMBERG_COLORS["box_bg"],
                      edgecolor=risk_color,
                      linewidth=2,
                      alpha=0.95))

    # ========== 6. 軸設定與美化 ==========
    ax.grid(True, color=BLOOMBERG_COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    ax.set_xlabel('日期', color=BLOOMBERG_COLORS["text_dim"], fontsize=10)
    ax.set_ylabel('WUDSHO (Millions USD)', color=BLOOMBERG_COLORS["text_dim"], fontsize=10)
    ax.tick_params(axis='both', colors=BLOOMBERG_COLORS["text_dim"])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(format_millions))

    # 最新值標註
    latest_date = full_series.index[-1]
    latest_value = full_series.iloc[-1]
    if abs(latest_value) >= 1e6:
        value_str = f'{latest_value/1e6:.0f}M'
    elif abs(latest_value) >= 1e3:
        value_str = f'{latest_value/1e3:.0f}K'
    else:
        value_str = f'{latest_value:.0f}'
    ax.annotate(
        f'當前: {value_str}',
        xy=(latest_date, latest_value),
        xytext=(-60, 10),
        textcoords='offset points',
        color=BLOOMBERG_COLORS["primary"],
        fontsize=10,
        fontweight='bold',
        va='bottom',
        ha='right',
        arrowprops=dict(arrowstyle='->', color=BLOOMBERG_COLORS["primary"], lw=1)
    )

    # 推測終點標註
    if len(projection_values) > 1:
        final_proj_value = projection_values[-1]
        final_proj_date = projection_dates[-1]
        if abs(final_proj_value) >= 1e6:
            proj_value_str = f'{final_proj_value/1e6:.0f}M'
        elif abs(final_proj_value) >= 1e3:
            proj_value_str = f'{final_proj_value/1e3:.0f}K'
        else:
            proj_value_str = f'{final_proj_value:.0f}'

        change_pct = (final_proj_value - latest_value) / abs(latest_value) * 100
        change_str = f'+{change_pct:.1f}%' if change_pct > 0 else f'{change_pct:.1f}%'

        ax.annotate(
            f'推測: {proj_value_str}\n({change_str})',
            xy=(final_proj_date, final_proj_value),
            xytext=(10, 0),
            textcoords='offset points',
            color=BLOOMBERG_COLORS["tertiary"],
            fontsize=10,
            fontweight='bold',
            va='center',
            ha='left'
        )

    # 圖例
    ax.legend(
        loc='upper left',
        fontsize=9,
        facecolor=BLOOMBERG_COLORS["box_bg"],
        edgecolor=BLOOMBERG_COLORS["grid"],
        labelcolor=BLOOMBERG_COLORS["text"]
    )

    # 標題
    fig.suptitle(
        '聯準會未攤銷折價（WUDSHO）走勢分析與推測',
        color=BLOOMBERG_COLORS["text"],
        fontsize=14,
        fontweight='bold',
        y=0.98
    )

    # 頁尾
    fig.text(0.02, 0.02,
             "資料來源: FRED",
             color=BLOOMBERG_COLORS["text_dim"],
             fontsize=8,
             ha='left')
    fig.text(0.98, 0.02,
             f'截至: {latest_date.strftime("%Y-%m-%d")}',
             color=BLOOMBERG_COLORS["text_dim"],
             fontsize=8,
             ha='right')

    # 輸出
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08, right=0.98, left=0.06)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=BLOOMBERG_COLORS["background"])
    plt.close()

    print(f"[Saved] {output_path}")


# ============================================================================
# 主函數
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="聯準會未攤銷折價走勢模式偵測 - 視覺化"
    )
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="輸出目錄（預設：專案根目錄 output/）")
    parser.add_argument("--target_series", type=str, default="WUDSHO",
                        help="目標序列")
    parser.add_argument("--recent_days", type=int, default=120,
                        help="近期窗口天數")
    parser.add_argument("--json", type=str, default=None,
                        help="使用現有的 JSON 分析結果")

    args = parser.parse_args()

    # 設定輸出目錄（預設為專案根目錄的 output）
    if args.output:
        output_dir = Path(args.output)
    else:
        # 預設輸出到專案根目錄的 output/
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent.parent.parent.parent / "output"

    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 如果有 JSON 檔案，直接使用
    if args.json:
        json_path = Path(args.json)
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                analysis_result = json.load(f)
            print(f"[Load] 載入分析結果: {json_path}")

            # 從 JSON 重建所需資料
            best_match = analysis_result.get("best_match", {})
            stress_details = analysis_result.get("stress_confirmation", {}).get("details", [])
            stress_score = analysis_result.get("stress_confirmation", {}).get("score", 0)
            composite_score = analysis_result.get("composite_risk_score", 0)
        else:
            print(f"[Error] JSON 檔案不存在: {json_path}")
            return

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

    # 執行分析（如果沒有 JSON）
    if not args.json:
        print("[Step 2] 執行形狀比對...")

        all_matches = []
        for baseline in DEFAULT_BASELINE_WINDOWS:
            baseline_data = target_data[
                (target_data.index >= baseline.start) &
                (target_data.index <= baseline.end)
            ]
            if len(baseline_data) >= len(recent):
                match = find_best_match(
                    recent, baseline_data, "zscore",
                    {"corr": 0.4, "dtw": 0.3, "shape_features": 0.3}
                )
                if match:
                    match["baseline"] = baseline.name
                    all_matches.append(match)
                    print(f"  {baseline.name}: corr={match['corr']:.2f}, score={match['pattern_similarity_score']:.2f}")

        if not all_matches:
            print("[Error] 無法找到匹配的歷史片段")
            return

        best_match = max(all_matches, key=lambda x: x["pattern_similarity_score"])

        # 壓力驗證
        print("[Step 3] 壓力驗證...")
        stress_details = []
        for indicator in DEFAULT_CONFIRMATORY_INDICATORS:
            if indicator.series == "yield_curve":
                ind_data = all_data.get("yield_curve", pd.Series())
            else:
                ind_data = all_data.get(indicator.series, pd.Series())
            result = calculate_stress_signal(ind_data, indicator)
            stress_details.append(result)

        stress_score = aggregate_stress_scores(stress_details)
        pattern_score = best_match["pattern_similarity_score"]
        composite_score = 0.6 * pattern_score + 0.4 * stress_score

    # 取得最佳匹配片段
    baseline_name = best_match.get("baseline", "")
    baseline_win = None
    for win in DEFAULT_BASELINE_WINDOWS:
        if win.name == baseline_name:
            baseline_win = win
            break

    if baseline_win:
        baseline_data = target_data[
            (target_data.index >= baseline_win.start) &
            (target_data.index <= baseline_win.end)
        ]
        # 取出最佳匹配片段
        seg_start = pd.Timestamp(best_match.get("segment_start"))
        seg_end = pd.Timestamp(best_match.get("segment_end"))
        baseline_segment = baseline_data[(baseline_data.index >= seg_start) & (baseline_data.index <= seg_end)]
    else:
        baseline_segment = recent  # fallback

    # 生成圖表
    print("[Step 4] 生成圖表...")

    # 歷史走勢 + 推測走勢合併圖
    plot_history_with_projection(
        full_series=target_data,
        baseline_windows=DEFAULT_BASELINE_WINDOWS,
        recent_start=recent_start,
        best_match=best_match,
        stress_score=stress_score,
        composite_score=composite_score,
        output_path=output_dir / f"fed_unamortized_discount_analysis_{date_str}.png"
    )

    print(f"\n[Done] 圖表已儲存至: {output_dir}")
    print(f"  - fed_unamortized_discount_analysis_{date_str}.png")


if __name__ == "__main__":
    main()
