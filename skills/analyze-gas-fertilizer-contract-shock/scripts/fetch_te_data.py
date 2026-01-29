#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingEconomics 數據爬蟲（全自動 Chrome CDP）

自動啟動 Chrome、等待頁面載入、提取 Highcharts 數據、關閉 Chrome。
完全繞過 Cloudflare 防護。

Usage:
    # 抓取天然氣（全自動）
    python fetch_te_data.py --symbol natural-gas

    # 抓取化肥（全自動）
    python fetch_te_data.py --symbol urea

    # 同時抓取多個商品
    python fetch_te_data.py --symbol natural-gas --symbol urea

    # 強制更新（忽略快取）
    python fetch_te_data.py --symbol natural-gas --force-refresh
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# ============================================================================
# 配置
# ============================================================================

TE_BASE_URL = "https://tradingeconomics.com/commodity"
CDP_PORT = 9222
CACHE_MAX_AGE_HOURS = 12
PAGE_LOAD_WAIT_SECONDS = 25  # TradingEconomics 載入較快

# Chrome 路徑（按優先順序嘗試）
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
]

# 商品代碼對應
SYMBOL_MAP = {
    "natural-gas": {"slug": "natural-gas", "unit": "USD/MMBtu", "name": "Natural Gas"},
    "eu-natural-gas": {"slug": "eu-natural-gas", "unit": "EUR/MWh", "name": "EU Natural Gas"},
    "uk-natural-gas": {"slug": "uk-natural-gas", "unit": "GBP/therm", "name": "UK Natural Gas"},
    "urea": {"slug": "urea", "unit": "USD/ton", "name": "Urea"},
    "dap": {"slug": "dap", "unit": "USD/ton", "name": "DAP"},
    "fertilizers": {"slug": "fertilizers", "unit": "Index", "name": "Fertilizers Index"},
    "dollar-index": {"slug": "dollar-index", "unit": "Index", "name": "US Dollar Index (DXY)", "url": "https://tradingeconomics.com/united-states/currency"},
}


# ============================================================================
# JavaScript for clicking 5Y button and extracting data
# ============================================================================

# Click time range buttons
def make_click_button_js(label: str) -> str:
    """Generate JavaScript to click a specific time range button"""
    return f'''
(function() {{
    var target = '{label}';
    var buttons = document.querySelectorAll('a, button, span');
    for (var i = 0; i < buttons.length; i++) {{
        var text = buttons[i].textContent.trim();
        if (text === target || text.toLowerCase() === target.toLowerCase()) {{
            buttons[i].click();
            return JSON.stringify({{success: true, clicked: target}});
        }}
    }}
    var rangeButtons = document.querySelectorAll('[data-range], .chart-range-btn, .range-selector button');
    for (var i = 0; i < rangeButtons.length; i++) {{
        var text = rangeButtons[i].textContent.trim();
        if (text === target || text.toLowerCase() === target.toLowerCase()) {{
            rangeButtons[i].click();
            return JSON.stringify({{success: true, clicked: target + ' (alt)'}});
        }}
    }}
    return JSON.stringify({{success: false, error: target + ' button not found'}});
}})()
'''

CLICK_1Y_BUTTON_JS = make_click_button_js('1Y')
CLICK_5Y_BUTTON_JS = make_click_button_js('5Y')

