<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/seasonality-guide.md - 季節性分解方法
3. references/signal-types.md - 訊號分型定義
4. references/data-sources.md - Selenium 爬取方式與防偵測策略
</required_reading>

<objective>
深度分析 Google Trends 訊號，進行訊號分型，並提取 related queries 作為驅動詞彙參考。
使用 Selenium 模擬真人瀏覽器行為，避免被 Google 偵測。
</objective>

<prerequisites>
**環境準備：**

```bash
# 安裝依賴
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

確保系統已安裝 Chrome 瀏覽器。

**注意：** 深度分析包含 related queries 抓取，會發送較多請求。
建議在非高峰時段執行，避免觸發速率限制。
</prerequisites>

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
  anomaly_method: "zscore"   # zscore|mad
  anomaly_threshold: 2.5
  related_queries: true      # 深度分析建議啟用

  # 可選
  compare_terms: ["Unemployment", "Inflation", "Medicare"]
  headless: true             # 隱藏瀏覽器
  debug: false               # 調試模式
```

**Step 2: 使用 trend_fetcher.py 抓取數據**

```python
from scripts.trend_fetcher import fetch_trends, analyze_ath

# 抓取主題趨勢（Selenium 模擬瀏覽器）
data = fetch_trends(
    topic="Health Insurance",
    geo="US",
    timeframe="2004-01-01 2025-12-31",
    headless=True
)

# 執行完整分析（含 related queries）
# 注意：這會額外發送一個請求抓取 related queries
result = analyze_ath(data, threshold=2.5, include_related=True)
```

或使用 CLI：

```bash
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --geo US \
  --timeframe "2004-01-01 2025-12-31" \
  --threshold 2.5 \
  --output ./output/health_insurance.json
```

**Step 3: 解讀分析結果**

分析結果包含以下關鍵欄位：

```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "timeframe": "2004-01-01 2025-12-31",
  "analysis": {
    "latest_value": 100,
    "latest_date": "Dec 2025",
    "historical_max": 100,
    "historical_max_date": "Dec 2025",
    "historical_min": 12,
    "mean": 45.23,
    "std": 15.67,
    "zscore": 3.1,
    "is_all_time_high": true,
    "is_anomaly": true,
    "signal_type": "regime_shift",
    "trend_direction": "rising",
    "data_points": 252
  },
  "drivers_from_related_queries": [
    {"term": "obamacare", "type": "rising", "value": "+450%"},
    {"term": "aca enrollment", "type": "rising", "value": "+320%"},
    {"term": "health insurance marketplace", "type": "top", "value": 100}
  ],
  "recommendation": "搜尋趨勢創下歷史新高且異常飆升，建議進一步分析驅動因素",
  "analyzed_at": "2025-12-15T10:30:00"
}
```

**Step 4: 訊號分型判讀**

根據 `signal_type` 判讀：

| signal_type | 特徵 | 解讀建議 |
|-------------|------|----------|
| seasonal_spike | ATH 但低異常分數 | 檢查是否為固定月份（投保季、報稅季） |
| event_driven_shock | 高 z-score、短期尖峰 | 檢查 related queries 尋找事件詞 |
| regime_shift | ATH + 異常 + 上升趨勢 | 結構性變化，關注長期趨勢 |
| normal | 低異常分數 | 正常波動範圍 |

**Step 5: Related Queries 驅動分析**

從 `drivers_from_related_queries` 識別驅動因素：

- **Rising queries**：上升中的搜尋詞，揭示「為什麼」
  - `+N%`：上升百分比
  - `Breakout`：上升超過 5000%（新興熱點）

- **Top queries**：最常搜尋的相關詞
  - 反映主題的常態關聯

**Step 6: 組裝深度分析報告**

```python
def interpret_signal_type(signal_type):
    interpretations = {
        "regime_shift": "結構性上升，搜尋關注度持續攀升，可能反映長期趨勢變化",
        "event_driven_shock": "短期事件衝擊，可能由新聞/政策/突發事件驅動",
        "seasonal_spike": "季節性尖峰，可能為固定週期（如投保季、報稅季）",
        "normal": "正常波動，無異常訊號"
    }
    return interpretations.get(signal_type, "未知訊號類型")

def extract_key_drivers(drivers):
    rising = [d for d in drivers if d.get("type") == "rising"]
    top = [d for d in drivers if d.get("type") == "top"]
    return {
        "rising_drivers": [d["term"] for d in rising[:5]],
        "top_related": [d["term"] for d in top[:3]]
    }

report = {
    "summary": {
        "topic": result["topic"],
        "is_ath": result["analysis"]["is_all_time_high"],
        "signal_type": result["analysis"]["signal_type"],
        "anomaly_score": result["analysis"]["zscore"]
    },
    "interpretation": interpret_signal_type(result["analysis"]["signal_type"]),
    "key_drivers": extract_key_drivers(result.get("drivers_from_related_queries", [])),
    "recommendation": result.get("recommendation", "")
}
```
</process>

<interpretation_guide>
**訊號解讀指南**

| 情境 | 訊號組合 | 解讀 |
|------|----------|------|
| 投保季高點 | seasonal_spike + 11-12月 | 正常季節性，無需過度關注 |
| 政策公告 | event_driven_shock + 政策相關 queries | 短期政策影響，觀察持續性 |
| 長期焦慮上升 | regime_shift + 經濟相關 queries | 結構性變化，可能反映宏觀環境 |
</interpretation_guide>

<success_criteria>
此工作流程成功完成時：
- [ ] Selenium 成功啟動並抓取數據
- [ ] 成功抓取 Google Trends 時間序列
- [ ] 判定訊號類型
- [ ] 提取驅動詞彙（related queries）
- [ ] 輸出符合 templates/output-schema.yaml
- [ ] 提供清晰的解讀建議
</success_criteria>

<output_example>
見 examples/health_insurance_ath.json
</output_example>

<anti_detection_notes>
**防偵測注意事項**

深度分析會發送多個請求（時間序列 + related queries），請注意：

1. **請求間隔**：腳本已內建隨機延遲（1-3 秒）
2. **避免頻繁執行**：建議間隔 5 分鐘以上
3. **若被封鎖**：等待 24 小時或更換 IP
4. **減少請求**：使用 `--no-related` 跳過 related queries

```bash
# 僅抓取時間序列（較快、較少請求）
python scripts/trend_fetcher.py --topic "Health Insurance" --no-related
```
</anti_detection_notes>
