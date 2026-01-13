<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/seasonality-guide.md - 季節性分解方法
3. references/hypothesis-templates.md - 假說模板
4. references/data-sources.md - 驗證數據來源
</required_reading>

<objective>
深度分析 Google Trends 訊號，進行季節性分解、訊號分型，並生成可檢驗假說清單。
</objective>

<process>
**Step 1: 確認完整參數**

```yaml
parameters:
  # 必要
  topic: "Health Insurance"
  geo: "US"
  timeframe: "2004-01-01 2025-12-31"

  # 建議
  granularity: "weekly"
  use_topic_entity: true
  smoothing_window: 4
  seasonality_method: "stl"  # none|stl|month_fixed_effects
  anomaly_method: "zscore"   # zscore|mad|changepoint
  anomaly_threshold: 2.5
  related_queries: true

  # 可選
  compare_terms: ["Unemployment", "Inflation", "Medicare"]
  event_calendars: ["open_enrollment", "policy_announcements"]
```

**Step 2: 抓取數據**

```python
# 主題趨勢
ts = fetch_trends(topic, geo, timeframe, granularity, use_topic_entity)

# Related queries
rq = fetch_related_queries(topic, geo, timeframe) if related_queries else None

# 對照主題（可選）
comps = {t: fetch_trends(t, geo, timeframe, granularity, False)
         for t in compare_terms} if compare_terms else {}
```

**Step 3: 平滑處理**

```python
ts_smoothed = ts.rolling(smoothing_window).mean()
```

**Step 4: 季節性分解**

```python
if seasonality_method == "stl":
    from statsmodels.tsa.seasonal import STL

    # 週數據用 period=52，月數據用 period=12
    period = 52 if granularity == "weekly" else 12

    stl = STL(ts_smoothed, period=period, robust=True)
    result = stl.fit()

    trend = result.trend
    seasonal = result.seasonal
    resid = result.resid

    ts_deseasonalized = ts_smoothed - seasonal
    seasonal_strength = 1 - (resid.var() / (seasonal + resid).var())
```

**Step 5: ATH 與異常偵測**

```python
# ATH 判定
latest = float(ts.iloc[-1])
hist_max = float(ts.max())
is_ath = latest >= hist_max

# 異常偵測
if anomaly_method == "zscore":
    mean = resid.mean()
    std = resid.std()
    zscore = (resid.iloc[-1] - mean) / std
    is_anomaly = abs(zscore) >= anomaly_threshold

elif anomaly_method == "mad":
    from scipy.stats import median_abs_deviation
    mad = median_abs_deviation(resid, nan_policy='omit')
    median = resid.median()
    mad_score = (resid.iloc[-1] - median) / mad
    is_anomaly = abs(mad_score) >= anomaly_threshold

elif anomaly_method == "changepoint":
    import ruptures as rpt
    algo = rpt.Pelt(model="rbf").fit(resid.values)
    change_points = algo.predict(pen=10)
    is_anomaly = len(change_points) > 1 and change_points[-2] > len(resid) - 8
```

**Step 6: 訊號分型**

```python
def classify_signal(is_ath, is_anomaly, seasonal_strength, resid):
    """
    分類訊號類型：
    - seasonal_spike: 季節性尖峰
    - event_driven_shock: 事件驅動衝擊
    - regime_shift: 結構性轉變
    """
    if seasonal_strength > 0.5 and not is_anomaly:
        return "seasonal_spike"
    elif is_anomaly and resid.iloc[-4:].mean() < resid.iloc[-1]:
        return "event_driven_shock"
    elif is_ath and is_anomaly:
        # 檢查是否趨勢線上移
        recent_trend = trend.iloc[-12:].mean()
        historical_trend = trend.iloc[:-12].mean()
        if recent_trend > historical_trend * 1.2:
            return "regime_shift"
    return "event_driven_shock" if is_anomaly else "normal"
```

**Step 7: 驅動詞彙提取**

```python
def extract_driver_terms(related_queries):
    """從 related queries 提取驅動詞彙"""
    drivers = []

    if related_queries and 'rising' in related_queries:
        for item in related_queries['rising'].head(10).itertuples():
            drivers.append({
                "term": item.query,
                "type": "rising",
                "value": item.value  # 上升百分比或 "Breakout"
            })

    if related_queries and 'top' in related_queries:
        for item in related_queries['top'].head(5).itertuples():
            drivers.append({
                "term": item.query,
                "type": "top",
                "value": item.value
            })

    return drivers
```

**Step 8: 假說生成**

```python
def build_testable_hypotheses(signal_type, drivers, topic):
    """根據訊號類型與驅動詞彙生成可檢驗假說"""
    hypotheses = []

    # 讀取 references/hypothesis-templates.md 中的模板
    templates = load_hypothesis_templates(topic)

    for template in templates:
        # 檢查驅動詞彙是否符合模板條件
        if matches_template_condition(drivers, template['trigger_terms']):
            hypotheses.append({
                "id": template['id'],
                "hypothesis": template['hypothesis'],
                "evidence_in_trends": find_evidence(drivers, template),
                "verify_with": template['verification_data']
            })

    return hypotheses[:4]  # 最多 4 個假說
```

**Step 9: 組裝輸出**

```python
output = {
    "topic": topic,
    "geo": geo,
    "timeframe": timeframe,
    "granularity": granularity,
    "latest": latest,
    "hist_max": hist_max,
    "is_all_time_high": is_ath,
    "signal_type": signal_type,
    "seasonality": {
        "method": seasonality_method,
        "is_seasonal_pattern_detected": seasonal_strength > 0.3,
        "seasonal_strength": round(seasonal_strength, 2)
    },
    "anomaly_detection": {
        "method": anomaly_method,
        "threshold": anomaly_threshold,
        "latest_score": round(zscore, 2),
        "is_anomaly": is_anomaly
    },
    "drivers_from_related_queries": drivers[:10],
    "testable_hypotheses": hypotheses,
    "next_data_to_pull": collect_verification_data(hypotheses)
}
```
</process>

<success_criteria>
此工作流程成功完成時：
- [ ] 完成季節性分解
- [ ] 判定訊號類型
- [ ] 提取驅動詞彙
- [ ] 生成 2-4 個可檢驗假說
- [ ] 每個假說配對驗證數據來源
- [ ] 輸出符合 templates/output-schema.yaml
</success_criteria>

<output_example>
見 examples/health_insurance_ath.json
</output_example>
