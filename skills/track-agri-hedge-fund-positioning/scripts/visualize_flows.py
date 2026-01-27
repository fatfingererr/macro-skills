#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
農產品對沖基金部位視覺化

生成 Bloomberg 風格的 COT 資金流分析圖表。

Usage:
    python visualize_flows.py
    python visualize_flows.py --output path/to/output.png
    python visualize_flows.py --weeks 52
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前設定

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

from fetch_cot_data import (
    ALL_GROUPS,
    aggregate_by_group,
    calculate_flows,
    fetch_cot_from_api,
    parse_cot_data,
)


# ========== Bloomberg 風格配色（依據 bloomberg-style-chart-guide.md）==========
COLORS = {
    # 背景與網格
    "background": "#1a1a2e",
    "grid": "#2d2d44",

    # 文字
    "text": "#ffffff",
    "text_dim": "#888888",

    # 群組配色（6 個群組）
    "grains": "#ff6b35",       # 橙紅（穀物 - 主要）
    "oilseeds": "#ffaa00",     # 橙黃（油籽）
    "meats": "#00ff88",        # 綠色（肉類）
    "softs": "#00bfff",        # 藍色（軟性商品）
    "fiber": "#cc66ff",        # 紫色（纖維）
    "dairy": "#ff66b2",        # 粉紅（乳製品）

    # 淨部位線
    "net_pos_line": "#ffffff",  # 白色

    # 火力配色（熱圖）
    "firepower_high": "#00ff88",   # 高火力（綠 = 買進空間大）
    "firepower_mid": "#ffaa00",    # 中火力（橙）
    "firepower_low": "#ff4444",    # 低火力（紅 = 擁擠）

    # 訊號配色
    "bullish": "#00ff88",
    "bearish": "#ff4444",
    "neutral": "#888888",

    # 輔助
    "zero_line": "#666666",
}

# 群組顯示名稱（純中文）
GROUP_LABELS = {
    "grains": "穀物",
    "oilseeds": "油籽",
    "meats": "肉類",
    "softs": "軟商品",
    "fiber": "纖維",
    "dairy": "乳製品",
}

# 火力圖排序（由上到下）：肉類 > 油籽 > 乳製品 > 穀物 > 纖維 > 軟商品
FIREPOWER_ORDER = ["meats", "oilseeds", "dairy", "grains", "fiber", "softs"]

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


# ========== USDA 關鍵事件標註（用於 Total 部位轉折解讀）==========
USDA_EVENT_ANNOTATIONS = [
    # A) 年初核心供需錨
    {"date": "2025-01-10", "label": "年初供需錨",
     "desc": "WASDE+庫存+冬麥\n全年定調起點", "category": "wasde"},
    # B) 月度 WASDE 節點
    {"date": "2025-02-11", "label": "2月WASDE",
     "desc": "修正南美/出口\n穀物油籽情緒", "category": "wasde"},
    {"date": "2025-03-11", "label": "3月WASDE",
     "desc": "春季前校準\n全球出口節奏", "category": "wasde"},
    {"date": "2025-04-10", "label": "4月WASDE",
     "desc": "新作年度鋪陳\n25/26預期啟動", "category": "wasde"},
    # C) 春季大轉折：種植意向
    {"date": "2025-03-31", "label": "種植意向",
     "desc": "玉米/黃豆面積\n供給預期重錨", "category": "planting"},
    # D) 夏季再定錨：實際播種面積
    {"date": "2025-06-30", "label": "實際面積",
     "desc": "意向→落地\n穀物供給硬定錨", "category": "planting"},
    # E) 收成期供給衝擊 + 資料中斷
    {"date": "2025-09-12", "label": "供給巨大化",
     "desc": "玉米創紀錄預估\n庫存大增→偏空", "category": "wasde"},
    {"date": "2025-09-30", "label": "季度庫存",
     "desc": "收成前後更新\n穀物部位再調整", "category": "stocks"},
    {"date": "2025-10-09", "label": "資料黑箱",
     "desc": "政府停擺\nCOT/出口數據中斷", "category": "shutdown"},
    # F) 報告回補/延後釋出
    {"date": "2025-11-14", "label": "報告回補",
     "desc": "黑箱後WASDE\n估計分歧創高", "category": "wasde"},
    # G) 年末供需更新 + 年度總結
    {"date": "2025-12-09", "label": "年末WASDE",
     "desc": "年末供需更新\n資金調倉節點", "category": "wasde"},
    {"date": "2026-01-12", "label": "年度總結",
     "desc": "2025產量定案\n年初再定錨依據", "category": "summary"},
]

