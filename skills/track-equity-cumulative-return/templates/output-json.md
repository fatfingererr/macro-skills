# JSON 輸出格式定義

本文檔定義累積報酬率追蹤技能的 JSON 輸出結構。

---

## 1. 多標的比較模式 (mode: compare)

**注意**：`start_date` 為前一年最後一個交易日（基準日），例如分析 2022 年起的報酬率，start_date 為 2021-12-31。

```json
{
  "skill": "track-equity-cumulative-return",
  "as_of": "2026-01-28",
  "mode": "compare",
  "parameters": {
    "tickers": ["NVDA", "AMD", "GOOGL"],
    "start_year": 2022,
    "benchmark": "^GSPC"
  },
  "period": {
    "start_date": "2021-12-31",
    "end_date": "2026-01-28",
    "days_held": 1489,
    "years_held": 4.08
  },
  "benchmark": {
    "ticker": "^GSPC",
    "name": "S&P 500",
    "cumulative_return_pct": 45.2
  },
  "summary": {
    "best_performer": "NVDA",
    "best_return": 320.5,
    "benchmark_return": 45.2,
    "beat_benchmark_count": 3,
    "total_count": 3
  },
  "results": [
    {
      "ticker": "NVDA",
      "name": "NVIDIA (NVDA)",
      "cumulative_return_pct": 320.5,
      "vs_benchmark": 275.3,
      "price_start": 29.25,
      "price_end": 123.15
    },
    {
      "ticker": "AMD",
      "name": "AMD (AMD)",
      "cumulative_return_pct": 180.2,
      "vs_benchmark": 135.0,
      "price_start": 45.50,
      "price_end": 127.48
    },
    {
      "ticker": "GOOGL",
      "name": "Google (GOOGL)",
      "cumulative_return_pct": 65.3,
      "vs_benchmark": 20.1,
      "price_start": 144.25,
      "price_end": 238.50
    }
  ]
}
```

---

## 2. 指數 Top N 模式 (mode: top20)

**注意**：`start_date` 為前一年最後一個交易日（基準日），例如分析 2022 年起的報酬率，start_date 為 2021-12-31。

```json
{
  "skill": "track-equity-cumulative-return",
  "as_of": "2026-01-28",
  "mode": "top20",
  "parameters": {
    "index": "nasdaq100",
    "index_name": "Nasdaq 100",
    "start_year": 2022,
    "top_n": 20
  },
  "period": {
    "start_date": "2021-12-31",
    "end_date": "2026-01-28",
    "days_held": 1489,
    "years_held": 4.08
  },
  "benchmark": {
    "ticker": "^GSPC",
    "name": "S&P 500",
    "cumulative_return_pct": 45.2
  },
  "summary": {
    "total_components": 100,
    "analyzed": 98,
    "failed": 2,
    "beat_benchmark": 45,
    "beat_benchmark_pct": 45.9,
    "top_n_avg_return": 145.6,
    "all_avg_return": 52.3
  },
  "top_performers": [
    {
      "rank": 1,
      "ticker": "NVDA",
      "name": "NVIDIA (NVDA)",
      "cumulative_return_pct": 320.5,
      "vs_benchmark": 275.3
    },
    {
      "rank": 2,
      "ticker": "META",
      "name": "Meta (META)",
      "cumulative_return_pct": 250.2,
      "vs_benchmark": 205.0
    }
  ]
}
```

---

## 3. 欄位說明

### 基本資訊

| 欄位       | 類型   | 說明                           |
|------------|--------|--------------------------------|
| skill      | string | 技能名稱                       |
| as_of      | string | 分析日期 (YYYY-MM-DD)          |
| mode       | string | 模式 (compare/top20)           |

### parameters

| 欄位        | 類型       | 說明                           |
|-------------|------------|--------------------------------|
| tickers     | string[]   | 股票代碼列表 (compare 模式)    |
| start_year  | int        | 起始年份                       |
| benchmark   | string     | 基準指數代碼                   |
| index       | string     | 指數代碼 (top20 模式)          |
| index_name  | string     | 指數名稱 (top20 模式)          |
| top_n       | int        | Top N 數量 (top20 模式)        |

### period

| 欄位        | 類型   | 說明                           |
|-------------|--------|--------------------------------|
| start_date  | string | 起始日期 (YYYY-MM-DD)          |
| end_date    | string | 結束日期 (YYYY-MM-DD)          |
| days_held   | int    | 持有天數                       |
| years_held  | float  | 持有年數                       |

### benchmark

| 欄位                  | 類型   | 說明                           |
|-----------------------|--------|--------------------------------|
| ticker                | string | 基準代碼                       |
| name                  | string | 基準名稱                       |
| cumulative_return_pct | float  | 基準累積報酬率 (%)             |

### summary (compare 模式)

| 欄位                 | 類型   | 說明                           |
|----------------------|--------|--------------------------------|
| best_performer       | string | 最佳表現者代碼                 |
| best_return          | float  | 最佳報酬率 (%)                 |
| benchmark_return     | float  | 基準報酬率 (%)                 |
| beat_benchmark_count | int    | 打敗基準數量                   |
| total_count          | int    | 總標的數量                     |

### summary (top20 模式)

| 欄位              | 類型   | 說明                           |
|-------------------|--------|--------------------------------|
| total_components  | int    | 指數總成分股數                 |
| analyzed          | int    | 成功分析數量                   |
| failed            | int    | 失敗/跳過數量                  |
| beat_benchmark    | int    | 打敗基準數量                   |
| beat_benchmark_pct| float  | 打敗基準比例 (%)               |
| top_n_avg_return  | float  | Top N 平均報酬率 (%)           |
| all_avg_return    | float  | 全體平均報酬率 (%)             |

### results / top_performers

| 欄位                  | 類型   | 說明                           |
|-----------------------|--------|--------------------------------|
| rank                  | int    | 排名 (僅 top20 模式)           |
| ticker                | string | 股票代碼                       |
| name                  | string | 股票名稱                       |
| cumulative_return_pct | float  | 累積報酬率 (%)                 |
| vs_benchmark          | float  | 相對基準報酬 (%)               |
| price_start           | float  | 起始價格 (僅 compare 模式)     |
| price_end             | float  | 結束價格 (僅 compare 模式)     |
