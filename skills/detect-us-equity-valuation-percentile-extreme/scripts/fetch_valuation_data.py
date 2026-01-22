#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
估值資料抓取工具

從多個公開資料源抓取估值指標，支援 Shiller CAPE、FRED、Yahoo Finance。
"""

import argparse
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# 嘗試導入可選依賴
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


# =============================================================================
# Shiller CAPE 資料
# =============================================================================

def fetch_shiller_cape(output_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    從 Shiller 資料集抓取 CAPE 及相關資料

    Parameters
    ----------
    output_path : str, optional
        輸出 CSV 路徑

    Returns
    -------
    pd.DataFrame or None
    """
    if not HAS_REQUESTS:
        print("錯誤: requests 套件未安裝")
        return None

    print("正在抓取 Shiller CAPE 資料...")

    try:
        url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

        # 隨機延遲
        time.sleep(random.uniform(0.5, 1.5))

        df = pd.read_excel(url, sheet_name="Data", skiprows=7)

        # 重命名欄位（根據典型的 Shiller 資料格式）
        # 欄位順序可能會變化，這裡使用位置索引
        expected_columns = [
            'Date', 'SP_Price', 'Dividend', 'Earnings', 'CPI',
            'Date_Fraction', 'Long_Rate', 'Real_Price', 'Real_Dividend',
            'Real_TR_Price', 'Real_Earnings', 'Real_TR_Scaled_Earnings',
            'CAPE', 'TR_CAPE', 'Excess_CAPE_Yield', 'Monthly_TR',
            'Monthly_TR_Reinvested', 'Monthly_Real_TR', 'Monthly_Real_TR_Reinvested'
        ]

        if len(df.columns) >= len(expected_columns):
            df.columns = expected_columns[:len(df.columns)]
        else:
            df.columns = expected_columns[:len(df.columns)]

        # 處理日期
        df['Date'] = pd.to_datetime(
            df['Date'].astype(str).str[:7].str.replace('.', '-'),
            format='%Y-%m',
            errors='coerce'
        )

        df = df.dropna(subset=['Date'])
        df = df.set_index('Date')

        # 選擇需要的欄位
        output_df = df[['SP_Price', 'Earnings', 'CAPE', 'Long_Rate', 'CPI']].copy()
        output_df = output_df.dropna(subset=['CAPE'])

        print(f"成功抓取 {len(output_df)} 筆 Shiller 資料")
        print(f"日期範圍: {output_df.index[0]} 至 {output_df.index[-1]}")

        if output_path:
            output_df.to_csv(output_path)
            print(f"已保存至: {output_path}")

        return output_df

    except Exception as e:
        print(f"Shiller 資料抓取失敗: {e}")
        return None


# =============================================================================
# FRED 資料
# =============================================================================

