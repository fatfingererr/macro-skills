#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
礦業股/金屬價格比率基本面分析器

從價格數據和財報計算四大基本面因子，並執行門檻反推分析。

Usage:
    python fundamental_analyzer.py --quick
    python fundamental_analyzer.py --metal-symbol SI=F --miner-universe etf:SIL
    python fundamental_analyzer.py --backsolve-target 1.7 --event-study
"""

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None
    print("Warning: yfinance not installed. Run: pip install yfinance")


# =============================================================================
# 配置
# =============================================================================

@dataclass
class AnalyzerConfig:
    """分析器配置"""
    metal_symbol: str = "SI=F"
    miner_universe_type: str = "etf_holdings"
    miner_universe_ticker: str = "SIL"
    miner_universe_tickers: list = field(default_factory=list)
    miner_universe_weights: list = field(default_factory=list)

    region_profile: str = "us_sec"
    start_date: str = ""
    end_date: str = ""
    frequency: str = "1wk"

    bottom_quantile: float = 0.20
    top_quantile: float = 0.80

    aisc_method: str = "hybrid"
    leverage_method: str = "net_debt_to_ev"
    multiple_method: str = "ev_to_ebitda"
    dilution_method: str = "weighted_avg_shares"

    cache_enabled: bool = True
    cache_dir: str = "./cache"

    output_format: str = "json"
    output_path: str = ""

    def __post_init__(self):
        if not self.start_date:
            self.start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        if not self.end_date:
            self.end_date = datetime.now().strftime("%Y-%m-%d")


# =============================================================================
# 價格數據
# =============================================================================

def fetch_prices(symbol: str, start: str, end: str, interval: str = "1wk") -> pd.Series:
    """
    取得價格數據

    Parameters
    ----------
    symbol : str
        Yahoo Finance 代碼
    start : str
        起始日期
    end : str
        結束日期
    interval : str
        取樣頻率

    Returns
    -------
    pd.Series
        收盤價序列
    """
    if yf is None:
        raise ImportError("yfinance is required. Install with: pip install yfinance")

    data = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        progress=False
    )

    if data.empty:
        raise ValueError(f"No data returned for {symbol}")

    # Handle MultiIndex columns from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        close = data['Close']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = data['Close']

    return close.dropna()


# =============================================================================
# 模擬財報數據（實際使用時需實現 SEC EDGAR 抓取）
# =============================================================================

# 常見銀礦公司基本面數據（模擬值，實際應從 SEC 抓取）
SIMULATED_FUNDAMENTALS = {
    "PAAS": {
        "name": "Pan American Silver",
        "aisc": 24.5,
        "total_debt": 450,
        "cash": 280,
        "market_cap": 4500,
        "ebitda": 650,
        "shares": 420,
        "shares_base": 400,
    },
    "AG": {
        "name": "First Majestic Silver",
        "aisc": 26.8,
        "total_debt": 180,
        "cash": 95,
        "market_cap": 2200,
        "ebitda": 320,
        "shares": 280,
        "shares_base": 260,
    },
    "HL": {
        "name": "Hecla Mining",
        "aisc": 22.5,
        "total_debt": 520,
        "cash": 180,
        "market_cap": 3800,
        "ebitda": 580,
        "shares": 610,
        "shares_base": 580,
    },
    "CDE": {
        "name": "Coeur Mining",
        "aisc": 28.2,
        "total_debt": 380,
        "cash": 120,
        "market_cap": 1800,
        "ebitda": 280,
        "shares": 340,
        "shares_base": 300,
    },
    "EXK": {
        "name": "Endeavour Silver",
        "aisc": 25.5,
        "total_debt": 85,
        "cash": 45,
        "market_cap": 680,
        "ebitda": 95,
        "shares": 180,
        "shares_base": 165,
    },
    "FSM": {
        "name": "Fortuna Silver",
        "aisc": 23.8,
        "total_debt": 220,
        "cash": 160,
        "market_cap": 2800,
        "ebitda": 420,
        "shares": 310,
        "shares_base": 295,
    },
    "MAG": {
        "name": "MAG Silver",
        "aisc": 18.5,
        "total_debt": 0,
        "cash": 180,
        "market_cap": 1500,
        "ebitda": 180,
        "shares": 98,
        "shares_base": 95,
    },
}

# 模擬 ETF 持股權重
SIMULATED_HOLDINGS = {
    "SIL": {
        "PAAS": 0.125,
        "AG": 0.082,
        "HL": 0.071,
        "CDE": 0.058,
        "EXK": 0.045,
        "FSM": 0.068,
        "MAG": 0.052,
    }
}


def get_fundamentals(ticker: str) -> dict:
    """取得公司基本面數據（模擬）"""
    if ticker in SIMULATED_FUNDAMENTALS:
        return SIMULATED_FUNDAMENTALS[ticker].copy()
    return None


def get_holdings(etf_ticker: str) -> dict:
    """取得 ETF 持股（模擬）"""
    if etf_ticker in SIMULATED_HOLDINGS:
        return SIMULATED_HOLDINGS[etf_ticker].copy()
    return {}


# =============================================================================
# 因子計算
# =============================================================================

def compute_factors(fundamentals: dict, metal_price: float) -> dict:
    """
    計算四大基本面因子

    Parameters
    ----------
    fundamentals : dict
        公司財務數據
    metal_price : float
        金屬價格

    Returns
    -------
    dict
        計算後的因子
    """
    S = metal_price
    aisc = fundamentals.get("aisc", 0)

    # (A) 成本因子
    C = 1 - aisc / S if S > 0 else 0

    # (B) 槓桿因子
    total_debt = fundamentals.get("total_debt", 0)
    cash = fundamentals.get("cash", 0)
    market_cap = fundamentals.get("market_cap", 0)

    net_debt = total_debt - cash
    ev = market_cap + net_debt
    L = net_debt / ev if ev > 0 else 0
    one_minus_L = 1 - L

    # (C) 倍數因子
    ebitda = fundamentals.get("ebitda", 0)
    M = ev / ebitda if ebitda > 0 else 0

    # (D) 稀釋因子
    shares = fundamentals.get("shares", 0)
    shares_base = fundamentals.get("shares_base", shares)
    D = shares_base / shares if shares > 0 else 1

    return {
        "aisc": aisc,
        "C": C,
        "net_debt": net_debt,
        "ev": ev,
        "L": L,
        "one_minus_L": one_minus_L,
        "ebitda": ebitda,
        "M": M,
        "shares": shares,
        "shares_base": shares_base,
        "D": D,
        "shares_yoy": shares / shares_base - 1 if shares_base > 0 else 0,
    }


def weighted_aggregate(factors_list: list, weights: list) -> dict:
    """權重加總因子"""
    agg = {
        "aisc": 0,
        "C": 0,
        "one_minus_L": 0,
        "L": 0,
        "M": 0,
        "D": 0,
        "shares_yoy": 0,
        "net_debt": 0,
        "ev": 0,
        "ebitda": 0,
    }

    total_weight = sum(weights)
    if total_weight == 0:
        return agg

    for factors, w in zip(factors_list, weights):
        norm_w = w / total_weight
        agg["aisc"] += factors["aisc"] * norm_w
        agg["C"] += factors["C"] * norm_w
        agg["one_minus_L"] += factors["one_minus_L"] * norm_w
        agg["L"] += factors["L"] * norm_w
        agg["M"] += factors["M"] * norm_w
        agg["D"] += factors["D"] * norm_w
        agg["shares_yoy"] += factors["shares_yoy"] * norm_w
        agg["net_debt"] += factors["net_debt"] * norm_w
        agg["ev"] += factors["ev"] * norm_w
        agg["ebitda"] += factors["ebitda"] * norm_w

    return agg


# =============================================================================
# 反推分析
# =============================================================================

def backsolve(
    R_now: float,
    R_target: float,
    factors_now: dict,
    metal_price: float
) -> dict:
    """
    反推需要的因子組合

    Parameters
    ----------
    R_now : float
        當前比率
    R_target : float
        目標比率
    factors_now : dict
        當前因子狀態
    metal_price : float
        當前金屬價格

    Returns
    -------
    dict
        反推結果
    """
    ratio_mult = R_target / R_now if R_now > 0 else 0

    M_now = factors_now["M"]
    L_now = factors_now["L"]
    C_now = factors_now["C"]
    D_now = factors_now["D"]
    AISC_now = factors_now["aisc"]
    S = metal_price

    # 單因子反推
    M_need = M_now * ratio_mult
    one_minus_L_need = (1 - L_now) * ratio_mult
    C_need = C_now * ratio_mult
    D_need = D_now * ratio_mult

    # 反推 AISC
    AISC_implied = S * (1 - C_need) if C_need <= 1 else None

    single_factor = {
        "multiple_only_need": M_need,
        "multiple_change_pct": ratio_mult - 1,
        "deleverage_only_need_1_minus_L": one_minus_L_need,
        "deleverage_feasible": one_minus_L_need <= 1.5,
        "cost_only_need_C": C_need,
        "cost_only_implied_aisc": AISC_implied,
        "cost_feasible": AISC_implied is not None and 0 < AISC_implied < AISC_now,
        "dilution_only_need_D": D_need,
        "dilution_feasible": 0.5 < D_need < 1.5,
    }

    # 雙因子組合網格
    two_factor_grid = []
    for m_mult in [1.10, 1.15, 1.20, 1.25, 1.30]:
        for s_mult in [0.85, 0.90, 0.95, 1.00]:
            new_S = S * s_mult
            new_C = 1 - AISC_now / new_S if new_S > 0 else 0
            achieved = m_mult * (new_C / C_now) if C_now > 0 else 0

            two_factor_grid.append({
                "scenario": "multiple_up_metal_down",
                "multiple_change": m_mult - 1,
                "metal_change": s_mult - 1,
                "achieved_multiplier": achieved,
                "hits_target": achieved >= ratio_mult,
            })

    return {
        "target_ratio": R_target,
        "ratio_multiplier": ratio_mult,
        "single_factor": single_factor,
        "two_factor_grid": two_factor_grid,
    }


# =============================================================================
# 事件研究
# =============================================================================

def event_study(
    ratio: pd.Series,
    bottom_threshold: float,
    min_separation: int = 180
) -> list:
    """
    識別歷史底部事件

    Parameters
    ----------
    ratio : pd.Series
        比率序列
    bottom_threshold : float
        底部門檻
    min_separation : int
        最小間隔天數

    Returns
    -------
    list
        底部事件列表
    """
    is_bottom = ratio <= bottom_threshold
    events = []

    last_event = None
    for date, val in ratio[is_bottom].items():
        if last_event is None or (date - last_event).days >= min_separation:
            events.append({
                "date": date.strftime("%Y-%m-%d"),
                "ratio": float(val),
            })
            last_event = date

    return events


# =============================================================================
# 主分析函數
# =============================================================================

def run_analysis(config: AnalyzerConfig) -> dict:
    """
    執行完整分析

    Parameters
    ----------
    config : AnalyzerConfig
        分析配置

    Returns
    -------
    dict
        分析結果
    """
    print(f"開始分析: {config.miner_universe_ticker} / {config.metal_symbol}")
    print(f"區間: {config.start_date} ~ {config.end_date}")

    # 1. 取得價格
    print("取得價格數據...")
    metal = fetch_prices(
        config.metal_symbol,
        config.start_date,
        config.end_date,
        config.frequency
    )

    miner = fetch_prices(
        config.miner_universe_ticker,
        config.start_date,
        config.end_date,
        config.frequency
    )

    # 對齊日期
    common_dates = metal.index.intersection(miner.index)
    metal = metal.loc[common_dates]
    miner = miner.loc[common_dates]

    # 計算比率
    ratio = miner / metal

    print(f"數據點數: {len(ratio)}")

    # 2. 當前狀態
    R_now = float(ratio.iloc[-1])
    S_now = float(metal.iloc[-1])
    E_now = float(miner.iloc[-1])
    R_percentile = float((ratio <= R_now).mean())

    # 門檻
    R_bottom = float(ratio.quantile(config.bottom_quantile))
    R_top = float(ratio.quantile(config.top_quantile))
    R_median = float(ratio.quantile(0.5))

    # 區間判定
    if R_percentile <= 0.20:
        zone = "bottom"
    elif R_percentile <= 0.40:
        zone = "low"
    elif R_percentile <= 0.60:
        zone = "neutral"
    elif R_percentile <= 0.80:
        zone = "high"
    else:
        zone = "top"

    print(f"當前比率: {R_now:.3f} (分位數: {R_percentile:.1%}, {zone})")

    # 3. 取得持股與計算因子
    print("計算基本面因子...")
    holdings = get_holdings(config.miner_universe_ticker)

    factors_list = []
    weights = []
    holdings_detail = []

    for ticker, weight in holdings.items():
        fundamentals = get_fundamentals(ticker)
        if fundamentals:
            factors = compute_factors(fundamentals, S_now)
            factors_list.append(factors)
            weights.append(weight)

            holdings_detail.append({
                "ticker": ticker,
                "name": fundamentals.get("name", ticker),
                "weight": weight,
                "aisc": factors["aisc"],
                "aisc_method": "simulated",
                "net_debt_to_ev": factors["L"],
                "ev_to_ebitda": factors["M"],
                "shares_yoy": factors["shares_yoy"],
            })

    # 權重加總
    agg_factors = weighted_aggregate(factors_list, weights)

    print(f"AISC (加權): ${agg_factors['aisc']:.1f}/oz")
    print(f"NetDebt/EV: {agg_factors['L']:.1%}")
    print(f"EV/EBITDA: {agg_factors['M']:.1f}x")

    # 4. 反推分析
    print("執行門檻反推...")
    backsolve_top = backsolve(R_now, R_top, agg_factors, S_now)
    backsolve_median = backsolve(R_now, R_median, agg_factors, S_now)

    # 5. 事件研究
    print("執行事件研究...")
    events = event_study(ratio, R_bottom)
    print(f"偵測到 {len(events)} 次底部事件")

    # 6. 組裝輸出
    output = {
        "skill": "backsolve_miner_vs_metal_ratio_with_fundamentals",
        "version": "0.1.0",
        "generated_at": datetime.now().isoformat(),

        "inputs": {
            "metal_symbol": config.metal_symbol,
            "miner_universe": {
                "type": config.miner_universe_type,
                "etf_ticker": config.miner_universe_ticker,
            },
            "region_profile": config.region_profile,
            "time_range": {
                "start": config.start_date,
                "end": config.end_date,
                "frequency": config.frequency,
            },
        },

        "now": {
            "date": ratio.index[-1].strftime("%Y-%m-%d"),
            "metal_price": S_now,
            "miner_price": E_now,
            "ratio": R_now,
            "ratio_percentile": R_percentile,
            "zone": zone,
        },

        "thresholds": {
            "bottom_ratio": R_bottom,
            "top_ratio": R_top,
            "median_ratio": R_median,
        },

        "fundamentals_weighted": {
            "aisc_usd_per_oz": agg_factors["aisc"],
            "net_debt_to_ev": agg_factors["L"],
            "ev_to_ebitda": agg_factors["M"],
            "shares_yoy_change": agg_factors["shares_yoy"],
        },

        "factors_now": {
            "cost_factor_C": agg_factors["C"],
            "leverage_factor_1_minus_L": agg_factors["one_minus_L"],
            "multiple_M": agg_factors["M"],
            "dilution_discount_D": agg_factors["D"],
        },

        "backsolve_to_top": backsolve_top,
        "backsolve_to_median": backsolve_median,

        "event_study": {
            "bottom_threshold": R_bottom,
            "events_count": len(events),
            "bottom_events": events,
        },

        "holdings_detail": holdings_detail,

        "summary": (
            f"{config.miner_universe_ticker}/{config.metal_symbol} 比率處於歷史"
            f"{zone}區間（{R_percentile:.1%} 分位數）。"
            f"當前 AISC ${agg_factors['aisc']:.1f}/oz，"
            f"EV/EBITDA {agg_factors['M']:.1f}x。"
        ),

        "notes": [
            "AISC 使用模擬數據，實際應從 SEC EDGAR 抓取",
            "財報數據時滯 1-2 季，反映過去而非當前狀態",
            "建議交叉驗證：COT 持倉、ETF 流量、美元/實質利率",
        ],

        "data_sources": {
            "prices": "yfinance",
            "filings": "simulated",
            "holdings": "simulated",
        },
    }

    return output


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="礦業股/金屬價格比率基本面分析器"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="使用預設參數快速分析 (SIL / SI=F)"
    )

    parser.add_argument(
        "--metal-symbol",
        type=str,
        default="SI=F",
        help="金屬價格代碼 (預設: SI=F)"
    )

    parser.add_argument(
        "--miner-universe",
        type=str,
        default="etf:SIL",
        help="礦業股定義 (格式: etf:SIL 或 tickers:PAAS,AG,HL)"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default="",
        help="起始日期 (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default="",
        help="結束日期 (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--freq",
        type=str,
        default="1wk",
        choices=["1d", "1wk", "1mo"],
        help="取樣頻率"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="輸出檔案路徑"
    )

    parser.add_argument(
        "--event-study",
        action="store_true",
        help="執行事件研究"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # 解析 miner_universe
    miner_type = "etf_holdings"
    miner_ticker = "SIL"

    if args.miner_universe.startswith("etf:"):
        miner_ticker = args.miner_universe.split(":")[1]
    elif args.miner_universe.startswith("tickers:"):
        miner_type = "ticker_list"
        # 這裡可以解析 tickers 列表

    config = AnalyzerConfig(
        metal_symbol=args.metal_symbol,
        miner_universe_type=miner_type,
        miner_universe_ticker=miner_ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        frequency=args.freq,
    )

    # 執行分析
    result = run_analysis(config)

    # 輸出
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n結果已輸出至: {output_path}")
    else:
        print("\n" + "=" * 60)
        print("分析結果")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
