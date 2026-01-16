# JSON 輸出結構模板

本文件定義 Skill 的標準 JSON 輸出結構。

---

## Full Analysis 輸出結構

```json
{
  "metadata": {
    "skill": "lithium-supply-demand-gap-radar",
    "version": "0.1.0",
    "asof_date": "2026-01-16",
    "etf_ticker": "LIT",
    "data_level": "free_nolimit",
    "generated_at": "2026-01-16T10:30:00Z"
  },

  "data_sources_used": {
    "supply": ["USGS", "AU_REQ", "ABS"],
    "demand": ["IEA"],
    "price": ["CME_proxy"],
    "etf": ["GlobalX"]
  },

  "balance_nowcast": {
    "index": {
      "conservative": 0.65,
      "neutral": 0.85,
      "aggressive": 1.05
    },
    "trend": "widening",
    "inflection": {
      "detected": false,
      "type": null
    },
    "supply_summary": {
      "latest_year": 2024,
      "value": 220,
      "unit": "kt_LCE",
      "yoy_growth": 22.2
    },
    "demand_summary": {
      "latest_year": 2024,
      "scenarios": {
        "conservative": {"value": 180, "kg_per_kwh": 0.12},
        "neutral": {"value": 200, "kg_per_kwh": 0.15},
        "aggressive": {"value": 216, "kg_per_kwh": 0.18}
      },
      "unit": "kt_LCE"
    }
  },

  "price_regime": {
    "carbonate": {
      "regime": "bottoming",
      "confidence": 0.75,
      "indicators": {
        "roc_12w": -2.3,
        "roc_26w": -8.5,
        "slope": -0.12,
        "volatility": 4.2,
        "mean_deviation": -12
      },
      "signal": "觀望，等待確認"
    },
    "hydroxide": {
      "regime": "bottoming",
      "confidence": 0.75,
      "indicators": {
        "roc_12w": -3.1,
        "roc_26w": -9.2,
        "slope": -0.15,
        "volatility": 4.8,
        "mean_deviation": -14
      },
      "signal": "觀望，等待確認"
    },
    "spread": {
      "current": 2500,
      "unit": "USD/t",
      "percentile": 45,
      "trend": "narrowing"
    },
    "sync_status": "synchronized"
  },

  "etf_exposure": {
    "holdings_summary": {
      "total_holdings": 40,
      "asof_date": "2026-01-15",
      "source": "GlobalX"
    },
    "segment_weights": {
      "upstream": 35.2,
      "midstream": 18.5,
      "downstream": 42.3,
      "unknown": 4.0
    },
    "beta_analysis": {
      "current_beta_li": 0.72,
      "current_beta_ev": 0.58,
      "52w_avg_beta_li": 0.68,
      "trend": "rising"
    },
    "transmission_status": {
      "status": "normal",
      "description": "傳導正常：近期平均 Beta = 0.72"
    },
    "top_holdings": [
      {"rank": 1, "ticker": "ALB", "weight": 8.2, "segment": "upstream", "country": "US"},
      {"rank": 2, "ticker": "TSLA", "weight": 7.5, "segment": "downstream", "country": "US"},
      {"rank": 3, "ticker": "SQM", "weight": 6.8, "segment": "upstream", "country": "Chile"}
    ]
  },

  "thesis": {
    "direction": "neutral_bullish",
    "confidence": 0.70,
    "summary": "供需缺口擴大中，價格制度築底待確認，傳導正常",
    "components": {
      "balance_score": 0.85,
      "regime_score": 0.50,
      "transmission_score": 0.72
    }
  },

  "targets": {
    "support": {"level": 38.50, "type": "prior_low"},
    "mid_channel": {"level": 48.50, "type": "ma_50w"},
    "prior_high": {"level": 56.20, "type": "resistance"},
    "upper_channel": {"level": 68.00, "type": "upper_band"}
  },

  "invalidation": [
    {
      "condition": "price < 38.50",
      "description": "跌破關鍵支撐",
      "severity": "high"
    },
    {
      "condition": "balance_index < 0",
      "description": "供需平衡轉負（過剩）",
      "severity": "high"
    },
    {
      "condition": "regime == downtrend",
      "description": "價格制度再次轉弱",
      "severity": "medium"
    },
    {
      "condition": "beta_li < 0.3 for 8w",
      "description": "傳導斷裂",
      "severity": "medium"
    }
  ],

  "catalysts": [
    {
      "event": "IEA Global EV Outlook 2026",
      "expected_date": "2026-04",
      "direction": "positive",
      "impact": "medium"
    },
    {
      "event": "Australia REQ Q1 2026",
      "expected_date": "2026-03",
      "direction": "neutral",
      "impact": "low"
    }
  ],

  "confidence_matrix": {
    "overall": 0.75,
    "by_component": {
      "balance_nowcast": 0.80,
      "price_regime": 0.70,
      "etf_exposure": 0.85
    },
    "data_freshness": {
      "supply_data": "2024-annual",
      "demand_data": "2024-annual",
      "price_data": "2026-01-16",
      "holdings_data": "2026-01-15"
    }
  }
}
```

