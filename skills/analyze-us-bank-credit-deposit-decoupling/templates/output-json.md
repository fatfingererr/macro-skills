# JSON 輸出模板

本文件定義美國銀行信貸存款脫鉤分析的 JSON 輸出結構。

---

## 完整輸出結構

```json
{
  "skill": "analyze_bank_credit_deposit_decoupling",
  "version": "0.1.0",
  "generated_at": "2026-01-23T10:30:00Z",

  "status": "success",

  "analysis_period": {
    "start": "2022-06-01",
    "end": "2026-01-23",
    "frequency": "weekly",
    "observation_count": 187
  },

  "data_sources": {
    "loans": {
      "series_id": "TOTLL",
      "name": "Loans and Leases in Bank Credit, All Commercial Banks",
      "unit": "Billions USD",
      "latest_value": 12450.5,
      "latest_date": "2026-01-22"
    },
    "deposits": {
      "series_id": "DPSACBW027SBOG",
      "name": "Deposits, All Commercial Banks",
      "unit": "Billions USD",
      "latest_value": 17890.2,
      "latest_date": "2026-01-22"
    },
    "rrp": {
      "series_id": "RRPONTSYD",
      "name": "Overnight Reverse Repurchase Agreements",
      "unit": "Billions USD",
      "latest_value": 520.8,
      "latest_date": "2026-01-22"
    }
  },

  "cumulative_changes": {
    "base_date": "2022-06-01",
    "new_loans_billion_usd": 2100.5,
    "new_deposits_billion_usd": 520.3,
    "rrp_change_billion_usd": 1450.2,
    "unit": "Billions USD"
  },

  "decoupling_metrics": {
    "decoupling_gap_billion_usd": 1580.2,
    "decoupling_gap_trillion_usd": 1.58,
    "deposit_stress_ratio": 0.752,
    "deposit_stress_ratio_percentile": 0.94,
    "rrp_gap_correlation": 0.87
  },

  "time_series": {
    "dates": ["2022-06-01", "2022-06-08", "..."],
    "loan_change": [0, 15.2, "..."],
    "deposit_change": [0, 8.1, "..."],
    "rrp_change": [0, 12.5, "..."],
    "decoupling_gap": [0, 7.1, "..."],
    "stress_ratio": [0, 0.47, "..."]
  },

  "assessment": {
    "tightening_type": "hidden_balance_sheet_tightening",
    "tightening_type_label": "隱性資產負債表緊縮",
    "primary_driver": "RRP_liquidity_absorption",
    "primary_driver_label": "RRP 流動性吸收",
    "confidence": "high",
    "confidence_score": 0.85
  },

  "stress_level": {
    "current": "extreme",
    "thresholds": {
      "low": 0.3,
      "medium": 0.5,
      "high": 0.7,
      "extreme": 0.85
    }
  },

  "historical_context": {
    "current_percentile": 0.94,
    "comparable_periods": [
      {
        "period": "2018 Q4",
        "stress_ratio": 0.67,
        "outcome": "Fed 提前結束 QT"
      },
      {
        "period": "2023 Q1",
        "stress_ratio": 0.80,
        "outcome": "SVB 危機"
      }
    ]
  },

  "macro_implication": "本次緊縮並非來自銀行縮手放貸，而是聯準會透過 RRP 抽走體系存款，導致市場必須爭奪有限的存款來支撐既有負債結構，屬於「隱性金融緊縮」狀態。",

  "recommended_next_checks": [
    "監控 RRP 規模變化趨勢",
    "觀察銀行存款利率是否上升",
    "追蹤 SOFR-Fed Funds 利差變化",
    "關注大額存款（>$250K）外逃跡象"
  ],

  "caveats": [
    "本分析假設 RRP 是主要的存款吸收來源，忽略 TGA 等其他因素",
    "週頻數據可能錯過日內波動",
    "deposit_stress_ratio 歷史分位數基於 2013 年後數據"
  ],

  "artifacts": {
    "chart_path": "output/decoupling_chart_2026-01-23.png",
    "cache_files": [
      "cache/loans_TOTLL.json",
      "cache/deposits_DPSACBW027SBOG.json",
      "cache/rrp_RRPONTSYD.json"
    ]
  }
}
```

---

## 欄位說明

### 頂層欄位

| 欄位           | 類型   | 說明                                  |
|----------------|--------|---------------------------------------|
| `skill`        | string | 技能名稱                              |
| `version`      | string | 輸出格式版本                          |
| `generated_at` | string | 生成時間（ISO 8601）                  |
| `status`       | string | 執行狀態（success / partial / error） |

### analysis_period

| 欄位                | 類型    | 說明         |
|---------------------|---------|--------------|
| `start`             | string  | 分析起始日期 |
| `end`               | string  | 分析結束日期 |
| `frequency`         | string  | 數據頻率     |
| `observation_count` | integer | 觀測值數量   |

### decoupling_metrics

| 欄位                         | 類型  | 說明                 |
|------------------------------|-------|----------------------|
| `decoupling_gap_billion_usd` | float | 脫鉤落差（十億美元） |
| `deposit_stress_ratio`       | float | 存款壓力比率（0-1）  |
| `rrp_gap_correlation`        | float | RRP 與 Gap 相關係數  |

### assessment

| 欄位              | 類型   | 可能值                                                                  |
|-------------------|--------|-------------------------------------------------------------------------|
| `tightening_type` | string | hidden_balance_sheet_tightening, traditional_credit_tightening, neutral |
| `primary_driver`  | string | RRP_liquidity_absorption, credit_contraction, both                      |
| `confidence`      | string | high, medium, low                                                       |

---

## 簡化輸出（quick 模式）

```json
{
  "as_of": "2026-01-23",
  "decoupling_gap_trillion_usd": 1.58,
  "deposit_stress_ratio": 0.75,
  "tightening_type": "hidden_balance_sheet_tightening",
  "confidence": "high",
  "summary": "銀行負債端壓力顯著，隱性緊縮狀態"
}
```
