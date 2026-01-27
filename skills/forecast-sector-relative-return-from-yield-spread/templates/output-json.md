# JSON 輸出模板

本文件定義技能的 JSON 輸出結構，供程式解析使用。

---

## 完整結構

```json
{
  "skill": "forecast_sector_relative_return_from_yield_spread",
  "version": "0.1.0",
  "generated_at": "2026-01-27T10:30:00",

  "inputs": {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "short_tenor": "2Y",
    "long_tenor": "10Y",
    "lead_months": 24,
    "lookback_years": 12,
    "freq": "weekly",
    "smoothing_window": 13,
    "return_horizon_months": 24,
    "model_type": "lagged_regression",
    "confidence_level": 0.80
  },

  "signal_name": "US02Y_minus_US10Y_leads_QQQ_over_XLV",

  "current_state": {
    "spread": -0.35,
    "spread_percentile": 35,
    "spread_3m_change": 0.25,
    "spread_6m_change": 0.40,
    "spread_trend": "steepening",
    "as_of_date": "2026-01-24"
  },

  "model": {
    "type": "lagged_regression",
    "coefficients": {
      "alpha": 0.02,
      "beta": -0.45
    },
    "fit_quality": {
      "corr_x_y": -0.32,
      "r_squared": 0.10,
      "p_value": 0.001,
      "n_observations": 520,
      "notes": "負 beta 意味歷史上倒掛/緊縮的 spread 對應未來 QQQ 相對走弱"
    }
  },

  "forecast": {
    "horizon_months": 24,
    "future_relative_return": {
      "log": -0.08,
      "pct": -0.077
    },
    "interval": {
      "confidence_level": 0.80,
      "log": [-0.25, 0.04],
      "pct": [-0.22, 0.04]
    },
    "direction": {
      "defensive_outperform_prob": 0.70,
      "expected_winner": "XLV"
    },
    "interpretation": "若此關係維持，未來24個月QQQ相對XLV期望報酬為-7.7%，XLV較可能跑贏；但區間仍含正值，需搭配其他條件確認。"
  },

  "diagnostics": {
    "lead_scan": {
      "performed": true,
      "scan_range": [6, 12, 18, 24, 30],
      "best_lead_months": 24,
      "correlation_by_lead": {
        "6": -0.15,
        "12": -0.22,
        "18": -0.28,
        "24": -0.32,
        "30": -0.30
      }
    },
    "stability_checks": {
      "first_half_period": "2014-01-01 to 2020-01-01",
      "second_half_period": "2020-01-01 to 2026-01-01",
      "first_half_corr": -0.30,
      "second_half_corr": -0.34,
      "consistency": "medium-high",
      "notes": "兩段相關性符號一致且差異 < 0.1，關係跨時期穩定"
    },
    "data_quality": {
      "yield_data_points": 3120,
      "price_data_points": 520,
      "missing_pct": 0.02,
      "date_range": "2014-01-03 to 2026-01-24"
    }
  },

  "summary": "殖利率利差（2Y-10Y）對 QQQ/XLV 相對報酬存在約 24 個月的領先關係。當前 spread 為 -0.35%（曲線輕微倒掛），對應未來 24 個月 XLV 相對跑贏的預期。",

  "notes": [
    "領先關係反映的是『歷史統計規律』，不保證未來成立。",
    "R² 僅 0.10，spread 只解釋約 10% 的相對報酬變異。",
    "當前 spread 趨勢為變陡（從倒掛回正），需持續觀察。",
    "建議搭配：景氣指標、估值分位、資金流向做交叉驗證。"
  ],

  "next_steps": [
    "監控 spread 是否持續變陡",
    "檢查經濟領先指標（ISM、消費者信心）",
    "比較 Healthcare 基本面（防禦需求）",
    "3 個月後重新驗證預測"
  ],

  "artifacts": [
    {
      "type": "chart",
      "path": "output/spread_forecast_2026-01-27.png",
      "description": "利差與相對報酬對齊圖"
    }
  ]
}
```

---

## 欄位說明

### 頂層欄位

| 欄位         | 類型   | 必要 | 說明                     |
|--------------|--------|------|--------------------------|
| skill        | string | ✓    | 技能識別碼               |
| version      | string | ✓    | 技能版本                 |
| generated_at | string | ✓    | 報告生成時間（ISO 8601） |

### inputs

記錄使用的輸入參數，供重現與除錯。

### current_state

| 欄位             | 類型   | 說明                           |
|------------------|--------|--------------------------------|
| spread           | float  | 當前殖利率利差（%）            |
| spread_percentile| float  | 利差在歷史的分位數（0-100）    |
| spread_3m_change | float  | 利差過去 3 個月變化            |
| spread_trend     | string | 趨勢：steepening/flattening    |
| as_of_date       | string | 數據截止日期                   |

### model

| 欄位        | 類型   | 說明                     |
|-------------|--------|--------------------------|
| type        | string | 模型類型                 |
| coefficients| object | 迴歸係數（alpha, beta）  |
| fit_quality | object | 擬合品質指標             |

### forecast

| 欄位                   | 類型   | 說明                          |
|------------------------|--------|-------------------------------|
| horizon_months         | int    | 預測視野（月）                |
| future_relative_return | object | 預測報酬（log 與 pct）        |
| interval               | object | 信心區間                      |
| direction              | object | 方向預測（哪邊跑贏機率）      |
| interpretation         | string | 自然語言解讀                  |

### diagnostics

| 欄位             | 類型   | 說明                     |
|------------------|--------|--------------------------|
| lead_scan        | object | 領先掃描結果             |
| stability_checks | object | 穩定性驗證結果           |
| data_quality     | object | 數據品質指標             |

---

## 狀態碼

若執行失敗，輸出以下結構：

```json
{
  "skill": "forecast_sector_relative_return_from_yield_spread",
  "status": "error",
  "error": {
    "code": "DATA_FETCH_FAILED",
    "message": "Failed to fetch DGS10 from FRED",
    "details": "Connection timeout after 30s"
  },
  "partial_results": null
}
```

**錯誤碼：**
| 代碼                 | 說明                   |
|----------------------|------------------------|
| DATA_FETCH_FAILED    | 數據抓取失敗           |
| INSUFFICIENT_DATA    | 數據點不足             |
| INVALID_PARAMS       | 參數無效               |
| MODEL_FIT_FAILED     | 模型估計失敗           |
| STABILITY_CHECK_FAIL | 穩定性驗證不通過       |
