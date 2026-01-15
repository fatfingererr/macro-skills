# 行情體質判定規則

本文件定義資產行情體質的判定規則。

**重要說明**：
- 本文件主要描述**黃金專屬**的 1970s-like vs 2000s-like 體質判定
- 其他資產需要定義不同的體質分類和驅動因子
- 若對非黃金資產啟用宏觀分析，需自行設計適當的因子

## 概念基礎

### 什麼是「行情體質」？

行情體質描述當前市場的宏觀驅動因素組合，決定了：

1. 資產上漲的持續性
2. 偏離度回歸的可能性
3. 適合的交易/配置策略

### 黃金的特殊性

黃金作為貨幣替代品和通膨對沖工具，其行情體質主要由貨幣政策、通膨環境、地緣風險決定，因此有獨特的體質分類方法。

### 黃金的兩種典型體質

| 體質 | 主要驅動 | 黃金角色 | 偏離度特性 |
|------|----------|----------|------------|
| **1970s-like** | 高通膨、法幣信心下滑、地緣風險 | 避險/對沖通膨 | 可維持極端偏離較長時間 |
| **2000s-like** | 成長、資產配置、適度通膨 | 多元化資產 | 偏離度較容易回歸均值 |

### 其他資產的體質定義（範例）

**股票指數**：
- **Risk-On**：經濟成長、盈利擴張、低波動
- **Risk-Off**：衰退擔憂、盈利下修、避險情緒

**比特幣**：
- **機構採用期**：主流接受度提升、法規友善、機構配置增加
- **投機主導期**：零售情緒驅動、槓桿過度、監管不確定性

## 判定因子

### 1. 實質利率（Real Rate）

**定義**：名目利率 - 通膨預期

**數據代理**：
- 首選：10Y TIPS 收益率（FRED: DFII10）
- 替代：FFR - Core CPI YoY

**判定規則**：

```python
def score_real_rate(real_rate: float, trend: str) -> float:
    """
    評分實質利率因子

    Args:
        real_rate: 當前實質利率（%）
        trend: "up" / "down" / "flat"

    Returns:
        0-1 的分數，1 = 完全支持 1970s-like
    """
    score = 0.0

    # 負實質利率強烈支持 1970s-like
    if real_rate < 0:
        score = 1.0
    elif real_rate < 1.0:
        score = 0.5
    else:
        score = 0.0

    # 下降趨勢額外加分
    if trend == "down" and score < 1.0:
        score += 0.2

    return min(score, 1.0)
```

**權重**：0.30

### 2. 通膨/通膨預期（Inflation）

**定義**：市場對未來通膨的預期

**數據代理**：
- 首選：5Y Breakeven（FRED: T5YIE）
- 替代：5y5y Forward Inflation Expectation（FRED: T5YIFR）
- 替代：CPI YoY

**判定規則**：

```python
def score_inflation(inflation: float, trend: str) -> float:
    """
    評分通膨因子

    Args:
        inflation: 當前通膨預期（%）
        trend: "up" / "down" / "flat"

    Returns:
        0-1 的分數
    """
    score = 0.0

    # 高通膨預期支持 1970s-like
    if inflation > 3.0:
        score = 1.0
    elif inflation > 2.5:
        score = 0.7
    elif inflation > 2.0:
        score = 0.3
    else:
        score = 0.0

    # 上升趨勢額外加分
    if trend == "up" and score < 1.0:
        score += 0.3

    return min(score, 1.0)
```

**權重**：0.25

### 3. 地緣政治風險（Geopolitical Risk）

**定義**：全球地緣政治緊張程度

**數據代理**：
- 首選：GPR Index（Caldara-Iacoviello）
- 替代：新聞關鍵詞計數（war, conflict, sanction, tension）

**判定規則**：

```python
def score_geopolitical(gpr_percentile: float, trend: str) -> float:
    """
    評分地緣風險因子

    Args:
        gpr_percentile: GPR 指數在歷史中的分位數（0-100）
        trend: "up" / "down" / "flat"

    Returns:
        0-1 的分數
    """
    score = 0.0

    # 高分位數支持 1970s-like
    if gpr_percentile > 80:
        score = 1.0
    elif gpr_percentile > 60:
        score = 0.6
    elif gpr_percentile > 40:
        score = 0.3
    else:
        score = 0.0

    # 上升趨勢額外加分
    if trend == "up" and score < 1.0:
        score += 0.2

    return min(score, 1.0)
```

**權重**：0.25

### 4. 美元強弱（USD）

**定義**：美元對其他主要貨幣的相對強弱

**數據代理**：
- 首選：Trade-Weighted USD Index（FRED: DTWEXBGS）
- 替代：DXY（Yahoo Finance）

**判定規則**：

