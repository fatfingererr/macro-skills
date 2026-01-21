# Markdown 報告模板

## 報告結構

```markdown
# 白銀礦業/金屬比率分析報告

**生成時間：** {generated_at}
**數據區間：** {start_date} 至 {end_date}

---

## 一句話結論

{summary}

---

## 當前狀態

| 指標       | 數值                          |
|------------|-------------------------------|
| 礦業代理   | {miner_proxy} ({miner_price}) |
| 白銀代理   | {metal_proxy} ({metal_price}) |
| 當前比率   | {ratio:.4f}                   |
| 平滑比率   | {ratio_smoothed:.4f}          |
| 歷史分位數 | {ratio_percentile:.1f}%       |
| 估值區間   | {zone}                        |

**門檻參考：**
- 底部門檻（{bottom_quantile*100}%）：{bottom_threshold:.4f}
- 頂部門檻（{top_quantile*100}%）：{top_threshold:.4f}
- 歷史中位數：{median_threshold:.4f}

---

## 歷史類比分析

### 底部事件列表

歷史上比率落入底部區間（≤ {bottom_quantile*100}%）的日期：

| # | 事件日期 | 備註 |
|---|----------|------|
| 1 | {date_1} |      |
| 2 | {date_2} |      |
| 3 | {date_3} |      |
...

### 前瞻報酬統計

底部事件後白銀的表現：

| 前瞻期 | 事件數 | 中位數報酬 | 平均報酬 | 勝率  | 最差情境 |
|--------|--------|------------|----------|-------|----------|
| 1 年   | {n}    | {median}%  | {mean}%  | {wr}% | {worst}% |
| 2 年   | {n}    | {median}%  | {mean}%  | {wr}% | {worst}% |
| 3 年   | {n}    | {median}%  | {mean}%  | {wr}% | {worst}% |

**解讀：** 歷史上底部事件後 1 年，白銀中位數報酬為 {median_1y}%，勝率 {wr_1y}%。

---

## 情境推演

**目標：** 比率回到{scenario_target_label}（{target_ratio:.4f}）

### 情境 A：白銀不變

若白銀價格維持 {metal_price}：
- 礦業需漲至 {target_miner_price}
- **漲幅：{miner_gain_pct:.1f}%**

### 情境 B：礦業不變

若礦業價格維持 {miner_price}：
- 白銀需跌至 {target_metal_price}
- **跌幅：{metal_drop_pct:.1f}%**

**解讀：** 這是極端情境的量化邊界，實際可能是兩者同時調整。

---

## 背離檢查

| 指標           | 當前狀態                |
|----------------|-------------------------|
| 比率分位數     | {ratio_percentile:.1f}% |
| 白銀價格分位數 | {metal_percentile:.1f}% |
| 是否存在背離   | {is_divergence}         |

{divergence_interpretation}

---

## 風險提示

1. **比率訊號不是價格保證**：衡量「相對估值」，不預測單邊價格。

2. **樣本量有限**：歷史底部事件僅 {event_count} 次，統計推論能力有限。

3. **結構性風險**：礦業可能因以下原因合理落後：
   - 成本上升（AISC 走高）
   - 股權稀釋（增發融資）
   - 地緣/政策風險
   - ESG 合規成本

4. **ETF 結構差異**：SIL vs SILJ 成分股差異大，需注意代理選擇。

---

## 後續研究建議

1. **成本驗證**：檢查 SIL 主要成分股的 AISC 成本趨勢
2. **持倉分析**：查看 COT 報告中的白銀投機淨部位
3. **資金流向**：觀察 SLV ETF 持倉量變化
4. **跨市場比較**：比較 GDX/GDXJ 是否有類似的比率低估

---

## 附錄：分析參數

| 參數         | 值                       |
|--------------|--------------------------|
| 礦業代理     | {miner_proxy}            |
| 金屬代理     | {metal_proxy}            |
| 分析起點     | {start_date}             |
| 分析終點     | {end_date}               |
| 取樣頻率     | {freq}                   |
| 平滑視窗     | {smoothing_window}       |
| 底部分位門檻 | {bottom_quantile}        |
| 頂部分位門檻 | {top_quantile}           |
| 事件去重間隔 | {min_separation_days} 天 |
| 前瞻期       | {forward_horizons}       |

---

*本報告由 analyze-silver-miner-metal-ratio skill 自動生成*
```

## 使用說明

### 1. 從 JSON 輸出轉換

```python
import json

with open('result.json') as f:
    data = json.load(f)

# 使用模板生成報告
report = generate_markdown_report(data)
```

### 2. 變數替換

模板中的 `{variable}` 需替換為實際數值：

| 變數               | 來源                                             |
|--------------------|--------------------------------------------------|
| {generated_at}     | 生成時間                                         |
| {miner_proxy}      | inputs.miner_proxy                               |
| {ratio_percentile} | current.ratio_percentile                         |
| {zone}             | current.zone                                     |
| {median_1y}        | history_analogs.forward_metal_returns.252.median |
| {miner_gain_pct}   | scenarios.miner_gain_pct_if_metal_flat           |

### 3. 條件區塊

根據分析結果調整報告內容：

```python
if data['current']['zone'] == 'bottom':
    conclusion = "礦業相對白銀處於歷史低估區間"
elif data['current']['zone'] == 'top':
    conclusion = "礦業相對白銀處於歷史高估區間"
else:
    conclusion = "礦業相對白銀處於中性區間"
```
