#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
從 CEIC Data 網站抓取上海期貨交易所白銀庫存數據

策略：
1. 首先嘗試直接從 Highcharts 圖表中提取數據
2. 如果失敗，嘗試解析 SVG 路徑並反推數據
3. 模擬人類操作選擇「五年」時間範圍
"""

import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    webdriver = None
    print("警告: Selenium 未安裝")
    print("請執行: pip install selenium webdriver-manager")

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

CEIC_URL = "https://www.ceicdata.com/zh-hans/china/shanghai-futures-exchange-commodity-futures-stock/cn-warehouse-stock-shanghai-future-exchange-silver"


def get_stealth_driver(headless: bool = True) -> webdriver.Chrome:
    """建立防偵測的 Chrome Driver"""
    if webdriver is None:
        raise ImportError("Selenium 未安裝")

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

    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)
    return driver


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """隨機延遲（模擬人類行為）"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def extract_highcharts_data(driver: webdriver.Chrome) -> Optional[List[Dict]]:
    """
    從 Highcharts 圖表中提取數據
    """
    scripts = [
        # 方法 1: 直接訪問 Highcharts.charts
        """
        if (typeof Highcharts !== 'undefined' && Highcharts.charts) {
            var charts = Highcharts.charts.filter(c => c);
            for (var i = 0; i < charts.length; i++) {
                var chart = charts[i];
                if (chart && chart.series && chart.series.length > 0) {
                    var series = chart.series[0];
                    if (series.data && series.data.length > 0) {
                        return series.data.map(function(p) {
                            return {x: p.x, y: p.y};
                        });
                    }
                }
            }
        }
        return null;
        """,
        # 方法 2: 從 window 對象查找
        """
        if (window.chart && window.chart.series) {
            return window.chart.series[0].data.map(function(p) {
                return {x: p.x, y: p.y};
            });
        }
        return null;
        """,
        # 方法 3: 查找所有 Highcharts 實例
        """
        var result = null;
        document.querySelectorAll('[data-highcharts-chart]').forEach(function(el) {
            var chartId = el.getAttribute('data-highcharts-chart');
            if (Highcharts.charts[chartId]) {
                var chart = Highcharts.charts[chartId];
                if (chart.series && chart.series[0] && chart.series[0].data) {
                    result = chart.series[0].data.map(function(p) {
                        return {x: p.x, y: p.y};
                    });
                }
            }
        });
        return result;
        """,
    ]

    for i, script in enumerate(scripts):
        try:
            result = driver.execute_script(script)
            if result and len(result) > 10:
                print(f"  -> 方法 {i+1} 成功，找到 {len(result)} 個數據點")
                return result
        except Exception as e:
            print(f"  -> 方法 {i+1} 失敗: {e}")

    return None


def extract_svg_data(driver: webdriver.Chrome) -> Optional[List[Tuple[float, float]]]:
    """
    從 SVG 路徑中提取數據（備用方法）
    """
    try:
        # 找到 SVG 中的 area 路徑
        svg_paths = driver.find_elements(By.CSS_SELECTOR, "svg path.highcharts-area")
        if not svg_paths:
            svg_paths = driver.find_elements(By.CSS_SELECTOR, "svg path[d*='L']")

        for path in svg_paths:
            d = path.get_attribute("d")
            if d and len(d) > 100:
                # 解析 SVG 路徑 M x,y L x,y L x,y ...
                points = []
                # 移除 M 和 Z，只保留數據點
                d = re.sub(r'[MZ]', '', d)
                # 找到所有 L 命令
                matches = re.findall(r'L?\s*([\d.]+)\s+([\d.]+)', d)
                for x, y in matches:
                    points.append((float(x), float(y)))

                if len(points) > 10:
                    print(f"  -> 從 SVG 提取到 {len(points)} 個座標點")
                    return points
    except Exception as e:
        print(f"  -> SVG 提取失敗: {e}")

    return None


