#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium ETF Beta Computation

計算 ETF 對鋰價因子的滾動 Beta
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BetaResult:
    """Beta 計算結果"""
    beta_li: float
    beta_li_confidence: float
    beta_ev: Optional[float]
    transmission_status: str
    signals: List[str]
    asof_date: str


@dataclass
class HoldingsAnalysis:
    """持股分析結果"""
    upstream_weight: float
    midstream_weight: float
    downstream_weight: float
    top_holdings: List[Dict[str, Any]]
    concentration_risk: str


# ============================================================================
# Beta 計算
# ============================================================================

def compute_rolling_beta(
    y_returns: List[float],
    x_returns: List[float],
    window: int = 52
) -> Optional[float]:
    """
    計算滾動 Beta

    Beta = Cov(Y, X) / Var(X)

    Args:
        y_returns: ETF 報酬序列
        x_returns: 因子報酬序列
        window: 滾動視窗

    Returns:
        Beta 值
    """
    if len(y_returns) < window or len(x_returns) < window:
        return None

    y = y_returns[-window:]
    x = x_returns[-window:]

    n = len(y)
    mean_y = sum(y) / n
    mean_x = sum(x) / n

    # 計算 Cov(Y, X)
    cov = sum((y[i] - mean_y) * (x[i] - mean_x) for i in range(n)) / (n - 1)

    # 計算 Var(X)
    var_x = sum((x[i] - mean_x) ** 2 for i in range(n)) / (n - 1)

    if var_x == 0:
        return None

    return cov / var_x


def compute_beta_confidence(
    y_returns: List[float],
    x_returns: List[float],
    beta: float,
    window: int = 52
) -> float:
    """
    計算 Beta 的 R² 作為置信度

    Args:
        y_returns: ETF 報酬序列
        x_returns: 因子報酬序列
        beta: 計算得到的 Beta
        window: 視窗大小

    Returns:
        R² 值（0-1）
    """
    if len(y_returns) < window or len(x_returns) < window:
        return 0

    y = y_returns[-window:]
    x = x_returns[-window:]

    n = len(y)
    mean_y = sum(y) / n
    mean_x = sum(x) / n

    # 計算 alpha (intercept)
    alpha = mean_y - beta * mean_x

    # 計算預測值
    y_pred = [alpha + beta * x[i] for i in range(n)]

    # 計算 SS_res 和 SS_tot
    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

    if ss_tot == 0:
        return 0

    r_squared = 1 - (ss_res / ss_tot)
    return max(0, r_squared)


def classify_transmission(
    beta: float,
    threshold: float = 0.3,
    historical_betas: Optional[List[float]] = None,
    duration_weeks: int = 8
) -> Tuple[str, List[str]]:
    """
    判斷傳導狀態

    Args:
        beta: 當前 Beta
        threshold: 弱傳導閾值
        historical_betas: 歷史 Beta 序列
        duration_weeks: 斷裂持續週數

    Returns:
        status: strong | weak | broken
        signals: 判斷信號列表
    """
    signals = []

    # 當前強度判斷
    if beta >= 0.7:
        current_strength = "strong"
        signals.append(f"當前 Beta ({beta:.2f}) 處於強傳導區間")
    elif beta >= threshold:
        current_strength = "moderate"
        signals.append(f"當前 Beta ({beta:.2f}) 處於中等傳導區間")
    else:
        current_strength = "weak"
        signals.append(f"當前 Beta ({beta:.2f}) 低於閾值 ({threshold})")

    # 檢查持續性
    if historical_betas and len(historical_betas) >= duration_weeks:
        recent = historical_betas[-duration_weeks:]
        weak_count = sum(1 for b in recent if b < threshold)

        if weak_count >= duration_weeks * 0.8:
            signals.append(f"近 {duration_weeks} 週有 {weak_count} 週低於閾值，傳導斷裂")
            return "broken", signals
        elif weak_count >= duration_weeks * 0.5:
            signals.append(f"近 {duration_weeks} 週有 {weak_count} 週低於閾值，傳導減弱")

    if current_strength == "strong":
        return "strong", signals
    elif current_strength == "moderate":
        return "moderate", signals
    else:
        return "weak", signals


# ============================================================================
# 持股分析
# ============================================================================

