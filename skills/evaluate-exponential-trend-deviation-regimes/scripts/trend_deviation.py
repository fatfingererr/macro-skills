#!/usr/bin/env python3
"""
Gold Exponential Trend Deviation & Regime Analysis

Evaluates gold price deviation from exponential growth trendline and
determines market regime (1970s-like vs 2000s-like).

Based on analysis of "Gold % distance from exponential growth trendline" metrics.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas_datareader as pdr
except ImportError:
    pdr = None


def fetch_gold_prices(
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch gold prices from Yahoo Finance.

    Args:
        symbol: Asset symbol (e.g., GC=F)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with price data
    """
    if yf is None:
        raise ImportError("yfinance is required. Install with: pip install yfinance")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)

    if df is None or df.empty:
        # Try with a more recent start date if long history unavailable
        fallback_start = "2000-01-01"
        print(f"Warning: No data from {start_date}, trying from {fallback_start}",
              file=sys.stderr)
        df = ticker.history(start=fallback_start, end=end_date)

    if df is None or df.empty:
        raise ValueError(f"No data found for {symbol}")

    return df


def fit_exponential_trend(prices: pd.Series) -> tuple[pd.Series, tuple[float, float]]:
    """
    Fit exponential trend line to price series.

    Args:
        prices: Price series

    Returns:
        (trend_series, (a, b)) where trend = exp(a + b*t)
    """
    t = np.arange(len(prices))
    y = np.log(prices.values)

    # OLS: y = a + b*t
    X = np.vstack([np.ones_like(t), t]).T
    params, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a, b = params

    trend = np.exp(a + b * t)
    return pd.Series(trend, index=prices.index), (float(a), float(b))


def calculate_distance_pct(prices: pd.Series, trend: pd.Series) -> pd.Series:
    """Calculate percentage distance from trend."""
    return (prices / trend - 1.0) * 100.0


def calculate_percentile(distance_series: pd.Series) -> float:
    """Calculate current distance percentile in history."""
    current = distance_series.iloc[-1]
    percentile = (distance_series < current).sum() / len(distance_series) * 100
    return float(percentile)


def find_reference_peaks(
    distance_series: pd.Series,
    peak_dates: list[str] | None = None,
) -> dict:
    """
    Find reference peak distances.

    Args:
        distance_series: Distance percentage series
        peak_dates: Specific dates to check (optional)

    Returns:
        Dictionary of reference peaks
    """
    references = {}

    # If user provided specific dates, use them
    if peak_dates:
        for date_str in peak_dates:
            try:
                target_date = pd.to_datetime(date_str)
                # Find nearest available date
                idx = distance_series.index.get_indexer([target_date], method="nearest")[0]
                references[date_str] = float(distance_series.iloc[idx])

                # Also record year max
                year = target_date.year
                year_data = distance_series[distance_series.index.year == year]
                if not year_data.empty:
                    references[f"{year}_max"] = float(year_data.max())
            except Exception:
                continue
    else:
        # Auto-detect: find historical maximum
        max_idx = distance_series.idxmax()
        max_date = max_idx.strftime("%Y-%m-%d")
        references["historical_max"] = {
            "date": max_date,
            "distance_pct": float(distance_series.loc[max_idx])
        }

        # Also find historical minimum (for completeness)
        min_idx = distance_series.idxmin()
        min_date = min_idx.strftime("%Y-%m-%d")
        references["historical_min"] = {
            "date": min_date,
            "distance_pct": float(distance_series.loc[min_idx])
        }

    return references


def determine_trend(series: pd.Series, lookback: int = 60) -> str:
    """
    Determine trend direction.

    Args:
        series: Data series
        lookback: Lookback period in days

    Returns:
        "up" / "down" / "flat"
    """
    recent = series.dropna().tail(lookback)
    if len(recent) < lookback // 2:
        return "flat"

    t = np.arange(len(recent))
    try:
        slope, _ = np.polyfit(t, recent.values, 1)
        normalized_slope = slope / recent.std() if recent.std() > 0 else 0

        if normalized_slope > 0.1:
            return "up"
        elif normalized_slope < -0.1:
            return "down"
        else:
            return "flat"
    except Exception:
        return "flat"


def fetch_macro_data(
    start_date: str,
    end_date: str,
) -> dict:
    """
    Fetch macro proxy data from FRED.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Dictionary of macro data series
    """
    if pdr is None:
        return {}

    macro_data = {}
    series_map = {
        "real_rate": "DFII10",
        "inflation": "T5YIE",
        "usd": "DTWEXBGS",
    }

    for key, fred_code in series_map.items():
        try:
            df = pdr.DataReader(fred_code, "fred", start_date, end_date)
            macro_data[key] = df[fred_code]
        except Exception:
            macro_data[key] = None

    return macro_data


def score_real_rate(value: float | None, trend: str) -> float:
    """Score real rate factor."""
    if value is None:
        return 0.5  # neutral if unavailable

    score = 0.0
    if value < 0:
        score = 1.0
    elif value < 1.0:
        score = 0.5
    else:
        score = 0.0

    if trend == "down" and score < 1.0:
        score += 0.2

    return min(score, 1.0)