# ============================================================================
# Highcharts 數據提取 JavaScript
# ============================================================================

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
                    if (s.yData[k] !== null && s.yData[k] !== undefined) {
                        seriesData.push({
                            x: s.xData[k],
                            y: s.yData[k],
                            date: new Date(s.xData[k]).toISOString().split('T')[0]
                        });
                    }
                }
            } else if (s.data && s.data.length > 0) {
                seriesData = s.data.filter(p => p && p.y !== null).map(function(point) {
                    return {
                        x: point.x,
                        y: point.y,
                        date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                    };
                });
            }

            if (seriesData.length > 0) {
                chartInfo.series.push({
                    name: s.name || 'Series ' + j,
                    type: s.type,
                    dataLength: seriesData.length,
                    data: seriesData
                });
            }
        }

        if (chartInfo.series.length > 0) {
            result.push(chartInfo);
        }
    }

    return JSON.stringify(result);
})()
'''


# ============================================================================
# Chrome 自動化管理
# ============================================================================

def find_chrome_path() -> Optional[str]:
    """尋找 Chrome 可執行檔路徑"""
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    return None


def is_chrome_debug_running(port: int = CDP_PORT) -> bool:
    """檢查 Chrome 調試端口是否已開啟"""
    import requests

    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def start_chrome_debug(url: str, port: int = CDP_PORT) -> Optional[subprocess.Popen]:
    """
    自動啟動 Chrome 調試模式

    Returns
    -------
    subprocess.Popen or None
        Chrome 進程句柄，失敗返回 None
    """
    chrome_path = find_chrome_path()
    if not chrome_path:
        print("[Error] 找不到 Chrome，請確認已安裝 Google Chrome")
        return None

    # 用戶數據目錄（避免與現有 Chrome 衝突）
    user_data_dir = Path.home() / ".chrome-cdp-profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        url
    ]

    print(f"[Chrome] 啟動 Chrome (port {port})...")

    # Windows 使用 CREATE_NEW_PROCESS_GROUP 避免繼承控制台
    if sys.platform == 'win32':
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    return proc


def wait_for_chrome_ready(port: int = CDP_PORT, timeout: int = 30) -> bool:
    """等待 Chrome 調試端口準備好"""
    import requests

    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=2)
            if resp.status_code == 200 and len(resp.json()) > 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def close_chrome_debug(proc: subprocess.Popen):
    """關閉 Chrome 進程"""
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def navigate_to_url(port: int, url: str) -> bool:
    """導航到指定 URL"""
    import requests
    import websocket

    try:
        # 獲取當前頁面
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        pages = resp.json()
        if not pages:
            return False

        ws_url = pages[0].get('webSocketDebuggerUrl')
        if not ws_url:
            return False

        # 導航
        ws = websocket.create_connection(ws_url, timeout=30)
        cmd = {
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": url}
        }
        ws.send(json.dumps(cmd))
        ws.recv()
        ws.close()
        return True

    except Exception as e:
        print(f"[CDP] 導航失敗: {e}")
        return False


# ============================================================================
# CDP 數據抓取
# ============================================================================

def get_cdp_ws_url(port: int = CDP_PORT, url_keyword: Optional[str] = None) -> Optional[str]:
    """取得目標頁面的 WebSocket URL"""
    import requests

    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        pages = resp.json()

        # 優先找包含關鍵字的頁面
        if url_keyword:
            for page in pages:
                if url_keyword.lower() in page.get('url', '').lower():
                    return page.get('webSocketDebuggerUrl')

        # 優先找 tradingeconomics 頁面
        for page in pages:
            if 'tradingeconomics' in page.get('url', '').lower():
                return page.get('webSocketDebuggerUrl')

        # 沒找到就返回第一個頁面
        return pages[0].get('webSocketDebuggerUrl') if pages else None

    except Exception as e:
        print(f"[CDP] 無法連接到 Chrome (port {port}): {e}")
        return None


def cdp_execute_js(ws_url: str, js_code: str, timeout: int = 30) -> Any:
    """透過 CDP 執行 JavaScript"""
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


def fetch_symbol_via_cdp(
    symbol: str,
    port: int = CDP_PORT,
    wait_seconds: int = PAGE_LOAD_WAIT_SECONDS,
    chrome_proc: Optional[subprocess.Popen] = None,
    we_started_chrome: bool = False
) -> Dict[str, Any]:
    """
    透過 CDP 抓取單一商品數據

    Parameters
    ----------
    symbol : str
        商品代碼（如 natural-gas, urea）
    port : int
        CDP 端口
    wait_seconds : int
        等待頁面載入秒數
    chrome_proc : subprocess.Popen
        已存在的 Chrome 進程（可選）
    we_started_chrome : bool
        是否由本函數啟動 Chrome

    Returns
    -------
    Dict[str, Any]
        包含圖表數據的字典
    """
    symbol_info = SYMBOL_MAP.get(symbol, {"slug": symbol, "unit": "unknown", "name": symbol})
    target_url = f"{TE_BASE_URL}/{symbol_info['slug']}"

    try:
        # 檢查是否已有 Chrome 調試實例
        if not is_chrome_debug_running(port):
            if chrome_proc is None:
                # 啟動 Chrome
                chrome_proc = start_chrome_debug(target_url, port)
                if not chrome_proc:
                    raise RuntimeError("無法啟動 Chrome")
                we_started_chrome = True

                # 等待 Chrome 準備好
                print("[CDP] 等待 Chrome 啟動...")
                if not wait_for_chrome_ready(port, timeout=30):
                    raise RuntimeError("Chrome 啟動超時")
        else:
            # 已有 Chrome，導航到目標 URL
            print(f"[CDP] 發現已運行的 Chrome，導航到 {symbol} 頁面...")
            navigate_to_url(port, target_url)

        # 等待頁面載入（Highcharts 渲染需要時間）
        print(f"[CDP] 等待 {symbol} 頁面載入 ({wait_seconds} 秒)...")
        time.sleep(wait_seconds)

        # 連接並提取數據
        ws_url = get_cdp_ws_url(port, symbol_info['slug'])
        if not ws_url:
            raise RuntimeError("無法取得 WebSocket URL")

        print(f"[CDP] 提取 {symbol} Highcharts 數據...")
        result = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

        value = result.get('result', {}).get('result', {}).get('value')
        if not value:
            raise ValueError(f"無法取得數據: {result}")

        data = json.loads(value)

        if isinstance(data, dict) and 'error' in data:
            raise ValueError(f"提取失敗: {data['error']}")

        print(f"[CDP] 成功提取 {symbol} 數據，共 {len(data)} 個圖表!")

        return {
            "symbol": symbol,
            "source": "TradingEconomics (CDP Auto)",
            "url": target_url,
            "unit": symbol_info['unit'],
            "charts": data,
            "fetched_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"[CDP] {symbol} 數據抓取失敗: {e}")
        raise


def fetch_multiple_symbols(
    symbols: List[str],
    port: int = CDP_PORT,
    wait_seconds: int = PAGE_LOAD_WAIT_SECONDS
) -> Dict[str, Dict[str, Any]]:
    """
    全自動抓取多個商品數據

    Parameters
    ----------
    symbols : List[str]
        商品代碼列表
    port : int
        CDP 端口
    wait_seconds : int
        每個頁面等待秒數

    Returns
    -------
    Dict[str, Dict[str, Any]]
        {symbol: chart_data} 字典
    """
    results = {}
    chrome_proc = None
    we_started_chrome = False

    try:
        # 確定第一個 URL
        first_symbol = symbols[0]
        first_info = SYMBOL_MAP.get(first_symbol, {"slug": first_symbol})
        first_url = first_info.get('url', f"{TE_BASE_URL}/{first_info['slug']}")

        # 檢查是否需要啟動 Chrome
        if not is_chrome_debug_running(port):
            chrome_proc = start_chrome_debug(first_url, port)
            if not chrome_proc:
                raise RuntimeError("無法啟動 Chrome")
            we_started_chrome = True

            print("[CDP] 等待 Chrome 啟動...")
            if not wait_for_chrome_ready(port, timeout=30):
                raise RuntimeError("Chrome 啟動超時")

            # 等待第一個頁面載入
            print(f"[CDP] 等待 {first_symbol} 頁面載入 ({wait_seconds} 秒)...")
            time.sleep(wait_seconds)

        # 抓取每個商品（雙重抓取：1Y daily + 5Y weekly）
        for i, symbol in enumerate(symbols):
            try:
                if i > 0:
                    # 導航到下一個頁面
                    symbol_info = SYMBOL_MAP.get(symbol, {"slug": symbol})
                    target_url = symbol_info.get('url', f"{TE_BASE_URL}/{symbol_info['slug']}")
                    print(f"[CDP] 導航到 {symbol} 頁面...")
                    navigate_to_url(port, target_url)
                    time.sleep(wait_seconds)

                ws_url = get_cdp_ws_url(port)
                if not ws_url:
                    raise RuntimeError("無法取得 WebSocket URL")

                # ===== Step 1: 抓取 1Y 日頻數據 =====
                print(f"[CDP] 點擊 1Y 按鈕（日頻數據）...")
                click_result = cdp_execute_js(ws_url, CLICK_1Y_BUTTON_JS)
                click_value = click_result.get('result', {}).get('result', {}).get('value', '{}')
                click_data = json.loads(click_value) if click_value else {}
                if click_data.get('success'):
                    print(f"[CDP] 成功: {click_data.get('clicked')}")
                    time.sleep(6)
                else:
                    print(f"[CDP] 1Y 按鈕未找到")

                print(f"[CDP] 提取 {symbol} 1Y 數據...")
                result_1y = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)
                value_1y = result_1y.get('result', {}).get('result', {}).get('value')
                data_1y = json.loads(value_1y) if value_1y else None

                # ===== Step 2: 抓取 5Y 週頻數據 =====
                print(f"[CDP] 點擊 5Y 按鈕（週頻數據）...")
                click_result = cdp_execute_js(ws_url, CLICK_5Y_BUTTON_JS)
                click_value = click_result.get('result', {}).get('result', {}).get('value', '{}')
                click_data = json.loads(click_value) if click_value else {}
                if click_data.get('success'):
                    print(f"[CDP] 成功: {click_data.get('clicked')}")
                    time.sleep(6)
                else:
                    print(f"[CDP] 5Y 按鈕未找到")

                print(f"[CDP] 提取 {symbol} 5Y 數據...")
                result_5y = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)
                value_5y = result_5y.get('result', {}).get('result', {}).get('value')
                data_5y = json.loads(value_5y) if value_5y else None

                # 合併數據（1Y daily 優先，5Y weekly 補充舊數據）
                symbol_info = SYMBOL_MAP.get(symbol, {"slug": symbol, "unit": "unknown", "name": symbol})
                results[symbol] = {
                    "symbol": symbol,
                    "source": "TradingEconomics (CDP Auto - 1Y+5Y merged)",
                    "url": f"{TE_BASE_URL}/{symbol_info['slug']}",
                    "unit": symbol_info['unit'],
                    "charts_1y": data_1y,
                    "charts_5y": data_5y,
                    "fetched_at": datetime.now().isoformat()
                }
                print(f"[CDP] 成功提取 {symbol} (1Y + 5Y)!")

            except Exception as e:
                print(f"[Warning] {symbol} 數據抓取失敗: {e}")
                results[symbol] = None

        return results

    finally:
        # 關閉我們啟動的 Chrome
        if we_started_chrome and chrome_proc:
            print("[Chrome] 關閉 Chrome...")
            close_chrome_debug(chrome_proc)


# ============================================================================
# 數據處理
# ============================================================================

def _extract_series_from_charts(charts: List[Dict]) -> Optional[pd.DataFrame]:
    """從 charts 列表中提取最佳 series"""
    if not charts:
        return None

    best_series = None
    max_points = 0

    for chart in charts:
        for series in chart.get('series', []):
            data_length = series.get('dataLength', 0)
            if data_length > max_points:
                max_points = data_length
                best_series = series

    if not best_series or max_points == 0:
        return None

    points = best_series.get('data', [])
    df = pd.DataFrame(points)

    if df.empty:
        return None

    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'y': 'value'})
    df = df[['date', 'value']].dropna()
    df = df.sort_values('date').reset_index(drop=True)

    return df


def extract_price_series(chart_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    從圖表數據提取價格序列（支援 1Y+5Y 合併）

    自動尋找數據點最多的 series 作為主要價格序列。
    如果有 charts_1y 和 charts_5y，會合併：
    - 1Y 日頻數據用於近期
    - 5Y 週頻數據用於補充更早的歷史

    Parameters
    ----------
    chart_data : dict
        fetch_via_cdp 返回的數據

    Returns
    -------
    pd.DataFrame or None
        包含 date 和 value 的 DataFrame
    """
    # 檢查是否有分開的 1Y 和 5Y 數據
    charts_1y = chart_data.get('charts_1y')
    charts_5y = chart_data.get('charts_5y')

    if charts_1y or charts_5y:
        # 新格式：合併 1Y daily + 5Y weekly
        df_1y = _extract_series_from_charts(charts_1y) if charts_1y else None
        df_5y = _extract_series_from_charts(charts_5y) if charts_5y else None

        if df_1y is not None and df_5y is not None:
            # 找出 1Y 數據的最早日期
            cutoff_date = df_1y['date'].min()
            print(f"[Merge] 1Y 數據起始: {cutoff_date.strftime('%Y-%m-%d')}, 共 {len(df_1y)} 筆")

            # 5Y 數據只保留 cutoff 之前的部分
            df_5y_old = df_5y[df_5y['date'] < cutoff_date].copy()
            print(f"[Merge] 5Y 補充數據: {len(df_5y_old)} 筆 (cutoff 之前)")

            # 合併
            df = pd.concat([df_5y_old, df_1y], ignore_index=True)
            df = df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
            print(f"[OK] 合併後 {len(df)} 筆數據, {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
            return df

        elif df_1y is not None:
            print(f"[OK] 僅 1Y 數據: {len(df_1y)} 筆, {df_1y['date'].min().strftime('%Y-%m-%d')} ~ {df_1y['date'].max().strftime('%Y-%m-%d')}")
            return df_1y

        elif df_5y is not None:
            print(f"[OK] 僅 5Y 數據: {len(df_5y)} 筆, {df_5y['date'].min().strftime('%Y-%m-%d')} ~ {df_5y['date'].max().strftime('%Y-%m-%d')}")
            return df_5y

        return None

    # 舊格式：單一 charts 列表
    df = _extract_series_from_charts(chart_data.get('charts', []))
    if df is not None:
        print(f"[OK] 提取 {len(df)} 筆數據, {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    else:
        print("[Warning] 未找到有效的價格序列")

    return df


# ============================================================================
# 快取管理
# ============================================================================

class TECache:
    """TradingEconomics 數據快取管理"""

    def __init__(self, cache_dir: str = '../data/cache', max_age_hours: int = CACHE_MAX_AGE_HOURS):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _raw_cache_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}_raw.json"

    def _csv_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}.csv"

    def is_fresh(self, symbol: str) -> bool:
        cache_file = self._raw_cache_path(symbol)
        if not cache_file.exists():
            return False
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (datetime.now() - mtime) < self.max_age

    def get_raw(self, symbol: str) -> Optional[Dict]:
        if not self.is_fresh(symbol):
            return None
        try:
            with open(self._raw_cache_path(symbol), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def set_raw(self, symbol: str, data: Dict):
        with open(self._raw_cache_path(symbol), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Cache] 已儲存原始數據到 {self._raw_cache_path(symbol)}")

    def get_csv(self, symbol: str) -> Optional[pd.DataFrame]:
        csv_path = self._csv_path(symbol)
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df['date'] = pd.to_datetime(df['date'])
            return df
        return None

    def set_csv(self, symbol: str, df: pd.DataFrame):
        csv_path = self._csv_path(symbol)
        df.to_csv(csv_path, index=False)
        print(f"[Cache] 已儲存 CSV 到 {csv_path}")


# ============================================================================
# 主要 API
# ============================================================================

def fetch_te_commodity(
    symbol: str,
    cache_dir: Optional[str] = None,
    force_refresh: bool = False,
    cdp_port: int = CDP_PORT,
    output: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    獲取 TradingEconomics 商品價格數據（全自動）

    Parameters
    ----------
    symbol : str
        商品代碼（如 natural-gas, urea）
    cache_dir : str, optional
        快取目錄
    force_refresh : bool
        是否強制重新抓取
    cdp_port : int
        CDP 調試端口
    output : str, optional
        輸出 CSV 檔案路徑

    Returns
    -------
    pd.DataFrame or None
        包含 date 和 value 的 DataFrame
    """
    cache = TECache(cache_dir) if cache_dir else TECache()

    # 檢查快取
    if not force_refresh:
        cached_data = cache.get_raw(symbol)
        if cached_data:
            print(f"[Cache] 使用 {symbol} 快取數據")
            df = extract_price_series(cached_data)
            if df is not None:
                return df

    # 全自動抓取新數據
    print(f"[Fetch] 全自動使用 CDP 從 TradingEconomics 抓取 {symbol}...")

    results = fetch_multiple_symbols([symbol], port=cdp_port)
    chart_data = results.get(symbol)

    if not chart_data:
        raise RuntimeError(f"無法抓取 {symbol} 數據")

    # 儲存快取
    cache.set_raw(symbol, chart_data)

    # 提取價格序列
    df = extract_price_series(chart_data)

    if df is not None:
        # 儲存 CSV
        cache.set_csv(symbol, df)

        # 輸出到指定路徑
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"[Output] 已儲存到 {output_path}")

    return df


def fetch_te_commodities(
    symbols: List[str],
    cache_dir: Optional[str] = None,
    force_refresh: bool = False,
    cdp_port: int = CDP_PORT
) -> Dict[str, pd.DataFrame]:
    """
    獲取多個 TradingEconomics 商品價格數據（全自動）

    Parameters
    ----------
    symbols : List[str]
        商品代碼列表
    cache_dir : str, optional
        快取目錄
    force_refresh : bool
        是否強制重新抓取
    cdp_port : int
        CDP 調試端口

    Returns
    -------
    Dict[str, pd.DataFrame]
        {symbol: DataFrame} 字典
    """
    cache = TECache(cache_dir) if cache_dir else TECache()
    results = {}
    symbols_to_fetch = []

    # 檢查快取
    if not force_refresh:
        for symbol in symbols:
            cached_data = cache.get_raw(symbol)
            if cached_data:
                print(f"[Cache] 使用 {symbol} 快取數據")
                df = extract_price_series(cached_data)
                if df is not None:
                    results[symbol] = df
                    continue
            symbols_to_fetch.append(symbol)
    else:
        symbols_to_fetch = symbols

    # 抓取需要更新的商品
    if symbols_to_fetch:
        print(f"[Fetch] 全自動抓取: {', '.join(symbols_to_fetch)}")
        fetched = fetch_multiple_symbols(symbols_to_fetch, port=cdp_port)

        for symbol, chart_data in fetched.items():
            if chart_data:
                cache.set_raw(symbol, chart_data)
                df = extract_price_series(chart_data)
                if df is not None:
                    cache.set_csv(symbol, df)
                    results[symbol] = df

    return results


# ============================================================================
# 主程式
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="從 TradingEconomics 全自動抓取商品價格數據（Chrome CDP）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:

  # 抓取單一商品（全自動）
  python fetch_te_data.py --symbol natural-gas

  # 抓取多個商品（全自動）
  python fetch_te_data.py --symbol natural-gas --symbol urea

  # 強制更新（忽略快取）
  python fetch_te_data.py --symbol urea --force-refresh

可用商品代碼：
  natural-gas, eu-natural-gas, uk-natural-gas, urea, dap, fertilizers
"""
    )

    parser.add_argument(
        "--symbol", "-s",
        action="append",
        required=True,
        help="商品代碼，可指定多個 (如 --symbol natural-gas --symbol urea)"
    )
    parser.add_argument(
        "--cdp-port",
        type=int,
        default=CDP_PORT,
        help=f"CDP 調試端口 (預設: {CDP_PORT})"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="../data/cache",
        help="快取目錄 (預設: ../data/cache)"
    )
    parser.add_argument(
        "--force-refresh", "-f",
        action="store_true",
        help="強制重新抓取，忽略快取"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出 CSV 檔案路徑（僅適用於單一商品）"
    )

    args = parser.parse_args()

    try:
        if len(args.symbol) == 1:
            # 單一商品
            df = fetch_te_commodity(
                symbol=args.symbol[0],
                cache_dir=args.cache_dir,
                force_refresh=args.force_refresh,
                cdp_port=args.cdp_port,
                output=args.output
            )

            if df is not None:
                print(f"\n{'=' * 50}")
                print(f"{args.symbol[0].upper()} 數據摘要")
                print(f"{'=' * 50}")
                print(f"數據點: {len(df)}")
                print(f"範圍: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
                print(f"最新值: {df['value'].iloc[-1]:.4f}")
                print(f"\n最新 5 筆:")
                for _, row in df.tail(5).iterrows():
                    print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['value']:.4f}")
            else:
                print("[Error] 未獲取到數據")

        else:
            # 多個商品
            results = fetch_te_commodities(
                symbols=args.symbol,
                cache_dir=args.cache_dir,
                force_refresh=args.force_refresh,
                cdp_port=args.cdp_port
            )

            print(f"\n{'=' * 60}")
            print("TradingEconomics 數據摘要")
            print("=" * 60)

            for symbol, df in results.items():
                if df is not None:
                    print(f"\n[{symbol.upper()}]")
                    print(f"  數據點: {len(df)}")
                    print(f"  範圍: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
                    print(f"  最新值: {df['value'].iloc[-1]:.4f}")
                else:
                    print(f"\n[{symbol.upper()}] 抓取失敗")

    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
