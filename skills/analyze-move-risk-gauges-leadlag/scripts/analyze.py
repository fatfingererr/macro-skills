#!/usr/bin/env python3
"""
analyze.py - MOVE 風險指標領先落後分析

分析 MOVE 是否領先 VIX/Credit，以及是否對 JGB 衝擊「不恐慌」。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Import fetch utilities
from fetch_data import fetch_all_data

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG = {
    "smooth_window": 5,
    "zscore_window": 60,
    "lead_lag_max_days": 20,
    "shock_window_days": 5,
    "shock_threshold_bps": 15.0,
}


# =============================================================================
# Analysis Functions
# =============================================================================

def rolling_zscore(s: pd.Series, window: int) -> pd.Series:
    """
    計算滾動 Z 分數

    Parameters:
    -----------
    s : pd.Series
        輸入序列
    window : int
        滾動窗口

    Returns:
    --------
    pd.Series
        Z 分數序列
    """
    mu = s.rolling(window).mean()
    sd = s.rolling(window).std()
    return (s - mu) / sd


def crosscorr_leadlag(x: pd.Series, y: pd.Series, max_lag: int) -> tuple:
    """
    計算交叉相關，找出最佳 lag

    Parameters:
    -----------
    x : pd.Series
        第一個序列
    y : pd.Series
        第二個序列
    max_lag : int
        最大位移天數

    Returns:
    --------
    tuple (best_lag, best_corr)
        - best_lag > 0: x 領先 y
        - best_lag < 0: x 落後 y
    """
    best_lag, best_corr = 0, -np.inf

    for lag in range(-max_lag, max_lag + 1):
        corr = x.shift(lag).corr(y)
        if corr is not None and not np.isnan(corr) and corr > best_corr:
            best_corr, best_lag = corr, lag

    return best_lag, best_corr


def identify_shock_events(
    jgb: pd.Series,
    window: int,
    threshold_bps: float
) -> pd.Series:
    """
    識別 JGB 衝擊事件

    Parameters:
    -----------
    jgb : pd.Series
        JGB 10Y 殖利率
    window : int
        事件窗天數
    threshold_bps : float
        衝擊門檻 (bps)

    Returns:
    --------
    pd.Series (bool)
        衝擊事件標記
    """
    # 計算 window 日變化（bps）
    change_bps = (jgb - jgb.shift(window)) * 100
    # 標記衝擊
    shock = change_bps.abs() >= threshold_bps
    return shock


def compute_move_reaction(
    move: pd.Series,
    shock: pd.Series,
    window: int
) -> dict:
    """
    計算 MOVE 對衝擊事件的反應

    Parameters:
    -----------
    move : pd.Series
        MOVE 序列
    shock : pd.Series
        衝擊事件標記
    window : int
        事件窗天數

    Returns:
    --------
    dict
        反應統計
    """
    move_change = move - move.shift(window)
    reactions = move_change[shock].dropna()

    if len(reactions) == 0:
        return {
            "shock_count": 0,
            "mean_reaction": None,
            "median_reaction": None,
            "reactions": []
        }

    return {
        "shock_count": int(shock.sum()),
        "mean_reaction": float(reactions.mean()),
        "median_reaction": float(reactions.median()),
        "reactions": reactions.tolist()
    }


def compute_direction_alignment(df: pd.DataFrame) -> dict:
    """
    計算方向一致性

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ["MOVE", "VIX", "CREDIT"]

    Returns:
    --------
    dict
        同向比例
    """
    d = df.diff()
    move_down = d["MOVE"] < 0
    move_down_count = move_down.sum()

    if move_down_count == 0:
        return {
            "MOVE_down_and_VIX_down_ratio": None,
            "MOVE_down_and_CREDIT_down_ratio": None
        }

    vix_down = d["VIX"] < 0
    credit_down = d["CREDIT"] < 0

    return {
        "MOVE_down_and_VIX_down_ratio": round(float((move_down & vix_down).sum() / move_down_count), 2),
        "MOVE_down_and_CREDIT_down_ratio": round(float((move_down & credit_down).sum() / move_down_count), 2)
    }


def generate_headline(leadlag: dict, spooked: dict, alignment: dict) -> str:
    """
    生成一句話結論

    Parameters:
    -----------
    leadlag : dict
        領先落後分析結果
    spooked : dict
        恐慌檢定結果
    alignment : dict
        方向一致性結果

    Returns:
    --------
    str
        一句話結論
    """
    parts = []

    # 恐慌檢定
    mean_reaction = spooked.get("mean_MOVE_reaction_on_shocks")
    if mean_reaction is None or mean_reaction < 1.0:
        parts.append("MOVE not spooked by JGB yield moves")
    else:
        parts.append("MOVE appears spooked by JGB yield moves")

    # 領先判定
    move_vs_vix = leadlag.get("MOVE_vs_VIX", {}).get("best_lag_days", 0)
    move_vs_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("best_lag_days", 0)

    if move_vs_vix > 0 and move_vs_credit > 0:
        parts.append("and appears to lead VIX/Credit lower")
    elif move_vs_vix < 0 or move_vs_credit < 0:
        parts.append("but may lag VIX/Credit")
    else:
        parts.append("and moves in sync with VIX/Credit")

    return " ".join(parts) + "."


def determine_confidence(leadlag: dict, alignment: dict) -> str:
    """
    判斷信心水準

    Parameters:
    -----------
    leadlag : dict
        領先落後分析結果
    alignment : dict
        方向一致性結果

    Returns:
    --------
    str
        "HIGH", "MEDIUM", or "LOW"
    """
    corr_vix = leadlag.get("MOVE_vs_VIX", {}).get("corr", 0)
    corr_credit = leadlag.get("MOVE_vs_CREDIT", {}).get("corr", 0)
    align_vix = alignment.get("MOVE_down_and_VIX_down_ratio", 0) or 0
    align_credit = alignment.get("MOVE_down_and_CREDIT_down_ratio", 0) or 0

    if corr_vix > 0.7 and corr_credit > 0.6 and align_vix > 0.5:
        return "HIGH"
    elif corr_vix > 0.5 and align_vix > 0.4:
        return "MEDIUM"
    else:
        return "LOW"


# =============================================================================
# Main Analysis Function
# =============================================================================

def analyze(
    df: pd.DataFrame,
    smooth_window: int = 5,
    zscore_window: int = 60,
    lead_lag_max_days: int = 20,
    shock_window_days: int = 5,
    shock_threshold_bps: float = 15.0
) -> dict:
    """
    完整的利率波動率領先落後分析

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ["MOVE", "VIX", "CREDIT", "JGB10Y"]
    smooth_window : int
        平滑窗口
    zscore_window : int
        Z 分數窗口
    lead_lag_max_days : int
        最大 lag 天數
    shock_window_days : int
        事件窗天數
    shock_threshold_bps : float
        衝擊門檻 (bps)

    Returns:
    --------
    dict
        分析結果
    """
    # 1. 對齊
    df = df.sort_index()
    df.index = pd.to_datetime(df.index)
    df = df.ffill()

    # 2. 平滑
    if smooth_window > 0:
        df_s = df.rolling(smooth_window).mean()
    else:
        df_s = df.copy()

    # 3. Z 分數
    df_z = df_s.apply(lambda c: rolling_zscore(c, zscore_window))

    # 4. Lead/Lag
    lag_vix, corr_vix = crosscorr_leadlag(df_s["MOVE"], df_s["VIX"], lead_lag_max_days)
    lag_cr, corr_cr = crosscorr_leadlag(df_s["MOVE"], df_s["CREDIT"], lead_lag_max_days)

    leadlag = {
        "MOVE_vs_VIX": {
            "best_lag_days": int(lag_vix),
            "corr": round(corr_vix, 3),
            "interpretation": f"MOVE {'leads' if lag_vix > 0 else 'lags'} VIX by ~{abs(lag_vix)} trading days"
        },
        "MOVE_vs_CREDIT": {
            "best_lag_days": int(lag_cr),
            "corr": round(corr_cr, 3),
            "interpretation": f"MOVE {'leads' if lag_cr > 0 else 'lags'} Credit by ~{abs(lag_cr)} trading days"
        }
    }

    # 5. 事件窗檢定
    shock = identify_shock_events(df_s["JGB10Y"], shock_window_days, shock_threshold_bps)
    shock_dates = df_s.index[shock].strftime("%Y-%m-%d").tolist()

    move_react = df_s["MOVE"] - df_s["MOVE"].shift(shock_window_days)
    reactions = move_react[shock].dropna()

    move_z_now = df_z["MOVE"].iloc[-1] if not df_z["MOVE"].isna().all() else None

    spooked_check = {
        "shock_definition": f"abs(JGB10Y change over {shock_window_days}d) >= {shock_threshold_bps}bp",
        "shock_count": int(shock.sum()),
        "shock_dates": shock_dates,
        "mean_MOVE_reaction_on_shocks": round(float(reactions.mean()), 2) if len(reactions) else None,
        "median_MOVE_reaction_on_shocks": round(float(reactions.median()), 2) if len(reactions) else None,
        "MOVE_zscore_now": round(float(move_z_now), 2) if move_z_now is not None and not np.isnan(move_z_now) else None,
        "spooked_verdict": "NOT_SPOOKED" if (len(reactions) == 0 or reactions.mean() < 1.0) else "SPOOKED"
    }

    # 6. 方向一致性
    alignment = compute_direction_alignment(df_s)

    # 7. 生成結論
    headline = generate_headline(leadlag, spooked_check, alignment)
    confidence = determine_confidence(leadlag, alignment)

    # 8. 生成理由
    reasons = []
    mean_reaction = spooked_check.get("mean_MOVE_reaction_on_shocks")
    if mean_reaction is not None:
        reasons.append(f"MOVE reaction to JGB shocks (mean {mean_reaction:+.1f}) is {'below' if mean_reaction < 1.0 else 'above'} typical levels")
    reasons.append(f"MOVE vs VIX cross-correlation peaks at lag +{lag_vix} days with corr {corr_vix:.2f}")
    reasons.append(f"MOVE vs Credit cross-correlation peaks at lag +{lag_cr} days with corr {corr_cr:.2f}")
    align_vix = alignment.get("MOVE_down_and_VIX_down_ratio")
    if align_vix is not None:
        reasons.append(f"Direction alignment: {align_vix*100:.0f}% of MOVE declines are accompanied by VIX declines")

    # 9. 數據品質
    data_quality = {
        "total_observations": len(df),
        "missing_ratio": {col: round(df[col].isna().mean(), 3) for col in df.columns},
        "warnings": []
    }

    return {
        "skill": "analyze-move-risk-gauges-leadlag",
        "version": "0.1.0",
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "status": "ok",
        "headline": headline,
        "confidence": confidence,
        "leadlag": leadlag,
        "spooked_check": spooked_check,
        "direction_alignment": alignment,
        "reasons": reasons,
        "data_quality": data_quality,
        "notes": []
    }


# =============================================================================
# Output Formatting
# =============================================================================

def format_markdown(result: dict) -> str:
    """將結果格式化為 Markdown"""
    lines = [
        f"# Rates Vol Lead/Lag Check (MOVE vs VIX vs Credit) — Summary",
        "",
        f"**分析日期**: {result['as_of']}",
        f"**信心水準**: {result['confidence']}",
        "",
        "---",
        "",
        "## 結論",
        ""
    ]

    # 結論部分
    spooked = result['spooked_check']
    leadlag = result['leadlag']
    alignment = result['direction_alignment']

    spooked_verdict = "偏弱 / 未顯著升溫" if spooked['spooked_verdict'] == "NOT_SPOOKED" else "明顯上升"
    lines.append(f"- 利率波動率（MOVE）對「JGB 殖利率衝擊」反應{spooked_verdict} → **{spooked['spooked_verdict'].replace('_', ' ').lower()}**")

    lag_vix = leadlag['MOVE_vs_VIX']['best_lag_days']
    lag_credit = leadlag['MOVE_vs_CREDIT']['best_lag_days']
    if lag_vix > 0 and lag_credit > 0:
        lead_text = f"領先 {min(lag_vix, lag_credit)}-{max(lag_vix, lag_credit)} 天"
    else:
        lead_text = "無明確領先"
    lines.append(f"- MOVE 的變化在統計上呈現 **{lead_text}** 的特徵")

    align_vix = alignment.get('MOVE_down_and_VIX_down_ratio')
    align_credit = alignment.get('MOVE_down_and_CREDIT_down_ratio')
    if align_vix and align_credit:
        lines.append(f"- MOVE 下行時，VIX / 信用利差同步走低的比例：VIX = {align_vix*100:.0f}%、Credit = {align_credit*100:.0f}%")

    lines.extend([
        "",
        "---",
        "",
        "## 證據（量化）",
        "",
        "### 領先落後分析",
        "",
        "| 指標對 | 最佳 Lag | 相關係數 | 解讀 |",
        "|--------|----------|----------|------|",
        f"| MOVE vs VIX | +{lag_vix} 天 | {leadlag['MOVE_vs_VIX']['corr']} | {leadlag['MOVE_vs_VIX']['interpretation']} |",
        f"| MOVE vs Credit | +{lag_credit} 天 | {leadlag['MOVE_vs_CREDIT']['corr']} | {leadlag['MOVE_vs_CREDIT']['interpretation']} |",
        "",
        "### 事件窗檢定",
        "",
        "| 項目 | 數值 |",
        "|------|------|",
        f"| 衝擊定義 | {spooked['shock_definition']} |",
        f"| 衝擊事件數 | {spooked['shock_count']} 次 |",
        f"| MOVE 平均反應 | {spooked['mean_MOVE_reaction_on_shocks']} |",
        f"| MOVE 當前 Z 分數 | {spooked['MOVE_zscore_now']} |",
        f"| 判定 | {spooked['spooked_verdict']} |",
        "",
        "---",
        "",
        "## 一句話摘要",
        "",
        f"> {result['headline']}",
        "",
        "---",
        "",
        f"*Generated by analyze-move-risk-gauges-leadlag v{result['version']}*"
    ])

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Analyze rates volatility lead/lag relationships")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--quick", action="store_true", help="Quick check (last 6 months)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--output-mode", choices=["json", "markdown"], default="markdown", help="Output format")
    parser.add_argument("--chart", action="store_true", help="Generate Bloomberg-style visualization chart")
    parser.add_argument("--chart-output", help="Chart output path (default: output/move-leadlag-YYYY-MM-DD.png)")
    parser.add_argument("--rates-chart", action="store_true", help="Generate rates vs MOVE panic analysis chart")
    parser.add_argument("--rates-chart-output", help="Rates chart output path")
    parser.add_argument("--rates-col", default="JGB10Y", help="Column name for rates data (default: JGB10Y)")
    parser.add_argument("--rates-name", default="JGB 10Y", help="Display name for rates (default: JGB 10Y)")
    parser.add_argument("--smooth-window", type=int, default=5, help="Smoothing window")
    parser.add_argument("--zscore-window", type=int, default=60, help="Z-score window")
    parser.add_argument("--lead-lag-max-days", type=int, default=20, help="Max lead/lag days")
    parser.add_argument("--shock-window-days", type=int, default=5, help="Shock window days")
    parser.add_argument("--shock-threshold-bps", type=float, default=15.0, help="Shock threshold (bps)")

    args = parser.parse_args()

    # Determine date range
    if args.quick:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - pd.DateOffset(months=6)).strftime("%Y-%m-%d")
    else:
        if not args.start or not args.end:
            print("Error: --start and --end are required (or use --quick)")
            sys.exit(1)
        start_date = args.start
        end_date = args.end

    print(f"Analyzing: {start_date} to {end_date}")

    # Fetch data
    df = fetch_all_data(start_date, end_date)

    if df.empty:
        print("Error: No data fetched")
        sys.exit(1)

    # Run analysis
    result = analyze(
        df,
        smooth_window=args.smooth_window,
        zscore_window=args.zscore_window,
        lead_lag_max_days=args.lead_lag_max_days,
        shock_window_days=args.shock_window_days,
        shock_threshold_bps=args.shock_threshold_bps
    )

    # Add params to result
    result["params"] = {
        "start_date": start_date,
        "end_date": end_date,
        "smooth_window": args.smooth_window,
        "zscore_window": args.zscore_window,
        "lead_lag_max_days": args.lead_lag_max_days,
        "shock_window_days": args.shock_window_days,
        "shock_threshold_bps": args.shock_threshold_bps
    }

    # Format output
    if args.output_mode == "json":
        output = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        output = format_markdown(result)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Result saved to {args.output}")
    else:
        print(output)

    # Generate chart if requested
    if args.chart:
        try:
            from visualize import create_bloomberg_chart
            chart_path = args.chart_output
            if not chart_path:
                # 使用專案根目錄的 output/
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                chart_path = project_root / "output" / f"move-leadlag-{datetime.now().strftime('%Y-%m-%d')}.png"
            create_bloomberg_chart(df, result, str(chart_path))
        except ImportError as e:
            print(f"Warning: Could not generate chart - {e}")

    # Generate rates vs MOVE panic chart if requested
    if args.rates_chart:
        try:
            from visualize_rates_move import create_rates_move_chart
            rates_chart_path = args.rates_chart_output
            if not rates_chart_path:
                # 使用專案根目錄的 output/
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                safe_rates_name = args.rates_name.lower().replace(" ", "-").replace("/", "-")
                rates_chart_path = project_root / "output" / f"{safe_rates_name}-move-panic-{datetime.now().strftime('%Y-%m-%d')}.png"
            create_rates_move_chart(
                df, result, str(rates_chart_path),
                rates_col=args.rates_col,
                rates_name=args.rates_name
            )
        except ImportError as e:
            print(f"Warning: Could not generate rates chart - {e}")


if __name__ == "__main__":
    main()
