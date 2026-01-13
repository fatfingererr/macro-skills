<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 了解輸入參數
2. references/signal-types.md - 了解訊號分型
</required_reading>

<objective>
快速偵測指定主題是否創下 ATH（歷史新高）或出現異常飆升。
</objective>

<process>
**Step 1: 確認參數**

詢問或確認以下必要參數：

```yaml
required:
  topic: "要分析的 Google Trends 主題"
  geo: "地區代碼（如 US, TW, JP）"
  timeframe: "時間範圍（如 2004-01-01 2025-12-31）"

optional:
  granularity: "weekly"  # daily|weekly|monthly
  use_topic_entity: true  # 使用 Topic Entity 避免歧義
  anomaly_threshold: 2.5  # z-score 門檻
```

**Step 2: 抓取 Google Trends 數據**

```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)

# 建立 payload
pytrends.build_payload(
    kw_list=[topic],
    cat=0,
    timeframe=timeframe,
    geo=geo,
    gprop=''
)

# 取得 Interest over time
df = pytrends.interest_over_time()
```

**Step 3: ATH 判定**

```python
latest_value = float(df[topic].iloc[-1])
hist_max = float(df[topic].max())

is_ath = latest_value >= hist_max  # 或 >= hist_max - epsilon
```

**Step 4: 異常分數計算**

```python
from scipy import stats

# 簡單 z-score（若無季節性分解）
mean = df[topic].mean()
std = df[topic].std()
zscore = (latest_value - mean) / std

is_anomaly = zscore >= anomaly_threshold
```

**Step 5: 輸出結果**

```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "latest": 100,
  "hist_max": 100,
  "is_all_time_high": true,
  "zscore": 3.1,
  "is_anomaly": true,
  "recommendation": "建議進行深度分析（analyze workflow）以識別訊號類型與驅動因素"
}
```
</process>

<decision_tree>
**根據結果決定下一步：**

| is_ath | is_anomaly | 建議 |
|--------|------------|------|
| true | true | 確認異常高點，建議 analyze workflow 深度分析 |
| true | false | 可能是季節性高點，建議檢查季節性 |
| false | true | 異常但非 ATH，可能是局部飆升 |
| false | false | 正常波動，無需進一步分析 |
</decision_tree>

<success_criteria>
此工作流程成功完成時：
- [ ] 成功抓取 Google Trends 時間序列
- [ ] 判定 ATH 狀態
- [ ] 計算異常分數
- [ ] 給出下一步建議
</success_criteria>

<error_handling>
**錯誤處理：**

1. **429 Too Many Requests** → 等待後重試，建議使用 VPN 或 proxies
2. **Topic 找不到** → 嘗試用純關鍵字而非 Topic Entity
3. **數據不足** → 縮短時間範圍或改用月度數據
</error_handling>
