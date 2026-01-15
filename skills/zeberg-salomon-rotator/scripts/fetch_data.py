#!/usr/bin/env python3
"""
Zeberg-Salomon Rotator - Data Fetcher
從 FRED 和 Yahoo Finance 抓取宏觀經濟數據和價格數據
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, List, Optional

import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:
    yf = None


def fetch_fred_series(
    series_id: str,
    start_date: str,
    end_date: str,
) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Args:
        series_id: FRED 系列代碼
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)

    Returns:
        pd.Series: 時間序列數據
    """
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        # FRED API uses "observation_date" as the date column
        df = pd.read_csv(
            StringIO(response.text),
            parse_dates=["observation_date"],
            index_col="observation_date",
        )
        df.index.name = "DATE"
        df.columns = [series_id]

        # 處理缺失值標記
        df = df.replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        return df[series_id]

    except requests.RequestException as e:
        print(f"Error fetching {series_id}: {e}", file=sys.stderr)
        return pd.Series(dtype=float, name=series_id)


def fetch_multiple_fred_series(
    series_ids: List[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    批量抓取多個 FRED 系列

    Args:
        series_ids: FRED 系列代碼列表
        start_date: 起始日期
        end_date: 結束日期

    Returns:
        pd.DataFrame: 合併的數據框
    """
    series_list = []
    for sid in series_ids:
        print(f"Fetching FRED: {sid}...", file=sys.stderr)
        s = fetch_fred_series(sid, start_date, end_date)
        series_list.append(s)

    df = pd.concat(series_list, axis=1)
    return df


def fetch_yahoo_prices(
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.Series:
    """
    從 Yahoo Finance 抓取價格數據

    Args:
        ticker: 股票代碼
        start_date: 起始日期
        end_date: 結束日期

    Returns:
        pd.Series: 調整後收盤價
    """
    if yf is None:
        print("yfinance not installed. Run: pip install yfinance", file=sys.stderr)
        return pd.Series(dtype=float, name=ticker)

    try:
        print(f"Fetching Yahoo: {ticker}...", file=sys.stderr)
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True,
        )

        if data.empty:
            return pd.Series(dtype=float, name=ticker)

        # 處理 MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"][ticker]
        else:
            close = data["Close"]

        close.name = ticker
        return close

    except Exception as e:
        print(f"Error fetching {ticker}: {e}", file=sys.stderr)
        return pd.Series(dtype=float, name=ticker)


def fetch_multiple_yahoo_prices(
    tickers: List[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    批量抓取多個 Yahoo 價格

    Args:
        tickers: 股票代碼列表
        start_date: 起始日期
        end_date: 結束日期

    Returns:
        pd.DataFrame: 合併的價格數據框
    """
    series_list = []
    for ticker in tickers:
        s = fetch_yahoo_prices(ticker, start_date, end_date)
        series_list.append(s)

    df = pd.concat(series_list, axis=1)
    return df


def resample_to_monthly(df: pd.DataFrame, method: str = "last") -> pd.DataFrame:
    """
    將數據重採樣到月頻

    Args:
        df: 原始數據框
        method: 重採樣方法 ('last', 'mean', 'first')

    Returns:
        pd.DataFrame: 月頻數據框
    """
    if method == "last":
        return df.resample("ME").last()
    elif method == "mean":
        return df.resample("ME").mean()
    elif method == "first":
        return df.resample("ME").first()
    else:
        raise ValueError(f"Unknown resample method: {method}")


def fetch_all_data(
    leading_series: Optional[List[str]] = None,
    coincident_series: Optional[List[str]] = None,
    risk_series: Optional[List[str]] = None,
    price_tickers: Optional[List[str]] = None,
    start_date: str = "2000-01-01",
    end_date: Optional[str] = None,
    freq: str = "M",
) -> Dict:
    """
    抓取所有所需數據

    Args:
        leading_series: 領先指標 FRED 系列
        coincident_series: 同時指標 FRED 系列
        risk_series: 風險濾鏡 FRED 系列
        price_tickers: 價格資產代碼
        start_date: 起始日期
        end_date: 結束日期
        freq: 頻率

    Returns:
        Dict: 包含所有數據的字典
    """
    # 預設值
    if leading_series is None:
        leading_series = ["T10Y3M", "T10Y2Y", "PERMIT", "ACDGNO", "UMCSENT"]
    if coincident_series is None:
        coincident_series = ["PAYEMS", "INDPRO", "W875RX1", "CMRMTSPL"]
    if risk_series is None:
        risk_series = []
    if price_tickers is None:
        price_tickers = ["SPY", "TLT"]
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 抓取 FRED 數據
    all_fred_series = list(set(leading_series + coincident_series + risk_series))
    macro_df = fetch_multiple_fred_series(all_fred_series, start_date, end_date)

    # 抓取價格數據
    prices_df = fetch_multiple_yahoo_prices(price_tickers, start_date, end_date)

    # 重採樣到月頻
    if freq == "M":
        macro_df = resample_to_monthly(macro_df, method="last")
        prices_df = resample_to_monthly(prices_df, method="last")

    return {
        "macro": macro_df,
        "prices": prices_df,
        "metadata": {
            "start_date": start_date,
            "end_date": end_date,
            "freq": freq,
            "leading_series": leading_series,
            "coincident_series": coincident_series,
            "risk_series": risk_series,
            "price_tickers": price_tickers,
            "fetch_time": datetime.now().isoformat(),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch data for Zeberg-Salomon Rotator"
    )
    parser.add_argument(
        "--leading",
        type=str,
        default="T10Y3M,T10Y2Y,PERMIT,ACDGNO,UMCSENT",
        help="Leading indicator FRED series (comma-separated)",
    )
    parser.add_argument(
        "--coincident",
        type=str,
        default="PAYEMS,INDPRO,W875RX1,CMRMTSPL",
        help="Coincident indicator FRED series (comma-separated)",
    )
    parser.add_argument(
        "--risk",
        type=str,
        default="",
        help="Risk filter FRED series (comma-separated)",
    )
    parser.add_argument(
        "--prices",
        type=str,
        default="SPY,TLT",
        help="Price tickers (comma-separated)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--freq",
        type=str,
        default="M",
        choices=["M", "W", "D"],
        help="Frequency",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (JSON)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Only fetch latest data point",
    )

    args = parser.parse_args()

    # 解析參數
    leading_series = [s.strip() for s in args.leading.split(",") if s.strip()]
    coincident_series = [s.strip() for s in args.coincident.split(",") if s.strip()]
    risk_series = [s.strip() for s in args.risk.split(",") if s.strip()]
    price_tickers = [s.strip() for s in args.prices.split(",") if s.strip()]

    # 抓取數據
    data = fetch_all_data(
        leading_series=leading_series,
        coincident_series=coincident_series,
        risk_series=risk_series,
        price_tickers=price_tickers,
        start_date=args.start,
        end_date=args.end,
        freq=args.freq,
    )

    # 準備輸出
    output = {
        "metadata": data["metadata"],
        "macro": data["macro"].to_dict() if not data["macro"].empty else {},
        "prices": data["prices"].to_dict() if not data["prices"].empty else {},
    }

    # 如果只要最新數據
    if args.latest:
        if not data["macro"].empty:
            output["macro_latest"] = data["macro"].iloc[-1].to_dict()
            output["macro_latest"]["date"] = str(data["macro"].index[-1].date())
        if not data["prices"].empty:
            output["prices_latest"] = data["prices"].iloc[-1].to_dict()
            output["prices_latest"]["date"] = str(data["prices"].index[-1].date())

    # 輸出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Data saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
