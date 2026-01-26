# JSON 輸出結構定義

## 完整輸出結構

```json
{
  "skill": "analyze_jgb_insurer_superlong_flow",
  "version": "0.1.0",
  "as_of": "2026-01-26",
  "status": "success",

  "data_source": {
    "name": "JSDA Trends in Bond Transactions (by investor type)",
    "url": "https://www.jsda.or.jp/",
    "fetch_timestamp": "2026-01-26T10:30:00+09:00",
    "data_version": "2025-12"
  },

  "parameters": {
    "start_date": "2020-01",
    "end_date": "2025-12",
    "investor_group": "insurance_companies",
    "maturity_bucket": "super_long",
    "measure": "net_purchases",
    "frequency": "monthly",
    "currency": "JPY",
    "record_lookback_years": 999,
    "streak_sign": "negative"
  },

  "latest_month": {
    "date": "2025-12",
    "net_purchases_billion_jpy": -822.4,
    "net_purchases_trillion_jpy": -0.8224,
    "net_purchases_usd_billion": null,
    "interpretation": "淨賣出 ¥8,224 億"
  },

  "record_analysis": {
    "is_record_sale": true,
    "record_low_billion_jpy": -822.4,
    "record_low_date": "2025-12",
    "record_high_billion_jpy": 500.0,
    "record_high_date": "2020-03",
    "lookback_period": "全樣本 (2010-01 至 2025-12)",
    "interpretation": "創下歷史最大單月淨賣出紀錄"
  },

  "streak_analysis": {
    "consecutive_negative_months": 5,
    "streak_start": "2025-08",
    "streak_end": "2025-12",
    "cumulative_over_streak_billion_jpy": -1370.0,
    "cumulative_over_streak_trillion_jpy": -1.37,
    "interpretation": "自 2025-08 起連續 5 個月淨賣出，累積 ¥1.37 兆"
  },

  "historical_stats": {
    "sample_period": {
      "start": "2010-01",
      "end": "2025-12"
    },
    "count": 192,
    "mean_billion_jpy": 50.5,
    "std_billion_jpy": 150.3,
    "min_billion_jpy": -822.4,
    "max_billion_jpy": 500.0,
    "median_billion_jpy": 45.0,
    "percentile_25_billion_jpy": -30.0,
    "percentile_75_billion_jpy": 120.0,
    "latest_zscore": -5.81,
    "latest_percentile": 0.005,
    "interpretation": "當前值處於歷史 0.5% 分位，極端偏低"
  },

  "caliber_notes": [
    {
      "type": "maturity_bucket",
      "used": "super_long",
      "note": "JSDA 超長端分類，通常對應 20Y+ 或 30Y+。新聞若使用「10年以上」，數值可能略有差異。"
    },
    {
      "type": "investor_group",
      "used": "insurance_companies",
      "note": "包含壽險 + 產險。若僅需壽險，請使用 life_insurance。"
    },
    {
      "type": "unit",
      "used": "billion_jpy",
      "note": "十億日圓（¥B）。兆日圓 = 十億日圓 ÷ 1000。"
    }
  ],

  "headline_takeaways": [
    "日本保險公司在 2025-12 創下歷史最大單月淨賣出（-¥8,224 億）",
    "已連續 5 個月淨賣出，累積金額達 ¥1.37 兆",
    "當前淨賣出規模處於歷史 0.5% 分位，屬極端事件"
  ],

  "confidence": {
    "level": "high",
    "reasons": [
      "數據來源為 JSDA 官方統計（公開可下載）",
      "計算邏輯透明可重現",
      "無需依賴付費終端"
    ],
    "caveats": [
      "天期桶口徑與新聞可能不完全一致",
      "JSDA 數據約滯後 1 個月發布"
    ]
  },

  "artifacts": [
    {
      "type": "chart",
      "path": "output/jgb_insurer_flow_20260126.png",
      "description": "淨買賣月度走勢圖"
    }
  ]
}
```

---

## 欄位說明

