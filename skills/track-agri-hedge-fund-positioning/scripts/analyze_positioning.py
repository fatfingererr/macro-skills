#!/usr/bin/env python3
"""
農產品對沖基金部位分析主腳本

整合 COT 資料與宏觀指標，產出資金流分析報告。
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# 預設合約對照表
DEFAULT_CONTRACTS_MAP = {
    "CORN": "grains",
    "WHEAT-SRW": "grains",
    "WHEAT-HRW": "grains",
    "SOYBEANS": "oilseeds",
    "SOYBEAN OIL": "oilseeds",
    "SOYBEAN MEAL": "oilseeds",
    "LIVE CATTLE": "meats",
    "LEAN HOGS": "meats",
    "COFFEE C": "softs",
    "SUGAR NO. 11": "softs",
}


def percentile_rank(series: pd.Series, value: float) -> float:
    """計算分位數排名"""
    s = series.dropna().values
    if len(s) == 0:
        return 0.5
    return float((s <= value).mean())


def calculate_firepower(
    net_pos_series: pd.Series, lookback_weeks: int = 156
) -> float:
    """
    計算 buying firepower

    firepower = 1 - percentile_rank
    越低的部位 = 越高的火力（加碼空間）
    """
    if len(net_pos_series) < 10:
        return None

    hist = net_pos_series.iloc[-lookback_weeks:] if len(net_pos_series) > lookback_weeks else net_pos_series
    current = net_pos_series.iloc[-1]
    p = percentile_rank(hist, current)

    return float(1 - p)


def calculate_macro_tailwind(macro_df: pd.DataFrame, lookback_days: int = 5) -> Dict:
    """計算宏觀順風評分"""
    if macro_df is None or len(macro_df) < lookback_days:
        return {"score": None, "components": {}}

    recent = macro_df.iloc[-lookback_days:]

    # 計算報酬
    usd_ret = (recent["usd"].iloc[-1] / recent["usd"].iloc[0] - 1) if "usd" in recent else 0
    crude_ret = (recent["crude"].iloc[-1] / recent["crude"].iloc[0] - 1) if "crude" in recent else 0
    metals_ret = (recent["metals"].iloc[-1] / recent["metals"].iloc[0] - 1) if "metals" in recent else 0

    # 判斷順風條件
    components = {
        "usd_down": usd_ret < 0,
        "crude_up": crude_ret > 0,
        "metals_up": metals_ret > 0,
    }

    score = sum(components.values()) / len(components)

    return {"score": score, "components": components}


def generate_call(
    flow_total: float,
    firepower_total: float,
    macro_score: float,
    prev_flow_total: float = None,
) -> Dict:
    """產生可交易呼叫"""
    calls = []
    confidence_factors = []

    # Signal 1: Funds back & buying
    if flow_total > 0:
        if prev_flow_total is not None and prev_flow_total < 0:
            calls.append("Funds back & buying")
            confidence_factors.append(0.3)
        elif firepower_total and firepower_total > 0.5:
            calls.append("Funds continue buying")
            confidence_factors.append(0.2)

    # Signal 2: Crowded risk
    if firepower_total and firepower_total < 0.2:
        calls.append("Crowded long - caution")
        confidence_factors.append(-0.15)

    # Signal 3: Extreme short (opportunity)
    if firepower_total and firepower_total > 0.85:
        calls.append("Extreme short - watch for reversal")
        confidence_factors.append(0.1)

    # Signal 4: Macro alignment
    if macro_score and macro_score >= 0.67:
        calls.append("Macro mood bullish")
        confidence_factors.append(0.15)
    elif macro_score and macro_score <= 0.33:
        calls.append("Macro headwind")
        confidence_factors.append(-0.1)

    # 決定主要呼叫
    if not calls:
        primary_call = "Mixed signals"
        confidence = 0.5
    else:
        primary_call = calls[0]
        confidence = min(0.9, max(0.3, 0.5 + sum(confidence_factors)))

    return {
        "call": primary_call,
        "all_signals": calls,
        "confidence": round(confidence, 2),
    }


def generate_annotations(context: Dict) -> List[Dict]:
    """生成圖表標註"""
    annotations = []

    # Macro mood
    if context.get("macro_score", 0) >= 0.67:
        annotations.append({
            "label": "macro_mood_bullish",
            "rule_hit": True,
            "evidence": [
                k.replace("_", " ") for k, v in context.get("macro_components", {}).items() if v
            ],
            "date": context.get("date"),
        })

    # Funds buying
    if context.get("flow_total", 0) > 0 and context.get("firepower_total", 0) > 0.5:
        annotations.append({
            "label": "funds_back_buying",
            "rule_hit": True,
            "evidence": [
                f"Flow: {context.get('flow_total', 0):+,}",
                f"Firepower: {context.get('firepower_total', 0):.0%}",
            ],
            "date": context.get("date"),
        })

    # Crowded
    if context.get("firepower_total", 1) < 0.2:
        annotations.append({
            "label": "crowded_long",
            "rule_hit": True,
            "evidence": [f"Firepower: {context.get('firepower_total', 0):.0%}"],
            "date": context.get("date"),
        })

    return annotations


def run_quick_analysis() -> Dict:
    """快速分析模式（使用模擬資料）"""
    # 這裡使用模擬資料作為示範
    # 實際使用時應從 fetch_cot_data.py 和 fetch_macro_data.py 取得資料

    result = {
        "skill": "track-agri-hedge-fund-positioning",
        "version": "0.1.0",
        "generated_at": datetime.now().isoformat(),
        "as_of": (datetime.now() - timedelta(days=datetime.now().weekday() + 5)).strftime("%Y-%m-%d"),
        "summary": {
            "call": "Funds back & buying",
            "confidence": 0.72,
            "why": [
                "COT 週部位變化顯示農產品總流量由負轉正",
                "分組（穀物/油籽）同步改善",
                "宏觀順風：美元走弱、原油偏強",
            ],
            "risks": [
                "COT 只到週二：Wed-Fri 的買回屬推估",
                "USDA 報告可能讓訊號反轉",
            ],
        },
        "latest_metrics": {
            "cot_week_end": (datetime.now() - timedelta(days=datetime.now().weekday() + 5)).strftime("%Y-%m-%d"),
            "flow_total_contracts": 58000,
            "flow_by_group_contracts": {
                "grains": 35000,
                "oilseeds": 25000,
                "meats": 5000,
                "softs": -7000,
            },
            "buying_firepower": {
                "total": 0.63,
                "grains": 0.58,
                "oilseeds": 0.67,
                "meats": 0.41,
                "softs": 0.75,
            },
            "macro_tailwind_score": 0.67,
        },
        "annotations": [
            {
                "label": "macro_mood_bullish",
                "rule_hit": True,
                "evidence": ["USD down", "crude up"],
            }
        ],
    }

    return result


def run_full_analysis(
    start_date: str,
    end_date: str,
    cot_file: str = None,
    macro_file: str = None,
    lookback_weeks: int = 156,
) -> Dict:
    """完整分析模式"""
    # 載入資料
    if cot_file and Path(cot_file).exists():
        cot_df = pd.read_parquet(cot_file)
    else:
        print("COT data not found, using simulated data")
        return run_quick_analysis()

    if macro_file and Path(macro_file).exists():
        macro_df = pd.read_parquet(macro_file)
    else:
        macro_df = None

    # 計算分組流量
    groups = ["grains", "oilseeds", "meats", "softs"]

    flows = cot_df.groupby(["date", "group"])["flow"].sum().unstack(fill_value=0)
    for g in groups:
        if g not in flows.columns:
            flows[g] = 0
    flows["total"] = flows[groups].sum(axis=1)

    positions = cot_df.groupby(["date", "group"])["pos"].sum().unstack(fill_value=0)
    for g in groups:
        if g not in positions.columns:
            positions[g] = 0
    positions["total"] = positions[groups].sum(axis=1)

    # 計算火力
    firepower = {}
    for col in ["total"] + groups:
        fp = calculate_firepower(positions[col], lookback_weeks)
        firepower[col] = fp

    # 計算宏觀順風
    macro_result = calculate_macro_tailwind(macro_df) if macro_df is not None else {"score": None, "components": {}}

    # 取得最新資料
    latest_date = flows.index.max()
    latest_flow = flows.loc[latest_date]
    prev_date = flows.index[-2] if len(flows) > 1 else None
    prev_flow = flows.loc[prev_date]["total"] if prev_date else None

    # 產生呼叫
    call_result = generate_call(
        flow_total=latest_flow["total"],
        firepower_total=firepower["total"],
        macro_score=macro_result["score"],
        prev_flow_total=prev_flow,
    )

    # 產生標註
    context = {
        "date": str(latest_date),
        "flow_total": latest_flow["total"],
        "firepower_total": firepower["total"],
        "macro_score": macro_result["score"],
        "macro_components": macro_result["components"],
    }
    annotations = generate_annotations(context)

    # 組裝結果
    result = {
        "skill": "track-agri-hedge-fund-positioning",
        "version": "0.1.0",
        "generated_at": datetime.now().isoformat(),
        "as_of": str(latest_date),
        "summary": {
            "call": call_result["call"],
            "confidence": call_result["confidence"],
            "why": [
                f"總流量: {latest_flow['total']:+,.0f} 合約",
                f"穀物: {latest_flow['grains']:+,.0f}, 油籽: {latest_flow['oilseeds']:+,.0f}",
                f"火力: {firepower['total']:.0%}" if firepower["total"] else "火力: N/A",
            ],
            "risks": [
                "COT 資料只到週二",
                "宏觀情勢可能快速變化",
            ],
        },
        "latest_metrics": {
            "cot_week_end": str(latest_date),
            "flow_total_contracts": int(latest_flow["total"]),
            "flow_by_group_contracts": {g: int(latest_flow[g]) for g in groups},
            "buying_firepower": {k: round(v, 2) if v else None for k, v in firepower.items()},
            "macro_tailwind_score": round(macro_result["score"], 2) if macro_result["score"] else None,
        },
        "weekly_flows": flows.reset_index().to_dict(orient="records"),
        "annotations": annotations,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze agricultural hedge fund positioning")
    parser.add_argument("--quick", action="store_true", help="Quick analysis mode")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--cot-file", type=str, default="cache/cot_data.parquet", help="COT data file")
    parser.add_argument("--macro-file", type=str, default="cache/macro_data.parquet", help="Macro data file")
    parser.add_argument("--lookback", type=int, default=156, help="Lookback weeks for firepower")
    parser.add_argument("--output", type=str, default="output/result.json", help="Output file")
    parser.add_argument("--visualize", action="store_true", help="Also generate visualization")

    args = parser.parse_args()

    if args.quick:
        result = run_quick_analysis()
    else:
        start = args.start or "2025-01-01"
        end = args.end or datetime.now().strftime("%Y-%m-%d")
        result = run_full_analysis(
            start_date=start,
            end_date=end,
            cot_file=args.cot_file,
            macro_file=args.macro_file,
            lookback_weeks=args.lookback,
        )

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存結果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"Results saved to {output_path}")

    # 顯示摘要
    print("\n" + "=" * 50)
    print(f"Call: {result['summary']['call']}")
    print(f"Confidence: {result['summary']['confidence']:.0%}")
    print(f"As of: {result['as_of']}")
    print("=" * 50)

    if args.visualize:
        print("\nVisualization requested - run visualize_flows.py separately")


if __name__ == "__main__":
    main()
