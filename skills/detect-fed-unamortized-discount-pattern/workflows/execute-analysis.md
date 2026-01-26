# Workflow: 完整形狀比對分析

<required_reading>
**執行前請閱讀：**
1. references/methodology.md - 形狀比對方法論
2. references/data-sources.md - 資料來源與 FRED 代碼
3. references/input-schema.md - 完整參數定義
</required_reading>

<process>

## Step 1: 資料抓取

從 FRED 抓取目標序列與交叉驗證指標。

```bash
cd skills/detect-fed-unamortized-discount-pattern
python scripts/fetch_data.py --series WUDSHO --start 2015-01-01
```

或直接執行主腳本（自動抓取）：

```bash
python scripts/pattern_detector.py --quick
```

**驗證點**：
- [ ] WUDSHO 資料抓取成功
- [ ] 交叉驗證指標（信用利差、VIX 等）抓取成功
- [ ] 資料頻率對齊（週頻）

## Step 2: 窗口切片與正規化

切出近期窗口與歷史基準窗口，進行正規化。

**預設參數**：
- `recent_window_days`: 120（約 17 週）
- `normalize_method`: zscore
- `resample_freq`: W

**正規化目的**：
- 去除量級差異，只保留「形狀」
- zscore：均值=0、標準差=1，適合形狀比較
- pct_change：強調加速/減速，適合動量分析

## Step 3: 形狀相似度計算

使用多種方法計算相似度：

### 3.1 相關係數 (Correlation)
```
corr = pearson_corr(recent_normalized, baseline_normalized)
```
- 範圍：-1 ~ 1
- > 0.7：高度相似
- 0.4 ~ 0.7：中度相似
- < 0.4：低度相似

### 3.2 動態時間校正 (DTW)
```
dtw_dist = dtw_distance(recent_values, baseline_values)
```
- 範圍：0 ~ ∞（越小越相似）
- < 0.5：高度相似
- 0.5 ~ 1.5：中度相似
- > 1.5：低度相似

### 3.3 形狀特徵相似度
提取特徵：
- 趨勢斜率（線性回歸斜率）
- 拐點結構（峰谷數量與位置）
- 波動擴張（rolling std 變化）

計算特徵向量的餘弦相似度。

## Step 4: 最佳匹配選擇

對每個基準窗口，找出最相似的片段：

```python
for baseline_window in baseline_windows:
    for segment in rolling_segments(baseline, length=recent_length):
        score = weighted_avg(corr, 1-dtw_norm, feature_sim)
        if score > best_score:
            best_match = segment
```

輸出 `best_match`：
- baseline 名稱
- segment_start / segment_end
- corr / dtw / feature_sim
- pattern_similarity_score

## Step 5: 壓力驗證

計算交叉驗證指標的壓力分數：

```python
for indicator in confirmatory_indicators:
    data = fetch_series(indicator.series)
    recent_data = data.last(recent_window_days)
    z = (recent_data.mean() - historical_mean) / historical_std

    if indicator.name == "yield_curve":
        signal = "stress" if z < indicator.stress_threshold else "neutral"
    else:
        signal = "stress" if z > indicator.stress_threshold else "neutral"

    stress_score += indicator.weight * (1 if signal == "stress" else 0)
```

輸出 `stress_confirmation`：
- score（0-1）
- details（各指標名稱、訊號、z-score）

## Step 6: 合成風險分數

```python
composite = 0.6 * pattern_similarity_score + 0.4 * stress_confirmation_score
```

**解讀**：
- > 0.7：高風險，形狀相似且壓力驗證支持
- 0.4 ~ 0.7：中風險，形狀相似但壓力驗證中性
- < 0.4：低風險，形狀不相似或壓力驗證反對

## Step 7: 解讀生成

生成結構化解讀：

### summary
一句話總結：形狀相似度 + 壓力驗證 → 風險判斷

### what_to_watch_next_60d
未來 60 天觀察重點：
- 若形狀相似度維持高檔 + 壓力指標開始惡化 → 升級警報
- 若形狀相似度下降或壓力指標改善 → 降級警報

### rebuttal_to_claim
對「黑天鵝」敘事的反證：
- 形狀相似的替代解釋（利率效果、會計效果）
- 當前缺乏哪些壓力共振訊號
- 「像」≠「會發生」的認知提醒

## Step 8: 輸出結果

```bash
python scripts/pattern_detector.py \
  --target_series WUDSHO \
  --baseline_windows "COVID_2020:2020-01-01:2020-06-30" \
  --recent_window_days 120 \
  --output result.json
```

輸出檔案：
- `result.json`：完整 JSON 結果
- `result.md`：Markdown 報告（若指定 --markdown）

</process>

<success_criteria>
工作流完成時應產出：

- [ ] 成功抓取 WUDSHO 資料
- [ ] 成功抓取所有交叉驗證指標
- [ ] 計算完成 pattern_similarity_score
- [ ] 計算完成 stress_confirmation_score
- [ ] 計算完成 composite_risk_score
- [ ] 生成完整 interpretation
- [ ] 輸出 JSON 結果檔
- [ ] 包含 caveats 風險警語
</success_criteria>
