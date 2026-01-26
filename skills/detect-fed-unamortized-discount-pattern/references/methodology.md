### 為什麼需要形狀比對？

一般常見的「圖形類比」論述：
- ❌「這條線複製 COVID，60 天內黑天鵝」
- 問題：純粹肉眼判斷，無法量化，無法反駁

**本技能的解決方案**：
- 把「肉眼類比」轉成可量化的「形狀比對」
- 使用多種方法交叉驗證，避免單一指標誤判
- 輸出可被支持或反駁的數據

### 形狀比對 ≠ 事件預測

**重要認知**：
- 「形狀相似」只說明「當前走勢與歷史片段形狀類似」
- 不說明「歷史事件會再次發生」
- 需要搭配壓力驗證才能升級風險判斷

---

## 資料預處理

### 頻率對齊

FRED 週資料為主，所有序列對齊至週頻：

```python
def resample_align(series: pd.Series, freq: str = "W") -> pd.Series:
    """
    將序列重採樣至指定頻率

    Parameters
    ----------
    series : pd.Series
        原始時間序列（日頻或週頻）
    freq : str
        目標頻率（"W" 週頻、"D" 日頻）

    Returns
    -------
    pd.Series
        重採樣後的序列
    """
    if freq == "W":
        # 取週末值（或該週最後一個有效值）
        return series.resample("W-FRI").last().dropna()
    return series
```

### 正規化方法

去除量級差異，只保留「形狀」：

#### Z-Score 正規化
```python
def zscore_normalize(series: pd.Series) -> pd.Series:
    """
    Z-Score 正規化：均值=0，標準差=1

    適用：形狀比較，對量級不敏感
    """
    return (series - series.mean()) / series.std()
```

#### 百分比變化正規化
```python
def pct_change_normalize(series: pd.Series) -> pd.Series:
    """
    百分比變化正規化

    適用：強調加速/減速，對趨勢敏感
    """
    return series.pct_change().fillna(0)
```

#### Min-Max 正規化
```python
def minmax_normalize(series: pd.Series) -> pd.Series:
    """
    Min-Max 正規化：範圍縮放至 [0, 1]

    適用：需要統一範圍時
    """
    return (series - series.min()) / (series.max() - series.min())
```

**建議**：使用 Z-Score 作為主要方法，pct_change 作為輔助驗證。

---

## 形狀相似度計算

### 方法 1: 皮爾遜相關係數 (Correlation)

```python
def pearson_correlation(series_a: np.ndarray, series_b: np.ndarray) -> float:
    """
    計算兩個序列的皮爾遜相關係數

    Parameters
    ----------
    series_a, series_b : np.ndarray
        正規化後的時間序列（長度需相同）

    Returns
    -------
    float
        相關係數，範圍 [-1, 1]
    """
    return np.corrcoef(series_a, series_b)[0, 1]
```

**解讀**：
| 相關係數  | 解讀                       |
|-----------|----------------------------|
| > 0.8     | 高度正相關（形狀非常相似） |
| 0.5 ~ 0.8 | 中度正相關（形狀相似）     |
| 0.3 ~ 0.5 | 弱正相關（部分相似）       |
| < 0.3     | 無顯著相關（形狀不相似）   |

**優點**：
- 計算簡單快速
- 直觀易懂

**缺點**：
- 假設線性關係
- 對時間偏移敏感（快一點/慢一點會降低相關）

### 方法 2: 動態時間校正 (DTW)

```python
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

def dtw_distance(series_a: np.ndarray, series_b: np.ndarray) -> float:
    """
    計算兩個序列的 DTW 距離

    Parameters
    ----------
    series_a, series_b : np.ndarray
        正規化後的時間序列（長度可不同）

    Returns
    -------
    float
        DTW 距離，範圍 [0, ∞)，越小越相似
    """
    distance, path = fastdtw(series_a, series_b, dist=euclidean)
    # 正規化：除以序列長度
    return distance / max(len(series_a), len(series_b))
```

