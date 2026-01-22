# 估值分位數極端偵測方法論

## 核心概念

### 為什麼用分位數？

傳統估值指標（PE、PB、CAPE 等）有不同單位和量綱：
- PE 可能在 10-40 之間
- PB 可能在 1-5 之間
- 市值/GDP 可能在 50%-200% 之間

**問題**：如何比較「PE = 25」和「PB = 3」哪個更極端？

**解決方案**：轉換為「歷史分位數」
- PE = 25 若位於歷史第 85 分位 → 表示過去只有 15% 的時間比現在更貴
- PB = 3 若位於歷史第 92 分位 → 表示過去只有 8% 的時間比現在更貴
- 現在可以直接比較：PB 相對更極端

### 分位數計算公式

```python
def percentile_rank(series, value):
    """
    計算 value 在 series 中的分位數排名

    Parameters
    ----------
    series : pd.Series
        歷史樣本（去除缺值）
    value : float
        當期值

    Returns
    -------
    float
        0-100 的分位數
    """
    s = series.dropna().values
    return 100.0 * (s <= value).sum() / len(s)
```

**重要**：這是「經驗分布函數」(ECDF) 方法，假設歷史分布是當前估值的良好參考。

## 多指標合成邏輯

### 為什麼要合成多個指標？

單一估值指標可能受特定因素影響：
- **PE** 受短期盈餘波動影響（景氣低點時分母很小，PE 飆高但不代表高估）
- **PB** 對資產密集型行業更敏感
- **CAPE** 用 10 年平均盈餘，更穩定但反應較慢

**合成多指標**可以：
1. 降低單一指標的噪音
2. 捕捉「全面性高估」vs「單一指標異常」
3. 提供更穩健的估值信號

### 合成方法

```python
def aggregate_percentiles(pct_dict, weights=None, method="mean"):
    """
    合成多個指標的分位數

    Parameters
    ----------
    pct_dict : dict
        {指標名稱: 分位數}，如 {"cape": 98, "pe": 95, "pb": 92}
    weights : dict, optional
        指標權重，未給則等權
    method : str
        合成方法：mean（算術平均）、median（中位數）、trimmed_mean（去極端平均）

    Returns
    -------
    float
        合成分位數 (0-100)
    """
    if not pct_dict:
        return None

    items = list(pct_dict.items())
    vals = np.array([v for _, v in items], dtype=float)

    if weights:
        w = np.array([weights.get(k, 0.0) for k, _ in items], dtype=float)
        w = w / w.sum()
        return float(np.sum(vals * w))

    if method == "median":
        return float(np.median(vals))
    elif method == "trimmed_mean":
        # 去掉最高和最低後平均
        return float(np.mean(np.sort(vals)[1:-1])) if len(vals) > 2 else float(np.mean(vals))

    return float(np.mean(vals))
```

### 建議權重配置

| 指標 | 建議權重 | 理由 |
|------|----------|------|
| CAPE | 30% | 最穩定的長期估值指標 |
| 市值/GDP | 25% | 巴菲特指標，總量視角 |
| Trailing PE | 15% | 最即時但波動大 |
| Forward PE | 15% | 含預期但依賴分析師 |
| PB | 10% | 資產視角 |
| PS | 5% | 營收視角 |

## 極端偵測邏輯

### 門檻設定

```
極端高估判定：composite_percentile >= 95
```

**為什麼是 95？**
- 95 分位意味著「歷史上只有 5% 的時間比現在更貴」
- 對於 100 年歷史，這約等於 5 年
- 經驗上，這些時期通常對應重大市場頂點

**可調整門檻**：
- 90：更敏感，可能有更多假警報
- 97：更嚴格，只捕捉極端情況
- 99：非常罕見，可能錯過警示

### 歷史事件識別演算法

```python
def find_extreme_episodes(composite_series, threshold=95, min_gap_days=3650):
    """
    找出歷史上的極端高估事件

    Parameters
    ----------
    composite_series : pd.Series
        合成分位數的時間序列
    threshold : float
        極端門檻（分位數）
    min_gap_days : int
        事件去重的最小間隔（天）

    Returns
    -------
    list
        極端事件的日期列表
    """
    peaks = []
    last_peak_date = None

    for date, val in composite_series.items():
        if val >= threshold:
            if last_peak_date is None or (date - last_peak_date).days >= min_gap_days:
                # 新事件
                peaks.append(date)
                last_peak_date = date
            else:
                # 同一段期間內，保留更高者
                if composite_series[date] > composite_series[last_peak_date]:
                    peaks[-1] = date
                    last_peak_date = date

    return peaks
```

