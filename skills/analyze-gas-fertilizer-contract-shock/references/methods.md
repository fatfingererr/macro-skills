# 方法論：Shock 偵測與領先落後分析

<overview>
本文件說明天然氣→化肥因果假說檢驗的技術方法論。

核心問題：如何從價格時間序列判斷「A 導致 B」？

答案：時序上 A 先動、B 後動，且統計上 A 領先 B。
</overview>

---

## 1. 三段式因果檢驗框架

### 1.1 設計原理

敘事「天然氣暴漲→化肥供應受限→化肥飆價」包含三個可檢驗的假說：

| 階段 | 假說 | 可觀測證據 |
|------|------|-----------|
| A | 天然氣出現異常暴漲 | Gas 價格 z-score 或斜率突破閾值 |
| B | 化肥在 A 之後出現異常上漲 | Fert 價格在 Gas shock 後出現 spike |
| C | Gas 統計上領先 Fert | Cross-correlation 顯示 Gas 領先 |

### 1.2 判斷邏輯

```
A_pass AND B_pass AND C_pass → 敘事有強支撐
A_pass AND B_pass           → 敘事有中度支撐（但 lead-lag 不明確）
A_pass only                 → 敘事較弱（化肥未跟隨）
None                        → 不成立
```

---

## 2. Shock/Spike 偵測方法

### 2.1 Rolling Z-Score

**定義**：當日報酬率相對於歷史分布的標準化偏離程度。

```python
r_t = price_t / price_{t-1} - 1  # 日報酬率

mu_t = rolling_mean(r, window=60)  # 60 日滾動平均
sigma_t = rolling_std(r, window=60)  # 60 日滾動標準差

z_t = (r_t - mu_t) / sigma_t
```

**閾值解讀**：

| z 值 | 機率（常態分布） | 意義 |
|------|-----------------|------|
| z >= 2 | ~2.3% | 異常 |
| z >= 3 | ~0.13% | 極端異常 |
| z >= 4 | ~0.003% | 黑天鵝等級 |

**預設閾值**：z >= 3.0

### 2.2 斜率代理

**定義**：短期價格變化的日均漲幅。

```python
k = 20  # 20 日視窗
slope_t = (price_t / price_{t-k} - 1) / k
```

**解讀**：
- slope = 1.5% 代表過去 20 天日均漲 1.5%
- 20 天累計漲幅 = 1.5% × 20 = 30%

**預設閾值**：slope >= 1.5%/day

### 2.3 雙重確認

使用 z-score 或斜率任一觸發即標記為 shock：

```python
shock = (z_t >= z_threshold) | (slope_t >= slope_threshold)
```

**為什麼雙重條件？**
- z-score 捕捉「突然爆發」（單日大漲）
- 斜率捕捉「持續攀升」（多日累積）
- 兩者互補，覆蓋不同類型的 shock

---

## 3. Regime 合併演算法

### 3.1 問題

連續多天的 shock 應視為同一個 regime，而非多個獨立事件。

### 3.2 演算法

```python
def compress_boolean_to_regimes(df, shock_col, value_col):
    """
    將布林值序列壓縮為 regime 清單

    Returns:
    [
        {
            "start": "2026-01-12",
            "end": "2026-01-29",
            "peak_date": "2026-01-25",
            "peak_value": 6.95,
            "regime_return_pct": 85.4,
            "duration_days": 18
        },
        ...
    ]
    """
    regimes = []
    in_regime = False
    current_regime = None

    for idx, row in df.iterrows():
        if row[shock_col] and not in_regime:
            # 新 regime 開始
            in_regime = True
            current_regime = {
                "start": idx,
                "end": idx,
                "peak_value": row[value_col],
                "peak_date": idx,
                "start_value": row[value_col]
            }
        elif row[shock_col] and in_regime:
            # 延續 regime
            current_regime["end"] = idx
            if row[value_col] > current_regime["peak_value"]:
                current_regime["peak_value"] = row[value_col]
                current_regime["peak_date"] = idx
        elif not row[shock_col] and in_regime:
            # Regime 結束
            in_regime = False
            current_regime["regime_return_pct"] = (
                (current_regime["peak_value"] / current_regime["start_value"] - 1) * 100
            )
            current_regime["duration_days"] = (
                current_regime["end"] - current_regime["start"]
            ).days + 1
            regimes.append(current_regime)
            current_regime = None

    return regimes
```

---

## 4. 領先落後分析

### 4.1 Cross-Correlation

