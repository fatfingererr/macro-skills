# JSON 輸出模板 (Output JSON Template)

本文檔定義 `analyze-move-risk-gauges-leadlag` 技能的 JSON 輸出結構。

---

## 完整輸出結構

```json
{
  "skill": "analyze-move-risk-gauges-leadlag",
  "version": "0.1.0",
  "as_of": "2026-01-23",
  "params": {
    "start_date": "2024-01-01",
    "end_date": "2026-01-23",
    "rates_vol_symbol": "MOVE",
    "equity_vol_symbol": "VIX",
    "credit_spread_symbol": "CDX_IG_PROXY",
    "jgb_yield_symbol": "JGB10Y",
    "freq": "D",
    "smooth_window": 5,
    "zscore_window": 60,
    "lead_lag_max_days": 20,
    "shock_window_days": 5,
    "shock_threshold_bps": 15
  },
  "status": "ok",
  "headline": "MOVE not spooked by JGB yield moves and appears to lead VIX/Credit lower.",
  "confidence": "HIGH",
  "leadlag": {
    "MOVE_vs_VIX": {
      "best_lag_days": 6,
      "corr": 0.72,
      "interpretation": "MOVE leads VIX by ~6 trading days"
    },
    "MOVE_vs_CREDIT": {
      "best_lag_days": 4,
      "corr": 0.61,
      "interpretation": "MOVE leads Credit Spread by ~4 trading days"
    }
  },
  "spooked_check": {
    "shock_definition": "abs(JGB10Y change over 5d) >= 15bp",
    "shock_count": 3,
    "shock_dates": ["2024-03-15", "2024-07-22", "2025-01-10"],
    "mean_MOVE_reaction_on_shocks": 0.8,
    "median_MOVE_reaction_on_shocks": 0.5,
    "historical_median_reaction": 4.6,
    "MOVE_zscore_now": -0.4,
    "spooked_verdict": "NOT_SPOOKED"
  },
  "direction_alignment": {
    "MOVE_down_and_VIX_down_ratio": 0.58,
    "MOVE_down_and_CREDIT_down_ratio": 0.55,
    "interpretation": "When MOVE declines, VIX and Credit follow 55-58% of the time"
  },
  "data_quality": {
    "total_observations": 520,
    "missing_ratio": {
      "MOVE": 0.02,
      "VIX": 0.0,
      "CREDIT": 0.01,
      "JGB10Y": 0.03
    },
    "data_sources_used": {
      "MOVE": "rates_vol_proxy",
      "VIX": "yahoo_finance",
      "CREDIT": "fred_bamlc0a0cm",
      "JGB10Y": "investing_com"
    },
    "warnings": []
  },
  "artifacts": {
    "chart_path": "output/leadlag_analysis_2026-01-23.png",
    "data_cache_path": "cache/data.csv"
  },
  "reasons": [
    "MOVE reaction to JGB shocks (mean +0.8) is below historical median (+4.6)",
    "MOVE vs VIX cross-correlation peaks at lag +6 days with corr 0.72",
    "MOVE vs Credit cross-correlation peaks at lag +4 days with corr 0.61",
    "Direction alignment: 58% of MOVE declines are accompanied by VIX declines"
  ],
  "notes": [
    "MOVE data is proxied using DGS10 realized volatility due to fetch failure",
    "CDX IG is proxied by ICE BofA IG OAS (BAMLC0A0CM)"
  ]
}
```

---

## 欄位說明

### 頂層欄位

| 欄位         | 類型   | 說明                                  |
|--------------|--------|---------------------------------------|
| `skill`      | string | 技能名稱                              |
| `version`    | string | 技能版本                              |
| `as_of`      | string | 分析日期 (YYYY-MM-DD)                 |
| `params`     | object | 使用的參數                            |
| `status`     | string | 執行狀態 (`ok` / `error` / `warning`) |
| `headline`   | string | 一句話結論                            |
| `confidence` | string | 信心水準 (`HIGH` / `MEDIUM` / `LOW`)  |

### leadlag 物件

| 欄位             | 類型   | 說明                          |
|------------------|--------|-------------------------------|
| `best_lag_days`  | int    | 最大相關出現的 lag（正=領先） |
| `corr`           | float  | 最大相關係數                  |
| `interpretation` | string | 人類可讀的解讀                |

### spooked_check 物件

