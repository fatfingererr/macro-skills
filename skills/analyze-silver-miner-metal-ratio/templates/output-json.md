# JSON 輸出模板

## 完整輸出結構

```json
{
  "skill": "analyze_silver_miner_metal_ratio",
  "version": "0.1.0",
  "generated_at": "2025-01-21T10:30:00Z",

  "inputs": {
    "miner_proxy": "SIL",
    "metal_proxy": "SI=F",
    "start_date": "2010-01-01",
    "end_date": "2025-01-21",
    "freq": "1wk",
    "smoothing_window": 4,
    "bottom_quantile": 0.20,
    "top_quantile": 0.80,
    "min_separation_days": 180,
    "forward_horizons": [252, 504, 756],
    "scenario_target": "return_to_top"
  },

  "current": {
    "date": "2025-01-17",
    "miner_price": 29.45,
    "metal_price": 30.82,
    "ratio": 0.9555,
    "ratio_smoothed": 0.9612,
    "ratio_percentile": 12.5,
    "zone": "bottom",
    "bottom_threshold": 0.9800,
    "top_threshold": 1.4200,
    "median_threshold": 1.1500
  },

  "history_analogs": {
    "total_observations": 780,
    "bottom_event_count": 5,
    "bottom_event_dates": [
      "2010-08-06",
      "2015-12-18",
      "2016-01-29",
      "2020-03-20",
      "2022-09-30"
    ],
    "forward_metal_returns": {
      "252": {
        "horizon_label": "1 year",
        "count": 5,
        "median": 0.42,
        "mean": 0.39,
        "std": 0.25,
        "win_rate": 0.80,
        "best": 0.78,
        "worst": -0.12
      },
      "504": {
        "horizon_label": "2 years",
        "count": 4,
        "median": 0.65,
        "mean": 0.58,
        "std": 0.30,
        "win_rate": 1.00,
        "best": 0.95,
        "worst": 0.22
      },
      "756": {
        "horizon_label": "3 years",
        "count": 3,
        "median": 0.71,
        "mean": 0.66,
        "std": 0.28,
        "win_rate": 1.00,
        "best": 0.98,
        "worst": 0.31
      }
    }
  },

  "scenarios": {
    "target": "return_to_top",
    "target_ratio": 1.4200,
    "current_ratio": 0.9612,
    "miner_multiplier_if_metal_flat": 1.4773,
    "miner_gain_pct_if_metal_flat": 0.4773,
    "metal_multiplier_if_miner_flat": 0.6769,
    "metal_drop_pct_if_miner_flat": 0.3231,
    "interpretation": {
      "miner_scenario": "若白銀不變，礦業股需漲 47.7% 才回到頂部估值",
      "metal_scenario": "若礦業股不變，白銀需跌 32.3% 才回到頂部估值"
    }
  },

  "divergence_check": {
    "current_metal_percentile": 75.2,
    "is_divergence": true,
    "divergence_type": "ratio_low_metal_high",
    "interpretation": "比率處於底部區間，但白銀價格處於相對高位，形成背離訊號"
  },

  "summary": "銀礦股價/銀價比率目前處於歷史 12.5 百分位（底部區間），顯示礦業股相對白銀偏便宜。歷史上類似情境後，白銀 1 年報酬中位數為 42%，勝率 80%。若白銀不變，礦業股需漲 47.7% 才回到頂部估值。",

  "notes": [
    "比率訊號衡量的是『相對估值』，不是單邊價格保證。",
    "歷史類比樣本量僅 5 次，統計推論能力有限。",
    "礦業股可能因成本上升、地緣/政策風險、增發稀釋而合理落後。",
    "建議搭配：礦業股成本曲線、COT 持倉、ETF 流量、美元/實質利率做交叉驗證。"
  ],

  "recommended_next_checks": [
    "檢查 SIL 主要成分股的 AISC 成本趨勢",
    "查看 COT 報告中的投機淨部位",
    "觀察 SLV ETF 持倉量變化",
    "比較 GDX/GDXJ 是否有類似的比率低估"
  ]
}
```

## 欄位說明

### inputs

| 欄位                | 類型   | 說明             |
|---------------------|--------|------------------|
| miner_proxy         | string | 礦業股代理代號   |
| metal_proxy         | string | 金屬代理代號     |
| start_date          | string | 分析起點         |
| end_date            | string | 分析終點         |
| freq                | string | 取樣頻率         |
| smoothing_window    | int    | 平滑視窗         |
| bottom_quantile     | float  | 底部門檻分位數   |
| top_quantile        | float  | 頂部門檻分位數   |
| min_separation_days | int    | 事件去重間隔     |
| forward_horizons    | list   | 前瞻期（交易日） |
| scenario_target     | string | 情境目標         |

### current

| 欄位             | 類型   | 說明                           |
|------------------|--------|--------------------------------|
| date             | string | 最新數據日期                   |
| miner_price      | float  | 礦業股代理價格                 |
| metal_price      | float  | 金屬價格                       |
| ratio            | float  | 原始比率                       |
| ratio_smoothed   | float  | 平滑後比率                     |
| ratio_percentile | float  | 歷史分位數（0-100）            |
| zone             | string | 區間標記（bottom/neutral/top） |
| bottom_threshold | float  | 底部門檻值                     |
| top_threshold    | float  | 頂部門檻值                     |
| median_threshold | float  | 中位數值                       |

### history_analogs.forward_metal_returns

| 欄位          | 類型   | 說明       |
|---------------|--------|------------|
| horizon_label | string | 前瞻期標籤 |
| count         | int    | 事件數量   |
| median        | float  | 中位數報酬 |
| mean          | float  | 平均報酬   |
| std           | float  | 標準差     |
| win_rate      | float  | 正報酬機率 |
| best          | float  | 最佳報酬   |
| worst         | float  | 最差報酬   |

### scenarios

| 欄位                           | 類型   | 說明                           |
|--------------------------------|--------|--------------------------------|
| target                         | string | 情境目標                       |
| target_ratio                   | float  | 目標比率                       |
| current_ratio                  | float  | 當前比率                       |
| miner_multiplier_if_metal_flat | float  | 礦業股需要的倍數（白銀不變時） |
| miner_gain_pct_if_metal_flat   | float  | 礦業股需要的漲幅百分比         |
| metal_multiplier_if_miner_flat | float  | 白銀的倍數（礦業股不變時）     |
| metal_drop_pct_if_miner_flat   | float  | 白銀需要下跌的百分比           |

### divergence_check

| 欄位                     | 類型    | 說明                 |
|--------------------------|---------|----------------------|
| current_metal_percentile | float   | 金屬價格的歷史分位數 |
| is_divergence            | boolean | 是否存在背離         |
| divergence_type          | string  | 背離類型             |
| interpretation           | string  | 背離解讀             |
