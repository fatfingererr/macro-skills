# Workflow: Price Regime（價格型態分析）

<required_reading>
**Read these reference files NOW:**
1. references/data-sources.md
2. references/price-methodology.md
3. references/failure-modes.md
</required_reading>

<process>
## Step 1: Load Price Data

根據 `data_level` 載入價格數據：

### 1.1 Free Data Level

```python
def load_price_free(chem_focus):
    """
    免費數據源：
    1. CME Lithium Hydroxide Futures（可交易價格）
    2. 相關股票籃子 proxy（ALB, SQM, LTHM 等）
    """

    # CME 期貨（如可得）
    cme_data = load_cme_lithium_futures()

    # 股票 proxy（備援）
    stock_proxy = compute_lithium_stock_index([
        {"ticker": "ALB", "weight": 0.3},
        {"ticker": "SQM", "weight": 0.3},
        {"ticker": "LTHM", "weight": 0.2},
        {"ticker": "LAC", "weight": 0.2}
    ])

    return {
        "carbonate": cme_data.get("carbonate") or stock_proxy,
        "hydroxide": cme_data.get("hydroxide") or stock_proxy,
        "source": "CME/StockProxy",
        "data_level": "free_nolimit"
    }
```

### 1.2 Paid Data Level

```python
def load_price_paid(chem_focus, providers=["fastmarkets", "smm"]):
    """
    付費數據源：
    1. Fastmarkets 碳酸鋰/氫氧化鋰報價
    2. SMM 碳酸鋰現貨指數
    """

    prices = {}

    if "fastmarkets" in providers:
        prices["hydroxide"] = load_fastmarkets_lithium_hydroxide()
        prices["carbonate"] = load_fastmarkets_lithium_carbonate()

    if "smm" in providers:
        prices["carbonate_smm"] = load_smm_lithium_carbonate()

    return {
        "carbonate": prices.get("carbonate") or prices.get("carbonate_smm"),
        "hydroxide": prices.get("hydroxide"),
        "source": providers,
        "data_level": "paid"
    }
```

## Step 2: Compute Regime Indicators

### 2.1 Momentum Indicators

```python
def compute_momentum(price_series, periods=[12, 26]):
    """
    計算動能指標（Rate of Change）
    """

    results = {}
    for period in periods:
        roc = (price_series[-1] / price_series[-period] - 1) * 100
        results[f"roc_{period}w"] = roc

    return results
```

### 2.2 Trend Slope

```python
def compute_trend_slope(price_series, window=26):
    """
    計算趨勢斜率（線性回歸）
    """
    from scipy import stats

    x = np.arange(len(price_series[-window:]))
    y = price_series[-window:]

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return {
        "slope": slope,
        "r_squared": r_value ** 2,
        "slope_normalized": slope / np.mean(y)  # 標準化斜率
    }
```

### 2.3 Volatility

```python
def compute_volatility(price_series, window=26):
    """
    計算波動率（ATR% 或標準差）
    """

    returns = np.diff(price_series) / price_series[:-1]

    return {
        "volatility_std": np.std(returns[-window:]) * 100,
        "volatility_expanding": np.std(returns[-window//2:]) > np.std(returns[-window:-window//2]),
        "atr_pct": compute_atr_pct(price_series, window)
    }
```

### 2.4 Mean Reversion

```python
def compute_mean_deviation(price_series, ma_window=200):
    """
    計算均值偏離度
    """

    ma = np.mean(price_series[-ma_window:])
    current = price_series[-1]

    deviation = (current - ma) / ma * 100

    return {
        "ma_200w": ma,
        "deviation_pct": deviation,
        "extreme": abs(deviation) > 30  # 超過 30% 視為極端
    }
```

## Step 3: Classify Regime

```python
def classify_regime(momentum, slope, volatility, mean_dev):
    """
    四階段分類邏輯：

    | Regime    | ROC_12w | Slope | Volatility | 判斷優先級                   |
    |-----------|---------|-------|------------|------------------------------|
    | downtrend | < 0     | < 0   | any        | slope < 0 且 ROC < -5%       |
    | bottoming | 收斂    | 趨緩  | 下降       | -5% < ROC < 5%, slope 收斂   |
    | uptrend   | > 0     | > 0   | any        | slope > 0 且 ROC > 5%        |
    | overheat  | 極端+   | +     | 擴大       | ROC > 30% 或 deviation > 30% |
    """

    roc_12w = momentum["roc_12w"]
    roc_26w = momentum["roc_26w"]
    slope_val = slope["slope_normalized"]
    vol_expanding = volatility["volatility_expanding"]
    deviation = mean_dev["deviation_pct"]

    # 過熱判斷（最高優先級）
    if roc_12w > 30 or deviation > 30:
        return {
            "regime": "overheat",
            "confidence": 0.9,
            "signal": "獲利了結風險",
            "indicators": {"roc_12w": roc_12w, "deviation": deviation}
        }

    # 上行判斷
    if slope_val > 0 and roc_12w > 5:
        return {
            "regime": "uptrend",
            "confidence": 0.85,
            "signal": "做多視窗開啟",
            "indicators": {"roc_12w": roc_12w, "slope": slope_val}
        }

    # 下行判斷
    if slope_val < 0 and roc_12w < -5:
        return {
            "regime": "downtrend",
            "confidence": 0.85,
            "signal": "空頭主導，避免做多",
            "indicators": {"roc_12w": roc_12w, "slope": slope_val}
        }

    # 築底判斷（預設）
    return {
        "regime": "bottoming",
        "confidence": 0.75,
        "signal": "觀望，等待確認",
        "indicators": {
            "roc_12w": roc_12w,
            "roc_26w": roc_26w,
            "vol_trend": "下降" if not vol_expanding else "擴大"
        }
    }
```

