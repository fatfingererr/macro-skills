# JSON 輸出結構定義

## 單資產偵測輸出

```json
{
  "skill": "detect-atr-squeeze-regime",
  "symbol": "SI=F",
  "as_of": "2026-01-14",
  "data_range": {
    "start": "2021-01-14",
    "end": "2026-01-14",
    "trading_days": 1260
  },
  "regime": "volatility_dominated_squeeze",
  "atr_pct": 7.23,
  "atr_ratio_to_baseline": 2.41,
  "baseline_atr_pct": 3.0,
  "baseline_period_days": 756,
  "tech_level_reliability": "low",
  "tech_level_reliability_score": 28,
  "risk_adjustments": {
    "suggested_stop_atr_mult": 2.5,
    "position_scale": 0.41,
    "recommended_timeframe": "weekly",
    "instrument_suggestion": "options_or_spreads"
  },
  "interpretation": {
    "regime_explanation": "當前市場處於「波動主導的擠壓行情」。價格運動更多反映「被迫流」：保證金調整、期權避險、空頭回補。技術位可靠度下降，停損容易被噪音掃掉。",
    "tactics": [
      "偏向較長週期決策，降低被日內噪音主導的風險。",
      "若要參與趨勢，優先考慮 defined-risk（期權/價差）結構。",
      "避免緊停損的短線交易，結構性受損。"
    ]
  },
  "auxiliary_indicators": {
    "rsi_14": 72.5,
    "atr_change_5d_pct": 15.2,
    "regime_duration_days": 12
  },
  "metadata": {
    "generated_at": "2026-01-14T10:30:00Z",
    "parameters": {
      "atr_period": 14,
      "atr_smoothing": "ema",
      "baseline_window_days": 756,
      "spike_threshold_x": 2.0,
      "high_vol_threshold_pct": 6.0
    }
  }
}
```

## 欄位說明

### 核心欄位

| 欄位                           | 類型    | 說明                                                                                      |
|--------------------------------|---------|-------------------------------------------------------------------------------------------|
| `skill`                        | string  | 技能名稱                                                                                  |
| `symbol`                       | string  | 資產代碼                                                                                  |
| `as_of`                        | string  | 分析截至日期                                                                              |
| `regime`                       | string  | 行情判定：`orderly_market` / `elevated_volatility_trend` / `volatility_dominated_squeeze` |
| `atr_pct`                      | number  | 當前 ATR%（百分比）                                                                       |
| `atr_ratio_to_baseline`        | number  | ATR% 對基準的倍率                                                                         |
| `baseline_atr_pct`             | number  | 3 年滾動基準 ATR%                                                                         |
| `tech_level_reliability`       | string  | 技術位可靠度：`high` / `medium` / `low`                                                   |
| `tech_level_reliability_score` | integer | 技術位可靠度評分（0-100）                                                                 |

### risk_adjustments 物件

| 欄位                      | 類型   | 說明                                              |
|---------------------------|--------|---------------------------------------------------|
| `suggested_stop_atr_mult` | number | 建議停損倍數（ATR 倍數）                          |
| `position_scale`          | number | 建議倉位縮放係數（0-1）                           |
| `recommended_timeframe`   | string | 建議時間框架：`any` / `daily` / `weekly`          |
| `instrument_suggestion`   | string | 工具建議：`naked_position` / `options_or_spreads` |

### interpretation 物件

| 欄位                 | 類型          | 說明         |
|----------------------|---------------|--------------|
| `regime_explanation` | string        | 行情解釋文字 |
| `tactics`            | array[string] | 戰術建議清單 |

### auxiliary_indicators 物件（可選）

| 欄位                   | 類型    | 說明               |
|------------------------|---------|--------------------|
| `rsi_14`               | number  | 14 日 RSI          |
| `atr_change_5d_pct`    | number  | ATR% 5 日變化率    |
| `regime_duration_days` | integer | 當前行情已持續天數 |

---

## 批次掃描輸出

