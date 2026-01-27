#!/usr/bin/env python3
"""
宏觀指標抓取腳本

從 Yahoo Finance 和 FRED 抓取宏觀指標資料。
"""

import argparse
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict

import pandas as pd
import requests

# 嘗試導入 yfinance
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
        "description": "美元指數代理 (Invesco DB US Dollar Index)",
    },
    "crude": {
        "yahoo": "CL=F",
        "fred": "DCOILWTICO",
        "description": "WTI 原油期貨",
    },
    "metals": {
        "yahoo": "XME",
        "fred": None,
        "description": "SPDR S&P Metals & Mining ETF",
    },
    "agri": {
        "yahoo": "DBA",
        "fred": None,
        "description": "Invesco DB Agriculture Fund",
    },
    "gold": {
        "yahoo": "GC=F",
        "fred": None,
        "description": "黃金期貨",
    },
}

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_yahoo_series(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """從 Yahoo Finance 抓取序列"""
    if not HAS_YFINANCE:
        raise ImportError("yfinance not installed")

    print(f"  Downloading {symbol} from Yahoo Finance...")
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)

    if df.empty:
        print(f"  Warning: No data returned for {symbol}")
        return pd.Series(dtype=float, name=symbol)

    # 處理 MultiIndex columns（yfinance 新版本格式）
    if isinstance(df.columns, pd.MultiIndex):
        # 取 Close 價格
        if "Close" in df.columns.get_level_values(0):
            series = df["Close"].iloc[:, 0]
        else:
            # 取第一個價格列
            series = df.iloc[:, 0]
    else:
        # 舊版格式
        if "Adj Close" in df.columns:
            series = df["Adj Close"]
        elif "Close" in df.columns:
            series = df["Close"]
        else:
            series = df.iloc[:, 0]

    series.name = symbol
    return series


