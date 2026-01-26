#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
銅礦產量數據爬蟲（全自動 CDP 版本）

從 MacroMicro 的 Highcharts 圖表中提取 WBMS 銅礦產量完整時間序列數據。
自動啟動 Chrome、等待頁面載入、提取數據、關閉 Chrome。

Usage:
    python fetch_copper_production.py
    python fetch_copper_production.py --force-refresh
"""

import argparse
import json
import subprocess
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# ========== 配置區域 ==========
COPPER_PRODUCTION_URL = "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"
CDP_PORT = 9222
CACHE_MAX_AGE_HOURS = 12
PAGE_LOAD_WAIT_SECONDS = 40  # 等待頁面載入的時間

# Chrome 路徑（按優先順序嘗試）
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
]

# 國家名稱標準化映射
COUNTRY_NORMALIZE = {
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "DRC": "Democratic Republic of Congo",
    "Congo, Dem. Rep.": "Democratic Republic of Congo",
    "D.R. Congo": "Democratic Republic of Congo",
    "United States of America": "US",
    "USA": "US",
    "United States": "US",
    "Russian Federation": "Russia",
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


# ==================== Chrome 自動化管理 ====================

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
    if sys.platform == 'win32':
        user_data_dir = Path.home() / ".chrome-cdp-profile"
    else:
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


# ==================== CDP 數據抓取 ====================

def get_cdp_ws_url(port: int = CDP_PORT, url_keyword: str = 'macromicro') -> Optional[str]:
    """取得目標頁面的 WebSocket URL"""
    import requests

    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        pages = resp.json()

        for page in pages:
            if url_keyword.lower() in page.get('url', '').lower():
                return page.get('webSocketDebuggerUrl')

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


def fetch_via_cdp_auto(port: int = CDP_PORT, wait_seconds: int = PAGE_LOAD_WAIT_SECONDS) -> Dict[str, Any]:
    """
    全自動 CDP 抓取流程：
    1. 檢查是否已有 Chrome 調試實例
    2. 若無，自動啟動 Chrome
    3. 等待頁面載入
    4. 提取數據
    5. 關閉 Chrome（若是本次啟動的）
    """
    chrome_proc = None
    we_started_chrome = False

    try:
        # 檢查是否已有 Chrome 調試實例
        if is_chrome_debug_running(port):
            print(f"[CDP] 發現已運行的 Chrome (port {port})")
        else:
            # 啟動 Chrome
            chrome_proc = start_chrome_debug(COPPER_PRODUCTION_URL, port)
            if not chrome_proc:
                raise RuntimeError("無法啟動 Chrome")
            we_started_chrome = True

            # 等待 Chrome 準備好
            print("[CDP] 等待 Chrome 啟動...")
            if not wait_for_chrome_ready(port, timeout=30):
                raise RuntimeError("Chrome 啟動超時")

        # 等待頁面載入（Highcharts 渲染需要時間）
        print(f"[CDP] 等待頁面載入 ({wait_seconds} 秒)...")
        time.sleep(wait_seconds)

        # 連接並提取數據
        ws_url = get_cdp_ws_url(port)
        if not ws_url:
            raise RuntimeError("無法取得 WebSocket URL")

        print("[CDP] 提取 Highcharts 數據...")
        result = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

        value = result.get('result', {}).get('result', {}).get('value')
        if not value:
            raise ValueError(f"無法取得數據: {result}")

        data = json.loads(value)

        if isinstance(data, dict) and 'error' in data:
            raise ValueError(f"提取失敗: {data['error']}")

        print(f"[CDP] 成功提取 {len(data)} 個圖表!")

        return {
            "source": "MacroMicro (CDP Auto)",
            "url": COPPER_PRODUCTION_URL,
            "charts": data,
            "fetched_at": datetime.now().isoformat()
        }

    finally:
        # 關閉我們啟動的 Chrome
        if we_started_chrome and chrome_proc:
            print("[Chrome] 關閉 Chrome...")
            close_chrome_debug(chrome_proc)


# ==================== 數據處理 ====================

def normalize_country_name(name: str) -> str:
    """標準化國家名稱"""
    if name in COUNTRY_NORMALIZE:
        return COUNTRY_NORMALIZE[name]

    for key, value in COUNTRY_NORMALIZE.items():
        if key.lower() in name.lower() or name.lower() in key.lower():
            return value

    return name


def extract_all_series(chart_data: Dict[str, Any]) -> pd.DataFrame:
    """提取所有 series 數據"""
    all_rows = []

    for chart in chart_data.get('charts', []):
        for series in chart.get('series', []):
            series_name = series.get('name', 'Unknown')
            country = normalize_country_name(series_name)

            for point in series.get('data', []):
                if point.get('y') is not None and point.get('date'):
                    year = int(point['date'][:4])
                    all_rows.append({
                        'year': year,
                        'country': country,
                        'production': point['y'],  # 原始單位（噸）
                    })

    if not all_rows:
        raise ValueError("未能提取到任何數據")

    df = pd.DataFrame(all_rows)

    # 列出提取的國家
    countries = df['country'].unique()
    print(f"[Data] 提取到 {len(countries)} 個 series: {list(countries)}")

    return df


# ==================== 快取管理 ====================

class CopperProductionCache:
    """銅產量數據快取管理"""

    def __init__(self, cache_dir: str = 'cache', max_age_hours: int = CACHE_MAX_AGE_HOURS):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _cache_path(self) -> Path:
        return self.cache_dir / "copper_production_cache.json"

    def _csv_path(self) -> Path:
        return self.cache_dir / "copper_production.csv"

    def is_fresh(self) -> bool:
        cache_file = self._csv_path()
        if not cache_file.exists():
            return False
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (datetime.now() - mtime) < self.max_age

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        if not self.is_fresh():
            return None
        try:
            return pd.read_csv(self._csv_path())
        except Exception:
            return None

    def save(self, raw_data: Dict, df: pd.DataFrame):
        # 保存原始 JSON
        with open(self._cache_path(), 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)

        # 保存 CSV
        df.to_csv(self._csv_path(), index=False)
        print(f"[Cache] 已儲存到 {self._csv_path()}")


# ==================== 主要 API ====================

def fetch_copper_production(
    cache_dir: str = "cache",
    force_refresh: bool = False,
    cdp_port: int = CDP_PORT,
    start_year: int = 1970
) -> pd.DataFrame:
    """
    獲取全球銅礦產量數據（全自動）

    自動處理 Chrome 啟動、頁面載入、數據提取、Chrome 關閉。

    Parameters
    ----------
    cache_dir : str
        快取目錄
    force_refresh : bool
        是否強制重新抓取
    cdp_port : int
        CDP 調試端口
    start_year : int
        起始年份篩選

    Returns
    -------
    pd.DataFrame
        columns: year, country, production
    """
    cache = CopperProductionCache(cache_dir)

    # 檢查快取
    if not force_refresh:
        cached_df = cache.get_dataframe()
        if cached_df is not None:
            print("[Cache] 使用快取數據")
            return cached_df[cached_df.year >= start_year]

    # 全自動抓取
    print("[Fetch] 開始全自動抓取流程...")
    chart_data = fetch_via_cdp_auto(port=cdp_port)

    # 提取數據
    df = extract_all_series(chart_data)

    # 篩選年份
    df = df[df.year >= start_year]

    # 儲存快取
    cache.save(chart_data, df)

    return df


def main():
    parser = argparse.ArgumentParser(
        description="全自動抓取 MacroMicro WBMS 銅礦產量數據"
    )
    parser.add_argument(
        "--force-refresh", "-f",
        action="store_true",
        help="強制重新抓取，忽略快取"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="cache",
        help="快取目錄 (預設: cache)"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1970,
        help="起始年份 (預設: 1970)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="輸出 CSV 路徑"
    )

    args = parser.parse_args()

    try:
        df = fetch_copper_production(
            cache_dir=args.cache_dir,
            force_refresh=args.force_refresh,
            start_year=args.start_year
        )

        if df is None or len(df) == 0:
            print("[Error] 未獲取到任何數據")
            return 1

        # 顯示摘要
        print("\n" + "=" * 60)
        print("銅礦產量數據摘要")
        print("=" * 60)

        for country in sorted(df['country'].unique()):
            country_df = df[df['country'] == country]
            latest = country_df[country_df['year'] == country_df['year'].max()].iloc[0]
            print(f"  {country:35s} {country_df['year'].min()}-{country_df['year'].max()}  "
                  f"Latest: {latest['production']/1e6:.2f} Mt")

        if args.output:
            df.to_csv(args.output, index=False)
            print(f"\n[Saved] {args.output}")

        return 0

    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
