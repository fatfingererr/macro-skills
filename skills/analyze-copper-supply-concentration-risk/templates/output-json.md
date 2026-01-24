# JSON 輸出結構模板

## 完整報告輸出

```json
{
  "commodity": "copper",
  "analysis_type": "full_report",
  "generated_at": "2026-01-24T10:30:00Z",
  "period": {
    "start_year": 1970,
    "end_year": 2023
  },
  "parameters": {
    "concentration_metric": "HHI",
    "top_n_producers": 12,
    "structural_break": true,
    "ore_grade_mode": "country_proxy",
    "supply_lead_time_years": 10,
    "geopolitics_mode": "gdelt"
  },

  "proposition_a": {
    "title": "供應是否高度集中？",
    "verdict": "是",
    "metrics": {
      "hhi_latest": 1820,
      "hhi_10y_ago": 1750,
      "hhi_trend": "上升",
      "cr4_latest": 0.562,
      "cr8_latest": 0.734,
      "market_structure": "中等集中"
    },
    "chile_analysis": {
      "share_latest": 0.268,
      "share_peak": 0.342,
      "peak_year": 2003,
      "percentile": 75
    },
    "top_producers": [
      {"rank": 1, "country": "Chile", "share": 0.268, "production_mt": 5.26},
      {"rank": 2, "country": "Peru", "share": 0.102, "production_mt": 2.00},
      {"rank": 3, "country": "DRC", "share": 0.095, "production_mt": 1.86},
      {"rank": 4, "country": "China", "share": 0.087, "production_mt": 1.70}
    ]
  },

  "proposition_b": {
    "title": "智利是否結構性衰退？",
    "verdict": "是",
    "trend_metrics": {
      "peak_year": 2018,
      "peak_production_mt": 5.83,
      "latest_production_mt": 5.26,
      "drawdown": 0.098,
      "rolling_slope_t_per_year": -47000,
      "rolling_window": 10
    },
    "structural_break": {
      "detected": true,
      "break_year": 2016,
      "pre_slope_t_per_year": 85000,
      "post_slope_t_per_year": -38000
    },
    "classification": "structural_decline",
    "grade_inference": {
      "mode": "country_proxy",
      "grade_decline_likely": true,
      "evidence": [
        "產量增速遠低於全球需求增速",
        "高銅價環境下產量仍未提升"
      ],
      "confidence": 0.7
    }
  },

  "proposition_c": {
    "title": "是否依賴秘魯與DRC替代？",
    "verdict": "是",
    "chile_decline": {
      "method": "trend",
      "expected_decline_mt": 0.47
    },
    "replacement_capacity": {
      "Peru": {
        "historical_cagr": 0.042,
        "expected_increment_mt": 0.52,
        "execution_multiplier": 0.8,
        "adjusted_increment_mt": 0.416
      },
      "DRC": {
        "historical_cagr": 0.089,
        "expected_increment_mt": 0.87,
        "execution_multiplier": 0.7,
        "adjusted_increment_mt": 0.609
      }
    },
    "replacement_ratio": 2.18,
    "adjusted_replacement_ratio": 1.05,
    "gap_mt": -0.56,
    "interpretation": "表面充足，但考慮執行風險後僅剛好填補",
    "risk_assessment": {
      "Peru": {
        "political": "中",
        "operational": "中",
        "recent_events": ["2023年多次罷工", "Las Bambas衝突"]
      },
      "DRC": {
        "political": "高",
        "operational": "高",
        "recent_events": ["Mutanda關閉", "政府審查礦權"]
      }
    }
  },

  "proposition_d": {
    "title": "價格能快速帶來供應嗎？",
    "verdict": "否",
    "supply_constraints": {
      "lead_time_years": 10,
      "current_supply_mt": 22.0,
      "supply_ceiling_mt": 24.7,
      "increment_breakdown": {
        "brownfield_expansion": 0.3,
        "under_construction": 0.2,
        "chile_decline": -0.82,
        "peru_increment": 0.52,
        "drc_increment": 0.61
      }
    },
    "scenarios": [
      {
        "name": "slowdown",
        "demand_cagr": 0.015,
        "final_demand_mt": 25.6,
        "gap_mt": 0.9,
        "gap_pct": 0.041,
        "severity": "小缺口"
      },
      {
        "name": "base",
        "demand_cagr": 0.03,
        "final_demand_mt": 29.6,
        "gap_mt": 4.9,
        "gap_pct": 0.223,
        "severity": "嚴重缺口"
      },
      {
        "name": "electrification",
        "demand_cagr": 0.05,
        "final_demand_mt": 35.8,
        "gap_mt": 11.1,
        "gap_pct": 0.505,
        "severity": "嚴重缺口"
      }
    ]
  },

  "proposition_e": {
    "title": "地緣風險有多大？",
    "verdict": "顯著",
    "geo_risk_by_country": {
      "Chile": {
        "event_count_12m": 45,
        "z_score": 0.3,
        "risk_level": "低"
      },
      "Peru": {
        "event_count_12m": 120,
        "z_score": 1.2,
        "risk_level": "中高"
      },
      "DRC": {
        "event_count_12m": 280,
        "z_score": 2.1,
        "risk_level": "高"
      }
    },
    "geo_risk_weighted": 1.65,
    "data_source": "GDELT"
  },

  "system_risk": {
    "score": 73.5,
    "interpretation": "極高風險 - 供應中斷可能性顯著",
    "components": {
      "concentration_score": 18.2,
      "dependency_score": 0.12,
      "geo_risk_weighted": 1.65
    }
  },

  "data_sources": {
    "production": ["OWID Minerals", "USGS MCS"],
    "geopolitics": ["GDELT"],
    "unit": "t_Cu_content",
    "notes": [
      "所有產量數據為 mined copper content（非 refined）",
      "GDELT 數據為近 12 個月事件統計"
    ]
  },

  "recommendations": [
    "監控智利產量月度數據與主要礦區動態",
    "關注秘魯勞工談判與社區衝突",
    "追蹤 DRC 政治穩定性與礦權政策",
    "評估供應鏈多元化策略"
  ]
}
```

