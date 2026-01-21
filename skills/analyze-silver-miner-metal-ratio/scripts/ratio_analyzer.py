#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
白銀礦業/金屬比率分析器

以「白銀礦業價格 ÷ 白銀價格」的相對比率衡量礦業板塊相對於金屬本體的估值區間，
並用歷史分位數與類比區間推導「底部/頂部」訊號與情境推演。

Usage:
    python ratio_analyzer.py --quick
    python ratio_analyzer.py --miner-proxy SIL --metal-proxy SI=F --start-date 2010-01-01
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("錯誤：需要安裝 yfinance。請執行：pip install yfinance")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="白銀礦業/金屬比率分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python ratio_analyzer.py --quick
  python ratio_analyzer.py --miner-proxy SILJ --metal-proxy SLV
  python ratio_analyzer.py --start-date 2015-01-01 --freq 1mo
        """
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="使用預設參數快速分析"
    )
    parser.add_argument(
        "--miner-proxy",
        type=str,
        default="SIL",
        help="白銀礦業代表（預設：SIL）"
    )
    parser.add_argument(
        "--metal-proxy",
        type=str,
        default="SI=F",
        help="白銀價格代表（預設：SI=F）"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="歷史回溯起點（YYYY-MM-DD，預設：10 年前）"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="分析終點（YYYY-MM-DD，預設：今日）"
    )
    parser.add_argument(
        "--freq",
        type=str,
        default="1wk",
        choices=["1d", "1wk", "1mo"],
        help="取樣頻率（預設：1wk）"
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=4,
        help="比率平滑視窗（預設：4）"
    )
    parser.add_argument(
        "--bottom-quantile",
        type=float,
        default=0.20,
        help="底部估值區分位數門檻（預設：0.20）"
    )
    parser.add_argument(
        "--top-quantile",
        type=float,
        default=0.80,
        help="頂部估值區分位數門檻（預設：0.80）"
    )
    parser.add_argument(
        "--min-separation-days",
        type=int,
        default=180,
        help="類比事件去重間隔（預設：180）"
    )
    parser.add_argument(
        "--forward-horizons",
        type=str,
        default="252,504,756",
        help="前瞻期（逗號分隔，預設：252,504,756）"
    )
    parser.add_argument(
        "--scenario-target",
        type=str,
        default="return_to_top",
        choices=["return_to_top", "return_to_median"],
        help="情境推演目標（預設：return_to_top）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="輸出 JSON 檔案路徑"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細輸出"
    )

    return parser.parse_args()


def fetch_price_data(
    miner_proxy: str,
    metal_proxy: str,
    start_date: str,
    end_date: Optional[str] = None,
    verbose: bool = False
) -> Tuple[pd.Series, pd.Series]:
    """
    使用 yfinance 取得價格數據

    Parameters
    ----------
    miner_proxy : str
        礦業代理代號
    metal_proxy : str
        金屬代理代號
    start_date : str
        開始日期
    end_date : str, optional
        結束日期
    verbose : bool
        是否顯示詳細資訊

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (礦業價格序列, 金屬價格序列)
    """
    if verbose:
        print(f"正在下載數據：{miner_proxy}, {metal_proxy}")
        print(f"時間範圍：{start_date} 至 {end_date or '今日'}")

    # 下載數據
    tickers = [miner_proxy, metal_proxy]
    px = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )

    # 提取收盤價
    if isinstance(px.columns, pd.MultiIndex):
        close = px['Close']
    else:
        close = px

    # 處理缺值
    close = close.dropna(how='all')
    close = close.ffill()
    close = close.dropna()

    miner = close[miner_proxy]
    metal = close[metal_proxy]

    if verbose:
        print(f"數據點數：{len(miner)}")
        print(f"時間範圍：{miner.index.min().date()} 至 {miner.index.max().date()}")

    return miner, metal


def resample_data(
    miner: pd.Series,
    metal: pd.Series,
    freq: str
) -> Tuple[pd.Series, pd.Series]:
    """
    重新取樣數據

    Parameters
    ----------
    miner : pd.Series
        礦業價格序列
    metal : pd.Series
        金屬價格序列
    freq : str
        頻率（1d, 1wk, 1mo）

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        重新取樣後的序列
    """
    if freq == "1wk":
        miner = miner.resample("W-FRI").last()
        metal = metal.resample("W-FRI").last()
    elif freq == "1mo":
        miner = miner.resample("ME").last()
        metal = metal.resample("ME").last()
    # 1d 不需要重新取樣

    # 刪除缺值
    miner = miner.dropna()
    metal = metal.dropna()

    # 對齊索引
    common_idx = miner.index.intersection(metal.index)
    miner = miner.loc[common_idx]
    metal = metal.loc[common_idx]

    return miner, metal


def calculate_ratio(
    miner: pd.Series,
    metal: pd.Series,
    smoothing_window: int = 1
) -> pd.Series:
    """
    計算比率並可選平滑

    Parameters
    ----------
    miner : pd.Series
        礦業價格序列
    metal : pd.Series
        金屬價格序列
    smoothing_window : int
        平滑視窗

    Returns
    -------
    pd.Series
        比率序列
    """
    ratio = miner / metal

    if smoothing_window > 1:
        ratio = ratio.rolling(smoothing_window).mean()

    return ratio.dropna()


def calculate_thresholds(
    ratio: pd.Series,
    bottom_quantile: float,
    top_quantile: float
) -> Tuple[float, float, float]:
    """
    計算門檻值

    Returns
    -------
    Tuple[float, float, float]
        (底部門檻, 頂部門檻, 中位數)
    """
    bottom_thr = float(ratio.quantile(bottom_quantile))
    top_thr = float(ratio.quantile(top_quantile))
    median_thr = float(ratio.median())

    return bottom_thr, top_thr, median_thr


def determine_zone(
    current_ratio: float,
    bottom_thr: float,
    top_thr: float
) -> str:
    """判斷當前區間"""
    if current_ratio <= bottom_thr:
        return "bottom"
    elif current_ratio >= top_thr:
        return "top"
    else:
        return "neutral"


def detect_bottom_events(
    ratio: pd.Series,
    bottom_thr: float,
    min_separation_days: int
) -> List[datetime]:
    """
    偵測底部事件並去重

    Returns
    -------
    List[datetime]
        去重後的底部事件日期列表
    """
    is_bottom = ratio <= bottom_thr
    bottom_dates = ratio[is_bottom].index.tolist()

    # 去重
    dedup = []
    last = None
    for d in bottom_dates:
        if last is None or (d - last).days >= min_separation_days:
            dedup.append(d)
            last = d

    return dedup


def calculate_forward_returns(
    metal: pd.Series,
    event_dates: List[datetime],
    forward_horizons: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    計算事件後的前瞻報酬

    Returns
    -------
    Dict[int, Dict]
        各前瞻期的統計資料
    """
    results = {}

    for H in forward_horizons:
        rets = []
        for d in event_dates:
            if d in metal.index:
                i = metal.index.get_loc(d)
                j = i + H
                if j < len(metal):
                    ret = float(metal.iloc[j] / metal.iloc[i] - 1)
                    rets.append(ret)

        if rets:
            horizon_years = H / 252
            results[H] = {
                "horizon_label": f"{horizon_years:.0f} year" if horizon_years >= 1 else f"{H} days",
                "count": len(rets),
                "median": float(np.median(rets)),
                "mean": float(np.mean(rets)),
                "std": float(np.std(rets)) if len(rets) > 1 else 0.0,
                "win_rate": float(np.mean([r > 0 for r in rets])),
                "best": float(np.max(rets)),
                "worst": float(np.min(rets))
            }
        else:
            results[H] = {
                "horizon_label": f"{H} days",
                "count": 0,
                "median": None,
                "mean": None,
                "std": None,
                "win_rate": None,
                "best": None,
                "worst": None
            }

    return results