**解讀**：
| DTW 距離（正規化後） | 解讀     |
|----------------------|----------|
| < 0.3                | 高度相似 |
| 0.3 ~ 0.8            | 中度相似 |
| 0.8 ~ 1.5            | 弱相似   |
| > 1.5                | 不相似   |

**優點**：
- 允許時間軸「拉伸/壓縮」
- 捕捉「快一點/慢一點但形狀相似」的情況

**缺點**：
- 計算量較大
- 對參數敏感
- 可能過度對齊（把不相似的強行對齊）

### 方法 3: 形狀特徵相似度

提取結構化特徵，計算特徵向量的相似度：

```python
def extract_shape_features(series: np.ndarray) -> dict:
    """
    提取形狀特徵

    Returns
    -------
    dict
        特徵字典
    """
    n = len(series)
    x = np.arange(n)

    # 1. 趨勢斜率（線性回歸）
    slope, intercept = np.polyfit(x, series, 1)

    # 2. 波動度（標準差）
    volatility = np.std(series)

    # 3. 偏度（形狀不對稱性）
    from scipy.stats import skew
    skewness = skew(series)

    # 4. 峰谷數量
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(series)
    troughs, _ = find_peaks(-series)
    n_peaks = len(peaks)
    n_troughs = len(troughs)

    # 5. 首尾變化率
    start_to_end = (series[-1] - series[0]) / (abs(series[0]) + 1e-8)

    return {
        "slope": slope,
        "volatility": volatility,
        "skewness": skewness,
        "n_peaks": n_peaks,
        "n_troughs": n_troughs,
        "start_to_end": start_to_end
    }


def feature_similarity(feat_a: dict, feat_b: dict) -> float:
    """
    計算特徵向量的餘弦相似度
    """
    keys = feat_a.keys()
    vec_a = np.array([feat_a[k] for k in keys])
    vec_b = np.array([feat_b[k] for k in keys])

    # 正規化
    vec_a = vec_a / (np.linalg.norm(vec_a) + 1e-8)
    vec_b = vec_b / (np.linalg.norm(vec_b) + 1e-8)

    # 餘弦相似度
    return float(np.dot(vec_a, vec_b))
```

**優點**：
- 捕捉結構性特徵（趨勢、拐點）
- 對局部噪音較不敏感

**缺點**：
- 特徵選擇需要領域知識
- 可能遺漏某些形狀特性

### 綜合相似度分數

```python
def combine_similarity(
    corr: float,
    dtw_dist: float,
    feature_sim: float,
    weights: tuple = (0.4, 0.3, 0.3)
) -> float:
    """
    合成綜合相似度分數

    Parameters
    ----------
    corr : float
        相關係數 [-1, 1]
    dtw_dist : float
        DTW 距離（正規化後）[0, ∞)
    feature_sim : float
        特徵相似度 [0, 1]
    weights : tuple
        權重 (corr, dtw, feature)

    Returns
    -------
    float
        綜合相似度分數 [0, 1]
    """
    # 轉換至 [0, 1] 範圍
    corr_score = (corr + 1) / 2  # [-1, 1] -> [0, 1]
    dtw_score = max(0, 1 - dtw_dist / 2)  # 假設 dtw > 2 為不相似
    feat_score = max(0, feature_sim)  # 已經在 [0, 1]

    w_corr, w_dtw, w_feat = weights
    return w_corr * corr_score + w_dtw * dtw_score + w_feat * feat_score
```

---

## 交叉驗證邏輯

### 為什麼需要交叉驗證？

**WUDSHO 變動的可能成因**：
1. **利率環境變化**（最常見）
2. **持有債券久期結構調整**
3. **會計攤銷時程**
4. **真正的金融壓力**

只有第 4 種需要提高警覺，但形狀比對無法區分。

**解決方案**：用其他壓力指標交叉驗證。

