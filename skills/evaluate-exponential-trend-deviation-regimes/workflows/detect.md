# 單資產偵測工作流

偵測單一資產的趨勢偏離度與歷史分位數。

## 前置條件

- 使用者提供了資產代碼（symbol）
- 資產有足夠的歷史數據（建議 ≥ 10 年）

## 步驟

### Step 1: 確認參數

從使用者輸入解析以下參數：

| 參數 | 來源 | 預設值 | 說明 |
|------|------|--------|------|
| symbol | 使用者提供 | 必填 | 資產代碼（例如：GC=F, ^GSPC, BTC-USD） |
| start_date | 使用者提供 | 建議提供 | 起始日期，不同資產應有不同起點 |
| end_date | 使用者提供 | today | 結束日期 |
| trend_fit_window | 使用者提供 | full | 趨勢擬合策略 |
| include_macro | 使用者提供 | false | 僅黃金支援宏觀分析 |
| compare_peaks | 使用者提供 | null | 手動指定歷史參考日期 |

**資產專屬起始日期建議**：
- 黃金：1970-01-01（捕捉布雷頓森林體系瓦解後的歷史）
- S&P 500：1950-01-01
- 比特幣：2013-01-01（歷史較短）
- 原油：1980-01-01

若使用者未提供起始日期，腳本將使用較保守的預設值（2000-01-01）。

### Step 2: 執行偵測腳本

**基本偵測**（適用所有資產）：
```bash
cd skills/evaluate-exponential-trend-deviation-regimes
python scripts/trend_deviation.py \
  --symbol {symbol} \
  --start {start_date} \
  --end {end_date}
```

**含宏觀分析**（僅黃金）：
```bash
python scripts/trend_deviation.py \
  --symbol GC=F \
  --start 1970-01-01 \
  --include-macro
```

**指定歷史參考點**：
```bash
python scripts/trend_deviation.py \
  --symbol {symbol} \
  --compare-peaks "2011-09-06,2020-08-07"
```

### Step 3: 解讀輸出

腳本輸出 JSON 格式結果，核心欄位：

```json
{
  "skill": "evaluate-exponential-trend-deviation-regimes",
  "asset": "{symbol}",
  "as_of": "2026-01-14",
  "metrics": {
    "current_distance_pct": 53.6,
    "current_percentile": 89.5,
    "reference": {
      "2011_max": 104.3  // 若有指定參考日期
    },
    "verdict": {
      "surpassed_2011_by_this_metric": false  // 若有參考點
    }
  },
  "regime": {  // 僅當 --include-macro 時存在
    "regime_label": "2000s_like",
    "drivers": [...],
    "confidence": 0.72
  }
}
```

**關鍵欄位說明**：
- `current_distance_pct`：當前偏離度（%）
- `current_percentile`：歷史分位數（0-100）
- `reference`：與指定參考日期的比較（若有提供）
- `regime`：行情體質判定（僅黃金且使用 --include-macro）

### Step 4: 生成報告

根據 `templates/output-markdown.md` 模板格式化報告。

報告應包含：

1. **當前狀態表格**
   - 偏離度數值
   - 歷史分位數
   - 與歷史峰值比較

2. **行情體質判定**
   - 1970s-like / 2000s-like
   - 驅動因子清單
   - 信心度

3. **洞察與建議**
   - 當前市場位置解讀
   - 風險提示
   - 後續關注點

## 偏離度計算邏輯

```python
def fit_exponential_trend(prices: pd.Series):
    """擬合指數趨勢線"""
    t = np.arange(len(prices))
    y = np.log(prices.values)

    # OLS: y = a + b*t
    X = np.vstack([np.ones_like(t), t]).T
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]

    trend = np.exp(a + b * t)
    return pd.Series(trend, index=prices.index), (a, b)

def distance_from_trend_pct(prices: pd.Series, trend: pd.Series):
    """計算偏離度百分比"""
    return (prices / trend - 1.0) * 100.0
```

## 行情體質判定邏輯

```python
def calculate_regime_score(macro_data: dict) -> tuple[str, float, list]:
    """
    計算行情體質分數

    Returns:
        (regime_label, confidence, drivers)
    """
    score = 0.0
    drivers = []

    # 實質利率（權重 0.3）
    if macro_data.get('real_rate', 0) < 0:
        score += 0.3
        drivers.append("Real rates negative / falling")

    # 通膨趨勢（權重 0.25）
    if macro_data.get('inflation_trend', 'flat') == 'up':
        score += 0.25
        drivers.append("Inflation risk rising")

    # 地緣風險（權重 0.25）
    if macro_data.get('geopolitical_risk_trend', 'flat') == 'up':
        score += 0.25
        drivers.append("Geopolitical tension proxy rising")

    # 美元趨勢（權重 0.2）
    if macro_data.get('usd_trend', 'flat') == 'down':
        score += 0.2
        drivers.append("USD weakening")

    # 判定
    if score >= 0.5:
        return "1970s_like", score, drivers
    else:
        return "2000s_like", 1 - score, drivers
```

## 錯誤處理

- 若無法取得資料，提示使用者檢查 symbol 是否正確
- 若資料不足（< 10 年），警告趨勢擬合可能不準確
- 若 yfinance 失敗，建議使用 Stooq 替代
- 若 FRED 數據不可用，跳過宏觀因子分析，僅輸出偏離度

## 輸出範例

見 `examples/gold-deviation-2026.json`
