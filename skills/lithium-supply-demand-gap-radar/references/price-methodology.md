# 鋰價格數據方法學參考

理解價格報價的方法學對於正確使用價格數據至關重要。本文件整理主要價格來源的方法學要點。

---

## Fastmarkets 方法學

### 報價概述

Fastmarkets 是鋰價格報價的主要國際來源，其報價被 CME 期貨合約作為結算基準。

**方法學文件**
- URL: https://www.fastmarkets.com/methodology

### 主要報價規格

#### Lithium Carbonate (碳酸鋰)

| 報價名稱 | 規格 | 頻率 |
|----------|------|------|
| Lithium carbonate 99.5% Li2CO3 min, battery grade | CIF China, Japan, Korea | Weekly (Thursday) |
| Lithium carbonate 99% Li2CO3 min, technical/industrial grade | CIF China, Japan, Korea | Weekly |

**規格說明**
- 純度: ≥99.5% Li₂CO₃（電池級）
- 交貨條件: CIF（含運保費）
- 地點: 中國、日本、韓國港口
- 包裝: 噸袋或 25kg 袋

#### Lithium Hydroxide (氫氧化鋰)

| 報價名稱 | 規格 | 頻率 |
|----------|------|------|
| Lithium hydroxide monohydrate 56.5% LiOH.H2O min, battery grade | CIF China, Japan, Korea | Weekly (Thursday) |

**規格說明**
- 純度: ≥56.5% LiOH·H₂O
- 顆粒大小: 通常有規格要求
- 雜質限制: 特定元素含量上限

#### Spodumene Concentrate (鋰輝石精礦)

| 報價名稱 | 規格 | 頻率 |
|----------|------|------|
| Spodumene concentrate 6% Li2O min | FOB Australia | Weekly |

**規格說明**
- Li₂O 含量: ≥6%
- 水分: 通常 <8%
- 鐵含量: 有上限要求

### 報價計算方法

1. **數據收集**
   - 向生產商、貿易商、消費者收集成交/報價
   - 最少需要一定數量的數據點

2. **價格計算**
   - 使用加權平均或區間報價
   - 排除異常值
   - 考慮交貨時間調整

3. **發布**
   - 週四倫敦時間發布
   - 包含高、低、中間價

### 使用注意

- **時滯**: 報價反映過去一週的成交，非即時
- **樣本**: 可能無法覆蓋所有交易
- **規格**: 實際交易可能有規格差異，需調整

---

## SMM (上海有色網) 方法學

### 報價概述

SMM 是中國最大的金屬價格資訊平台，其碳酸鋰指數是中國市場的主要參考。

**方法學文件**
- 可在 SMM 網站查看指數計算說明

### 主要報價

| 報價名稱 | 規格 | 頻率 |
|----------|------|------|
| 電池級碳酸鋰 | ≥99.5% | 每日 |
| 工業級碳酸鋰 | ≥99.2% | 每日 |
| 電池級氫氧化鋰 | ≥56.5% | 每日 |
| 電池級碳酸鋰（微粉） | ≥99.5%, D50<10μm | 每日 |

### 報價計算方法

1. **數據收集**
   - 向國內主要生產商、貿易商收集報價
   - 電話/線上訪談

2. **指數計算**
   - 加權平均
   - 權重基於樣本企業市場份額

3. **發布**
   - 每日發布（工作日）
   - 人民幣/噸

### 中國 vs 國際價格差異

| 因素 | 說明 |
|------|------|
| 匯率 | CNY/USD 匯率波動 |
| 運費 | 國際運輸成本 |
| 品質 | 規格可能略有差異 |
| 供需 | 區域供需可能不同步 |
| 關稅 | 進出口關稅影響 |

**典型價差**: 中國價格通常低於國際價格 5-15%，但可能反轉

---

## CME 鋰期貨

### 合約規格

| 項目 | 說明 |
|------|------|
| 合約代碼 | LIH (氫氧化鋰) |
| 合約大小 | 1 metric ton |
| 報價單位 | USD / kilogram |
| 最小變動 | 0.001 USD/kg |
| 結算方式 | 現金結算 |
| 結算價基準 | Fastmarkets Lithium Hydroxide CIF CJK |

### 合約月份
- 連續 12 個月

### 交易時間
- 芝加哥時間: Sunday - Friday, 5:00 PM - 4:00 PM CT

### 使用作為價格 Proxy

