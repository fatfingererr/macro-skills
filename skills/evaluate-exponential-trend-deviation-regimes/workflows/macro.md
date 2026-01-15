# 宏觀因子分解工作流

詳細拆解各宏觀代理指標對行情體質判定的貢獻。

## 前置條件

- 使用者想了解體質判定背後的宏觀因子
- FRED 數據可用

## 步驟

### Step 1: 確認參數

| 參數 | 來源 | 預設值 |
|------|------|--------|
| symbol | 使用者提供 | GC=F |
| macro_proxies | 使用者提供 | 預設代理指標 |
| lookback_months | 使用者提供 | 12 |

預設宏觀代理指標：

```json
{
  "real_rate_series": "DFII10",
  "inflation_series": "T5YIE",
  "usd_series": "DTWEXBGS",
  "geopolitical_risk_series": null
}
```

### Step 2: 執行宏觀因子分析

```bash
cd skills/evaluate-exponential-trend-deviation-regimes
python scripts/trend_deviation.py \
  --symbol {symbol} \
  --macro-breakdown \
  --lookback-months {lookback_months}
```

### Step 3: 解讀宏觀因子結果

腳本輸出包含各因子的詳細分析：

```json
{
  "macro_breakdown": {
    "real_rate": {
      "series": "DFII10",
      "current_value": -0.5,
      "trend": "falling",
      "contribution_to_1970s_score": 0.3,
      "interpretation": "Negative real rates support gold"
    },
    "inflation_expectation": {
      "series": "T5YIE",
      "current_value": 2.8,
      "trend": "rising",
      "contribution_to_1970s_score": 0.25,
      "interpretation": "Rising inflation expectations support gold"
    },
    "usd_index": {
      "series": "DTWEXBGS",
      "current_value": 102.5,
      "trend": "weakening",
      "contribution_to_1970s_score": 0.2,
      "interpretation": "Weakening USD supports gold"
    },
    "geopolitical_risk": {
      "series": "proxy_news_count",
      "current_value": "elevated",
      "trend": "rising",
      "contribution_to_1970s_score": 0.25,
      "interpretation": "Elevated geopolitical risk supports gold"
    }
  },
  "total_1970s_score": 0.72,
  "regime_verdict": "1970s_like"
}
```

### Step 4: 生成因子分解報告

報告應包含：

1. **因子貢獻表格**

```
┌──────────────────┬────────┬────────┬────────┬─────────────────────────┐
│ 因子             │ 當前值 │ 趨勢   │ 權重   │ 對 1970s 分數貢獻       │
├──────────────────┼────────┼────────┼────────┼─────────────────────────┤
│ 實質利率         │ -0.5%  │ ↓ 下降 │ 0.30   │ +0.30 (滿分)            │
├──────────────────┼────────┼────────┼────────┼─────────────────────────┤
│ 通膨預期         │ 2.8%   │ ↑ 上升 │ 0.25   │ +0.25 (滿分)            │
├──────────────────┼────────┼────────┼────────┼─────────────────────────┤
│ 美元指數         │ 102.5  │ ↓ 走弱 │ 0.20   │ +0.20 (滿分)            │
├──────────────────┼────────┼────────┼────────┼─────────────────────────┤
│ 地緣風險         │ 偏高   │ ↑ 上升 │ 0.25   │ +0.25 (滿分)            │
├──────────────────┼────────┼────────┼────────┼─────────────────────────┤
│ **合計**         │        │        │ 1.00   │ **0.72**                │
└──────────────────┴────────┴────────┴────────┴─────────────────────────┘
```

2. **各因子詳細解讀**
   - 數據來源
   - 當前狀態
   - 與歷史比較
   - 對黃金的影響

3. **體質判定結論**
   - 綜合分數
   - 判定結果
   - 關鍵驅動因子

## 宏觀因子定義

### 1. 實質利率（Real Rate）

**數據來源**：FRED DFII10（10 年 TIPS 收益率）

**判定規則**：
- 負值 → 支持 1970s-like（權重 0.3）
- 趨勢下降 → 額外支持

**解讀**：
實質利率為負時，持有黃金的機會成本降低甚至為負，支持黃金需求。

### 2. 通膨預期（Inflation Expectation）

**數據來源**：FRED T5YIE（5 年 Breakeven 通膨率）

**判定規則**：
- 上升趨勢 → 支持 1970s-like（權重 0.25）
- 高於 2.5% → 額外支持

**解讀**：
通膨預期上升時，黃金作為通膨對沖工具的需求增加。

### 3. 美元指數（USD Index）

**數據來源**：FRED DTWEXBGS（貿易加權美元指數）

**判定規則**：
- 下降趨勢 → 支持 1970s-like（權重 0.2）
- 12 個月低點 → 額外支持

**解讀**：
美元走弱時，以美元計價的黃金對其他貨幣持有者更有吸引力。

### 4. 地緣政治風險（Geopolitical Risk）

**數據來源**：GPR 指數（若不可用則用新聞關鍵詞計數）

**判定規則**：
- 上升趨勢 → 支持 1970s-like（權重 0.25）
- 高於歷史中位數 → 額外支持

**解讀**：
地緣緊張時，黃金作為避險資產的需求增加。

## 趨勢判定邏輯

```python
def determine_trend(series: pd.Series, lookback: int = 60) -> str:
    """
    判定時間序列的趨勢

    Args:
        series: 數據序列
        lookback: 回看天數

    Returns:
        "up" / "down" / "flat"
    """
    recent = series.tail(lookback)
    if len(recent) < lookback // 2:
        return "flat"

    # 簡單線性回歸判定趨勢
    t = np.arange(len(recent))
    slope, _ = np.polyfit(t, recent.values, 1)

    # 標準化斜率
    normalized_slope = slope / recent.std()

    if normalized_slope > 0.1:
        return "up"
    elif normalized_slope < -0.1:
        return "down"
    else:
        return "flat"
```

## 錯誤處理

- 若 FRED 數據不可用，跳過該因子，調整權重
- 若地緣風險指數不可用，使用新聞關鍵詞計數替代
- 若多個因子不可用，警告使用者結果可能不完整

## 輸出範例

見 `templates/output-markdown.md` 中的宏觀因子分解報告模板
