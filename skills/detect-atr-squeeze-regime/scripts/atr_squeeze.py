#!/usr/bin/env python3
"""
ATR Squeeze Regime Detection

Detects whether an asset is in a "volatility-dominated squeeze" regime
based on 14-day exponentially smoothed ATR%.

Based on Ole Hansen's (Saxo Bank) analysis of silver market volatility.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None


def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    """Calculate True Range from OHLC data."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def calculate_atr(
    df: pd.DataFrame, period: int = 14, smoothing: str = "ema"
) -> pd.Series:
    """
    Calculate ATR with specified smoothing method.

    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period (default 14)
        smoothing: "ema" or "wilder"

    Returns:
        ATR series
    """
    tr = calculate_true_range(df)

    if smoothing == "ema":
        atr = tr.ewm(span=period, adjust=False).mean()
    elif smoothing == "wilder":
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    else:
        raise ValueError(f"Unsupported smoothing method: {smoothing}")

    return atr


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_reliability_score(regime: str, ratio: float) -> int:
    """
    Calculate technical level reliability score (0-100).

    Args:
        regime: Current regime classification
        ratio: ATR% ratio to baseline

    Returns:
        Score from 0 (least reliable) to 100 (most reliable)
    """
    if regime == "volatility_dominated_squeeze":
        # 2.0x -> 50, 4.5x -> 0
        score = max(0, int(50 - (ratio - 2.0) * 20))
    elif regime == "elevated_volatility_trend":
        # 1.2x -> 100, 2.0x -> 50
        score = int(50 + (2.0 - ratio) * 50 / 0.8)
    else:
        # 0.8x -> 100, 1.2x -> 90
        score = int(100 - (ratio - 0.8) * 25)

    return max(0, min(100, score))


def get_reliability_level(score: int) -> str:
    """Convert reliability score to level string."""
    if score >= 80:
        return "high"
    elif score >= 50:
        return "medium"
    elif score >= 20:
        return "low"
    else:
        return "very_low"


def classify_regime(
    atr_pct: float,
    ratio: float,
    high_vol_threshold: float = 6.0,
    spike_threshold: float = 2.0,
) -> str:
    """
    Classify market regime based on ATR% and ratio.

    Args:
        atr_pct: Current ATR as percentage of close
        ratio: ATR% ratio to baseline
        high_vol_threshold: Absolute ATR% threshold for high volatility
        spike_threshold: Ratio threshold for squeeze detection

    Returns:
        Regime classification string
    """
    if atr_pct >= high_vol_threshold and ratio >= spike_threshold:
        return "volatility_dominated_squeeze"
    elif ratio >= 1.2:
        return "elevated_volatility_trend"
    else:
        return "orderly_market"


def get_risk_adjustments(regime: str, atr_pct: float) -> dict[str, Any]:
    """
    Get risk adjustment recommendations based on regime.

    Args:
        regime: Current regime classification
        atr_pct: Current ATR%

    Returns:
        Dictionary of risk adjustment recommendations
    """
    if regime == "volatility_dominated_squeeze":
        stop_mult = round(2.0 + min(1.0, (atr_pct - 6.0) / 4.0), 1)
        position_scale = round(min(1.0, 3.0 / max(atr_pct, 0.01)), 2)
        timeframe = "weekly"
        instrument = "options_or_spreads"
    elif regime == "elevated_volatility_trend":
        stop_mult = round(1.5 + min(0.5, (atr_pct - 3.0) / 6.0), 1)
        position_scale = round(min(1.0, 4.0 / max(atr_pct, 0.01)), 2)
        timeframe = "daily"
        instrument = "naked_or_options"
    else:
        stop_mult = 1.2
        position_scale = 1.0
        timeframe = "any"
        instrument = "naked_position"

    return {
        "suggested_stop_atr_mult": stop_mult,
        "position_scale": position_scale,
        "recommended_timeframe": timeframe,
        "instrument_suggestion": instrument,
    }


