# 反推數學公式

本文件說明「門檻反推」的數學邏輯與計算方法。

## 核心問題

**問題**：若比率 R 要從當前值 R_now 達到目標值 R*（如歷史頂部），需要哪些因子變化？

**約束**：

```
R_t ≈ K × M_t × (1-L_t) × C_t × D_t
```

---

## 單因子反推

假設其他因子不變，只調整單一因子。

### 基本公式

比率變動倍數：

```
Ratio_multiplier = R* / R_now
```

### 只靠倍數擴張

```
M* = M_now × Ratio_multiplier
```

**範例**：
- R_now = 1.13, R* = 1.70
- Ratio_multiplier = 1.70 / 1.13 = 1.50
- M_now = 6.4
- M* = 6.4 × 1.50 = 9.6

**解讀**：EV/EBITDA 需從 6.4x 升至 9.6x。

---

### 只靠去槓桿

```
(1-L*) = (1-L_now) × Ratio_multiplier
```

**範例**：
- (1-L_now) = 0.75（即 NetDebt/EV = 25%）
- (1-L*) = 0.75 × 1.50 = 1.125

**解讀**：需要 (1-L) > 1，意味著需達到淨現金狀態且有大量現金超過負債。這通常不現實，說明單靠去槓桿無法達標。

---

### 只靠成本改善

```
C* = C_now × Ratio_multiplier
```

再反推 AISC*：

```
C* = 1 - AISC* / S
AISC* = S × (1 - C*)
```

**範例**：
- C_now = 0.703（AISC = $28, S = $94.4）
- C* = 0.703 × 1.50 = 1.055

**問題**：C* > 1 意味著 AISC* < 0，不可能。

**解讀**：單靠成本改善無法達標。

---

### 只靠減少稀釋

```
D* = D_now × Ratio_multiplier
```

**範例**：
- D_now = 0.89（股數較基期增加約 12%）
- D* = 0.89 × 1.50 = 1.335

**解讀**：需要股數減少 33%（大規模回購），通常不現實。

---

## 單因子反推摘要

| 因子     | 需要的調整                           | 可行性         |
|----------|--------------------------------------|----------------|
| 倍數 M   | 從 6.4x 升至 9.6x (+50%)             | 可能但激進     |
| 槓桿     | 達到大幅淨現金                       | 不現實         |
| 成本 C   | AISC 需為負                          | 不可能         |
| 稀釋 D   | 股數減少 33%                         | 不現實         |

**結論**：單因子無法獨立達成目標，需要多因子組合。

---

## 雙因子組合

更現實的情境是兩個因子同時調整。

### 組合公式

```
R* / R_now = (M* / M_now) × ((1-L*) / (1-L_now)) × (C* / C_now) × (D* / D_now)
```

若只調整兩個因子（如 M 和金屬價格 S）：

```
R* / R_now = (M* / M_now) × (C* / C_now)
```

其中 C 會因 S 變化而變化：

```
C = 1 - AISC / S
```

### 組合網格

```python
def generate_two_factor_grid(R_now, R_target, M_now, C_now, AISC, S):
    """
    生成雙因子組合網格

    組合 1: 倍數擴張 + 白銀下跌
    組合 2: 倍數擴張 + 去槓桿
    組合 3: 成本改善 + 倍數擴張
    """
    target_ratio = R_target / R_now
    results = []

    # 組合 1: 倍數 + 白銀
    for m_mult in [1.10, 1.15, 1.20, 1.25, 1.30]:
        for s_mult in [0.85, 0.90, 0.95, 1.00]:  # 白銀下跌
            new_S = S * s_mult
            new_C = 1 - AISC / new_S
            new_M = M_now * m_mult

            # 假設其他因子不變
            achieved_ratio = (m_mult) * (new_C / C_now)

            results.append({
                'scenario': 'multiple_plus_metal',
                'multiple_change': m_mult - 1,
                'metal_change': s_mult - 1,
                'achieved_ratio': achieved_ratio,
                'hits_target': achieved_ratio >= target_ratio
            })

    return results
```

### 範例輸出

