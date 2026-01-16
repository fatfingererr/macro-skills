#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium Price Regime Classification

鋰價型態分類（Downtrend → Bottoming → Uptrend → Overheat）
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """價格數據"""
    date: str
    price: float
    product: str = "carbonate"  # carbonate | hydroxide | spodumene


@dataclass
class RegimeResult:
    """Regime 分類結果"""
    regime: str
    confidence: float
    indicators: Dict[str, Any]
    signals: List[str]
    asof_date: str


# ============================================================================
# 技術指標計算
# ============================================================================

def compute_roc(prices: List[float], period: int = 12) -> Optional[float]:
    """
    計算 Rate of Change (ROC)

    ROC = (current - past) / past * 100

    Args:
        prices: 價格序列（最新在最後）
        period: 週期

    Returns:
        ROC 百分比
    """
    if len(prices) < period + 1:
        return None

    current = prices[-1]
    past = prices[-(period + 1)]

    if past <= 0:
        return None

    return (current - past) / past * 100


def compute_slope(prices: List[float], window: int = 26) -> Optional[float]:
    """
    計算趨勢斜率（標準化）

    使用線性回歸斜率

    Args:
        prices: 價格序列
        window: 視窗大小

    Returns:
        標準化斜率
    """
    if len(prices) < window:
        return None

    subset = prices[-window:]
    n = len(subset)

    # 簡單線性回歸
    x_mean = (n - 1) / 2
    y_mean = sum(subset) / n

    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(subset))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return None

    slope = numerator / denominator

    # 標準化（除以平均價格）
    if y_mean > 0:
        slope = slope / y_mean * 100

    return slope


def compute_volatility(prices: List[float], window: int = 26) -> Optional[float]:
    """
    計算波動率（ATR 風格）

    Args:
        prices: 價格序列
        window: 視窗大小

    Returns:
        波動率百分比
    """
    if len(prices) < window + 1:
        return None

    subset = prices[-(window + 1):]

    # 計算每週變化率的絕對值
    changes = []
    for i in range(1, len(subset)):
        if subset[i - 1] > 0:
            change = abs(subset[i] - subset[i - 1]) / subset[i - 1] * 100
            changes.append(change)

    if not changes:
        return None

    return sum(changes) / len(changes)


def compute_mean_deviation(
    prices: List[float],
    window: int = 200
) -> Optional[float]:
    """
    計算均值偏離度

    Args:
        prices: 價格序列
        window: 均值視窗

    Returns:
        偏離度百分比（正=高於均值，負=低於均值）
    """
    if len(prices) < window:
        # 使用可用數據
        window = len(prices)

    if window < 10:
        return None

    subset = prices[-window:]
    mean = sum(subset) / len(subset)
    current = prices[-1]

    if mean <= 0:
        return None

    return (current - mean) / mean * 100


# ============================================================================
# Regime 分類
# ============================================================================