def fetch_fred_series(
    series_ids: List[str],
    start: str = "1900-01-01",
    output_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    從 FRED 抓取多個時間序列

    Parameters
    ----------
    series_ids : list
        FRED 系列代碼清單
    start : str
        起始日期
    output_path : str, optional
        輸出 CSV 路徑

    Returns
    -------
    pd.DataFrame or None
    """
    if not HAS_REQUESTS:
        print("錯誤: requests 套件未安裝")
        return None

    print(f"正在抓取 FRED 資料: {series_ids}")

    results = {}

    for series_id in series_ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

        try:
            # 隨機延遲
            time.sleep(random.uniform(0.3, 0.8))

            df = pd.read_csv(url, parse_dates=['DATE'], index_col='DATE')
            df = df.rename(columns={series_id: series_id})
            df = df[df.index >= start]

            results[series_id] = df[series_id]
            print(f"  {series_id}: {len(df)} 筆資料")

        except Exception as e:
            print(f"  {series_id}: 抓取失敗 - {e}")

    if not results:
        return None

    # 合併
    output_df = pd.DataFrame(results)
    output_df = output_df.dropna(how='all')

    print(f"成功抓取 {len(results)} 個系列")

    if output_path:
        output_df.to_csv(output_path)
        print(f"已保存至: {output_path}")

    return output_df


def fetch_mktcap_to_gdp(output_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    計算並抓取市值/GDP（巴菲特指標）

    Parameters
    ----------
    output_path : str, optional
        輸出 CSV 路徑

    Returns
    -------
    pd.DataFrame or None
    """
    print("正在計算 市值/GDP（巴菲特指標）...")

    # 抓取資料
    fred_data = fetch_fred_series(['WILL5000PRFC', 'GDP'])

    if fred_data is None or fred_data.empty:
        return None

    # GDP 是季度資料，需要 forward fill 到月度
    gdp_monthly = fred_data['GDP'].resample('M').ffill()
    mktcap_monthly = fred_data['WILL5000PRFC'].resample('M').last()

    # 對齊並計算
    df = pd.DataFrame({
        'mktcap': mktcap_monthly,
        'gdp': gdp_monthly
    }).dropna()

    df['mktcap_to_gdp'] = (df['mktcap'] / df['gdp']) * 100

    print(f"成功計算 {len(df)} 筆市值/GDP 資料")
    print(f"日期範圍: {df.index[0]} 至 {df.index[-1]}")
    print(f"當前值: {df['mktcap_to_gdp'].iloc[-1]:.1f}%")

    if output_path:
        df.to_csv(output_path)
        print(f"已保存至: {output_path}")

    return df


# =============================================================================
# Yahoo Finance 資料
# =============================================================================

def fetch_yahoo_valuation(
    tickers: List[str],
    output_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    從 Yahoo Finance 抓取估值指標

    Parameters
    ----------
    tickers : list
        股票代碼清單
    output_path : str, optional
        輸出 JSON 路徑

    Returns
    -------
    dict or None
    """
    if not HAS_YFINANCE:
        print("錯誤: yfinance 套件未安裝")
        return None

    print(f"正在抓取 Yahoo Finance 估值資料: {tickers}")

    results = {}

    for ticker in tickers:
        try:
            # 隨機延遲
            time.sleep(random.uniform(0.5, 1.0))

            stock = yf.Ticker(ticker)
            info = stock.info

            results[ticker] = {
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'pb': info.get('priceToBook'),
                'ps': info.get('priceToSalesTrailing12Months'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),
                'peg_ratio': info.get('pegRatio'),
                'beta': info.get('beta'),
                'market_cap': info.get('marketCap'),
                'fetch_time': datetime.now().isoformat()
            }

            print(f"  {ticker}: 成功")

        except Exception as e:
            print(f"  {ticker}: 抓取失敗 - {e}")

    if not results:
        return None

    print(f"成功抓取 {len(results)} 個標的")

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"已保存至: {output_path}")

    return results


def fetch_yahoo_price_history(
    ticker: str,
    start: str = "1950-01-01",
    output_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    抓取價格歷史

    Parameters
    ----------
    ticker : str
        股票代碼
    start : str
        起始日期
    output_path : str, optional
        輸出 CSV 路徑

    Returns
    -------
    pd.DataFrame or None
    """
    if not HAS_YFINANCE:
        print("錯誤: yfinance 套件未安裝")
        return None

    print(f"正在抓取價格歷史: {ticker}")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, auto_adjust=True)

        if df.empty:
            print("無資料")
            return None

        print(f"成功抓取 {len(df)} 筆價格資料")
        print(f"日期範圍: {df.index[0]} 至 {df.index[-1]}")

        if output_path:
            df.to_csv(output_path)
            print(f"已保存至: {output_path}")

        return df

    except Exception as e:
        print(f"價格歷史抓取失敗: {e}")
        return None


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="估值資料抓取工具"
    )
    parser.add_argument(
        "--source",
        choices=["shiller", "fred", "yahoo", "mktcap_gdp", "all"],
        default="all",
        help="資料來源"
    )
    parser.add_argument(
        "--fred_series",
        default="WILL5000PRFC,GDP",
        help="FRED 系列代碼（逗號分隔）"
    )
    parser.add_argument(
        "--tickers",
        default="^GSPC,SPY",
        help="Yahoo Finance 股票代碼（逗號分隔）"
    )
    parser.add_argument(
        "--output_dir",
        default="data",
        help="輸出目錄"
    )

    args = parser.parse_args()

    # 建立輸出目錄
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")

    if args.source in ["shiller", "all"]:
        fetch_shiller_cape(
            output_path=str(output_dir / f"shiller_cape_{timestamp}.csv")
        )

    if args.source in ["fred", "all"]:
        fetch_fred_series(
            series_ids=args.fred_series.split(","),
            output_path=str(output_dir / f"fred_data_{timestamp}.csv")
        )

    if args.source in ["mktcap_gdp", "all"]:
        fetch_mktcap_to_gdp(
            output_path=str(output_dir / f"mktcap_to_gdp_{timestamp}.csv")
        )

    if args.source in ["yahoo", "all"]:
        fetch_yahoo_valuation(
            tickers=args.tickers.split(","),
            output_path=str(output_dir / f"yahoo_valuation_{timestamp}.json")
        )

        # 也抓取價格歷史
        for ticker in args.tickers.split(","):
            fetch_yahoo_price_history(
                ticker=ticker,
                output_path=str(output_dir / f"price_{ticker.replace('^', '')}_{timestamp}.csv")
            )

    print("\n資料抓取完成！")


if __name__ == "__main__":
    main()
