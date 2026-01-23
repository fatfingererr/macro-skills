本 skill 回答三個核心問題：

| 問題                          | 方法                               | 輸出                     |
|-------------------------------|------------------------------------|--------------------------|
| MOVE 是否領先其他風險指標？   | 交叉相關 (Cross-Correlation)       | 最佳 lag 天數 + 相關係數 |
| MOVE 對利率事件是否恐慌？     | 事件窗檢定 (Event Window)          | 平均反應 + Z 分數        |
| MOVE 下行時其他指標是否同步？ | 方向一致性 (Directional Alignment) | 同向比例                 |

---

## 2. 數據預處理

### 2.1 對齊到交易日

所有時間序列對齊到 Business Day 索引，缺值使用前向填充（forward fill）：

```python
df = df.sort_index().asfreq("B").ffill()
```

**記錄缺值比例**：若缺值比例超過 5%，應在輸出中標註。

### 2.2 平滑處理

為降低短期噪音對 lead/lag 判斷的干擾，使用移動平均平滑：

```python
if smooth_window > 0:
    df_smooth = df.rolling(smooth_window).mean()
else:
    df_smooth = df.copy()
```

**建議設定**：`smooth_window = 5`（一週）

### 2.3 Z 分數標準化

將不同尺度的指標轉換為可比較的單位：

$$z_t = \frac{x_t - \mu_{t,w}}{\sigma_{t,w}}$$

其中：
- $x_t$：當期數值
- $\mu_{t,w}$：過去 $w$ 期的滾動平均
- $\sigma_{t,w}$：過去 $w$ 期的滾動標準差

```python
def rolling_zscore(s: pd.Series, window: int) -> pd.Series:
    mu = s.rolling(window).mean()
    sd = s.rolling(window).std()
    return (s - mu) / sd
```

**建議設定**：`zscore_window = 60`（約 3 個月）

**解讀**：
- Z > +2：極端高位（歷史 97.7% 分位以上）
- Z ∈ [-1, +1]：正常區間
- Z < -2：極端低位

---

## 3. Lead/Lag 分析：交叉相關

### 3.1 原理

交叉相關（Cross-Correlation）衡量兩序列在不同時間位移下的相關性：

$$\text{CrossCorr}(X, Y, k) = \text{Corr}(X_{t+k}, Y_t)$$

- **k > 0**：X 領先 Y（X 的變化先發生）
- **k < 0**：X 落後 Y（Y 的變化先發生）
- **k = 0**：同步

### 3.2 實作

```python
def crosscorr_leadlag(x: pd.Series, y: pd.Series, max_lag: int) -> tuple:
    """
    計算 x 對 y 的交叉相關，找出最佳 lag

    返回：(best_lag, best_corr)
    - best_lag > 0：x 領先 y
    - best_lag < 0：x 落後 y
    """
    best_lag, best_corr = 0, -np.inf

    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            # x 領先：比較 x[:-lag] 與 y[lag:]
            corr = x.shift(lag).corr(y)
        else:
            # x 落後：比較 x[-lag:] 與 y[:lag]
            corr = x.shift(lag).corr(y)

        if corr is not None and not np.isnan(corr) and corr > best_corr:
            best_corr, best_lag = corr, lag

    return best_lag, best_corr
```

### 3.3 解讀

| 結果                                | 意義                                     |
|-------------------------------------|------------------------------------------|
| `MOVE_vs_VIX: lag=+6, corr=0.72`    | MOVE 變化領先 VIX 約 6 天，相關係數 0.72 |
| `MOVE_vs_CREDIT: lag=+4, corr=0.61` | MOVE 變化領先信用利差約 4 天             |
| `lag ≈ 0, corr > 0.8`               | 兩者同步移動                             |
| `lag < 0`                           | MOVE 反而落後（需檢查數據品質）          |

### 3.4 注意事項

1. **相關不等於因果**：lead/lag 只表示統計上的時序關係
2. **穩定性**：不同時期的 lead/lag 可能不同，建議計算滾動 lead/lag
3. **顯著性**：可用 bootstrap 或 Fisher z-transform 檢定相關係數顯著性

---

## 4. 事件窗檢定：是否被嚇到

### 4.1 原理

檢驗「當利率事件發生時，MOVE 是否恐慌」：

