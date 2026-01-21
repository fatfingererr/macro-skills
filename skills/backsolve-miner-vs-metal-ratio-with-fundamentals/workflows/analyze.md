# Workflow: 完整基本面分析

<required_reading>
**執行前請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/fundamental-factors.md - 四大因子計算邏輯
3. references/backsolve-math.md - 反推數學公式
</required_reading>

<process>

## Step 1: 確認分析參數

收集以下參數（若未提供則使用預設值）：

```yaml
metal_symbol: SI=F          # 金屬價格代碼
miner_universe:
  type: etf_holdings         # etf_holdings 或 ticker_list
  etf_ticker: SIL            # ETF 代碼
region_profile: us_sec       # us_sec / canada_sedar / mixed
time_range:
  start: 2020-01-01
  end: today
  frequency: weekly
ratio_thresholds:
  bottom_quantile: 0.20
  top_quantile: 0.80
fundamental_methods:
  aisc_method: hybrid
  leverage_method: net_debt_to_ev
  multiple_method: ev_to_ebitda
  dilution_method: weighted_avg_shares
```

## Step 2: 取得價格數據

執行價格數據抓取：

```python
import yfinance as yf
import pandas as pd

# 金屬價格
metal = yf.download(
    "SI=F",
    start="2020-01-01",
    end=pd.Timestamp.today().strftime('%Y-%m-%d'),
    interval="1wk"
)['Close']

# 礦業 ETF 價格
miner = yf.download(
    "SIL",
    start="2020-01-01",
    end=pd.Timestamp.today().strftime('%Y-%m-%d'),
    interval="1wk"
)['Close']

# 計算比率
ratio = miner / metal
```

## Step 3: 取得 ETF 持股與權重

若使用 ETF holdings：

```python
# 方法 1: 官方 CSV（優先）
# Global X SIL holdings: https://www.globalxetfs.com/funds/sil/

# 方法 2: SEC N-PORT（備援）
# 搜尋 CIK 並下載季度持股

# 輸出格式
holdings = {
    "PAAS": 0.12,  # 權重
    "AG": 0.08,
    "HL": 0.07,
    # ...
}
```

## Step 4: 抓取財報數據

對前 10 大持股執行財報抓取：

```python
# 對每家公司抓取：
# 1. 資產負債表：TotalDebt, Cash, Shares
# 2. 損益表：Revenue, OperatingIncome, NetIncome
# 3. 現金流量表：CFO, Capex
# 4. 補充揭露：AISC, 產量 (oz)

# 參考 workflows/data-fetch.md 的詳細抓取流程
```

## Step 5: 計算四大因子

對每家公司計算因子，再以權重加總：

```python
def compute_factors(company_data, metal_price):
    """計算單一公司的四大因子"""
    S = metal_price

    # (A) 成本因子
    aisc = company_data['aisc']
    C = 1 - aisc / S

    # (B) 槓桿因子
    net_debt = company_data['total_debt'] - company_data['cash']
    ev = company_data['market_cap'] + net_debt
    L = net_debt / ev
    one_minus_L = 1 - L

    # (C) 倍數因子
    ebitda = company_data['ebitda']
    M = ev / ebitda

    # (D) 稀釋因子
    shares_now = company_data['shares_outstanding']
    shares_base = company_data['shares_base']  # 基期
    D = shares_base / shares_now

    return {
        'C': C,
        'one_minus_L': one_minus_L,
        'M': M,
        'D': D
    }

# 權重加總
def weighted_aggregate(all_factors, weights):
    C_agg = sum(f['C'] * w for f, w in zip(all_factors, weights))
    # ... 其他因子類似
    return {'C': C_agg, ...}
```

## Step 6: 計算比率分位數與門檻

```python
# 當前比率
R_now = float(ratio.iloc[-1])

# 歷史分位數
R_percentile = (ratio <= R_now).mean()

# 門檻
R_bottom = ratio.quantile(0.20)
R_top = ratio.quantile(0.80)
R_median = ratio.quantile(0.50)

# 區間判定
if R_percentile <= 0.20:
    zone = "bottom"
elif R_percentile <= 0.40:
    zone = "low"
elif R_percentile <= 0.60:
    zone = "neutral"
elif R_percentile <= 0.80:
    zone = "high"
else:
    zone = "top"
```

## Step 7: 執行門檻反推（Backsolve）

