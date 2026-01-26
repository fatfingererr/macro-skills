# Workflow: 數據擷取與標準化

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. thoughts/shared/guide/macromicro-highcharts-crawler.md
</required_reading>

<process>
## Step 1: 確認擷取參數

```yaml
commodity: "copper"
start_year: 1970
end_year: 2023
sources:
  - MacroMicro   # 唯一主要來源（WBMS 數據）
output_dir: "data/"
cache_enabled: true
cache_ttl_days: 7
```

> **注意**：本技能僅使用 MacroMicro (WBMS) 作為產量數據的唯一主要來源。

## Step 2: 擷取 MacroMicro 銅礦產量數據

MacroMicro 提供 WBMS（World Bureau of Metal Statistics）銅礦產量數據，包含全球及各主要產銅國的歷史產量。

**數據源 URL**：
```
https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world
```

**擷取方式**：
使用 Selenium 模擬瀏覽器，從 Highcharts 圖表提取數據。

**擷取腳本**：

```python
import random
import time
import json
from pathlib import Path
from datetime import datetime

import pandas as pd

# MacroMicro 爬蟲配置
MACROMICRO_URL = "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"
CHART_WAIT_SECONDS = 35  # Highcharts 渲染需要長時間等待

# User-Agent 清單（防偵測）
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
]

# Highcharts 數據提取 JavaScript
EXTRACT_HIGHCHARTS_JS = '''
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found', retry: true});
    }

    var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
    if (charts.length === 0) {
        return JSON.stringify({error: 'No charts found', retry: true});
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


def get_selenium_driver():
    """建立 Selenium WebDriver（帶防偵測配置）"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()
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


def fetch_macromicro_copper(start_year: int, end_year: int, cache_dir: Path = Path("data/cache")):
    """
    從 MacroMicro 擷取銅產量數據

    Returns:
    --------
    pd.DataFrame with columns: year, country, production, unit, source_id, confidence
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"macromicro_copper_{start_year}_{end_year}.csv"

    # 檢查快取
    if cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age.days < 7:
            print(f"使用快取: {cache_file}")
            return pd.read_csv(cache_file)

    driver = None
    try:
        # 隨機延遲
        delay = random.uniform(1.0, 2.0)
        print(f"請求前延遲 {delay:.2f} 秒...")
        time.sleep(delay)

        # 啟動瀏覽器
        driver = get_selenium_driver()
        print(f"正在抓取: {MACROMICRO_URL}")
        driver.get(MACROMICRO_URL)

        # 等待頁面載入
        time.sleep(5)
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(3)

        # 等待圖表區域
        chart_selectors = ['.highcharts-container', '[data-highcharts-chart]']
        for selector in chart_selectors:
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue

        # 🔴 長時間等待 Highcharts 渲染
        print(f"等待圖表渲染 ({CHART_WAIT_SECONDS}秒)...")
        time.sleep(CHART_WAIT_SECONDS)

        # 執行 JavaScript 提取數據
        result = driver.execute_script(f"return {EXTRACT_HIGHCHARTS_JS}")
        chart_data = json.loads(result) if isinstance(result, str) else result

        if isinstance(chart_data, dict) and 'error' in chart_data:
            raise ValueError(f"提取失敗: {chart_data['error']}")

        # 解析數據
        all_data = []
        for chart in chart_data:
            for series in chart.get('series', []):
                series_name = series.get('name', '')
                for point in series.get('data', []):
                    if point.get('y') is None:
                        continue
                    try:
                        year = int(point['date'][:4])
                        if year < start_year or year > end_year:
                            continue
                        all_data.append({
                            'year': year,
                            'country': normalize_country_name(series_name),
                            'production': float(point['y']) * 1000,  # 千噸 -> 噸
                            'unit': 't_Cu_content',
                            'source_id': 'MacroMicro',
                            'confidence': 0.9,
                            'date': point['date']
                        })
                    except (ValueError, TypeError):
                        continue

        df = pd.DataFrame(all_data)

        # 去重：每年每國只保留一筆
        df = df.sort_values(['year', 'country', 'date'])
        df = df.groupby(['year', 'country']).last().reset_index()
        df = df[['year', 'country', 'production', 'unit', 'source_id', 'confidence']]

        # 保存快取
        df.to_csv(cache_file, index=False)
        print(f"數據已快取: {cache_file}")

        return df

    finally:
        if driver:
            driver.quit()
```

## Step 3: 國家名稱標準化