def classify_regime(
    roc_12w: Optional[float],
    roc_26w: Optional[float],
    slope: Optional[float],
    volatility: Optional[float],
    deviation: Optional[float],
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    根據技術指標分類價格型態

    型態定義：
    - downtrend: ROC < -5%, slope < 0
    - bottoming: ROC 接近 0, volatility 下降, deviation < -20%
    - uptrend: ROC > 5%, slope > 0
    - overheat: ROC > 30%, deviation > 30%

    Args:
        roc_12w: 12 週 ROC
        roc_26w: 26 週 ROC
        slope: 趨勢斜率
        volatility: 波動率
        deviation: 均值偏離度
        thresholds: 自定義閾值

    Returns:
        regime: 型態分類
        confidence: 置信度
        reasoning: 判斷理由
    """
    if thresholds is None:
        thresholds = {
            "roc_up": 5,
            "roc_down": -5,
            "roc_overheat": 30,
            "deviation_extreme": 30,
            "deviation_bottom": -20
        }

    signals = []
    regime_scores = {
        "downtrend": 0,
        "bottoming": 0,
        "uptrend": 0,
        "overheat": 0
    }

    # ROC 判斷
    if roc_12w is not None:
        if roc_12w > thresholds["roc_overheat"]:
            regime_scores["overheat"] += 3
            signals.append(f"ROC 12w ({roc_12w:.1f}%) > 30% 過熱")
        elif roc_12w > thresholds["roc_up"]:
            regime_scores["uptrend"] += 2
            signals.append(f"ROC 12w ({roc_12w:.1f}%) > 5% 上行")
        elif roc_12w < thresholds["roc_down"]:
            regime_scores["downtrend"] += 2
            signals.append(f"ROC 12w ({roc_12w:.1f}%) < -5% 下行")
        else:
            regime_scores["bottoming"] += 1
            signals.append(f"ROC 12w ({roc_12w:.1f}%) 趨近 0")

    # 斜率判斷
    if slope is not None:
        if slope > 0.5:
            regime_scores["uptrend"] += 1
            signals.append(f"趨勢斜率 ({slope:.2f}) 正向")
        elif slope < -0.5:
            regime_scores["downtrend"] += 1
            signals.append(f"趨勢斜率 ({slope:.2f}) 負向")
        else:
            regime_scores["bottoming"] += 1
            signals.append(f"趨勢斜率 ({slope:.2f}) 平緩")

    # 均值偏離判斷
    if deviation is not None:
        if deviation > thresholds["deviation_extreme"]:
            regime_scores["overheat"] += 2
            signals.append(f"均值偏離 ({deviation:.1f}%) 極端高估")
        elif deviation < thresholds["deviation_bottom"]:
            regime_scores["bottoming"] += 2
            signals.append(f"均值偏離 ({deviation:.1f}%) 低於長期均值")

    # 決定最終 regime
    max_score = max(regime_scores.values())
    if max_score == 0:
        regime = "unknown"
        confidence = 0.3
    else:
        regime = max(regime_scores, key=lambda k: regime_scores[k])
        total_score = sum(regime_scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.5

    return {
        "regime": regime,
        "confidence": confidence,
        "scores": regime_scores,
        "signals": signals
    }


def compute_price_regime(
    prices: List[float],
    product: str = "carbonate",
    thresholds: Optional[Dict[str, float]] = None
) -> RegimeResult:
    """
    完整價格型態計算

    Args:
        prices: 價格序列（週頻，最新在最後）
        product: 產品類型
        thresholds: 自定義閾值

    Returns:
        RegimeResult 完整結果
    """
    # 計算各技術指標
    roc_12w = compute_roc(prices, 12)
    roc_26w = compute_roc(prices, 26)
    slope = compute_slope(prices, 26)
    volatility = compute_volatility(prices, 26)
    deviation = compute_mean_deviation(prices, 200)

    # 分類
    classification = classify_regime(
        roc_12w, roc_26w, slope, volatility, deviation, thresholds
    )

    indicators = {
        "roc_12w": round(roc_12w, 2) if roc_12w else None,
        "roc_26w": round(roc_26w, 2) if roc_26w else None,
        "slope": round(slope, 3) if slope else None,
        "volatility": round(volatility, 2) if volatility else None,
        "mean_deviation_pct": round(deviation, 1) if deviation else None
    }

    return RegimeResult(
        regime=classification["regime"],
        confidence=classification["confidence"],
        indicators=indicators,
        signals=classification["signals"],
        asof_date=date.today().isoformat()
    )


# ============================================================================
# 輸出格式化
# ============================================================================

def format_regime_output(result: RegimeResult, product: str = "carbonate") -> Dict[str, Any]:
    """格式化輸出"""
    return {
        "product": product,
        "regime": result.regime,
        "regime_label": _regime_label(result.regime),
        "confidence": round(result.confidence, 2),
        "indicators": result.indicators,
        "signals": result.signals,
        "interpretation": _interpret_regime(result.regime),
        "asof_date": result.asof_date
    }


def _regime_label(regime: str) -> str:
    """Regime 中文標籤"""
    labels = {
        "downtrend": "下行趨勢",
        "bottoming": "築底盤整",
        "uptrend": "上行趨勢",
        "overheat": "過熱",
        "unknown": "未知"
    }
    return labels.get(regime, regime)


def _interpret_regime(regime: str) -> str:
    """Regime 投資解讀"""
    interpretations = {
        "downtrend": "價格處於下行趨勢，建議觀望或做空，等待築底信號",
        "bottoming": "價格可能正在築底，可開始關注反轉信號，分批建倉",
        "uptrend": "價格處於上行趨勢，順勢做多，設定移動止損",
        "overheat": "價格可能過熱，警惕回調風險，考慮獲利了結",
        "unknown": "數據不足以判斷，建議收集更多價格數據"
    }
    return interpretations.get(regime, "")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Lithium Price Regime Classification")
    parser.add_argument("--prices", type=str, help="Comma-separated prices (weekly)")
    parser.add_argument("--product", type=str, default="carbonate",
                       choices=["carbonate", "hydroxide", "spodumene"])
    parser.add_argument("--demo", action="store_true", help="Run with demo data")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.demo:
        # Demo: 模擬築底後上行的價格序列
        import random
        base = 20000  # USD/t
        prices = []
        # 下行階段
        for i in range(30):
            prices.append(base * (1 - i * 0.015) + random.uniform(-500, 500))
        # 築底階段
        for i in range(20):
            prices.append(prices[-1] * (1 + random.uniform(-0.01, 0.01)))
        # 上行階段
        for i in range(10):
            prices.append(prices[-1] * (1 + 0.02 + random.uniform(-0.005, 0.01)))

    elif args.prices:
        prices = [float(p.strip()) for p in args.prices.split(",")]
    else:
        print("Error: Must provide --prices or --demo")
        exit(1)

    result = compute_price_regime(prices, args.product)
    output = format_regime_output(result, args.product)

    print(json.dumps(output, indent=2, ensure_ascii=False))
