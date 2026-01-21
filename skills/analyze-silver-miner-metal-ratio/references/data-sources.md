# 數據來源

## 1. 礦業股代理

### 1.1 ETF（建議）

| 代號 | 名稱                                 | 成立日期   | 特點                    |
|------|--------------------------------------|------------|-------------------------|
| SIL  | Global X Silver Miners ETF           | 2010-04-19 | 大型礦業股，較穩定      |
| SILJ | ETFMG Prime Junior Silver Miners ETF | 2012-11-28 | 小型/初級礦業股，高波動 |
| GDXJ | VanEck Junior Gold Miners ETF        | 2009-11-10 | 含部分銀礦股            |

**SIL 主要成分股（2025 年）：**
- Wheaton Precious Metals (WPM)
- Pan American Silver (PAAS)
- First Majestic Silver (AG)
- Hecla Mining (HL)
- Coeur Mining (CDE)

### 1.2 自建指數

若需自訂成分股，可使用以下股票建立等權/市值加權指數：

**主要白銀生產商：**
| 代號 | 名稱                  | 產量（Moz/年） |
|------|-----------------------|----------------|
| CDE  | Coeur Mining          | ~10            |
| HL   | Hecla Mining          | ~15            |
| AG   | First Majestic Silver | ~20            |
| PAAS | Pan American Silver   | ~22            |
| MAG  | MAG Silver            | 開發階段       |

**計算方式：**
```python
miners = ['CDE', 'HL', 'AG', 'PAAS']
px = yf.download(miners, start='2010-01-01', auto_adjust=True)['Close']
miner_index = px.mean(axis=1)  # 等權平均
```

### 1.3 數據獲取

使用 yfinance：

```python
import yfinance as yf

# ETF
sil = yf.download('SIL', start='2010-01-01', auto_adjust=True)['Close']

# 多檔股票
miners = yf.download(['CDE', 'HL', 'AG'], start='2010-01-01', auto_adjust=True)['Close']
```

---

## 2. 金屬代理

### 2.1 可用選項

| 代號     | 類型 | 來源    | 交易時間     | 特點             |
|----------|------|---------|--------------|------------------|
| SI=F     | 期貨 | COMEX   | 美股交易時間 | 直接反映現貨價   |
| XAGUSD=X | 現貨 | Yahoo   | 24 小時      | 可能有報價滯後   |
| SLV      | ETF  | iShares | 美股交易時間 | 含 ETF 溢價/折價 |

**建議優先順序：** SI=F > SLV > XAGUSD=X

### 2.2 數據獲取

```python
import yfinance as yf

# 期貨（建議）
silver = yf.download('SI=F', start='2010-01-01', auto_adjust=True)['Close']

# ETF（備用）
slv = yf.download('SLV', start='2010-01-01', auto_adjust=True)['Close']
```

### 2.3 期貨換月處理

SI=F 代表 COMEX 白銀期貨「近月合約」：
- 自動換月至下一個活躍合約
- 可能在換月時產生價格跳躍
- 長期趨勢分析影響不大

---

## 3. 數據對齊

### 3.1 交易日對齊

礦業股 ETF 與白銀期貨的交易日應相同：

```python
# 合併數據
px = pd.concat([miner_series, metal_series], axis=1, join='inner')
px.columns = ['miner', 'metal']
```

`join='inner'` 確保只保留兩者都有交易的日期。

### 3.2 頻率轉換

```python
# 轉為週頻（週五收盤）
if freq == '1wk':
    px = px.resample('W-FRI').last()

# 轉為月頻（月末）
elif freq == '1mo':
    px = px.resample('M').last()

# 刪除缺值
px = px.dropna()
```

### 3.3 缺值處理

| 情況             | 處理方式         |
|------------------|------------------|
| 單日缺值（假日） | 前值填補 (ffill) |
| 連續缺值（停牌） | 刪除該區間       |
| 數據起點不同     | 取較晚的起點     |

---

## 4. 數據品質

### 4.1 時間範圍

**建議最小範圍：** 10 年

| ETF  | 最早可用日期 | 建議起點   |
|------|--------------|------------|
| SIL  | 2010-04-19   | 2010-05-01 |
| SILJ | 2012-11-28   | 2013-01-01 |
| SI=F | 更早         | 2010-01-01 |

### 4.2 品質檢查

```python
# 檢查數據完整性
print(f"數據點數: {len(px)}")
print(f"缺值數量: {px.isna().sum()}")
print(f"時間範圍: {px.index.min()} 至 {px.index.max()}")

# 檢查異常值
print(f"最小值: {px.min()}")
print(f"最大值: {px.max()}")
```

**警告信號：**
- 缺值超過 5%
- 最小值為 0 或負值
- 最大值異常跳躍（可能是股票分割未調整）

---

## 5. 替代數據源

若 yfinance 不可用，考慮以下替代：

### 5.1 免費 API

| 數據源        | 優點          | 缺點       |
|---------------|---------------|------------|
| Alpha Vantage | 免費額度      | 需 API Key |
| Yahoo Finance | yfinance 底層 | 可能有限流 |

### 5.2 付費數據

| 數據源        | 優點       | 缺點 |
|---------------|------------|------|
| Quandl/Nasdaq | 機構級品質 | 付費 |
| Bloomberg     | 專業終端   | 昂貴 |

### 5.3 爬蟲方案

若需從網站抓取：
- 設計原則見 `thoughts/shared/guide/design-human-like-crawler.md`
- MacroMicro 爬蟲見 `thoughts/shared/guide/macromicro-highcharts-crawler.md`

---

## 6. 數據更新頻率

| 用途     | 建議更新頻率 |
|----------|--------------|
| 長期研究 | 每月         |
| 中期監控 | 每週         |
| 短期交易 | 每日         |

本 skill 建議使用週頻數據，每週末更新一次。
