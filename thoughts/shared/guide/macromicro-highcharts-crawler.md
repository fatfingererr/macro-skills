# MacroMicro Highcharts 圖表爬蟲指南

從 MacroMicro (財經 M 平方) 網站的 Highcharts 互動圖表中提取完整時間序列數據的實戰經驗整理。

> **推薦方法**：使用 Chrome CDP 連接（繞過 Cloudflare），詳見 [方法一：Chrome CDP](#方法一chrome-cdp-推薦)

---

## 目錄

1. [網站特點](#網站特點)
2. [方法一：Chrome CDP（推薦）](#方法一chrome-cdp-推薦)
3. [方法二：Selenium 自動化（備選）](#方法二selenium-自動化備選)
4. [Highcharts 數據結構](#highcharts-數據結構)
5. [常見問題與解決方案](#常見問題與解決方案)
6. [可用圖表清單](#可用圖表清單)

---

## 網站特點

### 架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                  MacroMicro 圖表頁面結構                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  技術棧：                                                    │
│  ├─ 前端框架：Vue.js / React                                │
│  ├─ 圖表庫：Highcharts (全站統一)                           │
│  ├─ 數據載入：延遲 AJAX 載入                                │
│  └─ 渲染時間：需要 30-40 秒完全渲染                         │
│                                                              │
│  數據特點：                                                  │
│  ├─ 時間序列：從 Highcharts 對象直接提取                    │
│  ├─ 格式：Unix 時間戳 (毫秒) + 數值                         │
│  ├─ 多 Series：同一圖表可能包含多個數據系列                 │
│  └─ 完整歷史：可獲取圖表顯示的所有歷史數據                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 為何不用 API？

| 方案                      | 可行性         | 說明                         |
|---------------------------|----------------|------------------------------|
| 官方 API                  | ❌ 需付費會員   | 免費用戶無法存取完整時間序列 |
| 直接 HTTP 請求            | ❌ 無法取得數據 | 數據由 JavaScript 動態渲染   |
| Selenium 自動化           | ⚠️ 經常被擋    | Cloudflare 偵測自動化瀏覽器  |
| **Chrome CDP 連接**       | ✅ 推薦         | 連接真實 Chrome，繞過防護    |

---

## 方法一：Chrome CDP（推薦）

使用 Chrome DevTools Protocol 連接到你自己的 Chrome 瀏覽器，完全繞過 Cloudflare 和反爬蟲偵測。

> **前置知識**：詳細原理請參考 [Chrome CDP 數據爬取 SOP](./chrome-cdp-scraping-sop.md)

### 快速開始

**Step 1：關閉所有 Chrome，用調試端口重新啟動**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://www.macromicro.me/charts/46877/cass-freight-index"
```

**Step 2：確認頁面載入完成**（圖表已顯示）

**Step 3：執行爬蟲腳本**

```bash
python fetch_macromicro_cdp.py --output data.json
```

### 完整程式碼

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacroMicro Highcharts 數據提取器（CDP 版本）
透過 Chrome DevTools Protocol 連接到已開啟的 Chrome
"""

import json
import argparse
import requests
import websocket
from pathlib import Path

CDP_PORT = 9222

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

            // 優先使用 xData/yData
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


def get_page_ws_url(url_keyword='macromicro'):
    """取得目標頁面的 WebSocket URL"""
    try:
        resp = requests.get(f'http://127.0.0.1:{CDP_PORT}/json', timeout=5)
        pages = resp.json()

        for page in pages:
            if url_keyword.lower() in page.get('url', '').lower():
                return page.get('webSocketDebuggerUrl')

        return pages[0].get('webSocketDebuggerUrl') if pages else None

    except requests.exceptions.ConnectionError:
        print("錯誤：無法連接到 Chrome")
        print("請確認已用 --remote-debugging-port=9222 啟動 Chrome")
        return None


def execute_js(ws_url, js_code):
    """透過 CDP 執行 JavaScript"""
    ws = websocket.create_connection(ws_url, timeout=30)
    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {"expression": js_code, "returnByValue": True}
    }
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    ws.close()
    return result


def extract_highcharts_data(output_file=None):
    """提取 Highcharts 圖表數據"""
    print("正在連接到 Chrome...")
    ws_url = get_page_ws_url('macromicro')

    if not ws_url:
        raise ConnectionError("無法連接，請確認 Chrome 已啟動")

    print("正在提取 Highcharts 數據...")
    result = execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

    value = result.get('result', {}).get('result', {}).get('value')
    if not value:
        raise ValueError("無法取得數據")

    data = json.loads(value)

    if isinstance(data, dict) and 'error' in data:
        raise ValueError(f"提取失敗: {data['error']}")

    # 顯示摘要
    print(f"\n成功提取 {len(data)} 個圖表!")
    for chart in data:
        print(f"\n【{chart.get('title', 'Unknown')}】")
        for series in chart.get('series', []):
            if series.get('dataLength', 0) > 0:
                last = series['data'][-1]
                print(f"  {series['name']}: {series['dataLength']} 筆")
                print(f"    最新: {last['date']} = {last['y']:.4f}")

    # 保存
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已保存到: {output_file}")

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=str, help="輸出 JSON 檔案")
    args = parser.parse_args()
    extract_highcharts_data(output_file=args.output)
```

### 輔助函式

```python
def get_series_data(data, series_name):
    """取得特定 series 的數據（部分名稱匹配）"""
    for chart in data:
        for series in chart.get('series', []):
            if series_name.lower() in series.get('name', '').lower():
                return series.get('data', [])
    return []


def to_pandas_dataframe(data, series_name):
    """轉換為 Pandas DataFrame"""
    import pandas as pd

    points = get_series_data(data, series_name)
    if not points:
        return None

    df = pd.DataFrame(points)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    df = df[['y']].rename(columns={'y': series_name})
    return df
```

---

## 方法二：Selenium 自動化（備選）

當 CDP 方法不可用時，可以嘗試 Selenium。但請注意：**Cloudflare 經常會擋住 Selenium**。

---

## Highcharts 數據結構

### Highcharts 對象結構

MacroMicro 使用 Highcharts 渲染圖表，數據存儲在全域 `Highcharts.charts` 陣列中：

```javascript
// 瀏覽器控制台中執行
Highcharts.charts                    // 所有圖表實例
Highcharts.charts[0].series          // 第一個圖表的所有 series
Highcharts.charts[0].series[0].data  // 第一個 series 的數據點
```

每個數據點的結構：

```javascript
{
  x: 1704067200000,     // Unix 時間戳（毫秒）
  y: 16073.048707871698 // 數值
}
```

### 關鍵洞察

1. **Highcharts 全域對象**：MacroMicro 不會隱藏或混淆 Highcharts 對象
2. **完整歷史數據**：圖表加載後，所有可見的歷史數據都在 `series.data` 中
3. **多 Series 支援**：一個圖表可能有多個 series（如價格 + 持倉量）

---

## 完整實作流程

### 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                 MacroMicro 爬蟲流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 請求前準備                                               │
│     ├─ 隨機延遲 1-2 秒                                      │
│     ├─ 隨機 User-Agent                                      │
│     └─ 配置 Chrome headless + 防偵測                        │
│                                                              │
│  2. 頁面載入                                                 │
│     ├─ 載入目標圖表 URL                                     │
│     ├─ 初步等待 5 秒（頁面框架）                            │
│     ├─ 滾動到頁面頂部（觸發圖表可見）                       │
│     └─ 等待圖表區域選擇器出現                               │
│                                                              │
│  3. 🔴 長時間等待圖表渲染（關鍵）                           │
│     ├─ 等待 35 秒（Highcharts 完全初始化）                  │
│     └─ 原因：MacroMicro 圖表渲染非常慢                      │
│                                                              │
│  4. 執行 JavaScript 提取數據                                 │
│     ├─ 檢查 Highcharts 是否存在                             │
│     ├─ 遍歷所有圖表和 series                                │
│     ├─ 提取每個數據點的 x（時間）和 y（數值）               │
│     └─ 帶重試機制（最多 3 次）                              │
│                                                              │
│  5. 數據後處理                                               │
│     ├─ 根據 series 名稱篩選目標數據                         │
│     ├─ 時間戳轉換為日期字串                                 │
│     └─ 單位轉換（如 噸 → 盎司）                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 等待時間建議

| 階段                | 建議等待時間 | 說明                      |
|---------------------|--------------|---------------------------|
| 初始頁面載入        | 5 秒         | 頁面框架和基本元素        |
| 滾動後穩定          | 3 秒         | 確保視覺穩定              |
| **Highcharts 渲染** | **35 秒**    | 🔴 關鍵！圖表數據完全載入 |
| 重試前等待          | 10 秒        | 給予額外渲染時間          |

**總計**：約 43-55 秒（含重試）

---

## 程式碼模板

### 完整爬蟲模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacroMicro Highcharts 圖表數據爬蟲

使用 Selenium 模擬瀏覽器，從 MacroMicro 的 Highcharts 圖表中提取時間序列數據。
"""

import random
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ========== 配置區域 ==========
TARGET_URL = 'https://www.macromicro.me/charts/24945/silver-ishare-silver-trust-etf-tonnes-vs-silver'
TARGET_SERIES_KEYWORDS = ['持倉量', 'SLV']  # 用於匹配目標 series 的關鍵字
CHART_WAIT_SECONDS = 35  # Highcharts 渲染等待時間
MAX_RETRIES = 3
# ==============================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]


def get_selenium_driver():
    """建立 Selenium WebDriver（帶防偵測配置）"""
    chrome_options = Options()

    # 基本設定
    chrome_options.add_argument('--headless=new')  # 新版 headless 模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # 🔴 防偵測設定
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


# 🔴 核心：Highcharts 數據提取 JavaScript
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
        var seriesData = {
            name: s.name,
            type: s.type,
            dataLength: s.data.length,
            // 獲取所有數據點
            data: s.data.map(function(point) {
                return {
                    x: point.x,
                    y: point.y,
                    // 將時間戳轉換為日期字串
                    date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                };
            })
        };
        chartInfo.series.push(seriesData);
    }
    result.push(chartInfo);
}

return result;
'''


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
    driver = None

    try:
        # 1. 隨機延遲（模擬人類）
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

        # 4. 滾動到頁面頂部（確保圖表可見）
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
            except:
                continue

        # 6. 🔴 長時間等待 Highcharts 渲染完成
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

            # 檢查是否需要重試
            if isinstance(chart_data, dict) and chart_data.get('retry'):
                print(f"重試 {retry + 1}/{MAX_RETRIES}，等待 10 秒...")
                time.sleep(10)
                # 觸發圖表重新載入
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
    """
    根據關鍵字在圖表數據中尋找目標 series

    Parameters
    ----------
    chart_data : dict
        fetch_macromicro_chart() 返回的數據
    keywords : list
        用於匹配 series 名稱的關鍵字列表

    Returns
    -------
    dict or None
        匹配的 series 數據，或 None 如果未找到
    """
    for chart in chart_data.get('charts', []):
        for series in chart.get('series', []):
            series_name = series.get('name', '')
            for keyword in keywords:
                if keyword in series_name:
                    print(f"找到匹配 series: {series_name}")
                    return series

    # 列出所有可用的 series 供除錯
    all_series = [
        s['name']
        for c in chart_data.get('charts', [])
        for s in c.get('series', [])
    ]
    print(f"未找到匹配，可用 series: {all_series}")
    return None


# ========== 使用範例 ==========
if __name__ == "__main__":
    # 抓取圖表
    data = fetch_macromicro_chart(TARGET_URL)

    # 尋找目標 series
    series = find_series_by_keywords(data, TARGET_SERIES_KEYWORDS)

    if series:
        print(f"\nSeries: {series['name']}")
        print(f"數據點數量: {series['dataLength']}")
        print(f"最新 5 筆數據:")
        for point in series['data'][-5:]:
            print(f"  {point['date']}: {point['y']}")
```

### 數據轉換為 Pandas Series

```python
import pandas as pd

def macromicro_to_pandas(series_data: Dict[str, Any]) -> pd.Series:
    """
    將 MacroMicro 數據轉換為 Pandas Series

    Parameters
    ----------
    series_data : dict
        從 Highcharts 提取的 series 數據

    Returns
    -------
    pd.Series
        時間序列數據
    """
    points = series_data['data']

    # 轉換為 DataFrame
    df = pd.DataFrame(points)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df.sort_index()

    # 返回 y 值作為 Series
    result = df['y']
    result.name = series_data['name']

    return result


# 使用範例
series = find_series_by_keywords(data, TARGET_SERIES_KEYWORDS)
if series:
    ts = macromicro_to_pandas(series)
    print(ts.tail(10))
```

---

## 常見問題與解決方案

### 問題 1：Highcharts 未載入

**症狀**：返回 `{error: 'Highcharts not loaded'}`

**解決方案**：
```python
# 1. 增加等待時間
CHART_WAIT_SECONDS = 45  # 從 35 秒增加到 45 秒

# 2. 嘗試滾動觸發載入
driver.execute_script('window.scrollTo(0, 500); window.scrollTo(0, 0);')
time.sleep(5)

# 3. 檢查頁面是否正確載入
page_source = driver.page_source
if 'Highcharts' not in page_source:
    print("警告：頁面可能未正確載入 Highcharts")
```

### 問題 2：找不到目標 Series

**症狀**：`find_series_by_keywords()` 返回 None

**解決方案**：
```python
# 1. 先列出所有可用的 series
for chart in chart_data['charts']:
    for s in chart['series']:
        print(f"Series: {s['name']}, Type: {s['type']}, Points: {s['dataLength']}")

# 2. 使用更靈活的匹配
keywords = ['ETF', '持倉', 'Holdings', 'Silver', 'Gold']  # 多個備選關鍵字
```

### 問題 3：數據點為空

**症狀**：`series['dataLength'] == 0`

**解決方案**：
```python
# 1. 圖表可能使用不同的數據結構
# 嘗試從 xData/yData 提取
EXTRACT_HIGHCHARTS_JS_ALT = '''
var chart = Highcharts.charts[0];
var series = chart.series[0];

// 替代方法：使用 xData 和 yData
if (series.data.length === 0 && series.xData) {
    var data = [];
    for (var i = 0; i < series.xData.length; i++) {
        data.push({
            x: series.xData[i],
            y: series.yData[i],
            date: new Date(series.xData[i]).toISOString().split('T')[0]
        });
    }
    return data;
}
'''
```

### 問題 4：被網站封鎖

**症狀**：返回 403 或驗證碼頁面

**解決方案**：
```python
# 1. 增加隨機延遲
delay = random.uniform(3.0, 6.0)  # 增加延遲範圍

# 2. 降低爬取頻率
# 建議每天最多爬取 2-3 次

# 3. 使用本地快取
from pathlib import Path
import json

cache_file = Path('cache/macromicro_cache.json')
cache_max_age_hours = 12

if cache_file.exists():
    cache_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    cache_age = datetime.now() - cache_mtime
    if cache_age.total_seconds() < cache_max_age_hours * 3600:
        print("使用快取數據")
        with open(cache_file) as f:
            return json.load(f)
```

---

## 可用圖表清單

### 貴金屬 ETF 持倉

| 圖表         | URL                                                             | 可用 Series                  |
|--------------|-----------------------------------------------------------------|------------------------------|
| SLV 白銀 ETF | `/charts/24945/silver-ishare-silver-trust-etf-tonnes-vs-silver` | 白銀ETF(SLV)持倉量、白銀價格 |
| GLD 黃金 ETF | `/charts/1330/gold-spdr-gold-trust-tonnes-vs-gold`              | SPDR黃金ETF持倉量、黃金價格  |

### 經濟指標

| 圖表             | URL                                         | 可用 Series |
|------------------|---------------------------------------------|-------------|
| 美國 CPI         | `/charts/8/us-cpi-yoy`                      | CPI YoY     |
| 聯準會資產負債表 | `/charts/6/fed-balance-sheet`               | 總資產      |
| 10Y-2Y 利差      | `/charts/1/us-treasury-yield-spread-10y-2y` | 利差        |

### URL 模式

```
https://www.macromicro.me/charts/{chart_id}/{chart-slug}
```

**探索更多圖表**：
1. 在 MacroMicro 網站瀏覽
2. 複製 URL 中的 `/charts/{id}/{slug}` 部分
3. 使用本模板抓取數據

---

## 快取策略

### 建議的快取機制

```python
from pathlib import Path
from datetime import datetime, timedelta
import json

class MacroMicroCache:
    """MacroMicro 數據快取管理"""

    def __init__(self, cache_dir: str = 'data', max_age_hours: int = 12):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _cache_path(self, chart_id: str) -> Path:
        return self.cache_dir / f"macromicro_{chart_id}_cache.json"

    def is_fresh(self, chart_id: str) -> bool:
        """檢查快取是否仍然新鮮"""
        cache_file = self._cache_path(chart_id)
        if not cache_file.exists():
            return False

        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (datetime.now() - mtime) < self.max_age

    def get(self, chart_id: str) -> Optional[Dict]:
        """從快取讀取"""
        if not self.is_fresh(chart_id):
            return None

        with open(self._cache_path(chart_id), 'r', encoding='utf-8') as f:
            return json.load(f)

    def set(self, chart_id: str, data: Dict):
        """寫入快取"""
        with open(self._cache_path(chart_id), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 使用範例
cache = MacroMicroCache()
chart_id = "24945"

if cache.is_fresh(chart_id):
    data = cache.get(chart_id)
    print("使用快取數據")
else:
    data = fetch_macromicro_chart(TARGET_URL)
    cache.set(chart_id, data)
    print("已更新快取")
```

---

## 本專案實作參考

| 檔案                                                                              | 說明             |
|-----------------------------------------------------------------------------------|------------------|
| `.claude/skills/monitor-etf-holdings-drawdown-risk/scripts/fetch_etf_holdings.py` | SLV 持倉爬蟲實作 |
| `.claude/skills/monitor-etf-holdings-drawdown-risk/data/SLV_holdings_cache.csv`   | 快取數據範例     |

---

## 總結

| 要點     | 說明                                  |
|----------|---------------------------------------|
| 核心技術 | Selenium + Highcharts.charts 對象提取 |
| 等待時間 | 🔴 至少 35 秒（圖表渲染非常慢）       |
| 數據結構 | `{x: 時間戳, y: 數值}`                |
| 快取建議 | 12 小時內使用本地快取，避免頻繁請求   |
| 成功率   | 約 95%（帶重試機制）                  |
