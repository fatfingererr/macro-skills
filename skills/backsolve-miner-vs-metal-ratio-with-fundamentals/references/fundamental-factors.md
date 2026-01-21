# 四大基本面因子

本文件說明礦業股/金屬價格比率的四大基本面因子計算邏輯。

## 概述

礦業股/金屬價格比率可分解為四大可量化因子：

```
R_t ≈ K × M_t × (1-L_t) × C_t × D_t
```

| 符號    | 名稱     | 直覺                                 |
|---------|----------|--------------------------------------|
| R_t     | 比率     | 礦業股價格 / 金屬價格                |
| K       | 校準常數 | 吸收模型細節的殘差項                 |
| M_t     | 倍數因子 | 市場給予的估值倍數（EV/EBITDA）      |
| (1-L_t) | 槓桿因子 | 財務槓桿的折扣（1 - NetDebt/EV）     |
| C_t     | 成本因子 | 金屬價格與成本的差距（1 - AISC/S）   |
| D_t     | 稀釋因子 | 股權稀釋的折扣（Shares_base/Shares） |

---

## 成本因子 (C)

### 定義

成本因子衡量金屬價格與開採成本的差距：

```
C_t = 1 - AISC_t / S_t
```

其中：
- **AISC_t**：全維持成本（All-In Sustaining Cost），$/oz
- **S_t**：金屬價格，$/oz

### 直覺

| C 值    | 解讀                         |
|---------|------------------------------|
| C > 0.5 | 成本遠低於價格，礦企獲利豐厚 |
| C ≈ 0.3 | 成本約為價格 70%，正常獲利   |
| C < 0.1 | 成本接近價格，獲利微薄或虧損 |
| C < 0   | 成本高於價格，虧損           |

### AISC 組成

```
AISC = Cash Cost + Sustaining Capex + G&A - Byproduct Credits
```

| 組成              | 說明                       |
|-------------------|----------------------------|
| Cash Cost         | 採礦、加工、精煉的直接成本 |
| Sustaining Capex  | 維持現有產能的資本支出     |
| G&A               | 一般與管理費用             |
| Byproduct Credits | 副產品銷售抵減（如銅、鋅） |

### 計算方法

**方法 1：直接抽取（優先）**

從 MD&A 或年報抽取揭露的 AISC：

```python
# 正則匹配
pattern = r'AISC\s+(?:of\s+)?\$?([\d.]+)\s*(?:per\s+)?(?:ounce|oz)'
match = re.search(pattern, mda_text, re.IGNORECASE)
aisc = float(match.group(1))
```

**方法 2：Proxy 回算**

當直接揭露不可得時：

```python
def proxy_aisc(financials, production_oz):
    operating_cost = financials['cost_of_revenue']
    sustaining_capex = financials['capex'] * 0.6  # 假設 60% 維持性
    ga = financials['ga_expense']
    byproduct = financials['other_revenue'] * 0.5  # 估計值

    aisc = (operating_cost + sustaining_capex + ga - byproduct) / production_oz
    return aisc
```

---

## 槓桿因子 (1-L)

### 定義

槓桿因子反映財務槓桿對估值的折扣：

```
L_t = NetDebt_t / EV_t
(1-L_t) = 1 - NetDebt_t / EV_t
```

其中：
- **NetDebt**：淨負債 = 總負債 - 現金
- **EV**：企業價值 = 市值 + 總負債 - 現金

### 直覺

| (1-L) 值 | L 值    | 解讀                 |
|----------|---------|----------------------|
| > 1.0    | < 0     | 淨現金，財務非常健康 |
| 0.7-1.0  | 0-0.3   | 槓桿適中             |
| 0.5-0.7  | 0.3-0.5 | 槓桿偏高             |
| < 0.5    | > 0.5   | 高槓桿，財務風險較高 |

### 計算

```python
def compute_leverage_factor(total_debt, cash, market_cap):
    net_debt = total_debt - cash
    ev = market_cap + net_debt

    if ev <= 0:
        return None  # 異常情況

    L = net_debt / ev
    one_minus_L = 1 - L

    return {
        'net_debt': net_debt,
        'ev': ev,
        'L': L,
        'one_minus_L': one_minus_L
    }
```

### 替代方法

| 方法              | 公式                     | 適用場景         |
|-------------------|--------------------------|------------------|
| NetDebt/EV        | NetDebt / EV             | 標準方法（推薦） |
| NetDebt/EBITDA    | NetDebt / EBITDA         | 獲利能力視角     |
| Interest Coverage | EBITDA / InterestExpense | 償債能力視角     |

---

## 倍數因子 (M)

### 定義

倍數因子反映市場給予礦業股的估值倍數：

```
M_t = EV_t / EBITDA_t
```

### 直覺