**優點**:
- 可交易、可獲取
- 反映市場預期
- 有流動性數據

**缺點**:
- 流動性可能較低
- 期貨 vs 現貨價差
- 僅限氫氧化鋰

**價差調整**:
```python
# 期貨 → 現貨估計
spot_estimate = futures_price * (1 + basis_adjustment)

# basis_adjustment 通常在 -5% 到 +5% 之間
# 取決於市場狀態（contango/backwardation）
```

---

## 價格 Proxy 方法

當付費價格數據不可得時，可使用以下 proxy：

### 1. 鋰礦股籃子 Proxy

```python
def compute_lithium_stock_proxy(weights=None):
    """
    使用鋰相關股票建立價格 proxy
    """
    if weights is None:
        weights = {
            "ALB": 0.30,   # Albemarle
            "SQM": 0.25,   # SQM
            "LTHM": 0.20,  # Livent/Arcadium
            "LAC": 0.15,   # Lithium Americas
            "PLS.AX": 0.10 # Pilbara Minerals
        }

    # 載入股價
    prices = load_stock_prices(list(weights.keys()))

    # 計算加權指數
    proxy_index = sum(prices[ticker] * weight for ticker, weight in weights.items())

    return normalize_to_base_100(proxy_index)
```

**相關性驗證**:
- 與 Fastmarkets 碳酸鋰價格相關性通常 > 0.7
- 需定期重新校準權重

### 2. ETF Price Proxy

```python
def lit_etf_as_proxy():
    """
    使用 LIT ETF 價格作為鋰市場情緒 proxy
    """
    lit_price = load_price("LIT")

    # 注意：ETF 價格受多因素影響
    # 僅作為方向性指標，非絕對價格

    return lit_price
```

### 3. Spodumene → LCE 推算

```python
def implied_lce_from_spodumene(sc6_price):
    """
    從鋰輝石價格推算碳酸鋰價格
    """
    # 加工成本假設（USD/t LCE）
    conversion_cost = 3000  # 視市場狀況調整

    # 轉換係數
    sc6_to_lce_ratio = 7.0  # 約 7 噸 SC6 → 1 噸 LCE

    implied_lce = sc6_price * sc6_to_lce_ratio + conversion_cost

    return implied_lce
```

---

## 價格數據品質評估

### 評估維度

| 維度 | 說明 | 權重 |
|------|------|------|
| 時效性 | 數據更新頻率 | 25% |
| 覆蓋度 | 市場交易覆蓋比例 | 25% |
| 規格一致性 | 報價規格是否標準化 | 20% |
| 來源可靠性 | 數據收集方法是否透明 | 20% |
| 歷史深度 | 歷史數據長度 | 10% |

### 來源評分

| 來源 | 時效性 | 覆蓋度 | 規格 | 可靠性 | 歷史 | 總分 |
|------|--------|--------|------|--------|------|------|
| Fastmarkets | 5 | 4 | 5 | 5 | 4 | 4.6 |
| SMM | 5 | 5 | 4 | 4 | 4 | 4.5 |
| CME Futures | 5 | 2 | 5 | 5 | 2 | 3.6 |
| Stock Proxy | 5 | 3 | 2 | 3 | 5 | 3.5 |

---

## 價格分析最佳實踐

### 1. 標註數據來源

```python
price_data = {
    "value": 15000,
    "unit": "USD/t",
    "source": "Fastmarkets",
    "spec": "Lithium carbonate 99.5% battery grade CIF CJK",
    "asof_date": "2026-01-16",
    "data_level": "paid"
}
```

### 2. 多來源交叉驗證

```python
def validate_price(fastmarkets_price, smm_price, exchange_rate):
    """
    交叉驗證價格合理性
    """
    smm_usd = smm_price / exchange_rate

    diff_pct = abs(fastmarkets_price - smm_usd) / fastmarkets_price * 100

    if diff_pct > 20:
        return {"status": "warning", "message": f"價差異常: {diff_pct:.1f}%"}

    return {"status": "ok", "price_consensus": (fastmarkets_price + smm_usd) / 2}
```

### 3. 處理缺失數據

```python
def fill_missing_price(price_series, method="ffill"):
    """
    填補缺失價格
    """
    if method == "ffill":
        return price_series.ffill()  # 向前填充
    elif method == "linear":
        return price_series.interpolate()  # 線性插值
    else:
        return price_series
```
