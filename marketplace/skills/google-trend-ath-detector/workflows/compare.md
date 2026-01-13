<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 了解輸入參數
2. references/signal-types.md - 了解訊號分型
3. references/data-sources.md - 了解宏觀數據來源
</required_reading>

<objective>
比較多個主題的 Google Trends 趨勢，識別共振模式，區分「單點焦慮」與「系統性焦慮」。
</objective>

<use_cases>
**適用場景：**

1. 「Health Insurance 上升是因為整體經濟焦慮，還是醫療特定問題？」
2. 「多個經濟相關搜尋是否同時上升？」
3. 「這個訊號是孤立現象還是更廣泛趨勢的一部分？」
</use_cases>

<process>
**Step 1: 確認比較參數**

```yaml
parameters:
  primary_topic: "主要分析主題"
  compare_topics: ["對照主題1", "對照主題2", "對照主題3"]
  geo: "US"
  timeframe: "2019-01-01 2025-12-31"
  granularity: "weekly"

  # 分析選項
  correlation_window: 52  # 計算相關性的窗口（週數）
  lag_analysis: true      # 是否分析領先/滯後關係
  max_lag_weeks: 8        # 最大滯後週數
```

**Step 2: 抓取所有主題數據**

```python
# 主題
primary_ts = fetch_trends(primary_topic, geo, timeframe)

# 對照主題
compare_data = {}
for topic in compare_topics:
    compare_data[topic] = fetch_trends(topic, geo, timeframe)

# 對齊時間索引
all_data = pd.DataFrame({primary_topic: primary_ts})
for topic, ts in compare_data.items():
    all_data[topic] = ts

all_data = all_data.dropna()
```

**Step 3: 相關性分析**

```python
def compute_correlations(all_data, primary_topic):
    """計算主題間的相關性"""

    correlations = {}
    for col in all_data.columns:
        if col != primary_topic:
            # 整體相關性
            corr = all_data[primary_topic].corr(all_data[col])

            # 近期相關性（最近 52 週）
            recent_corr = all_data[primary_topic].iloc[-52:].corr(
                all_data[col].iloc[-52:]
            )

            correlations[col] = {
                "overall_correlation": round(corr, 3),
                "recent_correlation": round(recent_corr, 3),
                "correlation_change": round(recent_corr - corr, 3)
            }

    return correlations
```

**Step 4: 領先/滯後分析**

```python
def lag_analysis(primary_ts, compare_ts, max_lag=8):
    """分析領先滯後關係"""

    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # compare_ts 領先
            shifted = compare_ts.shift(-lag)
        else:
            # primary_ts 領先
            shifted = compare_ts.shift(lag)

        corr = primary_ts.corr(shifted)
        results.append({"lag": lag, "correlation": round(corr, 3)})

    # 找最佳滯後
    best = max(results, key=lambda x: abs(x['correlation']))

    return {
        "all_lags": results,
        "best_lag": best['lag'],
        "best_correlation": best['correlation'],
        "interpretation": interpret_lag(best['lag'])
    }

def interpret_lag(lag):
    if lag == 0:
        return "同步移動"
    elif lag > 0:
        return f"主題領先對照主題 {lag} 週"
    else:
        return f"對照主題領先主題 {-lag} 週"
```

**Step 5: 共振模式識別**

```python
def identify_resonance_pattern(all_data, primary_topic, correlations):
    """識別共振模式"""

    # 計算最近變化的同步性
    recent_changes = {}
    for col in all_data.columns:
        # 計算近 4 週 vs 前 4 週的變化
        recent = all_data[col].iloc[-4:].mean()
        previous = all_data[col].iloc[-8:-4].mean()
        change_pct = (recent - previous) / previous if previous > 0 else 0
        recent_changes[col] = change_pct

    # 判斷模式
    primary_change = recent_changes[primary_topic]
    compare_changes = {k: v for k, v in recent_changes.items() if k != primary_topic}

    # 計算同向移動的比例
    same_direction = sum(
        1 for v in compare_changes.values()
        if (v > 0) == (primary_change > 0)
    )
    same_direction_ratio = same_direction / len(compare_changes)

    if same_direction_ratio >= 0.7:
        pattern = "systemic_anxiety"
        explanation = "多數對照主題同向移動，表示系統性焦慮"
    elif same_direction_ratio <= 0.3:
        pattern = "isolated_signal"
        explanation = "主題獨立移動，表示單點焦慮或特定事件"
    else:
        pattern = "mixed_signal"
        explanation = "混合訊號，需進一步分析"

    return {
        "pattern": pattern,
        "same_direction_ratio": round(same_direction_ratio, 2),
        "explanation": explanation,
        "recent_changes": recent_changes
    }
```

**Step 6: 組裝比較報告**

```python
report = {
    "primary_topic": primary_topic,
    "compare_topics": compare_topics,
    "geo": geo,
    "timeframe": timeframe,

    "correlations": correlations,
    "lag_analysis": lag_results if lag_analysis else None,
    "resonance_pattern": resonance,

    "interpretation": {
        "signal_type": resonance['pattern'],
        "explanation": resonance['explanation'],
        "confidence": calculate_confidence(correlations, resonance)
    },

    "implications": generate_implications(resonance['pattern'], primary_topic),

    "next_steps": [
        "如果是 systemic_anxiety：檢查宏觀經濟指標（失業、通膨）",
        "如果是 isolated_signal：深入分析該主題的 related queries",
        "如果是 mixed_signal：擴大對照主題範圍或分段分析"
    ]
}
```
</process>

<pattern_interpretation>
**共振模式解讀：**

| 模式 | 特徵 | 解讀 |
|------|------|------|
| systemic_anxiety | 多個主題同步上升 | 整體經濟焦慮，非單一問題 |
| isolated_signal | 單一主題獨立移動 | 特定事件或政策影響 |
| mixed_signal | 部分同步、部分獨立 | 需細分時間段或擴大樣本 |

**領先滯後解讀：**

| 滯後 | 解讀 |
|------|------|
| 主題領先 | 主題可能是先行指標 |
| 對照領先 | 對照主題可能是驅動因素 |
| 同步 | 共同受第三因素影響 |
</pattern_interpretation>

<success_criteria>
此工作流程成功完成時：
- [ ] 抓取所有主題的時間序列
- [ ] 計算相關性矩陣
- [ ] 完成領先/滯後分析（若啟用）
- [ ] 識別共振模式
- [ ] 給出解讀與下一步建議
</success_criteria>

<example_output>
```json
{
  "primary_topic": "Health Insurance",
  "compare_topics": ["Unemployment", "Inflation", "Medicare"],
  "geo": "US",

  "correlations": {
    "Unemployment": {"overall": 0.45, "recent": 0.62, "change": 0.17},
    "Inflation": {"overall": 0.38, "recent": 0.55, "change": 0.17},
    "Medicare": {"overall": 0.72, "recent": 0.68, "change": -0.04}
  },

  "resonance_pattern": {
    "pattern": "mixed_signal",
    "same_direction_ratio": 0.67,
    "explanation": "Medicare 高度相關但經濟指標近期相關性上升"
  },

  "interpretation": {
    "signal_type": "mixed_signal",
    "explanation": "Health Insurance 搜尋同時受醫療特定因素（Medicare 相關）和經濟焦慮（Unemployment/Inflation 相關性上升）影響"
  }
}
```
</example_output>
