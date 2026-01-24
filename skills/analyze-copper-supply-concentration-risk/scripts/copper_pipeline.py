#!/usr/bin/env python3
"""
銅供應集中度風險分析管線

用公開資料量化「銅供應是否過度集中、主要產地是否結構性衰退、
替代增量是否依賴少數國家」，並輸出可行的中期供應風險結論與情境推演。
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('copper_pipeline')


# =============================================================================
# 數據擷取模組
# =============================================================================

def fetch_owid_copper(start_year: int, end_year: int, cache_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    從 OWID 擷取銅產量數據

    Parameters:
    -----------
    start_year : int
        起始年份
    end_year : int
        結束年份
    cache_dir : Path, optional
        快取目錄

    Returns:
    --------
    pd.DataFrame : 標準化後的產量數據
    """
    import requests
    from io import StringIO

    OWID_URL = (
        "https://raw.githubusercontent.com/owid/owid-datasets/master/"
        "datasets/Copper%20mine%20production%20(USGS%20%26%20BGS)/"
        "Copper%20mine%20production%20(USGS%20%26%20BGS).csv"
    )

    # 快取檢查
    if cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"owid_copper_{start_year}_{end_year}.csv"

        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age.days < 7:
                logger.info(f"使用快取: {cache_file}")
                return pd.read_csv(cache_file)

    # 下載數據
    logger.info("從 OWID 下載銅產量數據...")
    try:
        response = requests.get(OWID_URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"OWID 請求失敗: {e}")
        raise

    # 解析 CSV
    df = pd.read_csv(StringIO(response.text))

    # 標準化欄位
    df = df.rename(columns={
        "Entity": "country",
        "Year": "year",
        "Copper mine production (USGS & BGS)": "production"
    })

    # 國家名稱標準化
    country_mapping = {
        "Democratic Republic of the Congo": "Democratic Republic of Congo",
        "DRC": "Democratic Republic of Congo",
        "United States of America": "United States",
    }
    df["country"] = df["country"].replace(country_mapping)

    # 過濾年份
    df = df[(df.year >= start_year) & (df.year <= end_year)]

    # 添加標準欄位
    df["unit"] = "t_Cu_content"
    df["source_id"] = "OWID"
    df["confidence"] = 0.9

    # 保存快取
    if cache_dir:
        df.to_csv(cache_file, index=False)
        logger.info(f"數據已快取: {cache_file}")

    return df[["year", "country", "production", "unit", "source_id", "confidence"]]


# =============================================================================
# 集中度計算模組
# =============================================================================

