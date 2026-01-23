#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CASS Freight Index 爬蟲

從 MacroMicro 的 Highcharts 圖表中提取 CASS Freight Index 完整時間序列數據。
包含四個指標：Shipments Index, Expenditures Index, Shipments YoY, Expenditures YoY

推薦方法：Chrome CDP（繞過 Cloudflare）
備選方法：Selenium 自動化

Usage:
    # 方法一：Chrome CDP（推薦）
    # Step 1: 啟動 Chrome 調試模式
    # Windows:
    #   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
    #     --remote-debugging-port=9222 ^
    #     --remote-allow-origins=* ^
    #     --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
    #     "https://www.macromicro.me/charts/46877/cass-freight-index"
    #
    # Step 2: 等待頁面完全載入（圖表顯示），然後執行：
    python fetch_cass_freight.py --cdp

    # 方法二：Selenium（備選）
    python fetch_cass_freight.py --selenium --no-headless
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# ========== 配置區域 ==========
CASS_FREIGHT_URL = "https://www.macromicro.me/charts/46877/cass-freight-index"
CDP_PORT = 9222
CACHE_MAX_AGE_HOURS = 12

# CASS Freight Index 四個指標的關鍵字
CASS_SERIES_KEYWORDS = {
    "shipments_index": ["Shipments Index", "shipments index", "Shipments"],
    "expenditures_index": ["Expenditures Index", "expenditures index", "Expenditures"],
    "shipments_yoy": ["Shipments YoY", "shipments yoy", "Shipments Year"],
    "expenditures_yoy": ["Expenditures YoY", "expenditures yoy", "Expenditures Year"]
}
# ==============================

# Highcharts 數據提取 JavaScript
EXTRACT_HIGHCHARTS_JS = '''
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found'});
    }

    var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
    if (charts.length === 0) {
        return JSON.stringify({error: 'No charts found'});
    }

    var result = [];
    for (var i = 0; i < charts.length; i++) {
        var chart = charts[i];
        var chartInfo = {
            title: chart.title ? chart.title.textStr : 'Chart ' + i,
            series: []
        };

        for (var j = 0; j < chart.series.length; j++) {
            var s = chart.series[j];
            var seriesData = [];

            // 優先使用 xData/yData（更可靠）
            if (s.xData && s.xData.length > 0) {
                for (var k = 0; k < s.xData.length; k++) {
                    seriesData.push({
                        x: s.xData[k],
                        y: s.yData[k],
                        date: new Date(s.xData[k]).toISOString().split('T')[0]
                    });
                }
            } else if (s.data && s.data.length > 0) {
                seriesData = s.data.map(function(point) {
                    return {
                        x: point.x,
                        y: point.y,
                        date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                    };
                });
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
    return JSON.stringify(result);
})()
'''


# ==================== CDP 方法（推薦） ====================

def get_cdp_ws_url(port: int = CDP_PORT, url_keyword: str = 'macromicro') -> Optional[str]:
    """
    取得目標頁面的 WebSocket URL

    Parameters
    ----------
    port : int
        Chrome 調試端口
    url_keyword : str
        URL 關鍵字用於匹配目標頁面

    Returns
    -------
    str or None
        WebSocket URL，若無法連接則返回 None
    """
    import requests

    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        pages = resp.json()

        # 優先找包含關鍵字的頁面
        for page in pages:
            if url_keyword.lower() in page.get('url', '').lower():
                return page.get('webSocketDebuggerUrl')

        # 沒找到就返回第一個頁面
        return pages[0].get('webSocketDebuggerUrl') if pages else None

    except Exception as e:
        print(f"[CDP] 無法連接到 Chrome (port {port}): {e}")
        return None


def cdp_execute_js(ws_url: str, js_code: str, timeout: int = 30) -> Any:
    """
    透過 CDP 執行 JavaScript

    Parameters
    ----------
    ws_url : str
        WebSocket URL
    js_code : str
        要執行的 JavaScript 代碼
    timeout : int
        連線超時秒數

    Returns
    -------
    Any
        JavaScript 執行結果
    """
    import websocket

    ws = websocket.create_connection(ws_url, timeout=timeout)

    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": js_code,
            "returnByValue": True
        }
    }
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    ws.close()

    return result


