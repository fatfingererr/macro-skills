#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CASS Freight Index 爬蟲

從 MacroMicro 的 Highcharts 圖表中提取 CASS Freight Index 完整時間序列數據。
包含四個指標：Shipments Index, Expenditures Index, Shipments YoY, Expenditures YoY

Usage:
    python fetch_cass_freight.py
    python fetch_cass_freight.py --cache-dir ./cache
    python fetch_cass_freight.py --output cass_data.csv
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# ========== 配置區域 ==========
CASS_FREIGHT_URL = "https://en.macromicro.me/charts/46877/cass-freight-index"
CHART_WAIT_SECONDS = 35
MAX_RETRIES = 3
CACHE_MAX_AGE_HOURS = 12

# CASS Freight Index 四個指標的關鍵字
CASS_SERIES_KEYWORDS = {
    "shipments_index": ["Shipments Index", "shipments index", "Shipments"],
    "expenditures_index": ["Expenditures Index", "expenditures index", "Expenditures"],
    "shipments_yoy": ["Shipments YoY", "shipments yoy", "Shipments Year"],
    "expenditures_yoy": ["Expenditures YoY", "expenditures yoy", "Expenditures Year"]
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]
# ==============================

# Highcharts 數據提取 JavaScript
EXTRACT_HIGHCHARTS_JS = '''
// 檢查 Highcharts 是否存在
if (typeof Highcharts === 'undefined') {
    return {error: 'Highcharts not loaded', retry: true};
}

// 獲取所有有效的圖表
var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
if (charts.length === 0) {
    return {error: 'No charts found', totalCharts: Highcharts.charts.length, retry: true};
}

// 提取每個圖表的數據
var result = [];
for (var i = 0; i < charts.length; i++) {
    var chart = charts[i];
    var chartInfo = {
        title: chart.title ? chart.title.textStr : 'Chart ' + i,
        series: []
    };

    for (var j = 0; j < chart.series.length; j++) {
        var s = chart.series[j];

        // 嘗試從 data 或 xData/yData 提取
        var seriesData = [];
        if (s.data && s.data.length > 0) {
            seriesData = s.data.map(function(point) {
                return {
                    x: point.x,
                    y: point.y,
                    date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                };
            });
        } else if (s.xData && s.xData.length > 0) {
            for (var k = 0; k < s.xData.length; k++) {
                seriesData.push({
                    x: s.xData[k],
                    y: s.yData[k],
                    date: new Date(s.xData[k]).toISOString().split('T')[0]
                });
            }
        }

        chartInfo.series.push({
            name: s.name,
            type: s.type,
            dataLength: seriesData.length,
            data: seriesData
        });
    }
    result.push(chartInfo);
}

return result;
'''