# 事件類別顏色
EVENT_CATEGORY_COLORS = {
    "wasde": "#ffaa00",      # 橙黃：月度供需報告
    "planting": "#00ff88",   # 綠色：種植相關
    "stocks": "#00bfff",     # 藍色：庫存報告
    "shutdown": "#ff4444",   # 紅色：異常事件
    "summary": "#cc66ff",    # 紫色：年度總結
}


def add_usda_event_annotations(ax, dates, y_bottom, y_top):
    """
    在圖表上添加 USDA 關鍵事件標註（簡短中文摘要）

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        主圖表軸
    dates : pd.DatetimeIndex
        圖表的日期索引
    y_bottom : float
        Y 軸最小值
    y_top : float
        Y 軸最大值
    """
    from datetime import datetime as dt, date

    # 將日期轉為 date 對象以便比較（統一類型）
    def to_date(d):
        if hasattr(d, 'date'):
            return d.date()
        elif hasattr(d, 'to_pydatetime'):
            return d.to_pydatetime().date()
        elif isinstance(d, date):
            return d
        return d

    date_list = [to_date(d) for d in dates]
    date_min = min(date_list)
    date_max = max(date_list)

    # 過濾出在圖表範圍內的事件
    events_in_range = []
    for event in USDA_EVENT_ANNOTATIONS:
        event_date = dt.strptime(event["date"], "%Y-%m-%d").date()
        if date_min <= event_date <= date_max:
            events_in_range.append((event_date, event))

    if not events_in_range:
        return

    # 找出每個事件對應的 x 位置（最接近的週）
    for event_date, event in events_in_range:
        # 找最接近的索引
        min_diff = float('inf')
        closest_idx = 0
        for i, d in enumerate(date_list):
            diff = abs((d - event_date).days) if hasattr(d - event_date, 'days') else float('inf')
            if diff < min_diff:
                min_diff = diff
                closest_idx = i

        # 只有在合理範圍內（±7天）才標註
        if min_diff > 7:
            continue

        x_pos = closest_idx
        color = EVENT_CATEGORY_COLORS.get(event["category"], "#888888")

        # 繪製垂直虛線（淡化，不要太搶眼）
        ax.axvline(x=x_pos, color=color, linestyle=':', linewidth=0.8, alpha=0.4, zorder=1)

        # 組合標籤文字：主標籤 + 描述（換行）
        label_text = event["label"]
        if "desc" in event and event["desc"]:
            # 橫向顯示時用 | 分隔更緊湊
            desc_short = event["desc"].replace("\n", " | ")
            label_text = f"{event['label']}\n{desc_short}"

        # 在底部區域使用多層高度避免重疊
        # 根據索引分配不同層級（0.02, 0.12, 0.22, 0.32）
        idx = events_in_range.index((event_date, event))
        layer = idx % 4  # 4 層循環
        height_offset = 0.02 + layer * 0.10
        label_y = y_bottom + (y_top - y_bottom) * height_offset

        # 橫向標籤（字體小，淡色背景增加可讀性）
        ax.text(x_pos, label_y, label_text,
                rotation=0, fontsize=5, color=color, alpha=0.9,
                ha='center', va='bottom', zorder=4, linespacing=0.85,
                bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS['background'],
                          edgecolor=color, alpha=0.75, linewidth=0.3))


