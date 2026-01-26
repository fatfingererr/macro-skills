#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloomberg 風格：鈀金-白銀跨金屬確認圖表

根據 detect-palladium-lead-silver-turns 分析結果，生成符合 Bloomberg 風格的視覺化圖表。
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式後端

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None

# 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Bloomberg 配色
COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "primary": "#ff6b35",      # 白銀（橙紅）
    "secondary": "#ffaa00",    # 鈀金（橙黃）
    "tertiary": "#ffff00",     # 輔助指標（黃色）
    "area_fill": "#ff8c00",
    "area_alpha": 0.4,
    "level_line": "#666666",
    "confirmed": "#00ff88",    # 確認拐點（綠色）
    "unconfirmed": "#ff4444",  # 未確認拐點（紅色）
}


def format_price(x, pos):
    """價格格式化"""
    if x >= 1000:
        return f'${x/1000:.1f}K'
    return f'${x:.0f}'


def format_percent(x, pos):
    """百分比格式化"""
    return f'{x*100:.0f}%'


def fetch_price_data(symbol: str, start_date: str, end_date: str, interval: str = "1h"):
    """重新抓取價格數據"""
    if yf is None:
        return None

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        if not df.empty:
            return df["Close"]
    except Exception as e:
        print(f"警告：無法抓取 {symbol} 數據：{e}")

    return None