def get_selenium_driver():
    """建立 Selenium WebDriver（帶防偵測配置）"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()

    # 基本設定
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # 防偵測設定
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 隨機 User-Agent
    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f'user-agent={user_agent}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(120)

    return driver


def fetch_macromicro_chart(url: str) -> Dict[str, Any]:
    """
    從 MacroMicro 圖表抓取數據

    Parameters
    ----------
    url : str
        MacroMicro 圖表頁面 URL

    Returns
    -------
    dict
        包含所有圖表和 series 數據的字典
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = None

    try:
        # 1. 隨機延遲
        delay = random.uniform(1.0, 2.0)
        print(f"請求前延遲 {delay:.2f} 秒...")
        time.sleep(delay)

        # 2. 啟動瀏覽器
        driver = get_selenium_driver()
        print(f"正在抓取: {url}")
        driver.get(url)

        # 3. 初步等待頁面載入
        print("等待頁面載入...")
        time.sleep(5)

        # 4. 滾動到頁面頂部
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(3)

        # 5. 等待圖表區域出現
        print("等待圖表區域...")
        chart_selectors = [
            '.chart-area',
            '.chart-wrapper',
            '.mm-chart-wrapper',
            '#chartArea',
            '.highcharts-container',
            '[data-highcharts-chart]'
        ]

        for selector in chart_selectors:
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"找到圖表區域: {selector}")
                break
            except Exception:
                continue

        # 6. 長時間等待 Highcharts 渲染完成
        print(f"等待圖表完全渲染 ({CHART_WAIT_SECONDS}秒)...")
        time.sleep(CHART_WAIT_SECONDS)

        # 7. 確保頁面穩定
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(2)

        # 8. 執行 JavaScript 提取數據（帶重試）
        print("從 Highcharts 圖表中提取數據...")
        chart_data = None

        for retry in range(MAX_RETRIES):
            chart_data = driver.execute_script(EXTRACT_HIGHCHARTS_JS)

            if isinstance(chart_data, dict) and chart_data.get('retry'):
                print(f"重試 {retry + 1}/{MAX_RETRIES}，等待 10 秒...")
                time.sleep(10)
                driver.execute_script(
                    'window.scrollTo(0, 100); '
                    'setTimeout(() => window.scrollTo(0, 0), 500);'
                )
                continue
            else:
                break

        # 9. 檢查結果
        if isinstance(chart_data, dict) and 'error' in chart_data:
            raise ValueError(f"提取圖表數據失敗: {chart_data['error']}")

        print(f"成功獲取 {len(chart_data)} 個圖表的數據!")

        return {
            "source": "MacroMicro",
            "url": url,
            "charts": chart_data,
            "fetched_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"抓取失敗: {e}")
        raise

    finally:
        if driver:
            driver.quit()
            print("瀏覽器已關閉")


def find_series_by_keywords(
    chart_data: Dict[str, Any],
    keywords: List[str]
) -> Optional[Dict[str, Any]]:
    """根據關鍵字尋找 series"""
    for chart in chart_data.get('charts', []):
        for series in chart.get('series', []):
            series_name = series.get('name', '')
            for keyword in keywords:
                if keyword.lower() in series_name.lower():
                    return series
    return None


def extract_all_cass_series(chart_data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    提取所有 CASS Freight Index series

    Returns
    -------
    dict
        {series_key: DataFrame} 包含四個指標
    """
    results = {}

    # 列出所有可用 series
    all_series_names = []
    for chart in chart_data.get('charts', []):
        for s in chart.get('series', []):
            all_series_names.append(s.get('name', 'Unknown'))

    print(f"可用 series: {all_series_names}")

    # 嘗試匹配每個指標
    for key, keywords in CASS_SERIES_KEYWORDS.items():
        series = find_series_by_keywords(chart_data, keywords)
        if series and series.get('dataLength', 0) > 0:
            df = macromicro_to_dataframe(series)
            if df is not None and len(df) > 0:
                results[key] = df
                print(f"[Success] {key}: {len(df)} 筆數據, 範圍 {df.index.min()} ~ {df.index.max()}")
        else:
            print(f"[Warning] 未找到 {key}")

    return results


def macromicro_to_dataframe(series_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """將 MacroMicro series 轉換為 DataFrame"""
    try:
        points = series_data.get('data', [])
        if not points:
            return None

        df = pd.DataFrame(points)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df = df[['y']].rename(columns={'y': series_data.get('name', 'value')})

        return df
    except Exception as e:
        print(f"轉換失敗: {e}")
        return None


class CassFreightCache:
    """CASS Freight Index 數據快取管理"""

    def __init__(self, cache_dir: str = 'cache', max_age_hours: int = CACHE_MAX_AGE_HOURS):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _cache_path(self) -> Path:
        return self.cache_dir / "cass_freight_cache.json"

    def _csv_path(self, series_key: str) -> Path:
        return self.cache_dir / f"cass_{series_key}.csv"

    def is_fresh(self) -> bool:
        cache_file = self._cache_path()
        if not cache_file.exists():
            return False
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (datetime.now() - mtime) < self.max_age

    def get_raw(self) -> Optional[Dict]:
        if not self.is_fresh():
            return None
        try:
            with open(self._cache_path(), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def set_raw(self, data: Dict):
        with open(self._cache_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Cache] 已儲存原始數據到 {self._cache_path()}")

    def get_series(self, series_key: str) -> Optional[pd.DataFrame]:
        csv_path = self._csv_path(series_key)
        if not csv_path.exists():
            return None
        if not self.is_fresh():
            return None
        try:
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            return df
        except Exception:
            return None

    def set_series(self, series_key: str, df: pd.DataFrame):
        csv_path = self._csv_path(series_key)
        df.to_csv(csv_path)
        print(f"[Cache] 已儲存 {series_key} 到 {csv_path}")


def fetch_cass_freight_index(
    cache_dir: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    獲取 CASS Freight Index 所有四個指標

    Parameters
    ----------
    cache_dir : str, optional
        快取目錄
    force_refresh : bool
        是否強制重新抓取

    Returns
    -------
    dict
        {
            'shipments_index': DataFrame,
            'expenditures_index': DataFrame,
            'shipments_yoy': DataFrame,
            'expenditures_yoy': DataFrame
        }
    """
    cache = CassFreightCache(cache_dir) if cache_dir else None

    # 檢查快取
    if cache and not force_refresh:
        cached_data = cache.get_raw()
        if cached_data:
            print("[Cache Hit] 使用快取數據")
            results = extract_all_cass_series(cached_data)
            if results:
                return results

    # 抓取新數據
    print("從 MacroMicro 抓取 CASS Freight Index...")
    chart_data = fetch_macromicro_chart(CASS_FREIGHT_URL)

    # 儲存快取
    if cache:
        cache.set_raw(chart_data)

    # 提取 series
    results = extract_all_cass_series(chart_data)

    # 儲存各 series CSV
    if cache:
        for key, df in results.items():
            cache.set_series(key, df)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="從 MacroMicro 抓取 CASS Freight Index"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="快取目錄 (default: cache)"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="強制重新抓取，忽略快取"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出合併 CSV 檔案路徑"
    )

    args = parser.parse_args()

    try:
        # 抓取數據
        results = fetch_cass_freight_index(
            cache_dir=args.cache_dir,
            force_refresh=args.force_refresh
        )

        if not results:
            print("[Error] 未獲取到任何數據")
            return

        # 顯示結果摘要
        print("\n" + "=" * 50)
        print("CASS Freight Index 數據摘要")
        print("=" * 50)

        for key, df in results.items():
            print(f"\n[{key}]")
            print(f"  數據點: {len(df)}")
            print(f"  範圍: {df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}")
            print(f"  最新值: {df.iloc[-1].values[0]:.2f}")
            print(f"  最新 5 筆:")
            for idx, row in df.tail(5).iterrows():
                print(f"    {idx.strftime('%Y-%m-%d')}: {row.values[0]:.2f}")

        # 輸出合併 CSV
        if args.output:
            merged = pd.concat(
                [df.rename(columns={df.columns[0]: key}) for key, df in results.items()],
                axis=1
            )
            merged.to_csv(args.output)
            print(f"\n[Saved] 合併數據已儲存到 {args.output}")

    except Exception as e:
        print(f"\n[Error] {e}")
        raise


if __name__ == "__main__":
    main()
