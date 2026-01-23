#!/usr/bin/env python3
"""
銀行信貸-存款脫鉤分析器

分析銀行貸款與存款之間的「信貸創造脫鉤」現象，
用以辨識聯準會緊縮政策在銀行體系內部的真實傳導效果。

Usage:
    python decoupling_analyzer.py --quick
    python decoupling_analyzer.py --start 2022-06-01 --end 2026-01-23
    python decoupling_analyzer.py --start 2022-06-01 --output result.json

Data Sources (Public FRED CSV):
    - TOTLL: Loans and Leases in Bank Credit, All Commercial Banks
      https://fred.stlouisfed.org/series/TOTLL
    - DPSACBW027SBOG: Deposits, All Commercial Banks
      https://fred.stlouisfed.org/series/DPSACBW027SBOG
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from io import StringIO

import numpy as np
import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================================
# Configuration
# ============================================================================

CONFIG = {
    # FRED Series IDs and their public CSV URLs
    "series": {
        "loans": {
            "id": "TOTLL",
            "name": "Loans and Leases in Bank Credit, All Commercial Banks",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TOTLL"
        },
        "deposits": {
            "id": "DPSACBW027SBOG",
            "name": "Deposits, All Commercial Banks",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DPSACBW027SBOG"
        }
    },

    # Analysis parameters
    "default_start": "2022-06-01",
    "default_frequency": "weekly",

    # Stress thresholds
    "stress_thresholds": {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.7,
        "extreme": 0.85
    },

    # Cache settings
    "cache_dir": Path(__file__).parent / "cache",
    "cache_max_age_hours": 24
}


# ============================================================================
# Data Fetching (Public FRED CSV - No API Key Required)
# ============================================================================

def fetch_fred_csv(series_key: str) -> pd.Series:
    """
    Fetch data from FRED public CSV endpoint.

    Args:
        series_key: Key in CONFIG["series"] (e.g., "loans", "deposits")

    Returns:
        pandas Series with datetime index
    """
    if not HAS_REQUESTS:
        print("Error: requests library required. Run: pip install requests")
        sys.exit(1)

    series_info = CONFIG["series"][series_key]
    url = series_info["url"]
    series_id = series_info["id"]

    print(f"Fetching {series_id} ({series_info['name']})...")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse CSV
        df = pd.read_csv(StringIO(response.text))

        # FRED CSV format: DATE, SERIES_ID columns
        df.columns = ["DATE", "VALUE"]
        df["DATE"] = pd.to_datetime(df["DATE"])
        df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")
        df = df.dropna()
        df = df.set_index("DATE")

        series = df["VALUE"]
        series.name = series_id

        print(f"  Downloaded {len(series)} data points")
        print(f"  Date range: {series.index.min().date()} to {series.index.max().date()}")

        return series

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {series_id}: {e}")
        return pd.Series()
    except Exception as e:
        print(f"Error parsing {series_id} data: {e}")
        return pd.Series()


def load_cached_data(series_key: str) -> Optional[pd.Series]:
    """Load data from cache if available and not expired."""
    series_id = CONFIG["series"][series_key]["id"]
    cache_file = CONFIG["cache_dir"] / f"{series_id}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            cached = json.load(f)

        # Check age
        fetched_at = datetime.fromisoformat(cached["fetched_at"])
        age = datetime.now() - fetched_at
        if age > timedelta(hours=CONFIG["cache_max_age_hours"]):
            print(f"Cache expired for {series_id} (age: {age})")
            return None

        # Convert to Series
        data = pd.Series(cached["data"])
        data.index = pd.to_datetime(data.index)
        data.name = series_id
        print(f"Using cached data for {series_id} (cached {age.seconds // 3600}h ago)")
        return data

    except Exception as e:
        print(f"Cache read error for {series_id}: {e}")
        return None


def save_to_cache(series_key: str, data: pd.Series) -> None:
    """Save data to cache."""
    series_id = CONFIG["series"][series_key]["id"]
    CONFIG["cache_dir"].mkdir(parents=True, exist_ok=True)
    cache_file = CONFIG["cache_dir"] / f"{series_id}.json"

    # Convert index to string for JSON serialization
    data_dict = {str(k): v for k, v in data.to_dict().items()}

    cached = {
        "series_id": series_id,
        "series_name": CONFIG["series"][series_key]["name"],
        "fetched_at": datetime.now().isoformat(),
        "data": data_dict
    }

    with open(cache_file, "w") as f:
        json.dump(cached, f, default=str, indent=2)

    print(f"  Cached to {cache_file}")


def get_data(
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> Tuple[pd.Series, pd.Series]:
    """
    Get loan and deposit data from FRED.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        use_cache: Whether to use cached data

    Returns:
        Tuple of (loans, deposits) as pandas Series
    """
    results = []

    for series_key in ["loans", "deposits"]:
        # Try cache first
        if use_cache:
            cached = load_cached_data(series_key)
            if cached is not None:
                results.append(cached)
                continue

        # Fetch from FRED public CSV
        data = fetch_fred_csv(series_key)
        if data.empty:
            print(f"Error: Failed to fetch {series_key} data")
            sys.exit(1)

        save_to_cache(series_key, data)
        results.append(data)

    # Filter by date range
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    loans = results[0][(results[0].index >= start) & (results[0].index <= end)]
    deposits = results[1][(results[1].index >= start) & (results[1].index <= end)]

    return loans, deposits


# ============================================================================
# Analysis Functions
# ============================================================================

def align_data(
    loans: pd.Series,
    deposits: pd.Series
) -> Tuple[pd.Series, pd.Series]:
    """Align loan and deposit series to common dates."""
    # Find common dates
    common_idx = loans.index.intersection(deposits.index)

    return (
        loans.loc[common_idx],
        deposits.loc[common_idx]
    )


def calculate_cumulative_changes(
    loans: pd.Series,
    deposits: pd.Series
) -> Dict[str, pd.Series]:
    """Calculate cumulative changes from base date."""
    return {
        "loan_change": loans - loans.iloc[0],
        "deposit_change": deposits - deposits.iloc[0]
    }


def calculate_decoupling_metrics(
    cumulative: Dict[str, pd.Series]
) -> Dict[str, Any]:
    """Calculate decoupling gap, stress ratio, and deposit dynamics."""
    loan_change = cumulative["loan_change"]
    deposit_change = cumulative["deposit_change"]

    # Decoupling gap: 貸款增量 - 存款增量
    # 正值表示貸款創造的存款「消失」了
    decoupling_gap = loan_change - deposit_change

    # Stress ratio: Gap / 新增貸款
    # 表示每單位新增貸款中，有多少比例的存款「被抽走」
    with np.errstate(divide='ignore', invalid='ignore'):
        stress_ratio = decoupling_gap / loan_change
        stress_ratio = stress_ratio.replace([np.inf, -np.inf], np.nan)

    # === 存款動態分析 (Deposit Dynamics) ===
    # 存款最大回撤（Maximum Drawdown）
    deposit_min = deposit_change.min()
    deposit_min_idx = deposit_change.idxmin()
    deposit_min_date = str(deposit_min_idx.date()) if hasattr(deposit_min_idx, 'date') else str(deposit_min_idx)

    # 當前存款變化
    current_deposit = deposit_change.iloc[-1]

    # 從低谷回升的幅度
    recovery_from_trough = current_deposit - deposit_min

    # 回升比率（相對於低谷深度）
    if deposit_min < 0:
        recovery_ratio = recovery_from_trough / abs(deposit_min)
    else:
        recovery_ratio = 0

    # 判斷當前階段
    if current_deposit < 0:
        if current_deposit <= deposit_min * 0.9:  # 接近或超過低谷
            phase = "contraction_deepening"
            phase_label = "存款收縮加深"
        else:
            phase = "contraction_stabilizing"
            phase_label = "存款收縮趨穩"
    else:
        if recovery_ratio > 1.5:
            phase = "strong_recovery"
            phase_label = "強勁回升"
        elif recovery_ratio > 1.0:
            phase = "recovery_but_lagging"
            phase_label = "回升中但落後貸款"
        else:
            phase = "partial_recovery"
            phase_label = "部分回升"

    return {
        "decoupling_gap": decoupling_gap,
        "stress_ratio": stress_ratio,
        "loan_change_series": loan_change,
        "deposit_change_series": deposit_change,
        "latest_gap": decoupling_gap.iloc[-1],
        "latest_stress_ratio": stress_ratio.iloc[-1] if not np.isnan(stress_ratio.iloc[-1]) else 0,
        "latest_loan_change": loan_change.iloc[-1],
        "latest_deposit_change": deposit_change.iloc[-1],
        # 存款動態
        "deposit_max_drawdown": deposit_min,
        "deposit_max_drawdown_date": deposit_min_date,
        "recovery_from_trough": recovery_from_trough,
        "recovery_ratio": recovery_ratio,
        "phase": phase,
        "phase_label": phase_label
    }


def assess_tightening(metrics: Dict[str, Any]) -> Dict[str, str]:
    """Assess tightening type based on metrics."""
    stress = metrics["latest_stress_ratio"]
    gap = metrics["latest_gap"]
    loan_change = metrics["latest_loan_change"]
    deposit_change = metrics["latest_deposit_change"]

    # Handle NaN stress ratio
    if np.isnan(stress):
        stress = 0

    # Determine stress level
    thresholds = CONFIG["stress_thresholds"]
    if stress > thresholds["extreme"]:
        stress_level = "extreme"
    elif stress > thresholds["high"]:
        stress_level = "high"
    elif stress > thresholds["medium"]:
        stress_level = "medium"
    elif stress > thresholds["low"]:
        stress_level = "low"
    else:
        stress_level = "normal"

    # Determine tightening type based on gap and stress
    if gap > 0 and stress > thresholds["high"]:
        tightening_type = "severe_decoupling"
        tightening_label = "嚴重信貸-存款脫鉤"
        driver = "deposit_outflow"
        driver_label = "存款外流/緊縮傳導"
    elif gap > 0 and stress > thresholds["medium"]:
        tightening_type = "moderate_decoupling"
        tightening_label = "中度信貸-存款脫鉤"
        driver = "tightening_transmission"
        driver_label = "緊縮政策傳導"
    elif gap > 0 and stress > thresholds["low"]:
        tightening_type = "mild_decoupling"
        tightening_label = "輕度脫鉤"
        driver = "mixed"
        driver_label = "混合因素"
    elif deposit_change < 0:
        tightening_type = "deposit_contraction"
        tightening_label = "存款收縮"
        driver = "deposit_flight"
        driver_label = "存款外逃"
    else:
        tightening_type = "neutral"
        tightening_label = "正常"
        driver = "none"
        driver_label = "無"

    # Confidence level based on data quality
    if stress > thresholds["high"]:
        confidence = "high"
    elif stress > thresholds["medium"]:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "stress_level": stress_level,
        "tightening_type": tightening_type,
        "tightening_label": tightening_label,
        "primary_driver": driver,
        "driver_label": driver_label,
        "confidence": confidence
    }


def generate_implication(
    assessment: Dict[str, str],
    metrics: Dict[str, Any]
) -> str:
    """Generate macro implication text."""
    gap = metrics["latest_gap"]
    loan_change = metrics["latest_loan_change"]
    deposit_change = metrics["latest_deposit_change"]

    if assessment["tightening_type"] == "severe_decoupling":
        return (
            f"銀行信貸與存款出現嚴重脫鉤。"
            f"貸款累積增加 {loan_change:,.0f} 億美元，但存款僅增加 {deposit_change:,.0f} 億美元，"
            f"落差達 {gap:,.0f} 億美元（{gap/1000:.2f} 兆美元）。"
            f"這顯示緊縮政策正有效傳導至銀行體系，存款端承受顯著壓力。"
        )
    elif assessment["tightening_type"] == "moderate_decoupling":
        return (
            f"銀行信貸創造與存款增長出現中度脫鉤。"
            f"貸款增加 {loan_change:,.0f} 億美元，存款增加 {deposit_change:,.0f} 億美元，"
            f"落差 {gap:,.0f} 億美元。金融條件正在收緊，但尚未達到極端水準。"
        )
    elif assessment["tightening_type"] == "mild_decoupling":
        return (
            f"銀行信貸與存款增長出現輕度脫鉤，落差約 {gap:,.0f} 億美元。"
            f"緊縮傳導已開始，但銀行負債端壓力尚在可控範圍。"
        )
    elif assessment["tightening_type"] == "deposit_contraction":
        return (
            f"存款出現絕對收縮（減少 {abs(deposit_change):,.0f} 億美元），"
            f"顯示資金正從銀行體系外流，可能流向貨幣市場基金或其他資產。"
        )
    else:
        return (
            f"銀行信貸與存款增長大致同步，"
            f"信貸創造機制正常運作，暫無明顯的脫鉤跡象。"
        )


# ============================================================================
# Output Functions
# ============================================================================

def format_output(
    start_date: str,
    end_date: str,
    loans: pd.Series,
    deposits: pd.Series,
    cumulative: Dict[str, pd.Series],
    metrics: Dict[str, Any],
    assessment: Dict[str, str]
) -> Dict[str, Any]:
    """Format analysis output as dictionary."""
    implication = generate_implication(assessment, metrics)

    # Get actual data range from the series
    actual_start = loans.index.min()
    actual_end = loans.index.max()

    return {
        "skill": "analyze_bank_credit_deposit_decoupling",
        "version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "status": "success",

        "analysis_period": {
            "requested_start": start_date,
            "requested_end": end_date,
            "actual_start": str(actual_start.date()),
            "actual_end": str(actual_end.date()),
            "frequency": CONFIG["default_frequency"],
            "observation_count": len(loans)
        },

        "data_sources": {
            "loans": {
                "series_id": CONFIG["series"]["loans"]["id"],
                "series_name": CONFIG["series"]["loans"]["name"],
                "url": CONFIG["series"]["loans"]["url"],
                "base_value_billion_usd": round(float(loans.iloc[0]), 2),
                "latest_value_billion_usd": round(float(loans.iloc[-1]), 2),
                "latest_date": str(loans.index[-1].date())
            },
            "deposits": {
                "series_id": CONFIG["series"]["deposits"]["id"],
                "series_name": CONFIG["series"]["deposits"]["name"],
                "url": CONFIG["series"]["deposits"]["url"],
                "base_value_billion_usd": round(float(deposits.iloc[0]), 2),
                "latest_value_billion_usd": round(float(deposits.iloc[-1]), 2),
                "latest_date": str(deposits.index[-1].date())
            }
        },

        "cumulative_changes": {
            "base_date": str(actual_start.date()),
            "end_date": str(actual_end.date()),
            "loans_billion_usd": round(metrics["latest_loan_change"], 2),
            "deposits_billion_usd": round(metrics["latest_deposit_change"], 2),
            "gap_billion_usd": round(metrics["latest_gap"], 2),
            "gap_trillion_usd": round(metrics["latest_gap"] / 1000, 3)
        },

        "deposit_dynamics": {
            "max_drawdown_billion_usd": round(metrics["deposit_max_drawdown"], 2),
            "max_drawdown_trillion_usd": round(metrics["deposit_max_drawdown"] / 1000, 3),
            "max_drawdown_date": metrics["deposit_max_drawdown_date"],
            "current_deposit_change_billion_usd": round(metrics["latest_deposit_change"], 2),
            "recovery_from_trough_billion_usd": round(metrics["recovery_from_trough"], 2),
            "recovery_ratio": round(metrics["recovery_ratio"], 2),
            "phase": metrics["phase"],
            "phase_label": metrics["phase_label"]
        },

        "assessment": {
            "decoupling_status": assessment["tightening_type"],
            "decoupling_status_label": assessment["tightening_label"],
            "deposit_stress_ratio": round(metrics["latest_stress_ratio"], 3),
            "interpretation": f"每新增 $1 貸款，僅有 ${1 - metrics['latest_stress_ratio']:.2f} 形成存款",
            "confidence": assessment["confidence"],
            "stress_level": assessment["stress_level"]
        },

        "macro_implication": implication,

        "recommended_next_checks": [
            "觀察銀行存款利率是否上升（搶存款跡象）",
            "追蹤 SOFR-Fed Funds 利差變化",
            "關注大額存款（>$250K）外逃跡象",
            "監控貨幣市場基金流入量"
        ],

        "caveats": [
            "本分析僅使用貸款與存款兩個公開 FRED 指標",
            "週頻數據可能錯過日內波動",
            "未納入 TGA、RRP 等其他流動性因素"
        ]
    }


def format_quick_output(
    metrics: Dict[str, Any],
    assessment: Dict[str, str],
    loans: pd.Series,
    deposits: pd.Series
) -> Dict[str, Any]:
    """Format quick check output."""
    return {
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "data_end_date": str(loans.index[-1].date()),
        "loans_billion_usd": round(float(loans.iloc[-1]), 2),
        "deposits_billion_usd": round(float(deposits.iloc[-1]), 2),
        "decoupling_gap_billion_usd": round(metrics["latest_gap"], 2),
        "decoupling_gap_trillion_usd": round(metrics["latest_gap"] / 1000, 3),
        "deposit_stress_ratio": round(metrics["latest_stress_ratio"], 3),
        "tightening_type": assessment["tightening_type"],
        "tightening_label": assessment["tightening_label"],
        "stress_level": assessment["stress_level"],
        "confidence": assessment["confidence"],
        "summary": f"存款壓力比率 {assessment['stress_level']}（{metrics['latest_stress_ratio']:.1%}），{assessment['tightening_label']}"
    }


# ============================================================================
# Main
# ============================================================================

def run_analysis(
    start_date: str,
    end_date: str,
    quick: bool = False,
    output_file: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Run the decoupling analysis."""
    print(f"\n{'='*60}")
    print(f"  銀行信貸-存款脫鉤分析")
    print(f"  Bank Credit-Deposit Decoupling Analysis")
    print(f"{'='*60}")
    print(f"分析期間: {start_date} 至 {end_date}")
    print(f"數據來源: FRED (Federal Reserve Economic Data)\n")

    # Fetch data from FRED public CSV
    loans, deposits = get_data(start_date, end_date, use_cache=use_cache)

    if loans.empty or deposits.empty:
        print("Error: Failed to retrieve data")
        return {"status": "error", "message": "Failed to retrieve data"}

    # Align data
    loans, deposits = align_data(loans, deposits)
    print(f"\n對齊後數據點數: {len(loans)}")
    print(f"實際數據範圍: {loans.index.min().date()} 至 {loans.index.max().date()}")

    # Calculate metrics
    cumulative = calculate_cumulative_changes(loans, deposits)
    metrics = calculate_decoupling_metrics(cumulative)
    assessment = assess_tightening(metrics)

    # Print summary
    print(f"\n{'─'*60}")
    print("分析結果摘要:")
    print(f"  貸款變化: {metrics['latest_loan_change']:+,.1f} 億美元")
    print(f"  存款變化: {metrics['latest_deposit_change']:+,.1f} 億美元")
    print(f"  脫鉤落差: {metrics['latest_gap']:,.1f} 億美元 ({metrics['latest_gap']/1000:.2f} 兆)")
    print(f"  壓力比率: {metrics['latest_stress_ratio']:.1%}")
    print(f"  判定結果: {assessment['tightening_label']} ({assessment['stress_level']})")
    print(f"{'─'*60}\n")

    # Format output
    if quick:
        result = format_quick_output(metrics, assessment, loans, deposits)
    else:
        result = format_output(
            start_date, end_date,
            loans, deposits,
            cumulative, metrics, assessment
        )

    # Output
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_json)

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n結果已存儲至: {output_file}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="銀行信貸-存款脫鉤分析器 (使用 FRED 公開數據)"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="快速檢查模式（簡化輸出）"
    )
    parser.add_argument(
        "--start", "-s",
        default=CONFIG["default_start"],
        help=f"分析起始日期 (預設: {CONFIG['default_start']})"
    )
    parser.add_argument(
        "--end", "-e",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析結束日期 (預設: 今天)"
    )
    parser.add_argument(
        "--output", "-o",
        help="輸出檔案路徑 (JSON)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="不使用快取數據，強制從 FRED 重新下載"
    )

    args = parser.parse_args()

    run_analysis(
        start_date=args.start,
        end_date=args.end,
        quick=args.quick,
        output_file=args.output,
        use_cache=not args.no_cache
    )


if __name__ == "__main__":
    main()