def setup_bloomberg_style():
    """設定 Bloomberg 風格"""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': COLORS['background'],
        'axes.facecolor': COLORS['background'],
        'axes.edgecolor': COLORS['grid'],
        'axes.labelcolor': COLORS['text'],
        'axes.grid': True,
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.3,
        'grid.linestyle': '-',
        'grid.linewidth': 0.5,
        'text.color': COLORS['text'],
        'xtick.color': COLORS['text_dim'],
        'ytick.color': COLORS['text_dim'],
        'legend.facecolor': COLORS['background'],
        'legend.edgecolor': COLORS['grid'],
        'legend.labelcolor': COLORS['text'],
        'font.size': 10,
    })


def format_contracts(x, pos):
    """合約數格式化（K 表示千）"""
    if abs(x) >= 1000:
        return f'{x/1000:.0f}K'
    return f'{x:.0f}'


def calculate_firepower_series(positions_df: pd.DataFrame, lookback_weeks: int = 156) -> pd.DataFrame:
    """
    計算各群組的火力時序

    Parameters
    ----------
    positions_df : pd.DataFrame
        淨部位時序（columns = groups）
    lookback_weeks : int
        回溯週數

    Returns
    -------
    pd.DataFrame
        火力時序（columns = groups）
    """
    firepower_df = pd.DataFrame(index=positions_df.index)

    for col in positions_df.columns:
        fp_series = []
        for i in range(len(positions_df)):
            if i < 10:
                fp_series.append(np.nan)
                continue

            start_idx = max(0, i - lookback_weeks)
            hist = positions_df[col].iloc[start_idx:i+1]
            current = positions_df[col].iloc[i]

            # percentile rank
            p = (hist <= current).mean()
            fp = 1 - p
            fp_series.append(fp)

        firepower_df[col] = fp_series

    return firepower_df


