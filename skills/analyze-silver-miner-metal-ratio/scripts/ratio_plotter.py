#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
銀礦股價/銀價比率視覺化工具

生成比率走勢圖，標記當前位置與歷史分位數區間。
支援輸出到指定目錄，檔名包含日期。

Usage:
    python ratio_plotter.py --quick
    python ratio_plotter.py --miner-proxy SIL --metal-proxy SI=F --output-dir ../../output
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("錯誤：需要安裝 yfinance。請執行：pip install yfinance")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非互動式後端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
except ImportError:
    print("錯誤：需要安裝 matplotlib。請執行：pip install matplotlib")
    sys.exit(1)

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="銀礦股價/銀價比率視覺化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--quick", "-q", action="store_true", help="使用預設參數快速生成圖表")
    parser.add_argument("--miner-proxy", type=str, default="SIL", help="白銀礦業代表（預設：SIL）")
    parser.add_argument("--metal-proxy", type=str, default="SI=F", help="白銀價格代表（預設：SI=F）")
    parser.add_argument("--start-date", type=str, default=None, help="歷史回溯起點（YYYY-MM-DD）")
    parser.add_argument("--freq", type=str, default="1wk", choices=["1d", "1wk", "1mo"], help="取樣頻率")
    parser.add_argument("--smoothing-window", type=int, default=4, help="比率平滑視窗")
    parser.add_argument("--bottom-quantile", type=float, default=0.20, help="底部估值區分位數")
    parser.add_argument("--top-quantile", type=float, default=0.80, help="頂部估值區分位數")
    parser.add_argument("--output-dir", type=str, default=None, help="輸出目錄（預設：當前目錄）")
    parser.add_argument("--dpi", type=int, default=150, help="圖片解析度")
    parser.add_argument("--show", action="store_true", help="顯示圖表視窗")
    parser.add_argument("--comprehensive", "-c", action="store_true",
                        help="生成完整版圖表（含底部事件標記、前瞻報酬統計）")

    return parser.parse_args()


