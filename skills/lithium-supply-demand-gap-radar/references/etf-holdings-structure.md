# LIT ETF 持股結構參考

本文件說明 Global X Lithium & Battery Tech ETF (LIT) 的持股結構和產業鏈分類。

---

## ETF 概述

### 基本資訊

| 項目 | 說明 |
|------|------|
| 名稱 | Global X Lithium & Battery Tech ETF |
| 代碼 | LIT |
| 發行商 | Global X |
| 成立日期 | 2010-07-22 |
| 費用率 | 0.75% |
| 追蹤指數 | Solactive Global Lithium Index |

### 投資範圍

LIT 投資於鋰產業鏈的三個層級：

1. **Upstream (上游)**: 鋰礦開採
2. **Midstream (中游)**: 鋰精煉、化學品生產
3. **Downstream (下游)**: 電池製造、電動車

---

## 持股分類框架

### 產業鏈段定義

```
┌─────────────────────────────────────────────────────────────┐
│                     鋰產業鏈                                 │
├─────────────┬─────────────────┬─────────────────────────────┤
│  Upstream   │    Midstream    │         Downstream          │
│   (礦端)    │    (化學品)     │         (電池/EV)           │
├─────────────┼─────────────────┼─────────────────────────────┤
│ 鋰礦開採    │ 鋰精煉          │ 電池製造                    │
│ 鋰輝石生產  │ 碳酸鋰生產      │ 電池材料（正極/負極）       │
│             │ 氫氧化鋰生產    │ 電動車整車                  │
├─────────────┼─────────────────┼─────────────────────────────┤
│ 對鋰價敏感  │ 對鋰價敏感      │ 對鋰價較不敏感              │
│ 高 (1.5-2.5)│ 中 (0.8-1.2)    │ 低 (0.3-0.8)                │
└─────────────┴─────────────────┴─────────────────────────────┘
```

### 典型持股分類

#### Upstream (上游礦商)

| 股票代碼 | 公司名稱 | 國家 | 主要業務 |
|----------|----------|------|----------|
| ALB | Albemarle Corp | US | 鋰化學品巨頭、礦業 |
| SQM | Sociedad Quimica y Minera | Chile | 鹵水提鋰 |
| PLS.AX | Pilbara Minerals | Australia | 硬岩鋰輝石 |
| MIN.AX | Mineral Resources | Australia | 硬岩鋰輝石 |
| IGO.AX | IGO Ltd | Australia | 鋰、鎳礦 |
| LAC | Lithium Americas | US/Canada | 鋰開發項目 |
| SGML | Sigma Lithium | Brazil | 鋰輝石開發 |

**特徵**:
- 營收直接與鋰價掛鉤
- 高營業槓桿
- 對鋰價 beta 最高

#### Midstream (中游精煉)

| 股票代碼 | 公司名稱 | 國家 | 主要業務 |
|----------|----------|------|----------|
| LTHM | Arcadium Lithium | US | 氫氧化鋰生產 |
| GANF.PA | Ganfeng Lithium (ADR) | China | 鋰化學品 |
| TIAN.SZ | Tianqi Lithium | China | 鋰化學品 |

**特徵**:
- 受鋰價和加工費影響
- 垂直整合程度不一
- 對鋰價 beta 中等

#### Downstream (下游電池/EV)

| 股票代碼 | 公司名稱 | 國家 | 主要業務 |
|----------|----------|------|----------|
| TSLA | Tesla Inc | US | 電動車、儲能 |
| CATL (300750.SZ) | CATL | China | 電池製造 |
| 6752.T | Panasonic | Japan | 電池製造 |
| 051910.KS | LG Energy Solution | Korea | 電池製造 |
| 006400.KS | Samsung SDI | Korea | 電池製造 |
| 1211.HK | BYD | China | 電動車、電池 |

**特徵**:
- 鋰是成本項目之一，非全部
- 受競爭格局、技術路線影響
- 對鋰價 beta 較低

---

## 預期 Beta 估計

### 按產業鏈段

| 產業鏈段 | 對鋰價 Beta 範圍 | 說明 |
|----------|------------------|------|
| Upstream | 1.5 - 2.5 | 營收直接受鋰價影響 |
| Midstream | 0.8 - 1.2 | 受鋰價和加工費影響 |
| Downstream | 0.3 - 0.8 | 鋰是成本之一 |

### 個股 Beta 估計

