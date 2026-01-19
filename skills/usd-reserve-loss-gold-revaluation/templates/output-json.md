# JSON 輸出模板 (Output JSON Template)

## 完整輸出結構

```json
{
  "skill": "usd-reserve-loss-gold-revaluation",
  "version": "0.1.0",
  "scenario_date": "2026-01-07",

  "assumptions": {
    "monetary_aggregate": "M0",
    "liability_scope": "broad_money",
    "weighting_method": "fx_turnover",
    "fx_base": "USD",
    "gold_spot_usd_per_oz": 2050.0,
    "data_sources": {
      "gold_reserves": "World Gold Council (2024-Q3)",
      "money_supply": "FRED, IMF IFS",
      "fx_rates": "FRED (2026-01-07)",
      "fx_turnover": "BIS Triennial Survey (2022)"
    }
  },

  "headline": {
    "implied_gold_price_weighted_usd_per_oz": 39210.0,
    "vs_spot_multiple": 19.1,
    "interpretation": "資產負債表壓力測算（非價格預測）：在該權重與口徑下，若黃金成為唯一錨且需承擔相應貨幣負債，金價需重估至此水平。"
  },

  "table": [
    {
      "entity": "USD",
      "currency": "US Dollar",
      "gold_tonnes": 8133.5,
      "gold_oz": 261495775,
      "money_local": 5800000000000,
      "money_base_usd": 5800000000000,
      "fx_rate_to_usd": 1.0,
      "weight": 0.8825,
      "implied_gold_price": 22180.0,
      "implied_gold_price_weighted": 19573.9,
      "backing_ratio_at_spot": 0.092,
      "lever_multiple_vs_spot": 9.5,
      "required_gold_oz_full_back_at_spot": 2829268292,
      "additional_gold_oz_needed": 2567772517
    },
    {
      "entity": "JPY",
      "currency": "Japanese Yen",
      "gold_tonnes": 845.9,
      "gold_oz": 27201545,
      "money_local": 680000000000000,
      "money_base_usd": 4624000000000,
      "fx_rate_to_usd": 0.0068,
      "weight": 0.1692,
      "implied_gold_price": 170011.0,
      "implied_gold_price_weighted": 28773.9,
      "backing_ratio_at_spot": 0.012,
      "lever_multiple_vs_spot": 14.0,
      "required_gold_oz_full_back_at_spot": 2256097560,
      "additional_gold_oz_needed": 2228896015
    },
    {
      "entity": "CNY",
      "currency": "Chinese Yuan",
      "gold_tonnes": 2264.3,
      "gold_oz": 72808850,
      "money_local": 11600000000000,
      "money_base_usd": 1624000000000,
      "fx_rate_to_usd": 0.14,
      "weight": 0.0704,
      "implied_gold_price": 22305.0,
      "implied_gold_price_weighted": 1570.3,
      "backing_ratio_at_spot": 0.092,
      "lever_multiple_vs_spot": 0.77,
      "required_gold_oz_full_back_at_spot": 792195121,
      "additional_gold_oz_needed": 719386271
    },
    {
      "entity": "EUR",
      "currency": "Euro",
      "gold_tonnes": 10773.5,
      "gold_oz": 346416058,
      "money_local": 6200000000000,
      "money_base_usd": 6696000000000,
      "fx_rate_to_usd": 1.08,
      "weight": 0.3092,
      "implied_gold_price": 19331.0,
      "implied_gold_price_weighted": 5979.1,
      "backing_ratio_at_spot": 0.106,
      "lever_multiple_vs_spot": 2.9,
      "required_gold_oz_full_back_at_spot": 3266341463,
      "additional_gold_oz_needed": 2919925405
    },
    {
      "entity": "GBP",
      "currency": "British Pound",
      "gold_tonnes": 310.3,
      "gold_oz": 9976771,
      "money_local": 870000000000,
      "money_base_usd": 1104900000000,
      "fx_rate_to_usd": 1.27,
      "weight": 0.1288,
      "implied_gold_price": 110752.0,
      "implied_gold_price_weighted": 14264.8,
      "backing_ratio_at_spot": 0.019,
      "lever_multiple_vs_spot": 7.0,
      "required_gold_oz_full_back_at_spot": 538975609,
      "additional_gold_oz_needed": 528998838
    },
    {
      "entity": "CHF",
      "currency": "Swiss Franc",
      "gold_tonnes": 1040.0,
      "gold_oz": 33436776,
      "money_local": 720000000000,
      "money_base_usd": 842400000000,
      "fx_rate_to_usd": 1.17,
      "weight": 0.0503,
      "implied_gold_price": 25197.0,
      "implied_gold_price_weighted": 1267.4,
      "backing_ratio_at_spot": 0.081,
      "lever_multiple_vs_spot": 0.62,
      "required_gold_oz_full_back_at_spot": 411024390,
      "additional_gold_oz_needed": 377587614
    },
    {
      "entity": "ZAR",
      "currency": "South African Rand",
      "gold_tonnes": 125.4,
      "gold_oz": 4031687,
      "money_local": 150000000000,
      "money_base_usd": 7950000000,
      "fx_rate_to_usd": 0.053,
      "weight": 0.01,
      "implied_gold_price": 1972.0,
      "implied_gold_price_weighted": 19.7,
      "backing_ratio_at_spot": 1.04,
      "lever_multiple_vs_spot": 0.01,
      "required_gold_oz_full_back_at_spot": 3878048,
      "additional_gold_oz_needed": 0
    }
  ],

  "ranking": {
    "by_lever_multiple_desc": [
      {"rank": 1, "entity": "JPY", "lever_multiple": 14.0},
      {"rank": 2, "entity": "USD", "lever_multiple": 9.5},
      {"rank": 3, "entity": "GBP", "lever_multiple": 7.0},
      {"rank": 4, "entity": "EUR", "lever_multiple": 2.9},
      {"rank": 5, "entity": "CNY", "lever_multiple": 0.77},
      {"rank": 6, "entity": "CHF", "lever_multiple": 0.62},
      {"rank": 7, "entity": "ZAR", "lever_multiple": 0.01}
    ],
    "by_backing_ratio_asc": [
      {"rank": 1, "entity": "JPY", "backing_ratio": 0.012},
      {"rank": 2, "entity": "GBP", "backing_ratio": 0.019},
      {"rank": 3, "entity": "CHF", "backing_ratio": 0.081},
      {"rank": 4, "entity": "USD", "backing_ratio": 0.092},
      {"rank": 5, "entity": "CNY", "backing_ratio": 0.092},
      {"rank": 6, "entity": "EUR", "backing_ratio": 0.106},
      {"rank": 7, "entity": "ZAR", "backing_ratio": 1.04}
    ]
  },

  "insights": [
    {
      "id": 1,
      "title": "M0 與 M2 的差異",
      "content": "M0 與 M2 的差異主要反映『貨幣口徑』：廣義貨幣把銀行體系信用也算進來，因此隱含金價會極端放大（M2 約為 M0 的 4-5 倍）。"
    },
    {
      "id": 2,
      "title": "日本的高槓桿",
      "content": "backing_ratio 很低（約 1.2%）代表日本貨幣體系對信用擴張依賴度極高；在『黃金唯一錨』情境下，必然需要金價大幅重估或大規模增持黃金。"
    },
    {
      "id": 3,
      "title": "FX Turnover 權重的直覺",
      "content": "使用 fx_turnover 權重的直覺是：儲備/結算使用份額越高，被重錨時吸收的壓力越大；因此 headline 更像在描述『全球體系再定價』而不是單一國家內生均衡。"
    },
    {
      "id": 4,
      "title": "南非的特殊性",
      "content": "南非（ZAR）的 backing_ratio 超過 100%，表示其黃金儲備價值已超過 M0 貨幣量，這與其作為主要產金國的歷史有關。"
    }
  ],

  "aggregates_comparison": null,

  "metadata": {
    "generated_at": "2026-01-07T10:30:00Z",
    "execution_time_ms": 1234,
    "data_freshness": {
      "gold_reserves": "2024-Q3",
      "money_supply": "2025-11",
      "fx_rates": "2026-01-07",
      "fx_turnover": "2022"
    },
    "warnings": [
      "BIS FX Turnover 數據為 2022 年，可能不反映最新格局",
      "各國 M0 定義略有差異，跨國比較需謹慎"
    ]
  }
}
```

