# JSON 輸出結構定義

## 完整輸出結構

```json
{
  "skill": "detect-fed-unamortized-discount-pattern",
  "version": "0.1.0",
  "as_of_date": "2026-01-26",
  "target_series": "WUDSHO",
  "parameters": {
    "recent_window_days": 120,
    "resample_freq": "W",
    "normalize_method": "zscore",
    "similarity_metrics": ["corr", "dtw", "shape_features"]
  },
  "best_match": {
    "baseline": "COVID_2020",
    "segment_start": "2020-01-08",
    "segment_end": "2020-06-17",
    "corr": 0.91,
    "dtw": 0.38,
    "feature_sim": 0.82,
    "pattern_similarity_score": 0.88
  },
  "all_matches": [
    {
      "baseline": "COVID_2020",
      "segment_start": "2020-01-08",
      "segment_end": "2020-06-17",
      "corr": 0.91,
      "dtw": 0.38,
      "feature_sim": 0.82,
      "pattern_similarity_score": 0.88
    },
    {
      "baseline": "RATE_HIKE_2022",
      "segment_start": "2022-03-01",
      "segment_end": "2022-07-15",
      "corr": 0.78,
      "dtw": 0.55,
      "feature_sim": 0.75,
      "pattern_similarity_score": 0.75
    }
  ],
  "stress_confirmation": {
    "score": 0.22,
    "details": [
      {
        "name": "credit_spread",
        "series": "BAMLC0A0CM",
        "current_value": 1.05,
        "historical_mean": 0.95,
        "historical_std": 0.25,
        "z": 0.4,
        "signal": "neutral",
        "weight": 0.25
      },
      {
        "name": "equity_vol",
        "series": "VIXCLS",
        "current_value": 14.5,
        "historical_mean": 18.2,
        "historical_std": 8.5,
        "z": -0.44,
        "signal": "mild_risk_on",
        "weight": 0.20
      },
      {
        "name": "hy_spread",
        "series": "BAMLH0A0HYM2",
        "current_value": 3.2,
        "historical_mean": 3.0,
        "historical_std": 1.2,
        "z": 0.17,
        "signal": "neutral",
        "weight": 0.20
      },
      {
        "name": "yield_curve",
        "series": "DGS10-DGS2",
        "current_value": 0.15,
        "historical_mean": 0.8,
        "historical_std": 0.6,
        "z": -1.08,
        "signal": "mild_stress",
        "weight": 0.15
      },
      {
        "name": "fed_balance",
        "series": "WALCL",
        "current_value": 7500000,
        "historical_mean": 7200000,
        "historical_std": 500000,
        "z": 0.6,
        "signal": "neutral",
        "weight": 0.20
      }
    ]
  },
  "composite_risk_score": 0.49,
  "risk_level": "medium",
  "interpretation": {
    "summary": "走勢形狀與 COVID 早期片段相似度高（0.88），但壓力驗證指標偏中性（0.22），綜合風險分數 0.49（中等）。這更像是「利率/會計結構造成的圖形相似」，不足以支持「系統性壓力升高」的假說。",
    "pattern_analysis": {
      "finding": "近期 WUDSHO 走勢與 2020 年 1-6 月的形狀高度相關",
      "possible_causes": [
        "利率環境變化驅動（最可能）",
        "持有債券久期結構調整",
        "會計攤銷時程效果"
      ],
      "unlikely_cause": "系統性金融壓力（缺乏壓力指標共振）"
    },
    "stress_analysis": {
      "finding": "壓力驗證指標大多處於中性區間",
      "key_observations": [
        "信用利差未顯著走寬（z=0.4）",
        "VIX 偏低（z=-0.44），顯示股市風險偏好中性",
        "殖利率曲線輕微倒掛，但非極端"
      ]
    },
    "what_to_watch_next_60d": [
      "若形狀相似度維持高檔，同時信用利差明顯走寬（z > 1.5），才應升級風險警報",
      "若 VIX 持續上升並突破 25，顯示市場開始定價風險",
      "觀察 Fed 是否啟用緊急流動性工具（如 BTFP 類似機制）"
    ],
    "rebuttal_to_claim": [
      "「像」可以量化（相關係數 0.91），但「像 COVID」不等於「會發生 COVID 級事件」",
      "WUDSHO 變動最常見的原因是利率效果，不是金融壓力",
      "把「黑天鵝」定義成「精心策劃」屬於不可驗證敘事；本技能只輸出可被公開資料支持或反駁的部分"
    ]
  },
  "data_quality": {
    "target_series": {
      "series_id": "WUDSHO",
      "data_start": "2015-01-07",
      "data_end": "2026-01-22",
      "frequency": "W",
      "delay_days": 4,
      "missing_values": 0
    },
    "confirmatory_series": [
      {"series_id": "BAMLC0A0CM", "data_end": "2026-01-24", "status": "ok"},
      {"series_id": "VIXCLS", "data_end": "2026-01-24", "status": "ok"},
      {"series_id": "BAMLH0A0HYM2", "data_end": "2026-01-24", "status": "ok"},
      {"series_id": "DGS10", "data_end": "2026-01-24", "status": "ok"},
      {"series_id": "DGS2", "data_end": "2026-01-24", "status": "ok"},
      {"series_id": "WALCL", "data_end": "2026-01-22", "status": "ok"}
    ]
  },
  "caveats": [
    "形狀相似不代表因果相同；該序列可能強烈受利率、持有期限結構與會計攤銷影響。",
    "若缺乏壓力指標同步惡化，不應把圖形類比直接升級成『黑天鵝預言』。",
    "本工具提供的是『樣態比對 + 交叉驗證』，不是預測器。",
    "任何單一序列都不應被用來做高確信度的危機斷言。",
    "歷史事件樣本有限（4-6 次），統計推論受限。"
  ],
  "metadata": {
    "executed_at": "2026-01-26T10:30:00+08:00",
    "execution_time_ms": 2350,
    "cache_used": true,
    "skill_version": "0.1.0"
  }
}
```

