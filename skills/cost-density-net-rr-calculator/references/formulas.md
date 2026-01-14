# Cost Density Model: Complete Formula Reference

<notation>
**符號定義**

| 符號 | 名稱 | 定義 | 單位 |
|------|------|------|------|
| R | Fixed Risk | 每筆交易的固定風險金額 | 帳戶貨幣 (USD) |
| RR_g | Gross Risk-Reward | 毛風險報酬比 = Target / Stop | 無單位 |
| P | Stop-Loss Size | 停損大小 | pips 或 points |
| V | Pip Value | 每 pip 每手的價值 | 帳戶貨幣/pip |
| c | Commission | 來回佣金（每手） | 帳戶貨幣 |
| s | Spread | 來回點差 | pips 或 points |
| x | Load Coefficient | 負載係數 | 無單位 |
</notation>

<core_formulas>
**1. 部位規模（固定風險框架）**

```
Lot = R / (P × V)
```

推導：若風險 R 固定，停損 P pips，每 pip 價值 V，則：
- 最大損失 = Lot × P × V = R
- 因此 Lot = R / (P × V)

**2. 總交易成本**

```
C_total(P) = Lot × (c + s × V)
           = (R / (P × V)) × (c + s × V)
           = R × (c/V + s) / P
           = R × CostDensity / P
```

其中 **Cost Density = (c/V + s)** 是成本密度（pips 等效）。

關鍵洞察：成本與 P 成反比（雙曲線關係）。

**3. 淨風險報酬比**

```
實際利潤 = Lot × RR_g × P × V - C_total
         = R × RR_g - R × CostDensity / P

實際風險 = R + C_total
         = R × (1 + CostDensity / P)

RR_net = 實際利潤 / 實際風險
       = (R × RR_g - R × CostDensity / P) / (R × (1 + CostDensity / P))
       = (RR_g - CostDensity / P) / (1 + CostDensity / P)
```

令 **x = CostDensity / P**，得到正規形式：

```
RR_net = (RR_g - x) / (1 + x)
```

**重要性質：RR_net 與 R 無關**（R 在推導中被消去）。

**4. 負載係數 x**

```
x = CostDensity / P = (c/V + s) / P
```

x 的物理意義：成本佔停損的比例。

極限行為：
- P → ∞：x → 0，RR_net → RR_g
- P → 0：x → ∞，RR_net → -1

**5. 效率損失**

```
Loss_RR = 1 - (RR_net / RR_g)
        = (RR_g - RR_net) / RR_g
        = x × (RR_g + 1) / (RR_g × (1 + x))
```

一階導數分析表明：Loss_RR 對 x 的增長是加速的。

**6. 最低勝率（打平）**

期望值 E = WR × Win - (1-WR) × Loss = 0

在成本調整後：
- Win = RR_net × Risk
- Loss = Risk

解得：
```
WR_min = 1 / (1 + RR_net)
       = 1 / (1 + (RR_g - x)/(1 + x))
       = (1 + x) / (1 + RR_g)
```

WR_min 隨 x 線性增長。

**7. 臨界停損（效率減半點）**

設 RR_net = 0.5 × RR_g，求 P_critical：

```
(RR_g - x) / (1 + x) = 0.5 × RR_g
RR_g - x = 0.5 × RR_g × (1 + x)
RR_g - x = 0.5 × RR_g + 0.5 × RR_g × x
0.5 × RR_g = x × (1 + 0.5 × RR_g)
x = 0.5 × RR_g / (1 + 0.5 × RR_g)
x = RR_g / (2 + RR_g)
```

由 x = CostDensity / P：
```
P_critical = CostDensity / x
           = CostDensity × (2 + RR_g) / RR_g
           = CostDensity × (RR_g + 2) / RR_g
```
</core_formulas>

<invariance_proof>
**R 無關性證明**

定理：RR_net 不依賴固定風險 R。

證明：
1. 設任意 R > 0
2. Lot = R / (P × V)
3. C_total = Lot × (c + s × V) = R × (c/V + s) / P
4. 實際利潤 = Lot × RR_g × P × V - C_total = R × RR_g - R × x
5. 實際風險 = R + C_total = R × (1 + x)
6. RR_net = R × (RR_g - x) / (R × (1 + x)) = (RR_g - x) / (1 + x)

R 在最後一步被完全消去。QED

物理意義：效率衰減是結構性的，與資金規模無關。
</invariance_proof>

<limit_behavior>
**極限行為分析**

**Case 1: P → ∞ (大停損)**
```
x = CostDensity / P → 0
RR_net = (RR_g - 0) / (1 + 0) = RR_g
WR_min = (1 + 0) / (1 + RR_g) = 1 / (1 + RR_g)
```
成本影響趨近於零。

**Case 2: P → 0+ (極小停損)**
```
x = CostDensity / P → ∞
RR_net = (RR_g - ∞) / (1 + ∞) → -1
WR_min = (1 + ∞) / (1 + RR_g) → ∞
```
策略變為必輸。

**Case 3: P = CostDensity (停損等於成本)**
```
x = 1
RR_net = (RR_g - 1) / 2
```
若 RR_g = 3，則 RR_net = 1（損失 67%）。

**Case 4: P = RR_g × CostDensity (停損等於成本×毛RR)**
```
x = 1 / RR_g
RR_net = (RR_g - 1/RR_g) / (1 + 1/RR_g)
       = (RR_g² - 1) / (RR_g + 1)
       = RR_g - 1
```
若 RR_g = 3，則 RR_net = 2（損失 33%）。
</limit_behavior>

<numerical_example>
**XAU/USD 計算範例**

參數：
- RR_g = 3.0
- c = $7.00 (round-turn commission)
- s = 1.5 pips (spread)
- V = $10/pip (standard lot)

Step 1: Cost Density
```
CostDensity = c/V + s = 7/10 + 1.5 = 0.7 + 1.5 = 2.2 pips
```

Step 2: P_critical
```
P_critical = 2.2 × (3 + 2) / 3 = 2.2 × 5/3 = 3.67 pips
```

Step 3: 不同 P 值的結果

| P (pips) | x     | RR_net | Loss_RR | WR_min |
|----------|-------|--------|---------|--------|
| 5        | 0.440 | 1.78   | 40.8%   | 36.0%  |
| 10       | 0.220 | 2.28   | 24.1%   | 30.5%  |
| 20       | 0.110 | 2.60   | 13.3%   | 27.7%  |
| 50       | 0.044 | 2.83   | 5.6%    | 26.1%  |
| 100      | 0.022 | 2.92   | 2.9%    | 25.6%  |

觀察：
- 停損從 20 降至 5 pips（縮小 75%），效率損失從 13% 增至 41%（增加 3 倍）
- P = 5 時勝率需求 36%，P = 20 時僅需 27.7%
</numerical_example>
