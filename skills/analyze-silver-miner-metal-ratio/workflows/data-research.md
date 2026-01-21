# Workflow: 數據源研究

<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 數據來源詳細說明
</required_reading>

<process>

## Step 1: 理解數據需求

本 skill 需要兩類數據：

| 數據類型 | 用途                   | 預設代理    |
|----------|------------------------|-------------|
| 礦業價格 | 白銀礦業板塊的價格代表 | SIL (ETF)   |
| 金屬價格 | 白銀本體的價格代表     | SI=F (期貨) |

**關鍵要求：**
- 兩者的交易日需可對齊
- 建議使用相同的數據來源（如都用 yfinance）
- 頻率可選日/週/月

## Step 2: 礦業代理選擇

### 主要選項：ETF

| ETF  | 名稱                                 | 特點                   |
|------|--------------------------------------|------------------------|
| SIL  | Global X Silver Miners ETF           | 大型白銀礦業，較穩定   |
| SILJ | ETFMG Prime Junior Silver Miners ETF | 小型/初級礦業，波動大  |
| GDXJ | VanEck Junior Gold Miners ETF        | 含部分白銀礦業，較混合 |

**建議：** 使用 SIL 作為主要代理，SILJ 作為槓桿/投機參考。

### 替代選項：自建指數

若 ETF 不符合需求，可自建等權礦業指數：

```python
miners = ['CDE', 'HL', 'AG', 'PAAS', 'MAG']  # 主要白銀生產商
weights = [0.2] * 5  # 等權

# 使用 yfinance 抓取
px = yf.download(miners, start=start_date, auto_adjust=True)['Close']
miner_index = (px * weights).sum(axis=1)
```

**注意：** 自建指數需處理缺值、除權除息、成分股變動。

## Step 3: 金屬代理選擇

### 主要選項

| 代號     | 類型 | 來源    | 特點             |
|----------|------|---------|------------------|
| SI=F     | 期貨 | COMEX   | 直接反映現貨價   |
| XAGUSD=X | 現貨 | Yahoo   | 24 小時交易      |
| SLV      | ETF  | iShares | 含 ETF 溢價/折價 |

**建議：** 優先使用 SI=F，若交易日對齊困難則使用 SLV。

### 數據獲取

使用 yfinance：

```python
import yfinance as yf

# 期貨
silver = yf.download('SI=F', start='2010-01-01', auto_adjust=True)['Close']

# ETF
silver_etf = yf.download('SLV', start='2010-01-01', auto_adjust=True)['Close']
```

## Step 4: 數據對齊處理

### 頻率轉換

```python
# 轉為週頻（週五收盤）
if freq == '1wk':
    px = px.resample('W-FRI').last()

# 轉為月頻
elif freq == '1mo':
    px = px.resample('M').last()
```

### 缺值處理

```python
# 對齊交易日
px = px.dropna(how='all')

# 前值填補（適用於假日缺值）
px = px.ffill()
```

### 常見問題

| 問題                 | 解決方案              |
|----------------------|-----------------------|
| 期貨假日無交易       | 使用前值填補 (ffill)  |
| ETF 與期貨交易日不同 | 取交集日期            |
| 股票分割/配息        | 使用 auto_adjust=True |

## Step 5: 數據品質檢查

執行以下檢查：

```python
# 檢查時間範圍
print(f"數據起點: {px.index.min()}")
print(f"數據終點: {px.index.max()}")

# 檢查缺值
print(f"缺值數量: {px.isna().sum()}")

# 檢查異常值
print(f"最小值: {px.min()}")
print(f"最大值: {px.max()}")
```

**警告信號：**
- 缺值超過 5% → 考慮換數據源
- 最小值為 0 或負值 → 數據品質問題
- 時間範圍不足 10 年 → 歷史類比可能不足

## Step 6: 替代數據源

若 yfinance 不可用或品質不佳，考慮以下替代：

| 數據源        | 類型 | 適用場景     |
|---------------|------|--------------|
| Alpha Vantage | API  | 需要 API Key |
| Quandl/Nasdaq | 付費 | 機構級數據   |
| MacroMicro    | 爬蟲 | 含衍生指標   |
| TradingView   | 手動 | 圖表匯出     |

**爬蟲參考：**
- 設計原則見 `thoughts/shared/guide/design-human-like-crawler.md`
- MacroMicro 爬蟲見 `thoughts/shared/guide/macromicro-highcharts-crawler.md`

</process>

<success_criteria>
數據研究完成時應確認：

- [ ] 礦業代理選定（ETF 或自建指數）
- [ ] 金屬代理選定（期貨或 ETF）
- [ ] 數據可通過 yfinance 獲取
- [ ] 交易日可對齊
- [ ] 缺值處理策略確定
- [ ] 時間範圍足夠（建議 ≥10 年）
- [ ] 品質檢查通過
</success_criteria>
