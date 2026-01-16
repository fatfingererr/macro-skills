# Workflow: 持續監控

<required_reading>
**執行前請閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/data-sources.md - 數據更新頻率
</required_reading>

<process>

## Step 1: 設定監控參數

確認以下監控配置：

| 參數                 | 預設值      | 說明                   |
|----------------------|-------------|------------------------|
| silver_symbol        | SI=F        | 白銀標的代碼           |
| palladium_symbol     | PA=F        | 鈀金標的代碼           |
| timeframe            | 1h          | 監控時間尺度           |
| check_interval_min   | 60          | 檢查間隔（分鐘）       |
| alert_on_unconfirmed | true        | 未確認事件是否告警     |
| alert_on_new_turn    | true        | 新拐點是否告警         |

## Step 2: 啟動監控服務

### 方式 A：命令行監控

```bash
cd skills/detect-palladium-lead-silver-turns
python scripts/palladium_lead_silver.py \
  --silver SI=F \
  --palladium PA=F \
  --timeframe 1h \
  --monitor \
  --interval 60
```

### 方式 B：定時任務（cron）

```bash
# 每小時執行一次
0 * * * * cd /path/to/skills/detect-palladium-lead-silver-turns && python scripts/palladium_lead_silver.py --silver SI=F --palladium PA=F --quick --output /tmp/pd_ag_latest.json
```

### 方式 C：Python 腳本整合

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
import json

scheduler = AsyncIOScheduler()

def check_palladium_silver():
    result = subprocess.run([
        'python', 'scripts/palladium_lead_silver.py',
        '--silver', 'SI=F',
        '--palladium', 'PA=F',
        '--quick',
        '--output', '/tmp/pd_ag_latest.json'
    ], capture_output=True, text=True)

    with open('/tmp/pd_ag_latest.json') as f:
        data = json.load(f)

    # 檢查是否需要告警
    if data.get('latest_event', {}).get('failed_move'):
        send_alert(f"白銀拐點未被鈀金確認，可能為失敗走勢")

    if data.get('latest_event', {}).get('turn') and not data.get('latest_event', {}).get('confirmed'):
        send_alert(f"白銀新拐點（{data['latest_event']['turn']}），等待鈀金確認")

# 每 60 分鐘執行，±5 分鐘隨機偏移
scheduler.add_job(
    check_palladium_silver,
    trigger=IntervalTrigger(minutes=60, jitter=300),
    id='pd_ag_monitor'
)

scheduler.start()
```

## Step 3: 設定告警條件

### 告警類型

| 告警類型           | 觸發條件                         | 優先級 |
|--------------------|----------------------------------|--------|
| `new_turn`         | 白銀出現新拐點                   | 中     |
| `unconfirmed`      | 白銀拐點在窗口內未被確認         | 高     |
| `failed_move`      | 未確認 + 符合失敗走勢規則        | 高     |
| `participation_low`| 鈀金參與度低於門檻               | 中     |
| `regime_change`    | 領先滯後關係發生結構性變化       | 高     |

### 告警輸出格式

```json
{
  "alert_type": "unconfirmed",
  "timestamp": "2026-01-15T14:00:00Z",
  "message": "白銀出現頂部拐點，但鈀金在確認窗口內未出現同向拐點",
  "details": {
    "ag_turn": {"ts": "2026-01-15T14:00:00Z", "type": "top", "price": 30.50},
    "pd_status": "no_matching_turn",
    "window_checked": [-6, 6],
    "suggested_action": "視為流動性噪音，謹慎應對"
  },
  "priority": "high"
}
```

## Step 4: 整合通知渠道

### Telegram 通知

```python
import requests

def send_telegram_alert(message: str, chat_id: str, bot_token: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# 使用
send_telegram_alert(
    f"*白銀拐點告警*\n"
    f"類型: {alert['alert_type']}\n"
    f"時間: {alert['timestamp']}\n"
    f"訊息: {alert['message']}",
    chat_id=TELEGRAM_CHAT_ID,
    bot_token=TELEGRAM_BOT_TOKEN
)
```

### Discord Webhook

```python
import requests

def send_discord_alert(message: str, webhook_url: str):
    data = {"content": message}
    requests.post(webhook_url, json=data)
```

### Email 通知

```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(subject: str, body: str, to_email: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
```

## Step 5: 監控狀態追蹤

### 狀態文件

```json
{
  "last_check": "2026-01-15T14:00:00Z",
  "last_ag_turn": {
    "ts": "2026-01-15T10:00:00Z",
    "type": "bottom",
    "confirmed": true
  },
  "current_regime": {
    "pd_leads_by": 6,
    "correlation": 0.42,
    "confirmation_rate_7d": 0.75
  },
  "alerts_sent_today": 3,
  "next_check": "2026-01-15T15:00:00Z"
}
```

### 健康檢查

```bash
# 檢查監控服務狀態
python scripts/palladium_lead_silver.py --health-check

# 輸出
{
  "status": "healthy",
  "last_successful_check": "2026-01-15T14:00:00Z",
  "data_freshness": "1 hour ago",
  "next_scheduled_check": "2026-01-15T15:00:00Z"
}
```

## Step 6: 日報生成

每日結束時生成監控日報：

```bash
python scripts/palladium_lead_silver.py \
  --silver SI=F \
  --palladium PA=F \
  --daily-report \
  --date 2026-01-15 \
  --output daily_report_20260115.md
```

日報內容：
1. 當日新拐點列表
2. 確認狀態統計
3. 告警事件匯總
4. 領先滯後關係變化
5. 明日關注點

</process>

<monitoring_best_practices>

## 監控最佳實踐

### 1. 避免告警疲勞

- 設定告警冷卻時間（如同類告警 4 小時內不重複）
- 區分優先級，只對高優先級即時通知
- 低優先級告警批量匯總（如日報）

### 2. 數據新鮮度

| 時間尺度 | 建議檢查間隔 | 數據延遲容忍 |
|----------|--------------|--------------|
| 1h       | 30-60 分鐘   | 15 分鐘      |
| 4h       | 2-4 小時     | 1 小時       |
| 1d       | 每日一次     | 4 小時       |

### 3. 結構性變化監控

除了單次事件，還需監控長期關係變化：
- 滾動 7 日確認率是否下降
- 領先滯後是否發生方向翻轉
- 相關係數是否顯著下降

</monitoring_best_practices>

<success_criteria>
此工作流程完成時應有：

- [ ] 監控服務配置完成
- [ ] 告警條件設定
- [ ] 通知渠道整合
- [ ] 健康檢查機制
- [ ] （可選）日報自動生成
</success_criteria>