def calculate_scenarios(
    current_ratio: float,
    target_ratio: float,
    scenario_target: str
) -> Dict[str, Any]:
    """
    計算情境推演

    Returns
    -------
    Dict
        情境推演結果
    """
    miner_multiplier = target_ratio / current_ratio
    metal_multiplier = current_ratio / target_ratio
    metal_drop_pct = 1 - metal_multiplier

    target_label = "頂部" if scenario_target == "return_to_top" else "中位數"

    return {
        "target": scenario_target,
        "target_ratio": target_ratio,
        "current_ratio": current_ratio,
        "miner_multiplier_if_metal_flat": float(miner_multiplier),
        "miner_gain_pct_if_metal_flat": float(miner_multiplier - 1),
        "metal_multiplier_if_miner_flat": float(metal_multiplier),
        "metal_drop_pct_if_miner_flat": float(metal_drop_pct),
        "interpretation": {
            "miner_scenario": f"若白銀不變，礦業需漲 {(miner_multiplier - 1) * 100:.1f}% 才回到{target_label}估值",
            "metal_scenario": f"若礦業不變，白銀需跌 {metal_drop_pct * 100:.1f}% 才回到{target_label}估值"
        }
    }


def check_divergence(
    ratio_percentile: float,
    metal: pd.Series,
    bottom_quantile: float
) -> Dict[str, Any]:
    """
    檢查背離訊號

    Returns
    -------
    Dict
        背離檢查結果
    """
    metal_percentile = float(metal.rank(pct=True).iloc[-1] * 100)
    is_divergence = (ratio_percentile <= bottom_quantile * 100) and (metal_percentile > 70)

    if is_divergence:
        divergence_type = "ratio_low_metal_high"
        interpretation = "比率處於底部區間，但白銀價格處於相對高位，形成背離訊號"
    else:
        divergence_type = "none"
        interpretation = "未偵測到明顯背離"

    return {
        "current_metal_percentile": metal_percentile,
        "is_divergence": is_divergence,
        "divergence_type": divergence_type,
        "interpretation": interpretation
    }


