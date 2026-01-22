# 資料來源：SGE/SHFE 庫存數據抓取

本文件說明上海白銀庫存數據的來源、抓取方法與反偵測策略。

---

## 主要資料來源

### 1. SGE（上海黃金交易所）

**官方網站**：https://www.sge.com.cn

**數據位置**：行情周報 PDF → 指定倉庫庫存周報

**數據內容**：
| 欄位 | 說明 | 單位 |
|------|------|------|
| 日期 | 周報截止日 | YYYY-MM-DD |
| 白銀庫存 | 指定倉庫白銀庫存量 | kg |

**抓取方法**：
1. 訪問 SGE 官網「市場數據」→「行情周報」
2. 下載週報 PDF 檔案
3. 使用 pdfplumber 解析 PDF 表格
4. 定位「指定倉庫庫存周報」區塊
5. 提取白銀（Ag）庫存數據

**PDF 解析範例**：
```python
import pdfplumber

def parse_sge_pdf(pdf_path):
    """解析 SGE 行情周報 PDF"""
    with pdfplumber.open(pdf_path) as pdf:
        # 通常在最後幾頁
        for page in pdf.pages[-3:]:
            text = page.extract_text()
            if "指定仓库库存周报" in text:
                tables = page.extract_tables()
                for table in tables:
                    # 尋找白銀（Ag）行
                    for row in table:
                        if row and "Ag" in str(row[0]):
                            # 提取庫存數據
                            stock_kg = float(row[1].replace(",", ""))
                            return stock_kg
    return None
```

### 2. SHFE（上海期貨交易所）

**官方網站**：https://www.shfe.com.cn

**數據位置**：倉單日報 / Weekly Inventory

**數據內容**：
| 欄位 | 說明 | 單位 |
|------|------|------|
| 日期 | 數據日期 | YYYY-MM-DD |
| 白銀倉單 | 可交割倉單數量 | kg |

**抓取方法**：
1. 訪問 SHFE 官網「數據」→「倉單日報」
2. 選擇品種「白銀」
3. 等待 AJAX 載入完成
4. 解析 HTML 表格

**Selenium 抓取範例**：
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_shfe_inventory(driver, date):
    """抓取 SHFE 白銀倉單數據"""
    url = f"https://www.shfe.com.cn/data/dailydata/kx/kxXXXX.html"
    driver.get(url)

    # 等待表格載入
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "table.data-table")
    ))

    # 解析表格
    table = driver.find_element(By.CSS_SELECTOR, "table.data-table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells and "白银" in cells[0].text:
            stock_kg = float(cells[2].text.replace(",", ""))
            return stock_kg

    return None
```

---

## 反偵測策略

### Chrome 配置

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_stealth_driver():
    """建立防偵測的 Chrome Driver"""
    options = Options()

    # 基本設定
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
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
        # ... 更多 UA
    ]
    import random
    options.add_argument(f'user-agent={random.choice(user_agents)}')

    return webdriver.Chrome(options=options)
```

### 隨機延遲

```python
import asyncio
import random

async def random_delay(min_sec=1.0, max_sec=3.0):
    """隨機延遲，模擬人類行為"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)
```

### 重試機制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=10):
    """重試裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"嘗試 {attempt + 1} 失敗，{delay}秒後重試...")
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator
```

---

## 交叉驗證資料來源

### Yahoo Finance（價格數據）

```python
import yfinance as yf

# 白銀期貨近月
silver_futures = yf.download("SI=F", start="2020-01-01")

# 白銀現貨
silver_spot = yf.download("XAGUSD=X", start="2020-01-01")
```

### MacroMicro（ETF 持倉）

參考 `monitor-etf-holdings-drawdown-risk` skill 的 Highcharts 抓取方法。

**關鍵等待時間**：MacroMicro 圖表需要 35 秒以上才能完全渲染。

### COMEX 庫存

**來源**：CME Group 官網

**數據**：
- Registered（已登記）：可交割的庫存
- Eligible（合格）：符合交割標準但未登記

**注意**：COMEX 數據可能需要付費訂閱或有存取限制。

---

## 快取策略

### 快取目錄結構

```
data/
├── sge_stock.csv           # SGE 庫存時間序列
├── shfe_stock.csv          # SHFE 庫存時間序列
├── combined_stock.csv      # 合併庫存
├── cache_meta.json         # 快取元資料
└── debug/                  # 除錯用原始檔案
    ├── sge_report_20260116.pdf
    └── shfe_page_20260116.html
```

### 快取元資料

```json
{
  "sge": {
    "last_update": "2026-01-16T10:30:00Z",
    "data_range": ["2020-01-01", "2026-01-16"],
    "record_count": 312
  },
  "shfe": {
    "last_update": "2026-01-16T10:35:00Z",
    "data_range": ["2020-01-01", "2026-01-16"],
    "record_count": 1560
  }
}
```

### 快取有效期

- **預設**：12 小時
- **週末**：可延長至 48 小時（交易所不更新數據）

```python
from datetime import datetime, timedelta

def is_cache_valid(last_update, max_age_hours=12):
    """檢查快取是否有效"""
    if last_update is None:
        return False

    cache_age = datetime.now() - last_update
    return cache_age < timedelta(hours=max_age_hours)
```

---

## 常見問題

### Q: 中國網站存取受限怎麼辦？

A: 建議方案：
1. 使用 VPN 或代理
2. 從中國境內伺服器執行
3. 使用第三方數據提供商（如有）

### Q: PDF 格式變更怎麼辦？

A:
1. 檢查 `data/debug/` 目錄的原始 PDF
2. 分析新的表格結構
3. 更新 `parse_sge_pdf()` 函數中的選擇器

### Q: 被網站封鎖怎麼辦？

A:
1. 增加隨機延遲（3-5 秒）
2. 降低抓取頻率（每天 1-2 次）
3. 更換 User-Agent
4. 考慮使用 undetected-chromedriver
