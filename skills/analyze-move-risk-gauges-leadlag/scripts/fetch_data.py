#!/usr/bin/env python3
"""
fetch_data.py - 數據抓取工具

從公開來源抓取 MOVE、VIX、信用利差、JGB 殖利率數據。

資料來源：
- MOVE Index: MacroMicro (CDP) https://en.macromicro.me/charts/35584/us-treasury-move-index
- JGB 10Y: MacroMicro (CDP) https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield
- VIX: Yahoo Finance (yfinance)
- Credit (IG OAS): FRED (BAMLC0A0CM)

使用方式：
    # 方法一：Chrome CDP（推薦）
    # Step 1: 啟動 Chrome 調試模式，開啟 MOVE 頁面
    # Windows:
    #   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
    #     --remote-debugging-port=9222 ^
    #     --remote-allow-origins=* ^
    #     --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
    #     "https://en.macromicro.me/charts/35584/us-treasury-move-index"
    #
    # Step 2: 等待頁面載入，然後在瀏覽器中再開一個分頁載入 JGB 頁面：
    #   https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield
    #
    # Step 3: 等待兩個頁面的圖表都完全載入，然後執行：
    python fetch_data.py --start 2024-01-01 --end 2026-01-31
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:
    yf = None
    print("Warning: yfinance not installed, VIX from Yahoo will not be available")

try:
    import websocket
except ImportError:
    websocket = None
    print("Warning: websocket-client not installed, CDP method will not be available")

# =============================================================================
# Configuration
# =============================================================================

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
CDP_PORT = 9222
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_MAX_AGE = timedelta(hours=12)

# MacroMicro 圖表 URL
MACROMICRO_URLS = {
    "MOVE": "https://en.macromicro.me/charts/35584/us-treasury-move-index",
    "JGB10Y": "https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield"
}

# MacroMicro series 關鍵字匹配
MACROMICRO_SERIES_KEYWORDS = {
    "MOVE": ["MOVE", "Move Index", "Treasury", "Volatility"],
    "JGB10Y": ["10 Year", "10年", "Japan", "JGB", "Government Bond"]
}


# =============================================================================
# Cache Utilities
# =============================================================================

def is_cache_valid(key: str) -> bool:
    """檢查快取是否有效"""
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return (datetime.now() - mtime) < CACHE_MAX_AGE


def load_cache(key: str):
    """載入快取"""
    if is_cache_valid(key):
        with open(CACHE_DIR / f"{key}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data["data"])
            # 第一列是日期索引
            first_col = df.columns[0]
            df[first_col] = pd.to_datetime(df[first_col])
            df = df.set_index(first_col)
            return df
    return None


def save_cache(key: str, df: pd.DataFrame):
    """儲存快取"""
    CACHE_DIR.mkdir(exist_ok=True)
    # 確保索引有名稱
    df_to_save = df.copy()
    if df_to_save.index.name is None:
        df_to_save.index.name = "DATE"
    data = df_to_save.reset_index().to_dict(orient="records")
    with open(CACHE_DIR / f"{key}.json", "w", encoding="utf-8") as f:
        json.dump({"cached_at": datetime.now().isoformat(), "data": data}, f, default=str)


# =============================================================================
# CDP (Chrome DevTools Protocol) Functions
# =============================================================================

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


def get_cdp_ws_url(port: int = CDP_PORT, url_keyword: str = None) -> Optional[str]:
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
    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        pages = resp.json()

        # 優先找包含關鍵字的頁面
        if url_keyword:
            for page in pages:
                if url_keyword.lower() in page.get('url', '').lower():
                    return page.get('webSocketDebuggerUrl')

        # 沒找到就返回第一個頁面
        return pages[0].get('webSocketDebuggerUrl') if pages else None

    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        print(f"[CDP] Error getting WS URL: {e}")
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
    if websocket is None:
        raise ImportError("websocket-client not installed. Run: pip install websocket-client")

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


def get_all_cdp_pages(port: int = CDP_PORT) -> List[Dict]:
    """獲取所有開啟的 Chrome 頁面"""
    try:
        resp = requests.get(f'http://127.0.0.1:{port}/json', timeout=5)
        return resp.json()
    except Exception:
        return []


def find_series_by_keywords(
    chart_data: List[Dict],
    keywords: List[str]
) -> Optional[Dict[str, Any]]:
    """根據關鍵字尋找 series"""
    for chart in chart_data:
        for series in chart.get('series', []):
            series_name = series.get('name', '')
            for keyword in keywords:
                if keyword.lower() in series_name.lower():
                    return series
    return None


def series_to_pandas(series_data: Dict[str, Any], name: str = None) -> pd.Series:
    """將 series 數據轉換為 Pandas Series"""
    points = series_data.get('data', [])
    if not points:
        return pd.Series(dtype=float)

    df = pd.DataFrame(points)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    result = df['y']
    result.name = name or series_data.get('name', 'value')
    return result


def fetch_macromicro_via_cdp(
    indicator: str,
    port: int = CDP_PORT
) -> pd.Series:
    """
    使用 Chrome CDP 從 MacroMicro 抓取數據

    Parameters
    ----------
    indicator : str
        指標名稱: 'MOVE' 或 'JGB10Y'
    port : int
        Chrome 調試端口

    Returns
    -------
    pd.Series
        時間序列數據
    """
    if indicator not in MACROMICRO_URLS:
        raise ValueError(f"Unknown indicator: {indicator}. Available: {list(MACROMICRO_URLS.keys())}")

    url = MACROMICRO_URLS[indicator]
    keywords = MACROMICRO_SERIES_KEYWORDS[indicator]

    # 根據 URL 中的圖表 ID 找到對應頁面
    chart_id = url.split('/charts/')[-1].split('/')[0]

    print(f"[CDP] 尋找 {indicator} 頁面 (chart ID: {chart_id})...")
    ws_url = get_cdp_ws_url(port, chart_id)

    if not ws_url:
        raise ConnectionError(
            f"無法找到 {indicator} 頁面\n"
            f"請確認已在 Chrome 中開啟: {url}\n"
            f"並等待圖表完全載入"
        )

    print(f"[CDP] 已連接，正在提取 {indicator} 數據...")
    result = cdp_execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

    # 解析結果
    value = result.get('result', {}).get('result', {}).get('value')
    if not value:
        raise ValueError(f"無法取得數據: {result}")

    data = json.loads(value)

    if isinstance(data, dict) and 'error' in data:
        raise ValueError(f"提取失敗: {data['error']}")

    # 尋找目標 series
    series = find_series_by_keywords(data, keywords)
    if not series:
        # 列出所有可用 series
        all_series = [s.get('name') for c in data for s in c.get('series', [])]
        raise ValueError(f"未找到 {indicator}，可用 series: {all_series}")

    # 轉換為 pandas Series
    ts = series_to_pandas(series, indicator)
    print(f"[CDP] {indicator}: {len(ts)} 筆, {ts.index.min().strftime('%Y-%m-%d')} ~ {ts.index.max().strftime('%Y-%m-%d')}")

    return ts


def check_cdp_connection(port: int = CDP_PORT) -> bool:
    """檢查 CDP 連接是否可用"""
    pages = get_all_cdp_pages(port)
    return len(pages) > 0


def print_cdp_instructions():
    """打印 CDP 啟動指示"""
    print("\n" + "=" * 70)
    print("Chrome CDP 連接失敗！請依照以下步驟啟動 Chrome：")
    print("=" * 70)
    print("""