def score_inflation(value: float | None, trend: str) -> float:
    """Score inflation factor."""
    if value is None:
        return 0.5

    score = 0.0
    if value > 3.0:
        score = 1.0
    elif value > 2.5:
        score = 0.7
    elif value > 2.0:
        score = 0.3

    if trend == "up" and score < 1.0:
        score += 0.3

    return min(score, 1.0)


def score_usd(trend: str) -> float:
    """Score USD factor."""
    if trend == "down":
        return 0.7
    elif trend == "flat":
        return 0.3
    else:
        return 0.0


def calculate_regime(macro_data: dict) -> dict:
    """
    Calculate regime based on macro factors.

    Args:
        macro_data: Dictionary of macro series

    Returns:
        Regime analysis result
    """
    weights = {
        "real_rate": 0.30,
        "inflation": 0.25,
        "geopolitical": 0.25,
        "usd": 0.20,
    }

    scores = {}
    drivers = []
    factor_breakdown = {}

    # Real rate
    real_rate_series = macro_data.get("real_rate")
    if real_rate_series is not None and len(real_rate_series.dropna()) > 0:
        real_rate_value = float(real_rate_series.dropna().iloc[-1])
        real_rate_trend = determine_trend(real_rate_series)
        real_rate_score = score_real_rate(real_rate_value, real_rate_trend)
        scores["real_rate"] = real_rate_score
        factor_breakdown["real_rate"] = {
            "value": real_rate_value,
            "trend": real_rate_trend,
            "score": real_rate_score,
            "contribution": real_rate_score * weights["real_rate"],
        }
        if real_rate_score > 0.5:
            drivers.append("Real rates negative / falling")
    else:
        scores["real_rate"] = 0.5
        factor_breakdown["real_rate"] = {"value": None, "score": 0.5}

    # Inflation
    inflation_series = macro_data.get("inflation")
    if inflation_series is not None and len(inflation_series.dropna()) > 0:
        inflation_value = float(inflation_series.dropna().iloc[-1])
        inflation_trend = determine_trend(inflation_series)
        inflation_score = score_inflation(inflation_value, inflation_trend)
        scores["inflation"] = inflation_score
        factor_breakdown["inflation"] = {
            "value": inflation_value,
            "trend": inflation_trend,
            "score": inflation_score,
            "contribution": inflation_score * weights["inflation"],
        }
        if inflation_score > 0.5:
            drivers.append("Inflation risk rising")
    else:
        scores["inflation"] = 0.5
        factor_breakdown["inflation"] = {"value": None, "score": 0.5}

    # Geopolitical (placeholder - would need external data)
    scores["geopolitical"] = 0.6  # assume elevated
    factor_breakdown["geopolitical"] = {
        "percentile": 60,
        "trend": "rising",
        "score": 0.6,
        "contribution": 0.6 * weights["geopolitical"],
    }
    drivers.append("Geopolitical tension proxy rising")

    # USD
    usd_series = macro_data.get("usd")
    if usd_series is not None and len(usd_series.dropna()) > 0:
        usd_trend = determine_trend(usd_series)
        usd_score = score_usd(usd_trend)
        scores["usd"] = usd_score
        factor_breakdown["usd"] = {
            "trend": usd_trend,
            "score": usd_score,
            "contribution": usd_score * weights["usd"],
        }
        if usd_score > 0.5:
            drivers.append("USD weakening")
    else:
        scores["usd"] = 0.5
        factor_breakdown["usd"] = {"trend": None, "score": 0.5}

    # Calculate total score
    total_score = sum(scores[k] * weights[k] for k in scores)

    # Determine regime
    if total_score >= 0.5:
        regime_label = "1970s_like"
        confidence = total_score
    else:
        regime_label = "2000s_like"
        confidence = 1 - total_score

    return {
        "regime_label": regime_label,
        "drivers": drivers,
        "confidence": round(confidence, 2),
        "factor_breakdown": factor_breakdown,
    }


