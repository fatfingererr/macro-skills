<overview>
Google Trends 訊號分型定義。將搜尋趨勢飆升分類為三種結構性類型，並提供判定邏輯。
</overview>

<signal_types>
**三種訊號類型**

| 類型 | 英文 | 特徵 | 解讀 |
|------|------|------|------|
| 季節性尖峰 | Seasonal Spike | 每年固定月份重複、殘差不高 | 制度性週期 |
| 事件驅動衝擊 | Event-Driven Shock | 短期尖峰、z-score 高、事件詞上升 | 新聞/政策/系統故障 |
| 結構性轉變 | Regime Shift | 變點成立、趨勢線上移 | 長期關注度結構性上升 |
</signal_types>

<seasonal_spike>
**季節性尖峰 (Seasonal Spike)**

**定義：**
週期性重複的搜尋量上升，由制度性因素驅動。

**判定條件：**
```python
def is_seasonal_spike(ts, seasonal_strength, zscore):
    conditions = [
        seasonal_strength > 0.5,      # 強季節性
        abs(zscore) < 2.0,            # 殘差不異常
        has_recurring_pattern(ts)     # 歷史重複
    ]
    return all(conditions)

def has_recurring_pattern(ts, tolerance=0.15):
    """檢查是否每年同期間都有上升"""
    # 計算每年同月份的平均值
    monthly_avg = ts.groupby(ts.index.month).mean()
    peak_months = monthly_avg.nlargest(2).index.tolist()

    # 檢查過去幾年是否在相同月份出現高點
    for year in ts.index.year.unique()[-5:]:
        year_data = ts[ts.index.year == year]
        year_peak_month = year_data.idxmax().month
        if year_peak_month not in peak_months:
            return False
    return True
```

**常見例子：**
- Health Insurance：11-12 月（Open Enrollment）
- Tax：1-4 月（報稅季）
- Christmas：11-12 月（購物季）
- Flu：10-2 月（流感季）

**下一步：**
- 比較今年與歷史同期的分位數
- 若顯著高於歷史同期 95 分位數，可能疊加事件因素
</seasonal_spike>

<event_driven_shock>
**事件驅動衝擊 (Event-Driven Shock)**

**定義：**
由特定事件引發的短期搜尋量飆升。

**判定條件：**
```python
def is_event_shock(zscore, resid, drivers):
    conditions = [
        abs(zscore) >= 2.5,                    # 顯著異常
        is_spike_shape(resid),                 # 尖峰形狀
        has_event_terms(drivers)               # 驅動詞彙含事件詞
    ]
    return sum(conditions) >= 2

def is_spike_shape(resid, window=4):
    """檢查是否為尖峰形狀（快速上升、可能快速下降）"""
    recent = resid.iloc[-window:]
    previous = resid.iloc[-window*2:-window]

    # 近期顯著高於前期
    return recent.mean() > previous.mean() + 2 * previous.std()

def has_event_terms(drivers):
    """檢查驅動詞彙是否含事件相關詞"""
    event_keywords = [
        'announcement', 'breaking', 'news', 'crisis',
        'deadline', 'lawsuit', 'scandal', 'shutdown'
    ]
    for driver in drivers:
        term_lower = driver['term'].lower()
        if any(kw in term_lower for kw in event_keywords):
            return True
    return False
```

**常見例子：**
- 政策公告（Fed 升息、新法案）
- 企業醜聞（資料外洩、財務造假）
- 自然災害（颶風、地震）
- 系統故障（網站當機、服務中斷）

**下一步：**
- 識別具體事件（related queries + 新聞搜尋）
- 評估事件的持續性影響
</event_driven_shock>

<regime_shift>
**結構性轉變 (Regime Shift)**

**定義：**
搜尋量的長期結構性上升，表示關注度發生根本性變化。

**判定條件：**
```python
def is_regime_shift(ts, trend, zscore):
    conditions = [
        abs(zscore) >= 2.0,                    # 異常
        is_trend_elevated(trend),              # 趨勢線上移
        is_sustained(ts)                       # 持續性
    ]
    return all(conditions)

def is_trend_elevated(trend, lookback=52):
    """檢查趨勢線是否上移"""
    recent_trend = trend.iloc[-lookback:].mean()
    historical_trend = trend.iloc[:-lookback].mean()

    # 近期趨勢比歷史高 20% 以上
    return recent_trend > historical_trend * 1.2

def is_sustained(ts, weeks=8):
    """檢查是否持續在高位"""
    recent = ts.iloc[-weeks:]
    historical_75 = ts.iloc[:-weeks].quantile(0.75)

    # 近期大多數時間在歷史 75 分位以上
    return (recent > historical_75).mean() > 0.7
```

**常見例子：**
- 生活成本長期上升（通膨壓力）
- 行業結構性變化（遠端工作、電動車）
- 人口結構變化（老齡化相關搜尋）

**下一步：**
- 識別結構性驅動因素
- 預期這是新常態而非暫時現象
</regime_shift>

<classification_flowchart>
**分類流程圖**

```
              ┌─────────────────┐
              │  原始訊號分析   │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ 季節性分解 (STL) │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    seasonal      trend         residual
         │             │             │
         ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │季節強度>0.5│  │趨勢上移?  │  │殘差異常?  │
  └─────┬────┘  └─────┬────┘  └─────┬────┘
        │             │             │
        ▼             ▼             ▼
   ┌────────────────────────────────────┐
   │          訊號分類決策              │
   └────────────────────────────────────┘
        │             │             │
        ▼             ▼             ▼
   Seasonal      Regime        Event
    Spike         Shift        Shock
```
</classification_flowchart>

<classification_logic>
**分類邏輯代碼**

```python
def classify_signal(
    is_ath: bool,
    is_anomaly: bool,
    seasonal_strength: float,
    trend: pd.Series,
    resid: pd.Series,
    drivers: list
) -> str:
    """
    分類訊號類型

    Returns:
        "seasonal_spike" | "event_driven_shock" | "regime_shift" | "normal"
    """

    # 1. 檢查季節性尖峰
    if seasonal_strength > 0.5 and not is_anomaly:
        return "seasonal_spike"

    # 2. 檢查結構性轉變
    if is_ath and is_anomaly:
        recent_trend = trend.iloc[-52:].mean()
        historical_trend = trend.iloc[:-52].mean()

        if recent_trend > historical_trend * 1.2:
            # 趨勢線上移且持續
            recent_above_p75 = (resid.iloc[-8:] > resid.quantile(0.75)).mean()
            if recent_above_p75 > 0.7:
                return "regime_shift"

    # 3. 檢查事件驅動衝擊
    if is_anomaly:
        # 尖峰形狀或事件詞彙
        if is_spike_shape(resid) or has_event_terms(drivers):
            return "event_driven_shock"

    # 4. 其他異常但未分類
    if is_anomaly:
        return "event_driven_shock"  # 預設為事件驅動

    return "normal"
```
</classification_logic>

<signal_implications>
**訊號類型的含義**

| 類型 | 投資/交易含義 | 宏觀含義 | 行動建議 |
|------|--------------|----------|----------|
| Seasonal | 預期內波動，可交易季節性 | 制度運作正常 | 等待季節結束 |
| Event | 短期機會/風險 | 需評估事件持續性 | 識別事件、評估影響 |
| Regime | 長期趨勢變化 | 結構性轉變 | 調整長期觀點 |
</signal_implications>