def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取序列（無需 API key）"""
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date,
    }

    print(f"  Downloading {series_id} from FRED...")

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
        print(f"  Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float, name=series_id)


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

    # 優先使用 Yahoo Finance
    if source == "yahoo" and HAS_YFINANCE:
        symbol = config.get("yahoo")
        if symbol:
            try:
                series = fetch_yahoo_series(symbol, start_date, end_date)
                if len(series) > 0:
                    series.name = indicator_name
                    return series
            except Exception as e:
                print(f"  Yahoo fetch failed: {e}")

    # Fallback to FRED
    fred_id = config.get("fred")
    if fred_id:
        series = fetch_fred_series(fred_id, start_date, end_date)
        series.name = indicator_name
        return series

    print(f"  Warning: No data source available for {indicator_name}")
    return pd.Series(dtype=float, name=indicator_name)


def fetch_all_indicators(
    start_date: str,
    end_date: str,
    indicators: list = None,
) -> pd.DataFrame:
    """抓取所有指標"""
    if indicators is None:
        indicators = ["usd", "crude", "metals"]

    print(f"Fetching macro indicators...")
    print(f"  Date range: {start_date} to {end_date}")

    data = {}
    for ind in indicators:
        print(f"Fetching {ind}...")
        try:
            series = fetch_indicator(ind, start_date, end_date)
            if len(series) > 0:
                data[ind] = series
                print(f"  Got {len(series)} records")
            else:
                print(f"  Warning: No data for {ind}")
        except Exception as e:
            print(f"  Failed: {e}")

    if not data:
        print("Error: No indicator data fetched")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.index.name = "date"

    # 前向填充缺失值（週末/假日）
    df = df.ffill()

    return df


def calculate_returns(df: pd.DataFrame, periods: int = 5) -> pd.DataFrame:
    """計算報酬率"""
    if df.empty:
        return pd.DataFrame()

    returns = df.pct_change(periods)
    returns.columns = [f"{col}_ret" for col in returns.columns]
    return returns


def calculate_tailwind_score(df: pd.DataFrame, returns_df: pd.DataFrame) -> pd.Series:
    """計算宏觀順風評分"""
    if returns_df.empty:
        return pd.Series(dtype=float, name="macro_tailwind")

    scores = []

    for date in returns_df.index:
        row = returns_df.loc[date]
        flags = []

        # USD 走弱 = 利於商品
        if "usd_ret" in row and pd.notna(row["usd_ret"]):
            flags.append(row["usd_ret"] < 0)

        # 原油走強 = 風險偏好上升
        if "crude_ret" in row and pd.notna(row["crude_ret"]):
            flags.append(row["crude_ret"] > 0)

        # 金屬走強 = 循環需求樂觀
        if "metals_ret" in row and pd.notna(row["metals_ret"]):
            flags.append(row["metals_ret"] > 0)

        score = sum(flags) / len(flags) if flags else None
        scores.append(score)

    return pd.Series(scores, index=returns_df.index, name="macro_tailwind")


def get_latest_tailwind_summary(df: pd.DataFrame) -> Dict:
    """取得最新宏觀順風摘要"""
    if df.empty or "macro_tailwind" not in df.columns:
        return {"score": None, "components": {}}

    # 取最新一行有效資料
    latest = df.dropna(subset=["macro_tailwind"]).iloc[-1] if len(df.dropna(subset=["macro_tailwind"])) > 0 else None

    if latest is None:
        return {"score": None, "components": {}}

    score = latest["macro_tailwind"]
    components = {}

    if "usd_ret" in latest and pd.notna(latest["usd_ret"]):
        components["usd_down"] = latest["usd_ret"] < 0
        components["usd_ret"] = round(latest["usd_ret"] * 100, 2)

    if "crude_ret" in latest and pd.notna(latest["crude_ret"]):
        components["crude_up"] = latest["crude_ret"] > 0
        components["crude_ret"] = round(latest["crude_ret"] * 100, 2)

    if "metals_ret" in latest and pd.notna(latest["metals_ret"]):
        components["metals_up"] = latest["metals_ret"] > 0
        components["metals_ret"] = round(latest["metals_ret"] * 100, 2)

    return {
        "score": round(score, 2) if pd.notna(score) else None,
        "components": components,
        "date": str(latest.name.date()) if hasattr(latest.name, "date") else str(latest.name),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch macro indicators")
    parser.add_argument(
        "--indicators",
        type=str,
        default="usd,crude,metals",
        help="Comma-separated list of indicators",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD), default: 30 days ago",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cache/macro_data.parquet",
        help="Output file path",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print latest tailwind summary",
    )

    args = parser.parse_args()

    indicators = [i.strip() for i in args.indicators.split(",")]

    # 抓取資料
    df = fetch_all_indicators(args.start, args.end, indicators)

    if df.empty:
        print("Error: No data fetched")
        return 1

    # 計算報酬
    returns = calculate_returns(df, periods=5)  # 5 日報酬

    # 計算順風評分
    tailwind = calculate_tailwind_score(df, returns)

    # 合併
    result = pd.concat([df, returns, tailwind], axis=1)

    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 儲存
    result.to_parquet(output_path)
    print(f"\nMacro data saved to {output_path}")
    print(f"  Date range: {result.index.min()} to {result.index.max()}")
    print(f"  Indicators: {list(df.columns)}")
    print(f"  Records: {len(result)}")

    # 顯示最新摘要
    if args.summary:
        summary = get_latest_tailwind_summary(result)
        print(f"\n{'='*50}")
        print(f"Latest Macro Tailwind Summary")
        print(f"{'='*50}")
        if summary["score"] is not None:
            print(f"Date:  {summary.get('date', 'N/A')}")
            print(f"Score: {summary['score']:.0%}")
            print("Components:")
            for k, v in summary["components"].items():
                if "_ret" in k:
                    print(f"  {k}: {v:+.2f}%")
                else:
                    print(f"  {k}: {'✓' if v else '✗'}")
        else:
            print("No tailwind data available")

    return 0


if __name__ == "__main__":
    exit(main())
