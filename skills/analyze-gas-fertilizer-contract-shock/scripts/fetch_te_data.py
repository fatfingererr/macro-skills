#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingEconomics 數據爬蟲（Chrome CDP）

使用 Chrome DevTools Protocol 直接連接到已開啟的 Chrome 瀏覽器，
繞過 Cloudflare 防護，提取 TradingEconomics 商品價格數據。

Usage:
    # Step 1: 啟動 Chrome 調試模式
    # Windows:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
      --remote-debugging-port=9222 ^
      --remote-allow-origins=* ^
      --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
      "https://tradingeconomics.com/commodity/natural-gas"

    # Step 2: 等待頁面完全載入（圖表顯示），然後執行：
    python fetch_te_data.py --symbol natural-gas

    # 抓取化肥（先在 Chrome 切換到化肥頁面）：
    python fetch_te_data.py --symbol urea
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import websocket


# ============================================================================
# 配置
# ============================================================================

TE_BASE_URL = "https://tradingeconomics.com/commodity"
CDP_PORT = 9222
CACHE_MAX_AGE_HOURS = 12

# 商品代碼對應
SYMBOL_MAP = {
    "natural-gas": {"slug": "natural-gas", "unit": "USD/MMBtu", "name": "Natural Gas"},
    "eu-natural-gas": {"slug": "eu-natural-gas", "unit": "EUR/MWh", "name": "EU Natural Gas"},
    "uk-natural-gas": {"slug": "uk-natural-gas", "unit": "GBP/therm", "name": "UK Natural Gas"},
    "urea": {"slug": "urea", "unit": "USD/ton", "name": "Urea"},
    "dap": {"slug": "dap", "unit": "USD/ton", "name": "DAP"},
    "fertilizers": {"slug": "fertilizers", "unit": "Index", "name": "Fertilizers Index"},
}


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
# Chrome CDP 模組
# ============================================================================

def get_cdp_ws_url(port: int = CDP_PORT, url_keyword: Optional[str] = None) -> Optional[str]:
    """
    取得目標頁面的 WebSocket URL

    Parameters
    ----------
    port : int
        Chrome 調試端口
    url_keyword : str, optional
        URL 關鍵字用於匹配目標頁面

    Returns
    -------
    str or None
        WebSocket URL，若無法連接則返回 None
    """
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


def get_all_chrome_pages(port: int = CDP_PORT) -> List[Dict]:
    """列出所有 Chrome 分頁"""
    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        return resp.json()
    except Exception:
        return []


# ============================================================================
# TradingEconomics 爬取
# ============================================================================

def fetch_via_cdp(symbol: str, port: int = CDP_PORT) -> Dict[str, Any]:
    """
    使用 Chrome CDP 抓取 TradingEconomics 圖表數據

    前置條件：
    1. 關閉所有 Chrome 視窗
    2. 用調試端口啟動 Chrome 並開啟目標頁面
    3. 等待頁面完全載入（圖表顯示）

    Parameters
    ----------
    symbol : str
        商品代碼（如 natural-gas, urea）
    port : int
        Chrome 調試端口（預設 9222）

    Returns
    -------
    dict
        包含圖表數據的字典
    """
    symbol_info = SYMBOL_MAP.get(symbol, {"slug": symbol, "unit": "unknown", "name": symbol})
    target_url = f"{TE_BASE_URL}/{symbol_info['slug']}"

    print(f"[CDP] 連接到 Chrome (port {port})...")
    ws_url = get_cdp_ws_url(port, symbol_info['slug'])

    if not ws_url:
        pages = get_all_chrome_pages(port)
        if pages:
            print(f"\n[CDP] 找到 {len(pages)} 個分頁：")
            for p in pages:
                print(f"  - {p.get('url', 'unknown')}")
            print(f"\n請在 Chrome 中開啟 {target_url}")
        else:
            print(
                f"\n[CDP] 無法連接到 Chrome 調試端口 {port}\n"
                f"請確認已用以下方式啟動 Chrome：\n\n"
                f"Windows:\n"
                f'  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^\n'
                f"    --remote-debugging-port={port} ^\n"
                f"    --remote-allow-origins=* ^\n"
                f'    --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^\n'
                f'    "{target_url}"\n\n'
                f"macOS:\n"
                f"  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\\n"
                f"    --remote-debugging-port={port} \\\n"
                f"    --remote-allow-origins=* \\\n"
                f'    --user-data-dir="$HOME/.chrome-debug-profile" \\\n'
                f'    "{target_url}"'
            )
        raise ConnectionError(f"無法連接到 Chrome 或找到 {symbol} 頁面")

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
        "symbol": symbol,
        "source": "TradingEconomics (CDP)",
        "url": target_url,
        "unit": symbol_info['unit'],
        "charts": data,
        "fetched_at": datetime.now().isoformat()
    }


