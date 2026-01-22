#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
從 CEIC Data 的 SVG 圖表中提取數據

CEIC 的圖表是通過以下 URL 格式返回 SVG：
https://www.ceicdata.com/datapage/charts/o_china_cn-warehouse-stock-shanghai-future-exchange-silver/
    ?type=area&from=YYYY-MM-DD&to=YYYY-MM-DD&lang=zh-hans

這個 SVG 包含 Highcharts 渲染的數據，我們可以：
1. 解析 SVG 中的路徑數據
2. 從軸刻度推算實際值
"""

import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

import pandas as pd
import requests

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

CHART_BASE_URL = "https://www.ceicdata.com/datapage/charts/o_china_cn-warehouse-stock-shanghai-future-exchange-silver/"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_stealth_driver(headless: bool = True):
    """建立防偵測的 Chrome Driver"""
    if not HAS_SELENIUM:
        raise ImportError("Selenium 未安裝")

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


def fetch_svg_with_selenium(url: str, headless: bool = True) -> Optional[str]:
    """使用 Selenium 獲取 SVG 內容（更可靠）"""
    driver = None
    try:
        print(f"  使用 Selenium 獲取: {url[:80]}...")
        driver = get_stealth_driver(headless=headless)

        # 隨機延遲
        time.sleep(random.uniform(1, 2))

        driver.get(url)
        time.sleep(3)  # 等待 SVG 渲染

        # 獲取頁面源碼
        content = driver.page_source

        # 提取 SVG 部分
        if '<svg' in content:
            start = content.find('<svg')
            end = content.find('</svg>') + 6
            if start != -1 and end > start:
                return content[start:end]

        return content

    except Exception as e:
        print(f"  Selenium 獲取失敗: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def fetch_svg_with_requests(url: str) -> Optional[str]:
    """使用 requests 獲取 SVG（快速但可能被攔截）"""
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Referer': 'https://www.ceicdata.com/',
        }

        print(f"  使用 requests 獲取: {url[:80]}...")
        time.sleep(random.uniform(0.5, 1.5))

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.text

    except Exception as e:
        print(f"  requests 獲取失敗: {e}")
        return None


def parse_svg_axis_labels(svg_content: str) -> Tuple[Optional[List[str]], Optional[List[float]]]:
    """
    從 SVG 中解析軸標籤

    Returns:
        (x_labels, y_labels): X 軸日期標籤, Y 軸數值標籤
    """
    x_labels = []
    y_labels = []

    # 尋找文字元素
    # Highcharts 的軸標籤通常在 <text> 元素中
    text_pattern = r'<text[^>]*>([^<]+)</text>'
    texts = re.findall(text_pattern, svg_content)

    for text in texts:
        text = text.strip()

        # 嘗試解析為日期 (如 "Jan '21", "2021", "Jan 2021" 等)
        if re.match(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", text, re.I):
            x_labels.append(text)
        elif re.match(r"20\d{2}", text):
            x_labels.append(text)

        # 嘗試解析為數值 (如 "1,000", "500", "1.5k" 等)
        if re.match(r'^[\d,\.]+[kKmM]?$', text):
            try:
                # 處理千位分隔符和 k/m 後綴
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
    """
    從 SVG 路徑中提取座標點

    Returns:
        座標點列表 [(x1, y1), (x2, y2), ...]
    """
    # 尋找 area 或 line 路徑
    # Highcharts 使用 class="highcharts-area" 或 "highcharts-graph"
    path_patterns = [
        r'<path[^>]*class="[^"]*highcharts-area[^"]*"[^>]*d="([^"]+)"',
        r'<path[^>]*class="[^"]*highcharts-graph[^"]*"[^>]*d="([^"]+)"',
        r'<path[^>]*d="(M[^"]+L[^"]+)"[^>]*class="[^"]*highcharts',
        r'd="(M[\d\s.,LHVCSQTAZlhvcsqtaz-]+)"',
    ]

    path_data = None
    for pattern in path_patterns:
        match = re.search(pattern, svg_content, re.IGNORECASE)
        if match:
            path_data = match.group(1)
            break

    if not path_data:
        # 嘗試找最長的路徑（通常是數據路徑）
        all_paths = re.findall(r'd="(M[^"]+)"', svg_content)
        if all_paths:
            path_data = max(all_paths, key=len)

    if not path_data:
        return None

    # 解析路徑命令
    points = []

    # SVG 路徑命令: M (移動), L (直線), H (水平), V (垂直), C (曲線), Z (閉合)
    # 簡化處理：只提取 M 和 L 命令的座標

    # 先將路徑正規化
    path_data = re.sub(r'([MLHVCSQTAZmlhvcsqtaz])', r' \1 ', path_data)
    path_data = re.sub(r',', ' ', path_data)
    path_data = re.sub(r'\s+', ' ', path_data).strip()

    tokens = path_data.split()
    i = 0
    current_x, current_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]

        if cmd in ['M', 'm']:
            # 移動命令
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
            # 直線命令
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
            # 水平線
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
            # 垂直線
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
            # 可能是隱式的 L 命令（連續座標）
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


def extract_plot_bounds(svg_content: str) -> Tuple[float, float, float, float, float, float]:
    """
    從 SVG 中提取繪圖區域邊界和變換

    Returns:
        (plot_left, plot_right, plot_top, plot_bottom, translate_x, translate_y)

    注意: Highcharts 的數據路徑通常有 transform="translate(x,y)"
    """
    # 尋找 highcharts-plot-background 元素
    match = re.search(
        r'highcharts-plot-background[^/]*x="([\d.]+)"[^/]*y="([\d.]+)"[^/]*width="([\d.]+)"[^/]*height="([\d.]+)"',
        svg_content
    )

    # 尋找 translate 變換
    translate_match = re.search(
        r'transform="translate\(([\d.]+),([\d.]+)\)',
        svg_content
    )
    translate_x = float(translate_match.group(1)) if translate_match else 0
    translate_y = float(translate_match.group(2)) if translate_match else 0

    if match:
        w = float(match.group(3))
        h = float(match.group(4))
        # 路徑座標是相對於變換後的原點，所以使用 0 到 width/height
        return (0, w, 0, h, translate_x, translate_y)

    # 預設值
    return (0, 1094, 0, 399, 76, 10)


def convert_svg_coords_to_data(
    points: List[Tuple[float, float]],
    x_labels: Optional[List[str]],
    y_labels: Optional[List[float]],
    date_range: Tuple[datetime, datetime],
    svg_content: str = "",
) -> pd.DataFrame:
    """
    將 SVG 座標轉換為實際數據

    這是一個近似轉換，假設線性映射
    """
    start_date, end_date = date_range

    # 從 SVG 中提取繪圖區域邊界
    plot_left, plot_right, plot_top, plot_bottom, tx, ty = extract_plot_bounds(svg_content)
    print(f"  繪圖區域: x=[{plot_left}, {plot_right}], y=[{plot_top}, {plot_bottom}], translate=({tx}, {ty})")

    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    # 確定 Y 軸範圍
    if y_labels and len(y_labels) >= 2:
        y_min = min(y_labels)
        y_max = max(y_labels)
    else:
        # 從點推斷
        y_coords = [p[1] for p in points]
        y_coord_min = min(y_coords)
        y_coord_max = max(y_coords)
        # 假設典型範圍
        y_min = 0
        y_max = 3500  # 白銀庫存典型最大值約 3500 噸

    # 計算時間範圍（天數）
    total_days = (end_date - start_date).days

    results = []
    for px, py in points:
        # X 座標 -> 日期
        x_ratio = (px - plot_left) / plot_width if plot_width > 0 else 0
        x_ratio = max(0, min(1, x_ratio))
        days_offset = int(x_ratio * total_days)
        date = start_date + timedelta(days=days_offset)

        # Y 座標 -> 數值（注意 SVG Y 軸是反的）
        y_ratio = (plot_bottom - py) / plot_height if plot_height > 0 else 0
        y_ratio = max(0, min(1, y_ratio))
        value = y_min + y_ratio * (y_max - y_min)

        results.append({
            'date': date,
            'stock_tonnes': round(value, 2),
            'px': px,
            'py': py,
        })

    df = pd.DataFrame(results)

    # 去重（按日期）
    df = df.drop_duplicates(subset=['date'], keep='first')
    df = df.sort_values('date').reset_index(drop=True)

    return df


def fetch_ceic_silver_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_selenium: bool = True,
    headless: bool = True,
    debug: bool = False,
) -> Optional[pd.DataFrame]:
    """
    從 CEIC 獲取白銀庫存數據

    Parameters
    ----------
    start_date : str, optional
        起始日期 (YYYY-MM-DD)，預設為 5 年前
    end_date : str, optional
        結束日期 (YYYY-MM-DD)，預設為今天
    use_selenium : bool
        是否使用 Selenium（更可靠）
    headless : bool
        是否無頭模式
    debug : bool
        是否保存除錯資訊
    """
    # 設定日期範圍
    if end_date is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    if start_date is None:
        start_dt = end_dt - timedelta(days=5*365)
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    # 構建 URL
    url = f"{CHART_BASE_URL}?type=area&from={start_dt.strftime('%Y-%m-%d')}&to={end_dt.strftime('%Y-%m-%d')}&lang=zh-hans"

    print("=" * 60)
    print("CEIC 上海期貨交易所白銀庫存數據抓取")
    print("=" * 60)
    print(f"\n日期範圍: {start_dt.date()} ~ {end_dt.date()}")
    print(f"圖表 URL: {url[:80]}...")

    # 獲取 SVG 內容
    print("\n[1] 獲取 SVG 內容...")
    svg_content = None

    if use_selenium and HAS_SELENIUM:
        svg_content = fetch_svg_with_selenium(url, headless=headless)

    if not svg_content:
        svg_content = fetch_svg_with_requests(url)

    if not svg_content:
        print("無法獲取 SVG 內容")
        return None

    # 保存除錯資訊
    if debug:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_DIR / "ceic_chart.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"  已保存 SVG 至 {DEBUG_DIR / 'ceic_chart.svg'}")

    # 解析 SVG
    print("\n[2] 解析 SVG...")

    # 提取軸標籤
    x_labels, y_labels = parse_svg_axis_labels(svg_content)
    print(f"  X 軸標籤: {x_labels[:5] if x_labels else 'N/A'}...")
    print(f"  Y 軸標籤: {y_labels if y_labels else 'N/A'}")

    # 提取路徑數據
    points = parse_svg_path_data(svg_content)
    if not points:
        print("  無法從 SVG 中提取路徑數據")
        return None

    print(f"  提取到 {len(points)} 個座標點")

    # 轉換座標
    print("\n[3] 轉換座標為實際數據...")
    df = convert_svg_coords_to_data(
        points=points,
        x_labels=x_labels,
        y_labels=y_labels,
        date_range=(start_dt, end_dt),
        svg_content=svg_content,
    )

    print(f"\n轉換完成，共 {len(df)} 條記錄")
    print(f"日期範圍: {df['date'].min()} ~ {df['date'].max()}")
    print(f"數值範圍: {df['stock_tonnes'].min():.1f} ~ {df['stock_tonnes'].max():.1f} 噸")

    print("\n最新 5 條記錄:")
    print(df[['date', 'stock_tonnes']].tail())

    return df[['date', 'stock_tonnes']]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="從 CEIC SVG 圖表抓取數據")
    parser.add_argument("--start", type=str, help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="結束日期 (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default=str(DATA_DIR / "ceic_shfe_silver.csv"))
    parser.add_argument("--no-selenium", action="store_true", help="不使用 Selenium")
    parser.add_argument("--no-headless", action="store_true", help="顯示瀏覽器")
    parser.add_argument("--debug", action="store_true", help="保存除錯資訊")

    args = parser.parse_args()

    df = fetch_ceic_silver_data(
        start_date=args.start,
        end_date=args.end,
        use_selenium=not args.no_selenium,
        headless=not args.no_headless,
        debug=args.debug,
    )

    if df is not None:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n數據已保存至: {output_path}")
    else:
        print("\n抓取失敗")


if __name__ == "__main__":
    main()
