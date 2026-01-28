#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天然氣→化肥因果假說分析器

用日頻價格數據檢驗「天然氣暴漲→化肥供應受限→化肥飆價」敘事是否成立。

Usage:
    python gas_fertilizer_analyzer.py \
        --gas-file ../data/natural_gas.csv \
        --fert-file ../data/urea.csv \
        --start 2025-08-01 \
        --end 2026-02-01 \
        --output ../data/analysis_result.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import signal


# ============================================================================
# 配置
# ============================================================================

DEFAULT_CONFIG = {
    "return_window": 1,
    "z_window": 60,
    "z_threshold": 3.0,
    "slope_window": 20,
    "slope_threshold": 0.015,  # 1.5% per day
    "max_lag_days": 60,
    "reasonable_lag_range": (7, 56),
}


# ============================================================================
# 數據載入
# ============================================================================

def load_series(file_path: str, date_col: str = "date", value_col: str = "value") -> pd.Series:
    """載入時間序列數據"""
    df = pd.read_csv(file_path)

    # 嘗試多種日期列名
    date_candidates = [date_col, "DATE", "Date", "datetime", "Datetime"]
    for col in date_candidates:
        if col in df.columns:
            date_col = col
            break

    # 嘗試多種值列名
    value_candidates = [value_col, "VALUE", "Value", "close", "Close", "price", "Price"]
    for col in value_candidates:
        if col in df.columns:
            value_col = col
            break

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)

    return df[value_col].astype(float)


def align_series(gas: pd.Series, fert: pd.Series) -> pd.DataFrame:
    """對齊兩個時間序列"""
    df = pd.DataFrame({"gas": gas, "fert": fert})
    df = df.sort_index()
    df = df.ffill()  # forward-fill 缺值
    df = df.dropna()
    return df


# ============================================================================
# Shock 偵測
# ============================================================================

def compute_returns(series: pd.Series, window: int = 1) -> pd.Series:
    """計算報酬率"""
    return series.pct_change(window)


def compute_rolling_zscore(returns: pd.Series, window: int = 60) -> pd.Series:
    """計算 rolling z-score"""
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()
    z = (returns - rolling_mean) / rolling_std
    return z


def compute_slope(prices: pd.Series, window: int = 20) -> pd.Series:
    """計算斜率代理（日均漲幅）"""
    slope = (prices / prices.shift(window) - 1) / window
    return slope


