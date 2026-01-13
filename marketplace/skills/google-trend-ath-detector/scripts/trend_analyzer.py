"""
Google Trend ATH Detector - Core Analysis Script

Fetches Google Trends data, performs seasonality decomposition,
detects ATH and anomalies, and classifies signal types.
"""

import json
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np


@dataclass
class AnalysisParams:
    """Analysis parameters with defaults"""
    topic: str
    geo: str
    timeframe: str
    granularity: str = "weekly"
    use_topic_entity: bool = True
    smoothing_window: int = 4
    seasonality_method: str = "stl"
    ath_lookback_policy: str = "full_history"
    anomaly_method: str = "zscore"
    anomaly_threshold: float = 2.5
    compare_terms: Optional[List[str]] = None
    related_queries: bool = True


def fetch_trends(
    topic: str,
    geo: str,
    timeframe: str,
    granularity: str = "weekly",
    use_topic_entity: bool = True
) -> pd.Series:
    """
    Fetch Google Trends interest over time.

    Args:
        topic: Search topic or keyword
        geo: Geographic region code (e.g., 'US')
        timeframe: Time range (e.g., '2004-01-01 2025-12-31')
        granularity: Data granularity (daily/weekly/monthly)
        use_topic_entity: Use Topic Entity vs raw keyword

    Returns:
        pandas Series with DatetimeIndex
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("pytrends not installed. Install with: pip install pytrends")
        return pd.Series()

    pytrends = TrendReq(hl='en-US', tz=360)

    kw_list = [topic]

    # Optionally resolve to Topic Entity
    if use_topic_entity:
        suggestions = pytrends.suggestions(keyword=topic)
        if suggestions:
            # Use the first suggestion's mid (Topic ID)
            kw_list = [suggestions[0].get('mid', topic)]

    pytrends.build_payload(
        kw_list=kw_list,
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop=''
    )

    df = pytrends.interest_over_time()

    if df.empty:
        return pd.Series()

    # Return the first column (topic data)
    col = df.columns[0]
    return df[col]


def fetch_related_queries(
    topic: str,
    geo: str,
    timeframe: str
) -> Optional[Dict]:
    """
    Fetch related queries (top and rising).

    Returns:
        Dict with 'top' and 'rising' DataFrames
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return None

    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload([topic], geo=geo, timeframe=timeframe)

    related = pytrends.related_queries()

    if topic in related:
        return related[topic]
    return None


def stl_decompose(
    ts: pd.Series,
    granularity: str = "weekly"
) -> Dict[str, Any]:
    """
    Perform STL seasonal decomposition.

    Returns:
        Dict with trend, seasonal, resid, seasonal_strength
    """
    try:
        from statsmodels.tsa.seasonal import STL
    except ImportError:
        print("statsmodels not installed. Install with: pip install statsmodels")
        return {}

    # Determine period
    period = 52 if granularity == "weekly" else 12

    # Clean data
    ts_clean = ts.dropna()

    if len(ts_clean) < period * 2:
        print(f"Warning: Need at least {period * 2} data points for STL")
        return {}

    # STL decomposition
    stl = STL(ts_clean, period=period, robust=True)
    result = stl.fit()

    # Calculate seasonal strength
    seasonal_plus_resid = result.seasonal + result.resid
    seasonal_strength = 1 - result.resid.var() / seasonal_plus_resid.var()

    return {
        'trend': result.trend,
        'seasonal': result.seasonal,
        'resid': result.resid,
        'seasonal_strength': round(float(seasonal_strength), 3)
    }


def compute_anomaly_score(
    resid: pd.Series,
    method: str = "zscore"
) -> Dict[str, Any]:
    """
    Compute anomaly score on residuals.

    Args:
        resid: Residual series from decomposition
        method: 'zscore' or 'mad'

    Returns:
        Dict with score and details
    """
    if method == "zscore":
        mean = resid.mean()
        std = resid.std()
        latest_score = (resid.iloc[-1] - mean) / std if std > 0 else 0

        return {
            'method': 'zscore',
            'mean': float(mean),
            'std': float(std),
            'latest_score': round(float(latest_score), 2),
            'all_scores': ((resid - mean) / std).tolist()
        }

    elif method == "mad":
        try:
            from scipy.stats import median_abs_deviation
            mad = median_abs_deviation(resid, nan_policy='omit')
            median = resid.median()
            latest_score = (resid.iloc[-1] - median) / mad if mad > 0 else 0

            return {
                'method': 'mad',
                'median': float(median),
                'mad': float(mad),
                'latest_score': round(float(latest_score), 2)
            }
        except ImportError:
            print("scipy not installed for MAD calculation")
            return {}

    return {}


def classify_signal(
    is_ath: bool,
    is_anomaly: bool,
    seasonal_strength: float,
    trend: Optional[pd.Series],
    resid: Optional[pd.Series]
) -> str:
    """
    Classify signal type based on analysis results.

    Returns:
        One of: 'seasonal_spike', 'event_driven_shock', 'regime_shift', 'normal'
    """
    # Seasonal spike: strong seasonality, not anomalous
    if seasonal_strength > 0.5 and not is_anomaly:
        return "seasonal_spike"

    # Regime shift: ATH + anomaly + elevated trend
    if is_ath and is_anomaly and trend is not None:
        recent_trend = trend.iloc[-52:].mean() if len(trend) > 52 else trend.mean()
        historical_trend = trend.iloc[:-52].mean() if len(trend) > 52 else trend.mean()

        if recent_trend > historical_trend * 1.2:
            return "regime_shift"

    # Event-driven shock: anomalous but not regime shift
    if is_anomaly:
        return "event_driven_shock"

    return "normal"


