# 輸入參數定義

## 參數總覽

```json
{
  "as_of_date": "2026-01-21",
  "universe": "^GSPC",
  "history_start": "1900-01-01",
  "metrics": ["cape", "mktcap_to_gdp", "trailing_pe", "pb"],
  "aggregation": "mean",
  "weights": null,
  "percentile_method": "rank",
  "extreme_threshold": 95,
  "episode_min_gap_days": 3650,
  "forward_windows_days": [180, 365, 1095],
  "risk_readouts": ["max_drawdown", "forward_return", "volatility_change"]
}
```

---

## 必要參數

### as_of_date

| 屬性 | 值 |
|------|-----|
| 類型 | string (YYYY-MM-DD) |
| 必要 | 是 |
| 預設 | 今日 |
| 說明 | 要評估的日期 |

**範例**：
```json
"as_of_date": "2026-01-21"
```

---

### universe

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 是 |
| 預設 | "^GSPC" |
| 說明 | 市場或指數代碼 |

**支援的代碼**：

| 代碼 | 名稱 | 說明 |
|------|------|------|
| ^GSPC | S&P 500 | 美股大盤（預設） |
| ^NDX | NASDAQ 100 | 科技股重 |
| ^DJI | Dow Jones | 藍籌股 |
| ACWI | MSCI ACWI | 全球股票 |

**範例**：
```json
"universe": "^GSPC"
```

---

### history_start

| 屬性 | 值 |
|------|-----|
| 類型 | string (YYYY-MM-DD) |
| 必要 | 是 |
| 預設 | "1900-01-01" |
| 說明 | 歷史起算日，用於計算分位數基準 |

**注意**：實際起算日受資料可得性限制。例如 CAPE 資料從 1871 年開始，但 Yahoo Finance 估值資料可能只到 1980 年代。

**範例**：
```json
"history_start": "1900-01-01"
```

---

### metrics

| 屬性 | 值 |
|------|-----|
| 類型 | array[string] |
| 必要 | 是 |
| 預設 | ["cape", "mktcap_to_gdp", "trailing_pe"] |
| 說明 | 要納入的估值指標清單 |

**支援的指標**：

| 代碼 | 名稱 | 歷史起始 |
|------|------|----------|
| trailing_pe | 本益比（過去 12 個月） | 1980s |
| forward_pe | 預估本益比 | 2000s |
| cape | CAPE / Shiller PE | 1871 |
| pb | 股價淨值比 | 1980s |
| ps | 股價營收比 | 1990s |
| ev_ebitda | 企業價值倍數 | 1990s |
| q_ratio | 托賓 Q 比率 | 1950s |
| mktcap_to_gdp | 市值 / GDP | 1950s |

**範例**：
```json
"metrics": ["cape", "mktcap_to_gdp", "trailing_pe", "pb", "ps"]
```

---

### aggregation

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 是 |
| 預設 | "mean" |
| 說明 | 多指標合成方法 |

**支援的方法**：

| 方法 | 公式 | 特性 |
|------|------|------|
| mean | 算術平均 | 各指標同等權重 |
| median | 中位數 | 抵抗單一指標異常 |
| trimmed_mean | 去極端平均 | 去掉最高最低後平均 |

**範例**：
```json
"aggregation": "mean"
```

---

## 選用參數

### weights

| 屬性 | 值 |
|------|-----|
| 類型 | object |
| 必要 | 否 |
| 預設 | null（等權） |
| 說明 | 指標權重，未給則等權 |

**範例**：
```json
"weights": {
  "cape": 0.30,
  "mktcap_to_gdp": 0.25,
  "trailing_pe": 0.20,
  "pb": 0.15,
  "ps": 0.10
}
```

**注意**：權重總和不需要等於 1，會自動正規化。

---

### percentile_method

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 必要 | 否 |
| 預設 | "rank" |
| 說明 | 分位數計算方式 |

**支援的方法**：

| 方法 | 說明 |
|------|------|
| rank | 排序百分等級（推薦） |
| ecdf | 經驗分布函數 |
| z_to_percentile | 先做 Z 分數再轉分位 |

**範例**：
```json
"percentile_method": "rank"
```

