### 1. 財政陷阱理論
「人口-財政陷阱」建立在以下經濟學原理之上：

#### 1.1 債務動態方程式
標準政府債務動態：

```
d(t) = d(t-1) × (1 + r) / (1 + g) + pb(t)
```

簡化為：
```
Δd ≈ (r - g) × d + pb
```

其中：
- d = 債務/GDP 比率
- r = 名義利率（債務成本）
- g = 名義 GDP 成長率
- pb = 基本財政餘額/GDP（= 支出 - 收入 - 利息）

**核心洞察**：當 r > g 且 pb ≥ 0 時，債務比率將自動膨脹，形成「雪球效應」。

#### 1.2 老化的財政影響
人口老化透過兩個管道影響財政：

**支出端**：
- 養老金支出：與老年人口規模正相關
- 健康支出：老年人均醫療支出為年輕人的 3-5 倍
- 長照支出：隨 80+ 人口增加而急升

**收入端**：
- 勞動人口縮減 → 所得稅基萎縮
- 消費結構改變 → 消費稅稅基變化
- 企業投資下降 → 企業稅收減少

#### 1.3 金融抑制理論
Reinhart & Sbrancia (2015) 定義金融抑制為：
> 政府透過人為壓低利率、強制銀行持有國債、資本管制等手段，將債務成本轉嫁給儲蓄者。

當財政改革政治成本過高，金融抑制成為「最小阻力路徑」：
- 負實質利率侵蝕債務實質價值
- 對儲蓄者的隱性課稅
- 避免名義違約的政治代價

---

## 分析框架

### 2. 四支柱評分系統

本技能採用四維度評分架構，各支柱設計如下：

#### 2.1 老化壓力 (Aging Pressure)

**定義**：衡量人口老化對財政的壓力程度

**計算公式**：
```python
aging_level = old_age_dependency_ratio[end_year]  # 65+/15-64
aging_slope = linear_regression_slope(old_age_dependency[end_year-10:end_year])

aging_pressure = 0.5 × zscore(aging_level) + 0.5 × zscore(aging_slope)
```

**權重配置邏輯**：
- 水準 (50%)：當前老化程度決定即期財政壓力
- 斜率 (50%)：趨勢決定未來壓力演化速度

**資料來源**：
- 首選：World Bank WDI (SP.POP.DPND.OL)
- 次選：UN World Population Prospects

#### 2.2 債務動態 (Debt Dynamics)

**定義**：衡量政府債務的可持續性與演化趨勢

**計算公式**：
```python
debt_level = debt_to_gdp[end_year]
debt_slope = linear_regression_slope(debt_to_gdp[end_year-5:end_year])
r_minus_g = nominal_yield_10y[end_year] - nominal_gdp_growth[end_year]

debt_dynamics = (
    0.50 × zscore(debt_level) +
    0.30 × zscore(debt_slope) +
    0.20 × zscore(r_minus_g)
)
```

**權重配置邏輯**：
- 水準 (50%)：高債務水準本身即為風險
- 斜率 (30%)：上升趨勢顯示問題惡化中
- r-g (20%)：決定債務自動演化方向

**資料來源**：
- 債務：IMF WEO (GGXWDG_NGDP) 或 World Bank (GC.DOD.TOTL.GD.ZS)
- 利率：OECD (IRLT) 或各國央行
- 成長：World Bank (NY.GDP.MKTP.KD.ZG) + CPI 推算名義成長

#### 2.3 官僚膨脹 (Bloat Index)

**定義**：衡量政府支出的規模與效率

**計算公式**：
```python
gov_consumption = government_consumption_to_gdp[end_year]
gov_expenditure = government_expenditure_to_gdp[end_year]

bloat_index = 0.6 × zscore(gov_consumption) + 0.4 × zscore(gov_expenditure)
```

**權重配置邏輯**：
- 政府消費 (60%)：直接反映官僚體系規模
- 總支出 (40%)：包含移轉性支出的整體規模

