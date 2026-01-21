# 數據來源說明

本文件說明 `backsolve-miner-vs-metal-ratio-with-fundamentals` 技能使用的數據來源。

## 價格數據

### Yahoo Finance (yfinance)

**主要來源**，透過 `yfinance` 套件取得。

| 資產類型       | 代碼範例    | 可用歷史   | 頻率支援          |
|----------------|-------------|------------|-------------------|
| 金屬期貨       | SI=F, GC=F  | 20+ 年     | 日/週/月          |
| 金屬現貨       | XAGUSD=X    | 10+ 年     | 日/週/月          |
| 礦業 ETF       | SIL, GDX    | 上市至今   | 日/週/月          |
| 礦業個股       | PAAS, AG    | 上市至今   | 日/週/月          |

```python
import yfinance as yf

# 白銀期貨週頻
silver = yf.download("SI=F", start="2015-01-01", interval="1wk")

# 銀礦 ETF 日頻
sil = yf.download("SIL", start="2015-01-01", interval="1d")
```

### 備援來源

| 來源          | 優點                     | 缺點                       |
|---------------|--------------------------|----------------------------|
| Stooq         | 覆蓋範圍廣               | API 限制較多               |
| Alpha Vantage | 支援更多指標             | 免費方案有日限額           |
| FRED          | 官方來源                 | 金屬數據有限               |

---

## 財務報表數據

### SEC EDGAR XBRL API（美國公司）

**主要來源**，結構化程度最高。

**API 端點**

```
https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
```

**可用欄位**

| 類別           | 欄位                                            |
|----------------|------------------------------------------------|
| 資產負債表     | LongTermDebt, CashAndCashEquivalents, Assets    |
| 損益表         | Revenues, OperatingIncomeLoss, NetIncome        |
| 現金流量表     | NetCashProvidedByOperatingActivities, Capex     |
| 股本           | CommonStockSharesOutstanding                    |

**常見銀礦公司 CIK**

| Ticker | CIK         | 公司名稱                    |
|--------|-------------|-----------------------------|
| PAAS   | 0001209028  | Pan American Silver Corp    |
| AG     | 0001331877  | First Majestic Silver Corp  |
| HL     | 0000719413  | Hecla Mining Company        |
| CDE    | 0000018974  | Coeur Mining, Inc.          |
| EXK    | 0001437419  | Endeavour Silver Corp       |
| FSM    | 0001555280  | Fortuna Silver Mines Inc.   |
| MAG    | 0001331255  | MAG Silver Corp             |

**使用注意**

- 需設定 User-Agent 標頭（含聯絡信箱）
- 建議設定合理的請求間隔（1-2 秒）
- 快取財報數據（季度更新）

---

### SEDAR+（加拿大公司）

許多銀礦公司在加拿大上市，需從 SEDAR+ 取得揭露：

**網址**

```
https://www.sedarplus.ca
```

**抓取方式**

需使用 Selenium 模擬瀏覽器：
1. 搜尋公司名稱
2. 篩選文件類型（年報、MD&A）
3. 下載 PDF 或 HTML

**AISC 常見位置**

- Management's Discussion & Analysis (MD&A)
- Annual Information Form (AIF)
- 年報的 Operations Review 章節

---

### 公司 Investor Relations

當 SEC/SEDAR 無法取得 AISC 時：

| 資訊類型       | 常見格式   | 位置                           |
|----------------|-----------|--------------------------------|
| 財報簡報       | PDF/PPT   | IR 網站 > Presentations        |
| 季報摘要       | PDF       | IR 網站 > Quarterly Reports    |
| 年報           | PDF       | IR 網站 > Annual Reports       |
| 產量報告       | PDF/HTML  | IR 網站 > Operations           |

---

## ETF 持股數據

### 官方 Holdings CSV（優先）

| ETF 發行商     | 網址                              | 更新頻率   |
|----------------|-----------------------------------|------------|
| Global X       | globalxetfs.com/funds/{ticker}/   | 每日       |
| VanEck         | vaneck.com/etf/{ticker}/          | 每日       |
| iShares        | ishares.com/us/products/          | 每日       |

**SIL Holdings 範例**

```
Ticker, Name, Weight(%)
PAAS, Pan American Silver, 12.5
AG, First Majestic, 8.2
HL, Hecla Mining, 7.1
...
```

### SEC N-PORT（備援）

基金季度持股申報（Form N-PORT）：

```
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={fund_cik}&type=N-PORT
```

**解析方式**

N-PORT 為 XML 格式，包含：
- 持股清單
- 市值
- 權重

**注意**

- 季度申報，時滯 60 天
- 格式較複雜

---

## AISC 專用來源

### MD&A 文字抽取

AISC 常見揭露格式：

```
"All-in sustaining costs (AISC) were $28.50 per silver ounce..."
"AISC of $27.80/oz for the quarter..."
"The Company reported an AISC of US$29.10 per payable ounce..."
```

**抽取正則**

```python
patterns = [
    r'AISC\s+(?:of\s+)?\$?([\d.]+)\s*(?:per\s+)?(?:ounce|oz)',
    r'all-in\s+sustaining\s+cost[s]?\s+(?:of\s+)?\$?([\d.]+)',
    r'AISC\s+(?:was|were)\s+\$?([\d.]+)',
]
```

### 產業報告

| 報告來源               | 內容                        | 取得方式         |
|------------------------|-----------------------------|------------------|
| World Silver Survey    | 全球銀礦成本曲線            | 付費             |
| S&P Global Market Intel| 個股成本估計                | 付費             |
| 公司簡報               | 揭露 AISC                   | 免費（IR 網站）  |

---

## 數據品質與限制

### 時滯問題

| 數據類型       | 典型時滯      | 影響                         |
|----------------|---------------|------------------------------|
| 價格           | 即時/前一日   | 無                           |
| 財報 (SEC)     | 1-2 月        | 因子反映過去                 |
| AISC (揭露)    | 1-3 月        | 成本估計滯後                 |
| ETF Holdings   | 1-2 日        | 權重基本準確                 |

### 覆蓋率問題

| 欄位           | 覆蓋率        | 補救措施                     |
|----------------|---------------|------------------------------|
| 價格           | 100%          | -                            |
| 負債/現金      | 95%+          | 用 yfinance 財務摘要補        |
| EBITDA         | 80%+          | 用 OperatingIncome + D&A proxy |
| AISC (揭露)    | 60%           | 用 proxy 回算                |
| 產量 (oz)      | 50%           | 從年報/簡報手動抽取          |

### 口徑差異

| 問題                 | 說明                                         | 處理方式              |
|----------------------|----------------------------------------------|-----------------------|
| AISC 定義不一致      | 各公司揭露標準略有差異                       | 使用同業中位數參考    |
| 財年不同步           | 有些公司財年結束在 6 月                      | 以最近一期為準        |
| 幣別差異             | 加拿大公司可能用 CAD 報告                    | 轉換為 USD            |

---

## 快取策略建議

| 數據類型       | 快取時間      | 理由                         |
|----------------|---------------|------------------------------|
| 價格           | 1 小時        | 交易時段可能變動             |
| ETF Holdings   | 1 天          | 每日更新                     |
| 財報 (SEC)     | 7 天          | 季度更新                     |
| AISC           | 30 天         | 季度揭露                     |

```python
cache_config = {
    'prices': {'max_age_hours': 1},
    'holdings': {'max_age_hours': 24},
    'filings': {'max_age_hours': 168},    # 7 天
    'aisc': {'max_age_hours': 720}        # 30 天
}
```
