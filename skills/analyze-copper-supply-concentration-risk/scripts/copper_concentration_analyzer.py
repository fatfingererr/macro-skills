#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
銅供應集中度分析器

計算全球銅供應的集中度指標（HHI, CR4, CR8）、智利產量趨勢分析、
以及秘魯/DRC 替代依賴度評估。

Usage:
    # 快速檢查最新集中度
    python copper_concentration_analyzer.py --quick

    # 完整分析（1970-2023）
    python copper_concentration_analyzer.py --start 1970 --end 2023

    # 智利趨勢分析
    python copper_concentration_analyzer.py --chile-trend --window 10

    # 輸出完整報告
    python copper_concentration_analyzer.py --full-report --output markdown
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd


# ==================== 集中度計算 ====================

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
    for p in top_producers:
        p["production_mt"] = round(p["production"] / 1e6, 2)
        del p["production"]

    return {
        "year": year,
        "hhi": round(hhi, 0),
        "cr4": round(cr4, 4),
        "cr8": round(cr8, 4),
        "chile_share": round(chile_share, 4),
        "market_structure": classify_market_structure(hhi),
        "top_producers": top_producers
    }


def analyze_concentration_trend(df: pd.DataFrame, start_year: int, end_year: int) -> dict:
    """分析集中度時序趨勢"""
    results = []
    available_years = sorted(df['year'].unique())

    for year in available_years:
        if start_year <= year <= end_year:
            try:
                result = analyze_concentration(df, year)
                results.append(result)
            except Exception as e:
                print(f"[Warning] 跳過 {year}: {e}")

    if not results:
        return {"error": "無可用數據"}

    # 計算趨勢
    latest = results[-1]
    first = results[0]

    # 找 10 年前的數據
    ten_years_ago = [r for r in results if r["year"] == latest["year"] - 10]
    hhi_10y_ago = ten_years_ago[0]["hhi"] if ten_years_ago else None

    return {
        "period": {"start_year": first["year"], "end_year": latest["year"]},
        "hhi_latest": latest["hhi"],
        "hhi_first": first["hhi"],
        "hhi_10y_ago": hhi_10y_ago,
        "hhi_change": latest["hhi"] - first["hhi"],
        "trend_direction": "上升" if latest["hhi"] > first["hhi"] else "下降",
        "cr4_latest": latest["cr4"],
        "cr8_latest": latest["cr8"],
        "market_structure": latest["market_structure"],
        "chile_share_latest": latest["chile_share"],
        "top_producers": latest["top_producers"],
        "yearly_data": results
    }


# ==================== 智利趨勢分析 ====================

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
                "pre_slope": round(p1[0], 0),
                "post_slope": round(p2[0], 0)
            }

    return best_break


def analyze_chile_trend(df: pd.DataFrame, window: int = 10) -> dict:
    """智利產量趨勢分析"""
    chile_data = df[df.country == "Chile"].sort_values("year")

    if chile_data.empty:
        return {"error": "無智利數據"}

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
    latest_slope = slopes.iloc[-1] if not np.isnan(slopes.iloc[-1]) else 0

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
        "country": "Chile",
        "peak_year": int(peak_idx),
        "peak_production_mt": round(peak_production / 1e6, 2),
        "latest_year": int(latest_year),
        "latest_production_mt": round(latest_production / 1e6, 2),
        "drawdown": round(drawdown, 4),
        "drawdown_pct": f"{drawdown * 100:.1f}%",
        "rolling_slope_t_per_year": round(latest_slope, 0),
        "rolling_window": window,
        "structural_break": breakpoint,
        "classification": classification,
        "classification_cn": {
            "structural_decline": "結構性衰退",
            "plateau": "高原期",
            "growth": "仍在增長",
            "uncertain": "不確定"
        }.get(classification, classification)
    }


# ==================== 替代依賴度分析 ====================