def detect_shock(
    prices: pd.Series,
    config: Dict
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    偵測 shock

    Returns:
        (z_scores, slopes, is_shock)
    """
    returns = compute_returns(prices, config["return_window"])
    z_scores = compute_rolling_zscore(returns, config["z_window"])
    slopes = compute_slope(prices, config["slope_window"])

    is_shock = (z_scores >= config["z_threshold"]) | (slopes >= config["slope_threshold"])

    return z_scores, slopes, is_shock


def compress_to_regimes(
    df: pd.DataFrame,
    shock_col: str,
    value_col: str
) -> List[Dict]:
    """
    將布林值序列壓縮為 regime 清單
    """
    regimes = []
    in_regime = False
    current = None

    for idx, row in df.iterrows():
        if row[shock_col] and not in_regime:
            # 新 regime 開始
            in_regime = True
            current = {
                "start": idx.strftime("%Y-%m-%d"),
                "end": idx.strftime("%Y-%m-%d"),
                "peak_value": row[value_col],
                "peak_date": idx.strftime("%Y-%m-%d"),
                "start_value": row[value_col],
                "_peak_idx": idx,
                "_start_idx": idx,
            }
        elif row[shock_col] and in_regime:
            # 延續 regime
            current["end"] = idx.strftime("%Y-%m-%d")
            if row[value_col] > current["peak_value"]:
                current["peak_value"] = row[value_col]
                current["peak_date"] = idx.strftime("%Y-%m-%d")
                current["_peak_idx"] = idx
        elif not row[shock_col] and in_regime:
            # Regime 結束
            in_regime = False
            current["regime_return_pct"] = round(
                (current["peak_value"] / current["start_value"] - 1) * 100, 1
            )
            current["duration_days"] = (
                pd.to_datetime(current["end"]) - pd.to_datetime(current["start"])
            ).days + 1

            # 移除內部欄位
            del current["_peak_idx"]
            del current["_start_idx"]

            regimes.append(current)
            current = None

    # 處理未結束的 regime
    if in_regime and current:
        current["regime_return_pct"] = round(
            (current["peak_value"] / current["start_value"] - 1) * 100, 1
        )
        current["duration_days"] = (
            pd.to_datetime(current["end"]) - pd.to_datetime(current["start"])
        ).days + 1
        del current["_peak_idx"]
        del current["_start_idx"]
        regimes.append(current)

    return regimes


# ============================================================================
# 領先落後分析
# ============================================================================

def cross_correlation_analysis(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 60
) -> Dict:
    """
    計算 x 與 y 的交叉相關

    Returns:
        {
            "best_lag": int,   # 正值表示 x 領先 y
            "best_corr": float,
            "corr_at_zero_lag": float
        }
    """
    # 對齊並去除 NaN
    combined = pd.DataFrame({"x": x, "y": y}).dropna()
    x_clean = combined["x"].values
    y_clean = combined["y"].values

    if len(x_clean) < 10:
        return {
            "best_lag": 0,
            "best_corr": 0.0,
            "corr_at_zero_lag": 0.0,
            "error": "數據點不足"
        }

    # 標準化
    x_norm = (x_clean - x_clean.mean()) / x_clean.std()
    y_norm = (y_clean - y_clean.mean()) / y_clean.std()

    # 計算交叉相關
    corr = signal.correlate(x_norm, y_norm, mode='full')
    lags = signal.correlation_lags(len(x_norm), len(y_norm), mode='full')

    # 正規化
    corr = corr / len(x_norm)

    # 限制在 max_lag 範圍內
    mask = (lags >= -max_lag) & (lags <= max_lag)
    lags_filtered = lags[mask]
    corr_filtered = corr[mask]

    # 找最大
    best_idx = np.argmax(np.abs(corr_filtered))
    best_lag = int(lags_filtered[best_idx])
    best_corr = float(corr_filtered[best_idx])

    # 零 lag 相關
    zero_idx = np.where(lags_filtered == 0)[0]
    corr_at_zero = float(corr_filtered[zero_idx[0]]) if len(zero_idx) > 0 else 0.0

    return {
        "best_lag": best_lag,
        "best_corr": round(best_corr, 3),
        "corr_at_zero_lag": round(corr_at_zero, 3)
    }


# ============================================================================
# 三段式因果檢驗
# ============================================================================

def three_part_test(
    gas_regimes: List[Dict],
    fert_regimes: List[Dict],
    lead_lag: Dict,
    config: Dict
) -> Dict:
    """
    執行三段式因果檢驗

    A: 天然氣出現 shock？
    B: 化肥在 A 之後出現 spike？
    C: Lead-lag 支持因果？
    """
    # A 段
    A_pass = len(gas_regimes) > 0
    A_info = {
        "pass": A_pass,
        "regime_count": len(gas_regimes),
        "max_return_pct": max((r["regime_return_pct"] for r in gas_regimes), default=0),
        "total_days": sum(r["duration_days"] for r in gas_regimes)
    }

    # B 段
    B_pass = False
    B_lag_days = None
    if A_pass and len(fert_regimes) > 0:
        for fert_r in fert_regimes:
            for gas_r in gas_regimes:
                fert_start = pd.to_datetime(fert_r["start"])
                gas_start = pd.to_datetime(gas_r["start"])
                if fert_start > gas_start:
                    B_pass = True
                    B_lag_days = (fert_start - gas_start).days
                    break
            if B_pass:
                break

    B_info = {
        "pass": B_pass,
        "fert_start_after_gas_start": B_pass,
        "lag_days": B_lag_days,
        "explanation": f"化肥 spike 起點晚於天然氣 shock 起點約 {B_lag_days} 天" if B_pass else "化肥未在天然氣 shock 後上漲"
    }

    # C 段
    best_lag = lead_lag.get("best_lag", 0)
    best_corr = lead_lag.get("best_corr", 0)
    min_lag, max_lag = config["reasonable_lag_range"]

    C_lag_in_range = min_lag <= best_lag <= max_lag
    C_corr_significant = abs(best_corr) >= 0.3
    C_pass = C_lag_in_range and best_lag > 0  # 必須是 gas 領先

    C_info = {
        "pass": C_pass,
        "lag_in_range": C_lag_in_range,
        "corr_significant": C_corr_significant,
        "explanation": f"best_lag={best_lag} 在合理範圍 [{min_lag},{max_lag}] 內" if C_pass else f"best_lag={best_lag} 不支持 gas 領先 fert"
    }

    return {
        "A_gas_shock": A_info,
        "B_fert_follows": B_info,
        "C_lead_lag_supports": C_info
    }


def determine_signal(test_result: Dict, lead_lag: Dict) -> Tuple[str, str]:
    """
    根據三段式檢驗結果判斷 signal 和 confidence
    """
    A_pass = test_result["A_gas_shock"]["pass"]
    B_pass = test_result["B_fert_follows"]["pass"]
    C_pass = test_result["C_lead_lag_supports"]["pass"]
    corr = abs(lead_lag.get("best_corr", 0))

    if A_pass and B_pass and C_pass:
        signal = "narrative_supported"
        confidence = "high" if corr > 0.5 else "medium"
    elif A_pass and B_pass:
        signal = "narrative_supported"
        confidence = "low"
    elif A_pass:
        signal = "narrative_weak"
        confidence = "low"
    else:
        signal = "inconclusive"
        confidence = "low"

    return signal, confidence


# ============================================================================
# 主程式
# ============================================================================

def analyze(
    gas_file: str,
    fert_file: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    config: Optional[Dict] = None
) -> Dict:
    """
    執行完整分析
    """
    config = {**DEFAULT_CONFIG, **(config or {})}

    # 載入數據
    gas = load_series(gas_file)
    fert = load_series(fert_file)

    # 對齊
    df = align_series(gas, fert)

    # 篩選日期範圍
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]

    # Shock 偵測
    df["gas_z"], df["gas_slope"], df["gas_shock"] = detect_shock(df["gas"], config)
    df["fert_z"], df["fert_slope"], df["fert_spike"] = detect_shock(df["fert"], config)

    # Regime 合併
    gas_regimes = compress_to_regimes(df, "gas_shock", "gas")
    fert_regimes = compress_to_regimes(df, "fert_spike", "fert")

    # 領先落後分析
    gas_ret = compute_returns(df["gas"], config["return_window"])
    fert_ret = compute_returns(df["fert"], config["return_window"])
    lead_lag = cross_correlation_analysis(gas_ret, fert_ret, config["max_lag_days"])

    # 三段式檢驗
    test_result = three_part_test(gas_regimes, fert_regimes, lead_lag, config)
    signal, confidence = determine_signal(test_result, lead_lag)

    # 組裝結果
    result = {
        "metadata": {
            "skill_name": "analyze-gas-fertilizer-contract-shock",
            "skill_version": "0.1.0",
            "analysis_timestamp": datetime.now().isoformat() + "Z",
            "parameters": {
                "start_date": start_date or str(df.index.min().date()),
                "end_date": end_date or str(df.index.max().date()),
                "freq": "1D"
            }
        },
        "series": {
            "natural_gas": {
                "symbol": Path(gas_file).stem,
                "source": "TradingEconomics",
                "unit": "USD/MMBtu",
                "data_points": len(df),
                "date_range": [str(df.index.min().date()), str(df.index.max().date())]
            },
            "fertilizer": {
                "symbol": Path(fert_file).stem,
                "source": "TradingEconomics",
                "unit": "USD/ton",
                "data_points": len(df),
                "date_range": [str(df.index.min().date()), str(df.index.max().date())]
            }
        },
        "detections": {
            "gas_shock_regimes": gas_regimes,
            "fert_spike_regimes": fert_regimes
        },
        "lead_lag_test": {
            "method": "corr_returns",
            "max_lag_days": config["max_lag_days"],
            "best_lag_days_gas_leads_fert": lead_lag["best_lag"],
            "best_corr": lead_lag["best_corr"],
            "corr_at_zero_lag": lead_lag["corr_at_zero_lag"],
            "reasonable_lag_range": list(config["reasonable_lag_range"]),
            "in_reasonable_range": config["reasonable_lag_range"][0] <= lead_lag["best_lag"] <= config["reasonable_lag_range"][1],
            "interpretation": f"天然氣報酬{'領先' if lead_lag['best_lag'] > 0 else '落後'}化肥報酬約 {abs(lead_lag['best_lag'])} 天，相關係數為{'高度' if abs(lead_lag['best_corr']) > 0.5 else '中度' if abs(lead_lag['best_corr']) > 0.3 else '低度'}"
        },
        "three_part_test": test_result,
        "signal": signal,
        "confidence": confidence,
        "narrative_assessment": {
            "summary": "三段式因果檢驗通過，敘事有量化支撐" if signal == "narrative_supported" else "敘事在數據上支撐較弱",
            "details": [],
            "alternative_explanations": [
                "化肥 spike 可能還受其他因素影響（運費、需求、政策）",
                f"相關係數 {lead_lag['best_corr']} 為{'中度' if abs(lead_lag['best_corr']) > 0.3 else '低度'}，部分變異來自其他驅動因素"
            ]
        },
        "caveats": [
            "數據來源可能與交易所官方數據有差異",
            "日頻數據可能有缺失，已使用 forward-fill 處理",
            "相關不代表因果，需配合機制分析",
            "本分析不構成任何投資建議"
        ]
    }

    # 填充 details
    if gas_regimes:
        result["narrative_assessment"]["details"].append(
            f"天然氣出現 {len(gas_regimes)} 個 shock regime"
        )
    if fert_regimes:
        result["narrative_assessment"]["details"].append(
            f"化肥出現 {len(fert_regimes)} 個 spike regime"
        )
    result["narrative_assessment"]["details"].append(
        f"交叉相關顯示 gas {'領先' if lead_lag['best_lag'] > 0 else '落後'} fert 約 {abs(lead_lag['best_lag'])} 天"
    )

    return result


def main():
    parser = argparse.ArgumentParser(description="天然氣→化肥因果假說分析器")
    parser.add_argument("--gas-file", required=True, help="天然氣數據檔案路徑")
    parser.add_argument("--fert-file", required=True, help="化肥數據檔案路徑")
    parser.add_argument("--start", help="分析起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", help="分析結束日期 (YYYY-MM-DD)")
    parser.add_argument("--z-window", type=int, default=60, help="Rolling z-score 視窗")
    parser.add_argument("--z-threshold", type=float, default=3.0, help="Z-score 閾值")
    parser.add_argument("--slope-threshold", type=float, default=1.5, help="斜率閾值 (%%/day)")
    parser.add_argument("--output", default="../data/analysis_result.json", help="輸出檔案路徑")
    parser.add_argument("--quick", action="store_true", help="快速模式")

    args = parser.parse_args()

    config = {
        **DEFAULT_CONFIG,
        "z_window": args.z_window,
        "z_threshold": args.z_threshold,
        "slope_threshold": args.slope_threshold / 100,
    }

    result = analyze(
        gas_file=args.gas_file,
        fert_file=args.fert_file,
        start_date=args.start,
        end_date=args.end,
        config=config
    )

    # 輸出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分析完成！結果已儲存至: {output_path}")
    print(f"Signal: {result['signal']} (Confidence: {result['confidence']})")


if __name__ == "__main__":
    main()