def fetch_via_cdp(port: int = CDP_PORT) -> Dict[str, Any]:
    """
    使用 Chrome CDP 抓取 MacroMicro 圖表數據

    這是推薦的方法，可以繞過 Cloudflare 防護。

    前置條件：
    1. 關閉所有 Chrome 視窗
    2. 用調試端口啟動 Chrome 並開啟目標頁面
    3. 等待頁面完全載入（圖表顯示）

    Parameters
    ----------
    port : int
        Chrome 調試端口（預設 9222）

    Returns
    -------
    dict
        包含圖表數據的字典
    """
    print(f"[CDP] 連接到 Chrome (port {port})...")
    ws_url = get_cdp_ws_url(port)

    if not ws_url:
        raise ConnectionError(
            f"無法連接到 Chrome 調試端口 {port}\n"
            f"請確認已用以下方式啟動 Chrome：\n"
            f'  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^\n'
            f"    --remote-debugging-port={port} ^\n"
            f"    --remote-allow-origins=* ^\n"
            f'    --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^\n'
            f'    "{CASS_FREIGHT_URL}"'
        )

    print(f"[CDP] 已連接，正在提取 Highcharts 數據...")
    result = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

    # 解析結果
    value = result.get('result', {}).get('result', {}).get('value')
    if not value:
        raise ValueError(f"無法取得數據: {result}")

    data = json.loads(value)

    if isinstance(data, dict) and 'error' in data:
        raise ValueError(f"提取失敗: {data['error']}")

    print(f"[CDP] 成功提取 {len(data)} 個圖表!")

    return {
        "source": "MacroMicro (CDP)",
        "url": CASS_FREIGHT_URL,
        "charts": data,
        "fetched_at": datetime.now().isoformat()
    }


# ==================== Selenium 方法（備選） ====================

