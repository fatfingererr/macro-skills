#!/usr/bin/env python3
"""
Zeberg-Salomon Rotator - Main Script
實作 Zeberg-Salomon 兩態景氣輪動策略
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from fetch_data import fetch_all_data


# ============================================================================
# 數據轉換函數
# ============================================================================


def transform_series(
    series: pd.Series,
    transform: str,
) -> pd.Series:
    """
    對序列進行轉換

    Args:
        series: 原始序列
        transform: 轉換類型 (level|yoy|mom|diff|logdiff)

    Returns:
        轉換後的序列
    """
    if transform == "level":
        return series
    elif transform == "yoy":
        return series.pct_change(periods=12)
    elif transform == "mom":
        return series.pct_change(periods=1)
    elif transform == "diff":
        return series.diff()
    elif transform == "logdiff":
        return np.log(series).diff()
    else:
        raise ValueError(f"Unknown transform: {transform}")


def rolling_zscore(
    series: pd.Series,
    window: int,
) -> pd.Series:
    """
    計算滾動 z-score

    Args:
        series: 輸入序列
        window: 滾動視窗

    Returns:
        z-score 序列
    """
    mean = series.rolling(window=window, min_periods=window // 2).mean()
    std = series.rolling(window=window, min_periods=window // 2).std()
    return (series - mean) / std


def ema(
    series: pd.Series,
    span: int,
) -> pd.Series:
    """
    計算指數移動平均

    Args:
        series: 輸入序列
        span: EMA span

    Returns:
        EMA 序列
    """
    return series.ewm(span=span, adjust=False).mean()


# ============================================================================
# 指標建構
# ============================================================================


def build_index(
    series_defs: List[Dict],
    data: pd.DataFrame,
    z_win: int = 120,
    smooth_win: int = 3,
) -> pd.Series:
    """
    建構合成指標

    Args:
        series_defs: 序列定義列表
        data: 數據框
        z_win: z-score 視窗
        smooth_win: 平滑視窗

    Returns:
        合成指標序列
    """
    z_list = []

    for sdef in series_defs:
        series_id = sdef["id"]
        if series_id not in data.columns:
            print(f"Warning: {series_id} not found in data", file=sys.stderr)
            continue

        x = data[series_id].copy()
        x = transform_series(x, sdef.get("transform", "level"))
        x = sdef.get("direction", 1) * x
        z = rolling_zscore(x, z_win)
        z = ema(z, smooth_win)
        z_list.append(sdef.get("weight", 1.0) * z)

    if not z_list:
        return pd.Series(dtype=float)

    result = sum(z_list)
    result.name = "Index"
    return result


def build_index_with_attribution(
    series_defs: List[Dict],
    data: pd.DataFrame,
    z_win: int = 120,
    smooth_win: int = 3,
) -> Tuple[pd.Series, Dict]:
    """
    建構合成指標並返回各成分貢獻

    Args:
        series_defs: 序列定義列表
        data: 數據框
        z_win: z-score 視窗
        smooth_win: 平滑視窗

    Returns:
        (合成指標序列, 成分貢獻字典)
    """
    z_dict = {}
    contrib_dict = {}

    for sdef in series_defs:
        series_id = sdef["id"]
        if series_id not in data.columns:
            continue

        x = data[series_id].copy()
        x = transform_series(x, sdef.get("transform", "level"))
        x = sdef.get("direction", 1) * x
        z = rolling_zscore(x, z_win)
        z = ema(z, smooth_win)

        weight = sdef.get("weight", 1.0)
        z_dict[series_id] = weight * z

        # 最新值的貢獻
        if not z.empty:
            contrib_dict[series_id] = {
                "value": float(x.iloc[-1]) if not pd.isna(x.iloc[-1]) else None,
                "z_score": float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else None,
                "weight": weight,
                "contribution": float(weight * z.iloc[-1])
                if not pd.isna(z.iloc[-1])
                else None,
            }

    if not z_dict:
        return pd.Series(dtype=float), {}

    result = sum(z_dict.values())
    result.name = "Index"
    return result, contrib_dict


# ============================================================================
# 切換邏輯
# ============================================================================


def protocol_signals(
    params: Dict,
    price_eq: pd.Series,
    price_bd: pd.Series,
    leading_index: pd.Series,
    coincident_index: pd.Series,
    euphoria_filter: Optional[pd.Series] = None,
    doubt_filter: Optional[pd.Series] = None,
) -> Dict:
    """
    執行兩態切換協議

    Args:
        params: 參數配置
        price_eq: 股票價格序列
        price_bd: 債券價格序列
        leading_index: 領先指標序列
        coincident_index: 同時指標序列
        euphoria_filter: 亢奮濾鏡序列
        doubt_filter: 懷疑濾鏡序列

    Returns:
        包含訊號和回測結果的字典
    """
    # 提取參數
    iceberg_threshold = params.get("iceberg_threshold", -0.3)
    sinking_threshold = params.get("sinking_threshold", -0.5)
    confirm_periods = params.get("confirm_periods", 2)
    hysteresis = params.get("hysteresis", 0.15)

    # 對齊索引
    common_idx = leading_index.index.intersection(coincident_index.index)
    L = leading_index.loc[common_idx]
    C = coincident_index.loc[common_idx]

    # 計算變化
    dL = L.diff()
    dC = C.diff()

    # 事件判定
    iceberg = L < iceberg_threshold
    sinking = C < sinking_threshold

    # 濾鏡（預設為 True）
    if euphoria_filter is not None:
        eup = euphoria_filter.reindex(common_idx, fill_value=True)
    else:
        eup = pd.Series(True, index=common_idx)

    if doubt_filter is not None:
        doubt = doubt_filter.reindex(common_idx, fill_value=True)
    else:
        doubt = pd.Series(True, index=common_idx)

    # 狀態機
    state = "RISK_ON"
    signals = []
    ice_cnt = 0
    rec_cnt = 0

    for t in common_idx:
        dl = dL.loc[t] if not pd.isna(dL.loc[t]) else 0
        dc = dC.loc[t] if not pd.isna(dC.loc[t]) else 0

        if state == "RISK_ON":
            # 檢查 Risk-Off 條件
            cond_off = (
                iceberg.loc[t]
                and (dl < 0)
                and (eup.loc[t] if not pd.isna(eup.loc[t]) else True)
            )
            ice_cnt = ice_cnt + 1 if cond_off else 0

            if ice_cnt >= confirm_periods:
                signals.append(
                    {
                        "date": str(t.date()),
                        "action": "EXIT_EQUITY_ENTER_LONG_BOND",
                        "from_state": "RISK_ON",
                        "to_state": "RISK_OFF",
                        "reason": {
                            "LeadingIndex": float(L.loc[t]),
                            "CoincidentIndex": float(C.loc[t]),
                            "iceberg": True,
                            "sinking": bool(sinking.loc[t]),
                            "euphoria": bool(eup.loc[t]) if not pd.isna(eup.loc[t]) else True,
                            "dL": float(dl),
                            "confirm_periods_met": confirm_periods,
                        },
                    }
                )
                state = "RISK_OFF"
                ice_cnt = 0

        else:  # RISK_OFF
            # 檢查 Risk-On 條件
            cond_on = (
                (L.loc[t] > iceberg_threshold + hysteresis)
                and (dl > 0)
                and (doubt.loc[t] if not pd.isna(doubt.loc[t]) else True)
            )
            rec_cnt = rec_cnt + 1 if cond_on else 0

            if rec_cnt >= confirm_periods:
                signals.append(
                    {
                        "date": str(t.date()),
                        "action": "EXIT_LONG_BOND_ENTER_EQUITY",
                        "from_state": "RISK_OFF",
                        "to_state": "RISK_ON",
                        "reason": {
                            "LeadingIndex": float(L.loc[t]),
                            "CoincidentIndex": float(C.loc[t]),
                            "recovery": True,
                            "hysteresis_cleared": True,
                            "dL": float(dl),
                            "dC": float(dc),
                            "confirm_periods_met": confirm_periods,
                        },
                    }
                )
                state = "RISK_ON"
                rec_cnt = 0

    # 回測
    backtest = backtest_two_asset(
        price_eq=price_eq,
        price_bd=price_bd,
        signals=signals,
        rebalance_on=params.get("rebalance_on", "next_month_open"),
        cost_bps=params.get("transaction_cost_bps", 5),
        slippage_bps=params.get("slippage_bps", 0),
    )

    return {
        "signals": signals,
        "leading_index": L,
        "coincident_index": C,
        "iceberg": iceberg,
        "sinking": sinking,
        "final_state": state,
        "backtest": backtest,
    }


# ============================================================================
# 回測函數
# ============================================================================


def backtest_two_asset(
    price_eq: pd.Series,
    price_bd: pd.Series,
    signals: List[Dict],
    rebalance_on: str = "next_month_open",
    cost_bps: float = 5,
    slippage_bps: float = 0,
) -> Dict:
    """
    執行兩態資產回測

    Args:
        price_eq: 股票價格序列
        price_bd: 債券價格序列
        signals: 切換訊號列表
        rebalance_on: 執行時點
        cost_bps: 交易成本（bps）
        slippage_bps: 滑價（bps）

    Returns:
        回測結果字典
    """
    if price_eq.empty or price_bd.empty:
        return {"error": "Price data is empty"}

    # 對齊價格
    common_idx = price_eq.index.intersection(price_bd.index)
    eq = price_eq.loc[common_idx]
    bd = price_bd.loc[common_idx]

    # 計算報酬
    eq_ret = eq.pct_change().fillna(0)
    bd_ret = bd.pct_change().fillna(0)

    # 建立切換時點
    switch_dates = {s["date"]: s["to_state"] for s in signals}

    # 初始狀態
    state = "RISK_ON"
    portfolio_ret = []
    states = []
    total_costs = 0

    for t in common_idx:
        date_str = str(t.date())

        # 檢查是否有切換
        if date_str in switch_dates:
            state = switch_dates[date_str]
            total_costs += (cost_bps + slippage_bps) / 10000

        # 根據狀態決定報酬
        if state == "RISK_ON":
            portfolio_ret.append(eq_ret.loc[t])
        else:
            portfolio_ret.append(bd_ret.loc[t])

        states.append(state)

    # 計算累積報酬
    portfolio_ret = pd.Series(portfolio_ret, index=common_idx)
    cumulative = (1 + portfolio_ret).cumprod()

    # 扣除交易成本
    cumulative_after_cost = cumulative * (1 - total_costs)

    # 計算績效指標
    total_return = cumulative_after_cost.iloc[-1] - 1
    years = len(common_idx) / 12
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Max Drawdown
    rolling_max = cumulative_after_cost.cummax()
    drawdown = (cumulative_after_cost - rolling_max) / rolling_max
    max_dd = drawdown.min()
    max_dd_date = str(drawdown.idxmin().date()) if not pd.isna(drawdown.idxmin()) else None

    # 年化波動率與 Sharpe
    annual_vol = portfolio_ret.std() * np.sqrt(12)
    sharpe = cagr / annual_vol if annual_vol > 0 else 0

    # 統計持有期
    states_series = pd.Series(states, index=common_idx)
    periods_in_equity = (states_series == "RISK_ON").sum()
    periods_in_bonds = (states_series == "RISK_OFF").sum()

    return {
        "period": {
            "start": str(common_idx[0].date()),
            "end": str(common_idx[-1].date()),
            "total_months": len(common_idx),
        },
        "performance": {
            "cumulative_return": float(total_return),
            "cagr": float(cagr),
            "annualized_volatility": float(annual_vol),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_dd),
            "max_drawdown_date": max_dd_date,
            "calmar_ratio": float(cagr / abs(max_dd)) if max_dd != 0 else 0,
        },
        "turnover": {
            "total_switches": len(signals),
            "avg_months_per_state": len(common_idx) / max(len(signals), 1),
            "periods_in_equity": int(periods_in_equity),
            "periods_in_bonds": int(periods_in_bonds),
        },
        "costs": {
            "total_transaction_costs_bps": len(signals) * cost_bps,
            "total_slippage_bps": len(signals) * slippage_bps,
            "net_impact": float(total_costs),
        },
        "cumulative_series": {str(k.date()): v for k, v in cumulative_after_cost.to_dict().items()},
    }


def calculate_benchmark(
    price: pd.Series,
    name: str,
) -> Dict:
    """計算 benchmark 績效"""
    if price.empty:
        return {"error": f"{name} price data is empty"}

    ret = price.pct_change().fillna(0)
    cumulative = (1 + ret).cumprod()

    total_return = cumulative.iloc[-1] - 1
    years = len(price) / 12
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_dd = drawdown.min()

    annual_vol = ret.std() * np.sqrt(12)
    sharpe = cagr / annual_vol if annual_vol > 0 else 0

    return {
        "cumulative_return": float(total_return),
        "cagr": float(cagr),
        "max_drawdown": float(max_dd),
        "sharpe_ratio": float(sharpe),
    }


# ============================================================================
# 主入口
# ============================================================================


def get_current_state(
    data: Dict,
    params: Dict,
) -> Dict:
    """獲取當前狀態（快速模式）"""
    leading_config = params.get(
        "leading_series",
        [
            {"id": "T10Y3M", "transform": "level", "direction": 1, "weight": 0.25},
            {"id": "T10Y2Y", "transform": "level", "direction": 1, "weight": 0.15},
            {"id": "PERMIT", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "ACDGNO", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "UMCSENT", "transform": "level", "direction": 1, "weight": 0.20},
        ],
    )

    coincident_config = params.get(
        "coincident_series",
        [
            {"id": "PAYEMS", "transform": "yoy", "direction": 1, "weight": 0.30},
            {"id": "INDPRO", "transform": "yoy", "direction": 1, "weight": 0.30},
            {"id": "W875RX1", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "CMRMTSPL", "transform": "yoy", "direction": 1, "weight": 0.20},
        ],
    )

    L, L_contrib = build_index_with_attribution(
        leading_config,
        data["macro"],
        z_win=params.get("standardize_window", 120),
        smooth_win=params.get("smooth_window", 3),
    )

    C, C_contrib = build_index_with_attribution(
        coincident_config,
        data["macro"],
        z_win=params.get("standardize_window", 120),
        smooth_win=params.get("smooth_window", 3),
    )

    iceberg_threshold = params.get("iceberg_threshold", -0.3)
    sinking_threshold = params.get("sinking_threshold", -0.5)

    latest_L = float(L.iloc[-1]) if not L.empty and not pd.isna(L.iloc[-1]) else None
    latest_C = float(C.iloc[-1]) if not C.empty and not pd.isna(C.iloc[-1]) else None

    iceberg_event = latest_L < iceberg_threshold if latest_L is not None else False
    sinking_event = latest_C < sinking_threshold if latest_C is not None else False

    dL = float(L.diff().iloc[-1]) if not L.empty and len(L) > 1 else None
    dC = float(C.diff().iloc[-1]) if not C.empty and len(C) > 1 else None

    return {
        "as_of": str(L.index[-1].date()) if not L.empty else None,
        "LeadingIndex": latest_L,
        "CoincidentIndex": latest_C,
        "dL": dL,
        "dC": dC,
        "iceberg_event": iceberg_event,
        "sinking_event": sinking_event,
        "distance_to_iceberg": latest_L - iceberg_threshold if latest_L is not None else None,
        "distance_to_sinking": latest_C - sinking_threshold if latest_C is not None else None,
        "leading_attribution": L_contrib,
        "coincident_attribution": C_contrib,
    }


def run_full_backtest(
    data: Dict,
    params: Dict,
) -> Dict:
    """執行完整回測"""
    leading_config = params.get(
        "leading_series",
        [
            {"id": "T10Y3M", "transform": "level", "direction": 1, "weight": 0.25},
            {"id": "T10Y2Y", "transform": "level", "direction": 1, "weight": 0.15},
            {"id": "PERMIT", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "ACDGNO", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "UMCSENT", "transform": "level", "direction": 1, "weight": 0.20},
        ],
    )

    coincident_config = params.get(
        "coincident_series",
        [
            {"id": "PAYEMS", "transform": "yoy", "direction": 1, "weight": 0.30},
            {"id": "INDPRO", "transform": "yoy", "direction": 1, "weight": 0.30},
            {"id": "W875RX1", "transform": "yoy", "direction": 1, "weight": 0.20},
            {"id": "CMRMTSPL", "transform": "yoy", "direction": 1, "weight": 0.20},
        ],
    )

    L = build_index(
        leading_config,
        data["macro"],
        z_win=params.get("standardize_window", 120),
        smooth_win=params.get("smooth_window", 3),
    )

    C = build_index(
        coincident_config,
        data["macro"],
        z_win=params.get("standardize_window", 120),
        smooth_win=params.get("smooth_window", 3),
    )

    equity_proxy = params.get("equity_proxy", "SPY")
    bond_proxy = params.get("bond_proxy", "TLT")

    result = protocol_signals(
        params=params,
        price_eq=data["prices"].get(equity_proxy, pd.Series()),
        price_bd=data["prices"].get(bond_proxy, pd.Series()),
        leading_index=L,
        coincident_index=C,
    )

    # 計算 benchmarks
    benchmarks = {}
    if equity_proxy in data["prices"].columns:
        benchmarks["equity_buy_hold"] = calculate_benchmark(
            data["prices"][equity_proxy], "Equity"
        )
    if bond_proxy in data["prices"].columns:
        benchmarks["bond_buy_hold"] = calculate_benchmark(
            data["prices"][bond_proxy], "Bond"
        )

    # 當前狀態
    current_state = get_current_state(data, params)

    return {
        "skill": "zeberg-salomon-rotator",
        "version": "0.1.1",
        "as_of": current_state["as_of"],
        "params_used": params,
        "current_state": {
            "state": result["final_state"],
            "since": result["signals"][-1]["date"] if result["signals"] else None,
        },
        "latest_indices": {
            "LeadingIndex": current_state["LeadingIndex"],
            "CoincidentIndex": current_state["CoincidentIndex"],
            "dL": current_state["dL"],
            "dC": current_state["dC"],
            "iceberg_event": current_state["iceberg_event"],
            "sinking_event": current_state["sinking_event"],
            "distance_to_iceberg": current_state["distance_to_iceberg"],
            "distance_to_sinking": current_state["distance_to_sinking"],
        },
        "switch_events": result["signals"],
        "backtest_summary": result["backtest"],
        "benchmarks": benchmarks,
        "index_series": {
            "leading": {str(k.date()): float(v) for k, v in result["leading_index"].to_dict().items() if not pd.isna(v)},
            "coincident": {str(k.date()): float(v) for k, v in result["coincident_index"].to_dict().items() if not pd.isna(v)},
        },
        "diagnostics": {
            "leading_components": list(current_state["leading_attribution"].values()),
            "coincident_components": list(current_state["coincident_attribution"].values()),
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_freshness": {
                "macro_data": current_state["as_of"],
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Zeberg-Salomon Rotator - Two-State Business Cycle Rotator"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick check: show current state only",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Backtest start date",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Backtest end date",
    )
    parser.add_argument(
        "--equity",
        type=str,
        default="SPY",
        help="Equity proxy ticker",
    )
    parser.add_argument(
        "--bond",
        type=str,
        default="TLT",
        help="Bond proxy ticker",
    )
    parser.add_argument(
        "--iceberg-threshold",
        type=float,
        default=-0.3,
        help="Iceberg event threshold",
    )
    parser.add_argument(
        "--sinking-threshold",
        type=float,
        default=-0.5,
        help="Sinking event threshold",
    )
    parser.add_argument(
        "--confirm-periods",
        type=int,
        default=2,
        help="Confirmation periods",
    )
    parser.add_argument(
        "--hysteresis",
        type=float,
        default=0.15,
        help="Hysteresis gap",
    )
    parser.add_argument(
        "--rebalance",
        type=str,
        default="next_month_open",
        choices=["signal_close", "next_open", "next_month_open"],
        help="Rebalance timing",
    )
    parser.add_argument(
        "--cost-bps",
        type=float,
        default=5,
        help="Transaction cost in bps",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path",
    )

    args = parser.parse_args()

    # 構建參數
    params = {
        "start_date": args.start,
        "end_date": args.end or datetime.now().strftime("%Y-%m-%d"),
        "equity_proxy": args.equity,
        "bond_proxy": args.bond,
        "iceberg_threshold": args.iceberg_threshold,
        "sinking_threshold": args.sinking_threshold,
        "confirm_periods": args.confirm_periods,
        "hysteresis": args.hysteresis,
        "rebalance_on": args.rebalance,
        "transaction_cost_bps": args.cost_bps,
        "standardize_window": 120,
        "smooth_window": 3,
    }

    # 抓取數據
    print("Fetching data...", file=sys.stderr)
    data = fetch_all_data(
        start_date=params["start_date"],
        end_date=params["end_date"],
        price_tickers=[params["equity_proxy"], params["bond_proxy"]],
    )

    if args.quick:
        # 快速模式
        result = get_current_state(data, params)
        output = {
            "skill": "zeberg-salomon-rotator",
            "as_of": result["as_of"],
            "state": "RISK_ON" if not result["iceberg_event"] else "RISK_OFF",
            "latest_indices": {
                "LeadingIndex": result["LeadingIndex"],
                "CoincidentIndex": result["CoincidentIndex"],
                "iceberg_event": result["iceberg_event"],
                "sinking_event": result["sinking_event"],
            },
        }
    else:
        # 完整回測
        print("Running backtest...", file=sys.stderr)
        output = run_full_backtest(data, params)

    # 輸出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Result saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