---

### extreme_threshold

| 屬性 | 值 |
|------|-----|
| 類型 | number |
| 必要 | 否 |
| 預設 | 95 |
| 範圍 | 0-100 |
| 說明 | 判定「極端高估」的分位數門檻 |

**建議值**：

| 門檻 | 敏感度 | 歷史事件數 |
|------|--------|------------|
| 90 | 高（更多警報） | ~6-8 次 |
| 95 | 中（預設） | ~4-5 次 |
| 97 | 低（嚴格） | ~2-3 次 |
| 99 | 極低 | ~1-2 次 |

**範例**：
```json
"extreme_threshold": 95
```

---

### episode_min_gap_days

| 屬性 | 值 |
|------|-----|
| 類型 | integer |
| 必要 | 否 |
| 預設 | 3650（約 10 年） |
| 說明 | 歷史極端事件去重的最小間隔（天） |

**目的**：避免同一輪牛市頂點被識別為多個事件。

**範例**：
```json
"episode_min_gap_days": 3650
```

---

### forward_windows_days

| 屬性 | 值 |
|------|-----|
| 類型 | array[integer] |
| 必要 | 否 |
| 預設 | [180, 365, 1095] |
| 說明 | 事後統計的未來視窗（天） |

**建議視窗**：

| 視窗 | 期間 | 用途 |
|------|------|------|
| 180 | 6 個月 | 短期 |
| 365 | 1 年 | 中期 |
| 1095 | 3 年 | 長期 |
| 1825 | 5 年 | 超長期 |

**範例**：
```json
"forward_windows_days": [180, 365, 1095, 1825]
```

---

### risk_readouts

| 屬性 | 值 |
|------|-----|
| 類型 | array[string] |
| 必要 | 否 |
| 預設 | ["max_drawdown", "forward_return", "volatility_change"] |
| 說明 | 要輸出的風險解讀項目 |

**支援的項目**：

| 項目 | 說明 |
|------|------|
| max_drawdown | 最大回撤 |
| forward_return | 未來報酬 |
| volatility_change | 波動變化 |
| valuation_reversion_speed | 估值均值回歸速度 |

**範例**：
```json
"risk_readouts": ["max_drawdown", "forward_return", "volatility_change"]
```

---

## 完整參數範例

### 最小配置

```json
{
  "as_of_date": "2026-01-21"
}
```

使用所有預設值。

### 標準配置

```json
{
  "as_of_date": "2026-01-21",
  "universe": "^GSPC",
  "metrics": ["cape", "mktcap_to_gdp", "trailing_pe", "pb"],
  "aggregation": "mean",
  "extreme_threshold": 95
}
```

### 完整配置

```json
{
  "as_of_date": "2026-01-21",
  "universe": "^GSPC",
  "history_start": "1900-01-01",
  "metrics": ["cape", "mktcap_to_gdp", "trailing_pe", "forward_pe", "pb", "ps"],
  "aggregation": "mean",
  "weights": {
    "cape": 0.30,
    "mktcap_to_gdp": 0.25,
    "trailing_pe": 0.15,
    "forward_pe": 0.10,
    "pb": 0.10,
    "ps": 0.10
  },
  "percentile_method": "rank",
  "extreme_threshold": 95,
  "episode_min_gap_days": 3650,
  "forward_windows_days": [180, 365, 1095],
  "risk_readouts": ["max_drawdown", "forward_return", "volatility_change", "valuation_reversion_speed"]
}
```

---

## 命令列參數對應

| JSON 參數 | CLI 參數 | 縮寫 |
|-----------|----------|------|
| as_of_date | --as_of_date | -d |
| universe | --universe | -u |
| history_start | --history_start | -h |
| metrics | --metrics | -m |
| aggregation | --aggregation | -a |
| extreme_threshold | --extreme_threshold | -t |
| output | --output | -o |

**範例**：

```bash
python scripts/valuation_percentile.py \
  -d "2026-01-21" \
  -u "^GSPC" \
  -m "cape,mktcap_to_gdp,trailing_pe" \
  -a "mean" \
  -t 95 \
  -o "output/result.json"
```
