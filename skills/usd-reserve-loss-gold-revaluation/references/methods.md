# 方法論 (Methodology)

本文件詳細解釋「美元失去儲備地位下黃金重估」壓力測試模型的計算邏輯與理論基礎。

---

## 核心假設：黃金錨定情境

### 情境設定

本模型基於以下極端假設：

1. **法定貨幣體系瓦解**：美元或其他儲備貨幣失去其儲備地位
2. **黃金成為唯一錨**：各國需要用實物黃金來「支撐」其貨幣負債
3. **全額支撐要求**：貨幣負債需要完全由黃金價值覆蓋

### 這不是什麼

- **不是價格預測**：這是壓力測試，不是預測金價會漲到 $39k
- **不是機率模型**：不評估此情境發生的可能性
- **不是投資建議**：僅用於理解極端情境下的資產負債表壓力

### 來源與啟發

此模型受 VanEck 的黃金分析啟發：
> "If you divide central bank money liabilities by gold reserves..."
> — VanEck Gold Research

---

## 核心公式

### 1. 隱含金價（Implied Gold Price）

**未加權版本**：

```
implied_gold_price = money_base_usd / gold_oz
```

其中：
- `money_base_usd`：以美元計價的貨幣量（M0 或 M2）
- `gold_oz`：黃金儲備（金衡盎司）

**加權版本**：

```
implied_gold_price_weighted = (money_base_usd × weight) / gold_oz
```

其中 `weight` 來自 FX turnover 或 reserve share。

### 2. Headline 隱含金價（加權總計）

```
headline_implied_price = Σ(money_base_i × weight_i) / Σ(gold_oz_i)
```

這是「若全球體系重新錨定到黃金」的總隱含金價。

### 3. 黃金支撐率（Backing Ratio）

```
backing_ratio = (gold_oz × gold_spot) / money_base_usd
```

解讀：
- `backing_ratio = 1.0`：黃金完全支撐貨幣負債
- `backing_ratio = 0.03`：黃金僅支撐 3% 的貨幣負債

### 4. 槓桿倍數（Leverage Multiple）

```
lever_multiple = implied_gold_price_weighted / gold_spot
```

表示「金價需要漲多少倍才能完全支撐」。

### 5. 黃金缺口（Gold Gap）

若要達到 100% 支撐：

```
required_gold_oz = money_base_usd / gold_spot
additional_gold_oz = max(0, required_gold_oz - gold_oz)
```

若要達到目標支撐率 X：

```
required_gold_oz = (money_base_usd × X) / gold_spot
```

---

## 貨幣口徑選擇

### M0（Monetary Base / 貨幣基數）

**定義**：央行直接創造的貨幣
- 流通中現金（Currency in Circulation）
- 銀行準備金（Bank Reserves）

**使用場景**：
- 評估央行資產負債表的直接壓力
- VanEck "$39k gold" 論點使用此口徑

**優點**：
- 口徑相對明確
- 數據可得性高
- 代表「高能貨幣」

### M2（Broad Money / 廣義貨幣）

**定義**：包含銀行體系信用擴張
- M0
- 活期存款
- 定期存款
- 貨幣市場基金等

**使用場景**：
- 評估整體金融體系的極端壓力
- 「如果連銀行存款都要黃金支撐」的情境

**優點**：
- 更全面反映貨幣供給
- 捕捉信用擴張程度

### M0 vs M2 的關係

```
Credit Multiplier = M2 / M0
```

典型值：4-10 倍，代表銀行體系的信用擴張程度。

| 口徑 | 典型隱含金價 | 解讀 |
|------|-------------|------|
| M0 | ~$39k | 央行壓力 |
| M2 | ~$184k | 全體系壓力 |

---

## 加權方法

### FX Turnover 加權

**來源**：BIS Triennial Survey（每三年更新）

**直覺**：
- 外匯交易份額 ≈ 國際結算/儲備使用強度
- 份額越高，在「重新錨定」時需吸收的壓力越大

**數學**：
```
weight_i = fx_turnover_share_i / Σ(fx_turnover_share)
```

**優點**：
- 反映實際國際使用強度
- 捕捉貨幣的「結算功能」

**缺點**：
- 每三年才更新
- 雙邊計算導致總和 > 100%

### Reserve Share 加權

**來源**：IMF COFER（季度更新）

**直覺**：
- 官方外匯儲備中的幣別佔比
- 反映各國央行對不同貨幣的「信任度」

