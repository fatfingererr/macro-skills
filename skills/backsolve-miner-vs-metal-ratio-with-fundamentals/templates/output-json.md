# JSON 輸出模板

本文件定義 `backsolve-miner-vs-metal-ratio-with-fundamentals` 的標準 JSON 輸出結構。

## 完整結構

```json
{
  "skill": "backsolve_miner_vs_metal_ratio_with_fundamentals",
  "version": "0.1.0",
  "generated_at": "2026-01-21T12:00:00Z",

  "inputs": {
    "metal_symbol": "SI=F",
    "miner_universe": {
      "type": "etf_holdings",
      "etf_ticker": "SIL"
    },
    "region_profile": "us_sec",
    "time_range": {
      "start": "2015-01-01",
      "end": "2026-01-21",
      "frequency": "weekly"
    },
    "ratio_thresholds": {
      "bottom_quantile": 0.20,
      "top_quantile": 0.80
    },
    "fundamental_methods": {
      "aisc_method": "hybrid",
      "leverage_method": "net_debt_to_ev",
      "multiple_method": "ev_to_ebitda",
      "dilution_method": "weighted_avg_shares"
    }
  },

  "now": {
    "date": "2026-01-17",
    "metal_price": 94.4,
    "miner_price": 103.4,
    "ratio": 1.13,
    "ratio_percentile": 0.111,
    "zone": "bottom"
  },

  "thresholds": {
    "bottom_ratio": 1.20,
    "top_ratio": 1.70,
    "median_ratio": 1.51,
    "current_vs_bottom": -0.06,
    "current_vs_top": -0.34
  },

  "fundamentals_weighted": {
    "aisc_usd_per_oz": 28.0,
    "net_debt_millions": 1250,
    "ev_millions": 5000,
    "net_debt_to_ev": 0.25,
    "ebitda_millions": 780,
    "ev_to_ebitda": 6.4,
    "shares_millions": 450,
    "shares_yoy_change": 0.12,
    "holdings_count": 35,
    "top10_weight": 0.62
  },

  "factors_now": {
    "cost_factor_C": 0.7034,
    "leverage_factor_1_minus_L": 0.75,
    "multiple_M": 6.4,
    "dilution_discount_D": 0.89,
    "calibration_K": 0.27
  },

  "factor_changes_yoy": {
    "cost_factor_change": -0.05,
    "leverage_factor_change": -0.02,
    "multiple_change": -0.18,
    "dilution_change": -0.12,
    "dominant_driver": "multiple_compression"
  },

  "backsolve_to_top": {
    "target_ratio": 1.70,
    "ratio_multiplier": 1.50,
    "single_factor": {
      "multiple_only_need": 9.6,
      "multiple_change_pct": 0.50,
      "deleverage_only_need_1_minus_L": 1.125,
      "deleverage_feasible": false,
      "cost_only_need_C": 1.055,
      "cost_only_implied_aisc": -5.2,
      "cost_feasible": false,
      "dilution_only_need_D": 1.335,
      "dilution_feasible": false
    },
    "two_factor_grid": [
      {
        "scenario": "multiple_up_metal_down",
        "multiple_change": 0.20,
        "metal_change": -0.15,
        "achieved_multiplier": 1.52,
        "hits_target": true
      },
      {
        "scenario": "multiple_up_metal_down",
        "multiple_change": 0.30,
        "metal_change": 0.00,
        "achieved_multiplier": 1.30,
        "hits_target": false
      },
      {
        "scenario": "multiple_up_deleverage",
        "multiple_change": 0.15,
        "leverage_change": -0.10,
        "achieved_multiplier": 1.38,
        "hits_target": false
      }
    ],
    "minimum_combination": {
      "multiple_change": 0.20,
      "metal_change": -0.15,
      "or_equivalent": "EV/EBITDA 從 6.4x 升至 7.7x + 白銀從 $94 跌至 $80"
    }
  },

  "backsolve_to_median": {
    "target_ratio": 1.51,
    "ratio_multiplier": 1.34,
    "single_factor": {
      "multiple_only_need": 8.6,
      "multiple_change_pct": 0.34
    }
  },

  "event_study": {
    "bottom_threshold": 1.20,
    "min_separation_days": 180,
    "events_count": 5,
    "bottom_events": [
      {
        "date": "2015-08-07",
        "ratio": 1.15,
        "aisc": 18.5,
        "net_debt_to_ev": 0.22,
        "ev_to_ebitda": 5.2,
        "shares_yoy": 0.08,
        "dominant_driver": "multiple_compression",
        "context": "商品熊市末期"
      },
      {
        "date": "2020-03-20",
        "ratio": 1.08,
        "aisc": 22.0,
        "net_debt_to_ev": 0.35,
        "ev_to_ebitda": 4.5,
        "shares_yoy": 0.15,
        "dominant_driver": "leverage_spike",
        "context": "COVID 危機"
      },
      {
        "date": "2022-09-02",
        "ratio": 1.12,
        "aisc": 26.0,
        "net_debt_to_ev": 0.28,
        "ev_to_ebitda": 5.8,
        "shares_yoy": 0.10,
        "dominant_driver": "cost_increase",
        "context": "通膨推高 AISC"
      },
      {
        "date": "2024-06-28",
        "ratio": 1.10,
        "aisc": 27.5,
        "net_debt_to_ev": 0.26,
        "ev_to_ebitda": 5.5,
        "shares_yoy": 0.14,
        "dominant_driver": "dilution",
        "context": ""
      },
      {
        "date": "2026-01-02",
        "ratio": 1.13,
        "aisc": 28.0,
        "net_debt_to_ev": 0.25,
        "ev_to_ebitda": 6.4,
        "shares_yoy": 0.12,
        "dominant_driver": "multiple_compression",
        "context": "當前"
      }
    ],
    "driver_frequency": {
      "multiple_compression": 3,
      "cost_increase": 2,
      "leverage_spike": 1,
      "dilution": 2
    }
  },

  "holdings_detail": [
    {
      "ticker": "PAAS",
      "name": "Pan American Silver",
      "weight": 0.125,
      "aisc": 24.5,
      "aisc_method": "reported",
      "net_debt_to_ev": 0.18,
      "ev_to_ebitda": 7.2,
      "shares_yoy": 0.05
    },
    {
      "ticker": "AG",
      "name": "First Majestic Silver",
      "weight": 0.082,
      "aisc": 26.8,
      "aisc_method": "reported",
      "net_debt_to_ev": 0.22,
      "ev_to_ebitda": 6.8,
      "shares_yoy": 0.08
    }
  ],

  "summary": "SIL/白銀比率處於歷史底部區間（11.1% 分位數），主要驅動因素為倍數壓縮（EV/EBITDA 從 8x 壓縮至 6.4x）。回到歷史頂部需要倍數擴張約 50%，或結合倍數 +20% 與白銀回調 -15%。",

  "notes": [
    "AISC 使用 hybrid 方法回算，部分公司為 proxy 值",
    "財報數據時滯 1-2 季，反映過去而非當前狀態",
    "建議交叉驗證：COT 持倉、ETF 流量、美元/實質利率",
    "比率訊號衡量「相對估值」，非單邊價格預測"
  ],

  "data_sources": {
    "prices": "yfinance",
    "filings": "sec_edgar",
    "holdings": "globalxetfs.com",
    "holdings_date": "2026-01-15"
  }
}
```