```python
def backsolve(R_now, R_target, factors_now, metal_price):
    """反推需要的因子組合"""
    ratio_multiplier = R_target / R_now

    C_now = factors_now['C']
    L_now = factors_now['L']
    M_now = factors_now['M']
    D_now = factors_now['D']
    S = metal_price

    # 單因子反推
    results = {
        'multiple_only_need': M_now * ratio_multiplier,
        'deleverage_only_need_1_minus_L': (1 - L_now) * ratio_multiplier,
        'cost_only_need_C': C_now * ratio_multiplier,
        'cost_only_implied_aisc': S * (1 - C_now * ratio_multiplier),
        'dilution_only_need_D': D_now * ratio_multiplier,
    }

    # 雙因子組合網格
    grid = []
    for m_up in [1.10, 1.15, 1.20]:
        for metal_down in [-0.10, -0.15, -0.20]:
            new_ratio = R_now * m_up / (1 + metal_down)
            hits_target = new_ratio >= R_target
            grid.append({
                'multiple_up': m_up,
                'metal_down': metal_down,
                'hits_target': hits_target
            })

    results['two_factor_grid'] = grid
    return results
```

## Step 8: 執行事件研究

```python
def event_study(ratio, factors_history, bottom_threshold, min_separation=180):
    """歷史底部事件的因子驅動分析"""
    # 識別底部事件
    is_bottom = ratio <= bottom_threshold
    events = []

    last_event = None
    for date, val in ratio[is_bottom].items():
        if last_event is None or (date - last_event).days >= min_separation:
            events.append(date)
            last_event = date

    # 對每次事件，分析當期因子
    results = []
    for event_date in events:
        factors = factors_history.loc[event_date]

        # 排名因子貢獻
        # 假設基期為前 1 年
        base_date = event_date - pd.Timedelta(days=365)
        base_factors = factors_history.loc[:base_date].iloc[-1]

        changes = {
            'aisc_change': factors['aisc'] / base_factors['aisc'] - 1,
            'leverage_change': factors['leverage'] - base_factors['leverage'],
            'multiple_change': factors['multiple'] / base_factors['multiple'] - 1,
            'dilution_change': factors['dilution'] / base_factors['dilution'] - 1,
        }

        # 識別主要驅動
        dominant = max(changes, key=lambda k: abs(changes[k]))

        results.append({
            'date': event_date.strftime('%Y-%m-%d'),
            'ratio': float(ratio.loc[event_date]),
            **factors.to_dict(),
            'dominant_driver': dominant.replace('_change', '')
        })

    return results
```

## Step 9: 生成輸出

```python
output = {
    "skill": "backsolve_miner_vs_metal_ratio_with_fundamentals",
    "inputs": {
        "metal_symbol": "SI=F",
        "miner_universe": {"type": "etf_holdings", "etf_ticker": "SIL"},
        "region_profile": "us_sec"
    },
    "now": {
        "metal_price": float(metal.iloc[-1]),
        "miner_price": float(miner.iloc[-1]),
        "ratio": R_now,
        "ratio_percentile": R_percentile
    },
    "thresholds": {
        "bottom_ratio": float(R_bottom),
        "top_ratio": float(R_top),
        "median_ratio": float(R_median)
    },
    "fundamentals_weighted": {
        "aisc_usd_per_oz": aggregated_aisc,
        "net_debt_to_ev": aggregated_leverage,
        "ev_to_ebitda": aggregated_multiple,
        "shares_yoy_change": aggregated_dilution
    },
    "factors_now": factors_now,
    "backsolve_to_top": backsolve_results,
    "event_study": {"bottom_events": event_results},
    "summary": generate_summary(zone, dominant_factors),
    "notes": [
        f"AISC 使用 {aisc_method} 方法回算",
        "建議交叉驗證：COT 持倉、ETF 流量、美元/實質利率"
    ]
}

# 輸出 JSON
import json
with open('result.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
```

</process>

<success_criteria>
此工作流完成時應產出：

- [ ] 價格數據已取得並對齊
- [ ] ETF 持股與權重已解析
- [ ] 前 10 大持股的財報數據已抓取
- [ ] 四大因子已計算並權重加總
- [ ] 比率分位數與門檻已計算
- [ ] 門檻反推結果已生成
- [ ] 歷史底部事件已分析
- [ ] 結果已輸出為 JSON 格式
- [ ] 數據來源與方法已標註
</success_criteria>