def click_five_year_button(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """
    點擊「五年」按鈕
    """
    selectors = [
        "//button[contains(text(), '五年')]",
        "//span[contains(text(), '五年')]",
        "//a[contains(text(), '五年')]",
        "//div[contains(@class, 'chart-range')]//button[3]",
        "//div[contains(@class, 'range')]//span[contains(text(), '5')]",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    # 滾動到元素
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    random_delay(0.5, 1.0)

                    # 使用 ActionChains 點擊（更像人類）
                    actions = ActionChains(driver)
                    actions.move_to_element(elem)
                    random_delay(0.2, 0.5)
                    actions.click()
                    actions.perform()

                    print(f"  -> 成功點擊「五年」按鈕")
                    return True
        except Exception:
            continue

    # 嘗試直接用 JavaScript 點擊
    try:
        result = driver.execute_script("""
            var buttons = document.querySelectorAll('button, span, a');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.includes('五年') || buttons[i].textContent.includes('5Y')) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """)
        if result:
            print(f"  -> 通過 JavaScript 成功點擊「五年」按鈕")
            return True
    except Exception as e:
        print(f"  -> JavaScript 點擊失敗: {e}")

    return False


def fetch_ceic_silver_data(
    headless: bool = True,
    debug: bool = False
) -> Optional[pd.DataFrame]:
    """
    抓取 CEIC 上海期貨交易所白銀庫存數據

    Parameters
    ----------
    headless : bool
        是否使用無頭模式
    debug : bool
        是否保存除錯資訊

    Returns
    -------
    pd.DataFrame or None
        包含 date 和 stock_tonnes 的 DataFrame
    """
    driver = None
    try:
        print("=" * 60)
        print("CEIC 上海期貨交易所白銀庫存數據抓取")
        print("=" * 60)

        # 1. 啟動瀏覽器
        print("\n[1] 啟動瀏覽器...")
        driver = get_stealth_driver(headless=headless)

        # 2. 載入頁面
        print(f"[2] 載入頁面...")
        driver.get(CEIC_URL)
        random_delay(3, 5)

        wait = WebDriverWait(driver, 30)

        # 3. 等待圖表載入
        print("[3] 等待圖表載入...")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg, .highcharts-container, iframe")))
        except:
            print("  -> 警告: 未能等到圖表元素")
        random_delay(2, 3)

        # 4. 嘗試點擊「五年」按鈕
        print("[4] 嘗試選擇「五年」時間範圍...")
        if click_five_year_button(driver, wait):
            random_delay(3, 5)  # 等待數據更新

        # 5. 保存頁面用於除錯
        if debug:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            with open(DEBUG_DIR / "ceic_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"  -> 已保存頁面至 {DEBUG_DIR / 'ceic_page.html'}")

        # 6. 嘗試提取 Highcharts 數據
        print("[5] 嘗試從 Highcharts 提取數據...")
        data = extract_highcharts_data(driver)

        if data:
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['x'], unit='ms')
            df['stock_tonnes'] = df['y']
            df = df[['date', 'stock_tonnes']].dropna()
            df = df.sort_values('date').reset_index(drop=True)

            print(f"\n成功提取 {len(df)} 條記錄")
            print(f"日期範圍: {df['date'].min()} ~ {df['date'].max()}")
            print(f"\n最新 5 條記錄:")
            print(df.tail())

            return df

        # 7. 嘗試從 iframe 中的圖表提取
        print("[6] 嘗試從 iframe 提取數據...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                src = iframe.get_attribute("src")
                if src and "chart" in src.lower():
                    print(f"  -> 找到圖表 iframe: {src[:80]}...")
                    driver.switch_to.frame(iframe)
                    random_delay(1, 2)

                    data = extract_highcharts_data(driver)
                    driver.switch_to.default_content()

                    if data:
                        df = pd.DataFrame(data)
                        df['date'] = pd.to_datetime(df['x'], unit='ms')
                        df['stock_tonnes'] = df['y']
                        df = df[['date', 'stock_tonnes']].dropna()
                        return df.sort_values('date').reset_index(drop=True)
            except Exception as e:
                print(f"  -> iframe 處理失敗: {e}")
                driver.switch_to.default_content()

        # 8. 備用：嘗試從 SVG 提取並映射
        print("[7] 備用方法：從 SVG 路徑提取數據...")
        svg_points = extract_svg_data(driver)
        if svg_points:
            # 這只能得到相對座標，需要軸信息來轉換
            # 暫時保存原始數據用於分析
            if debug:
                with open(DEBUG_DIR / "ceic_svg_points.json", "w") as f:
                    json.dump(svg_points, f)
            print("  -> SVG 數據需要軸映射，無法直接使用")

        print("\n抓取失敗：無法從頁面提取數據")
        return None

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        if driver:
            driver.quit()
            print("\n瀏覽器已關閉")


def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description="從 CEIC 抓取 SHFE 白銀庫存數據")
    parser.add_argument("--output", type=str, default=str(DATA_DIR / "ceic_shfe_silver.csv"),
                        help="輸出檔案路徑")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="使用無頭模式")
    parser.add_argument("--no-headless", action="store_true",
                        help="不使用無頭模式（顯示瀏覽器）")
    parser.add_argument("--debug", action="store_true",
                        help="保存除錯資訊")

    args = parser.parse_args()

    headless = args.headless and not args.no_headless

    df = fetch_ceic_silver_data(headless=headless, debug=args.debug)

    if df is not None:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n數據已保存至: {output_path}")
    else:
        print("\n抓取失敗，請檢查網站結構是否變化")


if __name__ == "__main__":
    main()
