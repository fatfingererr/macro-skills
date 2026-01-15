# Zeberg-Salomon 方法論 (Methodology)

## 模型概述

Zeberg-Salomon 模型是一個**兩態景氣輪動系統**，基於以下核心假設：

1. **景氣循環可預測**：領先指標會比實體經濟提前 6-12 個月轉折
2. **兩態簡化**：市場可簡化為 Risk-On（股票）與 Risk-Off（長債）兩種狀態
3. **漸進惡化**：衰退不會突然發生，而是「先撞冰山（領先轉弱）→ 再下沉（同時確認）」

## 參考來源

- **Zeberg Letter**: https://swissblock.net/products/reports/zeberg-letter
- **@SystematicPeter**: https://x.com/SystematicPeter/status/2011460563096760388

## 核心概念

### 1. 領先指標 vs 同時指標

| 類型 | 經濟意義 | 代表序列 | 作用 |
|------|----------|----------|------|
| **Leading** | 預測未來景氣 | 殖利率曲線、新訂單、房市 | 預警 |
| **Coincident** | 反映當前景氣 | 就業、工業生產、實質收入 | 確認 |

**為什麼要分開**：
- 領先指標可能「假警報」（曲線倒掛但未衰退）
- 同時指標確認後才行動，可降低錯誤切換
- 但也不能只看同時，那樣會太滯後

### 2. 冰山事件 (Iceberg Event)

**定義**：LeadingIndex 跌破 `iceberg_threshold`

**比喻**：鐵達尼號撞上冰山，船體已受損，但乘客尚未感知。

**訊號特徵**：
- 殖利率曲線倒掛或壓縮
- 新訂單/房市許可轉負
- 消費者信心開始下滑
- 但就業、生產仍維持

**建議反應**：
- 提高警戒
- 若連續確認 + 斜率為負 + 市場亢奮 → 考慮 Risk-Off

### 3. 下沉事件 (Sinking Event)

**定義**：CoincidentIndex 跌破 `sinking_threshold`

**比喻**：船開始下沉，所有人都感受到了。

**訊號特徵**：
- 就業開始惡化
- 工業生產收縮
- 實質收入下滑
- 零售銷售轉弱

**建議反應**：
- 此時應已在 Risk-Off
- 若尚未切換，需立即行動
- 但注意：此時切換可能已較晚

### 4. 復甦訊號 (Recovery Signal)

**定義**：LeadingIndex 回升超過 `iceberg_threshold + hysteresis`

**訊號特徵**：
- 殖利率曲線正常化
- 新訂單回升
- 消費者信心觸底回升
- 房市活動恢復

**建議反應**：
- 連續確認後 → Risk-On

## 合成指標計算

### Step 1: 數據轉換 (Transform)

將各原始序列轉換為可比較的形式：

| 轉換 | 公式 | 適用 |
|------|------|------|
| level | 原值 | 殖利率曲線、情緒指標 |
| yoy | (x_t - x_{t-12}) / x_{t-12} | 數量型指標 |
| mom | (x_t - x_{t-1}) / x_{t-1} | 月變化 |
| diff | x_t - x_{t-1} | 絕對變化 |
| logdiff | ln(x_t) - ln(x_{t-1}) | 對數報酬 |

### Step 2: 方向統一 (Direction)

確保「上升 = 景氣好」：

```python
x = direction * x
# direction = +1: 上升為好（多數指標）
# direction = -1: 下降為好（如失業率）
```

### Step 3: 標準化 (Standardization)

Rolling z-score 將不同量綱統一：

```python
def rolling_zscore(x, window):
    mean = x.rolling(window).mean()
    std = x.rolling(window).std()
    return (x - mean) / std
```

**建議 window**：120 期（月頻 = 10 年）

### Step 4: 平滑 (Smoothing)

EMA 降低雜訊：

```python
def ema(x, span):
    return x.ewm(span=span, adjust=False).mean()
```