def analyze_replacement(df: pd.DataFrame, chile_decline: float, horizon: int = 10) -> dict:
    """秘魯與 DRC 替代依賴度分析"""

    def compute_country_growth(country: str) -> Optional[dict]:
        country_data = df[df.country == country].sort_values("year")
        if len(country_data) < 11:
            return None

        recent = country_data.tail(11)
        start_prod = recent.iloc[0].production
        end_prod = recent.iloc[-1].production

        if start_prod <= 0:
            return None

        cagr = (end_prod / start_prod) ** 0.1 - 1

        # 預測增量
        future_prod = end_prod * (1 + cagr) ** horizon
        expected_increment = future_prod - end_prod

        return {
            "country": country,
            "latest_production_mt": round(end_prod / 1e6, 2),
            "historical_cagr": round(cagr, 4),
            "expected_increment_mt": round(expected_increment / 1e6, 2)
        }

    peru = compute_country_growth("Peru")
    drc = compute_country_growth("Democratic Republic of Congo")

    if not peru or not drc:
        return {"error": "秘魯或 DRC 數據不足"}

    # 執行係數調整（考慮執行風險）
    peru_multiplier = 0.8
    drc_multiplier = 0.7

    peru_adjusted = peru["expected_increment_mt"] * peru_multiplier
    drc_adjusted = drc["expected_increment_mt"] * drc_multiplier

    total_replacement = peru_adjusted + drc_adjusted
    chile_decline_mt = abs(chile_decline) / 1e6

    if chile_decline_mt > 0:
        ratio = total_replacement / chile_decline_mt
    else:
        ratio = float('inf')

    gap = chile_decline_mt - total_replacement

    return {
        "horizon_years": horizon,
        "chile_decline_mt": round(chile_decline_mt, 2),
        "peru": {
            "historical_cagr": peru["historical_cagr"],
            "expected_increment_mt": peru["expected_increment_mt"],
            "execution_multiplier": peru_multiplier,
            "adjusted_increment_mt": round(peru_adjusted, 2)
        },
        "drc": {
            "historical_cagr": drc["historical_cagr"],
            "expected_increment_mt": drc["expected_increment_mt"],
            "execution_multiplier": drc_multiplier,
            "adjusted_increment_mt": round(drc_adjusted, 2)
        },
        "total_replacement_mt": round(total_replacement, 2),
        "replacement_ratio": round(ratio, 2),
        "gap_mt": round(gap, 2),
        "assessment": "替代充足" if ratio >= 1.0 else "替代不足"
    }


# ==================== 主分析類 ====================

class CopperConcentrationAnalyzer:
    """銅供應集中度分析器"""

    def __init__(
        self,
        df: pd.DataFrame = None,
        cache_dir: str = "cache"
    ):
        self.df = df
        self.cache_dir = Path(cache_dir)

    def load_data(self) -> pd.DataFrame:
        """載入數據"""
        if self.df is not None:
            return self.df

        # 嘗試從快取載入
        csv_path = self.cache_dir / "copper_production.csv"
        if csv_path.exists():
            print(f"[Data] 載入快取: {csv_path}")
            self.df = pd.read_csv(csv_path)
            return self.df

        raise FileNotFoundError(
            "找不到數據。請先執行 fetch_copper_production.py --cdp"
        )

    def quick_check(self) -> dict:
        """快速檢查最新集中度"""
        df = self.load_data()
        latest_year = df['year'].max()
        return analyze_concentration(df, latest_year)

    def analyze_concentration(self, start_year: int = 1970, end_year: int = None) -> dict:
        """執行集中度趨勢分析"""
        df = self.load_data()
        if end_year is None:
            end_year = df['year'].max()
        return analyze_concentration_trend(df, start_year, end_year)

    def analyze_chile_trend(self, window: int = 10) -> dict:
        """執行智利趨勢分析"""
        df = self.load_data()
        return analyze_chile_trend(df, window)

    def analyze_replacement(self, horizon: int = 10) -> dict:
        """執行替代依賴度分析"""
        df = self.load_data()
        chile_trend = analyze_chile_trend(df)

        if "error" in chile_trend:
            return {"error": chile_trend["error"]}

        chile_decline = chile_trend["rolling_slope_t_per_year"] * horizon
        return analyze_replacement(df, chile_decline, horizon)

    def generate_full_report(self, start_year: int = 1970, end_year: int = None) -> dict:
        """生成完整報告"""
        df = self.load_data()
        if end_year is None:
            end_year = df['year'].max()

        concentration = self.analyze_concentration(start_year, end_year)
        chile_trend = self.analyze_chile_trend()
        replacement = self.analyze_replacement()

        return {
            "commodity": "copper",
            "analysis_type": "full_report",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start_year": start_year,
                "end_year": end_year
            },
            "data_source": {
                "primary": "MacroMicro (WBMS)",
                "url": "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world",
                "unit": "tonnes of copper content"
            },
            "proposition_a_concentration": concentration,
            "proposition_b_chile_trend": chile_trend,
            "proposition_c_replacement": replacement
        }


# ==================== 報告生成 ====================

