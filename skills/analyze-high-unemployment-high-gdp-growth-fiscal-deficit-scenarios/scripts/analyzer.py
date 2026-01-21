#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高失業高GDP情境下的財政赤字分析器

分析「失業率走高／勞動市場轉弱」但「GDP 仍維持高位」的情境下，
財政赤字占 GDP 可能擴張的區間，並生成對長天期美債的風險解讀。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# 導入數據抓取模組
from fetch_data import fetch_multiple_series, validate_data


# ============================================================
# 配置常數
# ============================================================

DEFAULT_CONFIG = {
    "lookback_years": 30,
    "frequency": "quarterly",
    "slack_metric": "unemployed_to_job_openings_ratio",
    "horizon_quarters": 8,
    "high_gdp_percentile_threshold": 0.70,
    "labor_soft_percentile_threshold": 0.80,
    "sahm_threshold": 0.5,
    "delta_ur_threshold": 1.0,
    "model": "event_study_banding"
}

REQUIRED_SERIES = ["UNRATE", "UNEMPLOY", "JTSJOL", "GDP", "GDPC1", "FYFSGDA188S"]


# ============================================================
# 數據處理函數
# ============================================================

def align_to_quarterly(data: pd.DataFrame, method: str = "quarter_end") -> pd.DataFrame:
    """將數據對齊到季度頻率"""
    if method == "quarter_end":
        return data.resample("QE").last()
    elif method == "quarter_avg":
        return data.resample("QE").mean()
    else:
        raise ValueError(f"Unknown method: {method}")


def compute_ujo(unemploy: pd.Series, jtsjol: pd.Series) -> pd.Series:
    """計算失業/職缺比 (UJO)"""
    ujo = unemploy / jtsjol
    ujo.name = "UJO"
    return ujo


def compute_sahm_rule(unrate: pd.Series) -> pd.Series:
    """計算 Sahm Rule"""
    ur_3m_ma = unrate.rolling(3).mean()
    ur_12m_min = unrate.rolling(12).min()
    sahm = ur_3m_ma - ur_12m_min
    sahm.name = "SAHM"
    return sahm


def compute_delta_ur(unrate: pd.Series, periods: int = 6) -> pd.Series:
    """計算失業率變化"""
    delta = unrate - unrate.shift(periods)
    delta.name = f"DELTA_UR_{periods}M"
    return delta


def compute_percentile_rank(series: pd.Series) -> pd.Series:
    """計算歷史分位數排名"""
    return series.rank(pct=True)


# ============================================================
# 事件識別函數
# ============================================================

def identify_labor_softening_events(
    data: pd.DataFrame,
    ujo_threshold_pctl: float = 0.80,
    sahm_threshold: float = 0.5,
    delta_ur_threshold: float = 1.0,
    min_duration: int = 2
) -> List[Dict]:
    """
    識別勞動轉弱事件

    Parameters
    ----------
    data : pd.DataFrame
        包含 UJO, SAHM, DELTA_UR 等指標的數據
    ujo_threshold_pctl : float
        UJO 分位數門檻
    sahm_threshold : float
        Sahm Rule 門檻
    delta_ur_threshold : float
        ΔUR 門檻
    min_duration : int
        最小持續期數

    Returns
    -------
    list
        事件列表
    """
    # 計算 UJO 分位數
    ujo_pctl = compute_percentile_rank(data["UJO"])

    # 定義轉弱條件
    labor_soft = (
        (ujo_pctl >= ujo_threshold_pctl) |
        (data["SAHM"] >= sahm_threshold) |
        (data["DELTA_UR_6M"] >= delta_ur_threshold)
    )

    # 識別連續事件
    events = []
    in_event = False
    event_start = None

    for i, (date, is_soft) in enumerate(labor_soft.items()):
        if is_soft and not in_event:
            in_event = True
            event_start = date
        elif not is_soft and in_event:
            duration = (date - event_start).days // 90  # 約季度數
            if duration >= min_duration:
                events.append({
                    "start_date": event_start,
                    "end_date": date,
                    "duration_quarters": duration,
                    "ujo_at_start": data.loc[event_start, "UJO"] if "UJO" in data.columns else None,
                    "sahm_at_start": data.loc[event_start, "SAHM"] if "SAHM" in data.columns else None,
                    "delta_ur_at_start": data.loc[event_start, "DELTA_UR_6M"] if "DELTA_UR_6M" in data.columns else None
                })
            in_event = False

    return events


