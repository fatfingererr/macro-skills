#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
計算美股當前估值歷史分位數

把多個股票估值指標統一轉成在過去百年歷史中的分位數，
再合成一個總分，判斷目前是否處於歷史極端高估區間，
並用歷史類比（如 1929、1965、1999）給出風險解讀。
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# 嘗試導入可選依賴
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# =============================================================================
# 常數與預設參數
# =============================================================================

DEFAULT_METRICS = ["cape", "mktcap_to_gdp", "trailing_pe"]
DEFAULT_AGGREGATION = "mean"
DEFAULT_THRESHOLD = 95
DEFAULT_EPISODE_GAP_DAYS = 3650  # 約 10 年
DEFAULT_FORWARD_WINDOWS = [180, 365, 1095]

# 歷史極端事件（硬編碼，作為參考）
KNOWN_HISTORICAL_EPISODES = {
    "1929-09-01": {"context": "大蕭條前夕", "cape": 33.0},
    "1965-01-01": {"context": "Nifty Fifty 時期", "cape": 24.0},
    "1999-12-01": {"context": "科技泡沫頂點", "cape": 44.0, "mktcap_to_gdp": 150.0},
    "2021-12-01": {"context": "疫情後牛市頂點", "cape": 40.0, "mktcap_to_gdp": 200.0},
}


# =============================================================================
# 資料抓取函數
# =============================================================================

def fetch_fred_series(series_id: str, start: str = "1900-01-01") -> Optional[pd.Series]:
    """
    從 FRED 抓取時間序列（使用 CSV endpoint，無需 API key）

    Parameters
    ----------
    series_id : str
        FRED 系列代碼
    start : str
        起始日期

    Returns
    -------
    pd.Series or None
    """
    if not HAS_REQUESTS:
        print(f"警告: requests 套件未安裝，無法抓取 FRED 資料")
        return None

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

    try:
        df = pd.read_csv(url, parse_dates=['DATE'], index_col='DATE')
        df = df.rename(columns={series_id: 'value'})
        df = df[df.index >= start]
        df = df.dropna()
        return df['value']
    except Exception as e:
        print(f"FRED 資料抓取失敗 ({series_id}): {e}")
        return None


def fetch_shiller_cape() -> Optional[pd.Series]:
    """
    從 Shiller 資料集抓取 CAPE

    Returns
    -------
    pd.Series or None
    """
    if not HAS_REQUESTS:
        print("警告: requests 套件未安裝，無法抓取 Shiller 資料")
        return None

    try:
        # Shiller 資料的 CSV 版本（更容易解析）
        url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

        df = pd.read_excel(url, sheet_name="Data", skiprows=7)

        # 嘗試找到 CAPE 欄位（欄位名稱可能變化）
        cape_col = None
        for col in df.columns:
            if 'CAPE' in str(col).upper():
                cape_col = col
                break

        if cape_col is None:
            # 嘗試使用位置（CAPE 通常在第 12-13 欄）
            cape_col = df.columns[12] if len(df.columns) > 12 else None

        if cape_col is None:
            print("警告: 無法在 Shiller 資料中找到 CAPE 欄位")
            return None

        # 處理日期欄位
        date_col = df.columns[0]
        df['Date'] = pd.to_datetime(
            df[date_col].astype(str).str[:7].str.replace('.', '-'),
            format='%Y-%m',
            errors='coerce'
        )

        df = df.dropna(subset=['Date', cape_col])
        df = df.set_index('Date')

        series = df[cape_col].astype(float)
        series.name = 'CAPE'

        return series

    except Exception as e:
        print(f"Shiller CAPE 資料抓取失敗: {e}")
        return None


