# Markdown 報告模板

## 單資產偵測報告

```markdown
# {symbol} 波動擠壓行情偵測結果

**分析日期**：{as_of}

## 當前狀態

| 指標            | 數值                | 狀態             |
|-----------------|---------------------|------------------|
| 當前 ATR%       | {atr_pct}%          | {atr_pct_status} |
| ATR% 對基準倍率 | {ratio}x            | {ratio_status}   |
| 3 年基準 ATR%   | {baseline_atr_pct}% | 常態參照值       |

## 行情判定

**{regime_display}**

技術位可靠度評分：**{reliability_score}/100**（{reliability_level}）

## 風控調整建議

| 調整項目 | 當前建議          | 秩序市場參照 |
|----------|-------------------|--------------|
| 停損倍數 | {stop_mult}x ATR  | 1.0-1.5x ATR |
| 倉位縮放 | {position_scale}x | 1.0x         |
| 時間框架 | {timeframe}       | 任意         |
| 工具選擇 | {instrument}      | 裸倉位       |

## 行情解讀

{regime_explanation}

## 戰術建議

{tactics_list}

---

*由 detect-atr-squeeze-regime 技能生成*
```

---

## 批次掃描報告

```markdown
# 多資產 ATR 擠壓行情掃描報告

**掃描日期**：{as_of}
**掃描資產**：{total_assets} 個

## 掃描結果

| Symbol | ATR% | Ratio | 行情 | 信任度 | 建議停損 |
|--------|------|-------|------|--------|----------|
{scan_table_rows}

## 摘要

- **擠壓行情**：{squeeze_count} 個資產
- **波動偏高**：{elevated_count} 個資產
- **秩序市場**：{orderly_count} 個資產

### 最需關注

- 最高倍率：{highest_ratio_symbol}（{highest_ratio}x）
- 最低倍率：{lowest_ratio_symbol}（{lowest_ratio}x）

## 建議

### 擠壓行情資產
{squeeze_recommendations}

### 波動偏高資產
{elevated_recommendations}

### 秩序市場資產
{orderly_recommendations}

---

*由 detect-atr-squeeze-regime 技能生成*
```

---

## 回測報告

```markdown
# {symbol} ATR 擠壓行情回測報告

**回測期間**：{start_date} 至 {end_date}
**資料點數**：{data_points}

## 行情分布

| 行情     | 天數            | 佔比            |
|----------|-----------------|-----------------|
| 秩序市場 | {orderly_days}  | {orderly_pct}%  |
| 波動偏高 | {elevated_days} | {elevated_pct}% |
| 擠壓行情 | {squeeze_days}  | {squeeze_pct}%  |

## 擠壓期間清單

| # | 起始 | 結束 | 天數 | 峰值 ATR% | 峰值倍率 | 事件 |
|---|------|------|------|-----------|----------|------|
{squeeze_periods_table}

## 統計指標

| 指標          | 數值                    |
|---------------|-------------------------|
| 擠壓期間總數  | {total_squeeze_periods} |
| 平均持續天數  | {avg_duration}          |
| 最長持續天數  | {max_duration}          |
| 平均峰值 ATR% | {avg_peak_atr}%         |
| 平均峰值倍率  | {avg_peak_ratio}x       |

## 事件匹配

- 已知事件匹配：{matched}/{total}（{match_rate}%）
- 匹配事件：{matched_events}
- 遺漏事件：{missed_events}

## 關鍵觀察

{observations}

---

*由 detect-atr-squeeze-regime 技能生成*
```

---

## 填充範例

### 行情顯示對照

| regime                         | regime_display                                     |
|--------------------------------|----------------------------------------------------|
| `orderly_market`               | 秩序市場（Orderly Market）                         |
| `elevated_volatility_trend`    | 波動偏高趨勢（Elevated Volatility Trend）          |
| `volatility_dominated_squeeze` | 波動主導的擠壓行情（Volatility-Dominated Squeeze） |

### ATR% 狀態判定

```python
if atr_pct >= high_vol_threshold_pct:
    atr_pct_status = f"高於高波動門檻（{high_vol_threshold_pct}%）"
elif atr_pct >= baseline * 1.5:
    atr_pct_status = "偏高"
else:
    atr_pct_status = "正常範圍"
```

### Ratio 狀態判定

```python
if ratio >= spike_threshold_x:
    ratio_status = f"高於擠壓門檻（{spike_threshold_x}x）"
elif ratio >= 1.2:
    ratio_status = "偏高"
else:
    ratio_status = "正常範圍"
```

### 可靠度等級

| reliability_score | reliability_level |
|-------------------|-------------------|
| 80-100            | 高                |
| 50-79             | 中                |
| 20-49             | 低                |
| 0-19              | 極低              |

### 時間框架建議

| regime                         | timeframe |
|--------------------------------|-----------|
| `orderly_market`               | 任意      |
| `elevated_volatility_trend`    | 日線以上  |
| `volatility_dominated_squeeze` | 週線以上  |

### 工具建議

| regime                         | instrument    |
|--------------------------------|---------------|
| `orderly_market`               | 裸倉位        |
| `elevated_volatility_trend`    | 裸倉位或期權  |
| `volatility_dominated_squeeze` | 期權/價差結構 |

### 戰術清單格式

```markdown
1. 偏向較長週期決策，降低被日內噪音主導的風險。
2. 若要參與趨勢，優先考慮 defined-risk（期權/價差）結構。
3. 避免緊停損的短線交易，結構性受損。
```