def filter_high_gdp_events(
    events: List[Dict],
    data: pd.DataFrame,
    gdp_threshold_pctl: float = 0.70
) -> List[Dict]:
    """
    篩選高 GDP 條件下的事件
    """
    gdp_pctl = compute_percentile_rank(data["GDP"])

    filtered = []
    for event in events:
        start = event["start_date"]
        if start in gdp_pctl.index:
            pctl = gdp_pctl.loc[start]
            if pctl >= gdp_threshold_pctl:
                event["gdp_percentile_at_start"] = pctl
                filtered.append(event)

    return filtered


# ============================================================
# 分析模型
# ============================================================

def event_study_banding(
    events: List[Dict],
    deficit_gdp: pd.Series,
    horizon_quarters: int = 8
) -> Dict:
    """
    事件分組區間法

    Parameters
    ----------
    events : list
        事件列表
    deficit_gdp : pd.Series
        赤字/GDP 時間序列
    horizon_quarters : int
        觀察期數

    Returns
    -------
    dict
        分析結果
    """
    forward_deficits = []

    for event in events:
        start = event["start_date"]
        end_date = start + pd.DateOffset(months=horizon_quarters * 3)

        # 取事件後的赤字峰值
        mask = (deficit_gdp.index >= start) & (deficit_gdp.index <= end_date)
        if mask.any():
            peak_deficit = deficit_gdp[mask].max()
            forward_deficits.append({
                "start": start,
                "deficit_peak": abs(peak_deficit),  # FRED 數據為負數表示赤字
                **event
            })

    if not forward_deficits:
        return {"error": "無有效事件樣本"}

    deficits = [d["deficit_peak"] for d in forward_deficits]

    return {
        "p25": np.percentile(deficits, 25),
        "p50": np.percentile(deficits, 50),
        "p75": np.percentile(deficits, 75),
        "min": min(deficits),
        "max": max(deficits),
        "n_episodes": len(deficits),
        "episodes": forward_deficits
    }


def quantile_mapping(
    current_slack: float,
    slack_series: pd.Series,
    deficit_gdp: pd.Series,
    epsilon: float = 0.10,
    horizon_quarters: int = 8
) -> Dict:
    """
    分位數映射法
    """
    # 計算當前 slack 的分位數
    current_pctl = (slack_series < current_slack).mean()

    # 找出相似時期
    all_pctl = compute_percentile_rank(slack_series)
    similar_mask = abs(all_pctl - current_pctl) < epsilon

    # 取這些時期的後續赤字
    forward_deficits = []
    for date in slack_series.index[similar_mask]:
        future_date = date + pd.DateOffset(months=horizon_quarters * 3)
        if future_date <= deficit_gdp.index.max():
            future_deficit = deficit_gdp.loc[:future_date].iloc[-1]
            forward_deficits.append(abs(future_deficit))

    if not forward_deficits:
        return {"error": "無相似時期樣本"}

    return {
        "current_percentile": current_pctl,
        "similar_periods_count": len(forward_deficits),
        "p25": np.percentile(forward_deficits, 25),
        "p50": np.percentile(forward_deficits, 50),
        "p75": np.percentile(forward_deficits, 75)
    }


# ============================================================
# 主分析函數
# ============================================================

