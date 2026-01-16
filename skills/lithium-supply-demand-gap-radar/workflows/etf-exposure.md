# Workflow: ETF Exposure（ETF 持股暴露與傳導分析）

<required_reading>
**Read these reference files NOW:**
1. references/data-sources.md
2. references/etf-holdings-structure.md
3. references/failure-modes.md
</required_reading>

<process>
## Step 1: Load ETF Data

### 1.1 Price Data

```python
def load_etf_price(ticker, years, freq):
    """
    使用 yfinance 載入 ETF 價格
    """
    import yfinance as yf

    etf = yf.Ticker(ticker)

    # 計算起始日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    # 下載數據
    df = etf.history(start=start_date, end=end_date, interval="1wk" if freq == "weekly" else "1d")

    # 計算收益率
    df["returns"] = df["Close"].pct_change()

    return {
        "prices": df["Close"].to_dict(),
        "returns": df["returns"].to_dict(),
        "ticker": ticker,
        "freq": freq
    }
```

### 1.2 Holdings Data

```python
def load_etf_holdings(ticker="LIT"):
    """
    從 Global X factsheet 或 ETF 官網載入持股

    來源：https://www.globalxetfs.com/funds/lit/
    """

    # 嘗試從官網 API 或 factsheet 抓取
    holdings = fetch_holdings_from_globalx(ticker)

    # 如果失敗，使用靜態備份
    if not holdings:
        holdings = load_static_holdings_backup(ticker)

    # 分類持股
    classified = classify_holdings(holdings)

    return {
        "holdings": classified,
        "asof_date": holdings.get("asof_date", "static"),
        "source": "GlobalX" if holdings else "StaticBackup"
    }

def classify_holdings(holdings):
    """
    將持股分類為 upstream/midstream/downstream
    """

    segment_mapping = {
        # Upstream (礦商)
        "ALB": "upstream",      # Albemarle
        "SQM": "upstream",      # SQM
        "PLS.AX": "upstream",   # Pilbara Minerals
        "MIN.AX": "upstream",   # Mineral Resources
        "IGO.AX": "upstream",   # IGO Limited
        "LAC": "upstream",      # Lithium Americas

        # Midstream (精煉/化學)
        "LTHM": "midstream",    # Livent (現 Arcadium)
        "GANF.PA": "midstream", # Ganfeng (if listed)

        # Downstream (電池/材料)
        "TSLA": "downstream",   # Tesla
        "CATL": "downstream",   # CATL (if accessible)
        "PANW": "downstream",   # Panasonic
        "LG": "downstream",     # LG Energy
        "BYD": "downstream",    # BYD
        "SSNLF": "downstream",  # Samsung SDI
    }

    for holding in holdings["list"]:
        ticker = holding["ticker"]
        holding["segment"] = segment_mapping.get(ticker, "unknown")

    return holdings
```

## Step 2: Compute Segment Weights

```python
def compute_segment_weights(holdings):
    """
    計算各產業鏈段的權重
    """

    segments = {"upstream": 0, "midstream": 0, "downstream": 0, "unknown": 0}

    for holding in holdings["list"]:
        segment = holding["segment"]
        weight = holding["weight"]
        segments[segment] += weight

    return {
        "weights": segments,
        "dominant_segment": max(segments, key=segments.get),
        "upstream_pct": segments["upstream"],
        "midstream_pct": segments["midstream"],
        "downstream_pct": segments["downstream"]
    }
```

## Step 3: Build Factor Data

### 3.1 Lithium Price Factor

```python
def build_lithium_factor(chem_focus, data_level):
    """
    建立鋰價因子（用於回歸）
    """

    # 載入價格數據
    li_price = load_lithium_price(chem_focus, data_level)

    # 計算收益率
    li_returns = compute_returns(li_price, freq="weekly")

    return {
        "factor_name": "lithium_price",
        "returns": li_returns,
        "source": li_price["source"]
    }
```

### 3.2 Demand Proxy Factor

```python
def build_demand_factor():
    """
    建立需求因子（EV 相關指數或代理）
    """

    # 使用 EV 相關 ETF 作為代理
    ev_proxy = load_price("DRIV", years=10, freq="weekly")  # Global X Autonomous & Electric Vehicles ETF

    # 或使用 Tesla 作為代理
    tsla_proxy = load_price("TSLA", years=10, freq="weekly")

    return {
        "factor_name": "ev_demand",
        "returns": ev_proxy["returns"],
        "source": "DRIV_ETF"
    }
```

## Step 4: Rolling Beta Regression

```python
def rolling_multifactor_beta(etf_returns, factors, window=52):
    """
    滾動多因子回歸計算 beta

    Model: ETF_ret = alpha + beta_li * Li_ret + beta_ev * EV_ret + epsilon
    """
    import statsmodels.api as sm

    # 對齊數據
    aligned = align_all_series(etf_returns, factors)

    results = []
    dates = list(aligned.index)

    for i in range(window, len(dates)):
        window_data = aligned.iloc[i-window:i]

        y = window_data["etf_returns"]
        X = window_data[["li_returns", "ev_returns"]]
        X = sm.add_constant(X)

        model = sm.OLS(y, X).fit()

        results.append({
            "date": dates[i],
            "beta_li": model.params.get("li_returns", 0),
            "beta_ev": model.params.get("ev_returns", 0),
            "alpha": model.params.get("const", 0),
            "r_squared": model.rsquared
        })

    return pd.DataFrame(results)
```

