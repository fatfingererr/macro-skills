#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上海白銀庫存耗盡訊號偵測器

量化上海白銀庫存耗盡的方向、速度與加速度，
並將其轉成可交易的供給緊縮訊號。

Usage:
    # 快速檢查
    python drain_detector.py --quick

    # 完整分析
    python drain_detector.py --start 2020-01-01 --end 2026-01-16 --output result.json
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# 設定專案根目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"


@dataclass
class DrainConfig:
    """耗盡偵測配置"""
    start_date: str = ""
    end_date: str = ""
    frequency: str = "weekly"
    include_sources: List[str] = None
    unit: str = "tonnes"
    smoothing_window_weeks: int = 4
    z_score_window_weeks: int = 156
    drain_threshold_z: float = -1.5
    accel_threshold_z: float = 1.0
    level_percentile_threshold: float = 0.20
    confirm_with_markets: bool = True

    def __post_init__(self):
        if self.include_sources is None:
            self.include_sources = ["SGE", "SHFE"]
        if not self.start_date:
            self.start_date = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")
        if not self.end_date:
            self.end_date = datetime.now().strftime("%Y-%m-%d")


@dataclass
class DrainResult:
    """耗盡分析結果"""
    skill: str = "detect_shanghai_silver_stock_drain"
    as_of: str = ""
    unit: str = "tonnes"
    sources: List[str] = None
    latest_combined_stock: float = 0.0
    level_percentile: float = 0.0
    delta1_weekly: float = 0.0
    drain_rate_4w_avg: float = 0.0
    acceleration_4w_avg: float = 0.0
    z_drain_rate: float = 0.0
    z_acceleration: float = 0.0
    signal_conditions: Dict[str, bool] = None
    signal: str = "NO_SIGNAL"
    narrative: List[str] = None
    caveats: List[str] = None


