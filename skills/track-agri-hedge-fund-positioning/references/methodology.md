CFTC Commitments of Traders (COT) 報告是追蹤期貨市場部位的官方資料：

| 報告類型      | 分類                                         | 可用期間 |
|---------------|----------------------------------------------|----------|
| Legacy        | Commercial / Non-Commercial / Non-Reportable | 1986-    |
| Disaggregated | Producer, Swap Dealer, Managed Money, Other  | 2009-    |
| TFF           | Dealer, Asset Manager, Leveraged, Other      | 2010-    |

**本技能預設使用 Legacy 報告的 Non-Commercial（非商業）部位**，因為：
- 歷史最長，可用於長期回測
- 非商業部位主要代表投機資金（對沖基金、CTA）
- 是市場情緒的經典代理指標

### 1.2 資金流定義

```
淨部位 = Long - Short
資金流 = 本週淨部位 - 上週淨部位
```

單位：合約口數（contracts）

**注意**：不同商品的合約規格不同，跨商品比較時需標準化。

### 1.3 分組彙總邏輯

將個別商品依特性分組：

| 群組     | 商品                                  | 典型合約  |
|----------|---------------------------------------|-----------|
| Grains   | Corn, Wheat (CBOT/KC/MGE), Rice, Oats | 5000 bu   |
| Oilseeds | Soybeans, Soybean Oil, Soybean Meal   | 5000 bu   |
| Meats    | Live Cattle, Lean Hogs, Feeder Cattle | 40000 lbs |
| Softs    | Coffee, Sugar #11, Cocoa, Cotton #2   | 各異      |

**Total Flow = Grains + Oilseeds + Meats + Softs**

---

## 2. 火力（Buying Firepower）量化

### 2.1 定義

火力衡量「基金還有多少加碼空間」：

```python
def calculate_firepower(net_pos_series, lookback_weeks=156):
    """
    firepower = 1 - percentile_rank(current_net_pos)

    - 高火力（>0.6）：部位處於歷史低檔，仍有大量買進空間
    - 低火力（<0.3）：部位已接近歷史高檔，擁擠風險高
    """
    historical = net_pos_series.iloc[-lookback_weeks:]
    current = net_pos_series.iloc[-1]
    percentile = (historical <= current).mean()
    return 1 - percentile
```

### 2.2 視窗選擇

| lookback_weeks | 意義               | 適用場景           |
|----------------|--------------------|--------------------|
| 52             | 1 年，短期循環     | 戰術性交易         |
| 104            | 2 年，中期循環     | 波段交易           |
| 156            | 3 年，完整景氣循環 | 策略性配置（預設） |
| 260            | 5 年，跨多個循環   | 長期歷史比較       |

### 2.3 替代計算方法

**距離上緣法**：
```python
p90 = net_pos_series.quantile(0.9)
firepower = (p90 - current) / abs(p90)
```

**風險容量法**（需 Open Interest）：
```python
net_pos_ratio = net_pos / open_interest
# 用 ratio 取代絕對部位做分位數
```

---

## 3. 宏觀順風評分

### 3.1 指標選擇

| 指標       | 代理序列         | 訊號解讀            |
|------------|------------------|---------------------|
| 美元 (USD) | DXY / DTWEXBGS   | 走弱 = 利於商品     |
| 原油 (Oil) | WTI / CL=F       | 走強 = 風險偏好上升 |
| 金屬       | XME / GDX / COPX | 走強 = 循環需求樂觀 |

### 3.2 計算方式

```python
def calculate_macro_tailwind(macro_df, lookback_days=5):
    """
    計算宏觀順風分數

    macro_tailwind_score = (USD弱 + Oil強 + Metals強) / 3
    """
    recent = macro_df.iloc[-lookback_days:]

    usd_ret = recent['dxy'].pct_change().sum()
    oil_ret = recent['wti'].pct_change().sum()
    metals_ret = recent['metals'].pct_change().sum()

    flags = [
        usd_ret < 0,      # USD 走弱
        oil_ret > 0,      # Oil 走強
        metals_ret > 0    # Metals 走強
    ]

    return sum(flags) / len(flags)
```

### 3.3 解讀

| macro_tailwind_score | 意義   | 對農產品含義         |
|----------------------|--------|----------------------|
| 0.67 - 1.00          | 強順風 | 風險偏好高，利於商品 |
| 0.33 - 0.66          | 中性   | 方向不明確           |
| 0.00 - 0.33          | 逆風   | 風險規避，壓抑商品   |

---

## 4. 週中回補驗證框架

### 4.1 問題背景

COT 資料截止到週二收盤，但新聞敘事常提到「週三到週五基金買回」。這段期間只能用代理證據驗證：

### 4.2 代理證據

| 證據類型 | 資料來源          | 驗證邏輯                    |
|----------|-------------------|-----------------------------|
| 價格動能 | 農產品 ETF（DBA） | Wed-Fri 累積報酬 > 0        |
| 成交量   | 期貨成交量        | 高於 20 日均量 = 有資金參與 |
| 未平倉量 | Open Interest     | OI 擴張 = 新倉（非純換手）  |
| 宏觀共振 | DXY, WTI, XME     | 與 USD↓、Oil↑、Metals↑ 同向 |

### 4.3 驗證流程

```
Step 1: COT 週（到週二）是否淨賣？
        └─ flow_week < 0 或 net_pos 下滑

Step 2: 週三～週五是否出現回補跡象？
        ├─ 農產品價格 Wed-Fri 報酬 > 0
        ├─ 成交量 > 20日均量
        └─ 宏觀指標共振 >= 2/3

Step 3: 綜合判斷
        └─ 若 Step 1 + Step 2 皆成立 → 支持「賣出後買回」敘事
```

---

## 5. 訊號生成規則

### 5.1 Signal 1: Funds Back & Buying

**觸發條件**：
- `total_flow_week` 由負轉正，或正向加速
- 主要子群組（穀物/油籽）同步轉正
- `firepower_total` > 0.5

### 5.2 Signal 2: Macro Tailwind Bullish

**觸發條件**：
- `macro_tailwind_score` >= 0.67
- 與資金流入同向

### 5.3 Signal 3: Fundamental Trigger

**觸發條件**：
- 當週有 USDA 報告發布
- 報告內容與流量方向一致
- 例：出口銷售超預期 + 穀物流入

### 5.4 Signal 4: Crowded Risk

**觸發條件**：
- `firepower_total` < 0.2
- 部位接近歷史極端
- 警告：擁擠風險高，可能反轉

---

## 6. 圖表標註規則對照

將圖表上的敘事標註轉為可重複的規則：

| 標註                | 觸發條件                                       |
|---------------------|------------------------------------------------|
| Strong Corn Demand  | corn_export_surprise > 0 AND grains_flow > 0   |
| Bearish USDA Stats  | wasde_surprise < 0 AND grains_flow < 0         |
| Small Holiday Flows | abs(total_flow) < p25_historical               |
| Macro Mood Bullish  | macro_tailwind_score >= 0.67                   |
| Fund Capitulation   | total_flow < p5_historical AND firepower > 0.8 |

---

## 7. 限制與注意事項

1. **COT 延遲**：資料到週二，週三～週五需用代理
2. **合約規格**：跨商品比較需標準化
3. **報告修正**：CFTC 可能修正歷史資料
4. **假日效應**：假日週流量偏低，不宜過度解讀
5. **結構變化**：Managed Money 興起後，Non-Commercial 含義略有變化