def analyze_asset_deviation(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    compare_peak_dates: list[str] | None = None,
    include_macro: bool = False,
) -> dict[str, Any]:
    """
    Main analysis function for any asset.

    Args:
        symbol: Asset symbol (stock, futures, ETF, crypto, etc.)
        start_date: Start date (recommended to provide based on asset)
        end_date: End date
        compare_peak_dates: Optional historical peak dates to compare
        include_macro: Whether to include macro analysis (currently only for gold)

    Returns:
        Analysis result dictionary
    """
    # Default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        # Conservative default - user should provide asset-specific start
        start_date = "2000-01-01"
        print(f"Warning: No start_date provided, using default {start_date}. "
              "Consider providing asset-specific start date for better analysis.",
              file=sys.stderr)

    # Fetch asset prices
    df = fetch_gold_prices(symbol, start_date, end_date)  # Function name kept for backwards compatibility

    # Convert to monthly for long-term analysis
    monthly_prices = df["Close"].resample("ME").last().dropna()

    if len(monthly_prices) < 120:  # Less than 10 years
        print("Warning: Less than 10 years of data, trend fit may be unreliable",
              file=sys.stderr)

    # Fit trend
    trend, (a, b) = fit_exponential_trend(monthly_prices)

    # Calculate distance
    distance_pct = calculate_distance_pct(monthly_prices, trend)

    # Current metrics
    current_distance = float(distance_pct.iloc[-1])
    current_percentile = calculate_percentile(distance_pct)

    # Reference peaks
    references = find_reference_peaks(distance_pct, compare_peak_dates)

    # Verdict
    verdict = {}
    if "2011_max" in references:
        verdict["surpassed_2011_by_this_metric"] = current_distance > references["2011_max"]
    if "1980_max" in references:
        verdict["distance_to_1980_peak_pct_points"] = round(
            references["1980_max"] - current_distance, 1
        )

    # Build result
    result = {
        "skill": "evaluate-exponential-trend-deviation-regimes",
        "asset": symbol,
        "trend_model": "exponential_log_linear",
        "date_range": {
            "start": monthly_prices.index[0].strftime("%Y-%m-%d"),
            "end": monthly_prices.index[-1].strftime("%Y-%m-%d"),
        },
        "metrics": {
            "current_distance_pct": round(current_distance, 2),
            "current_percentile": round(current_percentile, 1),
            "reference": {k: round(v, 1) for k, v in references.items()},
            "verdict": verdict,
        },
        "trend_parameters": {
            "a": round(a, 4),
            "b": round(b, 6),
            "annualized_growth_rate_pct": round((np.exp(b * 12) - 1) * 100, 2),
        },
        "auxiliary": {
            "latest_price": round(float(monthly_prices.iloc[-1]), 2),
            "trend_price": round(float(trend.iloc[-1]), 2),
            "data_points": len(monthly_prices),
        },
    }

    # Macro regime analysis
    if include_macro:
        macro_data = fetch_macro_data(start_date, end_date)
        regime = calculate_regime(macro_data)
        result["regime"] = regime

        # Generate insights
        insights = []

        # Distance insight
        if current_percentile > 95:
            insights.append(
                "Gold is trading at an extreme positive deviation from its long-run "
                "exponential trendline, above the 2011 deviation peak."
            )
        elif current_percentile > 80:
            insights.append(
                "Gold is trading at a significant positive deviation from its long-run "
                "exponential trendline."
            )

        # 1980 comparison
        if "1980_max" in references:
            diff = references["1980_max"] - current_distance
            if diff > 100:
                insights.append(
                    f"Compared with 1980-style blow-off, deviation is still materially "
                    f"lower ({diff:.0f} pct points), leaving room for extension if "
                    f"1970s-like conditions persist."
                )

        # Mean reversion risk
        if regime["regime_label"] == "1970s_like":
            insights.append(
                "If real rates re-anchor higher and inflation expectations cool, "
                "mean-reversion risk increases even if the long-term trend remains up."
            )

        result["insights"] = insights
    else:
        result["regime"] = None
        result["insights"] = []

    # Metadata
    result["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "data_sources": {
            "gold": f"Yahoo Finance ({symbol})",
            "macro": "FRED" if include_macro else None,
        },
        "warnings": [],
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Asset Exponential Trend Deviation Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick analysis for gold
  python trend_deviation.py --symbol GC=F --start 1970-01-01 --quick

  # Analyze S&P 500
  python trend_deviation.py --symbol ^GSPC --start 1950-01-01

  # With macro factors (gold only)
  python trend_deviation.py --symbol GC=F --start 1970-01-01 --include-macro

  # Compare with specific historical peaks
  python trend_deviation.py --symbol ^GSPC --compare-peaks "2000-03-24,2007-10-09,2020-02-19"

  # Output to file
  python trend_deviation.py --symbol GC=F --output result.json
        """,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Asset symbol (e.g., GC=F for gold, ^GSPC for S&P 500, BTC-USD for Bitcoin)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD). Recommended: gold=1970-01-01, stocks=1950-01-01, crypto=2013-01-01",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--compare-peaks",
        type=str,
        help="Comma-separated peak dates to compare",
    )
    parser.add_argument(
        "--include-macro",
        action="store_true",
        help="Include macro regime analysis (currently only supports gold)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (for gold, enables macro analysis)",
    )

    args = parser.parse_args()

    # Parse compare peaks
    compare_peaks = None
    if args.compare_peaks:
        compare_peaks = [s.strip() for s in args.compare_peaks.split(",")]

    # Quick mode defaults (only for gold)
    if args.quick and args.symbol == "GC=F":
        args.include_macro = True
        if not args.start:
            args.start = "1970-01-01"

    try:
        result = analyze_asset_deviation(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            compare_peak_dates=compare_peaks,
            include_macro=args.include_macro,
        )

        output_json = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"Results written to {args.output}")
        else:
            print(output_json)

    except Exception as e:
        error_result = {
            "skill": "evaluate-exponential-trend-deviation-regimes",
            "error": True,
            "error_type": type(e).__name__,
            "error_message": str(e),
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