```python
# 基於歷史回歸的 beta 估計（示例）
STOCK_BETAS = {
    # Upstream
    "ALB": 1.8,
    "SQM": 1.9,
    "PLS.AX": 2.2,
    "MIN.AX": 2.0,
    "LAC": 2.5,

    # Midstream
    "LTHM": 1.1,
    "GANF": 1.3,

    # Downstream
    "TSLA": 0.5,
    "CATL": 0.6,
    "6752.T": 0.4,
    "051910.KS": 0.5,
    "006400.KS": 0.5,
    "1211.HK": 0.7
}
```

---

## 加權 Beta 計算

### 公式

```python
def compute_weighted_etf_beta(holdings, stock_betas):
    """
    計算 ETF 的加權 beta

    ETF_beta = Σ(weight_i × beta_i)
    """
    weighted_beta = 0

    for holding in holdings:
        ticker = holding["ticker"]
        weight = holding["weight"] / 100  # 轉為小數

        beta = stock_betas.get(ticker, estimate_beta_by_segment(holding["segment"]))
        weighted_beta += weight * beta

    return weighted_beta
```

### 示例計算

假設 LIT 持股結構：

| 股票 | 權重 | Beta | 貢獻 |
|------|------|------|------|
| ALB | 8% | 1.8 | 0.144 |
| SQM | 6% | 1.9 | 0.114 |
| TSLA | 10% | 0.5 | 0.050 |
| CATL | 8% | 0.6 | 0.048 |
| ... | ... | ... | ... |
| **合計** | 100% | - | **~0.85** |

---

## 持股變動影響

### 定期調整

- LIT 追蹤 Solactive Global Lithium Index
- 指數定期再平衡（通常季度）
- 權重變動會影響 ETF 的整體 beta

### 監控要點

```python
def detect_holdings_change(current_holdings, previous_holdings):
    """
    偵測持股變動
    """
    changes = {
        "added": [],
        "removed": [],
        "weight_changed": []
    }

    current_set = set(h["ticker"] for h in current_holdings)
    previous_set = set(h["ticker"] for h in previous_holdings)

    changes["added"] = list(current_set - previous_set)
    changes["removed"] = list(previous_set - current_set)

    # 權重變動
    for c in current_holdings:
        ticker = c["ticker"]
        prev = next((p for p in previous_holdings if p["ticker"] == ticker), None)
        if prev and abs(c["weight"] - prev["weight"]) > 1:
            changes["weight_changed"].append({
                "ticker": ticker,
                "old_weight": prev["weight"],
                "new_weight": c["weight"]
            })

    return changes
```

---

## 傳導敏感度分析

### 傳導正常的特徵

1. ETF 對鋰價 rolling beta > 0.5
2. 上游持股權重穩定
3. 無重大個股特殊事件

### 傳導斷裂的特徵

1. Beta 持續低於 0.3 超過 8 週
2. 下游/非鋰業務持股權重上升
3. 市場情緒主導個股走勢

### 分析代碼

```python
def analyze_transmission(beta_history, holdings_history, threshold=0.3, duration=8):
    """
    分析傳導狀態
    """

    recent_betas = beta_history[-duration:]

    # 檢查 beta 趨勢
    if all(b < threshold for b in recent_betas):
        return {
            "status": "broken",
            "reason": f"Beta 低於 {threshold} 持續 {duration} 週",
            "recommendation": "分析個股因素，考慮直接交易鋰 proxy"
        }

    # 檢查持股結構變化
    upstream_weight_trend = compute_segment_weight_trend(holdings_history, "upstream")

    if upstream_weight_trend < -5:  # 上游權重下降超過 5%
        return {
            "status": "weakening",
            "reason": "上游持股權重下降",
            "recommendation": "監控 beta 是否持續下降"
        }

    return {
        "status": "normal",
        "reason": f"近期平均 Beta = {np.mean(recent_betas):.2f}",
        "recommendation": "正常使用 ETF 作為鋰暴露工具"
    }
```

---

## 替代 ETF 選項

如果 LIT 傳導不佳，可考慮其他選項：

| ETF | 代碼 | 特點 |
|-----|------|------|
| Global X Lithium | LITM | 更集中於純鋰業務 |
| Amplify Lithium & Battery Tech | BATT | 更廣泛的電池供應鏈 |
| First Trust NASDAQ Clean Edge Smart Grid | GRID | 電網/儲能相關 |
| iShares Global Clean Energy | ICLN | 更廣泛的清潔能源 |

### 直接暴露選項

- 個股籃子（ALB, SQM, PLS.AX）
- CME 鋰期貨
- 鋰相關公司債券