def plot_palladium_silver_confirmation(
    result_json: dict,
    output_path: str,
    title: str = None,
    refetch_data: bool = True
):
    """
    繪製鈀金-白銀跨金屬確認分析圖表

    Parameters
    ----------
    result_json : dict
        detect-palladium-lead-silver-turns 的輸出結果
    output_path : str
        輸出圖表路徑
    title : str, optional
        圖表標題，默認自動生成
    refetch_data : bool, optional
        是否重新抓取價格數據以繪製完整價格線，默認 True
    """
    plt.style.use('dark_background')

    # 提取數據
    symbol_pair = result_json["symbol_pair"]
    summary = result_json["summary"]
    events = result_json["events"]
    latest_event = result_json["latest_event"]
    interpretation = result_json["interpretation"]
    data_range = result_json["data_range"]
    timeframe = result_json.get("timeframe", "1h")

    # 如果有時間序列數據，使用它；否則嘗試重新抓取
    if "timeseries" in result_json:
        ts = result_json["timeseries"]
        timestamps = pd.to_datetime(ts["timestamps"])
        ag_close = pd.Series(ts["ag_close"], index=timestamps)
        pd_close = pd.Series(ts["pd_close"], index=timestamps)
    elif refetch_data and yf is not None:
        print("重新抓取價格數據以繪製完整價格線...")
        ag_close = fetch_price_data(
            symbol_pair["silver"],
            data_range["start"],
            data_range["end"],
            timeframe
        )
        pd_close = fetch_price_data(
            symbol_pair["palladium"],
            data_range["start"],
            data_range["end"],
            timeframe
        )

        if ag_close is None or pd_close is None:
            print("警告：無法抓取完整價格數據，僅使用事件點繪圖")
            timestamps = []
            ag_prices = []
            pd_prices = []
            for event in events:
                timestamps.append(pd.to_datetime(event["ts"]))
                ag_prices.append(event["ag_price"])
                pd_prices.append(event.get("pd_price", None))
            ag_close = pd.Series(ag_prices, index=timestamps)
            pd_close = pd.Series(pd_prices, index=timestamps) if pd_prices[0] is not None else None
        else:
            # 對齊兩個序列到共同的索引
            common_index = ag_close.index.intersection(pd_close.index)
            if len(common_index) == 0:
                print("警告：白銀與鈀金數據無法對齊，僅使用事件點繪圖")
                timestamps = []
                ag_prices = []
                pd_prices = []
                for event in events:
                    timestamps.append(pd.to_datetime(event["ts"]))
                    ag_prices.append(event["ag_price"])
                    pd_prices.append(event.get("pd_price", None))
                ag_close = pd.Series(ag_prices, index=timestamps)
                pd_close = pd.Series(pd_prices, index=timestamps) if pd_prices[0] is not None else None
            else:
                ag_close = ag_close.reindex(common_index)
                pd_close = pd_close.reindex(common_index)
    else:
        # 從 events 提取部分數據
        timestamps = []
        ag_prices = []
        for event in events:
            timestamps.append(pd.to_datetime(event["ts"]))
            ag_prices.append(event["ag_price"])
        ag_close = pd.Series(ag_prices, index=timestamps)
        pd_close = None

    # 創建圖表 (3行1列布局)
    fig = plt.figure(figsize=(14, 12), facecolor=COLORS["background"])

    # 上半部：價格疊加圖
    ax_main = plt.subplot2grid((4, 1), (0, 0), rowspan=2, fig=fig)
    ax_main.set_facecolor(COLORS["background"])

    # 中間：鈀金/白銀價格比率
    ax_ratio = plt.subplot2grid((4, 1), (2, 0), fig=fig, sharex=ax_main)
    ax_ratio.set_facecolor(COLORS["background"])

    # 下半部：統計面板（滾動確認率）
    ax_stats = plt.subplot2grid((4, 1), (3, 0), fig=fig, sharex=ax_main)
    ax_stats.set_facecolor(COLORS["background"])

    # === 上半部：價格疊加圖 ===

    # 創建遞增索引（避免假日斷點）
    x_indices = np.arange(len(ag_close))

    # 白銀價格 (R1 右軸)
    if pd_close is not None:
        # 鈀金價格 (R2 右軸外側)
        ax_pd = ax_main.twinx()
        ax_pd.plot(x_indices, pd_close.values,
                   color=COLORS["secondary"], linewidth=1.5, alpha=0.7,
                   label=f'鈀金 {symbol_pair["palladium"]} (R2)', zorder=3)
        ax_pd.set_ylabel('鈀金價格 (R2)', color=COLORS["secondary"], fontsize=10)
        ax_pd.tick_params(axis='y', colors=COLORS["secondary"])
        ax_pd.yaxis.set_major_formatter(FuncFormatter(format_price))

        # 白銀在主軸
        ax_main.plot(x_indices, ag_close.values,
                     color=COLORS["primary"], linewidth=2,
                     label=f'白銀 {symbol_pair["silver"]} (R1)', zorder=4)
        ax_main.set_ylabel('白銀價格 (R1)', color=COLORS["primary"], fontsize=10)
        ax_main.tick_params(axis='y', colors=COLORS["primary"])
    else:
        # 只有白銀數據
        ax_main.plot(x_indices, ag_close.values,
                     color=COLORS["primary"], linewidth=2,
                     label=f'白銀 {symbol_pair["silver"]}', zorder=4)
        ax_main.set_ylabel('白銀價格', color=COLORS["primary"], fontsize=10)
        ax_main.tick_params(axis='y', colors=COLORS["primary"])

    ax_main.yaxis.set_major_formatter(FuncFormatter(format_price))

    # 標記拐點（使用背景色帶而非三角形）
    confirmed_events = [e for e in events if e["confirmed"]]
    unconfirmed_events = [e for e in events if not e["confirmed"]]

    # 背景帶寬度（以索引為單位）
    bg_width = 3

    # 確認拐點（綠色背景帶）
    for event in confirmed_events:
        event_idx = event["idx"]
        ax_main.axvspan(event_idx - bg_width/2, event_idx + bg_width/2,
                       color=COLORS["confirmed"], alpha=0.15, zorder=1)

    # 未確認拐點（紅色背景帶）
    for event in unconfirmed_events:
        event_idx = event["idx"]
        ax_main.axvspan(event_idx - bg_width/2, event_idx + bg_width/2,
                       color=COLORS["unconfirmed"], alpha=0.15, zorder=1)

    # 標註最新拐點
    if latest_event:
        latest_idx = latest_event["idx"]
        latest_price = latest_event["ag_price"]
        latest_type = "底部" if latest_event["turn"] == "bottom" else "頂部"
        latest_status = "[OK]" if latest_event["confirmed"] else "[X]"

        ax_main.annotate(
            f'{latest_type} {latest_status}\n${latest_price:.2f}',
            xy=(latest_idx, latest_price),
            xytext=(20, 20 if latest_event["turn"] == "bottom" else -20),
            textcoords='offset points',
            color=COLORS["confirmed"] if latest_event["confirmed"] else COLORS["unconfirmed"],
            fontsize=10,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS["background"],
                     edgecolor=COLORS["confirmed"] if latest_event["confirmed"] else COLORS["unconfirmed"],
                     linewidth=1.5),
            arrowprops=dict(arrowstyle='->',
                          color=COLORS["confirmed"] if latest_event["confirmed"] else COLORS["unconfirmed"],
                          linewidth=1.5)
        )

    # 網格
    ax_main.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax_main.set_axisbelow(True)

    # X 軸設定（遞增索引）
    ax_main.set_xlabel('', fontsize=10)
    ax_main.tick_params(axis='x', colors=COLORS["text_dim"])
    plt.setp(ax_main.get_xticklabels(), visible=False)  # 隱藏 X 軸標籤

    # 圖例（改為背景色帶說明）
    legend_elements = [
        plt.Line2D([0], [0], color=COLORS["primary"], linewidth=2,
                   label=f'白銀 {symbol_pair["silver"]}'),
    ]
    if pd_close is not None:
        legend_elements.append(
            plt.Line2D([0], [0], color=COLORS["secondary"], linewidth=1.5, alpha=0.7,
                       label=f'鈀金 {symbol_pair["palladium"]}')
        )
    legend_elements.extend([
        Rectangle((0, 0), 1, 1, fc=COLORS["confirmed"], alpha=0.15,
                  label='已確認拐點區域'),
        Rectangle((0, 0), 1, 1, fc=COLORS["unconfirmed"], alpha=0.15,
                  label='未確認拐點區域'),
    ])

    ax_main.legend(handles=legend_elements, loc='upper left', fontsize=8,
                   facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                   labelcolor=COLORS["text"])

    # === 中間：鈀金/白銀價格比率 ===

    if pd_close is not None and ag_close is not None:
        # 計算價格比率
        # 確保兩個時間序列對齊
        common_index = ag_close.index.intersection(pd_close.index)
        if len(common_index) > 0:
            ag_aligned = ag_close.reindex(common_index)
            pd_aligned = pd_close.reindex(common_index)

            ratio = pd_aligned / ag_aligned
            ratio_x_indices = np.arange(len(ratio))

            # 繪製比率線
            ax_ratio.plot(ratio_x_indices, ratio.values,
                         color=COLORS["tertiary"], linewidth=2,
                         label='Pd/Ag 價格比率', zorder=4)

            # 添加移動平均線
            if len(ratio) >= 20:
                ma20 = ratio.rolling(20).mean()
                ax_ratio.plot(ratio_x_indices, ma20.values,
                             color=COLORS["secondary"], linewidth=1.5, linestyle='--', alpha=0.7,
                             label='20期均線', zorder=3)

            # 標記確認/未確認區域（與主圖一致）
            for event in confirmed_events:
                event_idx = event["idx"]
                ax_ratio.axvspan(event_idx - bg_width/2, event_idx + bg_width/2,
                               color=COLORS["confirmed"], alpha=0.15, zorder=1)

            for event in unconfirmed_events:
                event_idx = event["idx"]
                ax_ratio.axvspan(event_idx - bg_width/2, event_idx + bg_width/2,
                               color=COLORS["unconfirmed"], alpha=0.15, zorder=1)

            # 標註最新比率值
            latest_ratio = ratio.iloc[-1]
            ax_ratio.annotate(
                f'{latest_ratio:.2f}',
                xy=(ratio_x_indices[-1], latest_ratio),
                xytext=(10, 0),
                textcoords='offset points',
                color=COLORS["tertiary"],
                fontsize=10,
                fontweight='bold',
                va='center'
            )

            ax_ratio.set_ylabel('Pd/Ag 比率', color=COLORS["tertiary"], fontsize=10)
            ax_ratio.tick_params(axis='y', colors=COLORS["tertiary"])
            ax_ratio.legend(loc='upper left', fontsize=8,
                          facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                          labelcolor=COLORS["text"])

            # 網格
            ax_ratio.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
            ax_ratio.set_axisbelow(True)

            # X 軸設定
            ax_ratio.tick_params(axis='x', colors=COLORS["text_dim"])
            plt.setp(ax_ratio.get_xticklabels(), visible=False)  # 隱藏 X 軸標籤（與主圖共享）

    # === 下半部：統計面板（直條圖） ===

    # 計算滾動確認率（每20個事件）
    window = 20
    rolling_conf_rate = []
    rolling_indices = []

    for i in range(window, len(events) + 1):
        window_events = events[i-window:i]
        conf_count = sum(1 for e in window_events if e["confirmed"])
        rolling_conf_rate.append(conf_count / window)
        # 使用最後一個事件的索引
        rolling_indices.append(window_events[-1]["idx"])

    if rolling_indices:
        # 根據確認率設定顏色
        bar_colors = [COLORS["confirmed"] if rate >= 0.8 else COLORS["level_line"]
                     for rate in rolling_conf_rate]

        # 繪製直條圖
        ax_stats.bar(rolling_indices, rolling_conf_rate,
                    width=1.5,  # bar 寬度
                    color=bar_colors,
                    alpha=0.7,
                    edgecolor='none',
                    label=f'滾動確認率 ({window}事件)')

        # 添加 80% 參考線
        ax_stats.axhline(y=0.8,
                        color=COLORS["text_dim"], linestyle='--', linewidth=1, alpha=0.5,
                        label='80% 門檻')

        # 添加整體確認率參考線
        ax_stats.axhline(y=summary["confirmation_rate"],
                        color=COLORS["tertiary"], linestyle='--', linewidth=1.5,
                        label=f'整體確認率 {summary["confirmation_rate"]*100:.1f}%')

    ax_stats.set_ylabel('確認率', color=COLORS["text"], fontsize=10)
    ax_stats.tick_params(axis='y', colors=COLORS["text"])
    ax_stats.yaxis.set_major_formatter(FuncFormatter(format_percent))
    ax_stats.set_ylim(0, 1.1)

    # 網格
    ax_stats.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
    ax_stats.set_axisbelow(True)

    # X 軸設定（顯示索引標籤）
    ax_stats.tick_params(axis='x', colors=COLORS["text_dim"], rotation=0)
    ax_stats.set_xlabel('K 棒索引', color=COLORS["text_dim"], fontsize=10)

    ax_stats.legend(loc='lower left', fontsize=8,
                   facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                   labelcolor=COLORS["text"])

    # === 標題 ===
    if title is None:
        start_date = data_range["start"]
        end_date = data_range["end"]
        title = f'白銀-鈀金跨金屬拐點確認分析 ({start_date} ~ {end_date})'

    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight='bold', y=0.98)

    # === 統計文字框 ===
    stats_text = (
        f'確認率: {summary["confirmation_rate"]*100:.1f}%  |  '
        f'未確認失敗率: {summary["unconfirmed_failure_rate"]*100:.1f}%  |  '
        f'總拐點: {summary["total_ag_turns"]}  |  '
        f'已確認: {summary["confirmed_turns"]}  |  '
        f'失敗: {summary["failed_moves"]}'
    )

    fig.text(0.5, 0.95, stats_text,
             color=COLORS["text_dim"], fontsize=9, ha='center',
             bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS["background"],
                      edgecolor=COLORS["grid"], linewidth=1))

    # === 解讀文字框 ===
    interp_text = interpretation["current_status"]

    fig.text(0.5, 0.04, interp_text,
             color=COLORS["text"], fontsize=9, ha='center',
             bbox=dict(boxstyle='round,pad=0.5',
                      facecolor=COLORS["background"],
                      edgecolor=COLORS["confirmed"] if latest_event and latest_event["confirmed"] else COLORS["unconfirmed"],
                      linewidth=2))

    # === 頁尾 ===
    fig.text(0.02, 0.01,
             f'資料來源: Yahoo Finance ({symbol_pair["silver"]}, {symbol_pair["palladium"]})',
             color=COLORS["text_dim"], fontsize=8, ha='left')

    fig.text(0.98, 0.01,
             f'數據期間: {data_range["start"]} ~ {data_range["end"]}',
             color=COLORS["text_dim"], fontsize=8, ha='right')

    # === 佈局調整 ===
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, bottom=0.06, hspace=0.25)

    # === 輸出 ===
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS["background"])
    plt.close()

    print(f"✓ Bloomberg 風格圖表已儲存: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="生成 Bloomberg 風格的鈀金-白銀跨金屬確認圖表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 從 JSON 結果生成圖表
  python plot_bloomberg_style.py --input result.json --output output/palladium_silver_2026-01-26.png

  # 自訂標題
  python plot_bloomberg_style.py --input result.json --output output/chart.png --title "我的分析"
        """
    )

    parser.add_argument('--input', type=str, required=True,
                       help='detect-palladium-lead-silver-turns 的 JSON 輸出文件')
    parser.add_argument('--output', type=str, required=True,
                       help='輸出圖表路徑（含檔名）')
    parser.add_argument('--title', type=str,
                       help='圖表標題（可選）')

    args = parser.parse_args()

    # 讀取 JSON 結果
    with open(args.input, 'r', encoding='utf-8') as f:
        result_json = json.load(f)

    # 生成圖表
    plot_palladium_silver_confirmation(
        result_json,
        args.output,
        title=args.title
    )


if __name__ == "__main__":
    main()
