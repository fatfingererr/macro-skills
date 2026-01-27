#!/usr/bin/env python3
"""
農產品對沖基金部位分析主腳本

整合 COT 資料與宏觀指標，產出資金流分析報告。
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# 從 fetch_cot_data 導入函數
from fetch_cot_data import (
    ALL_GROUPS,
    aggregate_by_group,
    calculate_flows,
    fetch_cot_from_api,
    get_latest_week_summary,
    parse_cot_data,
)

# 從 fetch_macro_data 導入函數（如果存在）
try:
    from fetch_macro_data import fetch_all_indicators, calculate_tailwind_score
    HAS_MACRO = True
except ImportError:
    HAS_MACRO = False


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

    return round(1 - p, 3)


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

    return {"score": round(score, 2), "components": components}


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
    if flow_total is not None and flow_total > 0:
        if prev_flow_total is not None and prev_flow_total < 0:
            calls.append("Funds back & buying")
            confidence_factors.append(0.3)
        elif firepower_total and firepower_total > 0.5:
            calls.append("Funds continue buying")
            confidence_factors.append(0.2)

    # Signal 2: Funds selling
    if flow_total is not None and flow_total < 0:
        if prev_flow_total is not None and prev_flow_total > 0:
            calls.append("Funds turning bearish")
            confidence_factors.append(0.25)
        else:
            calls.append("Funds continue selling")
            confidence_factors.append(0.15)

    # Signal 3: Crowded risk
    if firepower_total and firepower_total < 0.2:
        calls.append("Crowded long - caution")
        confidence_factors.append(-0.15)

    # Signal 4: Extreme short (opportunity)
    if firepower_total and firepower_total > 0.85:
        calls.append("Extreme short - watch for reversal")
        confidence_factors.append(0.1)

    # Signal 5: Macro alignment
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
    if context.get("macro_score") and context.get("macro_score") >= 0.67:
        annotations.append({
            "label": "macro_mood_bullish",
            "rule_hit": True,
            "evidence": [
                k.replace("_", " ") for k, v in context.get("macro_components", {}).items() if v
            ],
            "date": context.get("date"),
        })

    # Funds buying
    if context.get("flow_total") and context.get("flow_total") > 0:
        fp = context.get("firepower_total")
        if fp and fp > 0.5:
            annotations.append({
                "label": "funds_back_buying",
                "rule_hit": True,
                "evidence": [
                    f"Flow: {context.get('flow_total', 0):+,}",
                    f"Firepower: {fp:.0%}" if fp else "N/A",
                ],
                "date": context.get("date"),
            })

    # Funds selling
    if context.get("flow_total") and context.get("flow_total") < -10000:
        annotations.append({
            "label": "funds_selling",
            "rule_hit": True,
            "evidence": [f"Flow: {context.get('flow_total', 0):+,}"],
            "date": context.get("date"),
        })

    # Crowded
    if context.get("firepower_total") is not None and context.get("firepower_total") < 0.2:
        annotations.append({
            "label": "crowded_long",
            "rule_hit": True,
            "evidence": [f"Firepower: {context.get('firepower_total', 0):.0%}"],
            "date": context.get("date"),
        })

    # Extreme short
    if context.get("firepower_total") is not None and context.get("firepower_total") > 0.85:
        annotations.append({
            "label": "extreme_short",
            "rule_hit": True,
            "evidence": [f"Firepower: {context.get('firepower_total', 0):.0%}"],
            "date": context.get("date"),
        })

    return annotations


def run_analysis(
    start_date: str = None,
    end_date: str = None,
    cot_file: str = None,
    macro_file: str = None,
    lookback_weeks: int = 156,
    fetch_fresh: bool = True,
) -> Dict:
    """
    執行完整分析

    Args:
        start_date: 起始日期
        end_date: 結束日期
        cot_file: 已存在的 COT 資料檔案路徑
        macro_file: 已存在的宏觀指標檔案路徑
        lookback_weeks: 火力計算視窗（週數）
        fetch_fresh: 是否從 API 抓取最新資料

    Returns:
        分析結果字典
    """
    # 設定日期範圍
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")

    # 載入或抓取 COT 資料
    if cot_file and Path(cot_file).exists() and not fetch_fresh:
        print(f"Loading COT data from {cot_file}")
        cot_df = pd.read_parquet(cot_file)
    else:
        print("Fetching fresh COT data from API...")
        raw_df = fetch_cot_from_api(start_date, end_date)
        if raw_df.empty:
            raise ValueError("Failed to fetch COT data from API")
        cot_df = parse_cot_data(raw_df)
        cot_df = calculate_flows(cot_df)

    # 載入宏觀資料（如果可用）
    macro_df = None
    macro_result = {"score": None, "components": {}}

    if macro_file and Path(macro_file).exists():
        try:
            macro_df = pd.read_parquet(macro_file)
            macro_result = calculate_macro_tailwind(macro_df)
        except Exception as e:
            print(f"Warning: Failed to load macro data: {e}")

    # 計算分組流量與部位
    flows, positions = aggregate_by_group(cot_df)

    # 計算火力
    firepower = {}
    for col in ["total"] + ALL_GROUPS:
        if col in positions.columns:
            fp = calculate_firepower(positions[col], lookback_weeks)
            firepower[col] = fp

    # 取得最新資料
    latest_date = flows.index.max()
    latest_flow = flows.loc[latest_date]
    latest_pos = positions.loc[latest_date]

    # 取得前一週資料
    prev_date = flows.index[-2] if len(flows) > 1 else None
    prev_flow_total = flows.loc[prev_date]["total"] if prev_date is not None else None

    # 產生呼叫
    call_result = generate_call(
        flow_total=latest_flow["total"],
        firepower_total=firepower.get("total"),
        macro_score=macro_result["score"],
        prev_flow_total=prev_flow_total,
    )

    # 產生標註
    context = {
        "date": str(latest_date),
        "flow_total": latest_flow["total"],
        "firepower_total": firepower.get("total"),
        "macro_score": macro_result["score"],
        "macro_components": macro_result["components"],
    }
    annotations = generate_annotations(context)

    # 建立 why 說明
    why_list = []
    why_list.append(f"總流量: {latest_flow['total']:+,.0f} 合約")

    group_changes = []
    for g in ALL_GROUPS:
        if g in latest_flow and latest_flow[g] != 0:
            group_changes.append(f"{g}: {latest_flow[g]:+,.0f}")
    if group_changes:
        why_list.append("分組: " + ", ".join(group_changes))

    if firepower.get("total") is not None:
        why_list.append(f"火力: {firepower['total']:.0%}")

    if macro_result["score"] is not None:
        why_list.append(f"宏觀順風: {macro_result['score']:.0%}")

    # 建立風險提示
    risks = ["COT 資料只到週二，Wed-Fri 為推估"]
    if firepower.get("total") and firepower.get("total") < 0.3:
        risks.append("部位已接近歷史高檔，擁擠風險")
    if abs(latest_flow["total"]) > 50000:
        risks.append("大幅流動可能引發反向修正")

    # 組裝結果
    result = {
        "skill": "track-agri-hedge-fund-positioning",
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "as_of": str(latest_date),
        "data_source": "CFTC Socrata API (real data)",
        "summary": {
            "call": call_result["call"],
            "all_signals": call_result["all_signals"],
            "confidence": call_result["confidence"],
            "why": why_list,
            "risks": risks,
        },
        "latest_metrics": {
            "cot_week_end": str(latest_date),
            "flow_total_contracts": int(latest_flow["total"]),
            "flow_by_group_contracts": {g: int(latest_flow[g]) for g in ALL_GROUPS if g in latest_flow},
            "net_pos_total_contracts": int(latest_pos["total"]),
            "net_pos_by_group_contracts": {g: int(latest_pos[g]) for g in ALL_GROUPS if g in latest_pos},
            "buying_firepower": {k: v for k, v in firepower.items() if v is not None},
            "macro_tailwind_score": macro_result["score"],
        },
        "historical_data": {
            "weeks_available": len(flows),
            "date_range": {
                "start": str(flows.index.min()),
                "end": str(flows.index.max()),
            },
        },
        "annotations": annotations,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze agricultural hedge fund positioning")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--cot-file", type=str, default="cache/cot_data.parquet", help="COT data file")
    parser.add_argument("--macro-file", type=str, default="cache/macro_data.parquet", help="Macro data file")
    parser.add_argument("--lookback", type=int, default=156, help="Lookback weeks for firepower (default: 156 = 3 years)")
    parser.add_argument("--output", type=str, default="output/result.json", help="Output file")
    parser.add_argument("--no-fetch", action="store_true", help="Use cached data instead of fetching fresh")

    args = parser.parse_args()

    try:
        result = run_analysis(
            start_date=args.start,
            end_date=args.end,
            cot_file=args.cot_file,
            macro_file=args.macro_file,
            lookback_weeks=args.lookback,
            fetch_fresh=not args.no_fetch,
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存結果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"\nResults saved to {output_path}")

    # 顯示摘要
    print("\n" + "=" * 60)
    print(f"農產品對沖基金部位分析 ({result['as_of']})")
    print("=" * 60)
    print(f"Call:       {result['summary']['call']}")
    print(f"Confidence: {result['summary']['confidence']:.0%}")
    print(f"Signals:    {', '.join(result['summary']['all_signals'])}")
    print("-" * 60)
    print("Latest Metrics:")
    metrics = result["latest_metrics"]
    print(f"  總流量:     {metrics['flow_total_contracts']:+,} 合約")
    print(f"  總淨部位:   {metrics['net_pos_total_contracts']:,} 合約")
    print("  分組流量:")
    for g, v in metrics["flow_by_group_contracts"].items():
        print(f"    {g:12}: {v:+,}")
    print("  火力分數:")
    for g, v in metrics["buying_firepower"].items():
        print(f"    {g:12}: {v:.0%}")
    if metrics["macro_tailwind_score"] is not None:
        print(f"  宏觀順風:   {metrics['macro_tailwind_score']:.0%}")
    print("-" * 60)
    print("Why:")
    for w in result["summary"]["why"]:
        print(f"  - {w}")
    print("Risks:")
    for r in result["summary"]["risks"]:
        print(f"  - {r}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
