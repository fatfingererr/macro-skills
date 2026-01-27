# Workflow: 週度監控與警報

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md
2. references/data-sources.md
</required_reading>

<process>

## Step 1: 確認 COT 發布時間

CFTC COT 報告發布時間表：
- **截止日**：每週二收盤
- **發布日**：每週五 15:30 ET（美東時間）
- **例外**：遇假日可能延後

```python
from datetime import datetime, timedelta
import pytz

def get_next_cot_release():
    """計算下一次 COT 發布時間"""
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)

    # 找到下一個週五
    days_until_friday = (4 - now.weekday()) % 7
    if days_until_friday == 0 and now.hour >= 16:
        days_until_friday = 7

    next_friday = now + timedelta(days=days_until_friday)
    release_time = next_friday.replace(hour=15, minute=30, second=0)

    return release_time
```

## Step 2: 設定監控排程

建議監控頻率：

| 時間點           | 動作                         |
|------------------|------------------------------|
| 週五 16:00 ET    | 抓取最新 COT 資料            |
| 週五 16:30 ET    | 執行完整分析                 |
| 週一開盤前       | 檢查 Wed-Fri 價格動能        |
| 週中 USDA 發布後 | 交叉驗證基本面               |

```bash
# 設定 cron job 範例（週五 16:00 ET）
0 16 * * 5 cd /path/to/skill && python scripts/analyze_positioning.py --quick --alert
```

## Step 3: 定義警報條件

```python
ALERT_CONDITIONS = {
    # 高優先級警報
    "regime_change": {
        "condition": lambda r: abs(r['flow_total']) > threshold_high and
                               r['prev_flow_total'] * r['flow_total'] < 0,
        "message": "Regime change detected: Flow reversed sign",
        "priority": "high"
    },

    # 中優先級警報
    "firepower_extreme": {
        "condition": lambda r: r['firepower_total'] < 0.15 or
                               r['firepower_total'] > 0.85,
        "message": "Extreme firepower level detected",
        "priority": "medium"
    },

    # 低優先級警報
    "macro_divergence": {
        "condition": lambda r: (r['flow_total'] > 0 and r['macro_score'] < 0.33) or
                               (r['flow_total'] < 0 and r['macro_score'] > 0.67),
        "message": "Macro divergence: Flow and macro signals misaligned",
        "priority": "low"
    }
}
```

## Step 4: 執行監控分析

```bash
python scripts/analyze_positioning.py \
  --mode monitor \
  --lookback-weeks 4 \
  --alert-config config/alert_rules.yaml \
  --output monitor_result.json
```

輸出範例：
```json
{
  "monitor_timestamp": "2026-01-24T16:30:00-05:00",
  "cot_week_end": "2026-01-21",
  "alerts_triggered": [
    {
      "alert_id": "firepower_extreme",
      "priority": "medium",
      "message": "Extreme firepower level detected",
      "details": {
        "firepower_total": 0.12,
        "interpretation": "Crowded long positioning"
      }
    }
  ],
  "week_over_week_changes": {
    "flow_total": {"current": -25, "previous": 58, "change": -83},
    "firepower_total": {"current": 0.12, "previous": 0.18, "change": -0.06}
  }
}
```

## Step 5: 發送通知

支援多種通知管道：

```python
def send_alert(alert_data, channels=['log']):
    """發送警報通知"""
    for channel in channels:
        if channel == 'log':
            log_alert(alert_data)
        elif channel == 'email':
            send_email_alert(alert_data)
        elif channel == 'slack':
            send_slack_alert(alert_data)
        elif channel == 'telegram':
            send_telegram_alert(alert_data)

# 設定檔範例 (config/alert_channels.yaml)
"""
channels:
  - type: log
    path: logs/alerts.log

  - type: slack
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#trading-alerts"

  - type: email
    smtp_server: smtp.gmail.com
    recipients:
      - trader@example.com
"""
```

## Step 6: 歷史比對

監控時自動比對歷史類似情境：

```python
def find_similar_episodes(current_state, history_df, top_n=3):
    """找出歷史上的類似情境"""
    similarity_scores = []

    for date, row in history_df.iterrows():
        # 計算特徵相似度
        features = ['firepower_total', 'macro_score', 'flow_direction']
        score = compute_similarity(current_state, row, features)
        similarity_scores.append((date, score, row))

    # 排序並返回最相似的 N 個
    similar = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[:top_n]

    return [
        {
            "date": str(s[0]),
            "similarity": s[1],
            "subsequent_move": get_subsequent_move(s[0], history_df)
        }
        for s in similar
    ]
```

## Step 7: 生成週報

每週五分析後自動生成週報：

```bash
python scripts/generate_weekly_report.py \
  --result monitor_result.json \
  --template templates/output-markdown.md \
  --output reports/weekly_2026-01-24.md
```

</process>

<success_criteria>
此工作流程完成時應確認：

- [ ] 在 COT 發布後及時執行分析
- [ ] 警報條件正確觸發
- [ ] 通知成功發送至指定管道
- [ ] 週報自動生成
- [ ] 歷史比對提供參考情境
- [ ] 監控日誌完整記錄
</success_criteria>
