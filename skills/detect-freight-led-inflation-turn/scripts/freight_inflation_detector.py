#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
美國貨運概況判斷通膨趨勢器

透過 CASS Freight Index 的週期轉折，偵測通膨壓力是否進入放緩或反轉階段。
數據來源：MacroMicro (CASS Freight Index)

Usage:
    python freight_inflation_detector.py --quick
    python freight_inflation_detector.py --start 2015-01-01 --lead-months 6
    python freight_inflation_detector.py --indicator shipments_yoy
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd
import requests

# ========== 配置區域 ==========
# CASS Freight Index 指標
CASS_INDICATORS = {
    "shipments_index": "CASS Shipments Index",
    "expenditures_index": "CASS Expenditures Index",
    "shipments_yoy": "CASS Shipments YoY",
    "expenditures_yoy": "CASS Expenditures YoY"
}

# 主要分析指標（推薦使用 Shipments YoY）
DEFAULT_INDICATOR = "shipments_yoy"

# FRED CPI 系列
CPI_SERIES = "CPIAUCSL"
FRED_CSV_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# 分析參數
DEFAULT_LEAD_MONTHS = 6
DEFAULT_CYCLE_WINDOW = 18
DEFAULT_YOY_THRESHOLD = 0.0

# 快取設定
CACHE_MAX_AGE_HOURS = 12
# ==============================


