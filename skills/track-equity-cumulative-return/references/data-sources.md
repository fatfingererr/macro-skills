# 數據來源說明

本文檔說明累積報酬率追蹤技能使用的數據來源。

---

## 1. Yahoo Finance

### 概述

| 項目     | 說明                           |
|----------|--------------------------------|
| 來源     | Yahoo Finance                  |
| API      | yfinance Python 套件           |
| 費用     | 免費                           |
| 限制     | 有速率限制，高頻請求可能被擋   |

### 官方連結

- 網站：https://finance.yahoo.com
- 套件：https://pypi.org/project/yfinance/

### 數據類型

| 欄位          | 說明                     |
|---------------|--------------------------|
| Open          | 開盤價                   |
| High          | 最高價                   |
| Low           | 最低價                   |
| Close         | 收盤價                   |
| Adj Close     | 調整後收盤價（已調整分割）|
| Volume        | 成交量                   |

### 本技能使用

- 使用 `Close`（收盤價）計算報酬率
- Yahoo Finance 的 Close 已經過股票分割調整

---

## 2. 支援的標的類型

### 個股

```
NVDA    NVIDIA
AMD     AMD
AAPL    Apple
GOOGL   Google
MSFT    Microsoft
TSLA    Tesla
META    Meta
AMZN    Amazon
```

### 指數

```
^GSPC   S&P 500
^NDX    Nasdaq 100
^IXIC   Nasdaq Composite
^DJI    Dow Jones Industrial
^SOX    Philadelphia Semiconductor
```

### ADR

```
TSM     台積電 ADR
ASML    ASML ADR
```

---

## 3. 快取機制

### 設計

為減少 API 請求，實作本地快取：

| 參數           | 設定              |
|----------------|-------------------|
| 快取目錄       | scripts/cache/    |
| 快取格式       | Parquet           |
| 有效期         | 12 小時           |

### 快取邏輯

1. 檢查是否有快取檔案
2. 檢查快取是否在有效期內
3. 若有效則使用快取，否則重新抓取
4. 抓取後更新快取

### 清除快取

```bash
python fetch_price_data.py --clear-cache
```

---

## 4. 數據品質

### 已知問題

| 問題           | 說明                               | 處理方式           |
|----------------|------------------------------------|--------------------|
| 缺值           | 部分日期可能無數據                 | dropna() 對齊      |
| 延遲           | 收盤價可能有 15 分鐘延遲           | 接受，非即時用途   |
| 分割           | 已調整，無需額外處理               | -                  |
| 股息           | **未**計入                         | 註明為價格報酬     |

### 數據驗證

建議與其他來源交叉驗證：

- Google Finance
- Bloomberg Terminal
- 券商平台

---

## 5. API 限制

### Yahoo Finance 限制

- 無明確公開的 rate limit
- 高頻請求可能被暫時封鎖
- 建議使用快取減少請求

### 最佳實踐

1. 使用快取（預設開啟）
2. 避免過於頻繁的請求
3. 批次抓取時加入延遲
4. 處理 API 錯誤並重試

---

## 6. 替代數據來源

若 Yahoo Finance 不可用，可考慮：

| 來源            | 特點                           | 費用    |
|-----------------|--------------------------------|---------|
| Alpha Vantage   | 需要 API key，有免費額度       | 免費/付費|
| IEX Cloud       | 可靠，但免費額度有限           | 免費/付費|
| Polygon.io      | 專業級數據，需付費             | 付費    |
| FRED            | 僅限總經數據                   | 免費    |

目前本技能僅支援 Yahoo Finance。
