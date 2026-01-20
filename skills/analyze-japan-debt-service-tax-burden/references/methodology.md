### 1. 計算 Interest/Tax Ratio

**定義**：
```
interest_tax_ratio = interest_payments / tax_revenue
```

**解讀**：
- 0.25 = 利息吃掉 1/4 稅收
- 0.333 = 利息吃掉 1/3 稅收
- 0.50 = 利息吃掉 1/2 稅收

### 2. 風險分級

| 區間      | 分級      | 含義                |
|-----------|-----------|---------------------|
| < 0.25    | 🟢 GREEN  | 財政彈性充足        |
| 0.25–0.40 | 🟡 YELLOW | 彈性開始下降        |
| 0.40–0.55 | 🟠 ORANGE | 政策空間明顯受限    |
| > 0.55    | 🔴 RED    | 接近敘事「2/3」區域 |

**閾值依據**：
- 0.25：一般財政健康標準
- 0.40：OECD 多數國家不超過此水平
- 0.55：接近歷史極端情況

## 壓力測試公式

### 利率衝擊映射

**核心公式**：
```
additional_interest = debt_stock × pass_through × delta_yield
```

其中：
- `debt_stock`：債務存量（日圓）
- `pass_through`：年度再定價/再融資比例
- `delta_yield`：殖利率上升幅度（小數，200bp = 0.02）

**範例**：
```
debt_stock = ¥1,200 兆
pass_through = 0.15（15%）
delta_yield = 0.02（200bp）

additional_interest = 1,200 × 0.15 × 0.02 = ¥3.6 兆
```

### 壓測後比率

```
stressed_ratio = (interest_payments + additional_interest) / (tax_revenue × (1 + tax_shock))
```

其中 `tax_shock` 為稅收衝擊（負數=下降）。

### 多年累積效應

Year 2 使用累積 pass_through：
```
cumulative_pass_through = pass_through_year1 + pass_through_year2
```

假設每年 15%，兩年累積 30% 存量債務被再定價。

## 殖利率統計分析

### Z-Score

```python
zscore = (latest - mean) / std
```

**解讀**：
- |Z| > 2.0：處於極端區域
- |Z| > 1.5：處於偏離區域

### 百分位數

```python
percentile = (series <= latest).mean()
```

**解讀**：
- > 0.95：近乎歷史最高
- > 0.80：處於高位區
- 0.20–0.80：中性區

## Pass-Through 估算

### 方法 1：平均到期年限

```
pass_through ≈ 1 / average_maturity
```

日本政府債務平均到期 ~8-9 年 → pass_through ~11-12%

### 方法 2：年度發債/到期數據

```
pass_through = (redemptions + new_issuance_at_new_rate) / debt_stock
```

若有實際發債計劃數據，此方法更精確。

### 預設假設

本 Skill 使用 15% 作為保守估計，涵蓋：
- 到期再融資 ~11%
- 新增發債 ~4%

## 敘事核對邏輯

### 「殖利率創 40 年新高」

核對方法：
1. 取 40 年歷史數據
2. 計算 percentile_rank
3. 若 > 0.99 且 latest > max(history[-40Y:]) → 敘事成立

### 「利息吃掉 1/3 稅收」

核對方法：
1. 確認口徑（哪種稅收？純利息還是國債費？）
2. 計算 interest_tax_ratio
3. 若 ≈ 0.333 且口徑對齊 → 敘事成立

### 「日本會拋售美債」

核對方法：
1. 確認日本持有美債規模（TIC）
2. 標示潛在通道與量級
3. **不做行為預測**：持有 ≠ 會拋售

## 局限性

1. **資料滯後**：財政數據通常有 1-2 年滯後
2. **口徑差異**：不同來源定義不同
3. **結構假設**：pass_through 是假設，非實際數據
4. **單一國家**：當前僅支援日本，跨國比較需調整
5. **非線性效應**：極端情況可能有非線性反應