**延伸指標**（若資料可用）：
- 公部門薪資佔 GDP 比例
- 公務員人數佔就業人口比例
- 政府採購效率指數

**資料來源**：
- World Bank WDI (NE.CON.GOVT.ZS, GC.XPN.TOTL.GD.ZS)
- IMF Government Finance Statistics

#### 2.4 成長拖累 (Growth Drag)

**定義**：低成長對財政可持續性的負面影響

**計算公式**：
```python
nominal_growth = nominal_gdp_growth[end_year]
growth_drag = zscore(-nominal_growth)  # 負向：低成長 = 高拖累
```

**邏輯**：
- 低成長 → r-g 缺口擴大 → 債務自動膨脹
- 低成長 → 稅基萎縮 → 財政收入下降
- 低成長 → 政治壓力 → 更難削減支出

---

### 3. Z-Score 標準化

#### 3.1 標準化公式
```python
zscore(x) = (x - μ) / σ
```

其中 μ 和 σ 為**跨國截面**統計量（非時間序列）。

#### 3.2 截面選擇
根據分析目的選擇截面群組：
- 全球比較：使用全部可用國家
- OECD 比較：僅使用 OECD 成員國
- 區域比較：使用特定區域國家

#### 3.3 解讀標準
| Z-Score    | 解讀         | 風險等級 |
|------------|--------------|----------|
| > 2.0      | 極端高於平均 | 紅燈     |
| 1.5 - 2.0  | 顯著高於平均 | 橙燈     |
| 0.5 - 1.5  | 略高於平均   | 黃燈     |
| -0.5 - 0.5 | 接近平均     | 綠燈     |
| < -0.5     | 低於平均     | 優良     |

---

### 4. 象限分類

#### 4.1 雙軸定義
- **X 軸**：Aging Pressure (z-score)
- **Y 軸**：Debt Dynamics (z-score)
- **閾值**：z = 1.0 作為高/低分界

#### 4.2 四象限意涵

| 象限 | 老化 | 債務 | 特徵                   | 典型國家      |
|------|------|------|------------------------|---------------|
| Q1   | 高   | 高   | 雙重壓力，政策空間極窄 | JPN, ITA, GRC |
| Q2   | 高   | 低   | 老化主導，債務尚有空間 | DEU, KOR      |
| Q3   | 低   | 高   | 債務主導，人口紅利尚存 | USA, BRA      |
| Q4   | 低   | 低   | 相對健康，政策空間寬廣 | IND, IDN      |

---

### 5. 通膨激勵指數

#### 5.1 理論基礎
當以下條件成立，政府有強烈動機選擇「通膨稀釋」路徑：
1. 債務水準高 → 稀釋效益大
2. r > g → 難以透過成長去槓桿
3. 支出剛性高 → 難以削減開支
4. 已有負實質利率歷史 → 路徑依賴

#### 5.2 計算公式
```python
inflation_incentive = (
    0.40 × zscore(debt_level) +
    0.20 × zscore(r_minus_g) +
    0.20 × zscore(neg_real_rate_share_5y) +
    0.20 × zscore(bloat_index)
)
```

#### 5.3 解讀
| 分數      | 政策傾向     | 投資意涵           |
|-----------|--------------|--------------------|
| < 0.5     | 正統財政     | 名義債券相對安全   |
| 0.5 - 1.5 | 溫和金融抑制 | 實質報酬承壓       |
| > 1.5     | 強烈稀釋動機 | 應持有通膨保值資產 |

---

## 參考文獻

1. Reinhart, C. M., & Sbrancia, M. B. (2015). "The Liquidation of Government Debt." *Economic Policy*, 30(82), 291-333.

2. Blanchard, O. (2019). "Public Debt and Low Interest Rates." *American Economic Review*, 109(4), 1197-1229.

3. IMF (2023). *Fiscal Monitor: Climate Crossroads*. International Monetary Fund.

4. OECD (2021). *Pensions at a Glance 2021*. OECD Publishing.

5. UN DESA (2022). *World Population Prospects 2022*. United Nations.