1. **定義事件**：JGB 殖利率在 $k$ 天內變動超過門檻
2. **計算反應**：事件窗內 MOVE 的變化
3. **比較歷史**：反應是否低於歷史分布中位數

### 4.2 事件定義

$$\text{Shock}_t = \mathbb{1}\left[ |Y_t - Y_{t-k}| \geq \tau \right]$$

其中：
- $Y_t$：JGB 10Y 殖利率
- $k$：事件窗天數（預設 5）
- $\tau$：門檻（預設 15 bps）

```python
def identify_shock_events(jgb: pd.Series, window: int, threshold_bps: float) -> pd.Series:
    """識別 JGB 衝擊事件"""
    # 計算 k 日變化（bps）
    change_bps = (jgb - jgb.shift(window)) * 100
    # 標記衝擊
    shock = change_bps.abs() >= threshold_bps
    return shock
```

### 4.3 MOVE 反應計算

$$\text{MOVE\_reaction}_t = \text{MOVE}_t - \text{MOVE}_{t-k}$$

```python
def compute_move_reaction(move: pd.Series, shock: pd.Series, window: int) -> dict:
    """計算 MOVE 對衝擊事件的反應"""
    move_change = move - move.shift(window)
    reactions = move_change[shock].dropna()

    return {
        "shock_count": int(shock.sum()),
        "mean_reaction": float(reactions.mean()) if len(reactions) else np.nan,
        "median_reaction": float(reactions.median()) if len(reactions) else np.nan,
        "reactions": reactions.tolist()
    }
```

### 4.4 「不恐慌」判定

| 條件                  | 判定                     |
|-----------------------|--------------------------|
| 平均反應 < 歷史中位數 | Not spooked              |
| 平均反應 ≥ 歷史中位數 | Spooked                  |
| 當前 MOVE Z 分數 < 0  | 目前偏低（利率市場平靜） |
| 當前 MOVE Z 分數 > +1 | 目前偏高（利率市場緊張） |

---

## 5. 方向一致性

### 5.1 原理

檢驗「當 MOVE 下行時，其他風險指標是否也下行」：

$$\text{Alignment}_{X,Y} = \frac{\sum \mathbb{1}[\Delta X_t < 0 \land \Delta Y_t < 0]}{\sum \mathbb{1}[\Delta X_t < 0]}$$

### 5.2 實作

```python
def compute_direction_alignment(df: pd.DataFrame) -> dict:
    """計算方向一致性"""
    d = df.diff()

    move_down = d["MOVE"] < 0
    vix_down = d["VIX"] < 0
    credit_down = d["CREDIT"] < 0

    align_vix = float((move_down & vix_down).sum() / move_down.sum())
    align_credit = float((move_down & credit_down).sum() / move_down.sum())

    return {
        "MOVE_down_and_VIX_down_ratio": align_vix,
        "MOVE_down_and_CREDIT_down_ratio": align_credit
    }
```

### 5.3 解讀

| 比例      | 意義                                      |
|-----------|-------------------------------------------|
| > 0.6     | 高度同向（符合「MOVE 帶動其他指標下行」） |
| 0.4 - 0.6 | 中等同向                                  |
| < 0.4     | 低同向（可能存在結構性差異）              |

---

## 6. 綜合判定邏輯

### 6.1 結論生成

```python
def generate_headline(leadlag: dict, spooked: dict, alignment: dict) -> str:
    """生成一句話結論"""
    parts = []

    # 恐慌檢定
    if spooked["mean_reaction"] < 1.0:
        parts.append("MOVE not spooked by JGB yield moves")
    else:
        parts.append("MOVE appears spooked by JGB yield moves")

    # 領先判定
    move_vs_vix = leadlag["MOVE_vs_VIX"]["best_lag_days"]
    move_vs_credit = leadlag["MOVE_vs_CREDIT"]["best_lag_days"]

    if move_vs_vix > 0 and move_vs_credit > 0:
        parts.append("and appears to lead VIX/Credit lower")
    elif move_vs_vix < 0 or move_vs_credit < 0:
        parts.append("but may lag VIX/Credit")
    else:
        parts.append("and moves in sync with VIX/Credit")

    return " ".join(parts) + "."
```

### 6.2 信心水準