def fetch_and_process_data(
    miner_proxy: str,
    metal_proxy: str,
    start_date: str,
    freq: str,
    smoothing_window: int
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """取得並處理數據"""

    # 下載數據
    tickers = [miner_proxy, metal_proxy]
    px = yf.download(tickers, start=start_date, auto_adjust=True, progress=False)

    # 提取收盤價
    if isinstance(px.columns, pd.MultiIndex):
        close = px['Close']
    else:
        close = px

    close = close.dropna(how='all').ffill().dropna()
    miner = close[miner_proxy]
    metal = close[metal_proxy]

    # 重新取樣
    if freq == "1wk":
        miner = miner.resample("W-FRI").last()
        metal = metal.resample("W-FRI").last()
    elif freq == "1mo":
        miner = miner.resample("ME").last()
        metal = metal.resample("ME").last()

    miner = miner.dropna()
    metal = metal.dropna()

    # 對齊索引
    common_idx = miner.index.intersection(metal.index)
    miner = miner.loc[common_idx]
    metal = metal.loc[common_idx]

    # 計算比率
    ratio = miner / metal
    if smoothing_window > 1:
        ratio = ratio.rolling(smoothing_window).mean()
    ratio = ratio.dropna()

    return miner.loc[ratio.index], metal.loc[ratio.index], ratio


def detect_bottom_events(
    ratio: pd.Series,
    bottom_thr: float,
    min_separation_days: int = 180
) -> List[datetime]:
    """偵測底部事件並去重"""
    is_bottom = ratio <= bottom_thr
    bottom_dates = ratio[is_bottom].index.tolist()

    dedup = []
    last = None
    for d in bottom_dates:
        if last is None or (d - last).days >= min_separation_days:
            dedup.append(d)
            last = d
    return dedup


def calculate_forward_returns(
    metal: pd.Series,
    event_dates: List[datetime],
    forward_horizons: List[int] = [52, 104, 156]
) -> Dict[int, Dict[str, Any]]:
    """計算事件後的前瞻報酬"""
    results = {}

    for H in forward_horizons:
        rets = []
        for d in event_dates:
            if d in metal.index:
                i = metal.index.get_loc(d)
                j = i + H
                if j < len(metal):
                    ret = float(metal.iloc[j] / metal.iloc[i] - 1)
                    rets.append(ret)

        if rets:
            horizon_years = H / 52
            results[H] = {
                "horizon_label": f"{horizon_years:.0f}Y",
                "count": len(rets),
                "median": float(np.median(rets)),
                "mean": float(np.mean(rets)),
                "win_rate": float(np.mean([r > 0 for r in rets])),
                "best": float(np.max(rets)),
                "worst": float(np.min(rets))
            }
        else:
            results[H] = {
                "horizon_label": f"{H}W",
                "count": 0,
                "median": None,
                "mean": None,
                "win_rate": None,
                "best": None,
                "worst": None
            }

    return results


def create_ratio_chart(
    miner: pd.Series,
    metal: pd.Series,
    ratio: pd.Series,
    miner_proxy: str,
    metal_proxy: str,
    bottom_quantile: float,
    top_quantile: float,
    output_path: str,
    dpi: int,
    show: bool
) -> str:
    """
    創建比率分析圖表

    包含三個子圖：
    1. 比率走勢 + 分位數區間
    2. 礦業價格走勢
    3. 白銀價格走勢
    """

    # 計算門檻
    bottom_thr = ratio.quantile(bottom_quantile)
    top_thr = ratio.quantile(top_quantile)
    median_thr = ratio.median()
    current_ratio = ratio.iloc[-1]
    ratio_percentile = ratio.rank(pct=True).iloc[-1] * 100

    # 判斷區間
    if current_ratio <= bottom_thr:
        zone = "底部"
        zone_color = "green"
    elif current_ratio >= top_thr:
        zone = "頂部"
        zone_color = "red"
    else:
        zone = "中性"
        zone_color = "gray"

    # 創建圖表
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                              gridspec_kw={'height_ratios': [2, 1, 1], 'hspace': 0.05})

    # ===== 子圖 1: 比率走勢 =====
    ax1 = axes[0]

    # 填充底部區間（綠色）
    ax1.fill_between(ratio.index, ratio.min() * 0.95, bottom_thr,
                     alpha=0.15, color='green', label=f'底部區間 (<={bottom_quantile*100:.0f}%)')

    # 填充頂部區間（紅色）
    ax1.fill_between(ratio.index, top_thr, ratio.max() * 1.05,
                     alpha=0.15, color='red', label=f'頂部區間 (>={top_quantile*100:.0f}%)')

    # 比率線
    ax1.plot(ratio.index, ratio.values, color='navy', linewidth=1.5, label='比率 (4週平滑)')

    # 門檻線
    ax1.axhline(y=bottom_thr, color='green', linestyle='--', linewidth=1, alpha=0.7)
    ax1.axhline(y=top_thr, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax1.axhline(y=median_thr, color='gray', linestyle=':', linewidth=1, alpha=0.7, label='中位數')

    # 當前位置標記
    ax1.scatter([ratio.index[-1]], [current_ratio], color=zone_color, s=100, zorder=5,
                edgecolors='black', linewidths=1.5)

    # 標註當前值
    ax1.annotate(
        f'當前: {current_ratio:.3f}\n({ratio_percentile:.1f}% 分位數)\n區間: {zone}',
        xy=(ratio.index[-1], current_ratio),
        xytext=(15, 0),
        textcoords='offset points',
        fontsize=10,
        fontweight='bold',
        color=zone_color,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=zone_color, alpha=0.9),
        ha='left',
        va='center'
    )

    # 標註門檻值
    ax1.text(ratio.index[0], bottom_thr, f' 底部門檻: {bottom_thr:.3f}',
             fontsize=9, color='green', va='center')
    ax1.text(ratio.index[0], top_thr, f' 頂部門檻: {top_thr:.3f}',
             fontsize=9, color='red', va='center')

    ax1.set_ylabel(f'{miner_proxy} / {metal_proxy} 比率', fontsize=11)
    ax1.set_title(f'銀礦股價/銀價比率分析 ({miner_proxy}/{metal_proxy})', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(ratio.min() * 0.95, ratio.max() * 1.1)

    # ===== 子圖 2: 礦業價格 =====
    ax2 = axes[1]
    ax2.plot(miner.index, miner.values, color='darkblue', linewidth=1.2)
    ax2.fill_between(miner.index, 0, miner.values, alpha=0.1, color='blue')
    ax2.set_ylabel(f'{miner_proxy} 價格', fontsize=10)
    ax2.grid(True, alpha=0.3)

    # 標註當前價格
    ax2.annotate(f'{miner.iloc[-1]:.2f}', xy=(miner.index[-1], miner.iloc[-1]),
                 xytext=(5, 0), textcoords='offset points', fontsize=9, color='darkblue')

    # ===== 子圖 3: 白銀價格 =====
    ax3 = axes[2]
    ax3.plot(metal.index, metal.values, color='silver', linewidth=1.2)
    ax3.fill_between(metal.index, 0, metal.values, alpha=0.2, color='gray')
    ax3.set_ylabel(f'{metal_proxy} 價格', fontsize=10)
    ax3.grid(True, alpha=0.3)

    # 標註當前價格
    ax3.annotate(f'{metal.iloc[-1]:.2f}', xy=(metal.index[-1], metal.iloc[-1]),
                 xytext=(5, 0), textcoords='offset points', fontsize=9, color='dimgray')

    # X 軸格式
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax3.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)

    # 底部標註
    fig.text(0.5, 0.01,
             f'生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 數據範圍: {ratio.index[0].strftime("%Y-%m-%d")} 至 {ratio.index[-1].strftime("%Y-%m-%d")} | 週數: {len(ratio)}',
             ha='center', fontsize=9, color='gray')

    plt.tight_layout(rect=[0, 0.02, 1, 1])

    # 保存圖表
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    print(f"圖表已保存至: {output_path}")

    if show:
        plt.show()
    else:
        plt.close()

    return output_path


