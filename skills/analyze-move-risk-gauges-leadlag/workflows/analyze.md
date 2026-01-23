# Workflow: 完整領先落後分析

<required_reading>
**執行前請閱讀：**
1. references/data-sources.md - 了解數據來源與替代方案
2. references/methodology.md - 了解分析方法論
3. references/input-schema.md - 了解可用參數
</required_reading>

<process>

## Step 1: 確認參數

確認使用者提供的參數，填充預設值：

```python
params = {
    "start_date": user_start_date,  # 必填
    "end_date": user_end_date,      # 必填
    "rates_vol_symbol": "MOVE",
    "equity_vol_symbol": "VIX",
    "credit_spread_symbol": "CDX_IG_PROXY",
    "jgb_yield_symbol": "JGB10Y",
    "freq": "D",
    "smooth_window": 5,
    "zscore_window": 60,
    "lead_lag_max_days": 20,
    "shock_window_days": 5,
    "shock_threshold_bps": 15.0,
    "output_mode": "markdown"
}
```

## Step 2: 抓取數據

執行 `scripts/fetch_data.py` 抓取所需數據：

```bash
cd skills/analyze-move-risk-gauges-leadlag
python scripts/fetch_data.py \
  --start {start_date} \
  --end {end_date} \
  --symbols MOVE,VIX,CREDIT,JGB10Y \
  --output cache/data.csv
```

**注意**：
- MOVE 和 JGB10Y 需要爬蟲，確保 Chrome 已開啟調試模式
- 若爬蟲失敗，腳本會自動使用代理數據

## Step 3: 數據預處理

執行數據預處理：

1. **對齊到交易日**：使用 Business Day 索引
2. **缺值處理**：前向填充，記錄缺值比例
3. **平滑處理**：`smooth_window` 日移動平均
4. **Z 分數標準化**：`zscore_window` 日滾動標準化

```python
# 內部執行
df = load_data("cache/data.csv")
df = df.sort_index().asfreq("B").ffill()

# 記錄數據品質
missing_ratio = df.isna().mean()
if missing_ratio.max() > 0.05:
    warnings.append(f"High missing ratio: {missing_ratio.to_dict()}")

# 平滑與標準化
df_smooth = df.rolling(smooth_window).mean() if smooth_window > 0 else df
df_z = df_smooth.apply(lambda c: rolling_zscore(c, zscore_window))
```

## Step 4: Lead/Lag 分析

計算 MOVE 對 VIX 和 Credit 的交叉相關：

```python
from scripts.analyze import crosscorr_leadlag

lag_vix, corr_vix = crosscorr_leadlag(df_smooth["MOVE"], df_smooth["VIX"], lead_lag_max_days)
lag_credit, corr_credit = crosscorr_leadlag(df_smooth["MOVE"], df_smooth["CREDIT"], lead_lag_max_days)

leadlag = {
    "MOVE_vs_VIX": {"best_lag_days": lag_vix, "corr": corr_vix},
    "MOVE_vs_CREDIT": {"best_lag_days": lag_credit, "corr": corr_credit}
}
```

**解讀**：
- `best_lag_days > 0`：MOVE 領先
- `corr > 0.7`：強相關，結果可信
- `corr < 0.5`：弱相關，需謹慎解讀

## Step 5: 事件窗檢定

識別 JGB 衝擊事件，計算 MOVE 反應：

```python
# 識別衝擊事件
jgb_change = (df_smooth["JGB10Y"] - df_smooth["JGB10Y"].shift(shock_window_days)) * 100
shock_events = jgb_change.abs() >= shock_threshold_bps

# 計算 MOVE 反應
move_change = df_smooth["MOVE"] - df_smooth["MOVE"].shift(shock_window_days)
reactions = move_change[shock_events].dropna()

spooked_check = {
    "shock_definition": f"abs(JGB10Y change over {shock_window_days}d) >= {shock_threshold_bps}bp",
    "shock_count": shock_events.sum(),
    "mean_MOVE_reaction_on_shocks": reactions.mean(),
    "MOVE_zscore_now": df_z["MOVE"].iloc[-1]
}
```

**判定規則**：
- `mean_reaction < 1.0`：Not spooked
- `mean_reaction >= 1.0`：Spooked
- `MOVE_zscore_now < 0`：目前 MOVE 偏低

## Step 6: 方向一致性

計算 MOVE 下行時其他指標的同向比例：

```python
d = df_smooth.diff()
move_down = d["MOVE"] < 0

alignment = {
    "MOVE_down_and_VIX_down_ratio": (move_down & (d["VIX"] < 0)).sum() / move_down.sum(),
    "MOVE_down_and_CREDIT_down_ratio": (move_down & (d["CREDIT"] < 0)).sum() / move_down.sum()
}
```

**解讀**：
- `> 0.6`：高度同向，支持「MOVE 領先帶動下行」的敘事
- `0.4-0.6`：中等同向
- `< 0.4`：低同向，敘事可能不成立

## Step 7: 生成報告

根據分析結果生成輸出：

**Markdown 格式**（見 `templates/output-markdown.md`）：
```markdown
# Rates Vol Lead/Lag Check (MOVE vs VIX vs Credit) — Summary

## 結論
- [恐慌判定結果]
- [領先落後判定結果]
- [方向一致性判定結果]

## 證據（量化）
| 指標           | 領先天數      | 相關係數      |
|----------------|---------------|---------------|
| MOVE vs VIX    | +{lag_vix}    | {corr_vix}    |
| MOVE vs Credit | +{lag_credit} | {corr_credit} |
```

**JSON 格式**（見 `templates/output-json.md`）：
```json
{
  "status": "ok",
  "headline": "...",
  "leadlag": {...},
  "spooked_check": {...},
  "direction_alignment": {...}
}
```

## Step 8: 輸出結果

根據 `output_mode` 輸出結果：

```bash
# Markdown
python scripts/analyze.py --start 2024-01-01 --end 2026-01-01 --output-mode markdown

# JSON
python scripts/analyze.py --start 2024-01-01 --end 2026-01-01 --output-mode json --output result.json
```

</process>

<error_handling>

## 常見錯誤處理

### 數據抓取失敗

```python
if fetch_error:
    # 使用代理數據
    if symbol == "MOVE":
        print("MOVE fetch failed, using rates volatility proxy")
        move = compute_rates_vol_proxy(dgs10)
    elif symbol == "JGB10Y":
        print("JGB10Y fetch failed, using FRED monthly data")
        jgb = fetch_fred_jgb_monthly()
```

### 數據不足

```python
if len(df) < zscore_window + lead_lag_max_days:
    raise ValueError(f"Insufficient data: need {zscore_window + lead_lag_max_days} days, got {len(df)}")
```

### 無衝擊事件

```python
if shock_events.sum() == 0:
    spooked_check = {
        "shock_count": 0,
        "mean_MOVE_reaction_on_shocks": None,
        "note": f"No shock events (|ΔJGB| >= {shock_threshold_bps}bp) in period"
    }
```

</error_handling>

<success_criteria>
完成此 workflow 時：

- [ ] 成功抓取或代理所有數據
- [ ] 記錄缺值比例（若 > 5% 需警告）
- [ ] 計算 MOVE vs VIX / Credit 的 lead/lag
- [ ] 識別 JGB 衝擊事件並計算 MOVE 反應
- [ ] 計算方向一致性比例
- [ ] 生成一句話結論
- [ ] 輸出完整報告（Markdown 或 JSON）
</success_criteria>
