# JSON 輸出模板

## 完整輸出結構

```json
{
  "skill": "detect-us-equity-valuation-percentile-extreme",
  "version": "0.1.0",
  "as_of_date": "2026-01-21",
  "universe": "^GSPC",
  "generated_at": "2026-01-21T15:30:00Z",

  "summary": {
    "composite_percentile": 97.3,
    "extreme_threshold": 95,
    "is_extreme": true,
    "status": "EXTREME_OVERVALUED",
    "status_description": "綜合估值分位數超過 95，處於歷史極端高估區間"
  },

  "metric_percentiles": {
    "cape": {
      "current_value": 38.5,
      "percentile": 98.2,
      "history_start": "1871-01-01",
      "data_points": 1860,
      "historical_median": 16.8,
      "historical_mean": 17.2
    },
    "mktcap_to_gdp": {
      "current_value": 195.3,
      "percentile": 96.5,
      "history_start": "1950-01-01",
      "data_points": 912,
      "historical_median": 82.5,
      "historical_mean": 88.7
    },
    "trailing_pe": {
      "current_value": 28.7,
      "percentile": 94.1,
      "history_start": "1980-01-01",
      "data_points": 552,
      "historical_median": 17.5,
      "historical_mean": 18.9
    },
    "pb": {
      "current_value": 4.8,
      "percentile": 92.3,
      "history_start": "1985-01-01",
      "data_points": 492,
      "historical_median": 2.6,
      "historical_mean": 2.9
    }
  },

  "aggregation_info": {
    "method": "mean",
    "weights": {
      "cape": 0.25,
      "mktcap_to_gdp": 0.25,
      "trailing_pe": 0.25,
      "pb": 0.25
    },
    "metrics_included": ["cape", "mktcap_to_gdp", "trailing_pe", "pb"],
    "metrics_excluded": []
  },

  "historical_episodes": [
    {
      "date": "1929-09-01",
      "composite_percentile": 97.8,
      "metric_values": {
        "cape": 33.0
      },
      "context": "大蕭條前夕"
    },
    {
      "date": "1965-01-01",
      "composite_percentile": 95.2,
      "metric_values": {
        "cape": 24.0
      },
      "context": "Nifty Fifty 時期"
    },
    {
      "date": "1999-12-01",
      "composite_percentile": 98.5,
      "metric_values": {
        "cape": 44.0,
        "mktcap_to_gdp": 150.0
      },
      "context": "科技泡沫頂點"
    },
    {
      "date": "2021-12-01",
      "composite_percentile": 97.1,
      "metric_values": {
        "cape": 40.0,
        "mktcap_to_gdp": 200.0
      },
      "context": "疫情後牛市頂點"
    }
  ],

  "forward_stats": {
    "180d": {
      "forward_return": {
        "median": -2.5,
        "p25": -12.3,
        "p10": -25.8,
        "positive_prob": 0.45,
        "sample_size": 5
      },
      "max_drawdown": {
        "median": -8.5,
        "p75": -18.2,
        "worst": -35.0
      }
    },
    "365d": {
      "forward_return": {
        "median": -5.8,
        "p25": -18.5,
        "p10": -32.1,
        "positive_prob": 0.40,
        "sample_size": 5
      },
      "max_drawdown": {
        "median": -15.2,
        "p75": -28.5,
        "worst": -50.8
      }
    },
    "1095d": {
      "forward_return": {
        "median": 8.5,
        "p25": -12.8,
        "p10": -25.5,
        "positive_prob": 0.55,
        "sample_size": 4
      },
      "max_drawdown": {
        "median": -28.5,
        "p75": -42.1,
        "worst": -89.0
      }
    }
  },

  "volatility_analysis": {
    "current_vix": 18.5,
    "vix_percentile": 45.2,
    "historical_pattern": {
      "vol_increase_prob_6m": 0.72,
      "vol_increase_prob_12m": 0.65,
      "median_vol_change": 5.2
    }
  },

  "risk_interpretation": {
    "headline": "當前估值處於歷史極端高估區間，風險分布不對稱",
    "key_points": [
      "綜合估值分位數 97.3，歷史上僅 2.7% 的時間比現在更貴",
      "CAPE (98.2) 和 市值/GDP (96.5) 是主要推升因素",
      "歷史上類似時期，未來 1-3 年最大回撤中位數約 -15% 至 -30%",
      "正報酬機率下降，但不代表「必然崩盤」"
    ],
    "caveats": [
      "歷史極端事件樣本數有限（約 4-5 次）",
      "當前低利率環境可能支持更高估值",
      "時代背景不同，直接類比有風險"
    ],
    "suggested_actions": [
      "降低整體槓桿",
      "增加防禦性資產配置",
      "不建議據此完全離場或做空"
    ]
  },

  "data_quality_notes": [
    "CAPE 資料來源: Shiller Online Data，可回溯至 1871 年",
    "市值/GDP 資料來源: FRED (WILL5000PRFC / GDP)，可回溯至 1950 年代",
    "Trailing PE 資料來源: Yahoo Finance，歷史約 40 年",
    "合成分位數使用各指標自身歷史分布，再在同日做等權合成"
  ],

  "metadata": {
    "execution_time_ms": 2500,
    "data_freshness": {
      "cape": "2026-01-20",
      "mktcap_to_gdp": "2026-01-15",
      "trailing_pe": "2026-01-21",
      "pb": "2026-01-21"
    },
    "cache_used": false
  }
}
```