# 產業鏈分類規則
SEGMENT_MAPPING = {
    # 上游 - 礦業
    "ALB": "upstream",
    "SQM": "upstream",
    "LTHM": "upstream",
    "LAC": "upstream",
    "PLL": "upstream",
    "002460": "upstream",  # 贛鋒鋰業
    "002466": "upstream",  # 天齊鋰業
    "1772.HK": "upstream",  # 贛鋒鋰業-H
    "IGO.AX": "upstream",
    "PLS.AX": "upstream",
    "MIN.AX": "upstream",

    # 中游 - 精煉/化工
    "002812": "midstream",  # 恩捷股份
    "300014": "midstream",  # 億緯鋰能

    # 下游 - 電池/整車
    "TSLA": "downstream",
    "LI": "downstream",
    "NIO": "downstream",
    "XPEV": "downstream",
    "RIVN": "downstream",
    "300750": "downstream",  # 寧德時代
    "002594": "downstream",  # 比亞迪
    "051910.KS": "downstream",  # LG 化學
    "006400.KS": "downstream",  # 三星 SDI
    "6752.T": "downstream",  # Panasonic
}


def classify_holding_segment(ticker: str, name: str = "") -> str:
    """
    分類持股的產業鏈段

    Args:
        ticker: 股票代碼
        name: 股票名稱

    Returns:
        segment: upstream | midstream | downstream | unknown
    """
    # 直接查表
    ticker_upper = ticker.upper()
    if ticker_upper in SEGMENT_MAPPING:
        return SEGMENT_MAPPING[ticker_upper]

    # 根據名稱關鍵字判斷
    name_lower = name.lower()

    upstream_keywords = ["lithium", "mining", "resources", "mineral", "鋰", "礦"]
    midstream_keywords = ["chemical", "refin", "material", "化工", "精煉"]
    downstream_keywords = ["battery", "ev", "motor", "auto", "電池", "汽車", "能源"]

    for kw in upstream_keywords:
        if kw in name_lower:
            return "upstream"

    for kw in downstream_keywords:
        if kw in name_lower:
            return "downstream"

    for kw in midstream_keywords:
        if kw in name_lower:
            return "midstream"

    return "unknown"


def analyze_holdings(holdings: List[Dict[str, Any]]) -> HoldingsAnalysis:
    """
    分析 ETF 持股結構

    Args:
        holdings: 持股列表，每個包含 ticker, name, weight

    Returns:
        HoldingsAnalysis 結果
    """
    segment_weights = {
        "upstream": 0,
        "midstream": 0,
        "downstream": 0,
        "unknown": 0
    }

    for holding in holdings:
        ticker = holding.get("ticker", "")
        name = holding.get("name", "")
        weight = holding.get("weight", 0)

        segment = classify_holding_segment(ticker, name)
        segment_weights[segment] += weight

    # 計算集中度風險
    top_weights = sorted([h.get("weight", 0) for h in holdings], reverse=True)
    top_10_weight = sum(top_weights[:10]) if len(top_weights) >= 10 else sum(top_weights)

    if top_10_weight > 60:
        concentration_risk = "high"
    elif top_10_weight > 40:
        concentration_risk = "moderate"
    else:
        concentration_risk = "low"

    # 取 top 5 holdings
    sorted_holdings = sorted(holdings, key=lambda x: x.get("weight", 0), reverse=True)
    top_holdings = sorted_holdings[:5]

    return HoldingsAnalysis(
        upstream_weight=segment_weights["upstream"],
        midstream_weight=segment_weights["midstream"],
        downstream_weight=segment_weights["downstream"],
        top_holdings=top_holdings,
        concentration_risk=concentration_risk
    )


# ============================================================================
# 完整 ETF 分析
# ============================================================================

