# Workflow: 持續監控

<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 數據更新頻率
2. references/methodology.md - 指標解讀
</required_reading>

<process>

## Step 1: 監控設定

設定監控參數：

```python
monitor_params = {
    "entities": ["USD", "EUR", "CNY", "JPY", "GBP"],
    "monetary_aggregate": "M0",
    "weighting_method": "fx_turnover",
    "track_metrics": [
        "implied_gold_price_weighted",
        "backing_ratio",
        "lever_multiple"
    ],
    "alert_thresholds": {
        "backing_ratio_change": 0.05,     # 支撐率變化超過 5%
        "gold_reserve_change": 50,        # 黃金儲備變化超過 50 噸
        "implied_price_change": 0.10      # 隱含金價變化超過 10%
    },
    "history_lookback": "1Y",             # 回顧 1 年歷史
    "output_dir": "output/"
}
```

## Step 2: 獲取歷史數據

```python
# 獲取歷史快照（通常季度更新）
history = fetch_historical_snapshots(
    entities=params["entities"],
    start_date=lookback_start,
    end_date="today",
    freq="Q"  # 季度快照
)
```

**數據更新頻率參考**：

| 數據類型 | 更新頻率 | 來源 |
|----------|----------|------|
| 黃金儲備 | 月度/季度 | World Gold Council / IMF |
| M0/M2 | 月度 | 各國央行 / FRED |
| 金價 | 即時 | Yahoo Finance / FRED |
| FX Turnover | 三年 | BIS Triennial |

## Step 3: 計算變化趨勢

```python
def calculate_trends(history):
    trends = {}
    for entity in params["entities"]:
        entity_history = history[entity]

        trends[entity] = {
            "backing_ratio_trend": calculate_trend(
                entity_history["backing_ratio"]
            ),
            "gold_reserve_change": (
                entity_history["gold_tonnes"].iloc[-1] -
                entity_history["gold_tonnes"].iloc[0]
            ),
            "implied_price_trend": calculate_trend(
                entity_history["implied_gold_price_weighted"]
            ),
            "money_growth_rate": calculate_cagr(
                entity_history["money_base"]
            )
        }

    return trends
```

## Step 4: 檢測重大變化

```python
def detect_alerts(trends, thresholds):
    alerts = []

    for entity, trend in trends.items():
        # 黃金儲備大幅變化
        if abs(trend["gold_reserve_change"]) > thresholds["gold_reserve_change"]:
            alerts.append({
                "entity": entity,
                "type": "gold_reserve_change",
                "value": trend["gold_reserve_change"],
                "threshold": thresholds["gold_reserve_change"],
                "message": f"{entity} 黃金儲備變化 {trend['gold_reserve_change']:.0f} 噸"
            })

        # 支撐率大幅變化
        if abs(trend["backing_ratio_trend"]["change"]) > thresholds["backing_ratio_change"]:
            alerts.append({
                "entity": entity,
                "type": "backing_ratio_change",
                "value": trend["backing_ratio_trend"]["change"],
                "threshold": thresholds["backing_ratio_change"],
                "message": f"{entity} 黃金支撐率變化 {trend['backing_ratio_trend']['change']:.1%}"
            })

    return alerts
```

## Step 5: 央行行為追蹤

特別關注央行的黃金買賣行為：

```python
def track_central_bank_activity(history):
    """追蹤各央行的黃金購買/出售行為"""
    activity = []

    for entity in params["entities"]:
        gold_history = history[entity]["gold_tonnes"]
        latest_change = gold_history.iloc[-1] - gold_history.iloc[-2]

        if abs(latest_change) > 5:  # 超過 5 噸的變化
            activity.append({
                "entity": entity,
                "action": "BUY" if latest_change > 0 else "SELL",
                "tonnes": abs(latest_change),
                "date": gold_history.index[-1],
                "interpretation": interpret_cb_action(entity, latest_change)
            })

    return activity
```

## Step 6: 生成監控報告

```python
report = {
    "skill": "usd-reserve-loss-gold-revaluation",
    "mode": "monitor",
    "as_of": "2026-01-07",
    "lookback_period": "1Y",

    "current_snapshot": {
        "headline_implied_price": 39210.0,
        "gold_spot": 2050.0,
        "entity_metrics": current_metrics
    },

    "trends": {
        "headline_change_1y": "+5.2%",
        "avg_backing_ratio_change": "-2.1%",
        "gold_reserve_change_total": "+285 tonnes"
    },

    "alerts": alerts,

    "central_bank_activity": activity,

    "insights": [
        "過去一年中國央行持續增持黃金，累計 +225 噸",
        "日本黃金支撐率持續下降，從 3.5% 降至 3.0%",
        "全球央行淨買入黃金 1050 噸，為連續第 N 年淨買入"
    ],

    "next_update": {
        "gold_reserves": "2026-02-15 (WGC monthly)",
        "bis_survey": "2025 (next triennial)"
    }
}
```

## Step 7: 輸出與通知

```bash
python scripts/gold_revaluation.py \
  --monitor \
  --lookback 1Y \
  --output monitor_report.json
```

可選：設定定期執行

```bash
# cron job 範例（每月執行一次）
0 9 1 * * python /path/to/gold_revaluation.py --monitor >> /var/log/gold_monitor.log
```

</process>

<success_criteria>
監控報告完成時應產出：

- [ ] 當前快照（隱含金價、支撐率）
- [ ] 歷史趨勢（選定週期內的變化）
- [ ] 重大變化警報（若有）
- [ ] 央行行為追蹤
- [ ] 監控洞察（至少 3 點）
- [ ] 下次數據更新時間
</success_criteria>