```json
{
  "skill": "detect-atr-squeeze-regime",
  "scan_mode": true,
  "as_of": "2026-01-14",
  "scan_results": [
    {
      "symbol": "SI=F",
      "regime": "volatility_dominated_squeeze",
      "atr_pct": 7.23,
      "ratio": 2.41,
      "reliability_score": 28,
      "suggested_stop_mult": 2.5
    },
    {
      "symbol": "GC=F",
      "regime": "orderly_market",
      "atr_pct": 2.85,
      "ratio": 1.15,
      "reliability_score": 85,
      "suggested_stop_mult": 1.2
    },
    {
      "symbol": "CL=F",
      "regime": "elevated_volatility_trend",
      "atr_pct": 4.12,
      "ratio": 1.48,
      "reliability_score": 62,
      "suggested_stop_mult": 1.8
    }
  ],
  "summary": {
    "total_assets": 3,
    "squeeze_count": 1,
    "elevated_count": 1,
    "orderly_count": 1,
    "highest_ratio": {
      "symbol": "SI=F",
      "ratio": 2.41
    },
    "lowest_ratio": {
      "symbol": "GC=F",
      "ratio": 1.15
    }
  },
  "alerts": [
    {
      "type": "squeeze_detected",
      "symbol": "SI=F",
      "message": "SI=F 處於擠壓行情，建議降槓桿"
    }
  ]
}
```

---

## 回測輸出

```json
{
  "skill": "detect-atr-squeeze-regime",
  "backtest_mode": true,
  "symbol": "SI=F",
  "backtest_period": {
    "start": "2015-01-01",
    "end": "2026-01-14"
  },
  "data_points": 2778,
  "regime_distribution": {
    "orderly_market": {
      "days": 1945,
      "pct": 70.0
    },
    "elevated_volatility_trend": {
      "days": 611,
      "pct": 22.0
    },
    "volatility_dominated_squeeze": {
      "days": 222,
      "pct": 8.0
    }
  },
  "squeeze_periods": [
    {
      "start": "2020-03-09",
      "end": "2020-04-15",
      "duration_days": 37,
      "peak_atr_pct": 12.45,
      "peak_ratio": 4.15,
      "peak_date": "2020-03-16",
      "context": "COVID-19 市場恐慌"
    },
    {
      "start": "2024-07-22",
      "end": "2024-08-28",
      "duration_days": 37,
      "peak_atr_pct": 8.92,
      "peak_ratio": 2.97,
      "peak_date": "2024-08-05",
      "context": "日圓套利平倉風暴"
    }
  ],
  "statistics": {
    "total_squeeze_periods": 5,
    "avg_duration_days": 44.4,
    "max_duration_days": 67,
    "min_duration_days": 18,
    "avg_peak_atr_pct": 9.8,
    "avg_peak_ratio": 3.27,
    "max_peak_ratio": 4.15
  },
  "event_matching": {
    "known_events_matched": 4,
    "known_events_total": 5,
    "match_rate": 0.80,
    "matched_events": [
      "COVID-19 (2020-03)",
      "俄烏戰爭 (2022-03)",
      "銀行危機 (2023-03)",
      "日圓平倉 (2024-08)"
    ],
    "missed_events": [
      "2022-09 英國養老金危機（影響較小）"
    ]
  },
  "timeseries": {
    "included": false,
    "note": "使用 --include-timeseries 以包含完整時間序列"
  }
}
```

---

## 時間序列輸出（可選）

若使用 `--include-timeseries`：

```json
{
  "timeseries": {
    "included": true,
    "columns": ["date", "close", "atr", "atr_pct", "baseline", "ratio", "regime"],
    "data": [
      ["2026-01-10", 30.15, 2.12, 7.03, 3.01, 2.34, "volatility_dominated_squeeze"],
      ["2026-01-11", 29.82, 2.15, 7.21, 3.01, 2.40, "volatility_dominated_squeeze"],
      ["2026-01-14", 30.00, 2.17, 7.23, 3.00, 2.41, "volatility_dominated_squeeze"]
    ]
  }
}
```
