# JSON 輸出模板 (Output JSON Template)

## 完整輸出結構

```json
{
  "skill": "zeberg-salomon-rotator",
  "version": "0.1.0",
  "as_of": "2026-01-15",
  "params_used": {
    "start_date": "2000-01-01",
    "end_date": "2026-01-15",
    "freq": "M",
    "equity_proxy": "SPY",
    "bond_proxy": "TLT",
    "iceberg_threshold": -0.3,
    "sinking_threshold": -0.5,
    "confirm_periods": 2,
    "hysteresis": 0.15,
    "rebalance_on": "next_month_open",
    "transaction_cost_bps": 5
  },

  "current_state": {
    "state": "RISK_ON",
    "since": "2023-06-30",
    "months_in_state": 19
  },

  "latest_indices": {
    "LeadingIndex": 0.41,
    "CoincidentIndex": 0.22,
    "dL": 0.05,
    "dC": 0.02,
    "iceberg_event": false,
    "sinking_event": false,
    "distance_to_iceberg": 0.71,
    "distance_to_sinking": 0.72
  },

  "latest_action": null,

  "switch_events": [
    {
      "date": "2000-03-31",
      "action": "EXIT_EQUITY_ENTER_LONG_BOND",
      "from_state": "RISK_ON",
      "to_state": "RISK_OFF",
      "reason": {
        "LeadingIndex": -0.52,
        "CoincidentIndex": 0.05,
        "iceberg": true,
        "sinking": false,
        "euphoria": true,
        "dL": -0.08,
        "confirm_periods_met": 2
      }
    },
    {
      "date": "2003-06-30",
      "action": "EXIT_LONG_BOND_ENTER_EQUITY",
      "from_state": "RISK_OFF",
      "to_state": "RISK_ON",
      "reason": {
        "LeadingIndex": 0.18,
        "CoincidentIndex": -0.08,
        "recovery": true,
        "hysteresis_cleared": true,
        "dL": 0.12,
        "confirm_periods_met": 2
      }
    }
  ],

  "backtest_summary": {
    "period": {
      "start": "2000-01-01",
      "end": "2026-01-15",
      "total_months": 313
    },
    "performance": {
      "cumulative_return": 4.25,
      "cagr": 0.123,
      "annualized_volatility": 0.12,
      "sharpe_ratio": 0.85,
      "max_drawdown": -0.27,
      "max_drawdown_date": "2008-11-30",
      "calmar_ratio": 0.46
    },
    "turnover": {
      "total_switches": 10,
      "avg_months_per_state": 31.3,
      "periods_in_equity": 210,
      "periods_in_bonds": 103
    },
    "costs": {
      "total_transaction_costs_bps": 100,
      "total_slippage_bps": 0,
      "net_return_after_costs": 4.15
    }
  },

  "benchmarks": {
    "equity_buy_hold": {
      "cumulative_return": 3.85,
      "cagr": 0.108,
      "max_drawdown": -0.55,
      "sharpe_ratio": 0.52
    },
    "bond_buy_hold": {
      "cumulative_return": 2.10,
      "cagr": 0.058,
      "max_drawdown": -0.35,
      "sharpe_ratio": 0.38
    },
    "60_40_portfolio": {
      "cumulative_return": 3.20,
      "cagr": 0.092,
      "max_drawdown": -0.38,
      "sharpe_ratio": 0.65
    }
  },

  "relative_performance": {
    "vs_equity": {
      "excess_cagr": 0.015,
      "reduced_drawdown": 0.28
    },
    "vs_60_40": {
      "excess_cagr": 0.031,
      "reduced_drawdown": 0.11
    }
  },

  "diagnostics": {
    "leading_components": [
      {
        "series_id": "T10Y3M",
        "latest_value": 0.85,
        "z_score": 0.32,
        "contribution": 0.08,
        "weight": 0.25
      },
      {
        "series_id": "T10Y2Y",
        "latest_value": 0.42,
        "z_score": 0.28,
        "contribution": 0.04,
        "weight": 0.15
      },
      {
        "series_id": "PERMIT",
        "latest_value": 0.05,
        "z_score": 0.45,
        "contribution": 0.09,
        "weight": 0.20
      },
      {
        "series_id": "ACDGNO",
        "latest_value": 0.03,
        "z_score": 0.38,
        "contribution": 0.08,
        "weight": 0.20
      },
      {
        "series_id": "UMCSENT",
        "latest_value": 72.5,
        "z_score": 0.62,
        "contribution": 0.12,
        "weight": 0.20
      }
    ],
    "coincident_components": [
      {
        "series_id": "PAYEMS",
        "latest_value": 0.018,
        "z_score": 0.28,
        "contribution": 0.08,
        "weight": 0.30
      },
      {
        "series_id": "INDPRO",
        "latest_value": 0.012,
        "z_score": 0.15,
        "contribution": 0.05,
        "weight": 0.30
      },
      {
        "series_id": "W875RX1",
        "latest_value": 0.025,
        "z_score": 0.22,
        "contribution": 0.04,
        "weight": 0.20
      },
      {
        "series_id": "CMRMTSPL",
        "latest_value": 0.015,
        "z_score": 0.25,
        "contribution": 0.05,
        "weight": 0.20
      }
    ],
    "top_contributors": [
      {"series_id": "UMCSENT", "contribution": 0.12, "direction": "positive"},
      {"series_id": "PERMIT", "contribution": 0.09, "direction": "positive"}
    ],
    "top_detractors": []
  },

  "filters_status": {
    "euphoria": {
      "active": false,
      "components": [
        {"type": "credit_spread_reversal", "triggered": false, "value": 1.85}
      ]
    },
    "recovery_doubt": {
      "active": true,
      "components": [
        {"type": "leading_momentum", "triggered": true, "value": 0.05}
      ]
    }
  },

  "time_series": {
    "available": true,
    "file": "time_series.csv",
    "columns": ["date", "LeadingIndex", "CoincidentIndex", "state", "equity_value", "bond_value", "portfolio_value"]
  },

  "notes": [
    "Indices are built from public FRED proxies; proprietary Zeberg model is approximated.",
    "TLT data starts from 2002-07; earlier periods use synthetic bond returns.",
    "All returns are based on adjusted close prices (including dividends)."
  ],

  "metadata": {
    "generated_at": "2026-01-15T10:30:00Z",
    "execution_time_ms": 2345,
    "data_freshness": {
      "macro_data": "2025-11-30",
      "price_data": "2026-01-14"
    }
  }
}
```

