# JSON 輸出結構定義

本文件定義 evaluate-exponential-trend-deviation-regimes 技能的 JSON 輸出格式。

## 完整輸出結構

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "asset": "GC=F",
  "trend_model": "exponential_log_linear",
  "date_range": {
    "start": "1970-01-01",
    "end": "2026-01-14"
  },
  "metrics": {
    "current_distance_pct": 92.4,
    "current_percentile": 97.8,
    "reference": {
      "2011_max_distance_pct": 85.1,
      "1980_peak_distance_pct": 320.7
    },
    "verdict": {
      "surpassed_2011_by_this_metric": true,
      "distance_to_1980_peak_pct_points": 228.3
    }
  },
  "regime": {
    "regime_label": "1970s_like",
    "drivers": [
      "Real rates negative / falling",
      "Inflation risk rising",
      "Geopolitical tension proxy rising"
    ],
    "confidence": 0.72,
    "factor_breakdown": {
      "real_rate": {
        "value": -0.5,
        "trend": "falling",
        "score": 1.0,
        "contribution": 0.30
      },
      "inflation": {
        "value": 2.8,
        "trend": "rising",
        "score": 0.7,
        "contribution": 0.175
      },
      "geopolitical": {
        "percentile": 75,
        "trend": "rising",
        "score": 0.8,
        "contribution": 0.20
      },
      "usd": {
        "trend": "weakening",
        "months_from_high": 4,
        "score": 0.7,
        "contribution": 0.14
      }
    }
  },
  "insights": [
    "Gold is trading at an extreme positive deviation from its long-run exponential trendline, above the 2011 deviation peak.",
    "Compared with 1980-style blow-off, deviation is still materially lower, leaving room for extension if 1970s-like conditions persist.",
    "If real rates re-anchor higher and inflation expectations cool, mean-reversion risk increases even if the long-term trend remains up."
  ],
  "trend_parameters": {
    "a": 3.555,
    "b": 0.00456,
    "annualized_growth_rate_pct": 5.5
  },
  "auxiliary": {
    "latest_price": 2650.5,
    "trend_price": 1379.2,
    "data_points": 660
  },
  "metadata": {
    "generated_at": "2026-01-15T10:30:00Z",
    "data_sources": {
      "gold": "Yahoo Finance (GC=F)",
      "real_rate": "FRED (DFII10)",
      "inflation": "FRED (T5YIE)",
      "usd": "FRED (DTWEXBGS)"
    },
    "warnings": []
  }
}
```

## 欄位說明

### 頂層欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| skill | string | 技能名稱 |
| asset | string | 資產代碼 |
| trend_model | string | 趨勢模型類型 |
| date_range | object | 數據範圍 |
| metrics | object | 核心指標 |
| regime | object | 行情體質判定 |
| insights | array | 洞察文字 |
| trend_parameters | object | 趨勢線參數 |
| auxiliary | object | 輔助信息 |
| metadata | object | 元數據 |

### metrics 子欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| current_distance_pct | float | 當前偏離度（%） |
| current_percentile | float | 歷史分位數（0-100） |
| reference | object | 參考峰值偏離度 |
| verdict | object | 與參考點的比較結論 |

### regime 子欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| regime_label | string | "1970s_like" 或 "2000s_like" |
| drivers | array | 驅動因子列表 |
| confidence | float | 信心度（0-1） |
| factor_breakdown | object | 各因子詳細分解 |

### trend_parameters 子欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| a | float | 截距（log scale） |
| b | float | 斜率（log scale，每交易日） |
| annualized_growth_rate_pct | float | 年化成長率（%） |

## 簡化輸出（--quick 模式）

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "asset": "GC=F",
  "as_of": "2026-01-14",
  "current_distance_pct": 92.4,
  "current_percentile": 97.8,
  "surpassed_2011": true,
  "regime_label": "1970s_like",
  "regime_confidence": 0.72
}
```

## 多資產掃描輸出

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "scan_mode": true,
  "as_of": "2026-01-14",
  "scan_results": [
    {
      "asset": "GC=F",
      "distance_pct": 92.4,
      "percentile": 97.8,
      "regime": "1970s_like",
      "regime_confidence": 0.72
    }
  ],
  "summary": {
    "total_assets": 1,
    "extreme_deviation_count": 1,
    "regime_1970s_count": 1,
    "regime_2000s_count": 0
  }
}
```

## 錯誤輸出

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "error": true,
  "error_type": "data_fetch_failed",
  "error_message": "Failed to fetch gold prices from Yahoo Finance",
  "suggestions": [
    "Check internet connection",
    "Try alternative data source (Stooq)",
    "Verify symbol is correct"
  ]
}
```

## 部分數據輸出

當部分宏觀數據不可用時：

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "asset": "GC=F",
  "metrics": {
    "current_distance_pct": 92.4,
    "current_percentile": 97.8
  },
  "regime": {
    "regime_label": "1970s_like",
    "confidence": 0.55,
    "factor_breakdown": {
      "real_rate": { "value": -0.5, "score": 1.0 },
      "inflation": { "value": null, "score": null },
      "geopolitical": { "percentile": null, "score": null },
      "usd": { "trend": "weakening", "score": 0.7 }
    }
  },
  "metadata": {
    "warnings": [
      "Inflation data unavailable, using reduced factor set",
      "Geopolitical risk data unavailable"
    ],
    "available_factors": 2,
    "total_factors": 4
  }
}
```