def format_markdown_report(report: dict) -> str:
    """生成 Markdown 格式報告"""
    conc = report.get("proposition_a_concentration", {})
    chile = report.get("proposition_b_chile_trend", {})
    repl = report.get("proposition_c_replacement", {})

    lines = [
        f"# 銅供應集中度風險分析報告",
        f"",
        f"**分析期間**: {report['period']['start_year']} - {report['period']['end_year']}",
        f"**生成時間**: {report['generated_at'][:10]}",
        f"**數據來源**: {report['data_source']['primary']}",
        f"",
        f"---",
        f"",
        f"## 執行摘要",
        f"",
        f"全球銅供應呈現 **{conc.get('market_structure', 'N/A')}** 結構。",
        f"HHI 指數為 {conc.get('hhi_latest', 'N/A'):.0f}，",
        f"較分析初期 {conc.get('trend_direction', 'N/A')} {abs(conc.get('hhi_change', 0)):.0f} 點。",
        f"前四大生產國控制 {conc.get('cr4_latest', 0) * 100:.1f}% 的全球供應。",
        f"",
        f"## 命題 A：供應集中度",
        f"",
        f"| 指標 | 最新值 | 解讀 |",
        f"|------|--------|------|",
        f"| HHI | {conc.get('hhi_latest', 'N/A'):.0f} | {conc.get('market_structure', 'N/A')} |",
        f"| CR4 | {conc.get('cr4_latest', 0) * 100:.1f}% | 前四國份額 |",
        f"| CR8 | {conc.get('cr8_latest', 0) * 100:.1f}% | 前八國份額 |",
        f"| 智利份額 | {conc.get('chile_share_latest', 0) * 100:.1f}% | 最大單一國家 |",
        f"",
        f"### 前五大生產國",
        f"",
        f"| 排名 | 國家 | 產量 (Mt) | 份額 |",
        f"|------|------|-----------|------|",
    ]

    for i, p in enumerate(conc.get('top_producers', [])[:5], 1):
        lines.append(f"| {i} | {p['country']} | {p['production_mt']:.2f} | {p['share'] * 100:.1f}% |")

    lines.extend([
        f"",
        f"## 命題 B：智利結構趨勢",
        f"",
        f"| 指標 | 值 |",
        f"|------|-----|",
        f"| 峰值年 | {chile.get('peak_year', 'N/A')} |",
        f"| 峰值產量 | {chile.get('peak_production_mt', 'N/A')} Mt |",
        f"| 最新產量 | {chile.get('latest_production_mt', 'N/A')} Mt ({chile.get('latest_year', 'N/A')}) |",
        f"| 峰值回撤 | {chile.get('drawdown_pct', 'N/A')} |",
        f"| 趨勢斜率 | {chile.get('rolling_slope_t_per_year', 'N/A')} t/年 |",
        f"| 分類 | {chile.get('classification_cn', 'N/A')} |",
        f"",
    ])

    if chile.get('structural_break', {}).get('detected'):
        sb = chile['structural_break']
        lines.extend([
            f"**結構斷點**: {sb['break_year']} 年",
            f"- 斷點前斜率: {sb['pre_slope']:.0f} t/年",
            f"- 斷點後斜率: {sb['post_slope']:.0f} t/年",
            f"",
        ])

    lines.extend([
        f"## 命題 C：替代依賴度",
        f"",
        f"| 指標 | 值 |",
        f"|------|-----|",
        f"| 智利預期衰退 | {repl.get('chile_decline_mt', 'N/A')} Mt ({repl.get('horizon_years', 10)} 年) |",
        f"| 秘魯增量 | {repl.get('peru', {}).get('adjusted_increment_mt', 'N/A')} Mt |",
        f"| DRC 增量 | {repl.get('drc', {}).get('adjusted_increment_mt', 'N/A')} Mt |",
        f"| 替代比率 | {repl.get('replacement_ratio', 'N/A')} |",
        f"| 缺口 | {repl.get('gap_mt', 'N/A')} Mt |",
        f"| 評估 | {repl.get('assessment', 'N/A')} |",
        f"",
        f"---",
        f"",
        f"## 數據來源",
        f"",
        f"- {report['data_source']['url']}",
        f"- 口徑: {report['data_source']['unit']}",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="銅供應集中度分析",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--quick", action="store_true", help="快速檢查最新集中度")
    parser.add_argument("--start", type=int, default=1970, help="分析起始年 (預設: 1970)")
    parser.add_argument("--end", type=int, default=None, help="分析結束年 (預設: 最新)")
    parser.add_argument("--chile-trend", action="store_true", help="智利趨勢分析")
    parser.add_argument("--window", type=int, default=10, help="滾動斜率窗口 (預設: 10)")
    parser.add_argument("--replacement", action="store_true", help="替代依賴度分析")
    parser.add_argument("--horizon", type=int, default=10, help="替代分析年限 (預設: 10)")
    parser.add_argument("--full-report", action="store_true", help="完整報告")
    parser.add_argument("--output", choices=["json", "markdown"], default="json", help="輸出格式")
    parser.add_argument("--cache-dir", type=str, default="cache", help="快取目錄")

    args = parser.parse_args()

    try:
        analyzer = CopperConcentrationAnalyzer(cache_dir=args.cache_dir)

        if args.quick:
            result = analyzer.quick_check()
        elif args.chile_trend:
            result = analyzer.analyze_chile_trend(window=args.window)
        elif args.replacement:
            result = analyzer.analyze_replacement(horizon=args.horizon)
        elif args.full_report:
            result = analyzer.generate_full_report(start_year=args.start, end_year=args.end)
        else:
            result = analyzer.analyze_concentration(start_year=args.start, end_year=args.end)

        if args.output == "markdown" and args.full_report:
            print(format_markdown_report(result))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except FileNotFoundError as e:
        print(f"[Error] {e}")
        print("\n請先執行數據抓取:")
        print("  1. 啟動 Chrome 調試模式")
        print("  2. python fetch_copper_production.py --cdp")


if __name__ == "__main__":
    main()
