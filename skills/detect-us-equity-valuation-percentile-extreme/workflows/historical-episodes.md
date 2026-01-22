# Workflow: Historical Episodes Analysis

<required_reading>
**執行前閱讀：**
1. references/methodology.md - 歷史類比邏輯
2. references/valuation-metrics.md - 理解各指標的歷史背景
</required_reading>

<process>

## Step 1: 確認分析範圍

**必要參數**：
- `history_start`: 歷史起算日（預設 1900-01-01，實際依資料可得性）
- `episode_min_gap_days`: 事件去重間隔（預設 3650 天 = 10 年）
- `forward_windows_days`: 事後分析視窗（預設 [180, 365, 1095]）

**可選參數**：
- `risk_readouts`: 要輸出的風險解讀項目
  - `max_drawdown`: 最大回撤
  - `forward_return`: 未來報酬
  - `volatility_change`: 波動變化
  - `valuation_reversion_speed`: 估值均值回歸速度

## Step 2: 建立完整歷史合成分位數序列

使用所有可得的歷史資料，計算「滾動分位數」：

```python
# 對每個時間點 t，計算「截至 t 的歷史分位數」
rolling_percentile = []
for t in date_range:
    history_up_to_t = data[:t]
    current_value = data[t]
    pct = percentile_rank(history_up_to_t, current_value)
    rolling_percentile.append(pct)
```

這樣可以得到一條「歷史上每個時點的估值分位數」序列。

## Step 3: 識別極端高估事件

使用峰值偵測演算法：

```python
def find_extreme_episodes(composite_series, threshold=95, min_gap_days=3650):
    peaks = []
    last_peak_date = None

    for date, val in composite_series.items():
        if val >= threshold:
            if last_peak_date is None or (date - last_peak_date).days >= min_gap_days:
                peaks.append(date)
                last_peak_date = date
            else:
                # 同一段期間內只保留更高者
                if composite_series[date] > composite_series[last_peak_date]:
                    peaks[-1] = date
                    last_peak_date = date

    return peaks
```

**歷史上的主要極端事件**（以 CAPE 為例）：

| 事件期間 | 背景 | CAPE 水準 | 後續發展 |
|----------|------|-----------|----------|
| 1929-09 | 大蕭條前夕 | ~33 | 崩跌 89% |
| 1965-01 | Nifty Fifty | ~24 | 16 年實質報酬歸零 |
| 1999-12 | 科技泡沫 | ~44 | 崩跌 50%+ |
| 2021-12 | 疫情後牛市 | ~40 | 待觀察 |

## Step 4: 計算每個事件的事後統計

對識別出的每個極端事件，計算以下統計：

### 4.1 未來報酬分布

```python
def calculate_forward_returns(price_series, event_dates, windows=[180, 365, 1095]):
    results = {}
    for window in windows:
        returns = []
        for event_date in event_dates:
            future_date = event_date + timedelta(days=window)
            if future_date in price_series.index:
                ret = price_series[future_date] / price_series[event_date] - 1
                returns.append(ret)

        results[f'{window}d'] = {
            'median': np.median(returns),
            'p25': np.percentile(returns, 25),
            'p10': np.percentile(returns, 10),
            'count': len(returns)
        }
    return results
```

### 4.2 最大回撤

```python
def calculate_max_drawdown(price_series, event_dates, windows):
    results = {}
    for window in windows:
        drawdowns = []
        for event_date in event_dates:
            end_date = event_date + timedelta(days=window)
            period_prices = price_series[event_date:end_date]

            rolling_max = period_prices.cummax()
            drawdown = (period_prices - rolling_max) / rolling_max
            max_dd = drawdown.min()
            drawdowns.append(max_dd)

        results[f'{window}d_max_drawdown'] = {
            'median': np.median(drawdowns),
            'p75': np.percentile(drawdowns, 75),
            'worst': np.min(drawdowns)
        }
    return results
```

### 4.3 波動變化

```python
def calculate_volatility_change(returns_series, event_dates, before_window=252, after_window=252):
    vol_changes = []
    for event_date in event_dates:
        before_vol = returns_series[event_date - timedelta(days=before_window):event_date].std() * np.sqrt(252)
        after_vol = returns_series[event_date:event_date + timedelta(days=after_window)].std() * np.sqrt(252)
        vol_changes.append(after_vol - before_vol)

    return {
        'median_change': np.median(vol_changes),
        'pct_increased': (np.array(vol_changes) > 0).mean()
    }
```

## Step 5: 彙整風險解讀

將統計結果轉化為可理解的風險解讀：

**解讀框架**：

```markdown
## 歷史極端高估事件的後續表現

當估值分位數接近 95-100 時，歷史上的特徵：

### 未來報酬
- **1 年後**: 中位數報酬 X%，下四分位 Y%
- **3 年後**: 中位數報酬 A%，下四分位 B%
- 正報酬機率：Z%

### 回撤風險
- **1 年最大回撤**: 中位數 -M%，最差情境 -N%
- **3 年最大回撤**: 中位數 -P%，最差情境 -Q%

### 波動特徵
- 事件後 12 個月波動上升機率：R%
- 波動中位數變化：+S 個百分點

### 關鍵結論
「估值極端高」不代表「立即崩盤」，但：
1. 風險分布變得不對稱（下跌尾巴變厚）
2. 未來中期報酬的不確定性大增
3. 估值均值回歸會壓低長期報酬上限
```

## Step 6: 輸出報告

產生歷史類比分析報告：

```bash
python scripts/valuation_percentile.py \
  --mode historical_episodes \
  --forward_windows "180,365,1095" \
  --risk_readouts "max_drawdown,forward_return,volatility_change" \
  --output "output/historical_episodes.json"
```

</process>

<success_criteria>
工作流程完成時：

- [ ] 成功建立歷史合成分位數序列
- [ ] 識別出所有極端高估事件（符合門檻）
- [ ] 每個事件都計算了事後統計
- [ ] 報酬、回撤、波動統計完整
- [ ] 產生可理解的風險解讀框架
- [ ] 輸出 JSON 或 Markdown 報告
</success_criteria>

<interpretation_notes>

**解讀注意事項**：

1. **樣本數有限**：百年歷史中極端高估事件可能只有 4-6 次，統計意義有限
2. **時代背景不同**：1929 與 2021 的市場結構、央行政策、全球化程度差異巨大
3. **倖存者偏差**：我們只看到美股這個「贏家」，其他市場的極端高估可能更慘
4. **估值可以維持更久**：「估值高」可能持續數年，擇時風險巨大

**建議用法**：
- 作為「風險雷達」而非「擇時工具」
- 極端高估 → 降低槓桿、增加防禦配置
- 不要據此做空或完全離場
</interpretation_notes>
