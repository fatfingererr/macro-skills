# 方法論：白銀礦業/金屬比率分析

## 1. 比率定義

### 1.1 基本公式

```
ratio_t = miner_price_t / metal_price_t
```

其中：
- `miner_price_t`：t 時點的白銀礦業代理價格（如 SIL ETF）
- `metal_price_t`：t 時點的白銀價格（如 SI=F 期貨）

### 1.2 經濟直覺

此比率衡量「為了購買 1 單位白銀敞口，投資者願意支付多少礦業股權」：

| 比率狀態 | 意義                                       |
|----------|--------------------------------------------|
| 比率高   | 礦業相對白銀偏貴（槓桿溢價高、過度樂觀）   |
| 比率低   | 礦業相對白銀偏便宜（可能被低估或反映風險） |

### 1.3 為何用比率而非價差？

- **比率**：無單位，可跨時間比較
- **價差**：受價格水位影響，2010 年的價差無法與 2025 年直接比較

## 2. 數據處理

### 2.1 頻率選擇

| 頻率 | 適用場景                 | 雜訊程度 |
|------|--------------------------|----------|
| 日頻 | 短期交易訊號             | 高       |
| 週頻 | 中期趨勢判斷（建議預設） | 中       |
| 月頻 | 長期循環研究             | 低       |

**建議：** 使用週頻（1wk）以平衡雜訊與及時性。

### 2.2 平滑處理

可選使用移動平均降低雜訊：

```python
ratio_smooth = ratio.rolling(smoothing_window).mean()
```

**建議視窗：**
- 週頻數據：4 週（約 1 個月）
- 月頻數據：3 個月

### 2.3 對數轉換（可選）

對於長期研究，可使用對數比率：

```python
log_ratio = np.log(miner_price) - np.log(metal_price)
```

對數比率在長期尺度更穩定，但直覺性較差。

## 3. 分位數計算

### 3.1 歷史分位數

計算當前比率在歷史分佈中的位置：

```python
ratio_pct = (ratio_smooth.rank(pct=True).iloc[-1]) * 100
```

結果為 0-100 的百分位數：
- 10 百分位 → 歷史上 90% 的時間比率都比現在高
- 90 百分位 → 歷史上 90% 的時間比率都比現在低

### 3.2 門檻定義

定義底部/頂部區間的門檻：

```python
bottom_thr = ratio_smooth.quantile(bottom_quantile)  # 如 0.20
top_thr = ratio_smooth.quantile(top_quantile)        # 如 0.80
```

### 3.3 區間標記

根據當前比率與門檻判斷區間：

```python
if current_ratio <= bottom_thr:
    zone = "bottom"
elif current_ratio >= top_thr:
    zone = "top"
else:
    zone = "neutral"
```

## 4. 歷史事件偵測

### 4.1 事件識別

識別歷史上落入底部區間的日期：

```python
is_bottom = ratio_smooth <= bottom_thr
bottom_dates = ratio_smooth[is_bottom].index
```

### 4.2 事件去重

避免同一段低估區被重複計數：

```python
dedup = []
last = None
for d in bottom_dates:
    if last is None or (d - last).days >= min_separation_days:
        dedup.append(d)
        last = d
```

**建議間隔：** 180 天（約 6 個月）

### 4.3 前瞻報酬計算

計算事件後的白銀報酬：

```python
for H in forward_horizons:  # 如 [252, 504, 756] 交易日
    for d in dedup:
        i = metal.index.get_loc(d)
        j = i + H
        if j < len(metal):
            ret = metal.iloc[j] / metal.iloc[i] - 1
            returns.append(ret)
```

### 4.4 統計摘要

計算前瞻報酬的統計量：

| 統計量   | 意義         |
|----------|--------------|
| count    | 事件數量     |
| median   | 中位數報酬   |
| mean     | 平均報酬     |
| win_rate | 正報酬的機率 |
| worst    | 最差情境報酬 |

## 5. 情境推演

### 5.1 目標設定

定義情境目標：

| 目標             | 公式                         |
|------------------|------------------------------|
| return_to_top    | target_ratio = top_thr       |
| return_to_median | target_ratio = median(ratio) |

### 5.2 礦業倍數計算

若白銀不變，礦業需要的倍數：

```python
miner_multiplier = target_ratio / current_ratio
```

例如：2.45 / 1.14 = 2.15x（需漲 115%）

### 5.3 白銀跌幅計算

若礦業不變，白銀需要的變化：

```python
metal_multiplier = current_ratio / target_ratio
metal_drop_pct = 1 - metal_multiplier
```

例如：1 - (1.14 / 2.45) = 54%（需跌 54%）

## 6. 訊號解讀

### 6.1 底部區間訊號

當 `zone = "bottom"` 時：

**正面解讀：**
- 礦業相對白銀歷史上很便宜
- 歷史類比顯示後續白銀多有正報酬
- 可能是中長期買入機會

**風險提示：**
- 礦業可能因成本上升被合理定價
- 股權稀釋可能壓低礦業估值
- 地緣/政策風險可能持續

### 6.2 背離訊號

當出現「比率低 + 白銀高」：

```python
if zone == "bottom" and silver_percentile > 70:
    signal = "divergence"
```

此背離意味著：
- 白銀價格已在高位
- 但礦業未同步上漲
- 可能是礦業追趕機會，或結構性問題

### 6.3 頂部區間訊號

當 `zone = "top"` 時：

**可能意涵：**
- 礦業相對白銀過度樂觀
- 槓桿溢價過高
- 需警惕均值回歸風險

## 7. 方法論限制

### 7.1 樣本量問題

- 歷史底部事件通常僅 3-5 次
- 統計推論能力有限
- 不應過度信賴勝率

### 7.2 代理選擇偏誤

- SIL vs SILJ 成分股差異大
- ETF 可能有追蹤誤差
- 自建指數需處理存活者偏誤

### 7.3 結構性變化

- 礦業成本結構可能永久改變
- 新礦山/技術可能改變供給曲線
- 過往關係可能不再適用

### 7.4 單因子限制

- 比率訊號應結合其他因子
- 建議搭配：成本曲線、COT 持倉、ETF 流量、美元/利率
