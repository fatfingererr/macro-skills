#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FRED 數據抓取工具

從 FRED CSV 端點抓取經濟數據，無需 API key。
支援勞動市場、GDP、財政等系列數據。
"""

import argparse
import json
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

# 預設數據系列配置
DEFAULT_SERIES = {
    "labor": ["UNRATE", "UNEMPLOY", "JTSJOL", "ICSA"],
    "gdp": ["GDP", "GDPC1"],
    "fiscal": ["FYFSGDA188S"],
    "all": ["UNRATE", "UNEMPLOY", "JTSJOL", "ICSA", "GDP", "GDPC1", "FYFSGDA188S"]
}

# 快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_MAX_AGE_HOURS = 12


def fetch_fred_csv(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True
) -> pd.Series:
    """
    從 FRED CSV 端點抓取單一數據系列

    Parameters
    ----------
    series_id : str
        FRED 系列代碼（如 UNRATE, GDP）
    start_date : str, optional
        起始日期 (YYYY-MM-DD)
    end_date : str, optional
        結束日期 (YYYY-MM-DD)
    use_cache : bool
        是否使用本地快取

    Returns
    -------
    pd.Series
        時間序列數據，index 為日期
    """
    # 檢查快取
    if use_cache:
        cached = _get_cached(series_id)
        if cached is not None:
            print(f"  {series_id}: 使用快取")
            return cached

    # 構建 URL
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    if start_date:
        url += f"&cosd={start_date}"
    if end_date:
        url += f"&coed={end_date}"

    # 請求數據
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"FRED 請求失敗 ({series_id}): {e}")

    # 解析 CSV
    try:
        df = pd.read_csv(
            StringIO(response.text),
            parse_dates=["DATE"],
            index_col="DATE"
        )
        series = df[series_id].replace(".", pd.NA).astype(float)
        series.name = series_id
    except Exception as e:
        raise RuntimeError(f"解析 {series_id} 數據失敗: {e}")

    # 保存快取
    if use_cache:
        _save_cache(series_id, series)

    print(f"  {series_id}: 從 FRED 抓取 ({len(series)} 筆)")
    return series


def fetch_multiple_series(
    series_ids: List[str],
    years: int = 30,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    批量抓取多個 FRED 系列

    Parameters
    ----------
    series_ids : list
        FRED 系列代碼列表
    years : int
        回看年數
    use_cache : bool
        是否使用本地快取

    Returns
    -------
    pd.DataFrame
        合併的數據框，columns 為系列代碼
    """
    start_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")

    print(f"正在抓取 {len(series_ids)} 個數據系列（回看 {years} 年）...")

    data = {}
    failed = []

    for sid in series_ids:
        try:
            data[sid] = fetch_fred_csv(sid, start_date=start_date, use_cache=use_cache)
        except Exception as e:
            print(f"  {sid}: 失敗 - {e}")
            failed.append(sid)

    if failed:
        print(f"\n警告：{len(failed)} 個系列抓取失敗: {failed}")

    df = pd.DataFrame(data)
    print(f"\n數據範圍: {df.index.min()} 至 {df.index.max()}")
    print(f"成功抓取: {len(data)}/{len(series_ids)} 個系列")

    return df


def _get_cached(series_id: str) -> Optional[pd.Series]:
    """檢查並讀取快取"""
    cache_file = CACHE_DIR / f"{series_id}.csv"

    if not cache_file.exists():
        return None

    # 檢查快取時效
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - mtime > timedelta(hours=CACHE_MAX_AGE_HOURS):
        return None

    try:
        series = pd.read_csv(cache_file, index_col=0, parse_dates=True).squeeze()
        series.name = series_id
        return series
    except Exception:
        return None


def _save_cache(series_id: str, series: pd.Series):
    """保存到快取"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{series_id}.csv"
    series.to_csv(cache_file)


def clear_cache():
    """清除所有快取"""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.csv"):
            f.unlink()
        print(f"已清除快取目錄: {CACHE_DIR}")
    else:
        print("快取目錄不存在")


def validate_data(df: pd.DataFrame) -> Dict:
    """
    驗證數據品質

    Parameters
    ----------
    df : pd.DataFrame
        數據框

    Returns
    -------
    dict
        驗證結果
    """
    results = {
        "valid": True,
        "issues": [],
        "coverage": {}
    }

    for col in df.columns:
        series = df[col].dropna()

        # 檢查是否有數據
        if len(series) == 0:
            results["issues"].append(f"{col}: 無有效數據")
            results["valid"] = False
            continue

        # 記錄覆蓋範圍
        results["coverage"][col] = {
            "start": series.index.min().strftime("%Y-%m-%d"),
            "end": series.index.max().strftime("%Y-%m-%d"),
            "count": len(series),
            "missing_pct": (df[col].isna().sum() / len(df)) * 100
        }

        # 檢查缺失值
        missing_pct = results["coverage"][col]["missing_pct"]
        if missing_pct > 20:
            results["issues"].append(f"{col}: 缺失值過多 ({missing_pct:.1f}%)")

    return results


def main():
    parser = argparse.ArgumentParser(description="FRED 數據抓取工具")
    parser.add_argument(
        "--series",
        type=str,
        default="all",
        help="數據系列，可用: labor, gdp, fiscal, all 或逗號分隔的代碼"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=30,
        help="回看年數 (預設: 30)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="不使用快取"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="清除快取後退出"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="輸出 CSV 檔案路徑"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="驗證數據並輸出報告"
    )

    args = parser.parse_args()

    # 清除快取
    if args.clear_cache:
        clear_cache()
        return

    # 解析系列
    if args.series in DEFAULT_SERIES:
        series_ids = DEFAULT_SERIES[args.series]
    else:
        series_ids = [s.strip() for s in args.series.split(",")]

    # 抓取數據
    df = fetch_multiple_series(
        series_ids,
        years=args.years,
        use_cache=not args.no_cache
    )

    # 驗證
    if args.validate:
        print("\n數據驗證報告:")
        print("-" * 40)
        results = validate_data(df)
        for col, cov in results["coverage"].items():
            print(f"{col}:")
            print(f"  範圍: {cov['start']} - {cov['end']}")
            print(f"  筆數: {cov['count']}")
            print(f"  缺失: {cov['missing_pct']:.1f}%")
        if results["issues"]:
            print("\n問題:")
            for issue in results["issues"]:
                print(f"  - {issue}")

    # 輸出
    if args.output:
        df.to_csv(args.output)
        print(f"\n數據已保存至: {args.output}")
    else:
        print("\n最新數據:")
        print(df.tail(5))


if __name__ == "__main__":
    main()
