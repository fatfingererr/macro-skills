# 完整輸入參數定義

## 參數總覽

| 參數分類 | 參數數量 | 說明 |
|----------|----------|------|
| 目標序列 | 1 | 要分析的 FRED 序列 |
| 窗口設定 | 3 | 近期/基準窗口配置 |
| 正規化 | 2 | 資料預處理方法 |
| 相似度 | 2 | 形狀比對方法 |
| 門檻 | 3 | 警報觸發條件 |
| 交叉驗證 | 2 | 壓力指標配置 |
| 輸出 | 2 | 輸出格式與路徑 |

---

## 詳細參數定義

### 目標序列參數

#### target_series
| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設值 | "WUDSHO" |
| 必要性 | Optional |
| 說明 | 目標 FRED 時間序列代碼 |

**可用值**:
- `WUDSHO`: 未攤銷折價（預設）
- `WSHOSHO`: 持有證券總額
- 其他 FRED 週頻序列

---

### 窗口設定參數

#### baseline_windows
| 屬性 | 值 |
|------|-----|
| 類型 | array[object] |
| 必要性 | Required |
| 說明 | 歷史參考事件窗口清單 |

**物件結構**:
```json
{
  "name": "COVID_2020",
  "start": "2020-01-01",
  "end": "2020-06-30"
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| name | string | 事件名稱（唯一識別） |
| start | date | 窗口起始日期（YYYY-MM-DD） |
| end | date | 窗口結束日期（YYYY-MM-DD） |

**預設值**:
```json
[
  {"name": "COVID_2020", "start": "2020-01-01", "end": "2020-06-30"},
  {"name": "GFC_2008", "start": "2008-09-01", "end": "2009-03-31"},
  {"name": "TAPER_2013", "start": "2013-05-01", "end": "2013-09-30"},
  {"name": "RATE_HIKE_2022", "start": "2022-01-01", "end": "2022-12-31"}
]
```

#### recent_window_days
| 屬性 | 值 |
|------|-----|
| 類型 | int |
| 預設值 | 120 |
| 範圍 | 30 ~ 365 |
| 必要性 | Required |
| 說明 | 近期比對窗口長度（天） |

**建議**:
- 60: 短期比對（約 8 週）
- 120: 標準比對（約 17 週）
- 180: 中期比對（約 26 週）

#### history_start_date
| 屬性 | 值 |
|------|-----|
| 類型 | string (date) |
| 預設值 | "2015-01-01" |
| 必要性 | Optional |
| 說明 | 歷史資料起始日期 |

---

### 正規化參數

#### resample_freq
| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設值 | "W" |
| 可用值 | "W", "D" |
| 必要性 | Optional |
| 說明 | 資料重採樣頻率 |

**說明**:
- `W`: 週頻（推薦，WUDSHO 原生頻率）
- `D`: 日頻（需要內插，可能引入噪音）

#### normalize_method
| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設值 | "zscore" |
| 可用值 | "zscore", "minmax", "pct_change" |
| 必要性 | Optional |
| 說明 | 正規化方法 |

**方法說明**:
| 方法 | 公式 | 適用場景 |
|------|------|----------|
| zscore | (x - mean) / std | 形狀比對（推薦） |
| minmax | (x - min) / (max - min) | 範圍統一 |
| pct_change | (x[t] - x[t-1]) / x[t-1] | 動量分析 |

---

### 相似度參數

#### similarity_metrics
| 屬性 | 值 |
|------|-----|
| 類型 | array[string] |
| 預設值 | ["corr", "dtw", "shape_features"] |
| 必要性 | Optional |
| 說明 | 要計算的相似度指標 |

**可用值**:
| 值 | 說明 | 計算成本 |
|----|------|----------|
| corr | 皮爾遜相關係數 | 低 |
| dtw | 動態時間校正距離 | 中 |
| shape_features | 形狀特徵相似度 | 低 |

#### similarity_weights
| 屬性 | 值 |
|------|-----|
| 類型 | object |
| 預設值 | {"corr": 0.4, "dtw": 0.3, "shape_features": 0.3} |
| 必要性 | Optional |
| 說明 | 各相似度指標的權重 |

---

### 門檻參數

#### alert_thresholds
| 屬性 | 值 |
|------|-----|
| 類型 | object |
| 必要性 | Optional |
| 說明 | 觸發警報的門檻 |

**預設值**:
```json
{
  "corr_min": 0.7,
  "dtw_max": 1.5,
  "risk_score_min": 0.6
}
```

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| corr_min | float | 0.7 | 相關係數最低門檻 |
| dtw_max | float | 1.5 | DTW 距離最高門檻 |
| risk_score_min | float | 0.6 | 風險分數最低門檻 |

---

### 交叉驗證參數

#### confirmatory_indicators
| 屬性 | 值 |
|------|-----|
| 類型 | array[object] |
| 必要性 | Optional |
| 說明 | 交叉驗證指標清單 |

**物件結構**:
```json
{
  "name": "credit_spread",
  "source": "FRED",
  "series": "BAMLC0A0CM",
  "weight": 0.25,
  "stress_threshold": 1.5
}
```

| 欄位 | 類型 | 說明 |
|------|------|------|
| name | string | 指標名稱（唯一識別） |
| source | string | 資料來源 |
| series | string | 系列代碼 |
| weight | float | 權重（0~1） |
| stress_threshold | float | 壓力門檻（z-score） |

**預設值**:
```json
[
  {"name": "credit_spread", "source": "FRED", "series": "BAMLC0A0CM", "weight": 0.25, "stress_threshold": 1.5},
  {"name": "hy_spread", "source": "FRED", "series": "BAMLH0A0HYM2", "weight": 0.20, "stress_threshold": 1.5},
  {"name": "equity_vol", "source": "FRED", "series": "VIXCLS", "weight": 0.20, "stress_threshold": 1.5},
  {"name": "yield_curve", "source": "FRED", "series": ["DGS10", "DGS2"], "weight": 0.15, "stress_threshold": -1.0},
  {"name": "fed_balance", "source": "FRED", "series": "WALCL", "weight": 0.20, "stress_threshold": 1.0}
]
```

#### lookahead_days
| 屬性 | 值 |
|------|-----|
| 類型 | int |
| 預設值 | 60 |
| 範圍 | 30 ~ 365 |
| 必要性 | Optional |
| 說明 | 前瞻期（情境敘事用） |

---

### 輸出參數

#### output_path
| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設值 | "output/pattern_analysis_{date}.json" |
| 必要性 | Optional |
| 說明 | JSON 結果輸出路徑 |

#### output_format
| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設值 | "json" |
| 可用值 | "json", "markdown", "both" |
| 必要性 | Optional |
| 說明 | 輸出格式 |

---

## 命令列參數對照

```bash
python scripts/pattern_detector.py \
  --target_series WUDSHO \
  --baseline_windows "COVID_2020:2020-01-01:2020-06-30,GFC_2008:2008-09-01:2009-03-31" \
  --recent_window_days 120 \
  --normalize_method zscore \
  --similarity_metrics "corr,dtw,shape_features" \
  --output result.json
