# Workflow: 完整資金流向分析

<required_reading>
**執行前請先閱讀：**
1. references/methodology.md
2. references/data-sources.md
3. references/input-schema.md
4. references/contracts-map.md
</required_reading>

<process>

## Step 1: 參數確認與驗證

確認使用者提供的參數，或使用預設值：

```python
params = {
    "date_start": user_input.get("date_start", "2025-01-01"),
    "date_end": user_input.get("date_end", "today"),
    "cot_report": user_input.get("cot_report", "legacy"),
    "trader_group": user_input.get("trader_group", "noncommercial"),
    "position_metric": user_input.get("position_metric", "net"),
    "lookback_weeks_firepower": user_input.get("lookback_weeks_firepower", 156),
    "output_mode": user_input.get("output_mode", "both")
}
```

驗證：
- [ ] 日期格式正確 (YYYY-MM-DD)
- [ ] cot_report 為 legacy / disaggregated / tff 之一
- [ ] trader_group 對應 cot_report 類型

## Step 2: 抓取 COT 資料

執行 `scripts/fetch_cot_data.py`：

```bash
python scripts/fetch_cot_data.py \
  --report {cot_report} \
  --start {date_start} \
  --end {date_end} \
  --output cache/cot_data.parquet
```

預期輸出：
- 每週每商品的 long / short / spreading / open_interest
- 欄位：date, contract, long, short, spreading, open_interest

## Step 3: 抓取宏觀指標

執行 `scripts/fetch_macro_data.py`：

```bash
python scripts/fetch_macro_data.py \
  --indicators dxy,wti,metals \
  --start {date_start} \
  --end {date_end} \
  --output cache/macro_data.parquet
```

預期輸出：
- 日頻資料：date, dxy, wti, metals (或代理 ETF)
- 計算 weekly return 用於 macro_tailwind_score

## Step 4: 計算基金流量與分組彙總

執行主分析腳本 `scripts/analyze_positioning.py`：

```python
# 核心邏輯摘要
df = load_cot_data()
df["group"] = df["contract"].map(contracts_map)

# 計算淨部位與流量
if position_metric == "net":
    df["pos"] = df["long"] - df["short"]
df["flow"] = df.groupby("contract")["pos"].diff()

# 分組彙總
flows = df.groupby(["date", "group"])["flow"].sum().unstack()
flows["total"] = flows[["grains", "oilseeds", "meats", "softs"]].sum(axis=1)
```

## Step 5: 計算火力分數

```python
def calculate_firepower(net_pos_series, lookback_weeks=156):
    """計算 buying firepower"""
    hist = net_pos_series.iloc[-lookback_weeks:]
    current = net_pos_series.iloc[-1]
    percentile = (hist <= current).mean()
    return 1 - percentile  # 越低的部位 = 越高的火力

firepower = {}
for group in ["total", "grains", "oilseeds", "meats", "softs"]:
    net_pos = df.groupby(["date", "group"])["pos"].sum().unstack()[group]
    firepower[group] = calculate_firepower(net_pos)
```

## Step 6: 計算宏觀順風評分

```python
macro_df = load_macro_data()
latest = macro_df.iloc[-1]

tailwind_flags = [
    latest["dxy_ret"] < 0,    # USD 走弱
    latest["wti_ret"] > 0,    # 原油走強
    latest["metals_ret"] > 0  # 金屬走強
]

macro_tailwind_score = sum(tailwind_flags) / len(tailwind_flags)
```

## Step 7: 產生訊號與呼叫

```python
def generate_call(flow_total, firepower_total, macro_score):
    """產生可交易呼叫"""
    signals = []

    # Signal 1: Funds back & buying
    if flow_total > 0 and firepower_total > 0.5:
        signals.append("Funds back & buying")

    # Signal 2: Macro tailwind
    if macro_score >= 0.67:
        signals.append("Macro mood bullish")

    # Signal 3: Crowded risk
    if firepower_total < 0.2:
        signals.append("Crowded positioning - caution")

    return signals
```

## Step 8: 生成標註規則

依據 `templates/annotations.md` 的規則對照表：

```python
annotations = []

# Strong Corn Demand
if corn_export_surprise > 0 and grains_flow > 0:
    annotations.append({
        "label": "strong_corn_demand",
        "rule_hit": True,
        "evidence": ["Export sales up", "Grains flow positive"]
    })

# Bearish USDA Stats
if usda_surprise < 0 and grains_flow < 0:
    annotations.append({
        "label": "bearish_usda_stats",
        "rule_hit": True,
        "evidence": ["WASDE bearish", "Grains outflow"]
    })
```

## Step 9: 組裝輸出

依據 `templates/output-json.md` 格式輸出：

```python
result = {
    "skill": "track-agri-hedge-fund-positioning",
    "as_of": date_end,
    "summary": {
        "call": primary_call,
        "confidence": confidence_score,
        "why": reasons_list,
        "risks": risks_list
    },
    "latest_metrics": {
        "cot_week_end": cot_week_end,
        "flow_total_contracts": flow_total,
        "flow_by_group_contracts": flow_by_group,
        "buying_firepower": firepower,
        "macro_tailwind_score": macro_score
    },
    "weekly_flows": weekly_flows_list,
    "annotations": annotations
}
```

## Step 10: 輸出報告

依據 output_mode 輸出：
- `json`：儲存至 `output/result.json`
- `markdown`：依據 `templates/output-markdown.md` 格式輸出
- `both`：兩者皆輸出

</process>

<success_criteria>
此工作流程完成時應確認：

- [ ] COT 資料成功抓取並解析
- [ ] 分組彙總計算正確（Grains/Oilseeds/Meats/Softs/Total）
- [ ] 火力分數落在 0-1 範圍
- [ ] 宏觀順風評分計算完成
- [ ] 產生至少一個可交易呼叫
- [ ] 輸出格式符合 template 定義
- [ ] 風險提示已包含
</success_criteria>
