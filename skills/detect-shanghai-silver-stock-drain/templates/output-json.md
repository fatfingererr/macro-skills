# JSON 輸出模板

本文件定義 `detect-shanghai-silver-stock-drain` skill 的 JSON 輸出結構。

---

## 完整輸出結構

```json
{
  "skill": "detect_shanghai_silver_stock_drain",
  "as_of": "2026-01-16",
  "unit": "tonnes",
  "sources": ["SGE", "SHFE"],
  "parameters": {
    "start_date": "2023-01-01",
    "end_date": "2026-01-16",
    "frequency": "weekly",
    "smoothing_window_weeks": 4,
    "z_score_window_weeks": 156,
    "drain_threshold_z": -1.5,
    "accel_threshold_z": 1.0,
    "level_percentile_threshold": 0.20
  },
  "result": {
    "latest_combined_stock": 1133.3,
    "level_percentile": 0.12,
    "delta1_weekly": -58.4,
    "drain_rate_4w_avg": 58.4,
    "acceleration_4w_avg": 9.7,
    "z_scores": {
      "z_drain_rate": -2.1,
      "z_acceleration": 1.4
    },
    "signal_conditions": {
      "A_level_low": true,
      "B_drain_abnormal": true,
      "C_acceleration": true
    },
    "signal": "HIGH_LATE_STAGE_SUPPLY_SIGNAL"
  },
  "historical_context": {
    "decade_high_stock": 3500.2,
    "decade_low_stock": 980.5,
    "current_percentile": 0.12,
    "is_decade_low": false,
    "distance_to_decade_low_pct": 0.156
  },
  "cross_validation": {
    "enabled": true,
    "confidence": 0.67,
    "checks": [
      {
        "indicator": "COMEX Registered",
        "status": "SUPPORT",
        "value": -0.082,
        "detail": "同期下降 8.2%"
      },
      {
        "indicator": "SLV Holdings",
        "status": "NEUTRAL",
        "value": 0.003,
        "detail": "持平 (+0.3%)"
      },
      {
        "indicator": "Futures Structure",
        "status": "SUPPORT",
        "value": "backwardation",
        "detail": "Mild Backwardation"
      }
    ],
    "validated_signal": "HIGH_LATE_STAGE_SUPPLY_SIGNAL"
  },
  "narrative": [
    "上海合併庫存處於歷史低分位（約 12% 分位）。",
    "近 4 週平均庫存流出顯著高於常態（耗盡速度 Z=-2.1）。",
    "流出在加速（加速度 Z=+1.4），符合「方向 + 速度」核心判準。",
    "若同時觀察到其他市場庫存/溢價惡化，可進一步提高信心。"
  ],
  "caveats": [
    "這是「交易所可交割/倉單/指定倉庫」口徑，不等於全中國社會庫存。",
    "單週跳動可能反映倉儲/交割規則變動或搬倉，需用平滑與多來源交叉確認。"
  ],
  "metadata": {
    "generated_at": "2026-01-16T10:30:00Z",
    "skill_version": "0.1.0",
    "data_freshness": {
      "sge_last_update": "2026-01-15",
      "shfe_last_update": "2026-01-16"
    }
  }
}
```

---

## 欄位說明

### 頂層欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| skill | string | 技能名稱 |
| as_of | string | 分析截止日期 |
| unit | string | 輸出單位 |
| sources | array | 使用的庫存來源 |
| parameters | object | 分析參數 |
| result | object | 分析結果 |
| historical_context | object | 歷史脈絡 |
| cross_validation | object | 交叉驗證結果 |
| narrative | array | 中文敘事解讀 |
| caveats | array | 數據口徑說明 |
| metadata | object | 元資料 |

### result 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| latest_combined_stock | float | 最新合併庫存（單位同 unit） |
| level_percentile | float | 庫存水位歷史分位數 (0-1) |
| delta1_weekly | float | 最新週變化量 |
| drain_rate_4w_avg | float | 近 4 週平均流出速度 |
| acceleration_4w_avg | float | 近 4 週平均加速度 |
| z_scores | object | Z 分數 |
| signal_conditions | object | 三段式條件判定 |
| signal | string | 訊號分級 |

### z_scores 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| z_drain_rate | float | 耗盡速度 Z 分數 |
| z_acceleration | float | 加速度 Z 分數 |

### signal_conditions 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| A_level_low | boolean | 條件 A：庫存水位偏低 |
| B_drain_abnormal | boolean | 條件 B：耗盡速度異常 |
| C_acceleration | boolean | 條件 C：耗盡加速 |

### signal 可能值

| 值 | 說明 |
|-----|------|
| HIGH_LATE_STAGE_SUPPLY_SIGNAL | A+B+C 同時成立 |
| MEDIUM_SUPPLY_TIGHTENING | (B+C) 或 (A+B) 成立 |
| WATCH | 任一條件成立 |
| NO_SIGNAL | 無異常 |

### cross_validation 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| enabled | boolean | 是否啟用交叉驗證 |
| confidence | float | 綜合信心度 (0-1) |
| checks | array | 各指標驗證結果 |
| validated_signal | string | 驗證後訊號 |

### checks 陣列元素

| 欄位 | 類型 | 說明 |
|------|------|------|
| indicator | string | 指標名稱 |
| status | string | SUPPORT / NEUTRAL / AGAINST |
| value | any | 指標數值 |
| detail | string | 詳細說明 |

---

## 精簡輸出（--quick 模式）

```json
{
  "skill": "detect_shanghai_silver_stock_drain",
  "as_of": "2026-01-16",
  "signal": "HIGH_LATE_STAGE_SUPPLY_SIGNAL",
  "latest_combined_stock_tonnes": 1133.3,
  "level_percentile": 0.12,
  "z_drain_rate": -2.1,
  "z_acceleration": 1.4
}
```

---

## 程式碼範例

### Python 讀取

```python
import json

with open("result.json", "r", encoding="utf-8") as f:
    result = json.load(f)

# 檢查訊號
if result["result"]["signal"] == "HIGH_LATE_STAGE_SUPPLY_SIGNAL":
    print("⚠️ 高度警戒：晚期供給訊號！")

# 讀取 Z 分數
z_drain = result["result"]["z_scores"]["z_drain_rate"]
print(f"耗盡速度 Z 分數：{z_drain}")

# 讀取敘事
for line in result["narrative"]:
    print(f"• {line}")
```

### jq 查詢

```bash
# 取得訊號
jq '.result.signal' result.json

# 取得 Z 分數
jq '.result.z_scores' result.json

# 取得敘事
jq '.narrative[]' result.json
```