def run_analysis(config: Dict = None) -> Dict:
    """
    執行完整分析

    Parameters
    ----------
    config : dict, optional
        配置參數，使用預設值補充缺失項

    Returns
    -------
    dict
        完整分析結果
    """
    # 合併配置
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    # Step 1: 抓取數據
    print("Step 1: 抓取 FRED 數據...")
    raw_data = fetch_multiple_series(REQUIRED_SERIES, years=cfg["lookback_years"])

    # Step 2: 數據對齊
    print("Step 2: 數據對齊到季度...")
    data = align_to_quarterly(raw_data, method="quarter_end")

    # Step 3: 計算指標
    print("Step 3: 計算勞動市場指標...")
    data["UJO"] = compute_ujo(data["UNEMPLOY"], data["JTSJOL"])

    # 需要月頻數據計算 Sahm 和 ΔUR
    monthly_ur = raw_data["UNRATE"].resample("ME").last()
    sahm_monthly = compute_sahm_rule(monthly_ur)
    delta_ur_monthly = compute_delta_ur(monthly_ur, periods=6)

    # 對齊到季度
    data["SAHM"] = sahm_monthly.resample("QE").last()
    data["DELTA_UR_6M"] = delta_ur_monthly.resample("QE").last()

    # 計算分位數
    ujo_pctl = compute_percentile_rank(data["UJO"])
    gdp_pctl = compute_percentile_rank(data["GDP"])

    # Step 4: 識別事件
    print("Step 4: 識別勞動轉弱事件...")
    events = identify_labor_softening_events(
        data,
        ujo_threshold_pctl=cfg["labor_soft_percentile_threshold"],
        sahm_threshold=cfg["sahm_threshold"],
        delta_ur_threshold=cfg["delta_ur_threshold"]
    )

    # 篩選高 GDP 事件
    high_gdp_events = filter_high_gdp_events(
        events, data,
        gdp_threshold_pctl=cfg["high_gdp_percentile_threshold"]
    )

    print(f"  找到 {len(events)} 個勞動轉弱事件")
    print(f"  其中 {len(high_gdp_events)} 個滿足高 GDP 條件")

    # Step 5: 執行分析模型
    print(f"Step 5: 執行 {cfg['model']} 分析...")

    # 赤字數據（取絕對值，因為 FRED 用負數表示赤字）
    deficit_gdp = data["FYFSGDA188S"].dropna()

    if cfg["model"] == "event_study_banding":
        projection = event_study_banding(
            high_gdp_events,
            deficit_gdp,
            horizon_quarters=cfg["horizon_quarters"]
        )
    elif cfg["model"] == "quantile_mapping":
        current_ujo = data["UJO"].dropna().iloc[-1]
        projection = quantile_mapping(
            current_ujo,
            data["UJO"].dropna(),
            deficit_gdp,
            horizon_quarters=cfg["horizon_quarters"]
        )
    else:
        projection = {"error": f"未知模型: {cfg['model']}"}

    # Step 6: 構建輸出
    print("Step 6: 構建輸出結果...")

    # 當前診斷
    latest = data.dropna(subset=["UJO"]).iloc[-1]
    latest_ujo_pctl = ujo_pctl.dropna().iloc[-1]
    latest_gdp_pctl = gdp_pctl.dropna().iloc[-1]

    # 判斷當前狀態
    triggered = (
        latest_ujo_pctl >= cfg["labor_soft_percentile_threshold"] or
        latest["SAHM"] >= cfg["sahm_threshold"] or
        latest["DELTA_UR_6M"] >= cfg["delta_ur_threshold"]
    )

    trigger_reasons = []
    if latest_ujo_pctl >= cfg["labor_soft_percentile_threshold"]:
        trigger_reasons.append("ujo_above_threshold")
    if latest["SAHM"] >= cfg["sahm_threshold"]:
        trigger_reasons.append("sahm_triggered")
    if latest["DELTA_UR_6M"] >= cfg["delta_ur_threshold"]:
        trigger_reasons.append("delta_ur_above_threshold")

    # 基線赤字
    baseline_deficit = abs(deficit_gdp.dropna().iloc[-1])

    # 構建結果
    result = {
        "skill": "analyze_high_unemployment_fiscal_deficit_scenarios",
        "version": "0.1.0",
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "inputs": cfg,
        "diagnostics": {
            "data_coverage": {
                "start_date": data.index.min().strftime("%Y-%m-%d"),
                "end_date": data.index.max().strftime("%Y-%m-%d"),
                "series_available": list(data.columns)
            },
            "current_indicators": {
                "unemployment_rate": float(raw_data["UNRATE"].dropna().iloc[-1]),
                "unemployed_level": float(latest["UNEMPLOY"]) if pd.notna(latest["UNEMPLOY"]) else None,
                "job_openings": float(latest["JTSJOL"]) if pd.notna(latest["JTSJOL"]) else None,
                "ujo_ratio": float(latest["UJO"]) if pd.notna(latest["UJO"]) else None,
                "sahm_rule": float(latest["SAHM"]) if pd.notna(latest["SAHM"]) else None,
                "delta_ur_6m": float(latest["DELTA_UR_6M"]) if pd.notna(latest["DELTA_UR_6M"]) else None
            },
            "current_slack_percentile": float(latest_ujo_pctl),
            "high_gdp_condition": bool(latest_gdp_pctl >= cfg["high_gdp_percentile_threshold"]),
            "gdp_percentile": float(latest_gdp_pctl),
            "triggered_labor_softening": bool(triggered),
            "trigger_reasons": trigger_reasons
        },
        "deficit_gdp_projection": {
            "baseline_deficit_gdp": float(baseline_deficit) / 100,  # 轉為小數
            "conditional_range_next_8q": {
                "p25": float(projection.get("p25", 0)) / 100 if "p25" in projection else None,
                "p50": float(projection.get("p50", 0)) / 100 if "p50" in projection else None,
                "p75": float(projection.get("p75", 0)) / 100 if "p75" in projection else None,
                "min": float(projection.get("min", 0)) / 100 if "min" in projection else None,
                "max": float(projection.get("max", 0)) / 100 if "max" in projection else None
            },
            "n_episodes": projection.get("n_episodes", 0),
            "episode_years": [
                f"{e['start_date'].year}-{e['start_date'].year + e['duration_quarters']//4 + 1}"
                for e in projection.get("episodes", [])
            ]
        },
        "interpretation": generate_interpretation(
            projection, baseline_deficit, triggered, latest_gdp_pctl
        ),
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_used": cfg["model"],
            "data_freshness": {
                col: data[col].dropna().index.max().strftime("%Y-%m-%d")
                for col in data.columns if data[col].dropna().any()
            }
        }
    }

    return result