Step 1: 關閉所有 Chrome 視窗

Step 2: 用調試端口啟動 Chrome（Windows）：

"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/35584/us-treasury-move-index"

Step 3: 在瀏覽器中再開一個分頁，載入 JGB 頁面：
  https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield

Step 4: 等待兩個頁面的圖表都完全載入（約 30-40 秒）

Step 5: 重新執行此腳本
""")
    print("=" * 70)


# =============================================================================
# FRED Data Fetching
# =============================================================================

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.Series:
    """
    從 FRED 抓取時間序列（無需 API key）

    Parameters
    ----------
    series_id : str
        FRED 系列代碼 (e.g., "DGS10", "BAMLC0A0CM")
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns
    -------
    pd.Series
        時間序列數據
    """
    params = {
        "id": series_id,
        "cosd": start_date,
        "coed": end_date
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df.columns = ["DATE", series_id]
        df["DATE"] = pd.to_datetime(df["DATE"])

        # Replace '.' with NaN (FRED uses '.' for missing values)
        df[series_id] = df[series_id].replace(".", pd.NA)
        df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

        df = df.dropna()
        df = df.set_index("DATE")

        return df[series_id]

    except Exception as e:
        print(f"Error fetching {series_id} from FRED: {e}")
        return pd.Series(dtype=float)


def fetch_ig_oas(start_date: str, end_date: str) -> pd.Series:
    """從 FRED 抓取 IG 信用利差 (OAS)"""
    return fetch_fred_series("BAMLC0A0CM", start_date, end_date)


# =============================================================================
# Yahoo Finance Data Fetching
# =============================================================================

def fetch_vix_yahoo(start_date: str, end_date: str) -> pd.Series:
    """
    從 Yahoo Finance 抓取 VIX

    Parameters
    ----------
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)

    Returns
    -------
    pd.Series
        VIX 收盤價
    """
    if yf is None:
        print("yfinance not available, returning empty series")
        return pd.Series(dtype=float)

    try:
        data = yf.download("^VIX", start=start_date, end=end_date, progress=False)
        if data.empty:
            print("No VIX data returned from Yahoo Finance")
            return pd.Series(dtype=float)

        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            vix = data[("Close", "^VIX")]
        else:
            vix = data["Close"]

        vix.name = "VIX"
        return vix

    except Exception as e:
        print(f"Error fetching VIX from Yahoo Finance: {e}")
        return pd.Series(dtype=float)


# =============================================================================
# Main Fetch Function
# =============================================================================

def fetch_all_data(
    start_date: str,
    end_date: str,
    use_cache: bool = True,
    cdp_port: int = CDP_PORT
) -> pd.DataFrame:
    """
    抓取所有需要的數據

    Parameters
    ----------
    start_date : str
        起始日期 (YYYY-MM-DD)
    end_date : str
        結束日期 (YYYY-MM-DD)
    use_cache : bool
        是否使用快取
    cdp_port : int
        CDP 調試端口

    Returns
    -------
    pd.DataFrame
        columns: ["MOVE", "VIX", "CREDIT", "JGB10Y"]
    """
    cache_key = f"data_{start_date}_{end_date}"

    if use_cache:
        cached = load_cache(cache_key)
        if cached is not None:
            print("Loaded data from cache")
            return cached

    print("Fetching data from sources...")

    # 1. 檢查 CDP 連接
    if not check_cdp_connection(cdp_port):
        print_cdp_instructions()
        raise ConnectionError("Chrome CDP not available")

    # 2. MOVE from MacroMicro (CDP)
    print("  Fetching MOVE from MacroMicro (CDP)...")
    try:
        move = fetch_macromicro_via_cdp("MOVE", cdp_port)
        move.name = "MOVE"
    except Exception as e:
        print(f"  Error fetching MOVE: {e}")
        move = pd.Series(dtype=float, name="MOVE")

    # 3. JGB10Y from MacroMicro (CDP)
    print("  Fetching JGB10Y from MacroMicro (CDP)...")
    try:
        jgb = fetch_macromicro_via_cdp("JGB10Y", cdp_port)
        jgb.name = "JGB10Y"
    except Exception as e:
        print(f"  Error fetching JGB10Y: {e}")
        jgb = pd.Series(dtype=float, name="JGB10Y")

    # 4. VIX from Yahoo
    print("  Fetching VIX from Yahoo Finance...")
    vix = fetch_vix_yahoo(start_date, end_date)
    vix.name = "VIX"

    # 5. IG OAS from FRED (as CDX IG proxy)
    print("  Fetching IG OAS from FRED...")
    credit = fetch_ig_oas(start_date, end_date)
    credit.name = "CREDIT"

    # Combine
    df = pd.concat([move, vix, credit, jgb], axis=1)

    # Align to business days
    df = df.sort_index()
    df.index = pd.to_datetime(df.index)

    # Filter by date range
    df = df.loc[start_date:end_date]

    # Forward fill missing values
    df = df.ffill()

    # Save cache
    if use_cache and not df.empty:
        save_cache(cache_key, df)
        print("  Data cached")

    return df


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fetch data for rates vol leadlag analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:

  Step 1: 啟動 Chrome 調試模式（Windows）：

    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
      --remote-debugging-port=9222 ^
      --remote-allow-origins=* ^
      --user-data-dir="%USERPROFILE%\\.chrome-debug-profile" ^
      "https://en.macromicro.me/charts/35584/us-treasury-move-index"

  Step 2: 在瀏覽器中開啟 JGB 頁面：
    https://en.macromicro.me/charts/944/jp-10-year-goverment-bond-yield

  Step 3: 等待圖表載入（約 30-40 秒），然後執行：

    python fetch_data.py --start 2024-01-01 --end 2026-01-31
"""
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", "-o", help="Output CSV path")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--cdp-port", type=int, default=CDP_PORT, help=f"CDP port (default: {CDP_PORT})")
    parser.add_argument("--symbols", default="MOVE,VIX,CREDIT,JGB10Y", help="Symbols to fetch")

    args = parser.parse_args()

    try:
        # Fetch data
        df = fetch_all_data(
            args.start,
            args.end,
            use_cache=not args.no_cache,
            cdp_port=args.cdp_port
        )

        if df.empty:
            print("Error: No data fetched")
            sys.exit(1)

        # Filter symbols
        symbols = [s.strip() for s in args.symbols.split(",")]
        df = df[[s for s in symbols if s in df.columns]]

        # Output
        if args.output:
            df.to_csv(args.output)
            print(f"Data saved to {args.output}")
        else:
            print(df.tail(10))

        # Print summary
        print(f"\nData Summary:")
        print(f"  Period: {df.index.min()} to {df.index.max()}")
        print(f"  Observations: {len(df)}")
        print(f"  Missing ratio: {df.isna().mean().to_dict()}")

    except ConnectionError as e:
        print(f"\nConnection Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