| M 值    | 解讀                           |
|---------|--------------------------------|
| M > 10  | 估值偏高，市場樂觀             |
| M ≈ 6-8 | 礦業股歷史平均區間             |
| M < 5   | 估值偏低，可能被低估或反映風險 |

### EBITDA 計算

若無直接欄位：

```python
def compute_ebitda_proxy(operating_income, depreciation):
    """
    EBITDA ≈ Operating Income + D&A
    """
    return operating_income + depreciation
```

### 替代方法

| 方法      | 公式            | 適用場景                   |
|-----------|-----------------|----------------------------|
| EV/EBITDA | EV / EBITDA     | 標準方法（推薦）           |
| P/NAV     | Price / NAV     | 資產淨值視角（需礦區估值） |
| FCF Yield | FCF / MarketCap | 自由現金流視角             |

---

## 稀釋因子 (D)

### 定義

稀釋因子反映股權稀釋對每股價值的影響：

```
D_t = Shares_base / Shares_t
```

其中：
- **Shares_base**：基期股數（如 1 年前或分析起點）
- **Shares_t**：當前股數

### 直覺

| D 值    | 解讀                           |
|---------|--------------------------------|
| D = 1   | 無稀釋                         |
| D > 1   | 股數減少（回購），每股價值提升 |
| D < 1   | 股數增加（增發），每股價值稀釋 |
| D = 0.8 | 股數增加 25%，每股價值稀釋 20% |

### 礦業公司常見稀釋來源

| 來源       | 說明                     |
|------------|--------------------------|
| 股權融資   | 發行新股籌資（熊市常見） |
| 可轉債轉換 | 債轉股                   |
| 員工選擇權 | 管理層激勵               |
| 併購對價   | 以股票支付收購           |

### 計算

```python
def compute_dilution_factor(shares_now, shares_base):
    """
    D = Shares_base / Shares_now

    D < 1 表示有稀釋
    D > 1 表示有回購
    """
    if shares_now <= 0:
        return None

    D = shares_base / shares_now
    dilution_pct = 1 - D  # 正值表示稀釋，負值表示回購

    return {
        'D': D,
        'dilution_pct': dilution_pct,
        'shares_change': shares_now / shares_base - 1
    }
```

---

## 權重加總

當分析 ETF 或股票組合時，需將個股因子加權匯總：

```python
def weighted_aggregate(company_factors, weights):
    """
    權重加總各因子

    Parameters
    ----------
    company_factors : list[dict]
        各公司的因子 {'C': ..., 'one_minus_L': ..., 'M': ..., 'D': ...}
    weights : list[float]
        權重，總和應為 1

    Returns
    -------
    dict
        加權匯總後的因子
    """
    agg = {
        'C': 0,
        'one_minus_L': 0,
        'M': 0,
        'D': 0,
        'aisc': 0,
        'net_debt_to_ev': 0
    }

    for factors, w in zip(company_factors, weights):
        agg['C'] += factors['C'] * w
        agg['one_minus_L'] += factors['one_minus_L'] * w
        agg['M'] += factors['M'] * w
        agg['D'] += factors['D'] * w
        agg['aisc'] += factors['aisc'] * w
        agg['net_debt_to_ev'] += factors['L'] * w

    return agg
```

---

## 因子驅動分析

識別比率變動的主要驅動因素：

```python
def analyze_factor_contribution(factors_now, factors_base):
    """
    分析各因子對比率變動的貢獻

    Returns
    -------
    dict
        各因子變化與貢獻排名
    """
    changes = {
        'cost': factors_now['C'] / factors_base['C'] - 1,
        'leverage': factors_now['one_minus_L'] / factors_base['one_minus_L'] - 1,
        'multiple': factors_now['M'] / factors_base['M'] - 1,
        'dilution': factors_now['D'] / factors_base['D'] - 1
    }

    # 按絕對值排名
    ranking = sorted(changes.items(), key=lambda x: abs(x[1]), reverse=True)

    return {
        'changes': changes,
        'dominant_driver': ranking[0][0],
        'ranking': [f[0] for f in ranking]
    }
```

---

## 敏感度分析

各因子變動對比率的影響：

| 因子變動            | 對比率 R 的影響           |
|---------------------|---------------------------|
| AISC 上升 10%       | C 下降 → R 下降約 3-5%    |
| NetDebt/EV 上升 10% | (1-L) 下降 → R 下降約 10% |
| EV/EBITDA 下降 10%  | M 下降 → R 下降約 10%     |
| 股數增加 10%        | D 下降 → R 下降約 10%     |

**關鍵洞察**：倍數因子（M）和槓桿因子（1-L）對比率的影響是 1:1 的線性關係，而成本因子（C）的影響取決於 AISC/S 的水平。
