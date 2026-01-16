# 跨金屬領先滯後方法論

## 核心假說

**「鈀金領先、白銀跟隨」** 的短週期領先關係假說：

1. **市場敏感度差異**：鈀金市場較小、流動性較低，對宏觀變化反應更敏感
2. **工業屬性關聯**：兩者皆有工業需求成分，但週期敏感度不同
3. **資金流動順序**：大資金進出貴金屬板塊時，先影響小市場

將這個「觀察」轉化為**可回測、可監控、可自動告警**的規則。

---

## 領先滯後估計 (Lead-Lag Estimation)

### 交叉相關分析

使用 cross-correlation 找出兩個時間序列的最佳滯後：

```python
import numpy as np
from scipy import signal

def estimate_lead_lag(pd_ret: np.ndarray, ag_ret: np.ndarray, max_lag: int = 24):
    """
    估計鈀金對白銀的領先滯後。

    Args:
        pd_ret: 鈀金報酬序列
        ag_ret: 白銀報酬序列
        max_lag: 最大滯後 K 數

    Returns:
        best_lag: 最佳滯後（正值表示鈀金領先）
        best_corr: 對應的相關係數
    """
    # 計算交叉相關
    correlation = signal.correlate(ag_ret, pd_ret, mode='full')
    lags = signal.correlation_lags(len(ag_ret), len(pd_ret), mode='full')

    # 限制在 [-max_lag, max_lag] 範圍
    mask = (lags >= -max_lag) & (lags <= max_lag)
    correlation = correlation[mask]
    lags = lags[mask]

    # 找最大相關
    best_idx = np.argmax(np.abs(correlation))
    best_lag = lags[best_idx]
    best_corr = correlation[best_idx] / len(ag_ret)  # 正規化

    return best_lag, best_corr
```

### 解讀

| 結果          | 含義                       |
|---------------|----------------------------|
| `lag > 0`     | 鈀金領先白銀 `lag` 根 K 棒 |
| `lag < 0`     | 白銀領先鈀金               |
| `lag ≈ 0`     | 同步移動                   |
| `corr > 0.3`  | 有意義的領先關係           |
| `corr < 0.3`  | 領先關係弱或不穩定         |

---

## 拐點偵測三法

### 1. Pivot 法

**原理**：左右 N 根 K 棒內的局部極值

```python
def detect_pivots(prices: pd.Series, left: int = 3, right: int = 3):
    """
    使用 pivot 法偵測局部高低點。

    pivot_high[i] = max(prices[i-left:i+right+1]) == prices[i]
    pivot_low[i] = min(prices[i-left:i+right+1]) == prices[i]
    """
    turns = []
    for i in range(left, len(prices) - right):
        window = prices.iloc[i-left:i+right+1]
        if prices.iloc[i] == window.max():
            turns.append({'idx': i, 'type': 'top', 'price': prices.iloc[i]})
        elif prices.iloc[i] == window.min():
            turns.append({'idx': i, 'type': 'bottom', 'price': prices.iloc[i]})
    return turns
```

**適用場景**：結構明確的趨勢市場

**參數建議**：
- 1h 圖：`left=right=3~5`
- 4h 圖：`left=right=2~4`
- 1d 圖：`left=right=2~3`

### 2. Peaks 法

**原理**：使用 scipy 的 `find_peaks` + prominence 控制

```python
from scipy.signal import find_peaks

def detect_peaks(prices: pd.Series, prominence: float = 0.5, distance: int = 5):
    """
    使用 scipy find_peaks 偵測極值。

    prominence: 突出度門檻（%）
    distance: 最小間隔 K 數
    """
    # 標準化價格變化
    pct_change = prices.pct_change().fillna(0)

    # 找頂部
    tops, _ = find_peaks(prices.values, prominence=prominence * prices.std(), distance=distance)

    # 找底部（反轉找）
    bottoms, _ = find_peaks(-prices.values, prominence=prominence * prices.std(), distance=distance)

    turns = []
    for t in tops:
        turns.append({'idx': t, 'type': 'top', 'price': prices.iloc[t]})
    for b in bottoms:
        turns.append({'idx': b, 'type': 'bottom', 'price': prices.iloc[b]})

    return sorted(turns, key=lambda x: x['idx'])
```

**適用場景**：自動化密度控制，適合不同市場條件

**參數建議**：
- `prominence=0.3~0.7`：較小值產生更多拐點
- `distance=5~15`：最小間隔 K 數

### 3. Slope Change 法

**原理**：趨勢斜率由正轉負或反之

```python
def detect_slope_changes(prices: pd.Series, window: int = 10, threshold: float = 0.0):
    """
    偵測趨勢斜率的方向變化。

    使用滾動線性迴歸的斜率。
    """
    from scipy import stats

    def rolling_slope(s):
        x = np.arange(len(s))
        slope, _, _, _, _ = stats.linregress(x, s)
        return slope

    slopes = prices.rolling(window).apply(rolling_slope, raw=False)

    # 找斜率符號變化點
    sign_change = (slopes.shift(1) * slopes) < 0

    turns = []
    for i in np.where(sign_change)[0]:
        if slopes.iloc[i] < 0 and slopes.iloc[i-1] > 0:
            turns.append({'idx': i, 'type': 'top', 'price': prices.iloc[i]})
        elif slopes.iloc[i] > 0 and slopes.iloc[i-1] < 0:
            turns.append({'idx': i, 'type': 'bottom', 'price': prices.iloc[i]})

    return turns
```

**適用場景**：平滑趨勢追蹤，減少噪音