```python
def score_usd(usd_trend: str, months_from_high: int) -> float:
    """
    評分美元因子

    Args:
        usd_trend: "up" / "down" / "flat"
        months_from_high: 距離 12 個月高點的月數

    Returns:
        0-1 的分數
    """
    score = 0.0

    # 美元走弱支持 1970s-like
    if usd_trend == "down":
        score = 0.7
    elif usd_trend == "flat":
        score = 0.3
    else:  # "up"
        score = 0.0

    # 遠離高點額外加分
    if months_from_high >= 6:
        score += 0.3

    return min(score, 1.0)
```

**權重**：0.20

## 綜合判定

### 計算總分

```python
def calculate_regime_score(factors: dict) -> tuple[str, float, list]:
    """
    計算行情體質總分

    Args:
        factors: {
            "real_rate": {"value": float, "trend": str},
            "inflation": {"value": float, "trend": str},
            "geopolitical": {"percentile": float, "trend": str},
            "usd": {"trend": str, "months_from_high": int}
        }

    Returns:
        (regime_label, confidence, drivers)
    """
    weights = {
        "real_rate": 0.30,
        "inflation": 0.25,
        "geopolitical": 0.25,
        "usd": 0.20
    }

    scores = {}
    drivers = []

    # 計算各因子分數
    scores["real_rate"] = score_real_rate(
        factors["real_rate"]["value"],
        factors["real_rate"]["trend"]
    )
    if scores["real_rate"] > 0.5:
        drivers.append("Real rates negative / falling")

    scores["inflation"] = score_inflation(
        factors["inflation"]["value"],
        factors["inflation"]["trend"]
    )
    if scores["inflation"] > 0.5:
        drivers.append("Inflation risk rising")

    scores["geopolitical"] = score_geopolitical(
        factors["geopolitical"]["percentile"],
        factors["geopolitical"]["trend"]
    )
    if scores["geopolitical"] > 0.5:
        drivers.append("Geopolitical tension proxy rising")

    scores["usd"] = score_usd(
        factors["usd"]["trend"],
        factors["usd"]["months_from_high"]
    )
    if scores["usd"] > 0.5:
        drivers.append("USD weakening")

    # 加權總分
    total_score = sum(
        scores[k] * weights[k] for k in scores
    )

    # 判定
    if total_score >= 0.5:
        return "1970s_like", total_score, drivers
    else:
        return "2000s_like", 1 - total_score, drivers
```

### 判定門檻

| 總分 | 判定 | 含義 |
|------|------|------|
| ≥ 0.7 | 強 1970s-like | 多個因子強烈支持 |
| 0.5-0.7 | 弱 1970s-like | 部分因子支持 |
| 0.3-0.5 | 弱 2000s-like | 部分因子支持 |
| < 0.3 | 強 2000s-like | 多個因子強烈支持 |

## 歷史案例

### 1970s（典型 1970s-like）

| 因子 | 狀態 | 分數 |
|------|------|------|
| 實質利率 | 深度負利率（-4% to -6%） | 1.0 |
| 通膨 | 高且上升（8%-14%） | 1.0 |
| 地緣風險 | 高（石油危機、越戰） | 1.0 |
| 美元 | 大幅走弱 | 1.0 |
| **總分** | | **1.0** |

**結果**：黃金從 $35 漲到 $850，偏離度達 320%。

### 2000s-2011（混合特徵）

| 因子 | 狀態 | 分數 |
|------|------|------|
| 實質利率 | 低但不一定負 | 0.5 |
| 通膨 | 溫和（2%-3%） | 0.3 |
| 地緣風險 | 中等偏高（911後、伊拉克戰爭） | 0.6 |
| 美元 | 先弱後穩 | 0.5 |
| **總分** | | **0.45** |

**結果**：黃金從 $250 漲到 $1900，偏離度約 85%，之後回調。

### 2019-2024（偏 1970s-like）

| 因子 | 狀態 | 分數 |
|------|------|------|
| 實質利率 | 負利率時期較長 | 0.8 |
| 通膨 | 上升後居高不下 | 0.7 |
| 地緣風險 | 高（俄烏、中東） | 0.8 |
| 美元 | 波動但未持續走強 | 0.5 |
| **總分** | | **0.72** |

## 使用建議

### 體質判定的用途

1. **風險評估**：1970s-like 體質下，高偏離度可能持續更久
2. **策略調整**：不同體質下，停損和倉位策略應有所不同
3. **情境規劃**：考慮體質轉變的可能性和觸發條件

### 不應用於

1. **短期交易訊號**：體質是中長期概念
2. **精確擇時**：體質判定是模糊的，不適合精確擇時
3. **單獨決策依據**：應結合其他分析工具使用

### 體質轉變的觸發條件

從 1970s-like → 2000s-like：
- 央行大幅升息，實質利率轉正
- 通膨預期被錨定
- 地緣風險緩和

從 2000s-like → 1970s-like：
- 通膨失控
- 央行政策失去公信力
- 重大地緣衝突