| 欄位                             | 類型   | 說明                                 |
|----------------------------------|--------|--------------------------------------|
| `shock_definition`               | string | 衝擊事件定義                         |
| `shock_count`                    | int    | 識別到的衝擊事件數                   |
| `shock_dates`                    | array  | 衝擊事件日期列表                     |
| `mean_MOVE_reaction_on_shocks`   | float  | 衝擊時 MOVE 平均反應                 |
| `median_MOVE_reaction_on_shocks` | float  | 衝擊時 MOVE 中位數反應               |
| `historical_median_reaction`     | float  | 歷史中位數反應（用於比較）           |
| `MOVE_zscore_now`                | float  | 當前 MOVE 的 Z 分數                  |
| `spooked_verdict`                | string | 判定結果 (`SPOOKED` / `NOT_SPOOKED`) |

### direction_alignment 物件

| 欄位                              | 類型   | 說明                            |
|-----------------------------------|--------|---------------------------------|
| `MOVE_down_and_VIX_down_ratio`    | float  | MOVE 下行時 VIX 也下行的比例    |
| `MOVE_down_and_CREDIT_down_ratio` | float  | MOVE 下行時 Credit 也下行的比例 |
| `interpretation`                  | string | 人類可讀的解讀                  |

### data_quality 物件

| 欄位                 | 類型   | 說明               |
|----------------------|--------|--------------------|
| `total_observations` | int    | 總觀察數           |
| `missing_ratio`      | object | 各序列缺值比例     |
| `data_sources_used`  | object | 實際使用的數據來源 |
| `warnings`           | array  | 數據品質警告       |

### artifacts 物件

| 欄位              | 類型   | 說明           |
|-------------------|--------|----------------|
| `chart_path`      | string | 生成圖表的路徑 |
| `data_cache_path` | string | 數據快取路徑   |

### reasons 陣列

結論的支持證據列表，每項為一個字串。

### notes 陣列

分析過程中的註記（如使用代理數據）。

---

## 精簡輸出（Quick Mode）

快速模式輸出較少欄位：

```json
{
  "status": "ok",
  "headline": "MOVE not spooked by JGB yield moves and appears to lead VIX/Credit lower.",
  "leadlag": {
    "MOVE_vs_VIX": {"best_lag_days": 6, "corr": 0.72},
    "MOVE_vs_CREDIT": {"best_lag_days": 4, "corr": 0.61}
  },
  "spooked_check": {
    "shock_count": 3,
    "mean_MOVE_reaction_on_shocks": 0.8,
    "MOVE_zscore_now": -0.4
  },
  "direction_alignment": {
    "MOVE_down_and_VIX_down_ratio": 0.58,
    "MOVE_down_and_CREDIT_down_ratio": 0.55
  }
}
```

---

## 錯誤輸出

當執行失敗時：

```json
{
  "skill": "analyze-move-risk-gauges-leadlag",
  "as_of": "2026-01-23",
  "status": "error",
  "error": {
    "code": "DATA_FETCH_FAILED",
    "message": "Failed to fetch JGB10Y data from all sources",
    "details": {
      "primary_source": "investing.com - connection timeout",
      "fallback_source": "FRED - series not available in requested frequency"
    }
  },
  "partial_result": {
    "leadlag": {
      "MOVE_vs_VIX": {"best_lag_days": 6, "corr": 0.72}
    },
    "note": "JGB-related analysis skipped due to data unavailability"
  }
}
```

---

## 驗證範例

```python
import json
from jsonschema import validate

schema = {
    "type": "object",
    "required": ["status", "headline", "leadlag", "spooked_check", "direction_alignment"],
    "properties": {
        "status": {"type": "string", "enum": ["ok", "error", "warning"]},
        "headline": {"type": "string"},
        "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
        "leadlag": {
            "type": "object",
            "properties": {
                "MOVE_vs_VIX": {
                    "type": "object",
                    "properties": {
                        "best_lag_days": {"type": "integer"},
                        "corr": {"type": "number", "minimum": -1, "maximum": 1}
                    }
                }
            }
        },
        "spooked_check": {
            "type": "object",
            "properties": {
                "shock_count": {"type": "integer", "minimum": 0},
                "mean_MOVE_reaction_on_shocks": {"type": ["number", "null"]},
                "MOVE_zscore_now": {"type": "number"}
            }
        }
    }
}

# Validate output
with open("result.json", "r") as f:
    result = json.load(f)
    validate(instance=result, schema=schema)
```
