# JSON 輸出模板

## 完整輸出結構

```json
{
  "skill": "detect-palladium-lead-silver-turns",
  "symbol_pair": {
    "silver": "SI=F",
    "palladium": "PA=F"
  },
  "as_of": "2026-01-14",
  "timeframe": "1h",
  "lookback_bars": 1200,

  "data_range": {
    "start": "2025-01-01",
    "end": "2026-01-14",
    "trading_bars": 1180,
    "missing_bars": 20
  },

  "summary": {
    "estimated_pd_leads_by_bars": 6,
    "lead_lag_corr": 0.42,
    "lead_lag_confidence_interval": [3, 9],
    "confirmation_rate": 0.71,
    "unconfirmed_failure_rate": 0.64,
    "total_ag_turns": 24,
    "confirmed_turns": 17,
    "unconfirmed_turns": 7,
    "failed_moves": 5
  },

  "lead_lag_analysis": {
    "best_lag": 6,
    "correlation": 0.42,
    "p_value": 0.002,
    "is_significant": true,
    "stability": {
      "rolling_windows": [
        {"period": "2025-Q1", "lag": 5, "corr": 0.38},
        {"period": "2025-Q2", "lag": 7, "corr": 0.45},
        {"period": "2025-Q3", "lag": 6, "corr": 0.41},
        {"period": "2025-Q4", "lag": 6, "corr": 0.44}
      ],
      "is_stable": true,
      "lag_std": 0.8,
      "corr_std": 0.03
    }
  },

  "confirmation_analysis": {
    "by_type": {
      "top": {"total": 12, "confirmed": 8, "rate": 0.67},
      "bottom": {"total": 12, "confirmed": 9, "rate": 0.75}
    },
    "confirmation_lag_distribution": {
      "mean": -2.3,
      "median": -3,
      "std": 1.8,
      "min": -6,
      "max": 4
    }
  },

  "failure_analysis": {
    "rule_used": "no_confirm_then_revert",
    "unconfirmed_events": 7,
    "failed_moves": 5,
    "unconfirmed_failure_rate": 0.71,
    "confirmed_failure_rate": 0.18,
    "failure_rate_ratio": 3.94,
    "average_revert_bars": {
      "unconfirmed": 8.2,
      "confirmed": 15.6
    }
  },

  "events": [
    {
      "ts": "2026-01-08T10:00:00Z",
      "idx": 1150,
      "turn": "bottom",
      "ag_price": 29.85,
      "confirmed": true,
      "confirmation_lag_bars": -3,
      "pd_turn_ts": "2026-01-08T07:00:00Z",
      "pd_turn_price": 1025.50,
      "participation_ok": true,
      "participation_score": 0.72,
      "failed_move": false,
      "subsequent_move_pct": 2.3
    },
    {
      "ts": "2026-01-15T14:00:00Z",
      "idx": 1195,
      "turn": "top",
      "ag_price": 30.50,
      "confirmed": false,
      "confirmation_lag_bars": null,
      "pd_turn_ts": null,
      "pd_turn_price": null,
      "participation_ok": false,
      "participation_score": 0.35,
      "failed_move": true,
      "subsequent_move_pct": -1.8
    }
  ],

  "latest_event": {
    "ts": "2026-01-15T14:00:00Z",
    "turn": "top",
    "confirmed": false,
    "participation_ok": false,
    "failed_move": true
  },

  "interpretation": {
    "regime_assessment": "鈀金在本回溯窗口內對白銀報酬的最佳領先滯後為 +6 bars（鈀金先動）。未被鈀金確認的白銀拐點事件，其後續回撤/回到區間的比例顯著較高。",
    "current_status": "當前白銀頂部未被鈀金確認，視為流動性噪音的可能性較高。",
    "tactics": [
      "避免基於未確認拐點進行方向性交易",
      "等待下一個被鈀金確認的拐點再決策",
      "若已有部位，可暫時觀望而非立即調整",
      "注意後續 10 根 K 內的價格走勢以驗證失敗判定"
    ]
  },

  "risk_metrics": {
    "confirmation_reliability": "high",
    "lead_lag_stability": "stable",
    "current_regime": "normal"
  },

  "metadata": {
    "generated_at": "2026-01-15T15:00:00Z",
    "parameters": {
      "turn_method": "pivot",
      "pivot_left": 3,
      "pivot_right": 3,
      "confirm_window_bars": 6,
      "lead_lag_max_bars": 24,
      "participation_metric": "direction_agree",
      "participation_threshold": 0.6,
      "failure_rule": "no_confirm_then_revert"
    },
    "data_source": "yfinance",
    "version": "0.1.0"
  }
}
```