---

## Balance Nowcast 輸出結構

```json
{
  "metadata": {
    "skill": "lithium-supply-demand-gap-radar",
    "workflow": "balance-nowcast",
    "asof_date": "2026-01-16"
  },

  "balance_index": {
    "conservative": {
      "value": 0.65,
      "trend": "widening",
      "kg_per_kwh_assumption": 0.12
    },
    "neutral": {
      "value": 0.85,
      "trend": "widening",
      "kg_per_kwh_assumption": 0.15
    },
    "aggressive": {
      "value": 1.05,
      "trend": "widening",
      "kg_per_kwh_assumption": 0.18
    }
  },

  "inflection": {
    "detected": false,
    "type": null,
    "last_inflection": {
      "date": "2023-06",
      "type": "bearish",
      "balance_index_at_time": 1.2
    }
  },

  "supply": {
    "world_production": {
      "2020": 82,
      "2021": 107,
      "2022": 130,
      "2023": 180,
      "2024": 220
    },
    "unit": "kt_LCE",
    "sources": ["USGS", "AU_REQ"],
    "confidence": 0.90
  },

  "demand": {
    "battery_gwh": {
      "2020": 150,
      "2021": 330,
      "2022": 550,
      "2023": 750,
      "2024": 1000
    },
    "lithium_demand_kt": {
      "conservative": {"2024": 180},
      "neutral": {"2024": 200},
      "aggressive": {"2024": 216}
    },
    "unit": "kt_LCE",
    "sources": ["IEA"],
    "confidence": 0.85
  },

  "interpretation": "需求增速持續高於供給增速，供需缺口擴大中。保守估計下缺口為負（過剩），但中性和積極估計均顯示缺口。"
}
```

---

## Price Regime 輸出結構

