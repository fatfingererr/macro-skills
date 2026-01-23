# 數據來源說明

本文件說明美國銀行信貸存款脫鉤分析所需的數據來源與獲取方式。

---

## 1. FRED API 概述

### 1.1 什麼是 FRED

FRED（Federal Reserve Economic Data）是聖路易斯聯邦儲備銀行維護的經濟數據庫：
- 超過 800,000 個經濟時間序列
- 完全免費、公開
- 提供 REST API

### 1.2 API Key 申請

1. 前往 https://fred.stlouisfed.org/docs/api/api_key.html
2. 註冊帳號（免費）
3. 申請 API Key
4. 設定環境變數：
```bash
export FRED_API_KEY="your_api_key_here"
```

---

## 2. 核心數據指標

### 2.1 銀行貸款總量 (TOTLL)

| 屬性          | 值                                                    |
|---------------|-------------------------------------------------------|
| **Series ID** | TOTLL                                                 |
| **名稱**      | Loans and Leases in Bank Credit, All Commercial Banks |
| **單位**      | Billions of U.S. Dollars                              |
| **頻率**      | Weekly, Ending Wednesday                              |
| **季節調整**  | Not Seasonally Adjusted                               |
| **起始日期**  | 1947-01-01                                            |

**說明**：
- 美國所有商業銀行的放款與租賃總額
- 反映銀行「資產端」擴張
- 高度領先於信用循環、經濟景氣

**URL**: https://fred.stlouisfed.org/series/TOTLL

### 2.2 銀行存款總量 (DPSACBW027SBOG)

| 屬性          | 值                             |
|---------------|--------------------------------|
| **Series ID** | DPSACBW027SBOG                 |
| **名稱**      | Deposits, All Commercial Banks |
| **單位**      | Billions of U.S. Dollars       |
| **頻率**      | Weekly, Ending Wednesday       |
| **季節調整**  | Seasonally Adjusted            |
| **起始日期**  | 1973-01-03                     |

**說明**：
- 美國所有商業銀行的存款總額
- 反映銀行「負債端」資金來源
- 與貨幣政策、資金流向高度相關

**URL**: https://fred.stlouisfed.org/series/DPSACBW027SBOG

### 2.3 隔夜逆回購 (RRPONTSYD)

| 屬性          | 值                                                                                       |
|---------------|------------------------------------------------------------------------------------------|
| **Series ID** | RRPONTSYD                                                                                |
| **名稱**      | Overnight Reverse Repurchase Agreements: Treasury Securities Sold by the Federal Reserve |
| **單位**      | Billions of U.S. Dollars                                                                 |
| **頻率**      | Daily                                                                                    |
| **季節調整**  | Not Seasonally Adjusted                                                                  |
| **起始日期**  | 2013-09-23                                                                               |

**說明**：
- 聯準會隔夜逆回購操作規模
- 貨幣市場基金主要參與者
- 作為「資金被吸出銀行體系」的 proxy

**URL**: https://fred.stlouisfed.org/series/RRPONTSYD

---

## 3. 數據獲取程式碼

### 3.1 使用 fredapi

```python
from fredapi import Fred
import os

# 初始化
fred = Fred(api_key=os.environ.get('FRED_API_KEY'))

# 抓取數據
loans = fred.get_series('TOTLL', start_date='2022-06-01', end_date='2026-01-23')
deposits = fred.get_series('DPSACBW027SBOG', start_date='2022-06-01', end_date='2026-01-23')
rrp = fred.get_series('RRPONTSYD', start_date='2022-06-01', end_date='2026-01-23')
```

### 3.2 數據對齊

由於 RRP 是日頻，需要對齊至週頻：

```python
# 將 RRP 重採樣至週頻（週三結束）
rrp_weekly = rrp.resample('W-WED').last()

# 對齊到共同日期
common_dates = loans.index.intersection(deposits.index).intersection(rrp_weekly.index)
loans = loans.loc[common_dates]
deposits = deposits.loc[common_dates]
rrp = rrp_weekly.loc[common_dates]
```

---

## 4. Fallback 替代方案

### 4.1 當 FRED API 不可用時

| 替代方案          | 說明                  |
|-------------------|-----------------------|
| **FRED 網站下載** | 直接從網站下載 CSV    |
| **Quandl (FRED)** | Quandl 鏡像 FRED 數據 |
| **本地快取**      | 使用已快取的歷史數據  |

### 4.2 CSV 下載方式

```
https://fred.stlouisfed.org/graph/fredgraph.csv?id=TOTLL
https://fred.stlouisfed.org/graph/fredgraph.csv?id=DPSACBW027SBOG
https://fred.stlouisfed.org/graph/fredgraph.csv?id=RRPONTSYD
```

---

## 5. 快取策略

### 5.1 建議快取設定

| 數據           | 更新頻率 | 建議快取時間 |
|----------------|----------|--------------|
| TOTLL          | 週頻     | 1 天         |
| DPSACBW027SBOG | 週頻     | 1 天         |
| RRPONTSYD      | 日頻     | 12 小時      |

### 5.2 快取檔案結構

```
cache/
├── loans_TOTLL.json
│   ├── data: [...]
│   ├── fetched_at: "2026-01-23T10:00:00Z"
│   └── source: "FRED"
├── deposits_DPSACBW027SBOG.json
└── rrp_RRPONTSYD.json
```

---

## 6. 數據品質檢查

### 6.1 檢查清單

- [ ] 數據起始日期正確
- [ ] 無異常缺失值
- [ ] 數值在合理範圍內
- [ ] 日期索引連續（週頻）

### 6.2 異常值處理

```python
# 檢查異常跳動（超過 20% 週變化）
pct_change = loans.pct_change()
anomalies = pct_change[abs(pct_change) > 0.20]
if len(anomalies) > 0:
    print(f"Warning: {len(anomalies)} anomalies detected")
```

---

## 7. 補充數據來源

### 7.1 TGA（財政部一般帳戶）

| 屬性          | 值                             |
|---------------|--------------------------------|
| **Series ID** | WTREGEN                        |
| **說明**      | 可用於進一步分解流動性吸收來源 |

### 7.2 銀行準備金

| 屬性          | 值                      |
|---------------|-------------------------|
| **Series ID** | TOTRESNS                |
| **說明**      | 銀行在 Fed 的準備金餘額 |

### 7.3 H.8 原始報告

更細緻的銀行資產負債表數據：
https://www.federalreserve.gov/releases/h8/current/

---

## 8. API 使用限制

### 8.1 FRED API 限制

| 限制             | 值                   |
|------------------|----------------------|
| 請求頻率         | 120 requests/minute  |
| 每次請求最大筆數 | 100,000 observations |

### 8.2 最佳實踐

- 使用本地快取減少 API 請求
- 批量請求多個序列
- 避免在迴圈中重複請求相同數據