def get_interpretation(regime: str, include_microstructure: bool = True) -> dict:
    """
    Get regime interpretation and tactical recommendations.

    Args:
        regime: Current regime classification
        include_microstructure: Whether to include microstructure notes

    Returns:
        Dictionary with explanation and tactics
    """
    interpretations = {
        "volatility_dominated_squeeze": {
            "regime_explanation": (
                "當前市場處於「波動主導的擠壓行情」。"
                "價格運動更多反映「被迫流」：保證金調整、期權避險、空頭回補。"
                "技術位可靠度下降，停損容易被噪音掃掉。"
            ),
            "tactics": [
                "偏向較長週期決策，降低被日內噪音主導的風險。",
                "若要參與趨勢，優先考慮 defined-risk（期權/價差）結構。",
                "避免緊停損的短線交易，結構性受損。",
                "宏觀方向對也難撐：短期雜訊大到足以讓正確部位先被洗掉。",
            ],
        },
        "elevated_volatility_trend": {
            "regime_explanation": (
                "當前市場波動偏高但仍有結構。"
                "技術位有效性下降，但方向性仍可辨識。"
                "需要適應性調整風控參數。"
            ),
            "tactics": [
                "適度放寬停損，避免被正常波動掃出。",
                "降低倉位規模，維持相同風險暴露。",
                "偏向日線以上週期交易。",
                "注意波動可能進一步擴大。",
            ],
        },
        "orderly_market": {
            "regime_explanation": (
                "當前市場處於秩序狀態。" "波動在歷史常態範圍內，技術分析有效。" "標準交易策略可用。"
            ),
            "tactics": [
                "正常執行交易策略。",
                "技術位（支撐/壓力）可靠度高。",
                "標準停損設置即可。",
                "任意時間框架皆可操作。",
            ],
        },
    }

    result = interpretations.get(
        regime, interpretations["orderly_market"]
    )

    if include_microstructure and regime == "volatility_dominated_squeeze":
        result["microstructure_notes"] = {
            "forced_flows": [
                "保證金調整 / 槓桿去化",
                "期權 Delta/Gamma 避險",
                "空頭回補",
                "被動風險平價再平衡",
            ],
            "technical_unreliability": (
                "突破/跌破更常是流動性與風控觸發的結果，而非市場共識改變。"
            ),
            "stop_vulnerability": "同一口波動可掃過多層 stops，低時間尺度交易結構性受損。",
        }

    return result