def fetch_via_selenium(
    headless: bool = False,
    wait_seconds: int = 35
) -> Dict[str, Any]:
    """
    使用 Selenium 抓取 MacroMicro 圖表數據

    這是備選方法，可能會被 Cloudflare 擋住。

    Parameters
    ----------
    headless : bool
        是否使用無頭模式（建議 False，以便手動通過驗證）
    wait_seconds : int
        等待圖表渲染的秒數

    Returns
    -------
    dict
        包含圖表數據的字典
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        print("[Warning] webdriver-manager 未安裝，使用系統 ChromeDriver")
        service = None

    options = Options()

    if headless:
        options.add_argument('--headless=new')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        print("[Selenium] 啟動瀏覽器...")
        if service:
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)

        driver.set_page_load_timeout(120)

        print(f"[Selenium] 載入頁面: {CASS_FREIGHT_URL}")
        driver.get(CASS_FREIGHT_URL)

        # 等待圖表區域
        print("[Selenium] 等待圖表區域...")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.highcharts-container'))
            )
        except Exception:
            print("[Warning] 未找到圖表區域，繼續等待...")

        # 等待圖表完全渲染
        print(f"[Selenium] 等待圖表渲染 ({wait_seconds}秒)...")
        time.sleep(wait_seconds)

        # 提取數據
        print("[Selenium] 提取 Highcharts 數據...")
        chart_data = driver.execute_script(f"return {EXTRACT_HIGHCHARTS_JS}")

        if isinstance(chart_data, str):
            chart_data = json.loads(chart_data)

        if isinstance(chart_data, dict) and 'error' in chart_data:
            raise ValueError(f"提取失敗: {chart_data['error']}")

        print(f"[Selenium] 成功提取 {len(chart_data)} 個圖表!")

        return {
            "source": "MacroMicro (Selenium)",
            "url": CASS_FREIGHT_URL,
            "charts": chart_data,
            "fetched_at": datetime.now().isoformat()
        }

    finally:
        if driver:
            driver.quit()
            print("[Selenium] 瀏覽器已關閉")


# ==================== 數據處理 ====================

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


def series_to_dataframe(series_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """將 series 數據轉換為 DataFrame"""
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
        print(f"[Error] 轉換失敗: {e}")
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

    print(f"[Info] 可用 series: {all_series_names}")

    # 匹配每個指標
    for key, keywords in CASS_SERIES_KEYWORDS.items():
        series = find_series_by_keywords(chart_data, keywords)
        if series and series.get('dataLength', 0) > 0:
            df = series_to_dataframe(series)
            if df is not None and len(df) > 0:
                results[key] = df
                print(f"[OK] {key}: {len(df)} 筆, {df.index.min().strftime('%Y-%m')} ~ {df.index.max().strftime('%Y-%m')}")
        else:
            print(f"[Warning] 未找到 {key}")

    return results


# ==================== 快取管理 ====================

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
        print(f"[Cache] 已儲存到 {self._cache_path()}")

    def set_series(self, series_key: str, df: pd.DataFrame):
        csv_path = self._csv_path(series_key)
        df.to_csv(csv_path)


# ==================== 主要 API ====================

def fetch_cass_freight_index(
    cache_dir: Optional[str] = None,
    force_refresh: bool = False,
    method: str = 'cdp',
    cdp_port: int = CDP_PORT,
    selenium_headless: bool = False,
    selenium_wait: int = 35
) -> Dict[str, pd.DataFrame]:
    """
    獲取 CASS Freight Index 所有四個指標

    Parameters
    ----------
    cache_dir : str, optional
        快取目錄
    force_refresh : bool
        是否強制重新抓取
    method : str
        抓取方法: 'cdp'（推薦）或 'selenium'
    cdp_port : int
        CDP 調試端口
    selenium_headless : bool
        Selenium 是否使用無頭模式
    selenium_wait : int
        Selenium 等待圖表渲染秒數

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
            print("[Cache] 使用快取數據")
            results = extract_all_cass_series(cached_data)
            if results:
                return results

    # 抓取新數據
    print(f"[Fetch] 使用 {method.upper()} 方法從 MacroMicro 抓取...")

    if method == 'cdp':
        chart_data = fetch_via_cdp(port=cdp_port)
    elif method == 'selenium':
        chart_data = fetch_via_selenium(headless=selenium_headless, wait_seconds=selenium_wait)
    else:
        raise ValueError(f"不支援的方法: {method}")

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
        description="從 MacroMicro 抓取 CASS Freight Index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:

  方法一：Chrome CDP（推薦）
  ========================
  Step 1: 啟動 Chrome 調試模式
    Windows:
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
        --remote-debugging-port=9222 ^
        --remote-allow-origins=* ^
        --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
        "https://www.macromicro.me/charts/46877/cass-freight-index"

  Step 2: 等待頁面載入（圖表顯示），然後執行：
    python fetch_cass_freight.py --cdp

  方法二：Selenium（備選）
  ======================
    python fetch_cass_freight.py --selenium --no-headless
"""
    )

    # 方法選擇
    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument(
        "--cdp",
        action="store_true",
        help="使用 Chrome CDP 方法（推薦）"
    )
    method_group.add_argument(
        "--selenium",
        action="store_true",
        help="使用 Selenium 方法（備選）"
    )

    # CDP 選項
    parser.add_argument(
        "--cdp-port",
        type=int,
        default=CDP_PORT,
        help=f"CDP 調試端口 (預設: {CDP_PORT})"
    )

    # Selenium 選項
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Selenium: 顯示瀏覽器視窗"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=35,
        help="Selenium: 等待圖表渲染秒數 (預設: 35)"
    )

    # 通用選項
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="快取目錄 (預設: cache)"
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

    # 決定使用哪種方法
    if args.selenium:
        method = 'selenium'
    else:
        method = 'cdp'  # 預設使用 CDP

    try:
        results = fetch_cass_freight_index(
            cache_dir=args.cache_dir,
            force_refresh=args.force_refresh,
            method=method,
            cdp_port=args.cdp_port,
            selenium_headless=not args.no_headless,
            selenium_wait=args.wait
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
            print(f"  最新 3 筆:")
            for idx, row in df.tail(3).iterrows():
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