```

| 命令列參數 | 對應配置參數 |
|------------|--------------|
| --target_series | target_series |
| --baseline_windows | baseline_windows（格式: name:start:end,name:start:end） |
| --recent_window_days | recent_window_days |
| --normalize_method | normalize_method |
| --similarity_metrics | similarity_metrics（逗號分隔） |
| --output | output_path |
| --quick | 使用預設參數快速執行 |
| --markdown | output_format = "markdown" |

---

## 配置檔範例

**config.json**:
```json
{
  "target_series": "WUDSHO",
  "baseline_windows": [
    {"name": "COVID_2020", "start": "2020-01-01", "end": "2020-06-30"},
    {"name": "GFC_2008", "start": "2008-09-01", "end": "2009-03-31"}
  ],
  "recent_window_days": 120,
  "resample_freq": "W",
  "normalize_method": "zscore",
  "similarity_metrics": ["corr", "dtw", "shape_features"],
  "similarity_weights": {"corr": 0.4, "dtw": 0.3, "shape_features": 0.3},
  "alert_thresholds": {
    "corr_min": 0.7,
    "dtw_max": 1.5,
    "risk_score_min": 0.6
  },
  "confirmatory_indicators": [
    {"name": "credit_spread", "source": "FRED", "series": "BAMLC0A0CM", "weight": 0.25, "stress_threshold": 1.5}
  ],
  "lookahead_days": 60,
  "output_path": "output/result.json",
  "output_format": "both"
}
```

使用：
```bash
python scripts/pattern_detector.py --config config.json
```
