#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium Balance Nowcast Computation

計算鋰供需平衡指數（Balance Index）
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BalanceInput:
    """Balance 計算輸入"""
    supply_kt_lce: float
    demand_kt_lce: float
    year: int
    source_id: str = "Derived"
    confidence: float = 0.8


@dataclass
class BalanceResult:
    """Balance 計算結果"""
    balance_index: float
    gap_kt_lce: float
    gap_pct: float
    regime: str
    zscore: Optional[float]
    confidence: float
    asof_date: str


# ============================================================================
# 單位轉換
# ============================================================================

LI_TO_LCE = 5.323
LCE_TO_LI = 0.1879


def li_to_lce(value_kt_li: float) -> float:
    """鋰金屬 → 碳酸鋰當量"""
    return value_kt_li * LI_TO_LCE


def lce_to_li(value_kt_lce: float) -> float:
    """碳酸鋰當量 → 鋰金屬"""
    return value_kt_lce * LCE_TO_LI


def gwh_to_kt_li(gwh: float, kg_per_kwh: float = 0.15) -> float:
    """電池容量 → 鋰金屬需求"""
    return gwh * kg_per_kwh / 1000


def gwh_to_kt_lce(gwh: float, kg_per_kwh: float = 0.15) -> float:
    """電池容量 → 碳酸鋰當量需求"""
    kt_li = gwh_to_kt_li(gwh, kg_per_kwh)
    return li_to_lce(kt_li)


# ============================================================================
# Balance 計算
# ============================================================================

def compute_gap(supply_kt_lce: float, demand_kt_lce: float) -> Dict[str, float]:
    """
    計算供需缺口

    Returns:
        gap_kt_lce: 缺口量（正=供給過剩，負=供給短缺）
        gap_pct: 缺口比例
    """
    gap = supply_kt_lce - demand_kt_lce
    gap_pct = gap / demand_kt_lce if demand_kt_lce > 0 else 0

    return {
        "gap_kt_lce": gap,
        "gap_pct": gap_pct
    }