### 壓力驗證計算

```python
def calculate_stress_score(
    indicator_data: pd.Series,
    indicator_config: dict,
    lookback_days: int = 252
) -> dict:
    """
    計算單一指標的壓力分數

    Parameters
    ----------
    indicator_data : pd.Series
        指標資料
    indicator_config : dict
        指標配置（包含 stress_threshold）
    lookback_days : int
        歷史回望期（計算 z-score 用）

    Returns
    -------
    dict
        包含 z-score、signal、score
    """
    recent = indicator_data.iloc[-1]
    historical = indicator_data.iloc[-lookback_days:-1]

    mean = historical.mean()
    std = historical.std()
    z = (recent - mean) / (std + 1e-8)

    threshold = indicator_config.get("stress_threshold", 1.5)

    # 信用利差、波動率：上升為壓力
    # 殖利率曲線：倒掛（負值）為壓力
    if indicator_config.get("name") == "yield_curve":
        signal = "stress" if z < -threshold else "neutral"
        score = max(0, -z / threshold) if z < 0 else 0
    else:
        signal = "stress" if z > threshold else "neutral"
        score = max(0, z / threshold) if z > 0 else 0

    return {
        "z": float(z),
        "signal": signal,
        "score": min(1.0, score)
    }
```

### 合成壓力分數

```python
def aggregate_stress_scores(
    indicator_results: list,
    indicator_configs: list
) -> dict:
    """
    合成所有指標的壓力分數

    Returns
    -------
    dict
        包含 score（加權平均）和 details
    """
    total_weight = 0
    weighted_score = 0
    details = []

    for result, config in zip(indicator_results, indicator_configs):
        weight = config.get("weight", 1.0)
        weighted_score += weight * result["score"]
        total_weight += weight
        details.append({
            "name": config["name"],
            "signal": result["signal"],
            "z": result["z"]
        })

    return {
        "score": weighted_score / total_weight if total_weight > 0 else 0,
        "details": details
    }
```

---

## 合成風險分數

```python
def calculate_composite_risk(
    pattern_score: float,
    stress_score: float,
    pattern_weight: float = 0.6,
    stress_weight: float = 0.4
) -> float:
    """
    合成最終風險分數

    Parameters
    ----------
    pattern_score : float
        形狀相似度分數 [0, 1]
    stress_score : float
        壓力驗證分數 [0, 1]
    pattern_weight : float
        形狀權重
    stress_weight : float
        壓力權重

    Returns
    -------
    float
        合成風險分數 [0, 1]
    """
    return pattern_weight * pattern_score + stress_weight * stress_score
```

### 解讀框架

| 合成風險分數 | 解讀                             | 建議行動               |
|--------------|----------------------------------|------------------------|
| > 0.7        | 高風險：形狀相似且壓力驗證支持   | 提高警覺，考慮防禦配置 |
| 0.5 ~ 0.7    | 中高風險：形狀相似，壓力開始出現 | 持續觀察，準備應對方案 |
| 0.3 ~ 0.5    | 中風險：形狀相似但壓力中性       | 可能是利率/會計效果    |
| < 0.3        | 低風險：形狀不相似或壓力反對     | 圖形類比不成立         |

---

## 方法論限制

1. **歷史不代表未來**：形狀相似不代表後續發展相同
2. **樣本有限**：極端事件只有 3-4 次，統計推論受限
3. **參數敏感**：DTW 和特徵提取對參數敏感
4. **時效性**：FRED 週資料有 T+1 ~ T+3 延遲
5. **因果謬誤**：相關不等於因果

---

## 參考文獻

- Berndt, D.J., & Clifford, J. (1994). "Using Dynamic Time Warping to Find Patterns in Time Series"
- Ratanamahatana, C.A., & Keogh, E. (2004). "Making Time-series Classification More Accurate Using Learned Constraints"
- Fed H.4.1 Release Documentation
