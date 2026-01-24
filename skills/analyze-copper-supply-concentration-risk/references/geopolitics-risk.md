# 地緣風險指數計算方法

## 概述

地緣政治是銅供應的「慢變量」風險：
- 市場常忽略（不在即時價格中反映）
- 但一旦爆發，影響可能是結構性的
- 需要持續監控並納入系統風險評估

---

## GDELT 事件資料庫

### 簡介

GDELT（Global Database of Events, Language, and Tone）是全球最大的事件資料庫：

- **覆蓋**：全球 240+ 國家/地區
- **歷史**：1979 年至今
- **更新**：每 15 分鐘
- **成本**：免費

### API 端點

```
https://api.gdeltproject.org/api/v2/doc/doc
```

### 查詢參數

| 參數 | 說明 | 範例 |
|------|------|------|
| query | 搜索關鍵字 | `mining AND (strike OR conflict)` |
| timespan | 時間範圍 | `3months` |
| mode | 輸出模式 | `ArtList`, `TimelineVol` |
| sourcecountry | 來源國家 | `PE` (秘魯) |

---

## 風險關鍵字設計

### 銅礦供應風險相關

```python
RISK_KEYWORDS = {
    "conflict": [
        "mining conflict",
        "mining protest",
        "mining strike",
        "mining violence",
        "indigenous protest mining"
    ],
    "policy": [
        "mining tax",
        "mining regulation",
        "nationalization mining",
        "export ban mining",
        "mining permit"
    ],
    "environmental": [
        "mining water rights",
        "mining pollution",
        "mining environmental",
        "tailings dam"
    ],
    "labor": [
        "mining strike",
        "mining union",
        "mining workers",
        "mining wage"
    ]
}
```

### 國家特定關鍵字

| 國家 | 額外關鍵字 |
|------|-----------|
| 智利 | `Codelco`, `Escondida`, `Atacama` |
| 秘魯 | `Las Bambas`, `Antamina`, `Arequipa` |
| DRC | `Katanga`, `Kamoa`, `Gécamines`, `cobalt` |

---

## 風險指數計算

### Step 1: 事件頻率統計

```python
def fetch_event_count(country: str, keywords: list, lookback_months: int = 12) -> int:
    """
    從 GDELT 擷取特定國家的事件數量

    Parameters:
    -----------
    country : str
        目標國家
    keywords : list
        搜索關鍵字
    lookback_months : int
        回溯月數

    Returns:
    --------
    int : 事件數量
    """
    import requests

    # 構建查詢
    query = " OR ".join([f'"{kw}"' for kw in keywords])
    query += f' AND (country:{country} OR sourcecountry:{country})'

    params = {
        "query": query,
        "mode": "TimelineVol",
        "timespan": f"{lookback_months}months",
        "format": "json"
    }

    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        # 解析並加總事件數
        total_events = sum(item.get("value", 0) for item in data.get("timeline", []))
        return total_events
    except Exception as e:
        print(f"GDELT 查詢失敗: {e}")
        return None
```

### Step 2: 歷史基準建立

```python
def compute_baseline_stats(country: str, keywords: list, years: int = 3) -> dict:
    """
    計算歷史基準統計

    Returns:
    --------
    dict : mean, std, min, max
    """
    # 抓取過去 N 年每月事件數
    monthly_counts = []

    for months_ago in range(0, years * 12, 1):
        count = fetch_event_count(country, keywords, lookback_months=1)
        monthly_counts.append(count)

    import numpy as np
    return {
        "mean": np.mean(monthly_counts),
        "std": np.std(monthly_counts),
        "min": np.min(monthly_counts),
        "max": np.max(monthly_counts)
    }
```

### Step 3: Z-Score 計算

```python
def compute_geo_risk_zscore(current_count: int, baseline: dict) -> float:
    """
    計算地緣風險 Z-Score

    Z = (current - mean) / std

    解讀：
    - Z < 0：低於歷史平均（較安全）
    - Z = 0-1：歷史平均水平
    - Z = 1-2：偏高風險
    - Z > 2：顯著高風險
    """
    if baseline["std"] == 0:
        return 0.0

    z_score = (current_count - baseline["mean"]) / baseline["std"]
    return round(z_score, 2)


def classify_risk_level(z_score: float) -> str:
    """
    根據 Z-Score 分類風險等級
    """
    if z_score < 0:
        return "低"
    elif z_score < 1:
        return "中"
    elif z_score < 2:
        return "中高"
    else:
        return "高"
```

---

## 完整風險指數計算

