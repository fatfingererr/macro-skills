# 鋰數據來源參考

本文件詳細說明所有可用的鋰相關數據來源，包括 URL、數據類型、更新頻率和使用限制。

---

## Tier 0: 免費、穩定、口徑一致

### USGS Lithium Statistics & Information

**主入口**
- URL: https://www.usgs.gov/centers/national-minerals-information-center/lithium-statistics-and-information
- 數據類型: 年度世界產量、國別結構、儲量、消費
- 更新頻率: 年度（每年 1-2 月發布前年數據）
- 格式: PDF (MCS)、Excel、HTML 表格

**直接數據連結**
- Mineral Commodity Summaries: https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lithium.pdf
- 歷史統計: https://www.usgs.gov/media/files/lithium-statistics

**關鍵欄位**
| 欄位 | 說明 | 單位 |
|------|------|------|
| World mine production | 全球礦場產量 | metric tons (Li content) |
| Production by country | 國別產量 | metric tons |
| Reserves | 儲量 | metric tons |
| Apparent consumption | 表觀消費（美國） | metric tons |

**注意事項**
- USGS 使用 Li content（鋰金屬含量），非 LCE
- 轉換: 1 t Li ≈ 5.32 t LCE

---

### IEA Global EV Outlook

**主入口**
- URL: https://www.iea.org/reports/global-ev-outlook-2024
- 數據類型: EV 銷量、電池需求、關鍵金屬需求
- 更新頻率: 年度（通常 4 月發布）
- 格式: 互動圖表、PDF、Excel

**數據瀏覽器**
- Global EV Data Explorer: https://www.iea.org/data-and-statistics/data-product/global-ev-data-explorer

**關鍵欄位**
| 欄位 | 說明 | 單位 |
|------|------|------|
| EV sales | 電動車銷量 | million units |
| Battery demand | 電池需求 | GWh |
| Lithium demand | 鋰需求（如有） | kt |
| EV stock | 電動車保有量 | million units |

**注意事項**
- IEA 電池需求包含 EV 和儲能
- 鋰需求需要自行轉換（假設 kg/kWh）

---

### Australia Resources & Energy Quarterly (REQ)

**主入口**
- URL: https://www.industry.gov.au/publications/resources-and-energy-quarterly
- 數據類型: 澳洲鋰產量、出口、價格展望
- 更新頻率: 季度
- 格式: PDF、Excel

**關鍵章節**
- Lithium outlook
- Export earnings
- Production volumes
- Price forecasts

**關鍵欄位**
| 欄位 | 說明 | 單位 |
|------|------|------|
| Production volume | 澳洲產量 | kt spodumene / kt LCE |
| Export value | 出口金額 | AUD billion |
| Export volume | 出口量 | kt |
| Price outlook | 價格展望 | USD/t |

**注意事項**
- 澳洲以鋰輝石(spodumene)為主，需轉換
- REQ 包含 5 年前瞻預測

---

### ABS Lithium Exports

**主入口**
- URL: https://www.abs.gov.au/statistics/economy/international-trade
- 數據類型: 澳洲鋰出口金額/數量
- 更新頻率: 月度
- 格式: TableBuilder、API

**HS Code**
- 2825.20 (Lithium oxide and hydroxide)
- 2836.91 (Lithium carbonate)
- 2530.90 (部分鋰精礦)

**關鍵欄位**
| 欄位 | 說明 | 單位 |
|------|------|------|
| Export value | 出口金額 | AUD |
| Export quantity | 出口數量 | kg |
| Destination | 目的地國家 | - |

---

### Global X LIT ETF

**主入口**
- URL: https://www.globalxetfs.com/funds/lit/
- 數據類型: ETF 持股、NAV、factsheet
- 更新頻率: 日度（持股）、月度（factsheet）
- 格式: HTML、PDF、CSV

**Factsheet**
- 通常在頁面底部或 Documents 區域

**關鍵欄位**
| 欄位 | 說明 | 單位 |
|------|------|------|
| Holdings | 持股列表 | ticker, weight |
| NAV | 淨值 | USD |
| Total assets | 總資產 | USD |
| Sector breakdown | 產業分布 | % |

---

## Tier 1: 免費但分散、需整合

### CME Lithium Hydroxide Futures