### 頂層欄位

| 欄位      | 類型   | 說明                        |
|-----------|--------|-----------------------------|
| `skill`   | string | Skill 識別碼                |
| `version` | string | Skill 版本                  |
| `as_of`   | string | 分析執行日期                |
| `status`  | string | 執行狀態（success / error） |

### data_source

| 欄位              | 類型   | 說明                     |
|-------------------|--------|--------------------------|
| `name`            | string | 數據來源名稱             |
| `url`             | string | 數據來源網址             |
| `fetch_timestamp` | string | 數據抓取時間（ISO 8601） |
| `data_version`    | string | 數據版本（最新可用月份） |

### parameters

記錄本次分析使用的所有參數，便於重現。

### latest_month

| 欄位                         | 類型       | 說明                         |
|------------------------------|------------|------------------------------|
| `date`                       | string     | 月份（YYYY-MM）              |
| `net_purchases_billion_jpy`  | float      | 淨買入（十億日圓）           |
| `net_purchases_trillion_jpy` | float      | 淨買入（兆日圓）             |
| `net_purchases_usd_billion`  | float/null | 淨買入（十億美元，若有換算） |
| `interpretation`             | string     | 中文解讀                     |

### record_analysis

| 欄位                      | 類型    | 說明                 |
|---------------------------|---------|----------------------|
| `is_record_sale`          | boolean | 是否為歷史最大淨賣出 |
| `record_low_billion_jpy`  | float   | 歷史最低值           |
| `record_low_date`         | string  | 歷史最低值日期       |
| `record_high_billion_jpy` | float   | 歷史最高值           |
| `record_high_date`        | string  | 歷史最高值日期       |
| `lookback_period`         | string  | 回溯期間說明         |
| `interpretation`          | string  | 中文解讀             |

### streak_analysis

| 欄位                                  | 類型   | 說明                 |
|---------------------------------------|--------|----------------------|
| `consecutive_negative_months`         | int    | 連續淨賣出月數       |
| `streak_start`                        | string | 本輪起始月           |
| `streak_end`                          | string | 本輪結束月           |
| `cumulative_over_streak_billion_jpy`  | float  | 本輪累積（十億日圓） |
| `cumulative_over_streak_trillion_jpy` | float  | 本輪累積（兆日圓）   |
| `interpretation`                      | string | 中文解讀             |

### historical_stats

| 欄位                | 類型  | 說明                      |
|---------------------|-------|---------------------------|
| `count`             | int   | 樣本月數                  |
| `mean_billion_jpy`  | float | 平均值                    |
| `std_billion_jpy`   | float | 標準差                    |
| `latest_zscore`     | float | 當前值的 Z-score          |
| `latest_percentile` | float | 當前值的歷史分位數（0-1） |

### caliber_notes

口徑說明陣列，每個元素包含：

| 欄位   | 類型   | 說明                                                |
|--------|--------|-----------------------------------------------------|
| `type` | string | 口徑類型（maturity_bucket / investor_group / unit） |
| `used` | string | 本次使用的口徑                                      |
| `note` | string | 說明與警示                                          |

### confidence

| 欄位      | 類型   | 說明                            |
|-----------|--------|---------------------------------|
| `level`   | string | 信心水準（high / medium / low） |
| `reasons` | array  | 支持信心水準的理由              |
| `caveats` | array  | 注意事項                        |

---

## 錯誤輸出結構

```json
{
  "skill": "analyze_jgb_insurer_superlong_flow",
  "version": "0.1.0",
  "as_of": "2026-01-26",
  "status": "error",
  "error": {
    "code": "DATA_FETCH_FAILED",
    "message": "無法從 JSDA 下載數據",
    "details": "HTTP 503 Service Unavailable",
    "suggestion": "請檢查 JSDA 網站是否可用，或使用本地快取數據"
  },
  "fallback": {
    "used": true,
    "cache_date": "2025-11",
    "note": "使用快取數據，非最新"
  }
}
```