# ============================================================================
# 數據處理
# ============================================================================

def extract_price_series(chart_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    從圖表數據提取價格序列

    自動尋找數據點最多的 series 作為主要價格序列

    Parameters
    ----------
    chart_data : dict
        fetch_via_cdp 返回的數據

    Returns
    -------
    pd.DataFrame or None
        包含 date 和 value 的 DataFrame
    """
    # 找數據點最多的 series
    best_series = None
    max_points = 0

    for chart in chart_data.get('charts', []):
        for series in chart.get('series', []):
            data_length = series.get('dataLength', 0)
            if data_length > max_points:
                max_points = data_length
                best_series = series

    if not best_series or max_points == 0:
        print("[Warning] 未找到有效的價格序列")
        return None

    # 轉換為 DataFrame
    points = best_series.get('data', [])
    df = pd.DataFrame(points)

    if df.empty:
        return None

    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'y': 'value'})
    df = df[['date', 'value']].dropna()
    df = df.sort_values('date')

    print(f"[OK] 提取 {len(df)} 筆數據, {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")

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
    獲取 TradingEconomics 商品價格數據

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

    # 抓取新數據
    print(f"[Fetch] 使用 CDP 從 TradingEconomics 抓取 {symbol}...")
    chart_data = fetch_via_cdp(symbol, port=cdp_port)

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


# ============================================================================
# 主程式
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="從 TradingEconomics 抓取商品價格數據（Chrome CDP）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:

  Step 1: 啟動 Chrome 調試模式
  ============================

  Windows:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
      --remote-debugging-port=9222 ^
      --remote-allow-origins=* ^
      --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
      "https://tradingeconomics.com/commodity/natural-gas"

  macOS:
    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
      --remote-debugging-port=9222 \\
      --remote-allow-origins=* \\
      --user-data-dir="$HOME/.chrome-debug-profile" \\
      "https://tradingeconomics.com/commodity/natural-gas"

  Step 2: 等待頁面載入（圖表顯示），然後執行：
  =============================================

    python fetch_te_data.py --symbol natural-gas
    python fetch_te_data.py --symbol urea

  可用商品代碼：
    natural-gas, eu-natural-gas, uk-natural-gas, urea, dap, fertilizers
"""
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="商品代碼 (如 natural-gas, urea, dap)"
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
        "--force-refresh",
        action="store_true",
        help="強制重新抓取，忽略快取"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出 CSV 檔案路徑"
    )

    args = parser.parse_args()

    try:
        df = fetch_te_commodity(
            symbol=args.symbol,
            cache_dir=args.cache_dir,
            force_refresh=args.force_refresh,
            cdp_port=args.cdp_port,
            output=args.output
        )

        if df is not None:
            print(f"\n{'=' * 50}")
            print(f"{args.symbol.upper()} 數據摘要")
            print(f"{'=' * 50}")
            print(f"數據點: {len(df)}")
            print(f"範圍: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"最新值: {df['value'].iloc[-1]:.4f}")
            print(f"\n最新 5 筆:")
            for _, row in df.tail(5).iterrows():
                print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['value']:.4f}")
        else:
            print("[Error] 未獲取到數據")

    except Exception as e:
        print(f"\n[Error] {e}")
        raise


if __name__ == "__main__":
    main()