```python
def compute_country_geo_risk(country: str, lookback_months: int = 12) -> dict:
    """
    計算單一國家的地緣風險指數

    Returns:
    --------
    dict : 完整風險評估
    """
    keywords = RISK_KEYWORDS["conflict"] + RISK_KEYWORDS["policy"] + RISK_KEYWORDS["labor"]

    # 當前事件數
    current_count = fetch_event_count(country, keywords, lookback_months)

    # 歷史基準（使用快取或預計算值）
    baseline = get_cached_baseline(country)
    if baseline is None:
        baseline = compute_baseline_stats(country, keywords)

    # Z-Score
    z_score = compute_geo_risk_zscore(current_count, baseline)

    return {
        "country": country,
        "event_count_12m": current_count,
        "historical_mean": baseline["mean"],
        "historical_std": baseline["std"],
        "z_score": z_score,
        "risk_level": classify_risk_level(z_score)
    }
```

---

## 系統風險整合

### 加權方法

地緣風險在系統風險中的權重，根據替代依賴度調整：

```python
def compute_geo_weighted_risk(
    geo_risks: dict,
    replacement_weights: dict
) -> float:
    """
    計算加權地緣風險

    Parameters:
    -----------
    geo_risks : dict
        各國地緣風險 Z-Score
        {"Peru": 1.2, "DRC": 2.1, "Chile": 0.3}
    replacement_weights : dict
        各國在替代供應中的權重
        {"Peru": 0.45, "DRC": 0.55}  # 基於增量貢獻

    Returns:
    --------
    float : 加權後的地緣風險分數
    """
    weighted_sum = 0
    total_weight = 0

    for country, weight in replacement_weights.items():
        if country in geo_risks:
            weighted_sum += geo_risks[country] * weight
            total_weight += weight

    if total_weight == 0:
        return 0

    return weighted_sum / total_weight
```

### 整合到系統風險分數

```python
def compute_system_risk(
    concentration_score: float,
    dependency_score: float,
    geo_risk_weighted: float
) -> dict:
    """
    計算綜合系統風險分數

    公式：
    system_risk = concentration × (1 + dependency) × (1 + geo_risk × 0.2)

    Parameters:
    -----------
    concentration_score : float
        集中度分數（HHI/100，0-100 範圍）
    dependency_score : float
        依賴度分數（1 - replacement_ratio，調整後）
    geo_risk_weighted : float
        加權地緣風險 Z-Score

    Returns:
    --------
    dict : 系統風險評估
    """
    # 地緣風險乘數（Z-Score → 乘數）
    geo_multiplier = 1 + geo_risk_weighted * 0.2

    # 綜合分數
    raw_score = concentration_score * (1 + dependency_score) * geo_multiplier

    # 標準化到 0-100
    system_risk = min(raw_score, 100)

    return {
        "system_risk_score": round(system_risk, 1),
        "components": {
            "concentration": round(concentration_score, 1),
            "dependency": round(dependency_score, 2),
            "geo_risk": round(geo_risk_weighted, 2)
        },
        "interpretation": interpret_system_risk(system_risk)
    }


def interpret_system_risk(score: float) -> str:
    if score < 30:
        return "低風險 - 供應鏈相對穩健"
    elif score < 50:
        return "中等風險 - 需關注關鍵國家動態"
    elif score < 70:
        return "高風險 - 建議評估對沖策略"
    else:
        return "極高風險 - 供應中斷可能性顯著"
```

---

## 替代方案

### 當 GDELT 不可用時

#### 1. 新聞計數代理（news_count）

使用 Google News API 或類似服務：

```python
def fetch_news_count_proxy(country: str, keywords: list, days: int = 30) -> int:
    """
    使用新聞搜索計數作為風險代理
    """
    # 使用 Google News RSS 或其他新聞 API
    pass
```

#### 2. 固定風險評級

基於歷史經驗設定固定值：

```python
FIXED_RISK_RATINGS = {
    "Chile": {"risk_level": "低", "z_score": 0.3},
    "Peru": {"risk_level": "中高", "z_score": 1.5},
    "DRC": {"risk_level": "高", "z_score": 2.0}
}
```

---

## 監控與警報

### 警報門檻

| Z-Score | 警報等級 | 行動 |
|---------|----------|------|
| < 1 | 正常 | 例行監控 |
| 1-2 | 注意 | 增加監控頻率 |
| 2-3 | 警告 | 評估對沖策略 |
| > 3 | 緊急 | 立即評估供應鏈影響 |

### 監控頻率

| 國家風險等級 | 建議頻率 |
|--------------|----------|
| 高（DRC） | 每日 |
| 中高（秘魯） | 每週 |
| 中/低（智利） | 每月 |
