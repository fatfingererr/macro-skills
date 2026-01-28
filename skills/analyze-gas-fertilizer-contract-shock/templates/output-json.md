# JSON 輸出結構定義

<overview>
本文件定義 analyze-gas-fertilizer-contract-shock 技能的 JSON 輸出結構。
</overview>

---

## 完整結構

```json
{
  "metadata": {
    "skill_name": "analyze-gas-fertilizer-contract-shock",
    "skill_version": "0.1.0",
    "analysis_timestamp": "2026-01-28T10:30:00Z",
    "parameters": {
      "start_date": "2025-08-01",
      "end_date": "2026-02-01",
      "freq": "1D"
    }
  },

  "series": {
    "natural_gas": {
      "symbol": "natural-gas",
      "source": "TradingEconomics",
      "unit": "USD/MMBtu",
      "data_points": 180,
      "date_range": ["2025-08-01", "2026-01-28"]
    },
    "fertilizer": {
      "symbol": "urea",
      "source": "TradingEconomics",
      "unit": "USD/ton",
      "data_points": 175,
      "date_range": ["2025-08-01", "2026-01-28"]
    }
  },

  "detections": {
    "gas_shock_regimes": [
      {
        "start": "2026-01-12",
        "end": "2026-01-29",
        "peak_date": "2026-01-29",
        "peak_value": 6.95,
        "start_value": 3.75,
        "regime_return_pct": 85.4,
        "duration_days": 18,
        "max_z_score": 4.2,
        "max_slope_pct_per_day": 2.1
      }
    ],
    "fert_spike_regimes": [
      {
        "start": "2026-01-20",
        "end": "2026-02-01",
        "peak_date": "2026-01-31",
        "peak_value": 420.0,
        "start_value": 344.0,
        "regime_return_pct": 22.1,
        "duration_days": 13,
        "max_z_score": 3.5,
        "max_slope_pct_per_day": 1.8
      }
    ]
  },

  "lead_lag_test": {
    "method": "corr_returns",
    "max_lag_days": 60,
    "best_lag_days_gas_leads_fert": 12,
    "best_corr": 0.41,
    "corr_at_zero_lag": 0.25,
    "reasonable_lag_range": [7, 56],
    "in_reasonable_range": true,
    "interpretation": "天然氣報酬領先化肥報酬約 12 天，相關係數為中度"
  },

  "three_part_test": {
    "A_gas_shock": {
      "pass": true,
      "regime_count": 1,
      "max_return_pct": 85.4,
      "total_days": 18
    },
    "B_fert_follows": {
      "pass": true,
      "fert_start_after_gas_start": true,
      "lag_days": 8,
      "explanation": "化肥 spike 起點（2026-01-20）晚於天然氣 shock 起點（2026-01-12）約 8 天"
    },
    "C_lead_lag_supports": {
      "pass": true,
      "lag_in_range": true,
      "corr_significant": true,
      "explanation": "best_lag=12 在合理範圍 [7,56] 內，相關係數 0.41 為中度"
    }
  },

  "signal": "narrative_supported",
  "confidence": "medium",

  "narrative_assessment": {
    "summary": "三段式因果檢驗通過，敘事有量化支撐",
    "details": [
      "天然氣在樣本末端出現明顯 shock regime（z-score/斜率同時觸發）",
      "化肥在天然氣 shock 後約 1-3 週出現 spike regime，時序關係符合預期",
      "交叉相關顯示 gas 報酬領先 fert 報酬約 12 天，達到中度相關",
      "僅憑價格無法證明 force majeure/毀約，但可提供敘事的時間序列支持度"
    ],
    "alternative_explanations": [
      "化肥 spike 可能還受其他因素影響（運費、需求、政策）",
      "相關係數 0.41 為中度，部分變異來自其他驅動因素"
    ]
  },

  "hedge_proxy": {
    "enabled": false,
    "contract_price": null,
    "unit": null,
    "peak_proxy": null,
    "interpretation": null
  },

  "artifacts": {
    "data_files": [
      "data/natural_gas.csv",
      "data/urea.csv",
      "data/analysis_result.json"
    ],
    "charts": [
      "output/gas_fert_shock_2026-01-28.png"
    ]
  },

  "caveats": [
    "數據來源為 TradingEconomics，可能與交易所官方數據有差異",
    "日頻數據可能有缺失，已使用 forward-fill 處理",
    "相關不代表因果，需配合機制分析",
    "本分析不構成任何投資建議"
  ]
}
```

---

## 欄位說明

### metadata

| 欄位 | 類型 | 說明 |
|------|------|------|
| skill_name | string | 技能名稱 |
| skill_version | string | 技能版本 |
| analysis_timestamp | string | 分析時間（ISO 8601） |
| parameters | object | 輸入參數快照 |

### series

每個商品包含：

| 欄位 | 類型 | 說明 |
|------|------|------|
| symbol | string | 商品代碼 |
| source | string | 數據來源 |
| unit | string | 價格單位 |
| data_points | int | 數據筆數 |
| date_range | array | 日期範圍 [start, end] |

### detections.gas_shock_regimes / fert_spike_regimes

| 欄位 | 類型 | 說明 |
|------|------|------|
| start | string | Regime 起始日 |
| end | string | Regime 結束日 |
| peak_date | string | 峰值日期 |
| peak_value | float | 峰值價格 |
| start_value | float | 起始價格 |
| regime_return_pct | float | Regime 內漲幅（%） |
| duration_days | int | 持續天數 |
| max_z_score | float | 最大 z-score |
| max_slope_pct_per_day | float | 最大斜率（%/day） |

### lead_lag_test

| 欄位 | 類型 | 說明 |
|------|------|------|
| method | string | 計算方法 |
| max_lag_days | int | 最大 lag 搜尋範圍 |
| best_lag_days_gas_leads_fert | int | 最佳 lag（正=gas 領先） |
| best_corr | float | 最大相關係數 |
| corr_at_zero_lag | float | 零 lag 相關係數 |
| reasonable_lag_range | array | 合理領先期範圍 |
| in_reasonable_range | bool | 是否在合理範圍內 |
| interpretation | string | 文字解讀 |

### three_part_test

三段式檢驗結果：

| 欄位 | 類型 | 說明 |
|------|------|------|
| A_gas_shock.pass | bool | A 段是否通過 |
| B_fert_follows.pass | bool | B 段是否通過 |
| C_lead_lag_supports.pass | bool | C 段是否通過 |

### signal

| 值 | 說明 |
|-----|------|
| `"narrative_supported"` | 敘事有量化支撐 |
| `"narrative_weak"` | 敘事較弱 |
| `"inconclusive"` | 無法判斷 |

### confidence

| 值 | 條件 |
|-----|------|
| `"high"` | 三段皆通過 + corr > 0.5 |
| `"medium"` | 三段皆通過 + 0.3 < corr <= 0.5 |
| `"low"` | 部分通過或 corr <= 0.3 |

---

## 精簡輸出（Quick Check）

```json
{
  "check_date": "2026-01-28",
  "lookback_days": 180,
  "gas_status": {
    "current_z": 2.1,
    "is_shock": false,
    "recent_shock": {
      "exists": true,
      "last_date": "2026-01-29",
      "days_ago": 0
    }
  },
  "fert_status": {
    "current_z": 1.5,
    "is_spike": false,
    "recent_spike": {
      "exists": true,
      "last_date": "2026-01-31",
      "days_ago": 0
    }
  },
  "quick_assessment": "gas_shock_recent_fert_following",
  "recommendation": "建議執行完整分析以驗證因果關係"
}
```
