# 方法論與計算邏輯

本文件說明「殖利率利差 → 板塊相對報酬」領先關係的完整方法論。

---

## 1. 核心概念

### 1.1 殖利率利差（Yield Spread）

殖利率曲線利差反映市場對未來經濟的預期：

```
spread_t = short_yield_t - long_yield_t
         = US02Y_t - US10Y_t
```

**解讀：**
- **spread > 0**：曲線倒掛（短端高於長端）→ 市場預期降息/衰退
- **spread < 0**：曲線正常（短端低於長端）→ 市場預期正常增長
- **spread 趨勢**：
  - 變陡（spread 下降）→ 經濟復甦預期
  - 變平/倒掛（spread 上升）→ 經濟放緩預期

### 1.2 相對報酬（Relative Return）

比較兩類資產的相對績效：

```
ratio_t = risk_asset_t / defensive_asset_t
        = QQQ_t / XLV_t
```

**預測目標**：未來 H 個月的對數相對報酬

```
future_rel_return_t,H = log(ratio_{t+H} / ratio_t)
                      = log(QQQ_{t+H}/XLV_{t+H}) - log(QQQ_t/XLV_t)
```

**為何用對數報酬而非水平值？**
- 避免非平穩性（ratio 有趨勢）
- 對數報酬近似對稱
- 統計性質更好（近似常態）

### 1.3 領先關係（Lead-Lag Relationship）

假設 spread 領先 relative return H 個月：

```
X_t = spread_t
Y_t = future_rel_return_{t,H}
```

若存在領先關係：
```
Corr(X_t, Y_t) ≠ 0
```

---

## 2. 計算步驟

### Step 1: 數據取得與對齊

1. **殖利率**：從 FRED 取得 DGS2、DGS10
2. **資產價格**：從 yfinance 取得 QQQ、XLV（調整後收盤價）
3. **頻率對齊**：統一為週頻或月頻

```python
def to_weekly(df):
    return df.resample("W-FRI").last().dropna()
```

### Step 2: 計算利差與比率

```python
# 殖利率利差
spread = dgs2 - dgs10  # 注意：2Y - 10Y

# 相對比率
ratio = qqq / xlv
```

### Step 3: 計算未來相對報酬

```python
def compute_future_rel_return(ratio: pd.Series, horizon_weeks: int) -> pd.Series:
    """計算未來 H 週的對數相對報酬"""
    return np.log(ratio.shift(-horizon_weeks) / ratio)
```

**注意**：`shift(-H)` 表示取未來值，最後 H 筆會是 NaN。

### Step 4: 可選平滑

```python
if smoothing_window > 1:
    spread_smoothed = spread.rolling(smoothing_window).mean()
else:
    spread_smoothed = spread
```

**平滑的作用**：
- 減少短期雜訊
- 捕捉趨勢而非日常波動
- 建議視窗：13 週（約 1 季）或 26 週（約半年）

---

## 3. 模型估計

### 3.1 相關性分析

```python
corr = np.corrcoef(spread_smoothed, future_rel_return)[0, 1]
```

**解讀**：
- |corr| > 0.3：中等關係
- |corr| > 0.5：較強關係
- 負相關意味：spread 越高 → 未來相對報酬越低

### 3.2 簡單迴歸

```python
# OLS 迴歸: Y = alpha + beta * X
beta = np.cov(x, y)[0, 1] / np.var(x)
alpha = np.mean(y) - beta * np.mean(x)
```

**係數解讀**：
- **beta < 0**：spread 每上升 1%，未來相對報酬預期下降 |beta|%
- **alpha**：當 spread = 0 時的基準相對報酬

### 3.3 預測與區間

**點估計**：
```python
x_now = spread_smoothed.iloc[-1]
y_hat = alpha + beta * x_now
```

**區間估計**（基於殘差分佈）：
```python
residuals = y - (alpha + beta * x)
lo, hi = np.quantile(residuals, [0.10, 0.90])  # 80% 區間
y_interval = (y_hat + lo, y_hat + hi)
```

**轉換為百分比**：
```python
pct_return = np.exp(y_hat) - 1
pct_interval = (np.exp(y_hat + lo) - 1, np.exp(y_hat + hi) - 1)
```

