#!/usr/bin/env python3
"""
宏觀指標抓取腳本

從 Yahoo Finance 和 FRED 抓取宏觀指標資料。
"""

import argparse
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

# 嘗試導入 yfinance，若失敗則使用 FRED 替代
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("Warning: yfinance not installed, using FRED fallback")


# 預設指標設定
DEFAULT_INDICATORS = {
    "usd": {
        "yahoo": "UUP",
        "fred": "DTWEXBGS",
        "description": "美元指數代理",
    },
    "crude": {
        "yahoo": "CL=F",
        "fred": "DCOILWTICO",
        "description": "WTI 原油",
    },
    "metals": {
        "yahoo": "XME",
        "fred": None,  # FRED 無直接金屬 ETF
        "description": "金屬礦業 ETF",
    },
    "agri": {
        "yahoo": "DBA",
        "fred": None,
        "description": "農產品 ETF",
    },
}

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_yahoo_series(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 抓取序列"""
    if not HAS_YFINANCE:
        raise ImportError("yfinance not installed")

    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    if df.empty:
        return pd.Series(dtype=float)

    return df["Adj Close"]


def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取序列（無需 API key）"""
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date,
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
        df = df.dropna().set_index("DATE")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)


def fetch_indicator(
    indicator_name: str,
    start_date: str,
    end_date: str,
    source: str = "yahoo",
) -> pd.Series:
    """抓取單一指標"""
    config = DEFAULT_INDICATORS.get(indicator_name)
    if config is None:
        raise ValueError(f"Unknown indicator: {indicator_name}")

    if source == "yahoo" and HAS_YFINANCE:
        symbol = config.get("yahoo")
        if symbol:
            return fetch_yahoo_series(symbol, start_date, end_date)

    # Fallback to FRED
    fred_id = config.get("fred")
    if fred_id:
        return fetch_fred_series(fred_id, start_date, end_date)

    raise ValueError(f"No available source for {indicator_name}")


def fetch_all_indicators(
    start_date: str,
    end_date: str,
    indicators: list = None,
) -> pd.DataFrame:
    """抓取所有指標"""
    if indicators is None:
        indicators = ["usd", "crude", "metals"]

    data = {}
    for ind in indicators:
        print(f"Fetching {ind}...")
        try:
            series = fetch_indicator(ind, start_date, end_date)
            data[ind] = series
        except Exception as e:
            print(f"  Failed: {e}")
            data[ind] = pd.Series(dtype=float)

    df = pd.DataFrame(data)
    df.index.name = "date"

    return df


def calculate_returns(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """計算報酬率"""
    returns = df.pct_change(periods)
    returns.columns = [f"{col}_ret" for col in returns.columns]
    return returns


def calculate_tailwind_score(returns_df: pd.DataFrame) -> pd.Series:
    """計算宏觀順風評分"""
    scores = []

    for date, row in returns_df.iterrows():
        flags = [
            row.get("usd_ret", 0) < 0,      # USD 走弱
            row.get("crude_ret", 0) > 0,    # 原油走強
            row.get("metals_ret", 0) > 0,   # 金屬走強
        ]
        score = sum(flags) / len(flags) if flags else 0
        scores.append(score)

    return pd.Series(scores, index=returns_df.index, name="macro_tailwind")


def main():
    parser = argparse.ArgumentParser(description="Fetch macro indicators")
    parser.add_argument(
        "--indicators",
        type=str,
        default="usd,crude,metals",
        help="Comma-separated list of indicators",
    )
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output",
        type=str,
        default="cache/macro_data.parquet",
        help="Output file path",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="yahoo",
        choices=["yahoo", "fred"],
        help="Data source",
    )

    args = parser.parse_args()

    indicators = [i.strip() for i in args.indicators.split(",")]

    # 抓取資料
    df = fetch_all_indicators(args.start, args.end, indicators)

    # 計算報酬
    returns = calculate_returns(df, periods=5)  # 5 日報酬

    # 計算順風評分
    tailwind = calculate_tailwind_score(returns)

    # 合併
    result = pd.concat([df, returns, tailwind], axis=1)

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存
    result.to_parquet(output_path)
    print(f"Macro data saved to {output_path}")
    print(f"Date range: {result.index.min()} to {result.index.max()}")
    print(f"Indicators: {list(df.columns)}")


if __name__ == "__main__":
    main()