def fetch_mktcap_to_gdp() -> Optional[pd.Series]:
    """
    計算市值/GDP（巴菲特指標）

    Returns
    -------
    pd.Series or None
    """
    # 抓取 Wilshire 5000 市值
    mktcap = fetch_fred_series('WILL5000PRFC')
    if mktcap is None:
        return None

    # 抓取 GDP
    gdp = fetch_fred_series('GDP')
    if gdp is None:
        return None

    # GDP 是季度資料，需要 forward fill 到月度
    gdp_monthly = gdp.resample('M').ffill()
    mktcap_monthly = mktcap.resample('M').last()

    # 對齊並計算
    df = pd.DataFrame({
        'mktcap': mktcap_monthly,
        'gdp': gdp_monthly
    }).dropna()

    df['mktcap_to_gdp'] = (df['mktcap'] / df['gdp']) * 100  # 百分比

    result = df['mktcap_to_gdp']
    result.name = 'mktcap_to_gdp'

    return result


def fetch_yahoo_pe(ticker: str = "^GSPC") -> Optional[float]:
    """
    從 Yahoo Finance 抓取當前 PE

    Parameters
    ----------
    ticker : str
        股票代碼

    Returns
    -------
    float or None
    """
    if not HAS_YFINANCE:
        print("警告: yfinance 套件未安裝")
        return None

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('trailingPE')
    except Exception as e:
        print(f"Yahoo Finance PE 抓取失敗: {e}")
        return None


def fetch_price_history(ticker: str = "^GSPC", start: str = "1950-01-01") -> Optional[pd.Series]:
    """
    抓取價格歷史

    Parameters
    ----------
    ticker : str
        股票代碼
    start : str
        起始日期

    Returns
    -------
    pd.Series or None
    """
    if not HAS_YFINANCE:
        return None

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, auto_adjust=True)
        if df.empty:
            return None
        return df['Close']
    except Exception as e:
        print(f"價格歷史抓取失敗: {e}")
        return None


# =============================================================================
# 分位數計算函數
# =============================================================================

def percentile_rank(series: pd.Series, value: float) -> float:
    """
    計算 value 在 series 中的分位數排名

    Parameters
    ----------
    series : pd.Series
        歷史樣本
    value : float
        當期值

    Returns
    -------
    float
        0-100 的分位數
    """
    s = series.dropna().values
    if len(s) == 0:
        return np.nan
    return 100.0 * (s <= value).sum() / len(s)


def compute_metric_percentiles(
    metric_df: pd.DataFrame,
    as_of_date: str
) -> Dict[str, Dict[str, Any]]:
    """
    計算各指標在 as_of_date 的分位數

    Parameters
    ----------
    metric_df : pd.DataFrame
        index=日期, columns=各估值指標
    as_of_date : str
        評估日期

    Returns
    -------
    dict
        {指標名稱: {current_value, percentile, ...}}
    """
    as_of = pd.to_datetime(as_of_date)
    asof_data = metric_df.loc[:as_of]

    if asof_data.empty:
        return {}

    # 取最新一筆
    latest_idx = asof_data.index[-1]
    latest = asof_data.loc[latest_idx]

    results = {}
    for m in metric_df.columns:
        hist = asof_data[m].dropna()
        if len(hist) < 60:  # 至少需要 60 個資料點
            continue

        current_value = latest[m] if m in latest and not pd.isna(latest[m]) else np.nan
        if pd.isna(current_value):
            continue

        pct = percentile_rank(hist, current_value)

        results[m] = {
            'current_value': float(current_value),
            'percentile': float(pct),
            'history_start': str(hist.index[0].date()),
            'data_points': len(hist),
            'historical_median': float(hist.median()),
            'historical_mean': float(hist.mean())
        }

    return results