## 欄位說明

### 頂層欄位

| 欄位         | 類型   | 說明                         |
|--------------|--------|------------------------------|
| skill        | string | 技能 ID                      |
| version      | string | 技能版本                     |
| generated_at | string | 輸出生成時間（ISO 8601）     |
| inputs       | object | 輸入參數                     |
| now          | object | 當前狀態                     |
| thresholds   | object | 歷史分位門檻                 |
| fundamentals_weighted | object | 權重加總後的基本面        |
| factors_now  | object | 當前四大因子                 |
| factor_changes_yoy | object | 因子 YoY 變化            |
| backsolve_to_top | object | 反推到頂部               |
| event_study  | object | 歷史事件研究                 |
| holdings_detail | array | 持股明細                   |
| summary      | string | 摘要                         |
| notes        | array  | 注意事項                     |
| data_sources | object | 數據來源標註                 |

### now 欄位

| 欄位             | 類型   | 說明                       |
|------------------|--------|----------------------------|
| date             | string | 數據日期                   |
| metal_price      | number | 金屬價格                   |
| miner_price      | number | 礦業股/ETF 價格            |
| ratio            | number | 比率                       |
| ratio_percentile | number | 歷史分位數（0-1）          |
| zone             | string | 區間判定（bottom/low/...） |

### factors_now 欄位

| 欄位                   | 類型   | 說明                       |
|------------------------|--------|----------------------------|
| cost_factor_C          | number | 成本因子 = 1 - AISC/S      |
| leverage_factor_1_minus_L | number | 槓桿因子 = 1 - ND/EV    |
| multiple_M             | number | 倍數因子 = EV/EBITDA       |
| dilution_discount_D    | number | 稀釋因子 = Shares_base/now |
| calibration_K          | number | 校準常數                   |
