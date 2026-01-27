# 圖表標註規則對照表

## 1. 標註規則定義

將圖表上的敘事標註轉為可重複驗證的規則：

### 1.1 基本面驅動標註

| 標註 ID              | 顯示文字           | 觸發條件                                    |
|----------------------|--------------------|--------------------------------------------|
| `strong_corn_demand` | Strong Corn Demand | corn_export_surprise > 0 AND grains_flow > 0 |
| `strong_soy_demand`  | Strong Soy Demand  | soy_export_surprise > 0 AND oilseeds_flow > 0 |
| `bearish_usda_stats` | Bearish USDA Stats | wasde_surprise < 0 AND grains_flow < 0      |
| `bullish_usda_stats` | Bullish USDA Stats | wasde_surprise > 0 AND grains_flow > 0      |
| `weather_premium`    | Weather Premium    | weather_concern = true AND flow > 0         |

### 1.2 宏觀驅動標註

| 標註 ID              | 顯示文字           | 觸發條件                                    |
|----------------------|--------------------|--------------------------------------------|
| `macro_mood_bullish` | Macro Mood Bullish | macro_tailwind_score >= 0.67                |
| `macro_headwind`     | Macro Headwind     | macro_tailwind_score <= 0.33                |
| `usd_tailwind`       | USD Tailwind       | usd_weekly_return < -0.5%                   |
| `risk_on_mode`       | Risk-On Mode       | spy_return > 1% AND vix_down                |

### 1.3 流量特徵標註

| 標註 ID              | 顯示文字           | 觸發條件                                    |
|----------------------|--------------------|--------------------------------------------|
| `funds_back_buying`  | Funds Back & Buying| flow_reversal = positive AND firepower > 0.5 |
| `fund_capitulation`  | Fund Capitulation  | flow < p5_historical AND firepower > 0.8   |
| `crowded_long`       | Crowded Long       | firepower < 0.2                             |
| `extreme_short`      | Extreme Short      | firepower > 0.85                            |
| `small_holiday_flows`| Small Holiday Flows| abs(total_flow) < p25_historical            |

### 1.4 群組動態標註

| 標註 ID               | 顯示文字            | 觸發條件                                    |
|-----------------------|---------------------|--------------------------------------------|
| `grains_momentum_up`  | Grains Momentum Up  | grains_flow > 0 for 2+ weeks               |
| `oilseeds_outflow`    | Oilseeds Outflow    | oilseeds_flow < 0 for 2+ weeks             |
| `meats_rotation`      | Meats Rotation      | meats_flow direction changed               |
| `broad_based_buying`  | Broad-Based Buying  | 3+ groups with positive flow               |
| `sector_divergence`   | Sector Divergence   | grains and oilseeds flow opposite signs    |

---

## 2. 規則實作

```python
ANNOTATION_RULES = {
    # 基本面驅動
    "strong_corn_demand": {
        "label": "Strong Corn Demand",
        "condition": lambda ctx: (
            ctx.get("corn_export_surprise", 0) > 0 and
            ctx.get("grains_flow", 0) > 0
        ),
        "evidence_fn": lambda ctx: [
            f"Corn export surprise: +{ctx.get('corn_export_surprise', 0):.1%}",
            f"Grains flow: {ctx.get('grains_flow', 0):+,} contracts"
        ],
        "priority": 2
    },

    "bearish_usda_stats": {
        "label": "Bearish USDA Stats",
        "condition": lambda ctx: (
            ctx.get("wasde_surprise", 0) < 0 and
            ctx.get("grains_flow", 0) < 0
        ),
        "evidence_fn": lambda ctx: [
            f"WASDE surprise: {ctx.get('wasde_surprise', 0):+.1%}",
            f"Grains outflow: {ctx.get('grains_flow', 0):,} contracts"
        ],
        "priority": 2
    },

    # 宏觀驅動
    "macro_mood_bullish": {
        "label": "Macro Mood Bullish",
        "condition": lambda ctx: ctx.get("macro_tailwind_score", 0) >= 0.67,
        "evidence_fn": lambda ctx: [
            f"Macro tailwind: {ctx.get('macro_tailwind_score', 0):.0%}",
            *[k for k, v in ctx.get("macro_components", {}).items() if v]
        ],
        "priority": 1
    },

    "macro_headwind": {
        "label": "Macro Headwind",
        "condition": lambda ctx: ctx.get("macro_tailwind_score", 0) <= 0.33,
        "evidence_fn": lambda ctx: [
            f"Macro tailwind: {ctx.get('macro_tailwind_score', 0):.0%}",
            "USD strong" if not ctx.get("macro_components", {}).get("usd_down") else None,
            "Oil weak" if not ctx.get("macro_components", {}).get("crude_up") else None
        ],
        "priority": 1
    },

    # 流量特徵
    "funds_back_buying": {
        "label": "Funds Back & Buying",
        "condition": lambda ctx: (
            ctx.get("flow_reversal") == "positive" and
            ctx.get("firepower_total", 0) > 0.5
        ),
        "evidence_fn": lambda ctx: [
            "Flow reversed to positive",
            f"Firepower: {ctx.get('firepower_total', 0):.0%}"
        ],
        "priority": 1
    },

    "crowded_long": {
        "label": "Crowded Long",
        "condition": lambda ctx: ctx.get("firepower_total", 1) < 0.2,
        "evidence_fn": lambda ctx: [
            f"Firepower critically low: {ctx.get('firepower_total', 0):.0%}",
            "Position near historical high"
        ],
        "priority": 1
    },

    "small_holiday_flows": {
        "label": "Small Holiday Flows",
        "condition": lambda ctx: (
            abs(ctx.get("total_flow", 0)) < ctx.get("flow_p25", float("inf"))
        ),
        "evidence_fn": lambda ctx: [
            f"Flow: {ctx.get('total_flow', 0):,} (below 25th percentile)",
            "Likely holiday/thin liquidity"
        ],
        "priority": 3
    },

    # 群組動態
    "broad_based_buying": {
        "label": "Broad-Based Buying",
        "condition": lambda ctx: (
            sum(1 for g in ["grains", "oilseeds", "meats", "softs"]
                if ctx.get(f"{g}_flow", 0) > 0) >= 3
        ),
        "evidence_fn": lambda ctx: [
            f"{g.capitalize()}: +{ctx.get(f'{g}_flow', 0):,}"
            for g in ["grains", "oilseeds", "meats", "softs"]
            if ctx.get(f"{g}_flow", 0) > 0
        ],
        "priority": 2
    }
}
```