## Step 4: Multi-Chemical Analysis

```python
def analyze_both_chemicals(carbonate_price, hydroxide_price):
    """
    同時分析碳酸鋰和氫氧化鋰
    """

    carbonate_regime = analyze_single(carbonate_price)
    hydroxide_regime = analyze_single(hydroxide_price)

    # 價差分析
    spread = compute_carbonate_hydroxide_spread(carbonate_price, hydroxide_price)

    # 同步性判斷
    sync_status = "synchronized" if carbonate_regime["regime"] == hydroxide_regime["regime"] else "divergent"

    return {
        "carbonate": carbonate_regime,
        "hydroxide": hydroxide_regime,
        "spread": spread,
        "sync_status": sync_status,
        "interpretation": generate_spread_interpretation(spread, sync_status)
    }
```

## Step 5: Generate Confirmation Signals

```python
def generate_confirmation_signals(regime_result):
    """
    生成型態轉換確認訊號
    """

    signals = []
    regime = regime_result["regime"]

    if regime == "bottoming":
        signals = [
            {"signal": "12週動能轉正（ROC > 0）", "status": "pending", "importance": "high"},
            {"signal": "波動率開始擴大", "status": "pending", "importance": "medium"},
            {"signal": "價格突破近期高點", "status": "pending", "importance": "high"},
            {"signal": "Balance Index 同步上行", "status": "pending", "importance": "high"}
        ]
    elif regime == "uptrend":
        signals = [
            {"signal": "維持 ROC > 5%", "status": "active", "importance": "high"},
            {"signal": "斜率持續為正", "status": "active", "importance": "medium"}
        ]

    return signals
```

## Step 6: Format Output

```python
def format_regime_report(regime_results, confirmation_signals):
    return {
        "asof_date": date.today().isoformat(),
        "carbonate": regime_results["carbonate"],
        "hydroxide": regime_results["hydroxide"],
        "spread_analysis": regime_results["spread"],
        "sync_status": regime_results["sync_status"],
        "confirmation_signals": confirmation_signals,
        "trading_implication": generate_trading_advice(regime_results)
    }
```
</process>

<output_template>
**Markdown 輸出：**

```markdown
# 鋰價型態分析報告

## 分析日期: [YYYY-MM-DD]
## 數據來源: [Fastmarkets/SMM/CME/Proxy]

---
## 碳酸鋰 (Lithium Carbonate)

| 指標           | 當前值 | 判讀   |
|----------------|--------|--------|
| 12週動能 (ROC) | [值]%  | [說明] |
| 26週動能 (ROC) | [值]%  | [說明] |
| 趨勢斜率       | [值]   | [說明] |
| 波動率 (ATR%)  | [值]%  | [說明] |
| 均值偏離度     | [值]%  | [說明] |

**型態判定**: [DOWNTREND/BOTTOMING/UPTREND/OVERHEAT]

---
## 氫氧化鋰 (Lithium Hydroxide)

[同上結構]

---
## 碳酸鋰/氫氧化鋰價差

| 指標     | 當前值      | 歷史分位 |
|----------|-------------|----------|
| 價差     | [值]        | [%]      |
| 價差方向 | [擴大/收斂] | -        |

---
## 週期位置

```
DOWNTREND → [BOTTOMING] → UPTREND → OVERHEAT
                 ↑
             目前位置
```

---
## 轉換確認訊號

| 訊號    | 狀態             | 重要性        |
|---------|------------------|---------------|
| [訊號1] | [pending/active] | [high/medium] |
| [訊號2] | ...              | ...           |

---
## 交易含義

[根據型態生成的交易建議]
```
</output_template>

<success_criteria>
此工作流程完成時：
- [ ] 價格數據已載入（含 fallback）
- [ ] 四個指標都已計算（動能/斜率/波動/均值偏離）
- [ ] 型態分類明確（四階段之一）
- [ ] 碳酸鋰/氫氧化鋰分開分析
- [ ] 確認訊號已生成
- [ ] 數據來源已標註
</success_criteria>