---

## 欄位說明

### 頂層欄位

| 欄位                 | 類型          | 說明                   |
|----------------------|---------------|------------------------|
| skill                | string        | 技能名稱               |
| version              | string        | 技能版本               |
| as_of_date           | string (date) | 分析截止日期           |
| target_series        | string        | 目標 FRED 系列代碼     |
| parameters           | object        | 使用的參數             |
| best_match           | object        | 最佳匹配的歷史片段     |
| all_matches          | array         | 所有歷史窗口的匹配結果 |
| stress_confirmation  | object        | 壓力驗證結果           |
| composite_risk_score | float         | 合成風險分數 [0-1]     |
| risk_level           | string        | 風險等級               |
| interpretation       | object        | 解讀框架               |
| data_quality         | object        | 資料品質資訊           |
| caveats              | array[string] | 風險警語               |
| metadata             | object        | 執行元資料             |

### best_match 欄位

| 欄位                     | 類型          | 說明                  |
|--------------------------|---------------|-----------------------|
| baseline                 | string        | 基準窗口名稱          |
| segment_start            | string (date) | 匹配片段起始日        |
| segment_end              | string (date) | 匹配片段結束日        |
| corr                     | float         | 相關係數 [-1, 1]      |
| dtw                      | float         | DTW 距離（正規化）    |
| feature_sim              | float         | 形狀特徵相似度 [0, 1] |
| pattern_similarity_score | float         | 綜合形狀相似度 [0, 1] |

### stress_confirmation 欄位

| 欄位    | 類型  | 說明                |
|---------|-------|---------------------|
| score   | float | 壓力驗證總分 [0, 1] |
| details | array | 各指標詳情          |

### details 物件

| 欄位            | 類型   | 說明          |
|-----------------|--------|---------------|
| name            | string | 指標名稱      |
| series          | string | FRED 系列代碼 |
| current_value   | float  | 當前值        |
| historical_mean | float  | 歷史均值      |
| historical_std  | float  | 歷史標準差    |
| z               | float  | z-score       |
| signal          | string | 訊號判斷      |
| weight          | float  | 權重          |

### signal 可能值

| 值             | 說明         |
|----------------|--------------|
| neutral        | 中性         |
| mild_risk_on   | 輕微風險偏好 |
| mild_stress    | 輕微壓力     |
| stress         | 壓力         |
| extreme_stress | 極端壓力     |

### risk_level 可能值

| 值          | composite_risk_score 範圍 | 說明     |
|-------------|---------------------------|----------|
| low         | < 0.3                     | 低風險   |
| medium      | 0.3 ~ 0.5                 | 中風險   |
| medium_high | 0.5 ~ 0.7                 | 中高風險 |
| high        | > 0.7                     | 高風險   |

---

## 精簡輸出模式

使用 `--quick` 時的精簡輸出：

```json
{
  "as_of_date": "2026-01-26",
  "best_match": {
    "baseline": "COVID_2020",
    "pattern_similarity_score": 0.88
  },
  "stress_confirmation": {
    "score": 0.22
  },
  "composite_risk_score": 0.49,
  "risk_level": "medium",
  "summary": "形狀相似度高但壓力驗證中性，可能是利率效果"
}
```
