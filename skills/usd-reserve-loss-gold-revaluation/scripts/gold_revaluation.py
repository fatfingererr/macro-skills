#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USD Reserve Loss Gold Revaluation Calculator

在「美元／某貨幣失去儲備地位、黃金成為唯一錨」的假設下，
用央行貨幣負債 ÷ 黃金儲備，推演「資產負債表可承受的隱含金價」。

Usage:
    python gold_revaluation.py --quick
    python gold_revaluation.py --entities USD,CNY,JPY --aggregate M0 --weighting fx_turnover
    python gold_revaluation.py --compare-aggregates
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from datetime import datetime, date
import json
import argparse
import pandas as pd
import numpy as np

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


# ============================================================================
# Constants
# ============================================================================

TONNE_TO_TROY_OZ = 32150.7466

# BIS 2022 FX Turnover weights (sum > 100% due to bilateral counting)
FX_TURNOVER_WEIGHTS_2022 = {
    "USD": 0.8825,
    "EUR": 0.3092,
    "JPY": 0.1692,
    "GBP": 0.1288,
    "CNY": 0.0704,
    "AUD": 0.0631,
    "CAD": 0.0620,
    "CHF": 0.0503,
    "HKD": 0.0264,
    "SGD": 0.0240,
}

# IMF COFER Reserve Share weights (2023 Q4)
RESERVE_SHARE_WEIGHTS_2023 = {
    "USD": 0.5889,
    "EUR": 0.1998,
    "JPY": 0.0545,
    "GBP": 0.0487,
    "CNY": 0.0262,
    "CAD": 0.0253,
    "AUD": 0.0202,
    "CHF": 0.0020,
}

# Static gold reserves data (tonnes) - World Gold Council 2024 Q3
GOLD_RESERVES_TONNES = {
    "USD": 8133.5,    # USA
    "EUR": 10773.5,   # Eurozone (ECB + members)
    "CNY": 2264.3,    # China
    "JPY": 845.9,     # Japan
    "GBP": 310.3,     # UK
    "CHF": 1040.0,    # Switzerland
    "AUD": 79.9,      # Australia
    "CAD": 0.0,       # Canada (sold all)
    "RUB": 2335.9,    # Russia
    "INR": 840.8,     # India
    "ZAR": 125.4,     # South Africa
    "KZT": 289.5,     # Kazakhstan
}

# Static M0 data (local currency, approximate 2024)
M0_LOCAL = {
    "USD": 5.8e12,     # USD
    "EUR": 6.2e12,     # EUR
    "CNY": 11.6e12,    # CNY
    "JPY": 680e12,     # JPY
    "GBP": 870e9,      # GBP
    "CHF": 720e9,      # CHF
    "AUD": 120e9,      # AUD
    "CAD": 110e9,      # CAD
    "RUB": 17e12,      # RUB
    "INR": 36e12,      # INR
    "ZAR": 150e9,      # ZAR
    "KZT": 3.5e12,     # KZT
}

# Static M2 data (local currency, approximate 2024)
M2_LOCAL = {
    "USD": 20.9e12,
    "EUR": 15.8e12,
    "CNY": 292e12,
    "JPY": 1200e12,
    "GBP": 3.1e12,
    "CHF": 1.2e12,
    "AUD": 2.5e12,
    "CAD": 2.3e12,
    "RUB": 95e12,
    "INR": 240e12,
    "ZAR": 4.5e12,
    "KZT": 25e12,
}

# FX rates: 1 unit local currency = ? USD (approximate)
FX_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "CNY": 0.14,
    "JPY": 0.0068,
    "GBP": 1.27,
    "CHF": 1.17,
    "AUD": 0.65,
    "CAD": 0.74,
    "RUB": 0.011,
    "INR": 0.012,
    "ZAR": 0.053,
    "KZT": 0.0020,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class GoldRevaluationInput:
    """Input parameters for gold revaluation analysis"""
    scenario_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    entities: List[str] = field(default_factory=lambda: ["USD", "EUR", "CNY", "JPY", "GBP", "CHF"])
    monetary_aggregate: Literal["M0", "M1", "M2", "MB", "M3"] = "M0"
    liability_scope: Literal["central_bank", "broad_money"] = "broad_money"
    weighting_method: Literal["fx_turnover", "reserve_share", "equal", "custom"] = "fx_turnover"
    weights: Optional[Dict[str, float]] = None
    fx_base: str = "USD"
    gold_reserve_unit: Literal["troy_oz", "tonnes"] = "troy_oz"
    gold_price_spot: Optional[float] = None
    fx_rates: Optional[Dict[str, float]] = None
    output_format: Literal["json", "markdown"] = "json"


