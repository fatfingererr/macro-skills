# Workflow: 監控模式

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md - 了解冰山/下沉事件定義
2. references/data-sources.md - 數據來源與更新頻率
</required_reading>

<process>

## Step 1: 確認監控配置

```python
monitor_config = {
    "check_interval": "daily",        # 檢查頻率
    "alert_on_iceberg": True,         # 冰山事件警報
    "alert_on_sinking": True,         # 下沉事件警報
    "alert_on_switch": True,          # 切換事件警報
    "alert_threshold_change": 0.1,    # 指標變化警報門檻
    "lookback_periods": 3             # 回看期數
}
```

## Step 2: 抓取最新數據

```bash
python scripts/fetch_data.py \
  --leading T10Y3M,T10Y2Y,PERMIT,ACDGNO,UMCSENT \
  --coincident PAYEMS,INDPRO,W875RX1,CMRMTSPL \
  --prices SPY,TLT \
  --start 2020-01-01 \
  --latest
```

**注意**：宏觀數據有 1-2 個月發布延遲，最新數據點可能是上月或前月。

## Step 3: 計算當前狀態

```python
from scripts.rotator import get_current_state

state = get_current_state(
    leading_series=leading_config,
    coincident_series=coincident_config,
    iceberg_threshold=-0.3,
    sinking_threshold=-0.5
)

# state 包含：
# - current_state: "RISK_ON" 或 "RISK_OFF"
# - LeadingIndex: 最新值
# - CoincidentIndex: 最新值
# - iceberg_event: bool
# - sinking_event: bool
# - dL: 領先指標變化
# - dC: 同時指標變化
# - confirm_count: 當前確認計數
```

## Step 4: 檢查警報條件

```python
alerts = []

# 冰山事件警報
if state["iceberg_event"] and not previous_state.get("iceberg_event"):
    alerts.append({
        "type": "ICEBERG_DETECTED",
        "message": f"領先指標跌破門檻: LeadingIndex = {state['LeadingIndex']:.2f}",
        "severity": "WARNING"
    })

# 下沉事件警報
if state["sinking_event"] and not previous_state.get("sinking_event"):
    alerts.append({
        "type": "SINKING_DETECTED",
        "message": f"同時指標跌破門檻: CoincidentIndex = {state['CoincidentIndex']:.2f}",
        "severity": "CRITICAL"
    })

# 狀態切換警報
if state["current_state"] != previous_state.get("current_state"):
    alerts.append({
        "type": "STATE_SWITCH",
        "message": f"狀態切換: {previous_state.get('current_state')} → {state['current_state']}",
        "severity": "ACTION_REQUIRED"
    })

# 指標大幅變化警報
if abs(state["dL"]) > monitor_config["alert_threshold_change"]:
    alerts.append({
        "type": "LEADING_INDEX_MOVE",
        "message": f"領先指標大幅變化: ΔL = {state['dL']:.2f}",
        "severity": "INFO"
    })
```

## Step 5: 輸出監控報告

```json
{
  "timestamp": "2026-01-15T10:00:00Z",
  "current_state": "RISK_ON",
  "indices": {
    "LeadingIndex": 0.41,
    "CoincidentIndex": 0.22,
    "dL": 0.05,
    "dC": 0.02
  },
  "events": {
    "iceberg": false,
    "sinking": false
  },
  "confirm_status": {
    "iceberg_confirm_count": 0,
    "recovery_confirm_count": 0
  },
  "alerts": [],
  "next_check": "2026-01-16T10:00:00Z"
}
```

## Step 6: 儲存狀態

將當前狀態儲存供下次比較：

```python
save_state(state, "monitor_state.json")
```

</process>

<alert_severity_levels>
| 級別 | 說明 | 建議行動 |
|------|------|----------|
| INFO | 資訊通知 | 記錄，無需行動 |
| WARNING | 預警 | 關注，準備行動 |
| CRITICAL | 嚴重 | 高度關注，考慮行動 |
| ACTION_REQUIRED | 需行動 | 立即執行切換操作 |
</alert_severity_levels>

<success_criteria>
監控完成時應產出：

- [ ] 當前狀態（RISK_ON/RISK_OFF）
- [ ] 最新指標值與變化
- [ ] 冰山/下沉事件狀態
- [ ] 確認計數
- [ ] 警報清單（若有）
- [ ] 下次檢查時間
</success_criteria>
