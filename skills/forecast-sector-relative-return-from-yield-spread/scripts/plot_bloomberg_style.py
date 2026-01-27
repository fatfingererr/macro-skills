#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloomberg 風格：美國公債利差領先板塊相對報酬分析圖表

根據 forecast-sector-relative-return-from-yield-spread 分析結果，
生成符合 Bloomberg 風格的視覺化圖表。
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式後端，必須在 import pyplot 前

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO
import requests

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
    "primary": "#ff6b35",      # 主要指標（橙紅）- 相對報酬
    "secondary": "#ffaa00",    # 次要指標（橙黃）- 利差
    "tertiary": "#ffff00",     # 輔助指標（黃色）
    "area_fill": "#ff8c00",
    "area_alpha": 0.4,
    "level_line": "#666666",
    "positive": "#00ff88",     # 正相關（綠色）
    "negative": "#ff4444",     # 負相關（紅色）
    "inverted": "#ff6b6b",     # 倒掛區域
    "normal": "#4ecdc4",       # 正常曲線區域
}

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def format_percent(x, pos):
    """百分比格式化"""
    return f'{x:.1f}%'


def format_ratio(x, pos):
    """比率格式化"""
    return f'{x:.2f}'


def format_corr(x, pos):
    """相關係數格式化"""
    return f'{x:.2f}'


def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取時間序列"""
    params = {"id": series_id, "cosd": start_date, "coed": end_date}
    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
        df = df.dropna().set_index("DATE")
        return df[series_id]
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return pd.Series(dtype=float)


def fetch_price_series(ticker: str, start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 抓取價格"""
    if yf is None:
        return pd.Series(dtype=float)
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return pd.Series(dtype=float)
        if isinstance(data.columns, pd.MultiIndex):
            if ("Close", ticker) in data.columns:
                return data[("Close", ticker)]
            elif ("Adj Close", ticker) in data.columns:
                return data[("Adj Close", ticker)]
            else:
                close_cols = [c for c in data.columns if c[0] in ["Close", "Adj Close"]]
                if close_cols:
                    return data[close_cols[0]]
        else:
            if "Adj Close" in data.columns:
                return data["Adj Close"]
            elif "Close" in data.columns:
                return data["Close"]
        return pd.Series(dtype=float)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.Series(dtype=float)


def to_weekly(series: pd.Series) -> pd.Series:
    """轉換為週頻"""
    return series.resample("W-FRI").last().dropna()


def compute_future_rel_return(ratio: pd.Series, horizon_periods: int) -> pd.Series:
    """計算未來 H 期的對數相對報酬"""
    return np.log(ratio.shift(-horizon_periods) / ratio)


def lead_scan(spread: pd.Series, ratio: pd.Series, leads: list, freq: str = "weekly") -> dict:
    """掃描多個領先期"""
    results = {}
    periods_per_month = 4 if freq == "weekly" else 1

    for lead in leads:
        horizon_periods = int(lead * periods_per_month)
        y = compute_future_rel_return(ratio, horizon_periods)
        valid = spread.notna() & y.notna()

        if valid.sum() < 30:
            results[lead] = None
            continue

        corr = np.corrcoef(spread[valid], y[valid])[0, 1]
        results[lead] = float(corr)

    return results


def stability_check(spread: pd.Series, y: pd.Series) -> dict:
    """子樣本穩定性檢查"""
    valid = spread.notna() & y.notna()
    spread_clean = spread[valid]
    y_clean = y[valid]

    n = len(spread_clean)
    mid = n // 2

    first_half = spread_clean.iloc[:mid]
    y_first = y_clean.iloc[:mid]
    second_half = spread_clean.iloc[mid:]
    y_second = y_clean.iloc[mid:]

    corr_first = np.corrcoef(first_half, y_first)[0, 1] if len(first_half) > 10 else None
    corr_second = np.corrcoef(second_half, y_second)[0, 1] if len(second_half) > 10 else None

    return {
        "first_half_period": f"{spread_clean.index[0].strftime('%Y-%m')} ~ {spread_clean.index[mid-1].strftime('%Y-%m')}",
        "second_half_period": f"{spread_clean.index[mid].strftime('%Y-%m')} ~ {spread_clean.index[-1].strftime('%Y-%m')}",
        "first_half_corr": float(corr_first) if corr_first is not None else None,
        "second_half_corr": float(corr_second) if corr_second is not None else None,
    }