def fetch_fred_cpi(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    從 FRED 抓取 CPI 數據

    Returns
    -------
    pd.DataFrame
        CPI 數據，index 為日期
    """
    params = {"id": CPI_SERIES}
    if start_date:
        params["cosd"] = start_date
    if end_date:
        params["coed"] = end_date

    url = f"{FRED_CSV_ENDPOINT}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    print(f"[Fetching] CPI from FRED...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df = df.set_index("date").sort_index()

        print(f"[Success] CPI: {len(df)} records")
        return df

    except Exception as e:
        print(f"[Error] Failed to fetch CPI: {e}")
        raise


def calculate_yoy(series: pd.Series) -> pd.Series:
    """
    計算年增率 (YoY)

    Parameters
    ----------
    series : pd.Series
        月度指數序列

    Returns
    -------
    pd.Series
        年增率（百分比形式）
    """
    return (series / series.shift(12) - 1) * 100


def detect_cycle_low(
    yoy: pd.Series,
    window: int = 18,
    min_periods: int = 12
) -> pd.Series:
    """
    偵測是否為 N 個月新低

    Parameters
    ----------
    yoy : pd.Series
        年增率序列
    window : int
        回看窗口（月）
    min_periods : int
        最小觀察期

    Returns
    -------
    pd.Series
        布林值序列
    """
    rolling_min = yoy.rolling(window=window, min_periods=min_periods).min()
    return yoy == rolling_min


def get_cycle_status(
    latest_yoy: float,
    is_new_low: bool,
    yoy_threshold: float = 0.0
) -> str:
    """
    判斷週期狀態

    Returns
    -------
    str
        'new_cycle_low' | 'negative' | 'positive'
    """
    if is_new_low and latest_yoy < yoy_threshold:
        return "new_cycle_low"
    elif latest_yoy < yoy_threshold:
        return "negative"
    else:
        return "positive"


def count_consecutive_negative(yoy: pd.Series) -> int:
    """計算最近連續負值月數"""
    count = 0
    for value in yoy.iloc[::-1]:
        if pd.notna(value) and value < 0:
            count += 1
        else:
            break
    return count


def lead_alignment_analysis(
    freight_yoy: pd.Series,
    cpi_yoy: pd.Series,
    lead_months: int = 6
) -> Dict[str, Any]:
    """
    領先對齊分析

    Parameters
    ----------
    freight_yoy : pd.Series
        貨運量年增率
    cpi_yoy : pd.Series
        CPI 年增率
    lead_months : int
        假設的領先月數

    Returns
    -------
    dict
        包含領先相關性和對齊驗證
    """
    # 將貨運 YoY 向前平移
    freight_lead = freight_yoy.shift(lead_months)

    # 對齊並計算相關性
    aligned = pd.DataFrame({
        "freight_lead": freight_lead,
        "cpi": cpi_yoy
    }).dropna()

    if len(aligned) < 24:
        return {
            "correlation": None,
            "lead_months": lead_months,
            "optimal_lead": lead_months,
            "alignment_quality": "insufficient_data"
        }

    correlation = aligned["freight_lead"].corr(aligned["cpi"])

    # 找最佳領先月數
    correlations = {}
    for lead in range(1, 13):
        shifted = freight_yoy.shift(lead)
        df_temp = pd.DataFrame({"freight": shifted, "cpi": cpi_yoy}).dropna()
        if len(df_temp) >= 24:
            corr = df_temp["freight"].corr(df_temp["cpi"])
            if pd.notna(corr):
                correlations[lead] = corr

    optimal_lead = max(correlations, key=correlations.get) if correlations else lead_months

    # 對齊品質評估
    if pd.isna(correlation):
        quality = "insufficient_data"
    elif correlation > 0.6:
        quality = "high"
    elif correlation > 0.4:
        quality = "medium"
    else:
        quality = "low"

    return {
        "correlation": round(correlation, 3) if pd.notna(correlation) else None,
        "lead_months": lead_months,
        "optimal_lead": optimal_lead,
        "alignment_quality": quality
    }


def assess_signal(
    freight_yoy: float,
    cycle_status: str,
    alignment_quality: str,
    consecutive_months: int,
    yoy_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    訊號評估

    Returns
    -------
    dict
        包含 signal, confidence, macro_implication
    """
    # 基礎訊號判斷
    if cycle_status == "new_cycle_low" and freight_yoy < yoy_threshold:
        signal = "inflation_easing"
        confidence = "high"
        implication = "通膨壓力正在放緩，未來 CPI 下行風險上升"
    elif freight_yoy < yoy_threshold:
        signal = "inflation_easing"
        confidence = "medium"
        implication = "貨運量轉負，通膨可能開始降溫"
    elif cycle_status == "positive" and freight_yoy > 5:
        signal = "inflation_rising"
        confidence = "medium"
        implication = "貨運量強勁，通膨上行壓力可能延續"
    else:
        signal = "neutral"
        confidence = "low"
        implication = "貨運量處於中性區間，通膨方向待觀察"

    # 根據對齊品質調整信心
    if alignment_quality in ["low", "insufficient_data"]:
        confidence = "low"

    # 根據連續負值月數加強信心
    if signal == "inflation_easing" and consecutive_months >= 3:
        if confidence == "medium":
            confidence = "high"

    return {
        "signal": signal,
        "confidence": confidence,
        "macro_implication": implication
    }


def historical_positioning(
    current_yoy: float,
    historical_yoy: pd.Series
) -> Dict[str, Any]:
    """
    計算當前數據在歷史分布中的位置

    Returns
    -------
    dict
        百分位數和歷史對照
    """
    valid_history = historical_yoy.dropna()
    if len(valid_history) == 0:
        return {
            "current_percentile": None,
            "similar_periods": [],
            "context": "資料不足"
        }

    percentile = (valid_history < current_yoy).mean() * 100

    # 歷史對照說明
    if percentile < 10:
        context = "極低，歷史上僅出現在衰退或危機期間（2008、2020）"
    elif percentile < 25:
        context = "偏低，通常對應經濟放緩期"
    elif percentile < 75:
        context = "中性區間，需觀察趨勢方向"
    elif percentile < 90:
        context = "偏高，經濟活動活躍"
    else:
        context = "極高，歷史上對應擴張期或復甦期"

    # 找類似歷史時期
    similar = historical_yoy[
        (historical_yoy > current_yoy - 2) &
        (historical_yoy < current_yoy + 2)
    ]
    similar_periods = similar.index.strftime("%Y-%m").tolist()[-5:]

    return {
        "current_percentile": round(percentile, 1),
        "similar_periods": similar_periods,
        "context": context
    }


def get_cpi_trend(cpi_yoy: pd.Series) -> str:
    """判斷 CPI 趨勢"""
    if len(cpi_yoy) < 3:
        return "unknown"

    recent = cpi_yoy.iloc[-3:]
    if len(cpi_yoy) >= 6:
        avg_recent = recent.mean()
        avg_prev = cpi_yoy.iloc[-6:-3].mean()
        diff = avg_recent - avg_prev
    else:
        diff = 0

    if diff > 0.2:
        return "rising"
    elif diff < -0.2:
        return "falling"
    else:
        return "stable"


def run_analysis(
    start_date: str = "2010-01-01",
    end_date: Optional[str] = None,
    indicator: str = DEFAULT_INDICATOR,
    lead_months: int = DEFAULT_LEAD_MONTHS,
    yoy_threshold: float = DEFAULT_YOY_THRESHOLD,
    cycle_window: int = DEFAULT_CYCLE_WINDOW,
    cache_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    執行完整分析

    Parameters
    ----------
    start_date : str
        分析起始日期
    end_date : str, optional
        分析結束日期
    indicator : str
        CASS 指標 (shipments_index, expenditures_index, shipments_yoy, expenditures_yoy)
    lead_months : int
        領先月數
    yoy_threshold : float
        YoY 警戒門檻
    cycle_window : int
        週期窗口
    cache_dir : str, optional
        快取目錄

    Returns
    -------
    dict
        完整分析結果
    """
    # 導入 CASS 爬蟲
    from fetch_cass_freight import fetch_cass_freight_index

    # 抓取 CASS 數據
    print(f"抓取 CASS Freight Index ({indicator})...")
    cass_data = fetch_cass_freight_index(
        cache_dir=cache_dir or "cache",
        force_refresh=False
    )

    if indicator not in cass_data:
        raise ValueError(f"未找到指標 {indicator}，可用指標: {list(cass_data.keys())}")

    cass_df = cass_data[indicator]
    cass_series = cass_df.iloc[:, 0]

    # 抓取 CPI 數據
    cpi_df = fetch_fred_cpi(start_date=start_date, end_date=end_date)
    cpi_series = cpi_df["value"]

    # 計算 YoY
    # 如果是 index，需要計算 YoY；如果已經是 YoY，直接使用
    if "yoy" in indicator.lower():
        freight_yoy = cass_series.dropna()
    else:
        freight_yoy = calculate_yoy(cass_series).dropna()

    cpi_yoy = calculate_yoy(cpi_series).dropna()

    # 對齊日期範圍
    common_start = max(freight_yoy.index.min(), cpi_yoy.index.min())
    common_end = min(freight_yoy.index.max(), cpi_yoy.index.max())

    if pd.Timestamp(start_date) > common_start:
        common_start = pd.Timestamp(start_date)

    freight_yoy = freight_yoy[common_start:common_end]
    cpi_yoy = cpi_yoy[common_start:common_end]

    if len(freight_yoy) == 0:
        raise ValueError("Insufficient freight data for analysis")

    # 偵測週期低點
    is_cycle_low = detect_cycle_low(freight_yoy, window=cycle_window)

    # 取最新數據
    latest_date = freight_yoy.index[-1]
    latest_freight_yoy = freight_yoy.iloc[-1]
    latest_is_low = is_cycle_low.iloc[-1] if len(is_cycle_low) > 0 else False

    # 判斷週期狀態
    cycle_status = get_cycle_status(latest_freight_yoy, latest_is_low, yoy_threshold)

    # 計算連續負值月數
    consecutive_months = count_consecutive_negative(freight_yoy)

    # 領先對齊分析
    alignment = lead_alignment_analysis(freight_yoy, cpi_yoy, lead_months)

    # 訊號評估
    signal_result = assess_signal(
        latest_freight_yoy,
        cycle_status,
        alignment["alignment_quality"],
        consecutive_months,
        yoy_threshold
    )

    # 歷史定位
    history_pos = historical_positioning(latest_freight_yoy, freight_yoy)

    # CPI 狀態
    latest_cpi_yoy = cpi_yoy.iloc[-1] if len(cpi_yoy) > 0 else None
    cpi_3m_avg = cpi_yoy.iloc[-3:].mean() if len(cpi_yoy) >= 3 else latest_cpi_yoy
    cpi_trend = get_cpi_trend(cpi_yoy)

    # 組裝結果
    result = {
        "metadata": {
            "analysis_time": datetime.now().isoformat(),
            "start_date": start_date,
            "end_date": end_date or "latest",
            "indicator": indicator,
            "indicator_name": CASS_INDICATORS.get(indicator, indicator),
            "lead_months": lead_months,
            "as_of_date": latest_date.strftime("%Y-%m-%d"),
            "data_source": "MacroMicro (CASS Freight Index)"
        },
        "freight_status": {
            "indicator": indicator,
            "indicator_name": CASS_INDICATORS.get(indicator, indicator),
            "latest_value": round(cass_series.iloc[-1], 2) if "index" in indicator else None,
            "yoy": round(latest_freight_yoy, 2),
            "yoy_3m_avg": round(freight_yoy.iloc[-3:].mean(), 2) if len(freight_yoy) >= 3 else round(latest_freight_yoy, 2),
            "cycle_status": cycle_status,
            "is_new_cycle_low": bool(latest_is_low),
            "cycle_low_window": cycle_window,
            "consecutive_negative_months": consecutive_months
        },
        "cpi_status": {
            "latest_yoy": round(latest_cpi_yoy, 2) if latest_cpi_yoy is not None else None,
            "yoy_3m_avg": round(cpi_3m_avg, 2) if cpi_3m_avg is not None else None,
            "trend": cpi_trend
        },
        "lead_alignment": alignment,
        "signal_assessment": signal_result,
        "historical_positioning": history_pos,
        "all_indicators": {
            key: {
                "latest_date": df.index[-1].strftime("%Y-%m-%d"),
                "latest_value": round(df.iloc[-1].values[0], 2),
                "data_points": len(df)
            }
            for key, df in cass_data.items()
        },
        "interpretation": generate_interpretation(
            latest_freight_yoy, cycle_status, signal_result, alignment, consecutive_months, indicator
        ),
        "caveats": [
            "CASS Freight Index 數據來自 MacroMicro，透過 Highcharts 爬取",
            f"數據可能有 1-2 個月延遲，最新值為 {latest_date.strftime('%Y-%m')}",
            "若有供給側衝擊（如罷工、天災、疫情），訊號可能失真",
            "領先相關性基於歷史數據，未來關係可能改變",
            "建議結合多個指標（Shipments + Expenditures）交叉驗證"
        ]
    }

    return result


def generate_interpretation(
    freight_yoy: float,
    cycle_status: str,
    signal_result: Dict,
    alignment: Dict,
    consecutive_months: int,
    indicator: str
) -> list:
    """產生解讀文字"""
    interp = []
    indicator_name = CASS_INDICATORS.get(indicator, indicator)

    # 貨運狀態描述
    if freight_yoy < 0:
        interp.append(f"{indicator_name} 年增率已轉為負值（{freight_yoy:.1f}%）")
        if cycle_status == "new_cycle_low":
            interp.append("並創下本輪週期新低")
    else:
        interp.append(f"{indicator_name} 年增率為正（{freight_yoy:.1f}%）")

    # 領先性說明
    if alignment["optimal_lead"]:
        interp.append(
            f"歷史上 CASS 指標通常領先 CPI 約 {alignment['optimal_lead']} 個月"
        )

    # 訊號強度
    if signal_result["confidence"] == "high":
        interp.append(
            f"訊號強度高：連續 {consecutive_months} 個月負增長 + 創週期新低"
        )
    elif signal_result["confidence"] == "medium":
        interp.append("訊號強度中等，建議結合其他 CASS 指標驗證")
    else:
        interp.append("訊號強度低，方向不明確")

    return interp


def run_quick_check(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    快速檢查模式

    Returns
    -------
    dict
        簡化的分析結果
    """
    result = run_analysis(
        start_date="2015-01-01",
        indicator=DEFAULT_INDICATOR,
        lead_months=DEFAULT_LEAD_MONTHS,
        cache_dir=cache_dir or "cache"
    )

    # 簡化輸出
    quick_result = {
        "as_of_date": result["metadata"]["as_of_date"],
        "indicator": result["freight_status"]["indicator"],
        "indicator_name": result["freight_status"]["indicator_name"],
        "freight_yoy": result["freight_status"]["yoy"],
        "cycle_status": result["freight_status"]["cycle_status"],
        "signal": result["signal_assessment"]["signal"],
        "confidence": result["signal_assessment"]["confidence"],
        "macro_implication": result["signal_assessment"]["macro_implication"],
        "all_indicators": result["all_indicators"]
    }

    return quick_result


def main():
    parser = argparse.ArgumentParser(
        description="美國貨運概況判斷通膨趨勢器（CASS Freight Index）"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速檢查模式"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2010-01-01",
        help="起始日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="結束日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--indicator",
        type=str,
        default=DEFAULT_INDICATOR,
        choices=list(CASS_INDICATORS.keys()),
        help=f"CASS 指標 (default: {DEFAULT_INDICATOR})"
    )
    parser.add_argument(
        "--lead-months",
        type=int,
        default=DEFAULT_LEAD_MONTHS,
        help=f"領先月數 (default: {DEFAULT_LEAD_MONTHS})"
    )
    parser.add_argument(
        "--yoy-threshold",
        type=float,
        default=DEFAULT_YOY_THRESHOLD,
        help=f"YoY 警戒門檻 (default: {DEFAULT_YOY_THRESHOLD})"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="快取目錄"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出檔案路徑 (JSON)"
    )

    args = parser.parse_args()

    try:
        if args.quick:
            result = run_quick_check(args.cache_dir)
            print("\n" + "=" * 60)
            print("CASS Freight Index - 通膨先行訊號快速檢查")
            print("=" * 60)
        else:
            result = run_analysis(
                start_date=args.start,
                end_date=args.end,
                indicator=args.indicator,
                lead_months=args.lead_months,
                yoy_threshold=args.yoy_threshold,
                cache_dir=args.cache_dir
            )
            print("\n" + "=" * 60)
            print("CASS Freight Index - 通膨先行訊號完整分析")
            print("=" * 60)

        # 輸出結果
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 儲存到檔案
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[Saved] {args.output}")

    except Exception as e:
        print(f"\n[Error] {e}")
        raise


if __name__ == "__main__":
    main()