def create_comprehensive_chart(
    miner: pd.Series,
    metal: pd.Series,
    ratio: pd.Series,
    miner_proxy: str,
    metal_proxy: str,
    bottom_quantile: float,
    top_quantile: float,
    output_path: str,
    dpi: int,
    show: bool
) -> str:
    """
    創建完整版比率分析圖表

    包含四個子圖：
    1. 比率走勢 + 分位數區間 + 底部事件標記
    2. 前瞻報酬統計柱狀圖
    3. 礦業價格走勢
    4. 白銀價格走勢
    """

    # 計算門檻
    bottom_thr = ratio.quantile(bottom_quantile)
    top_thr = ratio.quantile(top_quantile)
    median_thr = ratio.median()
    current_ratio = ratio.iloc[-1]
    ratio_percentile = ratio.rank(pct=True).iloc[-1] * 100

    # 偵測底部事件
    bottom_events = detect_bottom_events(ratio, bottom_thr)

    # 計算前瞻報酬
    forward_returns = calculate_forward_returns(metal, bottom_events)

    # 判斷區間
    if current_ratio <= bottom_thr:
        zone = "底部"
        zone_color = "green"
    elif current_ratio >= top_thr:
        zone = "頂部"
        zone_color = "red"
    else:
        zone = "中性"
        zone_color = "gray"

    # 計算情境推演
    miner_multiplier = top_thr / current_ratio
    metal_drop_pct = 1 - (current_ratio / top_thr)

    # 創建圖表 (2x2 佈局)
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.5, 1], width_ratios=[2, 1],
                          hspace=0.25, wspace=0.15)

    # ===== 子圖 1: 比率走勢（左上，跨兩列） =====
    ax1 = fig.add_subplot(gs[0, :])

    # 填充底部區間
    ax1.fill_between(ratio.index, ratio.min() * 0.95, bottom_thr,
                     alpha=0.15, color='green', label=f'底部區間 (<={bottom_quantile*100:.0f}%)')

    # 填充頂部區間
    ax1.fill_between(ratio.index, top_thr, ratio.max() * 1.05,
                     alpha=0.15, color='red', label=f'頂部區間 (>={top_quantile*100:.0f}%)')

    # 比率線
    ax1.plot(ratio.index, ratio.values, color='navy', linewidth=1.5, label='比率 (4週平滑)')

    # 門檻線
    ax1.axhline(y=bottom_thr, color='green', linestyle='--', linewidth=1, alpha=0.7)
    ax1.axhline(y=top_thr, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax1.axhline(y=median_thr, color='gray', linestyle=':', linewidth=1, alpha=0.7, label='中位數')

    # 底部事件垂直線標記
    for i, event_date in enumerate(bottom_events):
        ax1.axvline(x=event_date, color='darkgreen', linestyle='-', linewidth=1, alpha=0.5)
        # 只標註前幾個事件，避免擁擠
        if i < 4:
            ax1.annotate(event_date.strftime('%Y-%m'),
                        xy=(event_date, ratio.max() * 0.95),
                        fontsize=7, color='darkgreen', rotation=90, va='top', ha='right')

    # 當前位置標記
    ax1.scatter([ratio.index[-1]], [current_ratio], color=zone_color, s=120, zorder=5,
                edgecolors='black', linewidths=2, marker='o')

    # 標註當前值
    ax1.annotate(
        f'當前: {current_ratio:.3f}\n({ratio_percentile:.1f}% 分位數)\n區間: {zone}',
        xy=(ratio.index[-1], current_ratio),
        xytext=(15, 0),
        textcoords='offset points',
        fontsize=10,
        fontweight='bold',
        color=zone_color,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=zone_color, alpha=0.9),
        ha='left',
        va='center'
    )

    # 標註門檻值
    ax1.text(ratio.index[0], bottom_thr * 1.02, f' 底部門檻: {bottom_thr:.3f}',
             fontsize=9, color='green', va='bottom')
    ax1.text(ratio.index[0], top_thr * 0.98, f' 頂部門檻: {top_thr:.3f}',
             fontsize=9, color='red', va='top')

    ax1.set_ylabel(f'{miner_proxy} / {metal_proxy} 比率', fontsize=11)
    ax1.set_title(f'銀礦股價/銀價比率分析 ({miner_proxy}/{metal_proxy}) | 底部事件: {len(bottom_events)} 次',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(ratio.min() * 0.9, ratio.max() * 1.1)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))

    # ===== 子圖 2: 前瞻報酬柱狀圖（右下） =====
    ax2 = fig.add_subplot(gs[1, 1])

    horizons = list(forward_returns.keys())
    labels = [forward_returns[h]['horizon_label'] for h in horizons]
    medians = [forward_returns[h]['median'] * 100 if forward_returns[h]['median'] else 0 for h in horizons]
    win_rates = [forward_returns[h]['win_rate'] * 100 if forward_returns[h]['win_rate'] else 0 for h in horizons]
    counts = [forward_returns[h]['count'] for h in horizons]

    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax2.bar(x - width/2, medians, width, label='中位數報酬 (%)', color='steelblue', alpha=0.8)
    bars2 = ax2.bar(x + width/2, win_rates, width, label='勝率 (%)', color='forestgreen', alpha=0.8)

    # 標註數值
    for bar, val, cnt in zip(bars1, medians, counts):
        if val > 0:
            ax2.annotate(f'{val:.0f}%\n(n={cnt})',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8)

    for bar, val in zip(bars2, win_rates):
        if val > 0:
            ax2.annotate(f'{val:.0f}%',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8, color='darkgreen')

    ax2.set_xlabel('前瞻期', fontsize=10)
    ax2.set_ylabel('百分比 (%)', fontsize=10)
    ax2.set_title('底部事件後白銀前瞻表現', fontsize=11, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(0, max(max(medians), max(win_rates)) * 1.3 if medians else 100)

    # ===== 子圖 3: 價格對比（左下） =====
    ax3 = fig.add_subplot(gs[1, 0])

    # 正規化價格（起始點 = 100）
    miner_norm = miner / miner.iloc[0] * 100
    metal_norm = metal / metal.iloc[0] * 100

    ax3.plot(miner.index, miner_norm.values, color='darkblue', linewidth=1.5, label=f'{miner_proxy} (礦業)')
    ax3.plot(metal.index, metal_norm.values, color='silver', linewidth=1.5, label=f'{metal_proxy} (白銀)')

    # 標記底部事件
    for event_date in bottom_events:
        ax3.axvline(x=event_date, color='green', linestyle=':', linewidth=0.8, alpha=0.5)

    ax3.set_ylabel('正規化價格 (起點=100)', fontsize=10)
    ax3.set_title(f'價格走勢對比 | 礦業需漲 {(miner_multiplier-1)*100:.0f}% 才回到頂部估值', fontsize=11, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))

    # 標註當前價格
    ax3.annotate(f'{miner_proxy}: ${miner.iloc[-1]:.1f}',
                 xy=(miner.index[-1], miner_norm.iloc[-1]),
                 xytext=(5, 10), textcoords='offset points',
                 fontsize=9, color='darkblue')
    ax3.annotate(f'{metal_proxy}: ${metal.iloc[-1]:.1f}',
                 xy=(metal.index[-1], metal_norm.iloc[-1]),
                 xytext=(5, -15), textcoords='offset points',
                 fontsize=9, color='gray')

    # 底部標註
    fig.text(0.5, 0.01,
             f'生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 數據: {ratio.index[0].strftime("%Y-%m-%d")} ~ {ratio.index[-1].strftime("%Y-%m-%d")} | 情境: 白銀需跌 {metal_drop_pct*100:.0f}% 才回到頂部',
             ha='center', fontsize=9, color='gray')

    # 保存圖表
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    print(f"完整版圖表已保存至: {output_path}")

    if show:
        plt.show()
    else:
        plt.close()

    return output_path