def plot_yield_spread_forecast(
    result_json: dict = None,
    output_path: str = None,
    title: str = None,
    lookback_years: int = 18,
    lead_months: int = 24,
    risk_ticker: str = "QQQ",
    defensive_ticker: str = "XLV"
):
    """
    繪製美國公債利差領先板塊相對報酬分析圖表

    Parameters
    ----------
    result_json : dict, optional
        spread_forecaster.py 的輸出結果，如果提供則使用其中的數據
    output_path : str
        輸出圖表路徑
    title : str, optional
        圖表標題，默認自動生成
    lookback_years : int
        回測年數
    lead_months : int
        領先期（月）
    risk_ticker : str
        成長股標的
    defensive_ticker : str
        防禦股標的
    """
    plt.style.use('dark_background')

    # 獲取數據
    print("抓取數據中...")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback_years * 365 + 365)).strftime("%Y-%m-%d")

    dgs2 = fetch_fred_series("DGS2", start_date, end_date)
    dgs10 = fetch_fred_series("DGS10", start_date, end_date)
    risk_price = fetch_price_series(risk_ticker, start_date, end_date)
    defensive_price = fetch_price_series(defensive_ticker, start_date, end_date)

    if dgs2.empty or dgs10.empty or risk_price.empty or defensive_price.empty:
        print("Error: 無法抓取必要數據")
        return None

    # 計算利差與比率
    spread = to_weekly(dgs2 - dgs10)
    ratio = to_weekly(risk_price / defensive_price)

    # 對齊
    aligned = pd.concat({"spread": spread, "ratio": ratio}, axis=1).dropna()
    spread = aligned["spread"]
    ratio = aligned["ratio"]

    # 平滑
    smoothing_window = 13
    spread_smoothed = spread.rolling(smoothing_window).mean().dropna()

    # 計算未來相對報酬
    periods_per_month = 4
    horizon_periods = int(lead_months * periods_per_month)
    future_rel_return = compute_future_rel_return(ratio, horizon_periods)

    # 領先掃描
    print("執行領先掃描...")
    scan_leads = [6, 12, 18, 24, 30, 36]
    lead_scan_results = lead_scan(spread_smoothed, ratio, scan_leads)

    # 穩定性檢查
    model_data = pd.concat({"x": spread_smoothed, "y": future_rel_return}, axis=1).dropna()
    stability = stability_check(model_data["x"], model_data["y"])

    # 計算相關係數
    valid = model_data["x"].notna() & model_data["y"].notna()
    full_corr = np.corrcoef(model_data["x"][valid], model_data["y"][valid])[0, 1]

    # 創建圖表 (2行1列布局)
    fig = plt.figure(figsize=(14, 10), facecolor=COLORS["background"])

    # Row 1: 利差與相對報酬對齊圖（含預測）
    ax_main = plt.subplot2grid((2, 1), (0, 0), fig=fig)
    ax_main.set_facecolor(COLORS["background"])

    # Row 2: QQQ 與 XLV 個別走勢（含預測）
    ax_price = plt.subplot2grid((2, 1), (1, 0), fig=fig)
    ax_price.set_facecolor(COLORS["background"])

    # === Row 1: 利差與相對報酬對齊圖 ===

    # 將利差往前平移 lead_months 個月（延伸到未來）
    periods_shift = int(lead_months * 4.345)

    # 創建延伸到未來的日期索引
    last_date = spread_smoothed.index[-1]
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(weeks=1),
        periods=periods_shift,
        freq='W-FRI'
    )

    # 將原始利差數據平移到未來
    spread_shifted = spread_smoothed.copy()
    spread_shifted.index = spread_shifted.index + pd.DateOffset(months=lead_months)

    # 分割：歷史部分（已有 ratio 對應）vs 預測部分（未來）
    ratio_last_date = ratio.index[-1]
    spread_historical = spread_shifted[spread_shifted.index <= ratio_last_date]
    spread_future = spread_shifted[spread_shifted.index > ratio_last_date]

    # 利差（左軸）- 歷史部分
    ax_main.fill_between(spread_historical.index, spread_historical.values, 0,
                         where=spread_historical.values > 0,
                         alpha=0.3, color=COLORS["inverted"], label='倒掛區域')
    ax_main.fill_between(spread_historical.index, spread_historical.values, 0,
                         where=spread_historical.values <= 0,
                         alpha=0.3, color=COLORS["normal"], label='正常曲線')
    ax_main.plot(spread_historical.index, spread_historical.values,
                 color=COLORS["secondary"], linewidth=2, alpha=0.9,
                 label=f'2Y-10Y 利差 (領先 {lead_months} 月)')

    # 利差（左軸）- 領先部分（尚未有對應的 QQQ/XLV 報酬）
    if len(spread_future) > 0:
        ax_main.fill_between(spread_future.index, spread_future.values, 0,
                             where=spread_future.values > 0,
                             alpha=0.25, color=COLORS["inverted"])
        ax_main.fill_between(spread_future.index, spread_future.values, 0,
                             where=spread_future.values <= 0,
                             alpha=0.25, color=COLORS["normal"])
        ax_main.plot(spread_future.index, spread_future.values,
                     color=COLORS["secondary"], linewidth=2, alpha=0.9,
                     label=f'領先 {lead_months} 月 (至 {spread_future.index[-1].strftime("%Y-%m")})')

        # 添加分界線
        ax_main.axvline(ratio_last_date, color=COLORS["text_dim"], linestyle=':',
                        linewidth=1.5, alpha=0.8)
        ax_main.text(ratio_last_date, ax_main.get_ylim()[1] * 0.9, '  ← 當前',
                     color=COLORS["text_dim"], fontsize=9,
                     ha='left', va='top')

    ax_main.axhline(0, color=COLORS["level_line"], linestyle='--', linewidth=1)
    ax_main.set_ylabel('美國公債利差 (%)', color=COLORS["secondary"], fontsize=10)
    ax_main.tick_params(axis='y', colors=COLORS["secondary"])
    ax_main.yaxis.set_major_formatter(FuncFormatter(format_percent))

    # 相對比率（右軸）- 只顯示到當前
    ax_ratio = ax_main.twinx()
    ax_ratio.plot(ratio.index, ratio.values,
                  color=COLORS["primary"], linewidth=2,
                  label=f'{risk_ticker}/{defensive_ticker} 比率')
    ax_ratio.set_ylabel(f'{risk_ticker}/{defensive_ticker}', color=COLORS["primary"], fontsize=10)
    ax_ratio.tick_params(axis='y', colors=COLORS["primary"])
    ax_ratio.yaxis.set_major_formatter(FuncFormatter(format_ratio))

    # 標註最新值
    latest_spread = spread_smoothed.iloc[-1]
    latest_ratio = ratio.iloc[-1]

    # 利差標註在預測區域末端
    if len(spread_future) > 0:
        future_end_date = spread_future.index[-1]
        future_end_value = spread_future.iloc[-1]
        ax_main.annotate(f'{future_end_value:.2f}%',
                         xy=(future_end_date, future_end_value),
                         xytext=(10, 0), textcoords='offset points',
                         color=COLORS["secondary"], fontsize=10, fontweight='bold', va='center',
                         bbox=dict(boxstyle='round,pad=0.2', facecolor=COLORS["background"],
                                   edgecolor=COLORS["secondary"], linewidth=1))

    # 比率標註在當前最新位置
    ax_ratio.annotate(f'{latest_ratio:.2f}',
                      xy=(ratio.index[-1], latest_ratio),
                      xytext=(10, 0), textcoords='offset points',
                      color=COLORS["primary"], fontsize=10, fontweight='bold', va='center')

    # === 預測 QQQ/XLV 走勢（複製利差的走勢形狀）===

    # 建立迴歸模型供摘要使用
    x_data = model_data["x"][valid].values
    y_data = model_data["y"][valid].values
    z = np.polyfit(x_data, y_data, 1)
    p = np.poly1d(z)

    # 用領先部分的利差走勢形狀，直接映射到 QQQ/XLV
    if len(spread_future) > 0:
        # 計算利差的變化率（相對於起點的百分比變化）
        spread_future_start = spread_future.iloc[0]
        spread_changes = (spread_future.values - spread_future_start) / abs(spread_future_start) if spread_future_start != 0 else spread_future.values * 0

        # 將利差變化率縮放後應用到 QQQ/XLV
        # 縮放因子：讓走勢形狀一致但幅度合理
        current_ratio_value = ratio.iloc[-1]

        # 直接複製利差的走勢形狀到 ratio
        # 利差變化 → ratio 變化（同方向，因為正相關）
        scale_factor = 0.05  # 控制變化幅度
        predicted_ratios = current_ratio_value * (1 + spread_changes * scale_factor)

        predicted_ratio_series = pd.Series(predicted_ratios, index=spread_future.index)

        # 繪製預測的 QQQ/XLV 比率（虛線）
        ax_ratio.plot(predicted_ratio_series.index, predicted_ratio_series.values,
                      color=COLORS["primary"], linewidth=2, linestyle='--', alpha=0.7,
                      label=f'{risk_ticker}/{defensive_ticker} 預測')

        # 標註預測終點
        pred_end_ratio = predicted_ratio_series.iloc[-1]
        ax_ratio.annotate(f'{pred_end_ratio:.2f}',
                          xy=(predicted_ratio_series.index[-1], pred_end_ratio),
                          xytext=(10, 0), textcoords='offset points',
                          color=COLORS["primary"], fontsize=10, fontweight='bold', va='center',
                          alpha=0.7)

    # 圖例
    lines1, labels1 = ax_main.get_legend_handles_labels()
    lines2, labels2 = ax_ratio.get_legend_handles_labels()
    ax_main.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8,
                   facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                   labelcolor=COLORS["text"])

    ax_main.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax_main.set_axisbelow(True)
    ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_main.xaxis.set_major_locator(mdates.YearLocator(1))
    ax_main.tick_params(axis='x', colors=COLORS["text_dim"])

    # 設定 X 軸顯示範圍（從 2017 年開始）
    display_start = pd.Timestamp('2017-01-01')
    if len(spread_future) > 0:
        display_end = spread_future.index[-1] + pd.DateOffset(months=3)
    else:
        display_end = ratio.index[-1] + pd.DateOffset(months=3)
    ax_main.set_xlim(display_start, display_end)

    # === Row 2: QQQ 與 XLV 個別走勢 ===

    # 重新抓取個別價格（週頻）
    risk_price_weekly = to_weekly(risk_price)
    defensive_price_weekly = to_weekly(defensive_price)

    # 對齊到共同索引
    common_price_idx = risk_price_weekly.index.intersection(defensive_price_weekly.index)
    risk_plot = risk_price_weekly.loc[common_price_idx]
    defensive_plot = defensive_price_weekly.loc[common_price_idx]

    # 計算 XLV 的 100 週均線
    defensive_ma100 = defensive_plot.rolling(100).mean()

    # XLV 預測：沿著 100 週均線最後的斜率延伸（直線）
    if len(spread_future) > 0 and len(defensive_ma100.dropna()) >= 2:
        # 計算均線最後一段的斜率（最後 2 點）
        ma_valid = defensive_ma100.dropna()
        last_ma_slope = ma_valid.iloc[-1] - ma_valid.iloc[-2]  # 每週變化量

        # 從當前 XLV 價格開始，沿均線斜率延伸
        last_xlv_price = defensive_plot.iloc[-1]
        predicted_xlv = []
        for i in range(len(spread_future)):
            next_xlv = last_xlv_price + last_ma_slope * (i + 1)
            predicted_xlv.append(next_xlv)
        predicted_xlv_series = pd.Series(predicted_xlv, index=spread_future.index)

        # 反推 QQQ = (QQQ/XLV 預測) × (XLV 預測)
        predicted_qqq = predicted_ratio_series * predicted_xlv_series
    else:
        predicted_xlv_series = None
        predicted_qqq = None

    # 繪製 QQQ（主軸）
    ax_price.plot(risk_plot.index, risk_plot.values,
                  color=COLORS["primary"], linewidth=2,
                  label=f'{risk_ticker}')

    # 繪製 XLV（次軸）
    ax_xlv = ax_price.twinx()
    ax_xlv.plot(defensive_plot.index, defensive_plot.values,
                color=COLORS["normal"], linewidth=2,
                label=f'{defensive_ticker}')
    ax_xlv.plot(defensive_ma100.index, defensive_ma100.values,
                color=COLORS["normal"], linewidth=1, linestyle='--', alpha=0.5,
                label=f'{defensive_ticker} 100週均線')

    # 繪製預測
    if predicted_xlv_series is not None and predicted_qqq is not None:
        # 預測 XLV（沿均線延伸）
        ax_xlv.plot(predicted_xlv_series.index, predicted_xlv_series.values,
                    color=COLORS["normal"], linewidth=2, linestyle='--', alpha=0.7,
                    label=f'{defensive_ticker} 預測')

        # 預測 QQQ（反推）
        ax_price.plot(predicted_qqq.index, predicted_qqq.values,
                      color=COLORS["primary"], linewidth=2, linestyle='--', alpha=0.7,
                      label=f'{risk_ticker} 預測')

        # 標註預測終點
        ax_price.annotate(f'${predicted_qqq.iloc[-1]:.0f}',
                          xy=(predicted_qqq.index[-1], predicted_qqq.iloc[-1]),
                          xytext=(10, 0), textcoords='offset points',
                          color=COLORS["primary"], fontsize=10, fontweight='bold', va='center',
                          alpha=0.7)
        ax_xlv.annotate(f'${predicted_xlv_series.iloc[-1]:.0f}',
                        xy=(predicted_xlv_series.index[-1], predicted_xlv_series.iloc[-1]),
                        xytext=(10, 0), textcoords='offset points',
                        color=COLORS["normal"], fontsize=10, fontweight='bold', va='center',
                        alpha=0.7)

        # 添加分界線
        ax_price.axvline(ratio.index[-1], color=COLORS["text_dim"], linestyle=':',
                         linewidth=1.5, alpha=0.8)

    # 標註當前價格
    ax_price.annotate(f'${risk_plot.iloc[-1]:.0f}',
                      xy=(risk_plot.index[-1], risk_plot.iloc[-1]),
                      xytext=(10, 0), textcoords='offset points',
                      color=COLORS["primary"], fontsize=10, fontweight='bold', va='center')
    ax_xlv.annotate(f'${defensive_plot.iloc[-1]:.0f}',
                    xy=(defensive_plot.index[-1], defensive_plot.iloc[-1]),
                    xytext=(10, -15), textcoords='offset points',
                    color=COLORS["normal"], fontsize=10, fontweight='bold', va='center')

    ax_price.set_ylabel(f'{risk_ticker} 價格', color=COLORS["primary"], fontsize=10)
    ax_price.tick_params(axis='y', colors=COLORS["primary"])
    ax_xlv.set_ylabel(f'{defensive_ticker} 價格', color=COLORS["normal"], fontsize=10)
    ax_xlv.tick_params(axis='y', colors=COLORS["normal"])

    # 圖例
    lines_p1, labels_p1 = ax_price.get_legend_handles_labels()
    lines_p2, labels_p2 = ax_xlv.get_legend_handles_labels()
    ax_price.legend(lines_p1 + lines_p2, labels_p1 + labels_p2, loc='upper left', fontsize=8,
                    facecolor=COLORS["background"], edgecolor=COLORS["grid"],
                    labelcolor=COLORS["text"])

    ax_price.grid(True, color=COLORS["grid"], alpha=0.3, linestyle='-', linewidth=0.5)
    ax_price.set_axisbelow(True)
    ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_price.xaxis.set_major_locator(mdates.YearLocator(1))
    ax_price.tick_params(axis='x', colors=COLORS["text_dim"])

    # 設定 X 軸顯示範圍（與上圖一致）
    ax_price.set_xlim(display_start, display_end)

    # 計算迴歸模型參數供摘要使用
    current_x = spread_smoothed.iloc[-1]
    predicted_y = p(current_x)

    # === 標題 ===
    if title is None:
        title = f'美國公債利差 (2Y-10Y) 領先 {risk_ticker}/{defensive_ticker} 相對報酬表現'

    fig.suptitle(title, color=COLORS["text"], fontsize=14, fontweight='bold', y=0.995)

    # === 統計摘要 ===
    predicted_return_pct = (np.exp(predicted_y) - 1) * 100
    summary_text = (
        f'當前利差: {current_x:.2f}%  |  '
        f'預測 {lead_months}m 相對報酬: {predicted_return_pct:+.1f}%  |  '
        f'相關係數: {full_corr:.3f}  |  '
        f'R²: {full_corr**2:.2%}'
    )

    fig.text(0.5, 0.955, summary_text,
             color=COLORS["text_dim"], fontsize=9, ha='center',
             bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS["background"],
                       edgecolor=COLORS["grid"], linewidth=1))

    # === 頁尾 ===
    fig.text(0.02, 0.005,
             f'資料來源: FRED (DGS2, DGS10), Yahoo Finance ({risk_ticker}, {defensive_ticker})',
             color=COLORS["text_dim"], fontsize=8, ha='left')

    fig.text(0.98, 0.005,
             f'截至: {datetime.now().strftime("%Y-%m-%d")}',
             color=COLORS["text_dim"], fontsize=8, ha='right')

    # === 佈局調整 ===
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, bottom=0.05, hspace=0.25)

    # === 輸出 ===
    if output_path is None:
        output_path = f"output/yield_spread_forecast_{datetime.now().strftime('%Y-%m-%d')}.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=COLORS["background"])
    plt.close()

    print(f"✓ Bloomberg 風格圖表已儲存: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="生成 Bloomberg 風格的美國公債利差領先分析圖表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 快速生成默認圖表
  python plot_bloomberg_style.py --quick

  # 自訂參數
  python plot_bloomberg_style.py --lead-months 24 --lookback-years 18 --output output/chart.png

  # 從 JSON 結果生成
  python plot_bloomberg_style.py --input result.json --output output/chart.png
        """
    )

    parser.add_argument('--quick', action='store_true',
                        help='使用默認參數快速生成')
    parser.add_argument('--input', type=str,
                        help='spread_forecaster.py 的 JSON 輸出文件（可選）')
    parser.add_argument('--output', type=str,
                        help='輸出圖表路徑')
    parser.add_argument('--risk-ticker', type=str, default='QQQ',
                        help='成長股標的')
    parser.add_argument('--defensive-ticker', type=str, default='XLV',
                        help='防禦股標的')
    parser.add_argument('--lead-months', type=int, default=24,
                        help='領先期（月）')
    parser.add_argument('--lookback-years', type=int, default=18,
                        help='回測年數')
    parser.add_argument('--title', type=str,
                        help='圖表標題（可選）')

    args = parser.parse_args()

    # 設定輸出路徑
    if args.output:
        output_path = args.output
    else:
        output_path = f"output/yield_spread_forecast_{datetime.now().strftime('%Y-%m-%d')}.png"

    # 讀取 JSON 結果（如果提供）
    result_json = None
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            result_json = json.load(f)

    # 生成圖表
    plot_yield_spread_forecast(
        result_json=result_json,
        output_path=output_path,
        title=args.title,
        lookback_years=args.lookback_years,
        lead_months=args.lead_months,
        risk_ticker=args.risk_ticker,
        defensive_ticker=args.defensive_ticker
    )


if __name__ == "__main__":
    main()
