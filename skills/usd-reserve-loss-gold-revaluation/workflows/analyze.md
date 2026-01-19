# Workflow: 完整情境分析

<required_reading>
**執行前請先閱讀：**
1. references/input-schema.md - 完整參數定義
2. references/methodology.md - 方法論與計算邏輯
3. references/data-sources.md - 數據來源與獲取方式
</required_reading>

<process>

## Step 1: 確認參數

檢查用戶提供的參數，補充預設值：

```python
params = {
    "scenario_date": "today",                # 情境基準日期
    "entities": ["USD", "EUR", "CNY", "JPY", "GBP", "CHF", "AUD", "CAD"],
    "monetary_aggregate": "M0",              # M0 或 M2
    "liability_scope": "broad_money",        # central_bank 或 broad_money
    "weighting_method": "fx_turnover",       # fx_turnover, reserve_share, equal, custom
    "weights": None,                          # 若 weighting_method="custom"
    "fx_base": "USD",                         # 計價幣別
    "gold_reserve_unit": "troy_oz",          # troy_oz 或 tonnes
    "gold_price_spot": None,                 # 若不填則自動抓取
    "fx_rates": None,                        # 若不填則自動抓取
    "output_format": "json"                  # json 或 markdown
}
```

若用戶有指定參數，覆蓋上述預設值。

## Step 2: 抓取數據

執行 `scripts/gold_revaluation.py` 抓取所需數據：

### 2.1 黃金儲備數據

```python
# 從 World Gold Council 或 IMF 獲取各國黃金儲備（tonnes）
gold_reserves = {
    "USD": 8133.5,   # 美國
    "EUR": 10773.5,  # 歐元區（ECB + 成員國）
    "CNY": 2264.3,   # 中國
    "JPY": 845.9,    # 日本
    "GBP": 310.3,    # 英國
    "CHF": 1040.0,   # 瑞士
    "AUD": 79.9,     # 澳洲
    "CAD": 0.0,      # 加拿大（已出售所有黃金）
    # ... 更多國家
}
```

### 2.2 貨幣量數據

```python
# 從各國央行/FRED/IMF 獲取 M0 或 M2（本幣計價）
money_supply = {
    "USD": {"M0": 5.8e12, "M2": 20.9e12},   # 美元
    "EUR": {"M0": 6.2e12, "M2": 15.8e12},   # 歐元
    "CNY": {"M0": 11.6e12, "M2": 292e12},   # 人民幣
    "JPY": {"M0": 680e12, "M2": 1200e12},   # 日圓
    # ... 更多國家
}
```

### 2.3 匯率數據

```python
# 獲取各貨幣對 USD 的匯率
# 格式：1 單位本幣 = ? USD
fx_rates = {
    "USD": 1.0,
    "EUR": 1.08,      # 1 EUR = 1.08 USD
    "CNY": 0.14,      # 1 CNY = 0.14 USD
    "JPY": 0.0068,    # 1 JPY = 0.0068 USD
    "GBP": 1.27,      # 1 GBP = 1.27 USD
    "CHF": 1.17,      # 1 CHF = 1.17 USD
    "AUD": 0.65,      # 1 AUD = 0.65 USD
    "CAD": 0.74,      # 1 CAD = 0.74 USD
}
```

### 2.4 FX Turnover 權重

```python
# BIS 2022 Triennial Survey
# 注意：BIS 口徑是雙邊計算，總和 > 100%
fx_turnover_weights = {
    "USD": 0.8825,
    "EUR": 0.3092,
    "JPY": 0.1692,
    "GBP": 0.1288,
    "CNY": 0.0704,
    "AUD": 0.0631,
    "CAD": 0.0620,
    "CHF": 0.0503,
}
```

### 2.5 金價

```python
# 從 Yahoo Finance 或 FRED 獲取
gold_price_spot = 2050.0  # USD per troy oz
```

## Step 3: 單位換算

### 3.1 黃金儲備轉換

```python
TONNE_TO_TROY_OZ = 32150.7466

# 轉換為金衡盎司
gold_oz = {
    entity: tonnes * TONNE_TO_TROY_OZ
    for entity, tonnes in gold_reserves.items()
}
```

### 3.2 貨幣量轉換為 USD 計價

```python
# 將各國貨幣量轉為 USD
money_base = {
    entity: money_supply[entity][params["monetary_aggregate"]] * fx_rates[entity]
    for entity in params["entities"]
}
```

## Step 4: 計算核心指標

### 4.1 隱含金價（未加權）

```python
implied_price = {
    entity: money_base[entity] / gold_oz[entity]
    for entity in params["entities"]
    if gold_oz[entity] > 0  # 排除無黃金儲備的國家
}
```

### 4.2 隱含金價（加權）

```python
weights = get_weights(params["weighting_method"], params["weights"])

implied_price_weighted = {
    entity: (money_base[entity] * weights[entity]) / gold_oz[entity]
    for entity in params["entities"]
    if gold_oz[entity] > 0
}
```

### 4.3 加權總隱含金價（Headline Number）

```python
total_weighted_money = sum(
    money_base[e] * weights[e]
    for e in params["entities"]
)
total_gold_oz = sum(
    gold_oz[e]
    for e in params["entities"]
)
headline_implied_price = total_weighted_money / total_gold_oz
```

### 4.4 黃金支撐率

```python
backing_ratio = {
    entity: (gold_oz[entity] * gold_price_spot) / money_base[entity]
    for entity in params["entities"]
}
```

### 4.5 槓桿倍數

```python
lever_multiple = {
    entity: implied_price_weighted[entity] / gold_price_spot
    for entity in params["entities"]
}
```

### 4.6 黃金缺口

```python
# 若要達到 100% 支撐，需要再買多少黃金
additional_gold_needed = {
    entity: max(0, (money_base[entity] / gold_price_spot) - gold_oz[entity])
    for entity in params["entities"]
}
```

## Step 5: 排名與洞察

### 5.1 按槓桿倍數排名

```python
ranking = sorted(
    lever_multiple.items(),
    key=lambda x: x[1],
    reverse=True  # 從高槓桿到低槓桿
)
```

### 5.2 生成洞察

```python
insights = [
    f"M0 與 M2 的差異主要反映『信用乘數』槓桿效應",
    f"backing_ratio 很低（如 ~3%）代表該貨幣體系對信用擴張依賴度高",
    f"使用 {params['weighting_method']} 權重的直覺是：...",
]
```

## Step 6: 輸出結果

依據 `output_format` 參數產出結果：

- JSON 格式：參考 `templates/output-json.md`
- Markdown 格式：參考 `templates/output-markdown.md`

```bash
python scripts/gold_revaluation.py \
  --date {scenario_date} \
  --entities {entities} \
  --aggregate {monetary_aggregate} \
  --weighting {weighting_method} \
  --output result.json
```

</process>

<success_criteria>
分析完成時應產出：

- [ ] Headline 隱含金價（加權總計）
- [ ] 各實體的隱含金價（未加權與加權）
- [ ] 各實體的黃金支撐率（backing_ratio）
- [ ] 各實體的槓桿倍數（lever_multiple）
- [ ] 各實體的黃金缺口（additional_gold_needed）
- [ ] 按槓桿程度排名
- [ ] 敘事洞察（至少 3 點）
- [ ] 結果輸出為指定格式
</success_criteria>
