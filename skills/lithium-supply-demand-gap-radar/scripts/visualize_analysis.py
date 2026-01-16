#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium Analysis Visualization

生成鋰供需分析的視覺化圖表
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Check for visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available, charts will not be generated")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def setup_chinese_font():
    """設定中文字體"""
    if not HAS_MATPLOTLIB:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def generate_balance_chart(
    balance_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成供需平衡趨勢圖

    Args:
        balance_data: Balance nowcast 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑，或 None（如果失敗）
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        logger.warning("Required libraries not available for chart generation")
        return None

    setup_chinese_font()

    try:
        fig, ax = plt.subplots(figsize=(12, 6))

        # 假設我們有歷史 balance index 數據
        years = [2020, 2021, 2022, 2023, 2024, 2025]
        balance_values = [0.2, 0.5, 0.8, 1.2, 0.85, 0.9]  # Mock data

        ax.plot(years, balance_values, "b-o", linewidth=2, markersize=8)
        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

        ax.fill_between(years, balance_values, 0,
                       where=[v > 0 for v in balance_values],
                       alpha=0.3, color="green", label="缺口擴大")
        ax.fill_between(years, balance_values, 0,
                       where=[v <= 0 for v in balance_values],
                       alpha=0.3, color="red", label="供給過剩")

        ax.set_xlabel("年份", fontsize=12)
        ax.set_ylabel("Balance Index (Z-score)", fontsize=12)
        ax.set_title("鋰供需平衡指數趨勢", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_balance_trend_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Balance chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate balance chart: {e}")
        return None


def generate_regime_chart(
    regime_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成價格制度指標圖

    Args:
        regime_data: Price regime 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        return None

    setup_chinese_font()

    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 模擬數據
        weeks = np.arange(52)

        # ROC 12w
        roc_12w = np.sin(weeks / 10) * 20 + np.random.randn(52) * 5
        axes[0, 0].plot(weeks, roc_12w, "b-")
        axes[0, 0].axhline(y=0, color="gray", linestyle="--")
        axes[0, 0].axhline(y=5, color="green", linestyle=":", label="+5% 上行閾值")
        axes[0, 0].axhline(y=-5, color="red", linestyle=":", label="-5% 下行閾值")
        axes[0, 0].set_title("12 週動能 (ROC)", fontsize=12)
        axes[0, 0].set_ylabel("%")
        axes[0, 0].legend(fontsize=8)

        # 趨勢斜率
        slope = np.cumsum(np.random.randn(52) * 0.01)
        axes[0, 1].plot(weeks, slope, "purple")
        axes[0, 1].axhline(y=0, color="gray", linestyle="--")
        axes[0, 1].set_title("趨勢斜率 (標準化)", fontsize=12)

        # 波動率
        volatility = 5 + np.random.randn(52).cumsum() * 0.5
        volatility = np.abs(volatility)
        axes[1, 0].plot(weeks, volatility, "orange")
        axes[1, 0].set_title("波動率 (ATR%)", fontsize=12)
        axes[1, 0].set_ylabel("%")

        # 均值偏離
        deviation = np.sin(weeks / 15) * 20 + np.random.randn(52) * 5
        axes[1, 1].plot(weeks, deviation, "green")
        axes[1, 1].axhline(y=30, color="red", linestyle="--", label="極端正偏離")
        axes[1, 1].axhline(y=-30, color="red", linestyle="--", label="極端負偏離")
        axes[1, 1].fill_between(weeks, deviation, 0, alpha=0.3)
        axes[1, 1].set_title("均值偏離度", fontsize=12)
        axes[1, 1].set_ylabel("%")
        axes[1, 1].legend(fontsize=8)

        for ax in axes.flat:
            ax.set_xlabel("週")
            ax.grid(True, alpha=0.3)

        plt.suptitle("鋰價制度指標", fontsize=14, fontweight="bold")
        plt.tight_layout()

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_regime_indicators_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Regime chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate regime chart: {e}")
        return None


def generate_etf_exposure_chart(
    etf_data: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> Optional[str]:
    """
    生成 ETF 暴露分析圖

    Args:
        etf_data: ETF exposure 結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        return None

    setup_chinese_font()

    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # 產業鏈段分布餅圖
        segment_weights = etf_data.get("segment_weights", {
            "upstream": 35.2,
            "midstream": 18.5,
            "downstream": 42.3,
            "unknown": 4.0
        })

        labels = ["上游 (礦商)", "中游 (精煉)", "下游 (電池)", "其他"]
        sizes = [
            segment_weights.get("upstream", 0),
            segment_weights.get("midstream", 0),
            segment_weights.get("downstream", 0),
            segment_weights.get("unknown", 0)
        ]
        colors = ["#2ecc71", "#3498db", "#e74c3c", "#95a5a6"]
        explode = (0.05, 0, 0, 0)

        axes[0].pie(sizes, explode=explode, labels=labels, colors=colors,
                   autopct="%1.1f%%", shadow=True, startangle=90)
        axes[0].set_title("LIT ETF 產業鏈段分布", fontsize=12, fontweight="bold")

        # Beta 趨勢
        weeks = np.arange(52)
        beta_li = 0.7 + np.cumsum(np.random.randn(52) * 0.02)
        beta_ev = 0.55 + np.cumsum(np.random.randn(52) * 0.015)

        axes[1].plot(weeks, beta_li, "b-", label="鋰價因子 Beta", linewidth=2)
        axes[1].plot(weeks, beta_ev, "g-", label="EV 需求因子 Beta", linewidth=2)
        axes[1].axhline(y=0.3, color="red", linestyle="--", alpha=0.5, label="傳導斷裂閾值")
        axes[1].fill_between(weeks, 0, 0.3, alpha=0.1, color="red")

        axes[1].set_xlabel("週")
        axes[1].set_ylabel("Beta")
        axes[1].set_title("ETF 因子敏感度趨勢 (52 週)", fontsize=12, fontweight="bold")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_etf_exposure_{date.today().strftime('%Y%m%d')}.png"
        filepath = output_path / filename

        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"ETF exposure chart saved to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to generate ETF exposure chart: {e}")
        return None


def generate_all_charts(
    analysis_result: Dict[str, Any],
    output_dir: str = "output",
    prefix: str = "lithium"
) -> List[str]:
    """
    生成所有圖表

    Args:
        analysis_result: 完整分析結果
        output_dir: 輸出目錄
        prefix: 檔名前綴

    Returns:
        生成的圖片路徑列表
    """
    charts = []

    # Balance chart
    if "balance_nowcast" in analysis_result:
        path = generate_balance_chart(
            analysis_result["balance_nowcast"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    # Regime chart
    if "price_regime" in analysis_result:
        path = generate_regime_chart(
            analysis_result["price_regime"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    # ETF exposure chart
    if "etf_exposure" in analysis_result:
        path = generate_etf_exposure_chart(
            analysis_result["etf_exposure"],
            output_dir, prefix
        )
        if path:
            charts.append(path)

    logger.info(f"Generated {len(charts)} charts")
    return charts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 測試圖表生成
    mock_result = {
        "balance_nowcast": {
            "balance_index": {"neutral": {"value": 0.85}}
        },
        "price_regime": {
            "carbonate": {"regime": "bottoming"}
        },
        "etf_exposure": {
            "segment_weights": {
                "upstream": 35.2,
                "midstream": 18.5,
                "downstream": 42.3,
                "unknown": 4.0
            }
        }
    }

    charts = generate_all_charts(mock_result)
    print(f"Generated {len(charts)} charts:")
    for chart in charts:
        print(f"  - {chart}")