def extract_drivers(related_queries: Optional[Dict]) -> List[Dict]:
    """
    Extract driver terms from related queries.
    """
    drivers = []

    if not related_queries:
        return drivers

    # Rising queries
    if 'rising' in related_queries and related_queries['rising'] is not None:
        rising_df = related_queries['rising']
        for _, row in rising_df.head(10).iterrows():
            drivers.append({
                'term': row.get('query', ''),
                'type': 'rising',
                'value': str(row.get('value', ''))
            })

    # Top queries
    if 'top' in related_queries and related_queries['top'] is not None:
        top_df = related_queries['top']
        for _, row in top_df.head(5).iterrows():
            drivers.append({
                'term': row.get('query', ''),
                'type': 'top',
                'value': int(row.get('value', 0))
            })

    return drivers


def analyze_google_trends_ath_signal(
    topic: str,
    geo: str,
    timeframe: str,
    granularity: str = "weekly",
    use_topic_entity: bool = True,
    smoothing_window: int = 4,
    seasonality_method: str = "stl",
    anomaly_method: str = "zscore",
    anomaly_threshold: float = 2.5,
    related_queries: bool = True,
    compare_terms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main analysis function.

    Performs complete ATH detection and signal classification.
    """
    result = {
        'topic': topic,
        'geo': geo,
        'timeframe': timeframe,
        'granularity': granularity,
        'analyzed_at': datetime.now().isoformat()
    }

    # 1. Fetch trends data
    ts = fetch_trends(topic, geo, timeframe, granularity, use_topic_entity)

    if ts.empty:
        result['error'] = "Failed to fetch Google Trends data"
        return result

    # 2. Smooth
    ts_smoothed = ts.rolling(smoothing_window).mean().dropna()

    # 3. Basic stats
    latest = float(ts.iloc[-1])
    hist_max = float(ts.max())
    is_ath = latest >= hist_max * 0.98  # 2% tolerance

    result['latest'] = latest
    result['hist_max'] = hist_max
    result['is_all_time_high'] = is_ath

    # 4. Seasonality decomposition
    decomposition = {}
    seasonal_strength = 0.0

    if seasonality_method == "stl" and len(ts_smoothed) >= 104:
        decomposition = stl_decompose(ts_smoothed, granularity)
        seasonal_strength = decomposition.get('seasonal_strength', 0.0)

        result['seasonality'] = {
            'method': seasonality_method,
            'is_seasonal_pattern_detected': seasonal_strength > 0.3,
            'seasonal_strength': seasonal_strength
        }
    else:
        result['seasonality'] = {
            'method': 'none',
            'is_seasonal_pattern_detected': False,
            'seasonal_strength': 0.0
        }

    # 5. Anomaly detection
    if decomposition and 'resid' in decomposition:
        resid = decomposition['resid']
    else:
        # Use raw series minus mean
        resid = ts_smoothed - ts_smoothed.mean()

    anomaly_result = compute_anomaly_score(resid, anomaly_method)
    latest_score = anomaly_result.get('latest_score', 0.0)
    is_anomaly = abs(latest_score) >= anomaly_threshold

    result['anomaly_detection'] = {
        'method': anomaly_method,
        'threshold': anomaly_threshold,
        'latest_score': latest_score,
        'is_anomaly': is_anomaly
    }

    # 6. Signal classification
    trend = decomposition.get('trend') if decomposition else None
    signal_type = classify_signal(
        is_ath, is_anomaly, seasonal_strength, trend, resid
    )
    result['signal_type'] = signal_type

    # 7. Related queries / drivers
    if related_queries:
        rq = fetch_related_queries(topic, geo, timeframe)
        drivers = extract_drivers(rq)
        result['drivers_from_related_queries'] = drivers[:10]

    # 8. Compare terms (if provided)
    if compare_terms:
        correlations = {}
        for term in compare_terms:
            compare_ts = fetch_trends(term, geo, timeframe, granularity, False)
            if not compare_ts.empty:
                # Align series
                aligned = pd.concat([ts, compare_ts], axis=1).dropna()
                if len(aligned) > 10:
                    corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
                    correlations[term] = round(float(corr), 3)

        result['compare_correlations'] = correlations

    return result


# CLI interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Google Trend ATH Detector"
    )
    parser.add_argument("--topic", type=str, required=True,
                        help="Google Trends topic")
    parser.add_argument("--geo", type=str, default="US",
                        help="Geographic region")
    parser.add_argument("--timeframe", type=str,
                        default="2004-01-01 2025-12-31",
                        help="Time range")
    parser.add_argument("--granularity", type=str, default="weekly",
                        choices=["daily", "weekly", "monthly"])
    parser.add_argument("--threshold", type=float, default=2.5,
                        help="Anomaly threshold")
    parser.add_argument("--compare", type=str, default="",
                        help="Comma-separated compare terms")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    compare_terms = args.compare.split(",") if args.compare else None

    result = analyze_google_trends_ath_signal(
        topic=args.topic,
        geo=args.geo,
        timeframe=args.timeframe,
        granularity=args.granularity,
        anomaly_threshold=args.threshold,
        compare_terms=compare_terms
    )

    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Results written to: {args.output}")
    else:
        print(output_json)