---

## 4. 領先期掃描

### 4.1 掃描邏輯

測試多個領先期（如 6, 12, 18, 24, 30 個月），找最佳相關性：

```python
def lead_scan(spread, ratio, leads=[6, 12, 18, 24, 30]):
    results = {}
    for lead in leads:
        horizon_weeks = int(lead * 4.345)  # 月轉週
        y = compute_future_rel_return(ratio, horizon_weeks)
        valid = spread.notna() & y.notna()
        corr = np.corrcoef(spread[valid], y[valid])[0, 1]
        results[lead] = corr
    return results
```

### 4.2 最佳領先期選擇

```python
best_lead = max(results, key=lambda k: abs(results[k]))
```

**注意**：
- 選擇相關性絕對值最大的領先期
- 但要驗證穩定性（見下節）

---

## 5. 穩定性驗證

### 5.1 子樣本分割

將數據分成前半與後半，分別計算相關性：

```python
n = len(data)
first_half = data.iloc[:n//2]
second_half = data.iloc[n//2:]

corr_first = compute_correlation(first_half)
corr_second = compute_correlation(second_half)
```

### 5.2 一致性判斷

| 條件                    | 一致性等級 |
|-------------------------|------------|
| 兩段相關性符號相同且 |差| < 0.1 | 高         |
| 兩段相關性符號相同且 |差| < 0.2 | 中高       |
| 兩段相關性符號相同但 |差| > 0.2 | 中         |
| 兩段相關性符號不同                | 低         |

### 5.3 滾動相關（進階）

```python
def rolling_correlation(x, y, window=52):
    """滾動 1 年相關性"""
    return pd.Series(x).rolling(window).corr(pd.Series(y))
```

觀察滾動相關是否穩定在某個區間。

---

## 6. 經濟解讀

### 6.1 為何 spread 領先相對報酬？

1. **貨幣政策傳導**
   - 曲線形態反映 Fed 政策預期
   - 政策影響實體經濟需 12-24 個月

2. **風險偏好週期**
   - 倒掛 → 避險情緒 → 防禦股相對強
   - 變陡 → 風險偏好 → 成長股相對強

3. **企業獲利週期**
   - 曲線領先經濟 → 經濟領先獲利 → 獲利領先股價
   - 總計約 18-30 個月

### 6.2 負相關的直覺

**spread 高（曲線倒掛）**：
- 市場預期經濟放緩/衰退
- 成長股（高 beta、利率敏感）受壓
- 防禦股（Healthcare）相對抗跌
- → 未來 QQQ 相對 XLV 弱

**spread 低（曲線正常/變陡）**：
- 市場預期經濟復甦
- 成長股彈性大，受益風險偏好
- 防禦股相對落後
- → 未來 QQQ 相對 XLV 強

---

## 7. 限制與風險

### 7.1 統計限制

- **R² 偏低**：spread 僅解釋 ~10% 變異，其他因子更重要
- **樣本量**：過去 15-20 年僅約 2-3 次完整週期
- **數據挖掘**：掃描多個 lead 可能過度擬合

### 7.2 結構性風險

- **Fed 政策框架變化**：QE、YCC 可能改變曲線訊號意義
- **零利率下界**：曲線在零附近的訊號可能失效
- **財政主導**：大規模財政政策可能蓋過貨幣訊號

### 7.3 使用建議

1. **作為參考而非決定因子**：搭配其他指標
2. **關注區間而非點估計**：不確定性高
3. **定期驗證**：確認關係仍成立
4. **情境分析**：考慮關係失效的可能

---

## 8. 公式彙總

| 計算項目             | 公式                                         |
|----------------------|----------------------------------------------|
| 殖利率利差           | spread = DGS2 - DGS10                        |
| 相對比率             | ratio = QQQ / XLV                            |
| 未來相對報酬         | y = log(ratio_{t+H} / ratio_t)               |
| 迴歸預測             | ŷ = α + β × spread                           |
| 區間估計             | [ŷ + q_10(ε), ŷ + q_90(ε)]                   |
| 轉換為百分比         | pct = exp(y) - 1                             |