---

## 精簡輸出（--quick 模式）

```json
{
  "skill": "detect-palladium-lead-silver-turns",
  "symbol_pair": {"silver": "SI=F", "palladium": "PA=F"},
  "as_of": "2026-01-14",
  "timeframe": "1h",
  "summary": {
    "estimated_pd_leads_by_bars": 6,
    "lead_lag_corr": 0.42,
    "confirmation_rate": 0.71,
    "unconfirmed_failure_rate": 0.64
  },
  "latest_event": {
    "ts": "2026-01-15T14:00:00Z",
    "turn": "top",
    "confirmed": false,
    "participation_ok": false,
    "failed_move": true
  }
}
```

---

## 回測輸出

```json
{
  "skill": "detect-palladium-lead-silver-turns",
  "mode": "backtest",
  "symbol_pair": {"silver": "SI=F", "palladium": "PA=F"},
  "timeframe": "1h",
  "backtest_period": {
    "start": "2024-01-01",
    "end": "2026-01-01",
    "total_bars": 4800
  },

  "lead_lag_analysis": {
    "best_lag": 6,
    "correlation": 0.42,
    "confidence_interval": [3, 9],
    "stability": {
      "is_stable": true,
      "lag_std": 0.8
    }
  },

  "confirmation_analysis": {
    "total_ag_turns": 96,
    "confirmed_turns": 68,
    "confirmation_rate": 0.71,
    "by_type": {
      "top": {"total": 48, "confirmed": 32, "rate": 0.67},
      "bottom": {"total": 48, "confirmed": 36, "rate": 0.75}
    }
  },

  "failure_analysis": {
    "unconfirmed_failure_rate": 0.64,
    "confirmed_failure_rate": 0.18,
    "failure_rate_ratio": 3.56
  },

  "conclusion": {
    "is_effective": true,
    "effectiveness_score": 0.78,
    "recommendation": "跨金屬確認邏輯有效，可用於交易過濾"
  }
}
```

---

## 監控告警輸出

```json
{
  "alert_type": "unconfirmed",
  "timestamp": "2026-01-15T14:00:00Z",
  "priority": "high",
  "message": "白銀出現頂部拐點，但鈀金在確認窗口內未出現同向拐點",
  "details": {
    "ag_turn": {
      "ts": "2026-01-15T14:00:00Z",
      "type": "top",
      "price": 30.50
    },
    "pd_status": "no_matching_turn",
    "window_checked": [-6, 6],
    "participation_score": 0.35
  },
  "suggested_action": "視為流動性噪音，謹慎應對",
  "next_check": "2026-01-15T15:00:00Z"
}
```

---

## 欄位說明

### summary

| 欄位                       | 類型  | 說明                       |
|----------------------------|-------|----------------------------|
| estimated_pd_leads_by_bars | int   | 鈀金領先白銀的 K 棒數      |
| lead_lag_corr              | float | 領先滯後的相關係數         |
| confirmation_rate          | float | 白銀拐點被確認的比例       |
| unconfirmed_failure_rate   | float | 未確認事件的失敗比例       |

### events[]

| 欄位                | 類型    | 說明                       |
|---------------------|---------|----------------------------|
| ts                  | string  | 拐點時間戳                 |
| turn                | string  | 拐點類型（top/bottom）     |
| confirmed           | bool    | 是否被鈀金確認             |
| confirmation_lag_bars| int    | 確認滯後（正值=鈀金先）    |
| participation_ok    | bool    | 參與度是否達標             |
| failed_move         | bool    | 是否判定為失敗走勢         |

### interpretation

| 欄位             | 類型     | 說明                       |
|------------------|----------|----------------------------|
| regime_assessment| string   | 當前行情評估               |
| current_status   | string   | 最新事件狀態               |
| tactics          | string[] | 可操作建議                 |