**數學**：
```
weight_i = reserve_share_i
```

**優點**：
- 季度更新，較新
- 直接反映官方偏好

**缺點**：
- 主要反映官方行為，非市場行為
- CNY 佔比可能低估實際使用

### Equal Weight（等權重）

**直覺**：不考慮貨幣重要性差異

**使用場景**：
- 簡單比較各國單獨的壓力
- 避免權重選擇的主觀性

### Custom Weight（自訂權重）

**使用場景**：
- 特定情境分析（如「只考慮 G7」）
- 研究假設檢驗

---

## 單位換算

### 黃金單位

| 單位 | 轉換 |
|------|------|
| 1 噸 (tonne) | = 32,150.7466 金衡盎司 (troy oz) |
| 1 金衡盎司 | = 31.1035 克 |
| 1 公斤 | = 32.1507 金衡盎司 |

```python
TONNE_TO_TROY_OZ = 32150.7466
gold_oz = gold_tonnes * TONNE_TO_TROY_OZ
```

### 貨幣換算

將本幣貨幣量轉為 USD：

```python
money_base_usd = money_local * fx_rate_to_usd
```

其中 `fx_rate_to_usd` 是「1 單位本幣 = ? USD」。

---

## 解讀指南

### Backing Ratio 解讀

| 範圍 | 解讀 | 典型國家 |
|------|------|----------|
| < 5% | 極度槓桿 | 日本 (~3%) |
| 5-15% | 高度槓桿 | 美國 (~8%), 英國 |
| 15-30% | 中度槓桿 | 歐元區 |
| 30-50% | 低度槓桿 | 瑞士 (~35%) |
| > 50% | 接近完全支撐 | 某些新興市場 |

### Lever Multiple 解讀

| 倍數 | 解讀 |
|------|------|
| < 1x | 黃金已「超額支撐」，隱含金價低於市價 |
| 1-5x | 低槓桿，金價小幅重估即可支撐 |
| 5-20x | 中高槓桿，需金價顯著重估 |
| > 20x | 極度槓桿，需金價大幅重估 |

### Headline Number 解讀

VanEck 的 "$39k gold"：
- 口徑：M0
- 權重：FX turnover
- 解讀：這是壓力測試，非預測

要達到這個數字：
- 需要極端情境（法定貨幣體系瓦解）
- 需要全球同時發生
- 需要黃金成為唯一被接受的價值儲存

---

## 模型限制

### 1. 數據口徑不一致

各國 M0/M2 定義略有差異：
- 美國 M0 = Monetary Base
- 日本 M0 = 日銀券發行額 + 準備預金
- 中國 M0 = 流通中現金（不含準備金）

**緩解**：使用 IMF IFS 數據可提高可比性，但更新較慢。

### 2. 黃金儲備數據不完整

- 某些國家不完全公開
- 可能包含未配置儲備（Allocated vs Unallocated）
- 租借 (leasing) 可能重複計算

### 3. 情境的極端性

- 假設「全球同時發生」不切實際
- 忽略漸進調整過程
- 忽略其他價值儲存（如加密貨幣）

### 4. 權重的時效性

- BIS 調查每三年更新
- FX 格局可能已變化（尤其 CNY）

---

## 進階分析

### 情境模擬

可以調整參數進行敏感度分析：

```python
# 情境 1: 只考慮 G7
entities = ["USD", "EUR", "JPY", "GBP", "CAD"]

# 情境 2: 加入新興市場
entities = ["USD", "EUR", "CNY", "INR", "BRL", "RUB"]

# 情境 3: 調整權重（假設 CNY 份額上升）
custom_weights = {"USD": 0.70, "EUR": 0.25, "CNY": 0.15, ...}
```

### 歷史回測

追蹤 backing ratio 的歷史變化：

```python
# 過去 20 年的 backing ratio 變化
# 識別趨勢：各國是在「去槓桿化」還是「加槓桿」
```

### 央行行為追蹤

關聯央行的黃金買賣行為：

```python
# 過去 10 年央行淨買入/賣出
# 與 backing ratio 變化的關係
```

---

## 參考文獻

1. VanEck Gold Research Reports
2. BIS Triennial Central Bank Survey (2022)
3. IMF Currency Composition of Official Foreign Exchange Reserves (COFER)
4. World Gold Council Gold Demand Trends
5. Central Bank Gold Agreements (CBGA)