def fetch_data(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a symbol.

    Args:
        symbol: Asset symbol (e.g., SI=F, GC=F)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval (1d, 1h, etc.)

    Returns:
        DataFrame with OHLCV data
    """
    if yf is None:
        raise ImportError("yfinance is required. Install with: pip install yfinance")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)

    if df.empty:
        raise ValueError(f"No data found for {symbol}")

    # Ensure required columns exist
    required_cols = ["High", "Low", "Close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def detect_atr_squeeze_regime(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    timeframe: str = "1d",
    atr_period: int = 14,
    atr_smoothing: str = "ema",
    use_percent_atr: bool = True,
    baseline_window_days: int = 756,
    spike_threshold_x: float = 2.0,
    high_vol_threshold_pct: float = 6.0,
    rsi_period: int = 14,
    include_microstructure_notes: bool = True,
) -> dict[str, Any]:
    """
    Detect ATR squeeze regime for a given symbol.

    Args:
        symbol: Asset symbol (e.g., SI=F for silver futures)
        start_date: Start date (YYYY-MM-DD), default 5 years ago
        end_date: End date (YYYY-MM-DD), default today
        timeframe: Price frequency (1d, 1h)
        atr_period: ATR calculation period
        atr_smoothing: ATR smoothing method (ema, wilder)
        use_percent_atr: Convert ATR to percentage of close
        baseline_window_days: Rolling window for baseline calculation
        spike_threshold_x: Ratio threshold for squeeze detection
        high_vol_threshold_pct: Absolute ATR% threshold
        rsi_period: RSI calculation period
        include_microstructure_notes: Include microstructure explanations

    Returns:
        Dictionary with regime detection results
    """
    # Default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365 * 5)
        start_date = start_dt.strftime("%Y-%m-%d")

    # Fetch data
    df = fetch_data(symbol, start_date, end_date, timeframe)

    # Calculate ATR
    atr = calculate_atr(df, atr_period, atr_smoothing)

    # Convert to percentage if requested
    if use_percent_atr:
        atr_pct = 100.0 * atr / df["Close"]
    else:
        atr_pct = atr

    # Calculate baseline
    baseline = atr_pct.rolling(baseline_window_days).mean()

    # Calculate ratio
    ratio = atr_pct / baseline

    # Get latest values
    latest_atr_pct = float(atr_pct.iloc[-1])
    latest_baseline = float(baseline.iloc[-1]) if not pd.isna(baseline.iloc[-1]) else latest_atr_pct
    latest_ratio = float(ratio.iloc[-1]) if not pd.isna(ratio.iloc[-1]) else 1.0

    # Calculate RSI
    rsi = calculate_rsi(df["Close"], rsi_period)
    latest_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    # Classify regime
    regime = classify_regime(
        latest_atr_pct, latest_ratio, high_vol_threshold_pct, spike_threshold_x
    )

    # Calculate reliability score
    reliability_score = calculate_reliability_score(regime, latest_ratio)
    reliability_level = get_reliability_level(reliability_score)

    # Get risk adjustments
    risk_adjustments = get_risk_adjustments(regime, latest_atr_pct)

    # Get interpretation
    interpretation = get_interpretation(regime, include_microstructure_notes)

    # Build result
    result = {
        "skill": "detect-atr-squeeze-regime",
        "symbol": symbol,
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "data_range": {
            "start": df.index[0].strftime("%Y-%m-%d"),
            "end": df.index[-1].strftime("%Y-%m-%d"),
            "trading_days": len(df),
        },
        "regime": regime,
        "atr_pct": round(latest_atr_pct, 2),
        "atr_ratio_to_baseline": round(latest_ratio, 2),
        "baseline_atr_pct": round(latest_baseline, 2),
        "baseline_period_days": baseline_window_days,
        "tech_level_reliability": reliability_level,
        "tech_level_reliability_score": reliability_score,
        "risk_adjustments": risk_adjustments,
        "interpretation": interpretation,
        "auxiliary_indicators": {
            "rsi_14": round(latest_rsi, 1),
            "latest_close": round(float(df["Close"].iloc[-1]), 2),
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "parameters": {
                "atr_period": atr_period,
                "atr_smoothing": atr_smoothing,
                "baseline_window_days": baseline_window_days,
                "spike_threshold_x": spike_threshold_x,
                "high_vol_threshold_pct": high_vol_threshold_pct,
            },
        },
    }

    return result


def scan_multiple_symbols(
    symbols: list[str],
    **kwargs,
) -> dict[str, Any]:
    """
    Scan multiple symbols for ATR squeeze regime.

    Args:
        symbols: List of symbols to scan
        **kwargs: Parameters passed to detect_atr_squeeze_regime

    Returns:
        Dictionary with scan results and summary
    """
    results = []
    errors = []

    for symbol in symbols:
        try:
            result = detect_atr_squeeze_regime(symbol, **kwargs)
            results.append({
                "symbol": symbol,
                "regime": result["regime"],
                "atr_pct": result["atr_pct"],
                "ratio": result["atr_ratio_to_baseline"],
                "reliability_score": result["tech_level_reliability_score"],
                "suggested_stop_mult": result["risk_adjustments"]["suggested_stop_atr_mult"],
            })
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})

    # Calculate summary
    squeeze_count = sum(1 for r in results if r["regime"] == "volatility_dominated_squeeze")
    elevated_count = sum(1 for r in results if r["regime"] == "elevated_volatility_trend")
    orderly_count = sum(1 for r in results if r["regime"] == "orderly_market")

    highest_ratio = max(results, key=lambda x: x["ratio"]) if results else None
    lowest_ratio = min(results, key=lambda x: x["ratio"]) if results else None

    # Generate alerts
    alerts = []
    for r in results:
        if r["regime"] == "volatility_dominated_squeeze":
            alerts.append({
                "type": "squeeze_detected",
                "symbol": r["symbol"],
                "message": f"{r['symbol']} 處於擠壓行情（ratio={r['ratio']}x），建議降槓桿",
            })

    return {
        "skill": "detect-atr-squeeze-regime",
        "scan_mode": True,
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "scan_results": results,
        "errors": errors if errors else None,
        "summary": {
            "total_assets": len(symbols),
            "successful": len(results),
            "failed": len(errors),
            "squeeze_count": squeeze_count,
            "elevated_count": elevated_count,
            "orderly_count": orderly_count,
            "highest_ratio": {
                "symbol": highest_ratio["symbol"],
                "ratio": highest_ratio["ratio"],
            } if highest_ratio else None,
            "lowest_ratio": {
                "symbol": lowest_ratio["symbol"],
                "ratio": lowest_ratio["ratio"],
            } if lowest_ratio else None,
        },
        "alerts": alerts if alerts else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Detect ATR Squeeze Regime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick check for silver
  python atr_squeeze.py --symbol SI=F --quick

  # Full analysis with custom parameters
  python atr_squeeze.py --symbol SI=F --start 2020-01-01 --end 2026-01-01

  # Scan multiple assets
  python atr_squeeze.py --scan SI=F,GC=F,CL=F

  # Output to file
  python atr_squeeze.py --symbol SI=F --output result.json
        """,
    )

    parser.add_argument(
        "--symbol",
        type=str,
        help="Asset symbol (e.g., SI=F, GC=F, XAGUSD)",
    )
    parser.add_argument(
        "--scan",
        type=str,
        help="Comma-separated list of symbols to scan",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        help="Price frequency (1d, 1h)",
    )
    parser.add_argument(
        "--atr-period",
        type=int,
        default=14,
        help="ATR calculation period",
    )
    parser.add_argument(
        "--atr-smoothing",
        type=str,
        default="ema",
        choices=["ema", "wilder"],
        help="ATR smoothing method",
    )
    parser.add_argument(
        "--baseline-window",
        type=int,
        default=756,
        help="Baseline window in trading days",
    )
    parser.add_argument(
        "--spike-threshold",
        type=float,
        default=2.0,
        help="Ratio threshold for squeeze detection",
    )
    parser.add_argument(
        "--high-vol-threshold",
        type=float,
        default=6.0,
        help="Absolute ATR%% threshold",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with default symbol (SI=F)",
    )

    args = parser.parse_args()

    # Handle quick mode
    if args.quick and not args.symbol and not args.scan:
        args.symbol = "SI=F"

    # Validate arguments
    if not args.symbol and not args.scan:
        parser.error("Either --symbol or --scan is required")

    # Build parameters
    params = {
        "start_date": args.start,
        "end_date": args.end,
        "timeframe": args.timeframe,
        "atr_period": args.atr_period,
        "atr_smoothing": args.atr_smoothing,
        "baseline_window_days": args.baseline_window,
        "spike_threshold_x": args.spike_threshold,
        "high_vol_threshold_pct": args.high_vol_threshold,
    }

    try:
        if args.scan:
            # Scan mode
            symbols = [s.strip() for s in args.scan.split(",")]
            result = scan_multiple_symbols(symbols, **params)
        else:
            # Single symbol mode
            result = detect_atr_squeeze_regime(args.symbol, **params)

        # Output
        output_json = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"Results written to {args.output}")
        else:
            print(output_json)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
