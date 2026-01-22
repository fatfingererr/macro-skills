#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
探索 SHFE 網站結構
用於理解如何模擬人類操作抓取白銀庫存周報數據
"""

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

# 設定目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

# User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


def get_stealth_driver(headless: bool = False) -> webdriver.Chrome:
    """建立防偵測的 Chrome Driver"""
    options = Options()

    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # 防偵測設定
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # 隨機 User-Agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)

    return driver


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """隨機延遲（模擬人類行為）"""
    delay = random.uniform(min_sec, max_sec)
    print(f"  [人類延遲] {delay:.1f} 秒...")
    time.sleep(delay)


def explore_page():
    """探索 SHFE 頁面結構"""
    url = "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/"

    print("=" * 60)
    print("SHFE 網站結構探索")
    print("=" * 60)
    print(f"\n目標網址: {url}\n")

    driver = None
    try:
        print("[1] 啟動瀏覽器...")
        driver = get_stealth_driver(headless=False)  # 非 headless 方便觀察

        print("[2] 載入頁面...")
        driver.get(url)
        random_delay(3, 5)

        # 等待頁面完全載入
        print("[3] 等待頁面載入...")
        wait = WebDriverWait(driver, 30)

        # 保存初始頁面 HTML
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_DIR / "shfe_initial.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"  -> 已保存初始頁面至 {DEBUG_DIR / 'shfe_initial.html'}")

        # 分析頁面元素
        print("\n[4] 分析頁面元素...")

        # 查找日期選擇器
        date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text'][placeholder*='日期'], .el-date-editor, .date-picker")
        print(f"  -> 找到日期輸入框: {len(date_inputs)} 個")
        for i, elem in enumerate(date_inputs):
            print(f"     [{i}] class: {elem.get_attribute('class')}, id: {elem.get_attribute('id')}")

        # 查找下拉選單
        selects = driver.find_elements(By.CSS_SELECTOR, "select, .el-select")
        print(f"  -> 找到下拉選單: {len(selects)} 個")
        for i, elem in enumerate(selects):
            print(f"     [{i}] class: {elem.get_attribute('class')}, id: {elem.get_attribute('id')}")

        # 查找按鈕
        buttons = driver.find_elements(By.CSS_SELECTOR, "button, .el-button")
        print(f"  -> 找到按鈕: {len(buttons)} 個")
        for i, elem in enumerate(buttons):
            text = elem.text.strip()
            if text:
                print(f"     [{i}] text: '{text}', class: {elem.get_attribute('class')}")

        # 查找表格
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"  -> 找到表格: {len(tables)} 個")

        # 查找包含「庫存」「周報」的元素
        inventory_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '庫存') or contains(text(), '周報')]")
        print(f"  -> 找到包含「庫存/周報」文字的元素: {len(inventory_elements)} 個")
        for i, elem in enumerate(inventory_elements[:10]):
            text = elem.text.strip()[:50]
            tag = elem.tag_name
            print(f"     [{i}] <{tag}>: '{text}'")

        # 查找包含「白銀」的元素
        silver_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '白银') or contains(text(), '白銀')]")
        print(f"  -> 找到包含「白銀」文字的元素: {len(silver_elements)} 個")
        for i, elem in enumerate(silver_elements[:5]):
            text = elem.text.strip()[:50]
            tag = elem.tag_name
            print(f"     [{i}] <{tag}>: '{text}'")

        # 等待用戶觀察
        print("\n" + "=" * 60)
        print("頁面已載入，請手動觀察網頁結構")
        print("按 Enter 繼續探索或 Ctrl+C 退出...")
        print("=" * 60)
        input()

        # 嘗試尋找並列出所有可點擊的元素
        print("\n[5] 分析可點擊元素...")
        clickables = driver.find_elements(By.CSS_SELECTOR, "a, button, [onclick], [role='button'], .el-tabs__item")
        print(f"  -> 找到可點擊元素: {len(clickables)} 個")

        # 保存最終頁面
        with open(DEBUG_DIR / "shfe_final.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\n已保存最終頁面至 {DEBUG_DIR / 'shfe_final.html'}")

        print("\n探索完成！")
        print("請查看 debug 目錄中的 HTML 文件以了解頁面結構")

        # 保持瀏覽器開啟以便手動觀察
        print("\n瀏覽器保持開啟，按 Enter 關閉...")
        input()

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("瀏覽器已關閉")


if __name__ == "__main__":
    explore_page()