---

## 3. 標註生成函數

```python
def generate_annotations(context: dict) -> list:
    """
    根據上下文生成所有觸發的標註

    Parameters:
    -----------
    context : dict
        包含所有指標的上下文字典

    Returns:
    --------
    list
        觸發的標註清單
    """
    annotations = []

    for rule_id, rule in ANNOTATION_RULES.items():
        try:
            if rule["condition"](context):
                evidence = rule["evidence_fn"](context)
                # 過濾 None 值
                evidence = [e for e in evidence if e is not None]

                annotations.append({
                    "label": rule_id,
                    "display": rule["label"],
                    "rule_hit": True,
                    "evidence": evidence,
                    "priority": rule.get("priority", 2),
                    "date": context.get("date")
                })
        except Exception as e:
            # 規則執行失敗時跳過
            continue

    # 按優先級排序（1 最高）
    annotations.sort(key=lambda x: x["priority"])

    return annotations
```

---

## 4. 標註優先級

| 優先級 | 說明                 | 範例                           |
|--------|----------------------|--------------------------------|
| 1      | 核心訊號             | Funds Back & Buying, Crowded   |
| 2      | 重要驅動             | Strong Demand, USDA Stats      |
| 3      | 輔助資訊             | Small Holiday Flows            |

---

## 5. 標註顯示樣式

### 5.1 圖表標註

```python
ANNOTATION_STYLES = {
    "funds_back_buying": {"color": "green", "marker": "^", "size": 12},
    "fund_capitulation": {"color": "darkgreen", "marker": "^", "size": 14},
    "crowded_long": {"color": "red", "marker": "v", "size": 12},
    "extreme_short": {"color": "darkred", "marker": "v", "size": 14},
    "macro_mood_bullish": {"color": "blue", "marker": "o", "size": 10},
    "macro_headwind": {"color": "orange", "marker": "o", "size": 10},
    "strong_corn_demand": {"color": "gold", "marker": "s", "size": 8},
    "bearish_usda_stats": {"color": "brown", "marker": "s", "size": 8},
    "small_holiday_flows": {"color": "gray", "marker": ".", "size": 6}
}
```

### 5.2 Markdown 標註

```python
def format_annotation_markdown(ann: dict) -> str:
    """格式化標註為 Markdown"""
    emoji_map = {
        "funds_back_buying": "🟢",
        "crowded_long": "🔴",
        "macro_mood_bullish": "🔵",
        "strong_corn_demand": "🌽",
        "bearish_usda_stats": "📉",
        "small_holiday_flows": "🏖️"
    }

    emoji = emoji_map.get(ann["label"], "📌")
    evidence_str = ", ".join(ann["evidence"])

    return f"{emoji} **{ann['display']}**: {evidence_str}"
```

---

## 6. 使用範例

```python
# 建立上下文
context = {
    "date": "2026-01-21",
    "total_flow": 65000,
    "grains_flow": 35000,
    "oilseeds_flow": 25000,
    "meats_flow": 5000,
    "softs_flow": 0,
    "firepower_total": 0.63,
    "macro_tailwind_score": 0.67,
    "macro_components": {
        "usd_down": True,
        "crude_up": True,
        "metals_up": False
    },
    "corn_export_surprise": 0.05,
    "flow_reversal": "positive",
    "flow_p25": 20000
}

# 生成標註
annotations = generate_annotations(context)

# 輸出
for ann in annotations:
    print(f"[{ann['priority']}] {ann['display']}: {ann['evidence']}")
```

輸出：
```
[1] Funds Back & Buying: ['Flow reversed to positive', 'Firepower: 63%']
[1] Macro Mood Bullish: ['Macro tailwind: 67%', 'usd_down', 'crude_up']
[2] Strong Corn Demand: ['Corn export surprise: +5.0%', 'Grains flow: +35,000 contracts']
[2] Broad-Based Buying: ['Grains: +35,000', 'Oilseeds: +25,000', 'Meats: +5,000']
```