## 欄位說明

### current_state

| 欄位 | 說明 |
|------|------|
| state | 當前狀態（RISK_ON 或 RISK_OFF） |
| since | 進入當前狀態的日期 |
| months_in_state | 在當前狀態的月數 |

### latest_indices

| 欄位 | 說明 |
|------|------|
| LeadingIndex | 領先指標合成值 |
| CoincidentIndex | 同時指標合成值 |
| dL | 領先指標月變化 |
| dC | 同時指標月變化 |
| iceberg_event | 是否觸發冰山事件 |
| sinking_event | 是否觸發下沉事件 |
| distance_to_iceberg | 距離冰山門檻的距離（標準差） |
| distance_to_sinking | 距離下沉門檻的距離（標準差） |

### switch_events

| 欄位 | 說明 |
|------|------|
| date | 切換日期 |
| action | 執行動作 |
| from_state | 原狀態 |
| to_state | 新狀態 |
| reason | 觸發原因詳情 |

### backtest_summary.performance

| 欄位 | 說明 |
|------|------|
| cumulative_return | 累積報酬倍數 |
| cagr | 年化複合成長率 |
| annualized_volatility | 年化波動率 |
| sharpe_ratio | Sharpe 比率 |
| max_drawdown | 最大回撤 |
| calmar_ratio | Calmar 比率（CAGR / MaxDD） |

## 精簡輸出（--quick 模式）

```json
{
  "skill": "zeberg-salomon-rotator",
  "as_of": "2026-01-15",
  "state": "RISK_ON",
  "latest_indices": {
    "LeadingIndex": 0.41,
    "CoincidentIndex": 0.22,
    "iceberg_event": false,
    "sinking_event": false
  },
  "last_switch": {
    "date": "2023-06-30",
    "action": "EXIT_LONG_BOND_ENTER_EQUITY"
  }
}
```