def generate_interpretation(
    projection: Dict,
    baseline: float,
    triggered: bool,
    gdp_pctl: float
) -> Dict:
    """生成解讀文字"""

    p50 = projection.get("p50", baseline)
    n = projection.get("n_episodes", 0)

    macro_story = (
        f"在歷史上勞動市場明顯轉弱且 GDP 仍處高位的樣本中，"
        f"赤字/GDP 常出現階躍式上移，區間落在約 {projection.get('p25', 0):.0f}%–{projection.get('p75', 0):.0f}%"
        f"（中位數約 {p50:.1f}%）。"
    )

    if triggered:
        macro_story += (
            f"當前勞動市場已觸發轉弱條件，"
            f"而 GDP 仍處於 {gdp_pctl*100:.0f} 分位高位。"
        )
    else:
        macro_story += "當前勞動市場尚未觸發轉弱條件。"

    return {
        "macro_story": macro_story,
        "ust_duration_implications": [
            {
                "channel": "supply_pressure",
                "assessment": "高" if p50 > 12 else "中" if p50 > 8 else "低",
                "description": (
                    f"赤字/GDP 若進入 {p50:.0f}%+ 區間，通常意味更高的國債淨發行需求，"
                    "長端對期限溢酬變化更敏感。"
                )
            },
            {
                "channel": "risk_aversion",
                "assessment": "中等",
                "description": (
                    "若同時出現風險趨避（信用利差擴大、波動上升），"
                    "長端可能先被避險買盤壓低殖利率；需用風險指標判斷主導力量。"
                )
            }
        ],
        "watchlist_switch_indicators": [
            "信用利差/金融壓力指數是否急升（避險力道）",
            "通膨預期是否黏著（長端期限溢酬）",
            "國債拍賣尾差/投標倍數（供給壓力顯性化）",
            "Fed 政策立場（QE 暫停/重啟）",
            "股債相關性（轉負表示避險模式）"
        ]
    }


def run_quick_diagnosis() -> Dict:
    """執行快速診斷（簡化輸出）"""
    result = run_analysis()

    return {
        "skill": result["skill"],
        "as_of": result["as_of"],
        "state": {
            "current_slack_percentile": result["diagnostics"]["current_slack_percentile"],
            "high_gdp_condition": result["diagnostics"]["high_gdp_condition"],
            "triggered_labor_softening": result["diagnostics"]["triggered_labor_softening"]
        },
        "deficit_gdp_projection": {
            "baseline": result["deficit_gdp_projection"]["baseline_deficit_gdp"],
            "if_labor_softens": {
                "p25": result["deficit_gdp_projection"]["conditional_range_next_8q"]["p25"],
                "p50": result["deficit_gdp_projection"]["conditional_range_next_8q"]["p50"],
                "p75": result["deficit_gdp_projection"]["conditional_range_next_8q"]["p75"]
            }
        },
        "ust_risk_level": (
            "elevated" if result["diagnostics"]["triggered_labor_softening"] else "normal"
        ),
        "dominant_force": "supply_pressure"
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="高失業高GDP情境下的財政赤字分析器"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速診斷模式（簡化輸出）"
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=30,
        help="回看年數 (預設: 30)"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=8,
        help="推演季數 (預設: 8)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="event_study_banding",
        choices=["event_study_banding", "quantile_mapping"],
        help="分析模型 (預設: event_study_banding)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="自訂情境參數 (JSON 格式)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="輸出檔案路徑"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="json",
        choices=["json", "markdown"],
        help="輸出格式 (預設: json)"
    )

    args = parser.parse_args()

    # 構建配置
    config = {
        "lookback_years": args.lookback,
        "horizon_quarters": args.horizon,
        "model": args.model
    }

    if args.scenario:
        scenario = json.loads(args.scenario)
        config["scenario"] = scenario

    # 執行分析
    if args.quick:
        result = run_quick_diagnosis()
    else:
        result = run_analysis(config)

    # 輸出
    output_str = json.dumps(result, ensure_ascii=False, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"\n結果已保存至: {args.output}")
    else:
        print("\n分析結果:")
        print("=" * 60)
        print(output_str)


if __name__ == "__main__":
    main()