---

## 欄位說明

### assumptions

| 欄位 | 說明 |
|------|------|
| monetary_aggregate | 使用的貨幣口徑（M0/M2） |
| liability_scope | 負債口徑 |
| weighting_method | 加權方式 |
| fx_base | 計價幣別基準 |
| gold_spot_usd_per_oz | 使用的金價 |
| data_sources | 各數據來源與時間 |

### headline

| 欄位 | 說明 |
|------|------|
| implied_gold_price_weighted_usd_per_oz | 加權總隱含金價 |
| vs_spot_multiple | 相對於現價的倍數 |
| interpretation | 解讀說明 |

### table (各實體明細)

| 欄位 | 說明 |
|------|------|
| entity | 貨幣代碼 |
| currency | 貨幣名稱 |
| gold_tonnes | 黃金儲備（噸） |
| gold_oz | 黃金儲備（金衡盎司） |
| money_local | 本幣貨幣量 |
| money_base_usd | USD 計價貨幣量 |
| fx_rate_to_usd | 匯率（1 本幣 = ? USD） |
| weight | 權重 |
| implied_gold_price | 未加權隱含金價 |
| implied_gold_price_weighted | 加權隱含金價 |
| backing_ratio_at_spot | 黃金支撐率 |
| lever_multiple_vs_spot | 槓桿倍數 |
| required_gold_oz_full_back_at_spot | 完全支撐所需黃金量 |
| additional_gold_oz_needed | 黃金缺口 |