```json
{
  "metadata": {
    "skill": "lithium-supply-demand-gap-radar",
    "workflow": "price-regime",
    "asof_date": "2026-01-16"
  },

  "carbonate": {
    "regime": "bottoming",
    "confidence": 0.75,
    "price_latest": {
      "value": 12500,
      "unit": "USD/t",
      "source": "CME_proxy"
    },
    "indicators": {
      "roc_12w": {"value": -2.3, "interpretation": "收斂中"},
      "roc_26w": {"value": -8.5, "interpretation": "仍為負"},
      "slope": {"value": -0.12, "interpretation": "趨緩"},
      "volatility": {"value": 4.2, "interpretation": "下降"},
      "mean_deviation": {"value": -12, "interpretation": "低於均線"}
    },
    "signal": "觀望，等待確認",
    "confirmation_signals": [
      {"signal": "12週動能轉正", "status": "pending"},
      {"signal": "波動率擴大", "status": "pending"},
      {"signal": "突破近期高點", "status": "pending"}
    ]
  },

  "hydroxide": {
    "regime": "bottoming",
    "confidence": 0.75,
    "price_latest": {
      "value": 15000,
      "unit": "USD/t",
      "source": "CME_proxy"
    },
    "indicators": {
      "roc_12w": {"value": -3.1, "interpretation": "收斂中"},
      "roc_26w": {"value": -9.2, "interpretation": "仍為負"},
      "slope": {"value": -0.15, "interpretation": "趨緩"},
      "volatility": {"value": 4.8, "interpretation": "下降"},
      "mean_deviation": {"value": -14, "interpretation": "低於均線"}
    },
    "signal": "觀望，等待確認"
  },

  "spread_analysis": {
    "carbonate_hydroxide_spread": {
      "current": 2500,
      "unit": "USD/t",
      "percentile_52w": 45,
      "trend": "narrowing"
    },
    "interpretation": "氫氧化鋰溢價收窄，可能反映 LFP 需求上升"
  },

  "sync_status": "synchronized",

  "cycle_position": {
    "description": "DOWNTREND → [BOTTOMING] → UPTREND → OVERHEAT",
    "current": "BOTTOMING"
  }
}
```

---

## ETF Exposure 輸出結構

```json
{
  "metadata": {
    "skill": "lithium-supply-demand-gap-radar",
    "workflow": "etf-exposure",
    "asof_date": "2026-01-16",
    "etf_ticker": "LIT"
  },

  "holdings": {
    "total": 40,
    "asof_date": "2026-01-15",
    "source": "GlobalX",
    "top_10": [
      {"rank": 1, "ticker": "ALB", "name": "Albemarle Corp", "weight": 8.2, "segment": "upstream", "country": "US"},
      {"rank": 2, "ticker": "TSLA", "name": "Tesla Inc", "weight": 7.5, "segment": "downstream", "country": "US"},
      {"rank": 3, "ticker": "SQM", "name": "SQM", "weight": 6.8, "segment": "upstream", "country": "Chile"},
      {"rank": 4, "ticker": "CATL", "name": "CATL", "weight": 6.2, "segment": "downstream", "country": "China"},
      {"rank": 5, "ticker": "PLS.AX", "name": "Pilbara Minerals", "weight": 5.5, "segment": "upstream", "country": "Australia"}
    ]
  },

  "segment_analysis": {
    "weights": {
      "upstream": 35.2,
      "midstream": 18.5,
      "downstream": 42.3,
      "unknown": 4.0
    },
    "expected_beta_by_segment": {
      "upstream": 1.8,
      "midstream": 1.0,
      "downstream": 0.5
    },
    "weighted_expected_beta": 0.95
  },

  "beta_analysis": {
    "rolling_52w": {
      "beta_li": [0.65, 0.68, 0.71, 0.72],
      "beta_ev": [0.52, 0.55, 0.57, 0.58],
      "dates": ["2025-10", "2025-11", "2025-12", "2026-01"]
    },
    "current": {
      "beta_li": 0.72,
      "beta_ev": 0.58,
      "r_squared": 0.45
    },
    "52w_average": {
      "beta_li": 0.68,
      "beta_ev": 0.55
    },
    "trend": "rising"
  },

  "transmission": {
    "status": "normal",
    "description": "傳導正常：近期平均 Beta = 0.72",
    "implication": "ETF 正常反映鋰價變動",
    "threshold": 0.3,
    "duration_below_threshold": 0
  }
}
```

---

## 通用欄位說明

### 數據品質標記

| 欄位 | 類型 | 說明 |
|------|------|------|
| `confidence` | float | 數據置信度 (0-1) |
| `source` | string | 數據來源 |
| `asof_date` | string | 數據截止日期 |
| `data_level` | string | 數據等級 |

### 判讀標記

| 欄位 | 類型 | 說明 |
|------|------|------|
| `trend` | string | 趨勢方向 |
| `signal` | string | 交易信號 |
| `interpretation` | string | 人類可讀解釋 |