def compute_etf_exposure(
    etf_returns: List[float],
    li_price_returns: List[float],
    ev_demand_returns: Optional[List[float]] = None,
    holdings: Optional[List[Dict[str, Any]]] = None,
    beta_window: int = 52,
    transmission_threshold: float = 0.3
) -> Dict[str, Any]:
    """
    完整 ETF 暴露分析

    Args:
        etf_returns: ETF 報酬序列
        li_price_returns: 鋰價報酬序列
        ev_demand_returns: EV 需求報酬序列（可選）
        holdings: ETF 持股列表
        beta_window: Beta 計算視窗
        transmission_threshold: 傳導閾值

    Returns:
        完整分析結果
    """
    result = {
        "beta_analysis": {},
        "holdings_analysis": None,
        "signals": [],
        "asof_date": date.today().isoformat()
    }

    # Beta 計算
    beta_li = compute_rolling_beta(etf_returns, li_price_returns, beta_window)

    if beta_li is not None:
        confidence = compute_beta_confidence(
            etf_returns, li_price_returns, beta_li, beta_window
        )
        transmission_status, trans_signals = classify_transmission(
            beta_li, transmission_threshold
        )

        result["beta_analysis"]["li_price"] = {
            "beta": round(beta_li, 3),
            "r_squared": round(confidence, 3),
            "transmission_status": transmission_status
        }
        result["signals"].extend(trans_signals)

    # EV 需求因子
    if ev_demand_returns:
        beta_ev = compute_rolling_beta(etf_returns, ev_demand_returns, beta_window)
        if beta_ev is not None:
            ev_confidence = compute_beta_confidence(
                etf_returns, ev_demand_returns, beta_ev, beta_window
            )
            result["beta_analysis"]["ev_demand"] = {
                "beta": round(beta_ev, 3),
                "r_squared": round(ev_confidence, 3)
            }

    # 持股分析
    if holdings:
        holdings_result = analyze_holdings(holdings)
        result["holdings_analysis"] = {
            "segment_weights": {
                "upstream": round(holdings_result.upstream_weight, 1),
                "midstream": round(holdings_result.midstream_weight, 1),
                "downstream": round(holdings_result.downstream_weight, 1)
            },
            "concentration_risk": holdings_result.concentration_risk,
            "top_holdings": holdings_result.top_holdings
        }

        # 生成持股信號
        if holdings_result.upstream_weight > 40:
            result["signals"].append(
                f"上游礦業權重 ({holdings_result.upstream_weight:.1f}%) 較高，對鋰價敏感"
            )
        if holdings_result.downstream_weight > 50:
            result["signals"].append(
                f"下游電池/整車權重 ({holdings_result.downstream_weight:.1f}%) 較高，對 EV 銷量更敏感"
            )

    return result


# ============================================================================
# 輸出格式化
# ============================================================================

def format_etf_output(result: Dict[str, Any], ticker: str = "LIT") -> Dict[str, Any]:
    """格式化輸出"""
    output = {
        "etf_ticker": ticker,
        **result
    }

    # 添加投資解讀
    if "beta_analysis" in result and "li_price" in result["beta_analysis"]:
        beta_info = result["beta_analysis"]["li_price"]
        output["interpretation"] = _interpret_etf_beta(
            beta_info.get("beta"),
            beta_info.get("transmission_status")
        )

    return output


def _interpret_etf_beta(beta: Optional[float], status: Optional[str]) -> str:
    """ETF Beta 投資解讀"""
    if beta is None:
        return "Beta 數據不足，無法判斷"

    if status == "broken":
        return "ETF 與鋰價傳導已斷裂，ETF 走勢可能由其他因素主導（如整體市場情緒）"
    elif status == "weak":
        return "ETF 與鋰價傳導較弱，做多鋰價時 ETF 可能無法完全捕捉漲幅"
    elif status == "strong":
        return "ETF 與鋰價強傳導，可用 ETF 作為鋰價多頭工具"
    else:
        return "ETF 與鋰價傳導中等，需結合持股結構判斷"


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json
    import random

    parser = argparse.ArgumentParser(description="Lithium ETF Beta Computation")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    parser.add_argument("--ticker", type=str, default="LIT", help="ETF ticker")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.demo:
        # Demo 數據
        n_weeks = 60

        # 模擬相關的報酬序列
        li_returns = [random.gauss(0, 3) for _ in range(n_weeks)]
        etf_returns = [0.7 * li_returns[i] + random.gauss(0, 1.5) for i in range(n_weeks)]
        ev_returns = [random.gauss(0.5, 2) for _ in range(n_weeks)]

        # 模擬持股
        holdings = [
            {"ticker": "ALB", "name": "Albemarle Corp", "weight": 8.2},
            {"ticker": "TSLA", "name": "Tesla Inc", "weight": 7.5},
            {"ticker": "SQM", "name": "SQM", "weight": 6.8},
            {"ticker": "LTHM", "name": "Livent Corp", "weight": 5.2},
            {"ticker": "002460", "name": "贛鋒鋰業", "weight": 4.9},
            {"ticker": "300750", "name": "寧德時代", "weight": 4.5},
            {"ticker": "LAC", "name": "Lithium Americas", "weight": 3.8},
            {"ticker": "PLL", "name": "Piedmont Lithium", "weight": 3.2},
            {"ticker": "NIO", "name": "NIO Inc", "weight": 2.9},
            {"ticker": "LI", "name": "Li Auto", "weight": 2.5},
        ]

        result = compute_etf_exposure(
            etf_returns=etf_returns,
            li_price_returns=li_returns,
            ev_demand_returns=ev_returns,
            holdings=holdings
        )

        output = format_etf_output(result, args.ticker)
        print(json.dumps(output, indent=2, ensure_ascii=False))

    else:
        print("Use --demo to run with demo data")
        print("For production use, import and call compute_etf_exposure() directly")
