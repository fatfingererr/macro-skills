#!/usr/bin/env python3
"""
Palladium-Lead-Silver Turning Point Detection

Detects whether palladium leads silver in short-term turning points,
using quantifiable cross-metal confirmation rules.

Based on the hypothesis that palladium, as a smaller/less liquid market,
reacts faster to macro changes, with silver following.
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
    from scipy import signal, stats
    from scipy.signal import find_peaks
except ImportError:
    signal = None
    stats = None
    find_peaks = None


# =============================================================================
# Data Loading
# =============================================================================


def fetch_data(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    interval: str = "1h",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a symbol using yfinance.

    Args:
        symbol: Asset symbol (e.g., SI=F, PA=F)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval (1h, 4h, 1d)

    Returns:
        DataFrame with OHLCV data
    """
    if yf is None:
        raise ImportError("yfinance is required. Install with: pip install yfinance")

    # Default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365 * 2)
        start_date = start_dt.strftime("%Y-%m-%d")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)

    if df.empty:
        raise ValueError(f"No data found for {symbol}")

    return df


def align_data(ag_df: pd.DataFrame, pd_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align silver and palladium time series.

    Args:
        ag_df: Silver DataFrame
        pd_df: Palladium DataFrame

    Returns:
        Combined DataFrame with aligned timestamps
    """
    # Find common index
    common_index = ag_df.index.intersection(pd_df.index)

    if len(common_index) == 0:
        raise ValueError("No overlapping timestamps between silver and palladium data")

    ag_aligned = ag_df.reindex(common_index).ffill()
    pd_aligned = pd_df.reindex(common_index).ffill()

    df = pd.DataFrame(
        {
            "ag_close": ag_aligned["Close"],
            "pd_close": pd_aligned["Close"],
            "ag_high": ag_aligned["High"],
            "ag_low": ag_aligned["Low"],
            "pd_high": pd_aligned["High"],
            "pd_low": pd_aligned["Low"],
        }
    )

    # Calculate returns
    df["ag_ret"] = np.log(df["ag_close"]).diff()
    df["pd_ret"] = np.log(df["pd_close"]).diff()

    return df.dropna()


# =============================================================================
# Turning Point Detection
# =============================================================================


def detect_pivots(
    prices: pd.Series, left: int = 3, right: int = 3
) -> list[dict[str, Any]]:
    """
    Detect pivot highs and lows.

    Args:
        prices: Price series
        left: Number of bars to the left for confirmation
        right: Number of bars to the right for confirmation

    Returns:
        List of turning point events
    """
    turns = []
    prices_arr = prices.values

    for i in range(left, len(prices) - right):
        window = prices_arr[i - left : i + right + 1]
        current = prices_arr[i]

        if current == window.max():
            turns.append(
                {
                    "idx": i,
                    "ts": prices.index[i],
                    "type": "top",
                    "price": float(current),
                }
            )
        elif current == window.min():
            turns.append(
                {
                    "idx": i,
                    "ts": prices.index[i],
                    "type": "bottom",
                    "price": float(current),
                }
            )

    return turns


def detect_peaks_method(
    prices: pd.Series, prominence: float = 0.5, distance: int = 5
) -> list[dict[str, Any]]:
    """
    Detect turning points using scipy find_peaks.

    Args:
        prices: Price series
        prominence: Prominence threshold (std dev multiplier)
        distance: Minimum distance between peaks

    Returns:
        List of turning point events
    """
    if find_peaks is None:
        raise ImportError("scipy is required. Install with: pip install scipy")

    turns = []
    prom_value = prominence * prices.std()

    # Find tops
    tops, _ = find_peaks(prices.values, prominence=prom_value, distance=distance)

    # Find bottoms (invert)
    bottoms, _ = find_peaks(-prices.values, prominence=prom_value, distance=distance)

    for t in tops:
        turns.append(
            {"idx": t, "ts": prices.index[t], "type": "top", "price": float(prices.iloc[t])}
        )

    for b in bottoms:
        turns.append(
            {
                "idx": b,
                "ts": prices.index[b],
                "type": "bottom",
                "price": float(prices.iloc[b]),
            }
        )

    return sorted(turns, key=lambda x: x["idx"])


def detect_slope_changes(
    prices: pd.Series, window: int = 10
) -> list[dict[str, Any]]:
    """
    Detect turning points based on slope direction changes.

    Args:
        prices: Price series
        window: Rolling window for slope calculation

    Returns:
        List of turning point events
    """
    if stats is None:
        raise ImportError("scipy is required. Install with: pip install scipy")

    def rolling_slope(s):
        x = np.arange(len(s))
        slope, _, _, _, _ = stats.linregress(x, s)
        return slope

    slopes = prices.rolling(window).apply(rolling_slope, raw=False)

    # Find sign changes
    sign_change = (slopes.shift(1) * slopes) < 0

    turns = []
    for i in np.where(sign_change)[0]:
        if slopes.iloc[i] < 0 and slopes.iloc[i - 1] > 0:
            turns.append(
                {
                    "idx": i,
                    "ts": prices.index[i],
                    "type": "top",
                    "price": float(prices.iloc[i]),
                }
            )
        elif slopes.iloc[i] > 0 and slopes.iloc[i - 1] < 0:
            turns.append(
                {
                    "idx": i,
                    "ts": prices.index[i],
                    "type": "bottom",
                    "price": float(prices.iloc[i]),
                }
            )

    return turns


def detect_turns(
    prices: pd.Series,
    method: str = "pivot",
    pivot_left: int = 3,
    pivot_right: int = 3,
    prominence: float = 0.5,
    distance: int = 5,
    slope_window: int = 10,
) -> list[dict[str, Any]]:
    """
    Detect turning points using specified method.

    Args:
        prices: Price series
        method: Detection method (pivot, peaks, slope_change)
        pivot_left: Left confirmation bars for pivot
        pivot_right: Right confirmation bars for pivot
        prominence: Prominence for peaks method
        distance: Distance for peaks method
        slope_window: Window for slope_change method

    Returns:
        List of turning point events
    """
    if method == "pivot":
        return detect_pivots(prices, pivot_left, pivot_right)
    elif method == "peaks":
        return detect_peaks_method(prices, prominence, distance)
    elif method == "slope_change":
        return detect_slope_changes(prices, slope_window)
    else:
        raise ValueError(f"Unknown turn_method: {method}")


# =============================================================================
# Lead-Lag Analysis
# =============================================================================


def estimate_lead_lag(
    pd_ret: np.ndarray, ag_ret: np.ndarray, max_lag: int = 24
) -> tuple[int, float]:
    """
    Estimate lead-lag relationship using cross-correlation.

    Args:
        pd_ret: Palladium returns
        ag_ret: Silver returns
        max_lag: Maximum lag to consider

    Returns:
        Tuple of (best_lag, best_correlation)
        Positive lag means palladium leads silver
    """
    if signal is None:
        raise ImportError("scipy is required. Install with: pip install scipy")

    # Compute cross-correlation
    correlation = signal.correlate(ag_ret, pd_ret, mode="full")
    lags = signal.correlation_lags(len(ag_ret), len(pd_ret), mode="full")

    # Normalize
    correlation = correlation / len(ag_ret)

    # Restrict to [-max_lag, max_lag]
    mask = (lags >= -max_lag) & (lags <= max_lag)
    correlation = correlation[mask]
    lags = lags[mask]

    # Find maximum absolute correlation
    best_idx = np.argmax(np.abs(correlation))
    best_lag = int(lags[best_idx])
    best_corr = float(correlation[best_idx])

    return best_lag, best_corr


# =============================================================================
# Confirmation Logic
# =============================================================================


def check_confirmation(
    ag_turn: dict, pd_turns: list[dict], window_bars: int = 6
) -> tuple[bool, int | None]:
    """
    Check if silver turn is confirmed by palladium.

    Args:
        ag_turn: Silver turning point
        pd_turns: List of palladium turning points
        window_bars: Confirmation window

    Returns:
        Tuple of (is_confirmed, confirmation_lag)
        Positive lag means palladium moved first
    """
    ag_idx = ag_turn["idx"]
    ag_type = ag_turn["type"]

    for pd_turn in pd_turns:
        if pd_turn["type"] != ag_type:
            continue

        lag = ag_idx - pd_turn["idx"]  # Positive = palladium first
        if abs(lag) <= window_bars:
            return True, lag

    return False, None


# =============================================================================
# Participation Metrics
# =============================================================================


def check_participation_corr(
    df: pd.DataFrame, turn_idx: int, lookback: int = 10, threshold: float = 0.5
) -> tuple[bool, float]:
    """
    Check participation using return correlation.
    """
    start_idx = max(0, turn_idx - lookback)
    end_idx = min(len(df), turn_idx + lookback)

    ag_ret = df["ag_ret"].iloc[start_idx:end_idx]
    pd_ret = df["pd_ret"].iloc[start_idx:end_idx]

    if len(ag_ret) < 5:
        return False, 0.0

    corr = ag_ret.corr(pd_ret)
    if pd.isna(corr):
        corr = 0.0

    return corr >= threshold, float(corr)


def check_participation_direction(
    df: pd.DataFrame, turn_idx: int, lookback: int = 10, threshold: float = 0.6
) -> tuple[bool, float]:
    """
    Check participation using direction agreement.
    """
    start_idx = max(0, turn_idx - lookback)
    end_idx = min(len(df), turn_idx + lookback)

    ag_ret = df["ag_ret"].iloc[start_idx:end_idx]
    pd_ret = df["pd_ret"].iloc[start_idx:end_idx]

    if len(ag_ret) < 5:
        return False, 0.0

    same_direction = ((ag_ret > 0) & (pd_ret > 0)) | ((ag_ret < 0) & (pd_ret < 0))
    agree_rate = same_direction.sum() / len(ag_ret)

    return agree_rate >= threshold, float(agree_rate)


def check_participation_vol(
    df: pd.DataFrame, turn_idx: int, lookback: int = 10, threshold: float = 0.8
) -> tuple[bool, float]:
    """
    Check participation using volatility expansion.
    """
    start_idx = max(0, turn_idx - lookback)
    end_idx = min(len(df), turn_idx + lookback)

    ag_vol = df["ag_ret"].iloc[start_idx:end_idx].std()
    pd_vol = df["pd_ret"].iloc[start_idx:end_idx].std()

    if ag_vol == 0:
        return False, 0.0

    ratio = pd_vol / ag_vol
    return ratio >= threshold, float(ratio)


def check_participation(
    df: pd.DataFrame,
    turn_idx: int,
    metric: str = "direction_agree",
    threshold: float = 0.6,
    lookback: int = 10,
) -> tuple[bool, float]:
    """
    Check participation using specified metric.
    """
    if metric == "returns_corr":
        return check_participation_corr(df, turn_idx, lookback, threshold)
    elif metric == "direction_agree":
        return check_participation_direction(df, turn_idx, lookback, threshold)
    elif metric == "vol_expansion":
        return check_participation_vol(df, turn_idx, lookback, threshold)
    else:
        return True, 1.0


# =============================================================================
# Failure Detection
# =============================================================================


def check_failed_move_revert(
    df: pd.DataFrame, ag_turn: dict, confirmed: bool, revert_bars: int = 10
) -> bool:
    """
    Check if unconfirmed turn results in reversion.
    """
    if confirmed:
        return False

    turn_idx = ag_turn["idx"]
    turn_price = ag_turn["price"]
    turn_type = ag_turn["type"]

    for i in range(turn_idx + 1, min(len(df), turn_idx + revert_bars + 1)):
        current_price = df["ag_close"].iloc[i]
        if turn_type == "top" and current_price > turn_price:
            return True  # Made new high after top = failed top
        if turn_type == "bottom" and current_price < turn_price:
            return True  # Made new low after bottom = failed bottom

    return False


def check_failed_move(
    df: pd.DataFrame,
    ag_turn: dict,
    confirmed: bool,
    participation_ok: bool,
    rule: str = "no_confirm_then_revert",
    revert_bars: int = 10,
) -> bool:
    """
    Check if turn is a failed move.
    """
    if confirmed and participation_ok:
        return False

    if rule == "no_confirm_then_revert":
        return check_failed_move_revert(df, ag_turn, confirmed, revert_bars)
    elif rule == "no_confirm_then_break_fail":
        # Simplified: same as revert for now
        return check_failed_move_revert(df, ag_turn, confirmed, revert_bars)
    else:
        return False


# =============================================================================
# Main Detection Function
# =============================================================================


def detect_palladium_lead_silver_turns(
    silver_symbol: str = "SI=F",
    palladium_symbol: str = "PA=F",
    timeframe: str = "1h",
    lookback_bars: int = 1000,
    start_date: str | None = None,
    end_date: str | None = None,
    turn_method: str = "pivot",
    pivot_left: int = 3,
    pivot_right: int = 3,
    confirm_window_bars: int = 6,
    lead_lag_max_bars: int = 24,
    participation_metric: str = "direction_agree",
    participation_threshold: float = 0.6,
    failure_rule: str = "no_confirm_then_revert",
    revert_bars: int = 10,
    include_timeseries: bool = False,
) -> dict[str, Any]:
    """
    Detect palladium-lead-silver turning points.

    Args:
        silver_symbol: Silver symbol
        palladium_symbol: Palladium symbol
        timeframe: Analysis timeframe
        lookback_bars: Number of bars to analyze
        start_date: Start date (optional)
        end_date: End date (optional)
        turn_method: Turning point detection method
        pivot_left: Pivot left bars
        pivot_right: Pivot right bars
        confirm_window_bars: Cross-metal confirmation window
        lead_lag_max_bars: Max lag for lead-lag estimation
        participation_metric: Participation metric type
        participation_threshold: Participation threshold
        failure_rule: Failure move detection rule
        revert_bars: Bars to check for reversion
        include_timeseries: Include time series in output

    Returns:
        Detection results dictionary
    """
    # Fetch data
    ag_df = fetch_data(silver_symbol, start_date, end_date, timeframe)
    pd_df = fetch_data(palladium_symbol, start_date, end_date, timeframe)

    # Limit to lookback_bars
    if len(ag_df) > lookback_bars:
        ag_df = ag_df.iloc[-lookback_bars:]
    if len(pd_df) > lookback_bars:
        pd_df = pd_df.iloc[-lookback_bars:]

    # Align data
    df = align_data(ag_df, pd_df)

    # Detect turns
    ag_turns = detect_turns(
        df["ag_close"],
        method=turn_method,
        pivot_left=pivot_left,
        pivot_right=pivot_right,
    )
    pd_turns = detect_turns(
        df["pd_close"],
        method=turn_method,
        pivot_left=pivot_left,
        pivot_right=pivot_right,
    )

    # Estimate lead-lag
    best_lag, best_corr = estimate_lead_lag(
        df["pd_ret"].values, df["ag_ret"].values, lead_lag_max_bars
    )

    # Process each silver turn
    events = []
    confirmed_count = 0
    failed_count = 0

    for ag_turn in ag_turns:
        # Check confirmation
        confirmed, conf_lag = check_confirmation(ag_turn, pd_turns, confirm_window_bars)
        if confirmed:
            confirmed_count += 1

        # Check participation
        part_ok, part_score = check_participation(
            df, ag_turn["idx"], participation_metric, participation_threshold
        )

        # Check failure
        failed = check_failed_move(
            df, ag_turn, confirmed, part_ok, failure_rule, revert_bars
        )
        if failed:
            failed_count += 1

        # Find matching palladium turn if confirmed
        pd_turn_ts = None
        pd_turn_price = None
        if confirmed:
            for pt in pd_turns:
                if pt["type"] == ag_turn["type"]:
                    lag = ag_turn["idx"] - pt["idx"]
                    if abs(lag) <= confirm_window_bars:
                        pd_turn_ts = pt["ts"].isoformat() if hasattr(pt["ts"], "isoformat") else str(pt["ts"])
                        pd_turn_price = pt["price"]
                        break

        events.append(
            {
                "ts": ag_turn["ts"].isoformat() if hasattr(ag_turn["ts"], "isoformat") else str(ag_turn["ts"]),
                "idx": ag_turn["idx"],
                "turn": ag_turn["type"],
                "ag_price": ag_turn["price"],
                "confirmed": confirmed,
                "confirmation_lag_bars": conf_lag,
                "pd_turn_ts": pd_turn_ts,
                "pd_turn_price": pd_turn_price,
                "participation_ok": part_ok,
                "participation_score": round(part_score, 3),
                "failed_move": failed,
            }
        )

    # Calculate statistics
    total_turns = len(ag_turns)
    unconfirmed_count = total_turns - confirmed_count
    unconfirmed_failed = sum(
        1 for e in events if not e["confirmed"] and e["failed_move"]
    )
    confirmed_failed = sum(1 for e in events if e["confirmed"] and e["failed_move"])

    confirmation_rate = confirmed_count / total_turns if total_turns > 0 else 0
    unconfirmed_failure_rate = (
        unconfirmed_failed / unconfirmed_count if unconfirmed_count > 0 else 0
    )
    confirmed_failure_rate = (
        confirmed_failed / confirmed_count if confirmed_count > 0 else 0
    )

    # Build result
    result = {
        "skill": "detect-palladium-lead-silver-turns",
        "symbol_pair": {"silver": silver_symbol, "palladium": palladium_symbol},
        "as_of": df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], "strftime") else str(df.index[-1]),
        "timeframe": timeframe,
        "lookback_bars": len(df),
        "data_range": {
            "start": df.index[0].strftime("%Y-%m-%d") if hasattr(df.index[0], "strftime") else str(df.index[0]),
            "end": df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], "strftime") else str(df.index[-1]),
            "trading_bars": len(df),
        },
        "summary": {
            "estimated_pd_leads_by_bars": best_lag,
            "lead_lag_corr": round(best_corr, 3),
            "confirmation_rate": round(confirmation_rate, 3),
            "unconfirmed_failure_rate": round(unconfirmed_failure_rate, 3),
            "total_ag_turns": total_turns,
            "confirmed_turns": confirmed_count,
            "unconfirmed_turns": unconfirmed_count,
            "failed_moves": failed_count,
        },
        "events": events,
        "latest_event": events[-1] if events else None,
        "interpretation": get_interpretation(
            best_lag, best_corr, confirmation_rate, unconfirmed_failure_rate, events
        ),
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "parameters": {
                "turn_method": turn_method,
                "pivot_left": pivot_left,
                "pivot_right": pivot_right,
                "confirm_window_bars": confirm_window_bars,
                "lead_lag_max_bars": lead_lag_max_bars,
                "participation_metric": participation_metric,
                "participation_threshold": participation_threshold,
                "failure_rule": failure_rule,
            },
            "version": "0.1.0",
        },
    }

    if include_timeseries:
        result["timeseries"] = {
            "ag_close": df["ag_close"].tolist(),
            "pd_close": df["pd_close"].tolist(),
            "timestamps": [
                t.isoformat() if hasattr(t, "isoformat") else str(t) for t in df.index
            ],
        }

    return result


def get_interpretation(
    best_lag: int,
    best_corr: float,
    confirmation_rate: float,
    unconfirmed_failure_rate: float,
    events: list[dict],
) -> dict[str, Any]:
    """
    Generate interpretation based on analysis results.
    """
    # Lead-lag interpretation
    if best_lag > 0:
        lag_meaning = f"鈀金平均領先白銀 {best_lag} 根 K 棒"
    elif best_lag < 0:
        lag_meaning = f"白銀平均領先鈀金 {abs(best_lag)} 根 K 棒"
    else:
        lag_meaning = "鈀金與白銀同步移動"

    # Correlation interpretation
    if abs(best_corr) >= 0.5:
        corr_desc = "強相關"
    elif abs(best_corr) >= 0.3:
        corr_desc = "中等相關"
    else:
        corr_desc = "弱相關"

    # Confirmation effectiveness
    if unconfirmed_failure_rate > 0.5 and confirmation_rate > 0.5:
        effectiveness = "跨金屬確認邏輯有效"
    else:
        effectiveness = "跨金屬確認邏輯效果有限"

    # Latest event status
    latest_status = ""
    if events:
        latest = events[-1]
        if latest["confirmed"] and latest["participation_ok"]:
            latest_status = "最新白銀拐點已被鈀金確認，且參與度良好。"
        elif latest["confirmed"]:
            latest_status = "最新白銀拐點已被鈀金確認，但參與度不足。"
        elif latest["failed_move"]:
            latest_status = "最新白銀拐點未被確認，已判定為失敗走勢。"
        else:
            latest_status = "最新白銀拐點未被確認，等待後續驗證。"

    # Tactics
    tactics = []
    if events and not events[-1]["confirmed"]:
        tactics.append("避免基於未確認拐點進行方向性交易")
        tactics.append("等待下一個被鈀金確認的拐點再決策")
    if events and events[-1]["failed_move"]:
        tactics.append("當前拐點可能為流動性噪音，謹慎應對")
    if confirmation_rate > 0.6:
        tactics.append("歷史確認率良好，可繼續使用鈀金確認作為過濾條件")
    if unconfirmed_failure_rate > 0.5:
        tactics.append("未確認事件失敗率高，建議將確認作為交易前置條件")

    return {
        "regime_assessment": f"{lag_meaning}。{corr_desc}（{best_corr:.2f}）。{effectiveness}。",
        "current_status": latest_status,
        "tactics": tactics if tactics else ["持續監控跨金屬關係"],
    }


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Detect Palladium-Lead-Silver Turning Points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick check
  python palladium_lead_silver.py --quick

  # Custom symbols and parameters
  python palladium_lead_silver.py --silver SI=F --palladium PA=F --timeframe 1h --lookback 1000

  # Output to file
  python palladium_lead_silver.py --silver SI=F --palladium PA=F --output result.json
        """,
    )

    parser.add_argument("--silver", type=str, default="SI=F", help="Silver symbol")
    parser.add_argument("--palladium", type=str, default="PA=F", help="Palladium symbol")
    parser.add_argument("--timeframe", type=str, default="1h", help="Timeframe (1h, 4h, 1d)")
    parser.add_argument("--lookback", type=int, default=1000, help="Lookback bars")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--turn-method",
        type=str,
        default="pivot",
        choices=["pivot", "peaks", "slope_change"],
        help="Turn detection method",
    )
    parser.add_argument("--pivot-left", type=int, default=3, help="Pivot left bars")
    parser.add_argument("--pivot-right", type=int, default=3, help="Pivot right bars")
    parser.add_argument("--confirm-window", type=int, default=6, help="Confirmation window")
    parser.add_argument("--lead-lag-max", type=int, default=24, help="Max lead-lag")
    parser.add_argument(
        "--participation",
        type=str,
        default="direction_agree",
        choices=["returns_corr", "direction_agree", "vol_expansion"],
        help="Participation metric",
    )
    parser.add_argument(
        "--participation-threshold", type=float, default=0.6, help="Participation threshold"
    )
    parser.add_argument(
        "--failure-rule",
        type=str,
        default="no_confirm_then_revert",
        choices=["no_confirm_then_revert", "no_confirm_then_break_fail"],
        help="Failure rule",
    )
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--quick", action="store_true", help="Quick mode with defaults")
    parser.add_argument(
        "--include-timeseries", action="store_true", help="Include time series data"
    )
    parser.add_argument("--backtest", action="store_true", help="Backtest mode")
    parser.add_argument("--monitor", action="store_true", help="Monitor mode")
    parser.add_argument("--interval", type=int, default=60, help="Monitor interval (minutes)")

    args = parser.parse_args()

    try:
        result = detect_palladium_lead_silver_turns(
            silver_symbol=args.silver,
            palladium_symbol=args.palladium,
            timeframe=args.timeframe,
            lookback_bars=args.lookback,
            start_date=args.start,
            end_date=args.end,
            turn_method=args.turn_method,
            pivot_left=args.pivot_left,
            pivot_right=args.pivot_right,
            confirm_window_bars=args.confirm_window,
            lead_lag_max_bars=args.lead_lag_max,
            participation_metric=args.participation,
            participation_threshold=args.participation_threshold,
            failure_rule=args.failure_rule,
            include_timeseries=args.include_timeseries,
        )

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