**參數建議**：
- `window=10~20`：較長窗口更平滑
- `threshold=0`：可設小正值過濾微弱變化

---

## 跨金屬確認邏輯

### 確認定義

銀的拐點 `ag_turn` 被「確認」當且僅當：

1. 在確認窗口 `[ag_turn.ts - window, ag_turn.ts + window]` 內
2. 存在鈀金同向拐點 `pd_turn`（同為 top 或同為 bottom）

```python
def check_confirmation(ag_turn, pd_turns, window_bars: int = 6):
    """
    檢查銀拐點是否被鈀金確認。

    Args:
        ag_turn: 銀的拐點 {'idx': int, 'type': str}
        pd_turns: 鈀金拐點列表
        window_bars: 確認窗口 K 數

    Returns:
        confirmed: bool
        confirmation_lag: int or None（正值表示鈀金先動）
    """
    ag_idx = ag_turn['idx']
    ag_type = ag_turn['type']

    for pd_turn in pd_turns:
        if pd_turn['type'] != ag_type:
            continue

        lag = ag_idx - pd_turn['idx']  # 正值 = 鈀金先動
        if abs(lag) <= window_bars:
            return True, lag

    return False, None
```

### 確認滯後的含義

| confirmation_lag | 含義                   |
|------------------|------------------------|
| 正值（如 +3）    | 鈀金先於銀 3 根 K 出現拐點 |
| 負值（如 -2）    | 銀先於鈀金 2 根 K 出現拐點 |
| 0                | 同時出現               |

---

## 參與度判定

除了拐點確認，還需判斷鈀金是否「積極參與」銀的走勢。

### 1. 報酬相關 (returns_corr)

```python
def check_participation_corr(df, ag_turn_idx, lookback: int = 10, threshold: float = 0.5):
    """
    檢查拐點前後的報酬相關性。
    """
    start_idx = max(0, ag_turn_idx - lookback)
    end_idx = min(len(df), ag_turn_idx + lookback)

    ag_ret = df['ag_ret'].iloc[start_idx:end_idx]
    pd_ret = df['pd_ret'].iloc[start_idx:end_idx]

    corr = ag_ret.corr(pd_ret)
    return corr >= threshold, corr
```

### 2. 方向一致 (direction_agree)

```python
def check_participation_direction(df, ag_turn_idx, lookback: int = 10, threshold: float = 0.6):
    """
    檢查同向漲跌的比例。
    """
    start_idx = max(0, ag_turn_idx - lookback)
    end_idx = min(len(df), ag_turn_idx + lookback)

    ag_ret = df['ag_ret'].iloc[start_idx:end_idx]
    pd_ret = df['pd_ret'].iloc[start_idx:end_idx]

    same_direction = ((ag_ret > 0) & (pd_ret > 0)) | ((ag_ret < 0) & (pd_ret < 0))
    agree_rate = same_direction.sum() / len(ag_ret)

    return agree_rate >= threshold, agree_rate
```

### 3. 波動擴張 (vol_expansion)

```python
def check_participation_vol(df, ag_turn_idx, lookback: int = 10, threshold: float = 0.8):
    """
    檢查兩者波動是否同步擴張。
    """
    start_idx = max(0, ag_turn_idx - lookback)
    end_idx = min(len(df), ag_turn_idx + lookback)

    ag_vol = df['ag_ret'].iloc[start_idx:end_idx].std()
    pd_vol = df['pd_ret'].iloc[start_idx:end_idx].std()

    ratio = pd_vol / ag_vol if ag_vol > 0 else 0
    return ratio >= threshold, ratio
```

---

## 失敗走勢判定

### 規則 1：無確認則回撤 (no_confirm_then_revert)

```python
def check_failed_move_revert(df, ag_turn, confirmed: bool, revert_bars: int = 10):
    """
    未確認 + 銀在 N 根 K 內回撤過拐點價格。
    """
    if confirmed:
        return False

    turn_idx = ag_turn['idx']
    turn_price = ag_turn['price']
    turn_type = ag_turn['type']

    # 檢查後續 N 根 K
    for i in range(turn_idx + 1, min(len(df), turn_idx + revert_bars + 1)):
        if turn_type == 'top' and df['ag_close'].iloc[i] > turn_price:
            return True  # 頂部後創新高 = 失敗
        if turn_type == 'bottom' and df['ag_close'].iloc[i] < turn_price:
            return True  # 底部後創新低 = 失敗

    return False
```

### 規則 2：突破失敗 (no_confirm_then_break_fail)

```python
def check_failed_move_breakout(df, ag_turn, confirmed: bool, breakout_threshold: float = 0.02):
    """
    銀突破後，未確認且回落跌破突破點。
    """
    if confirmed:
        return False

    # 檢查是否有突破
    # ... 實作突破偵測邏輯
```

---

## 市場含義

### 確認事件

- **鈀金先行轉向**：宏觀/工業週期變化的早期信號
- **銀隨後確認**：更廣泛的貴金屬板塊共識
- **交易價值**：銀的動作有「後台支持」，可信度高

### 未確認事件

- **流動性噪音**：可能是大單進出、期權到期、保證金調整
- **孤立事件**：缺乏板塊共識
- **交易警示**：謹慎對待，不宜激進跟進

### 失敗走勢

- **假突破 / 假反轉**：價格運動缺乏持續性
- **回測統計**：未確認事件的失敗率顯著高於已確認
- **風控啟示**：可用於過濾交易訊號、調整倉位

---

## 參考資料

- Cross-correlation analysis in financial time series
- Lead-lag relationships in commodity markets
- Technical analysis: pivot points and trend detection