計算兩個時間序列在不同 lag 下的相關係數。

```python
from scipy import signal

def cross_correlation_analysis(x, y, max_lag=60):
    """
    計算 x 與 y 的交叉相關

    Returns:
    {
        "best_lag": int,   # 最大相關的 lag
        "best_corr": float, # 最大相關係數
        "all_lags": [...],  # 所有 lag
        "all_corrs": [...]  # 所有相關係數
    }
    """
    # 標準化
    x = (x - x.mean()) / x.std()
    y = (y - y.mean()) / y.std()

    # 計算交叉相關
    corr = signal.correlate(x, y, mode='full')
    lags = signal.correlation_lags(len(x), len(y), mode='full')

    # 正規化
    corr = corr / max(len(x), len(y))

    # 限制在 max_lag 範圍內
    mask = (lags >= -max_lag) & (lags <= max_lag)
    lags = lags[mask]
    corr = corr[mask]

    # 找最大
    best_idx = np.argmax(np.abs(corr))

    return {
        "best_lag": lags[best_idx],
        "best_corr": corr[best_idx],
        "all_lags": lags.tolist(),
        "all_corrs": corr.tolist()
    }
```

### 4.2 Lag 解讀

| best_lag | 意義 | 敘事支撐度 |
|----------|------|-----------|
| > 0 | x 領先 y（Gas 領先 Fert） | 高 |
| = 0 | 同時變動 | 中（共同驅動） |
| < 0 | y 領先 x（Fert 領先 Gas） | 低 |

### 4.3 合理領先期

根據經濟傳導機制，Gas → Fert 的合理領先期：

| 傳導環節 | 時間 |
|----------|------|
| 天然氣價格上漲被觀察 | 即時 |
| 生產商評估成本影響 | 1-2 週 |
| 決定減產/停產 | 2-4 週 |
| 供給減少反映到化肥價格 | 2-4 週 |
| **總計** | **1-8 週（7-56 天）** |

若 best_lag 在 7-56 天範圍內，敘事更有說服力。

---

## 5. 替代解釋

當敘事檢驗不成立時，應提供替代解釋：

### 5.1 Gas 大漲但 Fert 不動

可能原因：
- 化肥庫存充足，短期不受影響
- 化肥價格由需求主導（農業週期）
- 其他生產成本抵消（如運費下降）
- 政府補貼或價格管制

### 5.2 Fert 先動

可能原因：
- 化肥需求獨立變化（種植季節）
- 出口限制或貿易政策
- 預期效應（市場預期 Gas 將上漲）

### 5.3 兩者同時動

可能原因：
- 共同驅動因素（地緣政治事件）
- 整體能源成本上升
- 通膨預期

---

## 6. 方法論限制

### 6.1 無法證明因果

時間序列分析只能證明「相關」和「時序先後」，不能證明「因果」。

敘事成立需要額外條件：
- 機制合理（Gas 是 Fert 的成本）
- 無重大干擾因素
- 類似情況歷史上也成立

### 6.2 數據頻率限制

- TradingEconomics 日頻數據可能有缺失
- World Bank Pink Sheet 為月頻
- 不同頻率混用需謹慎對齊

### 6.3 地區差異

- 美國 Henry Hub 天然氣與歐洲 TTF 價格可能背離
- 全球化肥市場但有區域差異
- 跨區域分析需額外考慮

---

## 7. 參數建議

### 7.1 預設參數

```python
DEFAULT_PARAMS = {
    "return_window": 1,        # 日報酬
    "z_window": 60,            # 60 日 rolling
    "z_threshold": 3.0,        # 3 標準差
    "slope_window": 20,        # 20 日斜率
    "slope_threshold": 0.015,  # 1.5%/day
    "max_lag_days": 60,        # 最大 lag 60 天
    "reasonable_lag_range": (7, 56)  # 合理領先期
}
```

### 7.2 調參建議

| 場景 | 調整 |
|------|------|
| 波動性高的市場 | 提高 z_threshold 到 3.5-4.0 |
| 短期分析（< 3 個月） | 縮短 z_window 到 30-40 |
| 週頻數據 | 調整 reasonable_lag_range 到 (1, 8) 週 |

---

## 8. 參考文獻

- Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press.
- Granger, C. W. J. (1969). "Investigating Causal Relations by Econometric Models and Cross-spectral Methods." *Econometrica*.
- Stock, J. H., & Watson, M. W. (1999). "Forecasting Inflation." *Journal of Monetary Economics*.