| 信心   | 條件                                       |
|--------|--------------------------------------------|
| HIGH   | lead/lag 相關 > 0.7 且方向一致性 > 0.6     |
| MEDIUM | lead/lag 相關 0.5-0.7 或方向一致性 0.4-0.6 |
| LOW    | lead/lag 相關 < 0.5 或數據不足             |

---

## 7. 數學公式總結

### Z 分數
$$z_t = \frac{x_t - \bar{x}_{t-w:t}}{\sigma_{t-w:t}}$$

### 交叉相關
$$\rho_{XY}(k) = \frac{\text{Cov}(X_{t+k}, Y_t)}{\sigma_X \sigma_Y}$$

### 事件窗反應
$$R_t = \text{MOVE}_t - \text{MOVE}_{t-k} \quad \text{when} \quad |\Delta\text{JGB}_{t-k:t}| \geq \tau$$

### 方向一致性
$$\text{Align}_{XY} = P(\Delta Y < 0 | \Delta X < 0)$$

---

## 8. 參考文獻

1. **Lead-Lag Analysis**: Hamilton, J.D. (1994). Time Series Analysis
2. **Cross-Correlation**: Brockwell, P.J. & Davis, R.A. (2016). Introduction to Time Series and Forecasting
3. **Event Studies**: MacKinlay, A.C. (1997). Event Studies in Economics and Finance

---

## 9. 程式碼：完整分析函數

```python
import pandas as pd
import numpy as np

def analyze_rates_vol_leadlag(
    df: pd.DataFrame,
    smooth_window: int = 5,
    zscore_window: int = 60,
    lead_lag_max_days: int = 20,
    shock_window_days: int = 5,
    shock_threshold_bps: float = 15.0
) -> dict:
    """
    完整的利率波動率領先落後分析

    Parameters:
    -----------
    df : DataFrame with columns ["MOVE", "VIX", "CREDIT", "JGB10Y"]

    Returns:
    --------
    dict with leadlag, spooked_check, direction_alignment, headline
    """

    # 1. 對齊
    df = df.sort_index().asfreq("B").ffill()

    # 2. 平滑
    if smooth_window > 0:
        df_s = df.rolling(smooth_window).mean()
    else:
        df_s = df.copy()

    # 3. Z 分數
    z = df_s.apply(lambda c: rolling_zscore(c, zscore_window))

    # 4. Lead/Lag
    lag_vix, corr_vix = crosscorr_leadlag(df_s["MOVE"], df_s["VIX"], lead_lag_max_days)
    lag_cr, corr_cr = crosscorr_leadlag(df_s["MOVE"], df_s["CREDIT"], lead_lag_max_days)

    leadlag = {
        "MOVE_vs_VIX": {"best_lag_days": int(lag_vix), "corr": round(corr_vix, 3)},
        "MOVE_vs_CREDIT": {"best_lag_days": int(lag_cr), "corr": round(corr_cr, 3)}
    }

    # 5. 事件窗檢定
    jgb_change_bps = (df_s["JGB10Y"] - df_s["JGB10Y"].shift(shock_window_days)) * 100
    shock = jgb_change_bps.abs() >= shock_threshold_bps

    move_react = df_s["MOVE"] - df_s["MOVE"].shift(shock_window_days)
    reactions = move_react[shock].dropna()

    spooked_check = {
        "shock_definition": f"abs(JGB10Y change over {shock_window_days}d) >= {shock_threshold_bps}bp",
        "shock_count": int(shock.sum()),
        "mean_MOVE_reaction_on_shocks": round(float(reactions.mean()), 2) if len(reactions) else None,
        "MOVE_zscore_now": round(float(z["MOVE"].iloc[-1]), 2)
    }

    # 6. 方向一致性
    d = df_s.diff()
    move_down = d["MOVE"] < 0

    alignment = {
        "MOVE_down_and_VIX_down_ratio": round(float((move_down & (d["VIX"] < 0)).sum() / move_down.sum()), 2),
        "MOVE_down_and_CREDIT_down_ratio": round(float((move_down & (d["CREDIT"] < 0)).sum() / move_down.sum()), 2)
    }

    # 7. 生成結論
    headline = generate_headline(leadlag, spooked_check, alignment)

    return {
        "status": "ok",
        "headline": headline,
        "leadlag": leadlag,
        "spooked_check": spooked_check,
        "direction_alignment": alignment
    }
```