**建議 span**：3-6 期（月頻）

### Step 5: 加權合成 (Weighted Sum)

```python
def build_index(series_defs, data, z_win, smooth_win):
    z_list = []
    for sdef in series_defs:
        x = transform(data[sdef["id"]], sdef["transform"])
        x = sdef["direction"] * x
        z = rolling_zscore(x, z_win)
        z = ema(z, smooth_win)
        z_list.append(sdef["weight"] * z)
    return sum(z_list)
```

## 兩態切換邏輯

### 狀態定義

```
RISK_ON:  持有 equity_proxy (SPY)
RISK_OFF: 持有 bond_proxy (TLT)
```

### RISK_ON → RISK_OFF 條件

```python
cond_off = (
    iceberg.loc[t] and           # A: 冰山事件發生
    (dL < 0) and                  # B: 領先指標下降
    eup.loc[t]                    # C: 亢奮濾鏡（可選）
)

if cond_off 連續 confirm_periods 期:
    action = "EXIT_EQUITY_ENTER_LONG_BOND"
    state = "RISK_OFF"
```

### RISK_OFF → RISK_ON 條件

```python
cond_on = (
    (L.loc[t] > iceberg_threshold + hysteresis) and  # A: 領先回升超過門檻+間距
    (dL > 0) and                                      # B: 領先指標上升
    doubt.loc[t]                                      # C: 懷疑濾鏡（可選）
)

if cond_on 連續 confirm_periods 期:
    action = "EXIT_LONG_BOND_ENTER_EQUITY"
    state = "RISK_ON"
```

### Hysteresis 的作用

防止在門檻邊界來回切換：

```
iceberg_threshold = -0.3
hysteresis = 0.15

Risk-Off 觸發：L < -0.3
Risk-On 恢復：L > -0.3 + 0.15 = -0.15
```

## 濾鏡系統（可選）

### Euphoria Filters（亢奮濾鏡）

當市場處於亢奮狀態時，更容易觸發 Risk-Off：

```python
euphoria_filters = [
    # 信用利差低且開始上升
    {"type": "credit_spread_reversal", "series_id": "BAA10Y", "z_below": -1.0, "turn_up": True},
    # VIX 低且開始上升
    {"type": "vix_turn_up", "ticker": "VIXCLS", "level_below": 15, "turn_up": True}
]
```

**邏輯**：「大家都很樂觀，但領先指標已轉弱」→ 危險訊號

### Recovery Doubt Filters（復甦懷疑濾鏡）

當市場仍懷疑復甦時，更容易觸發 Risk-On：

```python
recovery_doubt_filters = [
    # 領先指標動量為正
    {"type": "leading_momentum", "above": 0}
]
```

**邏輯**：「大家還在懷疑，但領先指標已回升」→ 進場機會

## 回測假設

### 執行時點 (Rebalance On)

| 選項 | 說明 | 保守程度 |
|------|------|----------|
| signal_close | 訊號當日收盤執行 | 最不保守 |
| next_open | 訊號次日開盤執行 | 中等 |
| next_month_open | 訊號次月開盤執行 | 最保守（建議） |

### 交易成本

```python
transaction_cost_bps = 5   # 單邊 5 bps
slippage_bps = 0           # 滑價（可調整）
```

### 績效指標

| 指標 | 計算方式 |
|------|----------|
| CAGR | (終值/初值)^(1/年數) - 1 |
| Max Drawdown | max(1 - 價值/歷史高點) |
| Sharpe | (年化報酬 - 無風險利率) / 年化波動 |
| Turnovers | 切換次數 |

## 模型限制

1. **近似性**：本模型使用公開數據近似 Zeberg 原版，可能有差異
2. **發布延遲**：宏觀數據有 1-2 個月延遲，實際訊號會滯後
3. **樣本內偏差**：參數調整可能導致過度擬合
4. **尾部風險**：模型無法預測黑天鵝事件
5. **交易執行**：回測假設可能過於理想化