def load_stock_data(sources: List[str]) -> pd.DataFrame:
    """
    載入庫存數據

    Parameters
    ----------
    sources : list
        庫存來源 ["SGE", "SHFE"]

    Returns
    -------
    pd.DataFrame
        合併的庫存時間序列
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    dfs = []

    if "SGE" in sources:
        sge_path = DATA_DIR / "sge_stock.csv"
        if sge_path.exists():
            df_sge = pd.read_csv(sge_path, parse_dates=["date"])
            df_sge = df_sge.rename(columns={"stock_kg": "sge_kg"})
            dfs.append(df_sge)
        else:
            print(f"警告: SGE 數據檔案不存在 ({sge_path})")
            print("請先執行: python fetch_sge_stock.py")

    if "SHFE" in sources:
        shfe_path = DATA_DIR / "shfe_stock.csv"
        if shfe_path.exists():
            df_shfe = pd.read_csv(shfe_path, parse_dates=["date"])
            df_shfe = df_shfe.rename(columns={"stock_kg": "shfe_kg"})
            dfs.append(df_shfe)
        else:
            print(f"警告: SHFE 數據檔案不存在 ({shfe_path})")
            print("請先執行: python fetch_shfe_stock.py")

    if not dfs:
        # 如果沒有真實數據，生成模擬數據（開發/測試用）
        print("未找到真實數據，使用模擬數據...")
        return generate_mock_data()

    # 合併數據
    if len(dfs) == 1:
        df = dfs[0]
    else:
        df = pd.merge(dfs[0], dfs[1], on="date", how="outer")

    return df.sort_values("date").reset_index(drop=True)


def generate_mock_data() -> pd.DataFrame:
    """
    生成模擬數據（開發/測試用）

    Returns
    -------
    pd.DataFrame
        模擬的庫存時間序列
    """
    # 生成 3 年週度數據
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=3*365),
        end=datetime.now(),
        freq="W"
    )

    # 模擬庫存走勢：基線 + 趨勢 + 噪音
    np.random.seed(42)
    n = len(dates)

    # 基線：2000 噸
    baseline = 2000

    # 下降趨勢：每週減少 5-15 噸
    trend = np.linspace(0, -800, n)

    # 週期性波動
    seasonal = 100 * np.sin(np.linspace(0, 6*np.pi, n))

    # 隨機噪音
    noise = np.random.normal(0, 30, n)

    # 合成庫存（kg）
    sge_kg = (baseline + trend + seasonal + noise) * 1000
    shfe_kg = sge_kg * 0.3 + np.random.normal(0, 10000, n)  # SHFE 約為 SGE 的 30%

    df = pd.DataFrame({
        "date": dates,
        "sge_kg": np.maximum(sge_kg, 500000),  # 最低 500 噸
        "shfe_kg": np.maximum(shfe_kg, 100000)  # 最低 100 噸
    })

    return df


def build_combined_stock(df: pd.DataFrame, unit: str = "tonnes") -> pd.DataFrame:
    """
    合併 SGE + SHFE 庫存

    Parameters
    ----------
    df : pd.DataFrame
        包含 sge_kg 和/或 shfe_kg 欄位的 DataFrame
    unit : str
        輸出單位 (tonnes, kg, troy_oz)

    Returns
    -------
    pd.DataFrame
        包含合併庫存的 DataFrame
    """
    df = df.copy()

    # 計算合併庫存 (kg)
    sge = df.get("sge_kg", pd.Series(0, index=df.index)).fillna(0)
    shfe = df.get("shfe_kg", pd.Series(0, index=df.index)).fillna(0)
    df["combined_kg"] = sge + shfe

    # 單位轉換
    if unit == "tonnes":
        df["combined"] = df["combined_kg"] / 1000.0
    elif unit == "troy_oz":
        df["combined"] = (df["combined_kg"] / 1000.0) * 32150.7466
    else:  # kg
        df["combined"] = df["combined_kg"]

    return df.sort_values("date").reset_index(drop=True)


def compute_drain_metrics(
    df: pd.DataFrame,
    smooth: int = 4,
    z_window: int = 156
) -> pd.DataFrame:
    """
    計算耗盡三維度指標

    Parameters
    ----------
    df : pd.DataFrame
        包含 combined 欄位的 DataFrame
    smooth : int
        平滑視窗（週數）
    z_window : int
        Z 分數計算視窗（週數）

    Returns
    -------
    pd.DataFrame
        包含耗盡指標的 DataFrame
    """
    df = df.copy()

    # 方向（每週變化）
    df["delta1"] = df["combined"].diff(1)

    # 速度（流出量，正值 = 流出）
    df["drain_rate"] = -df["delta1"]

    # 加速度（速度變化）
    df["accel"] = df["drain_rate"].diff(1)

    # 平滑處理
    for col in ["combined", "drain_rate", "accel"]:
        df[f"{col}_sm"] = df[col].rolling(smooth, min_periods=1).mean()

    # Z 分數標準化
    for col in ["drain_rate_sm", "accel_sm"]:
        rolling_mean = df[col].rolling(z_window, min_periods=20).mean()
        rolling_std = df[col].rolling(z_window, min_periods=20).std()
        df[f"z_{col}"] = (df[col] - rolling_mean) / rolling_std

    # 水位百分位數
    df["level_pct_rank"] = df["combined_sm"].rolling(z_window, min_periods=20).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5,
        raw=False
    )

    return df


def classify_signal(
    df: pd.DataFrame,
    drain_z: float = -1.5,
    accel_z: float = 1.0,
    level_pctl: float = 0.2
) -> Tuple[str, Dict[str, bool]]:
    """
    判定供給訊號等級

    Parameters
    ----------
    df : pd.DataFrame
        包含耗盡指標的 DataFrame
    drain_z : float
        耗盡速度 Z 門檻
    accel_z : float
        加速度 Z 門檻
    level_pctl : float
        水位分位數門檻

    Returns
    -------
    Tuple[str, dict]
        (訊號等級, 條件判定結果)
    """
    latest = df.iloc[-1]

    # 三段式條件
    A = latest["level_pct_rank"] <= level_pctl  # 庫存水位偏低
    B = latest["z_drain_rate_sm"] <= drain_z    # 耗盡速度異常
    C = latest["z_accel_sm"] >= accel_z         # 耗盡加速

    conditions = {
        "A_level_low": bool(A),
        "B_drain_abnormal": bool(B),
        "C_acceleration": bool(C)
    }

    # 訊號分級
    if A and B and C:
        signal = "HIGH_LATE_STAGE_SUPPLY_SIGNAL"
    elif (B and C) or (A and B):
        signal = "MEDIUM_SUPPLY_TIGHTENING"
    elif A or B or C:
        signal = "WATCH"
    else:
        signal = "NO_SIGNAL"

    return signal, conditions


def generate_narrative(
    result: DrainResult,
    config: DrainConfig
) -> List[str]:
    """
    生成中文敘事解讀

    Parameters
    ----------
    result : DrainResult
        分析結果
    config : DrainConfig
        分析配置

    Returns
    -------
    list
        敘事段落列表
    """
    narrative = []

    # 水位描述
    pct = result.level_percentile * 100
    narrative.append(f"上海合併庫存處於歷史低分位（約 {pct:.0f}% 分位）。")

    # 速度描述
    if result.z_drain_rate <= config.drain_threshold_z:
        narrative.append(
            f"近 {config.smoothing_window_weeks} 週平均庫存流出顯著高於常態"
            f"（耗盡速度 Z={result.z_drain_rate:.1f}）。"
        )

    # 加速度描述
    if result.z_acceleration >= config.accel_threshold_z:
        narrative.append(
            f"流出在加速（加速度 Z=+{result.z_acceleration:.1f}），"
            f"符合「方向 + 速度」核心判準。"
        )

    # 建議
    narrative.append("若同時觀察到其他市場庫存/溢價惡化，可進一步提高信心。")

    return narrative


def generate_caveats() -> List[str]:
    """
    生成數據口徑說明

    Returns
    -------
    list
        說明段落列表
    """
    return [
        "這是「交易所可交割/倉單/指定倉庫」口徑，不等於全中國社會庫存。",
        "單週跳動可能反映倉儲/交割規則變動或搬倉，需用平滑與多來源交叉確認。"
    ]


def analyze(config: DrainConfig) -> DrainResult:
    """
    執行完整分析

    Parameters
    ----------
    config : DrainConfig
        分析配置

    Returns
    -------
    DrainResult
        分析結果
    """
    # 載入數據
    df = load_stock_data(config.include_sources)

    # 合併庫存
    df = build_combined_stock(df, config.unit)

    # 計算耗盡指標
    df = compute_drain_metrics(
        df,
        smooth=config.smoothing_window_weeks,
        z_window=config.z_score_window_weeks
    )

    # 過濾日期範圍
    df = df[
        (df["date"] >= config.start_date) &
        (df["date"] <= config.end_date)
    ].reset_index(drop=True)

    # 判定訊號
    signal, conditions = classify_signal(
        df,
        drain_z=config.drain_threshold_z,
        accel_z=config.accel_threshold_z,
        level_pctl=config.level_percentile_threshold
    )

    # 提取最新數據
    latest = df.iloc[-1]

    # 構建結果
    result = DrainResult(
        as_of=config.end_date,
        unit=config.unit,
        sources=config.include_sources,
        latest_combined_stock=round(latest["combined"], 1),
        level_percentile=round(latest["level_pct_rank"], 4),
        delta1_weekly=round(latest["delta1"], 1),
        drain_rate_4w_avg=round(latest["drain_rate_sm"], 1),
        acceleration_4w_avg=round(latest["accel_sm"], 1),
        z_drain_rate=round(latest["z_drain_rate_sm"], 2),
        z_acceleration=round(latest["z_accel_sm"], 2),
        signal_conditions=conditions,
        signal=signal
    )

    # 生成敘事
    result.narrative = generate_narrative(result, config)
    result.caveats = generate_caveats()

    return result


def quick_check() -> Dict[str, Any]:
    """
    快速檢查模式

    Returns
    -------
    dict
        精簡的分析結果
    """
    config = DrainConfig()
    result = analyze(config)

    return {
        "skill": result.skill,
        "as_of": result.as_of,
        "signal": result.signal,
        "latest_combined_stock_tonnes": result.latest_combined_stock,
        "level_percentile": result.level_percentile,
        "z_drain_rate": result.z_drain_rate,
        "z_acceleration": result.z_acceleration
    }


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description="上海白銀庫存耗盡訊號偵測器"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速檢查模式"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="",
        help="分析起始日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        default="",
        help="分析結束日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["SGE", "SHFE"],
        help="庫存來源"
    )
    parser.add_argument(
        "--unit",
        type=str,
        default="tonnes",
        choices=["tonnes", "kg", "troy_oz"],
        help="輸出單位"
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=4,
        help="平滑視窗（週數）"
    )
    parser.add_argument(
        "--drain-threshold",
        type=float,
        default=-1.5,
        help="耗盡速度 Z 門檻"
    )
    parser.add_argument(
        "--accel-threshold",
        type=float,
        default=1.0,
        help="加速度 Z 門檻"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="輸出檔案路徑"
    )

    args = parser.parse_args()

    if args.quick:
        # 快速檢查模式
        result = quick_check()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 完整分析模式
        config = DrainConfig(
            start_date=args.start,
            end_date=args.end,
            include_sources=args.sources,
            unit=args.unit,
            smoothing_window_weeks=args.smoothing_window,
            drain_threshold_z=args.drain_threshold,
            accel_threshold_z=args.accel_threshold
        )

        result = analyze(config)

        # 轉換為字典
        result_dict = {
            "skill": result.skill,
            "as_of": result.as_of,
            "unit": result.unit,
            "sources": result.sources,
            "result": {
                "latest_combined_stock": result.latest_combined_stock,
                "level_percentile": result.level_percentile,
                "delta1_weekly": result.delta1_weekly,
                "drain_rate_4w_avg": result.drain_rate_4w_avg,
                "acceleration_4w_avg": result.acceleration_4w_avg,
                "z_scores": {
                    "z_drain_rate": result.z_drain_rate,
                    "z_acceleration": result.z_acceleration
                },
                "signal_conditions": result.signal_conditions,
                "signal": result.signal
            },
            "narrative": result.narrative,
            "caveats": result.caveats
        }

        # 輸出
        output_json = json.dumps(result_dict, indent=2, ensure_ascii=False)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"結果已儲存至: {output_path}")
        else:
            print(output_json)


if __name__ == "__main__":
    main()