```python
def normalize_country_name(name: str) -> str:
    """標準化國家名稱"""
    mapping = {
        # 英文變體
        "Democratic Republic of the Congo": "Democratic Republic of Congo",
        "DRC": "Democratic Republic of Congo",
        "Congo, Dem. Rep.": "Democratic Republic of Congo",
        "D.R. Congo": "Democratic Republic of Congo",
        "United States of America": "United States",
        "USA": "United States",
        "US": "United States",
        "Russian Federation": "Russia",
        "USSR": "Russia",
        # 中文
        "智利": "Chile",
        "秘魯": "Peru",
        "中國": "China",
        "美國": "United States",
        "俄羅斯": "Russia",
        "澳洲": "Australia",
        "墨西哥": "Mexico",
        "加拿大": "Canada",
        "印尼": "Indonesia",
        "贊比亞": "Zambia",
        "哈薩克": "Kazakhstan",
        "剛果民主共和國": "Democratic Republic of Congo",
        "全球": "World",
        "世界": "World",
    }

    if name in mapping:
        return mapping[name]

    name_lower = name.lower()
    for key, value in mapping.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return value

    return name
```

## Step 4: 數據驗證

```python
def validate_data(df: pd.DataFrame, end_year: int) -> dict:
    """
    驗證數據完整性與一致性

    Returns:
    --------
    dict with validation results
    """
    results = {
        "total_records": len(df),
        "year_range": f"{df.year.min()}-{df.year.max()}",
        "countries": df.country.nunique(),
        "has_world_total": "World" in df.country.values,
        "latest_year_records": len(df[df.year == end_year]),
        "issues": []
    }

    # 檢查是否有世界總量
    if not results["has_world_total"]:
        results["issues"].append("缺少 World 總量數據")

    # 檢查最新年度是否有足夠國家
    if results["latest_year_records"] < 10:
        results["issues"].append(f"最新年度（{end_year}）記錄過少")

    # 檢查主要產銅國是否都有數據
    major_countries = ["Chile", "Peru", "China", "Democratic Republic of Congo"]
    for country in major_countries:
        if country not in df.country.values:
            results["issues"].append(f"缺少 {country} 數據")

    results["is_valid"] = len(results["issues"]) == 0

    return results
```

## Step 5: 保存標準化數據

```python
def save_normalized_data(df: pd.DataFrame, output_dir: Path = Path("data")):
    """
    保存標準化後的數據
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存完整數據
    output_file = output_dir / f"copper_production_normalized.csv"
    df.to_csv(output_file, index=False)
    print(f"標準化數據已保存: {output_file}")

    # 保存元數據
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "records": len(df),
        "year_range": f"{df.year.min()}-{df.year.max()}",
        "countries": df.country.nunique(),
        "source": "MacroMicro (WBMS)",
        "url": MACROMICRO_URL
    }

    meta_file = output_dir / "copper_production_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return output_file
```

## Step 6: 完整擷取流程

```python
def run_ingestion_pipeline(
    start_year: int = 1970,
    end_year: int = 2023,
    output_dir: Path = Path("data")
):
    """
    執行完整數據擷取流程
    """
    print("=" * 50)
    print("銅產量數據擷取流程（數據來源：MacroMicro）")
    print("=" * 50)

    # Step 1: 擷取 MacroMicro 數據
    print("\n[1/3] 擷取 MacroMicro 數據...")
    df = fetch_macromicro_copper(start_year, end_year)
    print(f"  - 擷取 {len(df)} 筆記錄")

    # Step 2: 驗證
    print("\n[2/3] 驗證數據...")
    validation = validate_data(df, end_year)
    print(f"  - 驗證結果: {'通過' if validation['is_valid'] else '有問題'}")
    if validation["issues"]:
        for issue in validation["issues"]:
            print(f"    ⚠️ {issue}")

    # Step 3: 保存
    print("\n[3/3] 保存數據...")
    output_file = save_normalized_data(df, output_dir)

    print("\n" + "=" * 50)
    print("擷取完成！")
    print(f"輸出檔案: {output_file}")
    print("=" * 50)

    return df

# 執行
if __name__ == "__main__":
    df = run_ingestion_pipeline()
```

## 替代方案：Chrome CDP 連接

如果 Selenium headless 被 Cloudflare 擋住，可使用 Chrome CDP 方式：

**Step 1: 啟動 Chrome 調試模式**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"
```

**Step 2: 等待頁面完全載入**（圖表顯示）

**Step 3: 使用 CDP 提取數據**

```python
import requests
import websocket
import json

CDP_PORT = 9222

def get_page_ws_url():
    resp = requests.get(f'http://127.0.0.1:{CDP_PORT}/json', timeout=5)
    pages = resp.json()
    for page in pages:
        if 'macromicro' in page.get('url', '').lower():
            return page.get('webSocketDebuggerUrl')
    return pages[0].get('webSocketDebuggerUrl') if pages else None

def execute_js(ws_url, js_code):
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

# 使用
ws_url = get_page_ws_url()
result = execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)
chart_data = json.loads(result['result']['result']['value'])
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] MacroMicro 銅產量數據已擷取
- [ ] 數據已標準化為統一 schema
- [ ] 國家名稱已標準化
- [ ] 數據完整性已驗證
- [ ] 快取機制正常運作
- [ ] 輸出 CSV + 元數據 JSON
</success_criteria>