def compute_shares(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """計算各國市場份額"""
    year_data = df[df.year == year].copy()

    # 取得世界總量
    world_row = year_data[year_data.country == "World"]
    if world_row.empty:
        world_total = year_data.production.sum()
    else:
        world_total = world_row.production.values[0]
        year_data = year_data[year_data.country != "World"]

    # 計算份額
    year_data["share"] = year_data.production / world_total
    year_data = year_data.sort_values("share", ascending=False).reset_index(drop=True)
    year_data["cumulative_share"] = year_data.share.cumsum()

    return year_data


def compute_hhi(shares_df: pd.DataFrame) -> float:
    """計算 Herfindahl-Hirschman Index"""
    return ((shares_df["share"] * 100) ** 2).sum()


def compute_cr_n(shares_df: pd.DataFrame, n: int) -> float:
    """計算前 N 大國家集中度"""
    return shares_df.head(n)["share"].sum()


def classify_market_structure(hhi: float) -> str:
    """根據 HHI 分類市場結構"""
    if hhi < 1500:
        return "低集中 (Unconcentrated)"
    elif hhi < 2500:
        return "中等集中 (Moderately Concentrated)"
    else:
        return "高集中 (Highly Concentrated)"


def analyze_concentration(df: pd.DataFrame, year: int) -> dict:
    """完整集中度分析"""
    shares = compute_shares(df, year)

    hhi = compute_hhi(shares)
    cr4 = compute_cr_n(shares, 4)
    cr8 = compute_cr_n(shares, 8)

    chile_row = shares[shares.country == "Chile"]
    chile_share = chile_row["share"].values[0] if not chile_row.empty else 0

    top_producers = shares.head(5)[["country", "production", "share"]].to_dict("records")

    return {
        "year": year,
        "hhi": round(hhi, 0),
        "cr4": round(cr4, 4),
        "cr8": round(cr8, 4),
        "chile_share": round(chile_share, 4),
        "market_structure": classify_market_structure(hhi),
        "top_producers": top_producers
    }


# =============================================================================
# 智利趨勢分析模組
# =============================================================================

def rolling_slope(series: pd.Series, window: int = 10) -> pd.Series:
    """計算滾動線性回歸斜率"""
    slopes = []
    years = series.index.values

    for i in range(window - 1, len(series)):
        y = series.values[i - window + 1:i + 1]
        x = years[i - window + 1:i + 1]
        coeffs = np.polyfit(x, y, 1)
        slopes.append(coeffs[0])

    result = [np.nan] * (window - 1) + slopes
    return pd.Series(result, index=series.index)


def find_breakpoint_simple(series: pd.Series, min_segment: int = 5) -> dict:
    """簡易結構斷點偵測"""
    years = series.index.values
    values = series.values
    n = len(series)

    if n < min_segment * 2:
        return {"detected": False, "reason": "數據長度不足"}

    best_mse = float('inf')
    best_break = None

    for i in range(min_segment, n - min_segment):
        # 前段回歸
        x1, y1 = years[:i], values[:i]
        p1 = np.polyfit(x1, y1, 1)
        mse1 = np.mean((y1 - np.polyval(p1, x1)) ** 2)

        # 後段回歸
        x2, y2 = years[i:], values[i:]
        p2 = np.polyfit(x2, y2, 1)
        mse2 = np.mean((y2 - np.polyval(p2, x2)) ** 2)

        total_mse = mse1 * len(x1) + mse2 * len(x2)

        if total_mse < best_mse:
            best_mse = total_mse
            best_break = {
                "detected": True,
                "break_year": int(years[i]),
                "pre_slope": p1[0],
                "post_slope": p2[0]
            }

    return best_break


def analyze_chile_trend(df: pd.DataFrame, window: int = 10) -> dict:
    """智利產量趨勢分析"""
    chile_data = df[df.country == "Chile"].sort_values("year")
    chile_series = chile_data.set_index("year")["production"]

    # 峰值分析
    peak_idx = chile_series.idxmax()
    peak_production = chile_series[peak_idx]
    latest_production = chile_series.iloc[-1]
    latest_year = chile_series.index[-1]

    # 回撤
    drawdown = (peak_production - latest_production) / peak_production

    # 滾動斜率
    slopes = rolling_slope(chile_series, window)
    latest_slope = slopes.iloc[-1]

    # 斷點偵測
    breakpoint = find_breakpoint_simple(chile_series)

    # 判定
    if latest_slope < -20000 and drawdown > 0.10 and breakpoint.get("detected", False):
        classification = "structural_decline"
    elif abs(latest_slope) < 20000 and drawdown > 0.05:
        classification = "plateau"
    elif latest_slope > 0:
        classification = "growth"
    else:
        classification = "uncertain"

    return {
        "peak_year": int(peak_idx),
        "peak_production_mt": round(peak_production / 1e6, 2),
        "latest_year": int(latest_year),
        "latest_production_mt": round(latest_production / 1e6, 2),
        "drawdown": round(drawdown, 4),
        "rolling_slope_t_per_year": round(latest_slope, 0),
        "rolling_window": window,
        "structural_break": breakpoint,
        "classification": classification
    }


# =============================================================================
# 替代依賴度分析模組
# =============================================================================

def analyze_replacement(df: pd.DataFrame, chile_decline: float, horizon: int = 10) -> dict:
    """秘魯與 DRC 替代依賴度分析"""

    def compute_country_growth(country: str) -> dict:
        country_data = df[df.country == country].sort_values("year")
        if len(country_data) < 11:
            return None

        recent = country_data.tail(11)
        start_prod = recent.iloc[0].production
        end_prod = recent.iloc[-1].production
        cagr = (end_prod / start_prod) ** 0.1 - 1

        # 預測增量
        future_prod = end_prod * (1 + cagr) ** horizon
        expected_increment = future_prod - end_prod

        return {
            "country": country,
            "start_production": start_prod,
            "end_production": end_prod,
            "historical_cagr": round(cagr, 4),
            "expected_increment": expected_increment
        }

    peru = compute_country_growth("Peru")
    drc = compute_country_growth("Democratic Republic of Congo")

    if not peru or not drc:
        return {"error": "數據不足"}

    # 執行係數調整
    peru_multiplier = 0.8
    drc_multiplier = 0.7

    peru_adjusted = peru["expected_increment"] * peru_multiplier
    drc_adjusted = drc["expected_increment"] * drc_multiplier

    total_replacement = peru_adjusted + drc_adjusted
    ratio = total_replacement / max(abs(chile_decline), 1)
    gap = chile_decline - total_replacement

    return {
        "chile_decline": round(chile_decline / 1e6, 2),
        "peru": {
            "historical_cagr": peru["historical_cagr"],
            "expected_increment_mt": round(peru["expected_increment"] / 1e6, 2),
            "multiplier": peru_multiplier,
            "adjusted_increment_mt": round(peru_adjusted / 1e6, 2)
        },
        "drc": {
            "historical_cagr": drc["historical_cagr"],
            "expected_increment_mt": round(drc["expected_increment"] / 1e6, 2),
            "multiplier": drc_multiplier,
            "adjusted_increment_mt": round(drc_adjusted / 1e6, 2)
        },
        "replacement_ratio": round(ratio, 2),
        "gap_mt": round(gap / 1e6, 2)
    }


# =============================================================================
# 主分析類別
# =============================================================================

class CopperSupplyAnalyzer:
    """銅供應集中度風險分析器"""

    def __init__(
        self,
        start_year: int = 1970,
        end_year: int = 2023,
        cache_dir: Optional[str] = None
    ):
        self.start_year = start_year
        self.end_year = end_year
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache")
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """載入數據"""
        if self.df is None:
            self.df = fetch_owid_copper(self.start_year, self.end_year, self.cache_dir)
        return self.df

    def analyze_concentration(self) -> dict:
        """執行集中度分析"""
        df = self.load_data()
        return analyze_concentration(df, self.end_year)

    def analyze_chile_trend(self, window: int = 10) -> dict:
        """執行智利趨勢分析"""
        df = self.load_data()
        return analyze_chile_trend(df, window)

    def analyze_replacement(self, horizon: int = 10) -> dict:
        """執行替代依賴度分析"""
        df = self.load_data()
        chile_trend = analyze_chile_trend(df)
        chile_decline = chile_trend["rolling_slope_t_per_year"] * horizon
        return analyze_replacement(df, chile_decline, horizon)

    def generate_full_report(self, output_format: str = "json") -> dict:
        """生成完整報告"""
        logger.info("開始完整分析...")

        concentration = self.analyze_concentration()
        chile_trend = self.analyze_chile_trend()
        replacement = self.analyze_replacement()

        report = {
            "commodity": "copper",
            "analysis_type": "full_report",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start_year": self.start_year,
                "end_year": self.end_year
            },
            "proposition_a": concentration,
            "proposition_b": chile_trend,
            "proposition_c": replacement,
            "data_sources": ["OWID Minerals"]
        }

        logger.info("分析完成")
        return report


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="銅供應集中度風險分析")
    parser.add_argument("command", choices=["analyze", "trend", "replacement", "full-report"],
                        help="分析命令")
    parser.add_argument("--start", type=int, default=1970, help="起始年份")
    parser.add_argument("--end", type=int, default=2023, help="結束年份")
    parser.add_argument("--output", choices=["json", "markdown"], default="json",
                        help="輸出格式")
    parser.add_argument("--cache-dir", type=str, default="data/cache",
                        help="快取目錄")

    args = parser.parse_args()

    analyzer = CopperSupplyAnalyzer(
        start_year=args.start,
        end_year=args.end,
        cache_dir=args.cache_dir
    )

    if args.command == "analyze":
        result = analyzer.analyze_concentration()
    elif args.command == "trend":
        result = analyzer.analyze_chile_trend()
    elif args.command == "replacement":
        result = analyzer.analyze_replacement()
    elif args.command == "full-report":
        result = analyzer.generate_full_report(args.output)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
