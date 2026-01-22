#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
數據抓取工具

抓取銅價、股市代理、中國10Y殖利率等數據。
"""

import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import yfinance as yf

# 快取目錄
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 單位換算係數
POUNDS_PER_TON = 2204.62262


def fetch_copper(
    series: str = "HG=F",
    start_date: str = "2020-01-01",
    end_date: str = None,
    freq: str = "1mo",
    convert_to_ton: bool = True,
    use_cache: bool = True,
    cache_hours: int = 12
) -> pd.Series:
    """
    抓取銅價數據

    Parameters
    ----------
    series : str
        銅價序列代碼（預設 HG=F）
    start_date : str
        起始日期
    end_date : str
        結束日期（預設今天）
    freq : str
        頻率（1mo, 1wk, 1d）
    convert_to_ton : bool
        是否轉換為 USD/ton（預設 True）
    use_cache : bool
        是否使用快取
    cache_hours : int
        快取有效時間（小時）

    Returns
    -------
    pd.Series
        銅價時間序列
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cache_file = CACHE_DIR / f"copper_{series}_{start_date}_{end_date}_{freq}.json"

    # 檢查快取
    if use_cache and cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_file, "r") as f:
                data = json.load(f)
            series_data = pd.Series(data["values"], index=pd.to_datetime(data["index"]))
            series_data.name = "copper"
            return series_data

    # 抓取數據
    print(f"正在抓取銅價數據: {series}")
    df = yf.download(series, start=start_date, end=end_date, interval=freq, progress=False)

    if df.empty:
        raise ValueError(f"無法取得 {series} 的數據")

    # 取收盤價
    copper = df["Close"].squeeze()

    # 單位換算
    if convert_to_ton and series == "HG=F":
        copper = copper * POUNDS_PER_TON
        print(f"已將 {series} 從 USD/lb 轉換為 USD/ton")

    copper.name = "copper"

    # 儲存快取
    cache_data = {
        "index": copper.index.strftime("%Y-%m-%d").tolist(),
        "values": copper.tolist(),
        "series": series,
        "converted_to_ton": convert_to_ton
    }
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

    return copper