---

## 單一分析輸出

### 集中度分析

```json
{
  "commodity": "copper",
  "analysis_type": "concentration",
  "generated_at": "2026-01-24T10:30:00Z",
  "period": {
    "start_year": 1970,
    "end_year": 2023
  },
  "concentration": {
    "metric": "HHI",
    "hhi_latest": 1820,
    "cr4_latest": 0.562,
    "cr8_latest": 0.734,
    "market_structure": "中等集中"
  },
  "top_producers": [...],
  "timeseries": [
    {"year": 2019, "hhi": 1780, "cr4": 0.55},
    {"year": 2020, "hhi": 1790, "cr4": 0.55},
    {"year": 2021, "hhi": 1800, "cr4": 0.56},
    {"year": 2022, "hhi": 1810, "cr4": 0.56},
    {"year": 2023, "hhi": 1820, "cr4": 0.56}
  ],
  "data_sources": ["OWID Minerals"]
}
```

### 智利趨勢分析

```json
{
  "commodity": "copper",
  "analysis_type": "chile_trend",
  "generated_at": "2026-01-24T10:30:00Z",
  "country": "Chile",
  "trend_metrics": {
    "peak_year": 2018,
    "peak_production_mt": 5.83,
    "latest_production_mt": 5.26,
    "drawdown": 0.098,
    "rolling_slope_t_per_year": -47000
  },
  "structural_break": {
    "detected": true,
    "break_year": 2016
  },
  "classification": "structural_decline",
  "data_sources": ["OWID Minerals"]
}
```

---

## 錯誤輸出

```json
{
  "status": "error",
  "error_code": "FM-001",
  "error_type": "DataFetchError",
  "message": "無法從 OWID 擷取數據",
  "context": {
    "url": "https://raw.githubusercontent.com/owid/...",
    "http_status": 500
  },
  "remediation": [
    "檢查網路連線",
    "使用本地快取",
    "稍後重試"
  ],
  "partial_results": null,
  "generated_at": "2026-01-24T10:30:00Z"
}
```