def generate_summary(
    zone: str,
    ratio_percentile: float,
    forward_returns: Dict[int, Dict],
    miner_gain_pct: float
) -> str:
    """生成一句話結論"""
    if zone == "bottom":
        zone_desc = "底部區間"
        valuation_desc = "礦業相對白銀偏便宜"
    elif zone == "top":
        zone_desc = "頂部區間"
        valuation_desc = "礦業相對白銀偏貴"
    else:
        zone_desc = "中性區間"
        valuation_desc = "礦業相對白銀處於正常水位"

    # 取得 1 年前瞻報酬
    fwd_1y = forward_returns.get(252, {})
    if fwd_1y.get("median") is not None:
        fwd_desc = f"歷史類似情境後，白銀 1 年報酬中位數為 {fwd_1y['median'] * 100:.0f}%，勝率 {fwd_1y['win_rate'] * 100:.0f}%。"
    else:
        fwd_desc = ""

    return (
        f"白銀礦業/白銀比率目前處於歷史 {ratio_percentile:.1f} 百分位（{zone_desc}），"
        f"顯示{valuation_desc}。{fwd_desc}"
        f"若白銀不變，礦業需漲 {miner_gain_pct * 100:.1f}% 才回到頂部估值。"
    )


def analyze_silver_miner_metal_ratio(
    miner_proxy: str = "SIL",
    metal_proxy: str = "SI=F",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    freq: str = "1wk",
    smoothing_window: int = 4,
    bottom_quantile: float = 0.20,
    top_quantile: float = 0.80,
    min_separation_days: int = 180,
    forward_horizons: List[int] = None,
    scenario_target: str = "return_to_top",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    主分析函數

    Parameters
    ----------
    miner_proxy : str
        白銀礦業代表
    metal_proxy : str
        白銀價格代表
    start_date : str, optional
        歷史回溯起點
    end_date : str, optional
        分析終點
    freq : str
        取樣頻率
    smoothing_window : int
        比率平滑視窗
    bottom_quantile : float
        底部估值區分位數門檻
    top_quantile : float
        頂部估值區分位數門檻
    min_separation_days : int
        類比事件去重間隔
    forward_horizons : List[int]
        前瞻期列表
    scenario_target : str
        情境推演目標
    verbose : bool
        是否顯示詳細輸出

    Returns
    -------
    Dict
        分析結果
    """
    if forward_horizons is None:
        forward_horizons = [252, 504, 756]

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365 * 10)).strftime("%Y-%m-%d")

    # Step 1: 取得數據
    if verbose:
        print("\n=== Step 1: 取得數據 ===")
    miner, metal = fetch_price_data(miner_proxy, metal_proxy, start_date, end_date, verbose)

    # Step 2: 重新取樣
    if verbose:
        print(f"\n=== Step 2: 重新取樣（{freq}） ===")
    miner, metal = resample_data(miner, metal, freq)
    if verbose:
        print(f"取樣後數據點數：{len(miner)}")

    # Step 3: 計算比率
    if verbose:
        print(f"\n=== Step 3: 計算比率（平滑視窗={smoothing_window}） ===")
    ratio = calculate_ratio(miner, metal, smoothing_window)

    # Step 4: 計算門檻與當前狀態
    if verbose:
        print("\n=== Step 4: 計算門檻與當前狀態 ===")
    bottom_thr, top_thr, median_thr = calculate_thresholds(ratio, bottom_quantile, top_quantile)
    current_ratio = float(ratio.iloc[-1])
    ratio_percentile = float(ratio.rank(pct=True).iloc[-1] * 100)
    zone = determine_zone(current_ratio, bottom_thr, top_thr)

    if verbose:
        print(f"當前比率：{current_ratio:.4f}")
        print(f"歷史分位數：{ratio_percentile:.1f}%")
        print(f"區間：{zone}")

    # Step 5: 偵測底部事件
    if verbose:
        print("\n=== Step 5: 偵測底部事件 ===")
    bottom_events = detect_bottom_events(ratio, bottom_thr, min_separation_days)
    if verbose:
        print(f"底部事件數量：{len(bottom_events)}")

    # Step 6: 計算前瞻報酬
    if verbose:
        print("\n=== Step 6: 計算前瞻報酬 ===")
    # 需要用原始頻率的金屬數據來計算前瞻報酬
    metal_for_fwd = metal.loc[ratio.index]
    forward_returns = calculate_forward_returns(metal_for_fwd, bottom_events, forward_horizons)

    # Step 7: 情境推演
    if verbose:
        print("\n=== Step 7: 情境推演 ===")
    target_ratio = top_thr if scenario_target == "return_to_top" else median_thr
    scenarios = calculate_scenarios(current_ratio, target_ratio, scenario_target)

    # Step 8: 背離檢查
    if verbose:
        print("\n=== Step 8: 背離檢查 ===")
    divergence = check_divergence(ratio_percentile, metal, bottom_quantile)

    # Step 9: 生成結果
    if verbose:
        print("\n=== Step 9: 生成結果 ===")

    result = {
        "skill": "analyze_silver_miner_metal_ratio",
        "version": "0.1.0",
        "generated_at": datetime.now().isoformat(),

        "inputs": {
            "miner_proxy": miner_proxy,
            "metal_proxy": metal_proxy,
            "start_date": start_date,
            "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
            "freq": freq,
            "smoothing_window": smoothing_window,
            "bottom_quantile": bottom_quantile,
            "top_quantile": top_quantile,
            "min_separation_days": min_separation_days,
            "forward_horizons": forward_horizons,
            "scenario_target": scenario_target
        },

        "current": {
            "date": ratio.index[-1].strftime("%Y-%m-%d"),
            "miner_price": float(miner.iloc[-1]),
            "metal_price": float(metal.iloc[-1]),
            "ratio": float(miner.iloc[-1] / metal.iloc[-1]),
            "ratio_smoothed": current_ratio,
            "ratio_percentile": ratio_percentile,
            "zone": zone,
            "bottom_threshold": bottom_thr,
            "top_threshold": top_thr,
            "median_threshold": median_thr
        },

        "history_analogs": {
            "total_observations": len(ratio),
            "bottom_event_count": len(bottom_events),
            "bottom_event_dates": [d.strftime("%Y-%m-%d") for d in bottom_events],
            "forward_metal_returns": forward_returns
        },

        "scenarios": scenarios,
        "divergence_check": divergence,

        "summary": generate_summary(
            zone,
            ratio_percentile,
            forward_returns,
            scenarios["miner_gain_pct_if_metal_flat"]
        ),

        "notes": [
            "比率訊號衡量的是『相對估值』，不是單邊價格保證。",
            f"歷史類比樣本量僅 {len(bottom_events)} 次，統計推論能力有限。",
            "礦業可能因成本上升、地緣/政策風險、增發稀釋而合理落後。",
            "建議搭配：礦業成本曲線、COT 持倉、ETF 流量、美元/實質利率做交叉驗證。"
        ],

        "recommended_next_checks": [
            "檢查 SIL 主要成分股的 AISC 成本趨勢",
            "查看 COT 報告中的白銀投機淨部位",
            "觀察 SLV ETF 持倉量變化",
            "比較 GDX/GDXJ 是否有類似的比率低估"
        ]
    }

    return result


def main():
    """主程式入口"""
    args = parse_args()

    # 解析前瞻期
    forward_horizons = [int(x.strip()) for x in args.forward_horizons.split(",")]

    # 執行分析
    result = analyze_silver_miner_metal_ratio(
        miner_proxy=args.miner_proxy,
        metal_proxy=args.metal_proxy,
        start_date=args.start_date,
        end_date=args.end_date,
        freq=args.freq,
        smoothing_window=args.smoothing_window,
        bottom_quantile=args.bottom_quantile,
        top_quantile=args.top_quantile,
        min_separation_days=args.min_separation_days,
        forward_horizons=forward_horizons,
        scenario_target=args.scenario_target,
        verbose=args.verbose
    )

    # 輸出結果
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"結果已輸出至：{args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