def fetch_equity(
    series: str = "ACWI",
    start_date: str = "2020-01-01",
    end_date: str = None,
    freq: str = "1mo",
    use_cache: bool = True,
    cache_hours: int = 12
) -> pd.Series:
    """
    抓取股市代理數據

    Parameters
    ----------
    series : str
        股市序列代碼（預設 ACWI）
    start_date : str
        起始日期
    end_date : str
        結束日期
    freq : str
        頻率
    use_cache : bool
        是否使用快取
    cache_hours : int
        快取有效時間

    Returns
    -------
    pd.Series
        股市時間序列
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cache_file = CACHE_DIR / f"equity_{series}_{start_date}_{end_date}_{freq}.json"

    # 檢查快取
    if use_cache and cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_file, "r") as f:
                data = json.load(f)
            series_data = pd.Series(data["values"], index=pd.to_datetime(data["index"]))
            series_data.name = "equity"
            return series_data

    # 抓取數據
    print(f"正在抓取股市數據: {series}")
    df = yf.download(series, start=start_date, end=end_date, interval=freq, progress=False)

    if df.empty:
        raise ValueError(f"無法取得 {series} 的數據")

    equity = df["Close"].squeeze()
    equity.name = "equity"

    # 儲存快取
    cache_data = {
        "index": equity.index.strftime("%Y-%m-%d").tolist(),
        "values": equity.tolist(),
        "series": series
    }
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

    return equity


def fetch_china_10y_yield(
    start_date: str = "2020-01-01",
    end_date: str = None,
    use_cache: bool = True,
    cache_hours: int = 12
) -> pd.Series:
    """
    抓取中國10Y殖利率數據

    注意：此函數需要 Selenium，若無法爬取會使用模擬數據

    Parameters
    ----------
    start_date : str
        起始日期
    end_date : str
        結束日期
    use_cache : bool
        是否使用快取
    cache_hours : int
        快取有效時間

    Returns
    -------
    pd.Series
        中國10Y殖利率時間序列
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cache_file = CACHE_DIR / f"china_10y_{start_date}_{end_date}.json"

    # 檢查快取
    if use_cache and cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_file, "r") as f:
                data = json.load(f)
            series_data = pd.Series(data["values"], index=pd.to_datetime(data["index"]))
            series_data.name = "cny10y"
            return series_data

    # 嘗試使用 Selenium 爬取
    try:
        yield_data = _fetch_china_yield_selenium()
        if yield_data is not None:
            # 儲存快取
            cache_data = {
                "index": yield_data.index.strftime("%Y-%m-%d").tolist(),
                "values": yield_data.tolist(),
                "source": "tradingeconomics"
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
            return yield_data
    except Exception as e:
        print(f"Selenium 爬取失敗: {e}")

    # 備用：使用模擬數據（僅供測試）
    print("警告：使用模擬的中國10Y殖利率數據")
    return _generate_mock_yield_data(start_date, end_date)


def _fetch_china_yield_selenium() -> Optional[pd.Series]:
    """
    使用 Selenium 從 TradingEconomics 爬取中國10Y殖利率

    Returns
    -------
    pd.Series or None
        殖利率時間序列，或 None 如果失敗
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup
    except ImportError:
        print("Selenium 未安裝，請執行: pip install selenium webdriver-manager beautifulsoup4")
        return None

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    driver = None
    try:
        # 隨機延遲
        time.sleep(random.uniform(1.0, 2.0))

        # Chrome 配置
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)

        # 載入頁面
        url = "https://tradingeconomics.com/china/government-bond-yield"
        print(f"正在抓取中國10Y殖利率: {url}")
        driver.get(url)

        # 等待頁面載入
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        time.sleep(3)

        # 解析頁面
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # 嘗試提取當前殖利率
        # 注意：選擇器可能需要根據實際頁面結構調整
        yield_element = soup.select_one('#ticker')
        if yield_element:
            current_yield = float(yield_element.get_text(strip=True))
            # 創建單點序列
            today = datetime.now().strftime("%Y-%m-%d")
            return pd.Series([current_yield], index=pd.to_datetime([today]), name="cny10y")

        return None

    except Exception as e:
        print(f"爬取中國殖利率失敗: {e}")
        return None

    finally:
        if driver:
            driver.quit()


def _generate_mock_yield_data(start_date: str, end_date: str) -> pd.Series:
    """
    生成模擬的殖利率數據（僅供測試）

    這是一個備用函數，當無法從網路取得數據時使用。
    實際使用時應確保能正常爬取。
    """
    import numpy as np

    date_range = pd.date_range(start=start_date, end=end_date, freq='M')

    # 生成模擬數據：基準值 2.5%，加上一些波動
    np.random.seed(42)
    base = 2.5
    trend = np.linspace(0, -0.5, len(date_range))  # 長期下降趨勢
    noise = np.random.normal(0, 0.2, len(date_range))
    values = base + trend + noise

    return pd.Series(values, index=date_range, name="cny10y")


def align_monthly(data_dict: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    將多條序列對齊到月底

    Parameters
    ----------
    data_dict : dict
        {"copper": series1, "equity": series2, "cny10y": series3}

    Returns
    -------
    pd.DataFrame
        對齊後的 DataFrame
    """
    df = pd.DataFrame(data_dict)

    # 確保索引為日期
    df.index = pd.to_datetime(df.index)

    # 重採樣到月底
    df = df.resample('M').last()

    # 前向填補（處理少量缺值）
    df = df.ffill()

    # 丟掉仍有缺值的行
    df = df.dropna()

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="數據抓取工具")
    parser.add_argument("--series", type=str, required=True, help="序列代碼（逗號分隔）")
    parser.add_argument("--start", type=str, default="2020-01-01", help="起始日期")
    parser.add_argument("--end", type=str, default=None, help="結束日期")
    parser.add_argument("--freq", type=str, default="1mo", help="頻率")
    parser.add_argument("--no-cache", action="store_true", help="不使用快取")

    args = parser.parse_args()

    series_list = args.series.split(",")

    for s in series_list:
        s = s.strip()
        if s in ["HG=F"]:
            data = fetch_copper(s, args.start, args.end, args.freq, use_cache=not args.no_cache)
        elif s in ["ACWI", "VT", "URTH"]:
            data = fetch_equity(s, args.start, args.end, args.freq, use_cache=not args.no_cache)
        elif s == "cny10y":
            data = fetch_china_10y_yield(args.start, args.end, use_cache=not args.no_cache)
        else:
            print(f"未知序列: {s}")
            continue

        print(f"\n{s}:")
        print(data.tail())