### ranking

| 欄位 | 說明 |
|------|------|
| by_lever_multiple_desc | 按槓桿倍數降序排名 |
| by_backing_ratio_asc | 按支撐率升序排名（最槓桿在前） |

---

## 精簡輸出（--quick 模式）

```json
{
  "skill": "usd-reserve-loss-gold-revaluation",
  "scenario_date": "2026-01-07",
  "headline": {
    "implied_gold_price_m0_weighted": 39210.0,
    "vs_spot_multiple": 19.1
  },
  "top_leveraged": [
    {"entity": "JPY", "backing_ratio": 0.012, "lever_multiple": 14.0},
    {"entity": "USD", "backing_ratio": 0.092, "lever_multiple": 9.5},
    {"entity": "GBP", "backing_ratio": 0.019, "lever_multiple": 7.0}
  ]
}
```

---

## 比較模式輸出

```json
{
  "skill": "usd-reserve-loss-gold-revaluation",
  "mode": "compare_aggregates",
  "scenario_date": "2026-01-07",
  "headline_comparison": {
    "m0": {
      "implied_gold_price_weighted": 39210.0,
      "vs_spot_multiple": 19.1
    },
    "m2": {
      "implied_gold_price_weighted": 184500.0,
      "vs_spot_multiple": 90.0
    },
    "credit_multiplier": 4.7
  },
  "entity_comparison": [
    {
      "entity": "USD",
      "m0_backing_ratio": 0.092,
      "m2_backing_ratio": 0.026,
      "credit_expansion_ratio": 3.6
    },
    {
      "entity": "JPY",
      "m0_backing_ratio": 0.012,
      "m2_backing_ratio": 0.007,
      "credit_expansion_ratio": 1.8
    }
  ],
  "insights": [
    "M0 vs M2 差距約 4.7 倍，反映全球平均信用乘數",
    "日本的信用擴張比率較低（1.8x），因 M0 本身已很大"
  ]
}
```
