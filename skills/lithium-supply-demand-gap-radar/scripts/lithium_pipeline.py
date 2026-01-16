#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lithium Supply-Demand Gap Radar - Core Pipeline

將鋰供需（礦端→化學品→電池）的公開/付費數據整合成可量化的供需/價格/政策/需求 proxy，
映射到鋰主題 ETF（如 LIT）的暴露與技術結構，輸出可執行的多空判斷、目標路徑與失效條件。

Usage:
    python lithium_pipeline.py analyze --ticker=LIT --lookback=10
    python lithium_pipeline.py balance --asof=2026-01-16
    python lithium_pipeline.py regime --chem=both
    python lithium_pipeline.py etf-beta --ticker=LIT --window=52
"""

import argparse
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LithiumConfig:
    """鋰分析配置"""
    etf_ticker: str = "LIT"
    lookback_years: int = 10
    price_freq: str = "weekly"
    region_focus: List[str] = field(default_factory=lambda: ["China", "Australia", "Chile", "Argentina"])
    chem_focus: str = "both"
    data_level: str = "free_nolimit"
    output_format: str = "markdown"

    # Balance Nowcast 參數
    kg_per_kwh_scenarios: List[float] = field(default_factory=lambda: [0.12, 0.15, 0.18])

    # Price Regime 參數
    momentum_periods: List[int] = field(default_factory=lambda: [12, 26])
    slope_window: int = 26
    volatility_window: int = 26
    mean_window: int = 200

    # ETF Beta 參數
    beta_window: int = 52
    transmission_threshold: float = 0.3
    transmission_duration: int = 8


# ============================================================================
# Unit Conversion
# ============================================================================

class LithiumUnitConverter:
    """鋰單位轉換工具"""

    LI_TO_LCE = 5.323
    LI_TO_LHE = 6.048
    LCE_TO_LHE = 1.136
    SC6_TO_LCE = 0.136  # 假設 6% Li₂O, 8% 損失

    @staticmethod
    def li_to_lce(li_kt: float) -> float:
        """鋰金屬 → 碳酸鋰當量"""
        return li_kt * LithiumUnitConverter.LI_TO_LCE

    @staticmethod
    def lce_to_li(lce_kt: float) -> float:
        """碳酸鋰當量 → 鋰金屬"""
        return lce_kt / LithiumUnitConverter.LI_TO_LCE

    @staticmethod
    def sc6_to_lce(sc6_kt: float, li2o_pct: float = 6.0, loss_pct: float = 8.0) -> float:
        """鋰輝石精礦 → 碳酸鋰當量"""
        effective = 1 - loss_pct / 100
        return sc6_kt * (li2o_pct / 100) * 2.473 * effective

    @staticmethod
    def gwh_to_lce(gwh: float, kg_per_kwh: float = 0.15) -> float:
        """電池容量 → 碳酸鋰當量需求"""
        li_kt = gwh * kg_per_kwh / 1000
        return li_kt * LithiumUnitConverter.LI_TO_LCE


# ============================================================================
# Data Loading (Mock implementations - replace with actual data sources)
# ============================================================================

def load_usgs_lithium() -> Dict[str, Any]:
    """
    載入 USGS 鋰統計數據

    實際實作應從 USGS 網站抓取或讀取本地緩存
    """
    logger.info("Loading USGS lithium data...")

    # Mock data - replace with actual data fetching
    return {
        "world_production": {
            2020: 82,
            2021: 107,
            2022: 130,
            2023: 180,
            2024: 220
        },
        "by_country": {
            "Australia": {2024: 86},
            "Chile": {2024: 44},
            "China": {2024: 33},
            "Argentina": {2024: 10}
        },
        "unit": "kt_Li",
        "source_id": "USGS",
        "confidence": 0.95
    }


def load_iea_ev_outlook() -> Dict[str, Any]:
    """
    載入 IEA EV 展望數據

    實際實作應從 IEA 網站抓取
    """
    logger.info("Loading IEA EV Outlook data...")

    # Mock data
    return {
        "ev_sales": {
            2020: 3.1,
            2021: 6.5,
            2022: 10.6,
            2023: 14.2,
            2024: 17.5
        },
        "battery_demand_gwh": {
            2020: 150,
            2021: 330,
            2022: 550,
            2023: 750,
            2024: 1000
        },
        "unit": "mixed",
        "source_id": "IEA",
        "confidence": 0.90
    }


def load_australia_req() -> Dict[str, Any]:
    """載入澳洲 REQ 數據"""
    logger.info("Loading Australia REQ data...")

    return {
        "production": {2024: 86},
        "exports": {2024: 80},
        "unit": "kt_Li",
        "source_id": "AU_REQ",
        "confidence": 0.90
    }


def load_lithium_price(chem_focus: str, data_level: str) -> Dict[str, Any]:
    """
    載入鋰價格數據

    根據 data_level 選擇數據源
    """
    logger.info(f"Loading lithium price data (level: {data_level})...")

    # Mock data - 實際應根據 data_level 選擇 Fastmarkets/SMM/CME
    base_price = 15000  # USD/t LCE

    # 生成模擬週度價格序列
    dates = pd.date_range(end=date.today(), periods=52 * 5, freq="W")
    np.random.seed(42)
    prices = base_price * (1 + np.cumsum(np.random.randn(len(dates)) * 0.02))

    return {
        "carbonate": pd.Series(prices * 0.9, index=dates),
        "hydroxide": pd.Series(prices, index=dates),
        "unit": "USD_per_t",
        "source_id": "CME_proxy" if data_level == "free_nolimit" else "Fastmarkets",
        "confidence": 0.70 if data_level == "free_nolimit" else 0.90
    }


def load_etf_price(ticker: str, years: int, freq: str) -> Dict[str, Any]:
    """載入 ETF 價格數據"""
    logger.info(f"Loading {ticker} price data...")

    try:
        import yfinance as yf

        etf = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        interval = "1wk" if freq == "weekly" else "1d"
        df = etf.history(start=start_date, end=end_date, interval=interval)

        return {
            "prices": df["Close"],
            "returns": df["Close"].pct_change(),
            "ticker": ticker,
            "freq": freq
        }
    except Exception as e:
        logger.warning(f"Failed to load ETF data: {e}")
        # Return mock data
        dates = pd.date_range(end=date.today(), periods=52 * years, freq="W")
        np.random.seed(42)
        prices = 50 * (1 + np.cumsum(np.random.randn(len(dates)) * 0.02))
        return {
            "prices": pd.Series(prices, index=dates),
            "returns": pd.Series(prices, index=dates).pct_change(),
            "ticker": ticker,
            "freq": freq
        }


def load_etf_holdings(ticker: str = "LIT") -> Dict[str, Any]:
    """載入 ETF 持股數據"""
    logger.info(f"Loading {ticker} holdings...")

    # Mock data - 實際應從 Global X 抓取
    return {
        "list": [
            {"ticker": "ALB", "name": "Albemarle Corp", "weight": 8.2, "segment": "upstream", "country": "US"},
            {"ticker": "TSLA", "name": "Tesla Inc", "weight": 7.5, "segment": "downstream", "country": "US"},
            {"ticker": "SQM", "name": "SQM", "weight": 6.8, "segment": "upstream", "country": "Chile"},
            {"ticker": "CATL", "name": "CATL", "weight": 6.2, "segment": "downstream", "country": "China"},
            {"ticker": "PLS.AX", "name": "Pilbara Minerals", "weight": 5.5, "segment": "upstream", "country": "Australia"},
            {"ticker": "LTHM", "name": "Arcadium Lithium", "weight": 5.0, "segment": "midstream", "country": "US"},
            {"ticker": "MIN.AX", "name": "Mineral Resources", "weight": 4.5, "segment": "upstream", "country": "Australia"},
            {"ticker": "LAC", "name": "Lithium Americas", "weight": 4.0, "segment": "upstream", "country": "US"},
        ],
        "asof_date": date.today().isoformat(),
        "source": "GlobalX"
    }


# ============================================================================
# Core Analysis Functions
# ============================================================================

class BalanceNowcast:
    """供需平衡即時估計"""

    def __init__(self, config: LithiumConfig):
        self.config = config

    def compute(self) -> Dict[str, Any]:
        """計算供需平衡指數"""
        logger.info("Computing balance nowcast...")

        # 載入數據
        usgs = load_usgs_lithium()
        iea = load_iea_ev_outlook()
        aus = load_australia_req()

        # 轉換 USGS 數據到 LCE
        supply_lce = {
            year: LithiumUnitConverter.li_to_lce(val)
            for year, val in usgs["world_production"].items()
        }

        # 計算需求（三情境）
        demand_scenarios = {}
        for scenario, kg_kwh in zip(
            ["conservative", "neutral", "aggressive"],
            self.config.kg_per_kwh_scenarios
        ):
            demand_scenarios[scenario] = {
                year: LithiumUnitConverter.gwh_to_lce(gwh, kg_kwh)
                for year, gwh in iea["battery_demand_gwh"].items()
            }

        # 計算 Balance Index
        balance_index = {}
        for scenario, demand in demand_scenarios.items():
            gap = []
            for year in sorted(set(supply_lce.keys()) & set(demand.keys())):
                gap.append(demand[year] - supply_lce[year])

            if gap:
                zscore = (gap[-1] - np.mean(gap)) / (np.std(gap) + 1e-6)
                balance_index[scenario] = {
                    "value": round(zscore, 2),
                    "trend": "widening" if zscore > 0 else "narrowing",
                    "kg_per_kwh": self.config.kg_per_kwh_scenarios[
                        ["conservative", "neutral", "aggressive"].index(scenario)
                    ]
                }

        # 拐點偵測
        inflection = self._detect_inflection(balance_index)

        return {
            "balance_index": balance_index,
            "inflection": inflection,
            "supply_summary": {
                "latest_year": max(supply_lce.keys()),
                "value": supply_lce[max(supply_lce.keys())],
                "unit": "kt_LCE"
            },
            "demand_summary": {
                "scenarios": demand_scenarios,
                "unit": "kt_LCE"
            },
            "sources": ["USGS", "IEA", "AU_REQ"]
        }

    def _detect_inflection(self, balance_index: Dict) -> Dict[str, Any]:
        """偵測拐點"""
        # 簡化的拐點偵測邏輯
        neutral_value = balance_index.get("neutral", {}).get("value", 0)

        return {
            "detected": False,
            "type": None,
            "description": "無明顯拐點"
        }


class PriceRegime:
    """價格制度分析"""

    def __init__(self, config: LithiumConfig):
        self.config = config

    def compute(self) -> Dict[str, Any]:
        """計算價格制度"""
        logger.info("Computing price regime...")

        # 載入價格數據
        prices = load_lithium_price(self.config.chem_focus, self.config.data_level)

        results = {}

        for chem in ["carbonate", "hydroxide"]:
            if chem not in prices or prices[chem] is None:
                continue

            price_series = prices[chem]

            # 計算指標
            indicators = self._compute_indicators(price_series)

            # 分類制度
            regime = self._classify_regime(indicators)

            results[chem] = {
                "regime": regime["regime"],
                "confidence": regime["confidence"],
                "indicators": indicators,
                "signal": regime["signal"]
            }

        # 價差分析
        if "carbonate" in results and "hydroxide" in results:
            results["spread"] = self._compute_spread(prices["carbonate"], prices["hydroxide"])

        results["sync_status"] = self._check_sync(results)

        return results

    def _compute_indicators(self, price_series: pd.Series) -> Dict[str, float]:
        """計算制度指標"""
        # ROC
        roc_12w = (price_series.iloc[-1] / price_series.iloc[-12] - 1) * 100 if len(price_series) > 12 else 0
        roc_26w = (price_series.iloc[-1] / price_series.iloc[-26] - 1) * 100 if len(price_series) > 26 else 0

        # 斜率
        if len(price_series) >= 26:
            x = np.arange(26)
            y = price_series.iloc[-26:].values
            slope = np.polyfit(x, y, 1)[0] / np.mean(y)
        else:
            slope = 0

        # 波動率
        returns = price_series.pct_change().dropna()
        volatility = returns.iloc[-26:].std() * 100 if len(returns) >= 26 else 0

        # 均值偏離
        ma_200 = price_series.iloc[-200:].mean() if len(price_series) >= 200 else price_series.mean()
        deviation = (price_series.iloc[-1] - ma_200) / ma_200 * 100

        return {
            "roc_12w": round(roc_12w, 2),
            "roc_26w": round(roc_26w, 2),
            "slope": round(slope, 4),
            "volatility": round(volatility, 2),
            "mean_deviation": round(deviation, 2)
        }

    def _classify_regime(self, indicators: Dict) -> Dict[str, Any]:
        """分類價格制度"""
        roc_12w = indicators["roc_12w"]
        slope = indicators["slope"]
        deviation = indicators["mean_deviation"]

        # 過熱
        if roc_12w > 30 or deviation > 30:
            return {
                "regime": "overheat",
                "confidence": 0.9,
                "signal": "獲利了結風險"
            }

        # 上行
        if slope > 0 and roc_12w > 5:
            return {
                "regime": "uptrend",
                "confidence": 0.85,
                "signal": "做多視窗開啟"
            }

        # 下行
        if slope < 0 and roc_12w < -5:
            return {
                "regime": "downtrend",
                "confidence": 0.85,
                "signal": "空頭主導，避免做多"
            }

        # 築底
        return {
            "regime": "bottoming",
            "confidence": 0.75,
            "signal": "觀望，等待確認"
        }

    def _compute_spread(self, carbonate: pd.Series, hydroxide: pd.Series) -> Dict:
        """計算碳酸鋰/氫氧化鋰價差"""
        spread = hydroxide - carbonate
        current_spread = spread.iloc[-1]
        percentile = (spread < current_spread).mean() * 100

        return {
            "current": round(current_spread, 0),
            "unit": "USD/t",
            "percentile": round(percentile, 0),
            "trend": "widening" if spread.iloc[-1] > spread.iloc[-4] else "narrowing"
        }

    def _check_sync(self, results: Dict) -> str:
        """檢查碳酸鋰/氫氧化鋰同步性"""
        if "carbonate" in results and "hydroxide" in results:
            if results["carbonate"]["regime"] == results["hydroxide"]["regime"]:
                return "synchronized"
        return "divergent"


class ETFExposure:
    """ETF 暴露分析"""

    def __init__(self, config: LithiumConfig):
        self.config = config

    def compute(self) -> Dict[str, Any]:
        """計算 ETF 暴露與傳導"""
        logger.info("Computing ETF exposure...")

        # 載入數據
        etf_data = load_etf_price(
            self.config.etf_ticker,
            self.config.lookback_years,
            self.config.price_freq
        )
        holdings = load_etf_holdings(self.config.etf_ticker)
        li_price = load_lithium_price(self.config.chem_focus, self.config.data_level)

        # 計算產業鏈段權重
        segment_weights = self._compute_segment_weights(holdings)

        # 計算 rolling beta
        beta_results = self._compute_rolling_beta(etf_data, li_price)

        # 評估傳導狀態
        transmission = self._assess_transmission(beta_results)

        return {
            "holdings_summary": {
                "total": len(holdings["list"]),
                "asof_date": holdings["asof_date"],
                "source": holdings["source"]
            },
            "segment_weights": segment_weights,
            "beta_analysis": beta_results,
            "transmission": transmission,
            "top_holdings": holdings["list"][:5]
        }

    def _compute_segment_weights(self, holdings: Dict) -> Dict[str, float]:
        """計算產業鏈段權重"""
        segments = {"upstream": 0, "midstream": 0, "downstream": 0, "unknown": 0}

        for h in holdings["list"]:
            segment = h.get("segment", "unknown")
            weight = h.get("weight", 0)
            segments[segment] = segments.get(segment, 0) + weight

        return {k: round(v, 1) for k, v in segments.items()}

    def _compute_rolling_beta(self, etf_data: Dict, li_price: Dict) -> Dict:
        """計算滾動 beta"""
        try:
            etf_returns = etf_data["returns"].dropna()
            li_returns = li_price["carbonate"].pct_change().dropna()

            # 對齊
            common_index = etf_returns.index.intersection(li_returns.index)
            if len(common_index) < self.config.beta_window:
                raise ValueError("Insufficient data for beta calculation")

            etf_aligned = etf_returns.loc[common_index]
            li_aligned = li_returns.loc[common_index]

            # 簡化：計算整體 beta
            cov = np.cov(etf_aligned.iloc[-self.config.beta_window:],
                        li_aligned.iloc[-self.config.beta_window:])[0, 1]
            var = np.var(li_aligned.iloc[-self.config.beta_window:])
            beta_li = cov / (var + 1e-10)

            return {
                "current_beta_li": round(beta_li, 2),
                "current_beta_ev": round(beta_li * 0.8, 2),  # 簡化估計
                "52w_avg_beta_li": round(beta_li * 0.95, 2),
                "trend": "rising" if beta_li > 0.5 else "falling"
            }
        except Exception as e:
            logger.warning(f"Beta calculation failed: {e}")
            return {
                "current_beta_li": 0.7,
                "current_beta_ev": 0.6,
                "52w_avg_beta_li": 0.68,
                "trend": "stable"
            }

    def _assess_transmission(self, beta_results: Dict) -> Dict:
        """評估傳導狀態"""
        beta = beta_results.get("current_beta_li", 0.5)

        if beta < self.config.transmission_threshold:
            return {
                "status": "broken",
                "description": f"傳導斷裂：Beta = {beta:.2f} 低於閾值 {self.config.transmission_threshold}"
            }
        elif beta < 0.5:
            return {
                "status": "weakening",
                "description": f"傳導減弱：Beta = {beta:.2f}"
            }
        else:
            return {
                "status": "normal",
                "description": f"傳導正常：Beta = {beta:.2f}"
            }


# ============================================================================
# Main Pipeline
# ============================================================================

class LithiumSupplyDemandRadar:
    """鋰產業鏈供需雷達主類"""

    def __init__(self, config: Optional[LithiumConfig] = None):
        self.config = config or LithiumConfig()
        self.balance = BalanceNowcast(self.config)
        self.price = PriceRegime(self.config)
        self.etf = ETFExposure(self.config)

    def full_analysis(self) -> Dict[str, Any]:
        """完整分析"""
        logger.info("Running full analysis...")

        balance_result = self.balance.compute()
        price_result = self.price.compute()
        etf_result = self.etf.compute()

        # 綜合判斷
        thesis = self._compute_thesis(balance_result, price_result, etf_result)

        # 目標路徑
        targets = self._compute_targets()

        # 失效條件
        invalidation = self._build_invalidation(balance_result, price_result, etf_result)

        return {
            "metadata": {
                "skill": "lithium-supply-demand-gap-radar",
                "version": "0.1.0",
                "asof_date": date.today().isoformat(),
                "data_level": self.config.data_level
            },
            "balance_nowcast": balance_result,
            "price_regime": price_result,
            "etf_exposure": etf_result,
            "thesis": thesis,
            "targets": targets,
            "invalidation": invalidation
        }

    def balance_nowcast(self) -> Dict[str, Any]:
        """僅供需平衡分析"""
        return self.balance.compute()

    def price_regime(self) -> Dict[str, Any]:
        """僅價格制度分析"""
        return self.price.compute()

    def etf_exposure(self) -> Dict[str, Any]:
        """僅 ETF 暴露分析"""
        return self.etf.compute()

    def _compute_thesis(self, balance: Dict, price: Dict, etf: Dict) -> Dict:
        """計算綜合論述"""
        balance_score = balance["balance_index"].get("neutral", {}).get("value", 0)
        price_regime = price.get("carbonate", {}).get("regime", "unknown")
        beta = etf["beta_analysis"].get("current_beta_li", 0.5)

        # 簡化的論述邏輯
        if balance_score > 0.5 and price_regime in ["bottoming", "uptrend"] and beta > 0.5:
            direction = "neutral_bullish"
        elif balance_score < -0.5 or price_regime == "downtrend":
            direction = "bearish"
        else:
            direction = "neutral"

        return {
            "direction": direction,
            "confidence": 0.70,
            "components": {
                "balance_score": balance_score,
                "regime_score": 0.5 if price_regime == "bottoming" else (0.8 if price_regime == "uptrend" else 0.3),
                "transmission_score": beta
            }
        }

    def _compute_targets(self) -> Dict:
        """計算目標路徑"""
        # 簡化實作
        return {
            "support": {"level": 38.50, "type": "prior_low"},
            "mid_channel": {"level": 48.50, "type": "ma_50w"},
            "prior_high": {"level": 56.20, "type": "resistance"},
            "upper_channel": {"level": 68.00, "type": "upper_band"}
        }

    def _build_invalidation(self, balance: Dict, price: Dict, etf: Dict) -> List[Dict]:
        """建立失效條件"""
        return [
            {
                "condition": "price < 38.50",
                "description": "跌破關鍵支撐",
                "severity": "high"
            },
            {
                "condition": "balance_index < 0",
                "description": "供需平衡轉負（過剩）",
                "severity": "high"
            },
            {
                "condition": "regime == downtrend",
                "description": "價格制度再次轉弱",
                "severity": "medium"
            },
            {
                "condition": "beta_li < 0.3 for 8w",
                "description": "傳導斷裂",
                "severity": "medium"
            }
        ]


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Lithium Supply-Demand Gap Radar")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Full analysis")
    analyze_parser.add_argument("--ticker", default="LIT", help="ETF ticker")
    analyze_parser.add_argument("--lookback", type=int, default=10, help="Lookback years")
    analyze_parser.add_argument("--freq", default="weekly", help="Price frequency")
    analyze_parser.add_argument("--output", default="json", help="Output format (json/markdown)")

    # balance command
    balance_parser = subparsers.add_parser("balance", help="Balance nowcast only")
    balance_parser.add_argument("--asof", default=date.today().isoformat(), help="As-of date")

    # regime command
    regime_parser = subparsers.add_parser("regime", help="Price regime only")
    regime_parser.add_argument("--chem", default="both", help="Chemical focus")

    # etf-beta command
    etf_parser = subparsers.add_parser("etf-beta", help="ETF beta only")
    etf_parser.add_argument("--ticker", default="LIT", help="ETF ticker")
    etf_parser.add_argument("--window", type=int, default=52, help="Beta window")

    args = parser.parse_args()

    # Create config from args
    config = LithiumConfig(
        etf_ticker=getattr(args, "ticker", "LIT"),
        lookback_years=getattr(args, "lookback", 10),
        price_freq=getattr(args, "freq", "weekly"),
        chem_focus=getattr(args, "chem", "both"),
        beta_window=getattr(args, "window", 52)
    )

    radar = LithiumSupplyDemandRadar(config)

    # Execute command
    if args.command == "analyze":
        result = radar.full_analysis()
    elif args.command == "balance":
        result = radar.balance_nowcast()
    elif args.command == "regime":
        result = radar.price_regime()
    elif args.command == "etf-beta":
        result = radar.etf_exposure()
    else:
        parser.print_help()
        return

    # Output
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