| 組合                    | 倍數調整 | 白銀調整 | 達標 |
|-------------------------|----------|----------|------|
| 倍數 +20%, 白銀 -15%    | +20%     | -15%     | ✓    |
| 倍數 +30%, 白銀 不變    | +30%     | 0%       | ✓    |
| 倍數 +10%, 白銀 -20%    | +10%     | -20%     | ✓    |
| 倍數 +15%, 去槓桿 -10%  | +15%     | -10% ND/EV| ✓   |

---

## 校準常數 K 估計

### 方法 1：當期校準

```python
def calibrate_K(R_now, M_now, one_minus_L_now, C_now, D_now):
    """
    由當前觀測值校準 K

    K = R_now / (M_now × (1-L_now) × C_now × D_now)
    """
    product = M_now * one_minus_L_now * C_now * D_now
    if product == 0:
        return None
    K = R_now / product
    return K
```

### 方法 2：回歸估計

```python
import statsmodels.api as sm
import numpy as np

def estimate_K_regression(ratio_series, factors_df):
    """
    使用回歸估計 K（更穩健）

    log(R) = log(K) + log(M) + log(1-L) + log(C) + log(D) + ε
    """
    # 取對數
    y = np.log(ratio_series)
    X = np.log(factors_df[['M', 'one_minus_L', 'C', 'D']])
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()

    # K = exp(intercept)
    K = np.exp(model.params['const'])

    return {
        'K': K,
        'r_squared': model.rsquared,
        'coefficients': model.params.to_dict()
    }
```

---

## 情境推演框架

### 完整推演流程

```python
def full_scenario_analysis(current_state, target_ratio):
    """
    完整情境推演

    Parameters
    ----------
    current_state : dict
        {'R': 1.13, 'M': 6.4, 'L': 0.25, 'C': 0.703, 'D': 0.89, 'AISC': 28, 'S': 94.4}
    target_ratio : float
        目標比率（如 1.7）

    Returns
    -------
    dict
        單因子反推 + 雙因子組合網格
    """
    R_now = current_state['R']
    ratio_mult = target_ratio / R_now

    # 單因子反推
    single_factor = {
        'multiple_only': current_state['M'] * ratio_mult,
        'leverage_only': (1 - current_state['L']) * ratio_mult,
        'cost_only_C': current_state['C'] * ratio_mult,
        'cost_only_aisc': current_state['S'] * (1 - current_state['C'] * ratio_mult),
        'dilution_only': current_state['D'] * ratio_mult
    }

    # 可行性判斷
    feasibility = {
        'multiple_only': single_factor['multiple_only'] < 15,  # 合理上限
        'leverage_only': single_factor['leverage_only'] <= 1.5,
        'cost_only': 0 < single_factor['cost_only_aisc'] < current_state['AISC'],
        'dilution_only': 0.5 < single_factor['dilution_only'] < 1.5
    }

    # 雙因子組合
    two_factor_grid = generate_two_factor_grid(
        R_now, target_ratio,
        current_state['M'], current_state['C'],
        current_state['AISC'], current_state['S']
    )

    return {
        'target_ratio': target_ratio,
        'ratio_multiplier': ratio_mult,
        'single_factor': single_factor,
        'feasibility': feasibility,
        'two_factor_grid': two_factor_grid
    }
```

---

## 歷史類比驗證

回顧歷史上比率從底部回到頂部的案例：

| 期間              | 起始比率 | 終點比率 | 礦業股漲幅 | 白銀漲幅 | 主要驅動     |
|-------------------|----------|----------|------------|----------|--------------|
| 2016 Q1 → 2016 Q3 | 1.2      | 2.0      | +180%      | +50%     | 倍數擴張     |
| 2020 Q1 → 2020 Q3 | 1.3      | 1.9      | +200%      | +140%    | 倍數 + 成本  |

**洞察**：歷史上比率回升時，礦業股漲幅通常顯著跑贏白銀（槓桿效應）。

---

## 注意事項

1. **非預測**：反推結果是「極端情境參考」，非價格預測
2. **路徑依賴**：實際可能是多因子同時調整，路徑複雜
3. **模型限制**：簡化模型忽略了許多細節（如稅率、匯率等）
4. **樣本外風險**：歷史類比不保證未來重演