## Step 5: Compute Weighted Beta

```python
def compute_weighted_etf_beta(holdings, stock_betas):
    """
    計算持股加權 beta

    ETF_beta_li = Σ(weight_i * beta_i_to_lithium)
    """

    weighted_beta = 0

    for holding in holdings["list"]:
        ticker = holding["ticker"]
        weight = holding["weight"]

        # 取得個股對鋰價的 beta
        beta = stock_betas.get(ticker, {}).get("beta_li", estimate_beta_by_segment(holding["segment"]))

        weighted_beta += weight * beta

    return {
        "weighted_beta_li": weighted_beta,
        "methodology": "holdings_weighted",
        "coverage": sum(1 for h in holdings["list"] if h["ticker"] in stock_betas) / len(holdings["list"])
    }

def estimate_beta_by_segment(segment):
    """
    按產業鏈段估計 beta（如無實際數據）
    """

    segment_betas = {
        "upstream": 1.8,    # 礦商高 beta
        "midstream": 1.0,   # 精煉中等
        "downstream": 0.5,  # 電池低 beta
        "unknown": 0.8
    }

    return segment_betas.get(segment, 0.8)
```

## Step 6: Assess Transmission Status

```python
def assess_transmission(beta_history, threshold=0.3, duration=8):
    """
    判斷傳導狀態

    斷裂條件：beta < threshold 持續 > duration 週
    """

    recent_betas = beta_history["beta_li"].tail(duration).tolist()

    if all(b < threshold for b in recent_betas):
        return {
            "status": "broken",
            "description": f"傳導斷裂：Beta 低於 {threshold} 已持續 {duration} 週",
            "implication": "ETF 與鋰價脫鉤，需關注個股特殊因素"
        }

    avg_beta = np.mean(recent_betas)

    if avg_beta < 0.5:
        return {
            "status": "weakening",
            "description": f"傳導減弱：近期平均 Beta = {avg_beta:.2f}",
            "implication": "傳導效率下降，可能受其他因素主導"
        }

    return {
        "status": "normal",
        "description": f"傳導正常：近期平均 Beta = {avg_beta:.2f}",
        "implication": "ETF 正常反映鋰價變動"
    }
```

## Step 7: Format Output

```python
def format_exposure_report(holdings, segment_weights, beta_results, transmission):
    return {
        "asof_date": date.today().isoformat(),
        "etf_ticker": "LIT",
        "holdings_summary": {
            "total_holdings": len(holdings["list"]),
            "top_10": holdings["list"][:10],
            "segment_weights": segment_weights
        },
        "beta_analysis": {
            "current_beta_li": beta_results["beta_li"].iloc[-1],
            "current_beta_ev": beta_results["beta_ev"].iloc[-1],
            "52w_avg_beta_li": beta_results["beta_li"].mean(),
            "trend": "rising" if beta_results["beta_li"].iloc[-1] > beta_results["beta_li"].iloc[-13] else "falling"
        },
        "transmission_status": transmission,
        "interpretation": generate_exposure_interpretation(segment_weights, beta_results, transmission)
    }
```
</process>

<output_template>
**Markdown 輸出：**

```markdown
# LIT ETF 暴露與傳導分析報告

## 分析日期: [YYYY-MM-DD]
## ETF: Global X Lithium & Battery Tech ETF (LIT)

---
## 持股結構

### 前 10 大持股
| 排名 | 股票 | 權重 | 產業鏈段 | 國家 |
|------|------|------|----------|------|
| 1 | [ticker] | [weight]% | [segment] | [country] |
| ... | ... | ... | ... | ... |

### 產業鏈段分布
| 產業鏈段 | 權重 | 預期鋰價 Beta |
|----------|------|---------------|
| Upstream (礦商) | [weight]% | 1.5-2.5 |
| Midstream (精煉) | [weight]% | 0.8-1.2 |
| Downstream (電池) | [weight]% | 0.3-0.8 |

---
## Beta 分析

### ETF 對因子敏感度
| 因子 | 當前 Beta | 52週平均 | 趨勢 |
|------|-----------|----------|------|
| 鋰價因子 | [值] | [值] | [上升/下降] |
| EV需求因子 | [值] | [值] | [上升/下降] |

### Beta 歷史趨勢
[過去 52 週 beta 變化描述]

---
## 傳導狀態

- **狀態**: [normal/weakening/broken]
- **依據**: [說明]
- **含義**: [投資建議]

---
## 關鍵發現

1. [發現1]
2. [發現2]
3. [發現3]

---
## 風險提示

- [風險1]
- [風險2]
```
</output_template>

<success_criteria>
此工作流程完成時：
- [ ] ETF 持股已載入並分類
- [ ] 產業鏈段權重已計算
- [ ] Rolling beta 已計算（52 週滾動）
- [ ] 傳導狀態已判斷
- [ ] 輸出包含持股前 10 大
- [ ] 數據來源已標註
</success_criteria>