def main():
    """主程式"""
    args = parse_args()

    # 設定參數
    start_date = args.start_date or (datetime.now() - timedelta(days=365 * 10)).strftime("%Y-%m-%d")

    # 設定輸出路徑
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = "."

    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    # 生成檔名（包含日期）
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"sil_silver_ratio_{today}.png"
    output_path = os.path.join(output_dir, filename)

    print(f"正在下載數據: {args.miner_proxy}, {args.metal_proxy}")
    print(f"時間範圍: {start_date} 至今")

    # 取得數據
    miner, metal, ratio = fetch_and_process_data(
        miner_proxy=args.miner_proxy,
        metal_proxy=args.metal_proxy,
        start_date=start_date,
        freq=args.freq,
        smoothing_window=args.smoothing_window
    )

    print(f"數據點數: {len(ratio)}")
    print(f"當前比率: {ratio.iloc[-1]:.4f}")
    print(f"歷史分位數: {ratio.rank(pct=True).iloc[-1] * 100:.1f}%")

    # 選擇圖表類型
    if args.comprehensive:
        # 完整版圖表（含底部事件、前瞻報酬）
        filename = f"sil_silver_ratio_comprehensive_{today}.png"
        output_path = os.path.join(output_dir, filename)
        create_comprehensive_chart(
            miner=miner,
            metal=metal,
            ratio=ratio,
            miner_proxy=args.miner_proxy,
            metal_proxy=args.metal_proxy,
            bottom_quantile=args.bottom_quantile,
            top_quantile=args.top_quantile,
            output_path=output_path,
            dpi=args.dpi,
            show=args.show
        )
    else:
        # 基本版圖表
        create_ratio_chart(
            miner=miner,
            metal=metal,
            ratio=ratio,
            miner_proxy=args.miner_proxy,
            metal_proxy=args.metal_proxy,
            bottom_quantile=args.bottom_quantile,
            top_quantile=args.top_quantile,
            output_path=output_path,
            dpi=args.dpi,
            show=args.show
        )

    return output_path


if __name__ == "__main__":
    main()
