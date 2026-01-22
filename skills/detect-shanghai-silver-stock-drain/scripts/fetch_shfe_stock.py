#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SHFE（上海期貨交易所）白銀庫存數據抓取

主要數據源：CEIC Data (通過 SVG 圖表解析)
- URL: https://www.ceicdata.com/zh-hans/china/shanghai-futures-exchange-commodity-futures-stock/cn-warehouse-stock-shanghai-future-exchange-silver
- 數據範圍：2012-07-02 至今
- 更新頻率：每日

Usage:
    python fetch_shfe_stock.py --output data/shfe_stock.csv
    python fetch_shfe_stock.py --weeks 50        # 獲取最近 50 週數據
    python fetch_shfe_stock.py --years 5         # 獲取 5 年數據
    python fetch_shfe_stock.py --force-update    # 強制更新
    python fetch_shfe_stock.py --debug           # 除錯模式
"""

import argparse
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("警告: Selenium 未安裝")
    print("請執行: pip install selenium webdriver-manager")

# 設定目錄
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

# CEIC 圖表 URL
CEIC_CHART_URL = "https://www.ceicdata.com/datapage/charts/o_china_cn-warehouse-stock-shanghai-future-exchange-silver/"

# User-Agent 列表（模擬人類瀏覽器）
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


def get_stealth_driver(headless: bool = True):
    """建立防偵測的 Chrome Driver"""
    if not HAS_SELENIUM:
        raise ImportError("Selenium 未安裝，請執行: pip install selenium webdriver-manager")

    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)
    return driver


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """隨機延遲（模擬人類行為）"""
    time.sleep(random.uniform(min_sec, max_sec))


def fetch_svg_content(url: str, headless: bool = True) -> Optional[str]:
    """使用 Selenium 獲取 SVG 內容"""
    driver = None
    try:
        print(f"  正在獲取圖表數據...")
        driver = get_stealth_driver(headless=headless)
        random_delay(1, 2)
        driver.get(url)
        time.sleep(3)

        content = driver.page_source
        if '<svg' in content:
            start = content.find('<svg')
            end = content.find('</svg>') + 6
            if start != -1 and end > start:
                return content[start:end]
        return content

    except Exception as e:
        print(f"  獲取失敗: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def extract_plot_bounds(svg_content: str) -> Tuple[float, float, float, float]:
    """從 SVG 中提取繪圖區域邊界"""
    match = re.search(
        r'highcharts-plot-background[^/]*x="([\d.]+)"[^/]*y="([\d.]+)"[^/]*width="([\d.]+)"[^/]*height="([\d.]+)"',
        svg_content
    )
    if match:
        w = float(match.group(3))
        h = float(match.group(4))
        return (0, w, 0, h)
    return (0, 1094, 0, 399)


def parse_svg_axis_labels(svg_content: str) -> Tuple[Optional[List[str]], Optional[List[float]]]:
    """從 SVG 中解析軸標籤"""
    x_labels = []
    y_labels = []

    text_pattern = r'<text[^>]*>([^<]+)</text>'
    texts = re.findall(text_pattern, svg_content)

    for text in texts:
        text = text.strip()
        if re.match(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", text, re.I):
            x_labels.append(text)
        elif re.match(r"20\d{2}", text):
            x_labels.append(text)

        if re.match(r'^[\d,\.]+[kKmM]?$', text):
            try:
                num_text = text.replace(',', '')
                if 'k' in num_text.lower():
                    value = float(num_text.lower().replace('k', '')) * 1000
                elif 'm' in num_text.lower():
                    value = float(num_text.lower().replace('m', '')) * 1000000
                else:
                    value = float(num_text)
                y_labels.append(value)
            except ValueError:
                pass

    return x_labels if x_labels else None, y_labels if y_labels else None


def parse_svg_path_data(svg_content: str) -> Optional[List[Tuple[float, float]]]:
    """從 SVG 路徑中提取座標點"""
    all_paths = re.findall(r'd="(M[^"]+)"', svg_content)
    if not all_paths:
        return None

    path_data = max(all_paths, key=len)
    points = []

    path_data = re.sub(r'([MLHVCSQTAZmlhvcsqtaz])', r' \1 ', path_data)
    path_data = re.sub(r',', ' ', path_data)
    path_data = re.sub(r'\s+', ' ', path_data).strip()

    tokens = path_data.split()
    i = 0
    current_x, current_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]

        if cmd in ['M', 'm']:
            if i + 2 < len(tokens):
                try:
                    x, y = float(tokens[i+1]), float(tokens[i+2])
                    if cmd == 'm':
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    points.append((x, y))
                    i += 3
                except ValueError:
                    i += 1
            else:
                i += 1

        elif cmd in ['L', 'l']:
            if i + 2 < len(tokens):
                try:
                    x, y = float(tokens[i+1]), float(tokens[i+2])
                    if cmd == 'l':
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    points.append((x, y))
                    i += 3
                except ValueError:
                    i += 1
            else:
                i += 1

        elif cmd in ['H', 'h']:
            if i + 1 < len(tokens):
                try:
                    x = float(tokens[i+1])
                    if cmd == 'h':
                        x += current_x
                    current_x = x
                    points.append((current_x, current_y))
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1

        elif cmd in ['V', 'v']:
            if i + 1 < len(tokens):
                try:
                    y = float(tokens[i+1])
                    if cmd == 'v':
                        y += current_y
                    current_y = y
                    points.append((current_x, current_y))
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1

        elif cmd in ['Z', 'z']:
            i += 1

        else:
            try:
                x = float(cmd)
                if i + 1 < len(tokens):
                    y = float(tokens[i+1])
                    current_x, current_y = x, y
                    points.append((x, y))
                    i += 2
                else:
                    i += 1
            except ValueError:
                i += 1

    return points if len(points) > 10 else None


def convert_svg_to_dataframe(
    points: List[Tuple[float, float]],
    y_labels: Optional[List[float]],
    date_range: Tuple[datetime, datetime],
    svg_content: str
) -> pd.DataFrame:
    """將 SVG 座標轉換為實際數據"""
    start_date, end_date = date_range
    plot_left, plot_right, plot_top, plot_bottom = extract_plot_bounds(svg_content)

    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    if y_labels and len(y_labels) >= 2:
        y_min = min(y_labels)
        y_max = max(y_labels)
    else:
        y_min = 0
        y_max = 3500

    total_days = (end_date - start_date).days

    results = []
    for px, py in points:
        x_ratio = (px - plot_left) / plot_width if plot_width > 0 else 0
        x_ratio = max(0, min(1, x_ratio))
        days_offset = int(x_ratio * total_days)
        date = start_date + timedelta(days=days_offset)

        y_ratio = (plot_bottom - py) / plot_height if plot_height > 0 else 0
        y_ratio = max(0, min(1, y_ratio))
        value = y_min + y_ratio * (y_max - y_min)

        results.append({
            'date': date,
            'stock_tonnes': round(value, 2),
        })

    df = pd.DataFrame(results)
    df = df.drop_duplicates(subset=['date'], keep='first')
    df = df.sort_values('date').reset_index(drop=True)
    return df


def fetch_ceic_shfe_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    headless: bool = True,
    debug: bool = False,
) -> Optional[pd.DataFrame]:
    """
    從 CEIC 獲取 SHFE 白銀庫存數據

    Parameters
    ----------
    start_date : str, optional
        起始日期 (YYYY-MM-DD)，預設為 5 年前
    end_date : str, optional
        結束日期 (YYYY-MM-DD)，預設為今天
    headless : bool
        是否無頭模式
    debug : bool
        是否保存除錯資訊
    """
    if end_date is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    if start_date is None:
        start_dt = end_dt - timedelta(days=5*365)
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    url = f"{CEIC_CHART_URL}?type=area&from={start_dt.strftime('%Y-%m-%d')}&to={end_dt.strftime('%Y-%m-%d')}&lang=zh-hans"

    print(f"\n日期範圍: {start_dt.date()} ~ {end_dt.date()}")

    # 獲取 SVG
    svg_content = fetch_svg_content(url, headless=headless)
    if not svg_content:
        print("無法獲取 SVG 內容")
        return None

    if debug:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_DIR / "ceic_chart.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)

    # 解析 SVG
    _, y_labels = parse_svg_axis_labels(svg_content)
    points = parse_svg_path_data(svg_content)

    if not points:
        print("無法從 SVG 中提取路徑數據")
        return None

    print(f"  提取到 {len(points)} 個數據點")

    # 轉換為 DataFrame
    df = convert_svg_to_dataframe(
        points=points,
        y_labels=y_labels,
        date_range=(start_dt, end_dt),
        svg_content=svg_content,
    )

    return df


def extract_weekly_data(df: pd.DataFrame, day_of_week: int = 4) -> pd.DataFrame:
    """
    提取週報數據（預設為週五）

    Parameters
    ----------
    df : pd.DataFrame
        每日數據
    day_of_week : int
        週幾 (0=週一, 4=週五)
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].dt.dayofweek

    weekly = df[df['weekday'] == day_of_week].copy()
    weekly = weekly.drop(columns=['weekday'])
    weekly = weekly.sort_values('date').reset_index(drop=True)

    return weekly


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="SHFE 白銀庫存數據抓取（CEIC 數據源）")
    parser.add_argument("--years", type=int, default=5, help="獲取幾年數據（預設 5 年）")
    parser.add_argument("--weeks", type=int, help="獲取最近幾週數據（覆蓋 --years）")
    parser.add_argument("--start", type=str, help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="結束日期 (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default=str(DATA_DIR / "shfe_stock.csv"), help="輸出檔案路徑")
    parser.add_argument("--weekly-output", type=str, default=str(DATA_DIR / "shfe_weekly_stock.csv"), help="週報輸出檔案")
    parser.add_argument("--force-update", action="store_true", help="強制更新（忽略快取）")
    parser.add_argument("--no-headless", action="store_true", help="顯示瀏覽器")
    parser.add_argument("--debug", action="store_true", help="除錯模式")

    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = Path(args.output)
    weekly_output_path = Path(args.weekly_output)

    # 檢查快取
    if output_path.exists() and not args.force_update:
        mtime = datetime.fromtimestamp(output_path.stat().st_mtime)
        cache_age = datetime.now() - mtime
        if cache_age < timedelta(hours=12):
            print(f"使用快取數據（{cache_age.total_seconds()/3600:.1f} 小時前更新）")
            df = pd.read_csv(output_path, parse_dates=["date"])
            print(f"數據範圍: {df['date'].min()} ~ {df['date'].max()}")
            print(f"記錄數: {len(df)}")
            return

    # 計算日期範圍
    end_date = args.end or datetime.now().strftime("%Y-%m-%d")

    if args.weeks:
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(weeks=args.weeks)).strftime("%Y-%m-%d")
    elif args.start:
        start_date = args.start
    else:
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=args.years*365)).strftime("%Y-%m-%d")

    print("=" * 60)
    print("SHFE 白銀庫存數據抓取（CEIC 數據源）")
    print("=" * 60)

    # 抓取數據
    df = fetch_ceic_shfe_data(
        start_date=start_date,
        end_date=end_date,
        headless=not args.no_headless,
        debug=args.debug,
    )

    if df is None or len(df) == 0:
        print("\n抓取失敗")
        return

    # 轉換為 kg 並保存（兼容原有格式）
    df_output = df.copy()
    df_output['stock_kg'] = df_output['stock_tonnes'] * 1000
    df_output = df_output[['date', 'stock_kg']]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_output.to_csv(output_path, index=False)
    print(f"\n每日數據已保存至: {output_path}")
    print(f"數據範圍: {df['date'].min()} ~ {df['date'].max()}")
    print(f"記錄數: {len(df)}")

    # 提取週報數據
    weekly_df = extract_weekly_data(df)
    weekly_df['stock_kg'] = weekly_df['stock_tonnes'] * 1000

    weekly_df[['date', 'stock_kg']].to_csv(weekly_output_path, index=False)
    print(f"\n週報數據已保存至: {weekly_output_path}")
    print(f"週報數據範圍: {weekly_df['date'].min()} ~ {weekly_df['date'].max()}")
    print(f"週報記錄數: {len(weekly_df)}")

    # 顯示最近數據
    print(f"\n最近 10 週數據:")
    for _, row in weekly_df.tail(10).iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')} (週五): {row['stock_tonnes']:.2f} 噸")


if __name__ == "__main__":
    main()