**主入口**
- URL: https://www.cmegroup.com/markets/metals/battery-metals/lithium-hydroxide-cif-cjk-fastmarkets.html
- 數據類型: 期貨價格、成交量、未平倉
- 更新頻率: 即時
- 格式: HTML、API（付費）

**合約規格**
| 項目 | 說明 |
|------|------|
| 標的 | Lithium Hydroxide Monohydrate CIF CJK |
| 報價基準 | Fastmarkets |
| 合約大小 | 1 metric ton |
| 報價單位 | USD/kg |

**注意事項**
- 流動性可能較低
- 可作為價格 proxy，但不完全等於現貨

---

### 鋰相關公司財報

主要公司及其報告來源：

| 公司 | 來源 | 類型 |
|------|------|------|
| Albemarle (ALB) | SEC EDGAR | 10-K, 10-Q |
| SQM | NYSE filings | 20-F |
| Livent/Arcadium (LTHM) | SEC EDGAR | 10-K, 10-Q |
| Pilbara Minerals (PLS.AX) | ASX | Annual Report |
| IGO Limited (IGO.AX) | ASX | Annual Report |
| Mineral Resources (MIN.AX) | ASX | Annual Report |
| Ganfeng Lithium | HKEX | Annual Report |

**關鍵數據**
- 產量/銷量
- 產能利用率
- 價格實現（realized price）
- 產能擴張計劃

---

## Tier 2: 付費、更即時完整

### Fastmarkets

**主入口**
- URL: https://www.fastmarkets.com/
- 數據類型: 碳酸鋰/氫氧化鋰報價
- 更新頻率: 週度（部分日度）
- 格式: API、Excel

**方法學（免費）**
- URL: https://www.fastmarkets.com/methodology
- 可了解報價規格、樣本來源、計算方法

**關鍵報價**
| 報價 | 規格 | 頻率 |
|------|------|------|
| Lithium carbonate 99.5% battery grade | CIF China, Japan, Korea | Weekly |
| Lithium hydroxide monohydrate 56.5% | CIF China, Japan, Korea | Weekly |
| Spodumene concentrate 6% | FOB Australia | Weekly |

---

### SMM (上海有色網)

**主入口**
- URL: https://www.smm.cn/
- 數據類型: 中國碳酸鋰現貨價格
- 更新頻率: 日度
- 格式: HTML、API（付費）

**方法學（免費）**
- 可查看指數計算方式、樣本企業

**關鍵報價**
| 報價 | 規格 | 頻率 |
|------|------|------|
| 電池級碳酸鋰 | 99.5% min | 日度 |
| 工業級碳酸鋰 | 99.2% min | 日度 |
| 電池級氫氧化鋰 | 56.5% min | 日度 |

**注意事項**
- 中國現貨價格，可能與國際價格有價差
- 人民幣報價，需匯率轉換

---

### 其他付費來源

| 來源 | 專長 | 網址 |
|------|------|------|
| Benchmark Mineral Intelligence | 電池供應鏈、成本曲線 | benchmarkminerals.com |
| BloombergNEF | 能源轉型、電池技術 | about.bnef.com |
| Wood Mackenzie | 採礦、金屬 | woodmac.com |
| CRU | 金屬價格、供需 | crugroup.com |
| S&P Global Market Intelligence | 礦業資產、產量 | spglobal.com |

---

## 數據等級對照表

| data_level | 供給數據 | 需求數據 | 價格數據 | ETF 數據 |
|------------|----------|----------|----------|----------|
| free_nolimit | USGS, AU REQ | IEA | CME 期貨/Proxy | Global X |
| free_limit | + ABS 月度 | + 公司財報 | + 方法學參考 | 同上 |
| paid_low | 同上 | + 詳細電池拆分 | Fastmarkets/SMM | 同上 |
| paid_high | + S&P mine DB | + BNEF 預測 | + Benchmark | 同上 |

---

## 數據抓取注意事項

### 遵守 robots.txt
- 所有網站抓取前檢查 robots.txt
- 遵守 Crawl-delay 指令

### 請求頻率
- 保持合理間隔（至少 1-2 秒）
- 使用隨機延遲避免被封鎖

### User-Agent
- 使用真實瀏覽器 User-Agent
- 參考 `design-human-like-crawler.md`

### 數據授權
- 免費數據可用於分析
- 付費數據需有效訂閱
- 不得重新分發原始數據