@dataclass
class EntityResult:
    """Result for a single entity"""
    entity: str
    gold_tonnes: float
    gold_oz: float
    money_local: float
    money_base_usd: float
    fx_rate_to_usd: float
    weight: float
    implied_gold_price: float
    implied_gold_price_weighted: float
    backing_ratio_at_spot: float
    lever_multiple_vs_spot: float
    required_gold_oz_full_back: float
    additional_gold_oz_needed: float


# ============================================================================
# Data Fetching Functions
# ============================================================================

def fetch_gold_price_fred() -> Optional[float]:
    """Fetch gold price from FRED (GOLDAMGBD228NLBM)"""
    if not HAS_REQUESTS:
        return None

    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
        params = {
            "id": "GOLDAMGBD228NLBM",
            "cosd": (datetime.now() - pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
            "coed": datetime.now().strftime("%Y-%m-%d")
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"])
        df = df.dropna()
        if len(df) > 0:
            return float(df.iloc[-1]["GOLDAMGBD228NLBM"])
    except Exception:
        pass

    return None


def fetch_gold_price_yahoo() -> Optional[float]:
    """Fetch gold price from Yahoo Finance"""
    if not HAS_YFINANCE:
        return None

    try:
        data = yf.download("GC=F", period="5d", progress=False)
        if len(data) > 0:
            return float(data["Close"].iloc[-1])
    except Exception:
        pass

    return None


def get_gold_price(spot_override: Optional[float] = None) -> float:
    """Get gold price with fallback chain"""
    if spot_override is not None:
        return spot_override

    # Try FRED
    price = fetch_gold_price_fred()
    if price:
        return price

    # Try Yahoo
    price = fetch_gold_price_yahoo()
    if price:
        return price

    # Default fallback
    return 2050.0


def get_weights(method: str, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Get weights based on method"""
    if method == "fx_turnover":
        return FX_TURNOVER_WEIGHTS_2022.copy()
    elif method == "reserve_share":
        return RESERVE_SHARE_WEIGHTS_2023.copy()
    elif method == "equal":
        return {}  # Will be filled with 1.0 for all entities
    elif method == "custom" and custom_weights:
        return custom_weights.copy()
    else:
        return {}


def get_money_supply(entity: str, aggregate: str) -> float:
    """Get money supply for entity"""
    if aggregate in ["M0", "MB"]:
        return M0_LOCAL.get(entity, 0)
    elif aggregate in ["M2", "M3"]:
        return M2_LOCAL.get(entity, 0)
    elif aggregate == "M1":
        # Approximate M1 as average of M0 and M2
        m0 = M0_LOCAL.get(entity, 0)
        m2 = M2_LOCAL.get(entity, 0)
        return (m0 + m2) / 2 if m2 > 0 else m0
    return 0


# ============================================================================
# Core Calculation Functions
# ============================================================================

def compute_gold_anchor_stress(params: GoldRevaluationInput) -> Dict:
    """
    Main calculation function for gold revaluation stress test

    Returns dict with:
    - headline: weighted implied gold price
    - table: per-entity results
    - ranking: sorted by leverage
    - insights: interpretation text
    """

    # Get gold price
    gold_spot = get_gold_price(params.gold_price_spot)

    # Get weights
    weight_map = get_weights(params.weighting_method, params.weights)

    # Get FX rates
    fx_rates = params.fx_rates if params.fx_rates else FX_RATES_TO_USD.copy()

    results: List[EntityResult] = []
    total_weighted_money = 0.0
    total_gold_oz = 0.0

    for entity in params.entities:
        # Get gold reserves
        gold_tonnes = GOLD_RESERVES_TONNES.get(entity, 0)
        gold_oz = gold_tonnes * TONNE_TO_TROY_OZ

        if gold_oz <= 0:
            continue  # Skip entities with no gold

        # Get money supply
        money_local = get_money_supply(entity, params.monetary_aggregate)
        fx_rate = fx_rates.get(entity, 1.0)
        money_base_usd = money_local * fx_rate

        # Get weight
        weight = weight_map.get(entity, 1.0 if params.weighting_method == "equal" else 0.0)

        # Calculate implied prices
        implied_price = money_base_usd / gold_oz if gold_oz > 0 else 0
        implied_price_weighted = (money_base_usd * weight) / gold_oz if gold_oz > 0 else 0

        # Calculate backing ratio
        backing_ratio = (gold_oz * gold_spot) / money_base_usd if money_base_usd > 0 else 0

        # Calculate lever multiple
        lever_multiple = implied_price_weighted / gold_spot if gold_spot > 0 else 0

        # Calculate gold gap
        required_gold = money_base_usd / gold_spot if gold_spot > 0 else 0
        additional_gold = max(0, required_gold - gold_oz)

        results.append(EntityResult(
            entity=entity,
            gold_tonnes=gold_tonnes,
            gold_oz=gold_oz,
            money_local=money_local,
            money_base_usd=money_base_usd,
            fx_rate_to_usd=fx_rate,
            weight=weight,
            implied_gold_price=implied_price,
            implied_gold_price_weighted=implied_price_weighted,
            backing_ratio_at_spot=backing_ratio,
            lever_multiple_vs_spot=lever_multiple,
            required_gold_oz_full_back=required_gold,
            additional_gold_oz_needed=additional_gold
        ))

        # Accumulate for headline
        total_weighted_money += money_base_usd * weight
        total_gold_oz += gold_oz

    # Calculate headline
    headline_implied_price = total_weighted_money / total_gold_oz if total_gold_oz > 0 else 0
    headline_multiple = headline_implied_price / gold_spot if gold_spot > 0 else 0

    # Sort by lever multiple (descending)
    ranking = sorted(results, key=lambda x: x.lever_multiple_vs_spot, reverse=True)

    # Generate insights
    insights = generate_insights(params, results, headline_implied_price, gold_spot)

    return {
        "skill": "usd-reserve-loss-gold-revaluation",
        "version": "0.1.0",
        "scenario_date": params.scenario_date,
        "assumptions": {
            "monetary_aggregate": params.monetary_aggregate,
            "weighting_method": params.weighting_method,
            "fx_base": params.fx_base,
            "gold_spot_usd_per_oz": gold_spot
        },
        "headline": {
            "implied_gold_price_weighted_usd_per_oz": round(headline_implied_price, 2),
            "vs_spot_multiple": round(headline_multiple, 2),
            "interpretation": "資產負債表壓力測算（非價格預測）：在該權重與口徑下，若黃金成為唯一錨且需承擔相應貨幣負債，金價需重估至此水平。"
        },
        "table": [
            {
                "entity": r.entity,
                "gold_tonnes": round(r.gold_tonnes, 1),
                "gold_oz": int(r.gold_oz),
                "money_base_usd": r.money_base_usd,
                "weight": round(r.weight, 4),
                "implied_gold_price": round(r.implied_gold_price, 2),
                "implied_gold_price_weighted": round(r.implied_gold_price_weighted, 2),
                "backing_ratio_at_spot": round(r.backing_ratio_at_spot, 4),
                "lever_multiple_vs_spot": round(r.lever_multiple_vs_spot, 2),
                "additional_gold_oz_needed": int(r.additional_gold_oz_needed)
            }
            for r in results
        ],
        "ranking": {
            "by_lever_multiple_desc": [
                {"rank": i+1, "entity": r.entity, "lever_multiple": round(r.lever_multiple_vs_spot, 2)}
                for i, r in enumerate(ranking)
            ],
            "by_backing_ratio_asc": [
                {"rank": i+1, "entity": r.entity, "backing_ratio": round(r.backing_ratio_at_spot, 4)}
                for i, r in enumerate(sorted(results, key=lambda x: x.backing_ratio_at_spot))
            ]
        },
        "insights": insights,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_freshness": {
                "gold_reserves": "2024-Q3 (WGC)",
                "money_supply": "2024 approx",
                "fx_turnover": "2022 (BIS)"
            }
        }
    }


def generate_insights(params: GoldRevaluationInput, results: List[EntityResult],
                      headline_price: float, gold_spot: float) -> List[Dict]:
    """Generate interpretation insights"""
    insights = []

    # Insight 1: M0 vs M2
    insights.append({
        "id": 1,
        "title": "M0 與 M2 的差異",
        "content": f"使用 {params.monetary_aggregate} 口徑。M0 與 M2 的差異主要反映『信用乘數』槓桿效應：M2 包含銀行體系信用擴張，因此隱含金價會極端放大（通常 4-5 倍）。"
    })

    # Find most leveraged
    most_leveraged = max(results, key=lambda x: x.lever_multiple_vs_spot)
    insights.append({
        "id": 2,
        "title": f"{most_leveraged.entity} 的高槓桿",
        "content": f"backing_ratio 很低（約 {most_leveraged.backing_ratio_at_spot:.1%}）代表該貨幣體系對信用擴張依賴度高；在『黃金唯一錨』情境下，需要金價大幅重估（{most_leveraged.lever_multiple_vs_spot:.1f}x）或大規模增持黃金。"
    })

    # Insight 3: Weighting method
    weight_desc = {
        "fx_turnover": "外匯成交佔比",
        "reserve_share": "外匯儲備幣別佔比",
        "equal": "等權重",
        "custom": "自訂權重"
    }
    insights.append({
        "id": 3,
        "title": f"加權方法的直覺",
        "content": f"使用 {weight_desc.get(params.weighting_method, params.weighting_method)} 權重。份額越高的貨幣，在「重新錨定」時需吸收的壓力越大；因此 headline 更像在描述『全球體系再定價』而不是單一國家內生均衡。"
    })

    # Find least leveraged
    least_leveraged = min(results, key=lambda x: x.lever_multiple_vs_spot)
    if least_leveraged.backing_ratio_at_spot > 0.5:
        insights.append({
            "id": 4,
            "title": f"{least_leveraged.entity} 的特殊性",
            "content": f"{least_leveraged.entity} 的 backing_ratio 達 {least_leveraged.backing_ratio_at_spot:.0%}，黃金儲備相對充足，在『黃金唯一錨』情境下相對穩健。"
        })

    return insights


def compare_aggregates(params: GoldRevaluationInput) -> Dict:
    """Compare M0 vs M2 results"""

    # Run M0
    params_m0 = GoldRevaluationInput(
        scenario_date=params.scenario_date,
        entities=params.entities,
        monetary_aggregate="M0",
        weighting_method=params.weighting_method,
        weights=params.weights,
        gold_price_spot=params.gold_price_spot,
        fx_rates=params.fx_rates
    )
    result_m0 = compute_gold_anchor_stress(params_m0)

    # Run M2
    params_m2 = GoldRevaluationInput(
        scenario_date=params.scenario_date,
        entities=params.entities,
        monetary_aggregate="M2",
        weighting_method=params.weighting_method,
        weights=params.weights,
        gold_price_spot=params.gold_price_spot,
        fx_rates=params.fx_rates
    )
    result_m2 = compute_gold_anchor_stress(params_m2)

    # Calculate credit multiplier
    m0_price = result_m0["headline"]["implied_gold_price_weighted_usd_per_oz"]
    m2_price = result_m2["headline"]["implied_gold_price_weighted_usd_per_oz"]
    credit_multiplier = m2_price / m0_price if m0_price > 0 else 0

    return {
        "skill": "usd-reserve-loss-gold-revaluation",
        "mode": "compare_aggregates",
        "scenario_date": params.scenario_date,
        "headline_comparison": {
            "m0": {
                "implied_gold_price": m0_price,
                "vs_spot_multiple": result_m0["headline"]["vs_spot_multiple"]
            },
            "m2": {
                "implied_gold_price": m2_price,
                "vs_spot_multiple": result_m2["headline"]["vs_spot_multiple"]
            },
            "credit_multiplier": round(credit_multiplier, 2)
        },
        "entity_comparison": [
            {
                "entity": m0_row["entity"],
                "m0_backing_ratio": m0_row["backing_ratio_at_spot"],
                "m2_backing_ratio": next(
                    (m2_row["backing_ratio_at_spot"]
                     for m2_row in result_m2["table"]
                     if m2_row["entity"] == m0_row["entity"]),
                    0
                ),
            }
            for m0_row in result_m0["table"]
        ],
        "insights": [
            {
                "title": "M0 vs M2 差距",
                "content": f"信用乘數約 {credit_multiplier:.1f} 倍，反映銀行體系的信用擴張程度"
            },
            {
                "title": "VanEck 的選擇",
                "content": "VanEck '$39k gold' 論點使用 M0 口徑，是相對保守的估計"
            }
        ]
    }


def quick_check() -> Dict:
    """Run quick check with default parameters"""
    params = GoldRevaluationInput(
        entities=["USD", "EUR", "CNY", "JPY", "GBP", "CHF"],
        monetary_aggregate="M0",
        weighting_method="fx_turnover"
    )

    result = compute_gold_anchor_stress(params)

    # Return simplified output
    return {
        "skill": "usd-reserve-loss-gold-revaluation",
        "scenario_date": result["scenario_date"],
        "headline": {
            "implied_gold_price_m0_weighted": result["headline"]["implied_gold_price_weighted_usd_per_oz"],
            "vs_spot_multiple": result["headline"]["vs_spot_multiple"]
        },
        "top_leveraged": result["ranking"]["by_lever_multiple_desc"][:3],
        "gold_spot": result["assumptions"]["gold_spot_usd_per_oz"]
    }


# ============================================================================
# Output Formatting
# ============================================================================

def format_markdown(result: Dict) -> str:
    """Format result as markdown"""
    lines = []

    lines.append("# 黃金重估壓力測試報告\n")
    lines.append(f"**情境日期**: {result['scenario_date']}")
    lines.append(f"**貨幣口徑**: {result['assumptions']['monetary_aggregate']}")
    lines.append(f"**加權方式**: {result['assumptions']['weighting_method']}")
    lines.append(f"**基準金價**: ${result['assumptions']['gold_spot_usd_per_oz']:,.0f} / oz\n")

    lines.append("---\n")
    lines.append("## Headline 隱含金價\n")
    lines.append(f"| 指標 | 數值 |")
    lines.append("|------|------|")
    lines.append(f"| 加權隱含金價 | **${result['headline']['implied_gold_price_weighted_usd_per_oz']:,.0f} / oz** |")
    lines.append(f"| 相對現價倍數 | **{result['headline']['vs_spot_multiple']:.1f}x** |\n")

    lines.append(f"> {result['headline']['interpretation']}\n")

    lines.append("---\n")
    lines.append("## 各貨幣槓桿分析\n")
    lines.append("| 排名 | 貨幣 | 黃金支撐率 | 槓桿倍數 |")
    lines.append("|:----:|------|----------:|--------:|")

    for item in result['ranking']['by_lever_multiple_desc']:
        backing = next(
            (r['backing_ratio_at_spot'] for r in result['table'] if r['entity'] == item['entity']),
            0
        )
        lines.append(f"| {item['rank']} | {item['entity']} | {backing:.1%} | {item['lever_multiple']:.1f}x |")

    lines.append("\n---\n")
    lines.append("## 關鍵洞察\n")
    for insight in result.get('insights', []):
        lines.append(f"### {insight['id']}. {insight['title']}\n")
        lines.append(f"{insight['content']}\n")

    lines.append("---\n")
    lines.append(f"*報告生成時間: {result['metadata']['generated_at']}*")

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="USD Reserve Loss Gold Revaluation Calculator"
    )
    parser.add_argument("--quick", action="store_true", help="Quick check with defaults")
    parser.add_argument("--compare-aggregates", action="store_true", help="Compare M0 vs M2")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Scenario date")
    parser.add_argument("--entities", default="USD,EUR,CNY,JPY,GBP,CHF", help="Comma-separated entities")
    parser.add_argument("--aggregate", default="M0", choices=["M0", "M1", "M2", "MB", "M3"])
    parser.add_argument("--weighting", default="fx_turnover",
                        choices=["fx_turnover", "reserve_share", "equal", "custom"])
    parser.add_argument("--gold-price", type=float, help="Override gold price")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", default="json", choices=["json", "markdown"])

    args = parser.parse_args()

    # Quick check
    if args.quick:
        result = quick_check()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Compare aggregates
    if args.compare_aggregates:
        params = GoldRevaluationInput(
            scenario_date=args.date,
            entities=args.entities.split(","),
            weighting_method=args.weighting,
            gold_price_spot=args.gold_price
        )
        result = compare_aggregates(params)
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Output saved to {args.output}")
        else:
            print(output)
        return

    # Full analysis
    params = GoldRevaluationInput(
        scenario_date=args.date,
        entities=args.entities.split(","),
        monetary_aggregate=args.aggregate,
        weighting_method=args.weighting,
        gold_price_spot=args.gold_price,
        output_format=args.format
    )

    result = compute_gold_anchor_stress(params)

    if args.format == "markdown":
        output = format_markdown(result)
    else:
        output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output saved to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
