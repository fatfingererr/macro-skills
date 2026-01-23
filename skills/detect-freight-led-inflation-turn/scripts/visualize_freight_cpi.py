#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CASS Freight Index vs CPI YoY 領先性視覺化

核心特徵：
1. CASS Freight Index 向前移動 6 個月 (6M fwd)
2. 雙軸對比：CPI YoY (左軸) vs CASS (右軸)
3. 衰退區間標記 (NBER Recession)
4. Bloomberg 風格配色
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime

# 中文字體設定
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'PingFang TC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Bloomberg 風格配色
COLORS = {
    "background": "#1a1a2e",
    "grid": "#2d2d44",
    "text": "#ffffff",
    "text_dim": "#888888",
    "cpi_line": "#1e90ff",          # 藍色 - CPI
    "cass_line": "#888888",         # 灰色 - CASS (與參考圖一致)
    "recession": "#ffcccc",         # 淡粉紅色 - 衰退區間
    "recession_alpha": 0.3,
    "zero_line": "#666666",
}

# NBER 衰退區間 (美國官方定義)
NBER_RECESSIONS = [
    ("1990-07-01", "1991-03-01"),
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]


def load_cass_data(cache_path: str) -> pd.DataFrame:
    """載入 CASS Freight Index 快取數據"""
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 解析數據
    result = {}
    for chart in data:
        for series in chart.get('series', []):
            name = series.get('name', '')
            series_data = series.get('data', [])

            if len(series_data) == 0:
                continue

            # 建立 DataFrame
            df = pd.DataFrame(series_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 映射名稱
            if '運載量(年增率)' in name or 'Shipment' in name.lower():
                result['cass_shipments_yoy'] = df['y']
            elif '總支出(年增率)' in name or 'Expenditure' in name.lower():
                result['cass_expenditures_yoy'] = df['y']

    return pd.DataFrame(result)


def fetch_cpi_data(start_date: str = "1990-01-01") -> pd.Series:
    """從 FRED 獲取 CPI YoY 數據"""
    try:
        import requests

        # FRED API - CPI All Items YoY
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd={start_date}"

        df = pd.read_csv(url)
        # 處理不同的列名格式
        date_col = df.columns[0]
        value_col = df.columns[1]

        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
        df.columns = ['cpi']

        # 計算 YoY
        cpi_yoy = (df['cpi'] / df['cpi'].shift(12) - 1) * 100
        cpi_yoy = cpi_yoy.dropna()

        return cpi_yoy
    except Exception as e:
        print(f"警告：無法獲取 CPI 數據: {e}")
        return None


def plot_freight_cpi_comparison(
    cass_df: pd.DataFrame,
    cpi_yoy: pd.Series,
    output_path: str,
    lead_months: int = 6,
    start_date: str = None,
    title: str = "US Headline CPI YoY% Change vs. Cass Freight Index: Shipment Volumes"
):
    """
    繪製 CASS Freight vs CPI 對比圖

    關鍵：CASS 向前移動 lead_months 個月
    """
    plt.style.use('dark_background')

    fig, ax1 = plt.subplots(figsize=(14, 8), facecolor=COLORS["background"])
    ax1.set_facecolor(COLORS["background"])

    # 準備數據
    cass_yoy = cass_df['cass_shipments_yoy'].copy()

    # 設定起始日期
    if start_date:
        start_ts = pd.Timestamp(start_date)
        cass_yoy = cass_yoy[cass_yoy.index >= start_ts]
        if cpi_yoy is not None:
            cpi_yoy = cpi_yoy[cpi_yoy.index >= start_ts]

    # 重採樣到月頻
    cass_yoy = cass_yoy.resample('ME').last().ffill()
    if cpi_yoy is not None:
        cpi_yoy = cpi_yoy.resample('ME').last().ffill()

    # 計算 CASS 向右移動後的新索引（會突出到未來）
    cass_forward_index = cass_yoy.index + pd.DateOffset(months=lead_months)
    cass_forward = pd.Series(cass_yoy.values, index=cass_forward_index)

    # 設定 X 軸範圍：從 start_date 到 CASS forward 的最後日期
    x_min = cass_yoy.index.min()
    x_max = cass_forward.index.max()  # CASS 會突出到 CPI 之後

    # === 繪製衰退區間 ===
    for start, end in NBER_RECESSIONS:
        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end)
        if start_dt >= cass_yoy.index.min() and start_dt <= cass_yoy.index.max():
            ax1.axvspan(start_dt, end_dt,
                       color=COLORS["recession"],
                       alpha=COLORS["recession_alpha"],
                       zorder=1,
                       label='Recession' if start == NBER_RECESSIONS[0][0] else '')

    # === 左軸：CPI YoY ===
    if cpi_yoy is not None:
        line_cpi, = ax1.plot(cpi_yoy.index, cpi_yoy.values,
                            color=COLORS["cpi_line"],
                            linewidth=1.5,
                            label='US Headline CPI YoY%',
                            zorder=3)
        ax1.set_ylabel('CPI YoY%', color=COLORS["cpi_line"], fontsize=10)
        ax1.tick_params(axis='y', labelcolor=COLORS["cpi_line"])

    # 設定左軸範圍
    if cpi_yoy is not None:
        ymin = min(cpi_yoy.min(), -2)
        ymax = max(cpi_yoy.max(), 8)
        ax1.set_ylim(ymin - 1, ymax + 1)

    # === 右軸：CASS Freight Index (6M forward) ===
    ax2 = ax1.twinx()

    # cass_forward 已在上方計算，向右移動 lead_months 個月
    # 這樣 CASS 的最新數據會「突出」到 CPI 數據的右邊

    line_cass, = ax2.plot(cass_forward.index, cass_forward.values,
                         color=COLORS["cass_line"],
                         linewidth=1.5,
                         label=f'Cass Freight Index ({lead_months}M fwd, rhs)',
                         zorder=2)
    ax2.set_ylabel(f'CASS Shipments YoY% ({lead_months}M fwd)',
                  color=COLORS["cass_line"], fontsize=10)
    ax2.tick_params(axis='y', labelcolor=COLORS["cass_line"])

    # 設定右軸範圍
    cass_min = cass_forward.min()
    cass_max = cass_forward.max()
    ax2.set_ylim(cass_min - 5, cass_max + 5)

    # === 零線 ===
    ax1.axhline(y=0, color=COLORS["zero_line"], linestyle='-', linewidth=0.8, alpha=0.5)
    ax2.axhline(y=0, color=COLORS["zero_line"], linestyle='-', linewidth=0.8, alpha=0.5)

    # === 網格 ===
    ax1.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)

    # === X 軸格式與範圍 ===
    ax1.set_xlim(x_min, x_max)  # 延伸到 CASS forward 的最後日期
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator(5))
    ax1.tick_params(axis='x', colors=COLORS["text_dim"])

    # === 標題 ===
    fig.suptitle(title,
                color=COLORS["text"],
                fontsize=14,
                fontweight='bold',
                y=0.98)

    # === 圖例 ===
    lines = [line_cpi, line_cass] if cpi_yoy is not None else [line_cass]
    labels = [l.get_label() for l in lines]

    # 添加 Recession 到圖例
    from matplotlib.patches import Patch
    recession_patch = Patch(facecolor=COLORS["recession"],
                           alpha=COLORS["recession_alpha"],
                           label='Recession')

    ax1.legend(handles=lines + [recession_patch],
              loc='upper left',
              fontsize=9,
              facecolor=COLORS["background"],
              edgecolor=COLORS["grid"],
              labelcolor=COLORS["text"])

    # === 頁尾 ===
    latest_date = cass_yoy.index[-1]
    fig.text(0.98, 0.02,
            f'As of: {latest_date.strftime("%Y-%m-%d")}',
            color=COLORS["text_dim"],
            fontsize=8,
            ha='right')

    # === 標註最新值 ===
    if cpi_yoy is not None and len(cpi_yoy) > 0:
        latest_cpi = cpi_yoy.iloc[-1]
        latest_cpi_date = cpi_yoy.index[-1]
        ax1.annotate(f'{latest_cpi:.1f}%',
                    xy=(latest_cpi_date, latest_cpi),
                    xytext=(10, 0),
                    textcoords='offset points',
                    color=COLORS["cpi_line"],
                    fontsize=10,
                    fontweight='bold',
                    va='center')

    # CASS 最新值（標註在 forward 後的位置，即圖表最右邊）
    latest_cass = cass_forward.iloc[-1]
    latest_cass_date = cass_forward.index[-1]
    ax2.annotate(f'{latest_cass:.1f}%',
                xy=(latest_cass_date, latest_cass),
                xytext=(10, 0),
                textcoords='offset points',
                color=COLORS["cass_line"],
                fontsize=10,
                fontweight='bold',
                va='center')

    # === 輸出 ===
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path,
               dpi=150,
               bbox_inches='tight',
               facecolor=COLORS["background"])
    plt.close()

    print(f"圖表已儲存: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description='CASS Freight vs CPI 視覺化')
    parser.add_argument('--cache', type=str, default='cache/cass_freight_cdp.json',
                       help='CASS 數據快取路徑')
    parser.add_argument('--output', type=str, default=None,
                       help='輸出路徑（預設: output/freight_cpi_YYYY-MM-DD.png）')
    parser.add_argument('--lead-months', type=int, default=6,
                       help='CASS 領先月數（預設: 6）')
    parser.add_argument('--start', type=str, default='2000-01-01',
                       help='起始日期')
    parser.add_argument('--no-cpi', action='store_true',
                       help='不抓取 CPI 數據，只顯示 CASS')

    args = parser.parse_args()

    # 設定輸出路徑
    if args.output is None:
        today = datetime.now().strftime('%Y-%m-%d')
        output_path = f'../../output/freight_cpi_{today}.png'
    else:
        output_path = args.output

    # 載入 CASS 數據
    print("載入 CASS Freight Index 數據...")
    cass_df = load_cass_data(args.cache)
    print(f"  數據範圍: {cass_df.index.min()} ~ {cass_df.index.max()}")
    print(f"  最新 Shipments YoY: {cass_df['cass_shipments_yoy'].iloc[-1]:.2f}%")

    # 獲取 CPI 數據
    cpi_yoy = None
    if not args.no_cpi:
        print("\n獲取 CPI 數據...")
        cpi_yoy = fetch_cpi_data(args.start)
        if cpi_yoy is not None:
            print(f"  數據範圍: {cpi_yoy.index.min()} ~ {cpi_yoy.index.max()}")
            print(f"  最新 CPI YoY: {cpi_yoy.iloc[-1]:.2f}%")

    # 繪製圖表
    print(f"\n繪製圖表（CASS {args.lead_months}M forward）...")
    plot_freight_cpi_comparison(
        cass_df=cass_df,
        cpi_yoy=cpi_yoy,
        output_path=output_path,
        lead_months=args.lead_months,
        start_date=args.start
    )


if __name__ == "__main__":
    main()