**去重邏輯的重要性**：
- 極端高估可能持續數月甚至數年
- 不去重會產生大量「重複事件」
- 預設 10 年間隔確保每個「世代」只保留最極端的一次

## 事後統計方法論

### 條件分布分析

當偵測到極端高估時，我們想回答：
> 「歷史上類似情況發生後，市場表現如何？」

這是一個「條件分布」問題：
```
P(未來報酬 | 當前估值 >= 95 分位)
```

### 計算方法

```python
def calculate_conditional_stats(price_series, event_dates, forward_windows):
    """
    計算條件分布統計

    對每個歷史事件，計算其後的報酬、回撤、波動
    """
    stats = {}

    for window in forward_windows:
        returns = []
        drawdowns = []

        for event_date in event_dates:
            # 未來報酬
            future_date = event_date + timedelta(days=window)
            if future_date in price_series.index:
                ret = (price_series[future_date] / price_series[event_date]) - 1
                returns.append(ret)

            # 最大回撤
            period_prices = price_series[event_date:future_date]
            if len(period_prices) > 0:
                rolling_max = period_prices.cummax()
                dd = (period_prices - rolling_max) / rolling_max
                drawdowns.append(dd.min())

        stats[f'{window}d'] = {
            'forward_return': {
                'median': np.median(returns),
                'p25': np.percentile(returns, 25),
                'p10': np.percentile(returns, 10),
                'positive_prob': (np.array(returns) > 0).mean()
            },
            'max_drawdown': {
                'median': np.median(drawdowns),
                'p75': np.percentile(drawdowns, 75),
                'worst': np.min(drawdowns)
            }
        }

    return stats
```

### 解讀框架

**重要認知**：
1. **不是預測**：這是「條件分布」，不是「一定會發生」
2. **樣本有限**：100 年可能只有 4-6 次極端事件
3. **時代差異**：1929 和 2021 的市場環境天差地別
4. **擇時風險**：估值可以「錯更久」，不適合做空

**建議用法**：
- 作為「風險雷達」：極端時提高警覺
- 調整配置：降低槓桿、增加防禦資產
- 不要據此「逃頂」：錯過最後一段上漲的代價很高

## 資料品質考量

### 不同指標的歷史長度

| 指標 | 可回溯至 | 來源 |
|------|----------|------|
| CAPE | 1871 年 | Shiller 資料集 |
| 市值/GDP | 1950 年代 | FRED |
| PE/PB | 1980 年代 | 公開金融資料 |
| Forward PE | 2000 年代 | 分析師預估 |

**處理方式**：
1. **方案 A**：只用共同可得期間（最短的那個）
2. **方案 B**：各指標用各自歷史算分位數，再在同日合成（本 skill 預設）

**必須揭露**：
- 使用方案 B 時，不同指標的「歷史基準」不同
- CAPE 的 95 分位可能是 130 年中的前 5%
- PE 的 95 分位可能只是 40 年中的前 5%

### 資料延遲

| 指標類型 | 延遲 | 說明 |
|----------|------|------|
| 價格類 | 實時 | 每日可得 |
| PE/PB | 季度 | 等待財報 |
| GDP | 季度+修正 | 初值 → 修正值 |

**處理方式**：
- 使用最新可得數據
- 揭露「資料截止日」
- 不要假裝是「即時」

## 方法論限制

1. **過去不代表未來**：歷史分布可能不再適用於當前環境
2. **結構性變化**：利率環境、央行政策、全球化改變了估值中樞
3. **倖存者偏差**：我們只研究「贏家」（美股），失敗的市場沒有 130 年數據
4. **均值回歸假設**：假設估值終會回歸，但「何時」是未知數
5. **交易成本**：據此操作可能產生大量交易成本

## 參考文獻

- Shiller, R.J. (2000). *Irrational Exuberance*
- Hussman, J. (2021). "Valuations and Prospective Returns"
- AQR (2017). "Expected Returns on Major Asset Classes"