def compute_balance_index(
    gap_pct: float,
    historical_gaps: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    計算 Balance Index

    Index 定義：
    - 正值：供給過剩程度
    - 負值：供給短缺程度
    - Z-score 標準化（如有歷史數據）

    Args:
        gap_pct: 當前缺口比例
        historical_gaps: 歷史缺口比例列表（用於 Z-score）

    Returns:
        balance_index: Balance 指數
        zscore: Z-score（如有歷史數據）
    """
    # 基本 index = gap_pct * 10（放大顯示）
    balance_index = gap_pct * 10

    zscore = None
    if historical_gaps and len(historical_gaps) >= 3:
        import statistics
        mean = statistics.mean(historical_gaps)
        stdev = statistics.stdev(historical_gaps)
        if stdev > 0:
            zscore = (gap_pct - mean) / stdev
            # 使用 Z-score 作為 balance_index
            balance_index = zscore

    return {
        "balance_index": balance_index,
        "zscore": zscore
    }


def classify_balance_regime(balance_index: float) -> str:
    """
    分類 Balance 狀態

    Returns:
        regime: severe_shortage | shortage | balanced | surplus | severe_surplus
    """
    if balance_index < -2:
        return "severe_shortage"
    elif balance_index < -0.5:
        return "shortage"
    elif balance_index < 0.5:
        return "balanced"
    elif balance_index < 2:
        return "surplus"
    else:
        return "severe_surplus"


def compute_balance_nowcast(
    supply_kt_lce: float,
    demand_kt_lce: float,
    historical_gaps: Optional[List[float]] = None,
    confidence: float = 0.8
) -> BalanceResult:
    """
    完整 Balance Nowcast 計算

    Args:
        supply_kt_lce: 供給量（kt LCE）
        demand_kt_lce: 需求量（kt LCE）
        historical_gaps: 歷史缺口比例
        confidence: 數據置信度

    Returns:
        BalanceResult 完整結果
    """
    # 計算缺口
    gap = compute_gap(supply_kt_lce, demand_kt_lce)

    # 計算 Balance Index
    index_result = compute_balance_index(gap["gap_pct"], historical_gaps)

    # 分類狀態
    regime = classify_balance_regime(index_result["balance_index"])

    return BalanceResult(
        balance_index=index_result["balance_index"],
        gap_kt_lce=gap["gap_kt_lce"],
        gap_pct=gap["gap_pct"],
        regime=regime,
        zscore=index_result["zscore"],
        confidence=confidence,
        asof_date=date.today().isoformat()
    )


# ============================================================================
# 多情境計算
# ============================================================================

def compute_multi_scenario_balance(
    supply_kt_lce: float,
    battery_demand_gwh: float,
    kg_per_kwh_scenarios: Optional[Dict[str, float]] = None,
    historical_gaps: Optional[List[float]] = None
) -> Dict[str, BalanceResult]:
    """
    多情境 Balance 計算

    Args:
        supply_kt_lce: 供給量
        battery_demand_gwh: 電池需求（GWh）
        kg_per_kwh_scenarios: kg/kWh 假設（conservative/neutral/aggressive）
        historical_gaps: 歷史缺口

    Returns:
        Dict[scenario_name, BalanceResult]
    """
    if kg_per_kwh_scenarios is None:
        kg_per_kwh_scenarios = {
            "conservative": 0.12,  # LFP 佔比上升
            "neutral": 0.15,       # 混合市場
            "aggressive": 0.18    # 高鎳 NMC 主導
        }

    results = {}

    for scenario, kg_per_kwh in kg_per_kwh_scenarios.items():
        demand_kt_lce = gwh_to_kt_lce(battery_demand_gwh, kg_per_kwh)
        result = compute_balance_nowcast(
            supply_kt_lce,
            demand_kt_lce,
            historical_gaps,
            confidence=0.75  # 情境假設降低置信度
        )
        results[scenario] = result

    return results


# ============================================================================
# 輸出格式化
# ============================================================================

def format_balance_output(result: BalanceResult) -> Dict[str, Any]:
    """格式化輸出為 dict"""
    return {
        "balance_index": {
            "value": round(result.balance_index, 2),
            "interpretation": _interpret_balance(result.balance_index)
        },
        "gap": {
            "kt_lce": round(result.gap_kt_lce, 1),
            "pct": round(result.gap_pct * 100, 1)
        },
        "regime": result.regime,
        "zscore": round(result.zscore, 2) if result.zscore else None,
        "confidence": result.confidence,
        "asof_date": result.asof_date
    }


def _interpret_balance(index: float) -> str:
    """解讀 Balance Index"""
    if index < -2:
        return "嚴重短缺 - 價格上行壓力大"
    elif index < -0.5:
        return "短缺 - 供給偏緊"
    elif index < 0.5:
        return "平衡 - 供需相對平衡"
    elif index < 2:
        return "過剩 - 供給寬鬆"
    else:
        return "嚴重過剩 - 價格下行壓力大"


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Lithium Balance Nowcast")
    parser.add_argument("--supply", type=float, required=True, help="Supply (kt LCE)")
    parser.add_argument("--demand", type=float, help="Demand (kt LCE)")
    parser.add_argument("--battery-gwh", type=float, help="Battery demand (GWh)")
    parser.add_argument("--kg-per-kwh", type=float, default=0.15, help="kg Li per kWh")
    parser.add_argument("--multi-scenario", action="store_true", help="Run multi-scenario")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.multi_scenario and args.battery_gwh:
        results = compute_multi_scenario_balance(args.supply, args.battery_gwh)
        output = {k: format_balance_output(v) for k, v in results.items()}
    else:
        if args.demand:
            demand = args.demand
        elif args.battery_gwh:
            demand = gwh_to_kt_lce(args.battery_gwh, args.kg_per_kwh)
        else:
            print("Error: Must provide --demand or --battery-gwh")
            exit(1)

        result = compute_balance_nowcast(args.supply, demand)
        output = format_balance_output(result)

    print(json.dumps(output, indent=2, ensure_ascii=False))