---

## 欄位說明

### 頂層欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| skill | string | 技能識別碼 |
| version | string | 技能版本 |
| as_of_date | string | 評估日期 |
| universe | string | 市場代碼 |
| generated_at | string | 報告產生時間（ISO 8601） |

### summary

| 欄位 | 類型 | 說明 |
|------|------|------|
| composite_percentile | number | 綜合估值分位數 (0-100) |
| extreme_threshold | number | 極端門檻 |
| is_extreme | boolean | 是否極端高估 |
| status | string | 狀態碼（EXTREME_OVERVALUED / ELEVATED / NORMAL / UNDERVALUED） |
| status_description | string | 狀態描述（人類可讀） |

### metric_percentiles

每個指標的詳細資訊：

| 欄位 | 類型 | 說明 |
|------|------|------|
| current_value | number | 當前值 |
| percentile | number | 分位數 (0-100) |
| history_start | string | 歷史起始日期 |
| data_points | integer | 歷史資料點數 |
| historical_median | number | 歷史中位數 |
| historical_mean | number | 歷史平均 |

### historical_episodes

每個歷史極端事件：

| 欄位 | 類型 | 說明 |
|------|------|------|
| date | string | 事件日期 |
| composite_percentile | number | 當時的綜合分位數 |
| metric_values | object | 當時各指標的值 |
| context | string | 事件背景說明 |

### forward_stats

每個視窗的事後統計：

| 欄位 | 類型 | 說明 |
|------|------|------|
| forward_return | object | 未來報酬統計 |
| max_drawdown | object | 最大回撤統計 |

forward_return 子欄位：
- median: 中位數報酬
- p25: 25 分位報酬
- p10: 10 分位報酬
- positive_prob: 正報酬機率
- sample_size: 樣本數

---

## 精簡輸出（--quick 模式）

```json
{
  "skill": "detect-us-equity-valuation-percentile-extreme",
  "as_of_date": "2026-01-21",
  "composite_percentile": 97.3,
  "is_extreme": true,
  "metric_percentiles": {
    "cape": 98.2,
    "mktcap_to_gdp": 96.5,
    "trailing_pe": 94.1
  },
  "status": "EXTREME_OVERVALUED"
}
```

---

## 狀態碼定義

| 狀態碼 | 分位數範圍 | 說明 |
|--------|------------|------|
| EXTREME_OVERVALUED | ≥95 | 歷史極端高估 |
| OVERVALUED | 80-94 | 高估 |
| ELEVATED | 65-79 | 偏高 |
| NORMAL | 35-64 | 正常範圍 |
| CHEAP | 20-34 | 偏低 |
| UNDERVALUED | 5-19 | 低估 |
| EXTREME_UNDERVALUED | <5 | 歷史極端低估 |