def create_positioning_chart(
    flows_df: pd.DataFrame,
    positions_df: pd.DataFrame,
    firepower_df: pd.DataFrame,
    latest_summary: Dict[str, Any],
    output_path: Optional[str] = None,
    title: str = "農產品對沖基金部位分析",
    weeks_to_show: int = 52,
) -> None:
    """
    創建農產品對沖基金部位分析圖表（Bloomberg 風格）
    """
    setup_bloomberg_style()

    # 取最近 N 週
    flows_df = flows_df.iloc[-weeks_to_show:].copy()
    positions_df = positions_df.iloc[-weeks_to_show:].copy()
    firepower_df = firepower_df.iloc[-weeks_to_show:].copy()

    # 建立圖表：2 行，左側大圖 + 右側資訊面板
    fig = plt.figure(figsize=(16, 10))
    fig.set_facecolor(COLORS['background'])

    # GridSpec: 2 行 x 4 列，左 3 列給圖表，右 1 列給資訊
    gs = fig.add_gridspec(2, 4, height_ratios=[1.5, 1], width_ratios=[1, 1, 1, 0.8],
                          hspace=0.3, wspace=0.3)

    # ========== 圖 1: 週流量堆疊柱狀圖 + 總淨部位折線 ==========
    ax1 = fig.add_subplot(gs[0, :3])
    ax1.set_facecolor(COLORS['background'])

    # 準備堆疊柱狀圖數據
    dates = flows_df.index
    x = np.arange(len(dates))
    width = 0.8

    # 分離正負流量
    positive_flows = flows_df[ALL_GROUPS].clip(lower=0)
    negative_flows = flows_df[ALL_GROUPS].clip(upper=0)

    # 繪製正向堆疊
    bottom_pos = np.zeros(len(dates))
    for group in ALL_GROUPS:
        ax1.bar(x, positive_flows[group], width, bottom=bottom_pos,
                color=COLORS[group], label=GROUP_LABELS[group], alpha=0.85)
        bottom_pos += positive_flows[group].values

    # 繪製負向堆疊
    bottom_neg = np.zeros(len(dates))
    for group in ALL_GROUPS:
        ax1.bar(x, negative_flows[group], width, bottom=bottom_neg,
                color=COLORS[group], alpha=0.85)
        bottom_neg += negative_flows[group].values

    # 零線
    ax1.axhline(y=0, color=COLORS['zero_line'], linewidth=1, zorder=3)

    # 右軸：總淨部位折線
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x, positions_df['total'] / 1000, color=COLORS['net_pos_line'],
                  linewidth=2.5, label='總淨部位（右軸）', zorder=5)
    ax1_twin.set_ylabel('總淨部位（千合約）', color=COLORS['text'], fontsize=10)
    ax1_twin.tick_params(axis='y', labelcolor=COLORS['text'])

    # 標註最新淨部位
    latest_pos = positions_df['total'].iloc[-1]
    ax1_twin.annotate(f'{latest_pos/1000:+,.0f}K',
                      xy=(x[-1], latest_pos/1000),
                      xytext=(10, 0), textcoords='offset points',
                      color=COLORS['net_pos_line'], fontsize=11, fontweight='bold', va='center')

    # X 軸設定（每 4 週一個標籤 + 確保最後一週，1月顯示年份，其他月只顯示月份）
    tick_positions = list(x[::4])
    # 確保最後一週也有標籤
    if x[-1] not in tick_positions:
        tick_positions.append(x[-1])

    tick_labels = []
    for i in tick_positions:
        d = dates[i]
        if hasattr(d, 'month'):
            # 1月顯示完整年月，其他月只顯示月份數字
            if d.month == 1:
                tick_labels.append(d.strftime('%Y-%m'))
            else:
                tick_labels.append(str(d.month))
        else:
            tick_labels.append(str(d)[:7])
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=0, fontsize=9)

    ax1.set_ylabel('週流量 (合約)', color=COLORS['text'], fontsize=10)
    ax1.yaxis.set_major_formatter(FuncFormatter(format_contracts))
    ax1.set_title('分組週流量 + 總淨部位', fontsize=11, color=COLORS['text'], pad=10)

    # 圖例
    handles = [Patch(facecolor=COLORS[g], label=GROUP_LABELS[g], alpha=0.85) for g in ALL_GROUPS]
    handles.append(plt.Line2D([0], [0], color=COLORS['net_pos_line'], linewidth=2.5, label='總淨部位（右軸）'))
    ax1.legend(handles=handles, loc='upper left', fontsize=8, ncol=4,
               facecolor=COLORS['background'], edgecolor=COLORS['grid'])

    ax1.grid(True, color=COLORS['grid'], alpha=0.3, linewidth=0.5)
    ax1.set_axisbelow(True)

    # ========== 添加 USDA 關鍵事件標註 ==========
    y_min, y_max = ax1.get_ylim()
    add_usda_event_annotations(ax1, dates, y_min, y_max)

    # ========== 圖 2: 火力熱圖時序 ==========
    ax2 = fig.add_subplot(gs[1, :3])
    ax2.set_facecolor(COLORS['background'])

    # 準備熱圖數據（使用指定排序）
    fp_data = firepower_df[FIREPOWER_ORDER].T.values  # groups x weeks
    fp_groups = [GROUP_LABELS[g] for g in FIREPOWER_ORDER]

    # 自定義顏色映射（低→高 = 紅→橙→綠）
    fp_cmap = LinearSegmentedColormap.from_list(
        'firepower',
        [COLORS['firepower_low'], COLORS['firepower_mid'], COLORS['firepower_high']]
    )

    im = ax2.imshow(fp_data, aspect='auto', cmap=fp_cmap, vmin=0, vmax=1)

    # Y 軸：群組名稱
    ax2.set_yticks(np.arange(len(fp_groups)))
    ax2.set_yticklabels(fp_groups, fontsize=9)

    # X 軸：日期（每 4 週一個標籤 + 確保最後一週，1月顯示年份，其他月只顯示月份）
    x_ticks = list(np.arange(0, len(dates), 4))
    # 確保最後一週也有標籤
    if len(dates) - 1 not in x_ticks:
        x_ticks.append(len(dates) - 1)

    # 生成標籤
    tick_labels = []
    for i in x_ticks:
        d = dates[i]
        if hasattr(d, 'month'):
            # 1月顯示完整年月，其他月只顯示月份數字
            if d.month == 1:
                tick_labels.append(d.strftime('%Y-%m'))
            else:
                tick_labels.append(str(d.month))
        else:
            tick_labels.append(str(d)[:7])
    ax2.set_xticks(x_ticks)
    ax2.set_xticklabels(tick_labels, rotation=0, fontsize=9)

    ax2.set_title('火力分數時序圖', fontsize=11, color=COLORS['text'], pad=10)

    # 色條
    cbar = fig.colorbar(im, ax=ax2, orientation='vertical', shrink=0.8, pad=0.02)
    cbar.set_label('火力 (高=淨賣出部位高=未來買回潛力大)', fontsize=9, color=COLORS['text'])
    cbar.ax.tick_params(labelcolor=COLORS['text_dim'])

    # 標註最新火力值
    for i, g in enumerate(FIREPOWER_ORDER):
        fp_val = firepower_df[g].iloc[-1]
        if pd.notna(fp_val):
            ax2.text(len(dates)-1 + 0.5, i, f'{fp_val:.0%}',
                     va='center', ha='left', fontsize=9, fontweight='bold',
                     color=COLORS['text'])

    # ========== 右側資訊面板 ==========
    ax_info = fig.add_subplot(gs[:, 3])
    ax_info.set_facecolor(COLORS['background'])
    ax_info.axis('off')

    # 資訊文字
    info_text = []
    info_text.append(f"━━━ 最新週摘要 ━━━")
    info_text.append(f"最新報告日: {latest_summary.get('date', 'N/A')}")
    info_text.append("")

    # 訊號
    call = latest_summary.get('call', 'N/A')
    confidence = latest_summary.get('confidence', 0)
    info_text.append(f"訊號: {call}")
    info_text.append(f"信心: {confidence:.0%}")
    info_text.append("")

    # 總體指標
    info_text.append("━━━ 總體指標 ━━━")
    total_flow = latest_summary.get('total_flow')
    total_pos = latest_summary.get('total_net_pos')
    total_fp = latest_summary.get('total_firepower')

    if total_flow is not None:
        info_text.append(f"週流量: {total_flow:+,}")
    if total_pos is not None:
        info_text.append(f"淨部位: {total_pos:,}")
    if total_fp is not None:
        info_text.append(f"火力: {total_fp:.0%}")
    info_text.append("")

    # 分組流量（使用中文群組名）
    info_text.append("━━━ 分組流量 ━━━")
    by_group = latest_summary.get('by_group', {})
    for g in ALL_GROUPS:
        if g in by_group:
            flow = by_group[g].get('flow')
            if flow is not None:
                label = GROUP_LABELS.get(g, g)
                info_text.append(f"{label:6}: {flow:+,}")
    info_text.append("")

    # 風險提示
    risks = latest_summary.get('risks', [])
    if risks:
        info_text.append("━━━ 風險提示 ━━━")
        for r in risks[:3]:
            info_text.append(f"• {r[:20]}")

    # 繪製文字
    y_pos = 0.95
    for line in info_text:
        if '━━━' in line:
            color = COLORS['text']
            fontweight = 'bold'
            fontsize = 10
        elif line.startswith('訊號:'):
            color = COLORS['bullish'] if '買進' in call else COLORS['bearish'] if '賣出' in call else COLORS['text']
            fontweight = 'bold'
            fontsize = 10
        else:
            color = COLORS['text_dim']
            fontweight = 'normal'
            fontsize = 9

        ax_info.text(0.05, y_pos, line, transform=ax_info.transAxes,
                     fontsize=fontsize, fontweight=fontweight, color=color,
                     verticalalignment='top')
        y_pos -= 0.045

    # ========== 標題 ==========
    fig.suptitle(title, color=COLORS['text'], fontsize=14, fontweight='bold', y=0.98)

    # ========== 頁尾 ==========
    fig.text(0.02, 0.01, "資料來源: CFTC CoT",
             color=COLORS['text_dim'], fontsize=8, ha='left')
    fig.text(0.98, 0.01, f'生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
             color=COLORS['text_dim'], fontsize=8, ha='right')

    # ========== 輸出 ==========
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.05)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, facecolor=COLORS['background'],
                    edgecolor='none', bbox_inches='tight')
        print(f"[Chart] 已保存到: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="生成農產品對沖基金部位視覺化圖表（Bloomberg 風格）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="輸出路徑（預設: output/agri_fund_positioning_YYYY-MM-DD.png）"
    )
    parser.add_argument(
        "--weeks", "-w",
        type=int,
        default=52,
        help="顯示週數（預設: 52）"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2023-01-01",
        help="資料起始日期（預設: 2023-01-01）"
    )

    args = parser.parse_args()

    try:
        print("\n" + "=" * 60)
        print("農產品對沖基金部位視覺化")
        print("=" * 60 + "\n")

        # 抓取資料
        print("正在抓取 CFTC COT 資料...")
        raw_df = fetch_cot_from_api(args.start, datetime.now().strftime("%Y-%m-%d"))

        if raw_df.empty:
            print("錯誤: 無法抓取資料")
            return 1

        # 解析與計算
        cot_df = parse_cot_data(raw_df)
        cot_df = calculate_flows(cot_df)
        flows_df, positions_df = aggregate_by_group(cot_df)

        print(f"資料範圍: {flows_df.index.min()} 至 {flows_df.index.max()}")
        print(f"週數: {len(flows_df)}")

        # 計算火力時序
        print("正在計算火力分數...")
        firepower_df = calculate_firepower_series(positions_df)

        # 準備最新摘要
        latest_date = flows_df.index.max()
        latest_flow = flows_df.loc[latest_date]
        latest_pos = positions_df.loc[latest_date]
        latest_fp = firepower_df.loc[latest_date]

        # 判斷訊號（純中文）
        total_flow = latest_flow['total']
        total_fp = latest_fp['total'] if pd.notna(latest_fp['total']) else None

        if total_flow > 0:
            call = "基金買進"
        elif total_flow < 0:
            call = "基金賣出"
        else:
            call = "中性"

        if total_fp and total_fp > 0.85:
            call += "（極端空頭）"
        elif total_fp and total_fp < 0.2:
            call += "（擁擠）"

        confidence = 0.7
        if total_fp and total_fp > 0.8:
            confidence += 0.1
        if abs(total_flow) > 30000:
            confidence += 0.1

        latest_summary = {
            "date": str(latest_date),
            "call": call,
            "confidence": min(confidence, 0.95),
            "total_flow": int(total_flow),
            "total_net_pos": int(latest_pos['total']),
            "total_firepower": total_fp,
            "by_group": {
                g: {
                    "flow": int(latest_flow[g]) if pd.notna(latest_flow[g]) else None,
                    "net_pos": int(latest_pos[g]) if pd.notna(latest_pos[g]) else None,
                    "firepower": latest_fp[g] if pd.notna(latest_fp[g]) else None,
                }
                for g in ALL_GROUPS
            },
            "risks": ["COT 資料只到週二"],
        }

        # 決定輸出路徑
        if args.output:
            output_path = args.output
        else:
            today = datetime.now().strftime('%Y-%m-%d')
            # 找到專案根目錄
            current_dir = Path(__file__).resolve().parent
            root_dir = current_dir
            for _ in range(5):
                if (root_dir / 'output').exists() or root_dir.name == 'macro-skills':
                    break
                root_dir = root_dir.parent

            output_path = root_dir / 'output' / f'agri_fund_positioning_{today}.png'

        # 生成圖表
        print(f"\n正在生成圖表...")
        create_positioning_chart(
            flows_df, positions_df, firepower_df,
            latest_summary,
            output_path=str(output_path),
            weeks_to_show=args.weeks,
        )

        print("\n完成!")
        return 0

    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
