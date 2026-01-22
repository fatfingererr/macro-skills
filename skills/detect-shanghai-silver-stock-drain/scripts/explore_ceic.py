#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
探索 CEIC Data 網站，嘗試從 JS 中提取數據
"""

import json
import random
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DEBUG_DIR = DATA_DIR / "debug"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_driver(headless: bool = False):
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')

    # 啟用性能日誌以捕獲網絡請求
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)
    return driver


def explore_ceic():
    url = "https://www.ceicdata.com/zh-hans/china/shanghai-futures-exchange-commodity-futures-stock/cn-warehouse-stock-shanghai-future-exchange-silver"

    print("=" * 60)
    print("CEIC Data 網站探索")
    print("=" * 60)

    driver = None
    try:
        print("\n[1] 啟動瀏覽器...")
        driver = get_driver(headless=False)

        print(f"[2] 載入頁面: {url}")
        driver.get(url)
        time.sleep(5)

        # 嘗試從 JavaScript 中提取 Highcharts 數據
        print("\n[3] 嘗試從 Highcharts 提取數據...")

        # 方法 1: 直接訪問 Highcharts 對象
        try:
            result = driver.execute_script("""
                if (typeof Highcharts !== 'undefined') {
                    var charts = Highcharts.charts.filter(c => c);
                    if (charts.length > 0) {
                        var chart = charts[0];
                        var series = chart.series[0];
                        if (series && series.data) {
                            return series.data.map(function(point) {
                                return {
                                    x: point.x,
                                    y: point.y,
                                    date: new Date(point.x).toISOString().split('T')[0]
                                };
                            });
                        }
                    }
                }
                return null;
            """)

            if result:
                print(f"  -> 成功！找到 {len(result)} 個數據點")
                print(f"  -> 範例: {result[:3]}")

                # 保存數據
                DEBUG_DIR.mkdir(parents=True, exist_ok=True)
                with open(DEBUG_DIR / "ceic_highcharts_data.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"  -> 已保存至 {DEBUG_DIR / 'ceic_highcharts_data.json'}")
            else:
                print("  -> Highcharts 數據不可用，嘗試其他方法...")
        except Exception as e:
            print(f"  -> 方法 1 失敗: {e}")

        # 方法 2: 查找頁面中的所有 script 標籤中的數據
        print("\n[4] 搜索頁面中嵌入的數據...")
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for i, script in enumerate(scripts):
                content = script.get_attribute("innerHTML")
                if content and ("series" in content or "data" in content.lower()):
                    if len(content) > 100:
                        print(f"  -> Script {i}: {len(content)} chars, 包含可能的數據")
                        # 保存可疑的 script
                        with open(DEBUG_DIR / f"ceic_script_{i}.js", "w", encoding="utf-8") as f:
                            f.write(content)
        except Exception as e:
            print(f"  -> 方法 2 失敗: {e}")

        # 方法 3: 點擊「五年」按鈕並監控網絡請求
        print("\n[5] 點擊「五年」按鈕...")
        try:
            # 尋找「五年」按鈕
            five_year_btn = None
            buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '五年')] | //span[contains(text(), '五年')] | //a[contains(text(), '五年')]")

            if buttons:
                five_year_btn = buttons[0]
                print(f"  -> 找到按鈕: {five_year_btn.text}")

                # 點擊前清空性能日誌
                driver.get_log('performance')

                # 點擊
                five_year_btn.click()
                time.sleep(3)

                # 獲取網絡請求
                logs = driver.get_log('performance')
                network_requests = []

                for log in logs:
                    try:
                        message = json.loads(log['message'])['message']
                        if message['method'] == 'Network.requestWillBeSent':
                            url = message['params']['request']['url']
                            if 'api' in url.lower() or 'data' in url.lower() or 'chart' in url.lower():
                                network_requests.append(url)
                    except:
                        pass

                if network_requests:
                    print(f"  -> 捕獲到 {len(network_requests)} 個相關網絡請求:")
                    for req in network_requests[:10]:
                        print(f"     {req}")
                else:
                    print("  -> 未捕獲到新的網絡請求")
            else:
                print("  -> 未找到「五年」按鈕")
                # 列出所有按鈕
                all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, .btn, [role='button']")
                print(f"  -> 頁面上找到 {len(all_buttons)} 個按鈕:")
                for btn in all_buttons[:10]:
                    text = btn.text.strip()
                    if text:
                        print(f"     - {text}")

        except Exception as e:
            print(f"  -> 方法 3 失敗: {e}")
            import traceback
            traceback.print_exc()

        # 方法 4: 再次嘗試讀取 Highcharts 數據（點擊按鈕後）
        print("\n[6] 再次嘗試讀取 Highcharts 數據...")
        try:
            result = driver.execute_script("""
                if (typeof Highcharts !== 'undefined') {
                    var charts = Highcharts.charts.filter(c => c);
                    var allData = [];
                    charts.forEach(function(chart, idx) {
                        if (chart && chart.series) {
                            chart.series.forEach(function(series, sidx) {
                                if (series.data) {
                                    allData.push({
                                        chartIndex: idx,
                                        seriesIndex: sidx,
                                        seriesName: series.name,
                                        dataLength: series.data.length,
                                        sampleData: series.data.slice(0, 5).map(function(p) {
                                            return {x: p.x, y: p.y};
                                        })
                                    });
                                }
                            });
                        }
                    });
                    return allData;
                }
                return null;
            """)

            if result:
                print(f"  -> 找到 {len(result)} 個圖表/系列:")
                for r in result:
                    print(f"     Chart {r['chartIndex']}, Series {r['seriesIndex']}: {r.get('seriesName', 'N/A')}, {r['dataLength']} 點")
                    if r['sampleData']:
                        print(f"       樣本: {r['sampleData'][:2]}")
        except Exception as e:
            print(f"  -> 失敗: {e}")

        # 保持瀏覽器開啟
        print("\n" + "=" * 60)
        print("探索完成！瀏覽器保持開啟，按 Enter 關閉...")
        print("=" * 60)
        input()

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    explore_ceic()