def aggregate_percentiles(
    pct_dict: Dict[str, Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    method: str = "mean"
) -> float:
    """
    合成多個指標的分位數

    Parameters
    ----------
    pct_dict : dict
        {指標名稱: {percentile: value, ...}}
    weights : dict, optional
        指標權重
    method : str
        合成方法

    Returns
    -------
    float
        合成分位數
    """
    if not pct_dict:
        return np.nan

    items = [(k, v['percentile']) for k, v in pct_dict.items()]
    vals = np.array([v for _, v in items], dtype=float)

    if weights:
        w = np.array([weights.get(k, 0.0) for k, _ in items], dtype=float)
        if w.sum() > 0:
            w = w / w.sum()
            return float(np.sum(vals * w))

    if method == "median":
        return float(np.median(vals))
    elif method == "trimmed_mean" and len(vals) > 2:
        return float(np.mean(np.sort(vals)[1:-1]))

    return float(np.mean(vals))


# =============================================================================
# 歷史事件識別
# =============================================================================

def find_extreme_episodes(
    composite_series: pd.Series,
    threshold: float = 95,
    min_gap_days: int = 3650
) -> List[Tuple[str, float]]:
    """
    找出歷史上的極端高估事件

    Parameters
    ----------
    composite_series : pd.Series
        合成分位數的時間序列
    threshold : float
        極端門檻
    min_gap_days : int
        事件去重的最小間隔（天）

    Returns
    -------
    list
        [(日期, 分位數), ...]
    """
    peaks = []
    last_peak_date = None

    for date, val in composite_series.items():
        if pd.isna(val) or val < threshold:
            continue

        if last_peak_date is None or (date - last_peak_date).days >= min_gap_days:
            peaks.append((str(date.date()), float(val)))
            last_peak_date = date
        else:
            # 同一段期間內，保留更高者
            if val > composite_series[last_peak_date]:
                peaks[-1] = (str(date.date()), float(val))
                last_peak_date = date

    return peaks


# =============================================================================
# 事後統計
# =============================================================================

def calculate_forward_stats(
    price_series: pd.Series,
    event_dates: List[str],
    windows: List[int]
) -> Dict[str, Dict[str, Any]]:
    """
    計算事後統計

    Parameters
    ----------
    price_series : pd.Series
        價格序列
    event_dates : list
        事件日期清單
    windows : list
        視窗（天）

    Returns
    -------
    dict
        {window: {forward_return: {...}, max_drawdown: {...}}}
    """
    results = {}

    for window in windows:
        returns = []
        drawdowns = []

        for event_date_str in event_dates:
            event_date = pd.to_datetime(event_date_str)

            # 找最近的交易日
            if event_date not in price_series.index:
                mask = price_series.index >= event_date
                if not mask.any():
                    continue
                event_date = price_series.index[mask][0]

            future_date = event_date + timedelta(days=window)

            # 找最近的交易日
            if future_date not in price_series.index:
                mask = price_series.index >= future_date
                if not mask.any():
                    continue
                future_date = price_series.index[mask][0]

            if future_date in price_series.index:
                ret = (price_series[future_date] / price_series[event_date]) - 1
                returns.append(ret * 100)  # 百分比

            # 最大回撤
            period_prices = price_series[event_date:future_date]
            if len(period_prices) > 1:
                rolling_max = period_prices.cummax()
                dd = (period_prices - rolling_max) / rolling_max
                drawdowns.append(dd.min() * 100)  # 百分比

        results[f'{window}d'] = {
            'forward_return': {
                'median': float(np.median(returns)) if returns else None,
                'p25': float(np.percentile(returns, 25)) if returns else None,
                'p10': float(np.percentile(returns, 10)) if returns else None,
                'positive_prob': float((np.array(returns) > 0).mean()) if returns else None,
                'sample_size': len(returns)
            },
            'max_drawdown': {
                'median': float(np.median(drawdowns)) if drawdowns else None,
                'p75': float(np.percentile(drawdowns, 75)) if drawdowns else None,
                'worst': float(np.min(drawdowns)) if drawdowns else None
            }
        }

    return results


# =============================================================================
# 主分析函數
# =============================================================================

def run_analysis(
    as_of_date: str,
    universe: str = "^GSPC",
    metrics: List[str] = None,
    aggregation: str = "mean",
    weights: Dict[str, float] = None,
    extreme_threshold: float = 95,
    episode_min_gap_days: int = 3650,
    forward_windows_days: List[int] = None,
    quick: bool = False
) -> Dict[str, Any]:
    """
    執行估值分位數分析

    Parameters
    ----------
    as_of_date : str
        評估日期
    universe : str
        市場代碼
    metrics : list
        估值指標清單
    aggregation : str
        合成方法
    weights : dict
        指標權重
    extreme_threshold : float
        極端門檻
    episode_min_gap_days : int
        事件去重間隔
    forward_windows_days : list
        事後統計視窗
    quick : bool
        快速模式

    Returns
    -------
    dict
        分析結果
    """
    if metrics is None:
        metrics = DEFAULT_METRICS
    if forward_windows_days is None:
        forward_windows_days = DEFAULT_FORWARD_WINDOWS

    print(f"開始估值分位數分析...")
    print(f"評估日期: {as_of_date}")
    print(f"市場: {universe}")
    print(f"指標: {metrics}")

    # 收集資料
    metric_data = {}

    if "cape" in metrics:
        print("抓取 CAPE 資料...")
        cape = fetch_shiller_cape()
        if cape is not None:
            metric_data['cape'] = cape

    if "mktcap_to_gdp" in metrics:
        print("計算 市值/GDP...")
        mktcap_gdp = fetch_mktcap_to_gdp()
        if mktcap_gdp is not None:
            metric_data['mktcap_to_gdp'] = mktcap_gdp

    # 注意：trailing_pe 等指標需要歷史資料，這裡使用 CAPE 作為近似
    # 在實際應用中，應從其他來源獲取
    if "trailing_pe" in metrics and "cape" in metric_data:
        print("注意: trailing_pe 使用 CAPE 近似（實際應用需其他資料源）")
        # 使用 CAPE 的一半作為 trailing PE 的近似（僅供演示）
        metric_data['trailing_pe'] = metric_data['cape'] * 0.7

    if not metric_data:
        return {"error": "無法獲取任何估值指標資料"}

    # 合併資料
    metric_df = pd.DataFrame(metric_data)
    metric_df = metric_df.dropna(how='all')

    if metric_df.empty:
        return {"error": "資料合併後為空"}

    # 計算分位數
    print("計算分位數...")
    metric_percentiles = compute_metric_percentiles(metric_df, as_of_date)

    if not metric_percentiles:
        return {"error": "無法計算分位數"}

    # 合成總分
    composite_percentile = aggregate_percentiles(metric_percentiles, weights, aggregation)

    # 判定極端
    is_extreme = composite_percentile >= extreme_threshold

    # 決定狀態
    if composite_percentile >= 95:
        status = "EXTREME_OVERVALUED"
        status_desc = "歷史極端高估"
    elif composite_percentile >= 80:
        status = "OVERVALUED"
        status_desc = "高估"
    elif composite_percentile >= 65:
        status = "ELEVATED"
        status_desc = "偏高"
    elif composite_percentile >= 35:
        status = "NORMAL"
        status_desc = "正常範圍"
    elif composite_percentile >= 20:
        status = "CHEAP"
        status_desc = "偏低"
    elif composite_percentile >= 5:
        status = "UNDERVALUED"
        status_desc = "低估"
    else:
        status = "EXTREME_UNDERVALUED"
        status_desc = "歷史極端低估"

    # 基本結果
    result = {
        "skill": "detect-us-equity-valuation-percentile-extreme",
        "version": "0.1.0",
        "as_of_date": as_of_date,
        "universe": universe,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "composite_percentile": round(composite_percentile, 1),
            "extreme_threshold": extreme_threshold,
            "is_extreme": is_extreme,
            "status": status,
            "status_description": status_desc
        },
        "metric_percentiles": {
            k: {
                "current_value": round(v["current_value"], 2),
                "percentile": round(v["percentile"], 1),
                "history_start": v["history_start"],
                "data_points": v["data_points"],
                "historical_median": round(v["historical_median"], 2),
                "historical_mean": round(v["historical_mean"], 2)
            }
            for k, v in metric_percentiles.items()
        }
    }

    if quick:
        return result

    # 完整分析：歷史事件
    print("識別歷史極端事件...")

    # 建立歷史合成分位數序列（簡化版：使用 CAPE 分位數）
    if 'cape' in metric_df.columns:
        cape_series = metric_df['cape'].dropna()
        rolling_pct = pd.Series(index=cape_series.index, dtype=float)

        for i, (date, val) in enumerate(cape_series.items()):
            if i < 60:
                continue
            hist = cape_series.iloc[:i+1]
            rolling_pct[date] = percentile_rank(hist, val)

        historical_episodes = find_extreme_episodes(
            rolling_pct,
            threshold=extreme_threshold,
            min_gap_days=episode_min_gap_days
        )
    else:
        historical_episodes = []

    # 加入已知歷史事件的背景資訊
    episodes_with_context = []
    for date_str, pct in historical_episodes:
        episode = {
            "date": date_str,
            "composite_percentile": round(pct, 1)
        }
        if date_str in KNOWN_HISTORICAL_EPISODES:
            episode["context"] = KNOWN_HISTORICAL_EPISODES[date_str]["context"]
        episodes_with_context.append(episode)

    result["historical_episodes"] = episodes_with_context

    # 事後統計
    if historical_episodes:
        print("計算事後統計...")
        price_series = fetch_price_history(universe)

        if price_series is not None:
            event_dates = [ep[0] for ep in historical_episodes]
            forward_stats = calculate_forward_stats(
                price_series,
                event_dates,
                forward_windows_days
            )
            result["forward_stats"] = forward_stats

    # 風險解讀
    result["risk_interpretation"] = {
        "headline": f"當前估值處於{status_desc}區間" + ("，風險分布不對稱" if is_extreme else ""),
        "key_points": [
            f"綜合估值分位數 {composite_percentile:.1f}，歷史上僅 {100-composite_percentile:.1f}% 的時間比現在更貴",
        ],
        "caveats": [
            "歷史極端事件樣本數有限",
            "當前環境可能與歷史不同",
            "估值可以維持極端更久"
        ],
        "suggested_actions": [
            "降低整體槓桿" if is_extreme else "維持正常配置",
            "增加防禦性資產" if is_extreme else "保持分散投資",
            "不建議據此完全離場或做空"
        ]
    }

    # 資料品質說明
    result["data_quality_notes"] = []
    for m, info in metric_percentiles.items():
        result["data_quality_notes"].append(
            f"{m} 資料可回溯至 {info['history_start']}，共 {info['data_points']} 個資料點"
        )

    return result


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="計算美股當前估值歷史分位數"
    )
    parser.add_argument(
        "-d", "--as_of_date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="評估日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "-u", "--universe",
        default="^GSPC",
        help="市場代碼"
    )
    parser.add_argument(
        "-m", "--metrics",
        default=",".join(DEFAULT_METRICS),
        help="估值指標（逗號分隔）"
    )
    parser.add_argument(
        "-a", "--aggregation",
        default=DEFAULT_AGGREGATION,
        choices=["mean", "median", "trimmed_mean"],
        help="合成方法"
    )
    parser.add_argument(
        "-t", "--extreme_threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="極端門檻"
    )
    parser.add_argument(
        "-o", "--output",
        help="輸出檔案路徑"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速模式（只輸出基本結果）"
    )

    args = parser.parse_args()

    # 執行分析
    result = run_analysis(
        as_of_date=args.as_of_date,
        universe=args.universe,
        metrics=args.metrics.split(","),
        aggregation=args.aggregation,
        extreme_threshold=args.extreme_threshold,
        quick=args.quick
    )

    # 輸出
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding='utf-8')
        print(f"\n結果已保存至: {args.output}")
    else:
        print("\n" + "="*60)
        print(output_json)


if __name__ == "__main__":
    main()
