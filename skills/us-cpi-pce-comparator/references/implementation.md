<overview>
此參考文件包含 CPI-PCE 比較分析的核心計算公式與 Python 實作範例。
</overview>

<dependencies>
```python
# Required libraries
import pandas as pd
import numpy as np
from fredapi import Fred
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
```
</dependencies>

<inflation_calculations>

<formula name="year_over_year">
**YoY 通膨率**

$$\pi_{yoy}(t) = \left(\frac{P_t}{P_{t-12}} - 1\right) \times 100$$

```python
def calc_yoy(series: pd.Series) -> pd.Series:
    """Calculate year-over-year inflation rate."""
    return series.pct_change(12) * 100
```
</formula>

<formula name="mom_saar">
**月增年化率 (MoM SAAR)**

$$\pi_{saar}(t) = \left[\left(1 + \frac{P_t - P_{t-1}}{P_{t-1}}\right)^{12} - 1\right] \times 100$$

```python
def calc_mom_saar(series: pd.Series) -> pd.Series:
    """Calculate month-over-month seasonally adjusted annual rate."""
    mom = series.pct_change(1)
    return ((1 + mom) ** 12 - 1) * 100
```
</formula>

<formula name="qoq_saar">
**季增年化率 (QoQ SAAR)**

$$\pi_{qsaar}(t) = \left[\left(1 + \frac{P_t - P_{t-3}}{P_{t-3}}\right)^{4} - 1\right] \times 100$$

```python
def calc_qoq_saar(series: pd.Series) -> pd.Series:
    """Calculate quarter-over-quarter seasonally adjusted annual rate."""
    qoq = series.pct_change(3)
    return ((1 + qoq) ** 4 - 1) * 100
```
</formula>

<unified_function>
```python
def calc_inflation(
    series: pd.Series,
    measure: Literal["yoy", "mom_saar", "qoq_saar"]
) -> pd.Series:
    """
    Calculate inflation rate based on specified measure.

    Args:
        series: Price index series
        measure: One of "yoy", "mom_saar", "qoq_saar"

    Returns:
        Inflation rate series (in percentage points)
    """
    if measure == "yoy":
        return series.pct_change(12) * 100
    elif measure == "mom_saar":
        mom = series.pct_change(1)
        return ((1 + mom) ** 12 - 1) * 100
    elif measure == "qoq_saar":
        qoq = series.pct_change(3)
        return ((1 + qoq) ** 4 - 1) * 100
    else:
        raise ValueError(f"Unsupported measure: {measure}")
```
</unified_function>

</inflation_calculations>

<weighted_inflation>

<formula name="pce_weighted">
**PCE 動態加權通膨**

$$\pi^{PCE}(t) = \sum_b w_b^{PCE}(t) \cdot \pi_b(t)$$

其中 $w_b^{PCE}(t)$ 是 bucket $b$ 在時間 $t$ 的 PCE 支出占比。
</formula>

<formula name="fixed_weighted">
**固定權重加權通膨（CPI-style proxy）**

$$\pi^{FIX}(t) = \sum_b w_b^{FIX} \cdot \pi_b(t)$$

其中 $w_b^{FIX}$ 是固定在某基準期的權重。
</formula>

<formula name="divergence">
**分歧計算**

$$\Delta_{bps}(t) = \left(\pi^{PCE}(t) - \pi^{FIX}(t)\right) \times 100$$
</formula>

<implementation>
```python
def calc_weighted_inflation(
    pi_buckets: Dict[str, pd.Series],
    weights: Dict[str, pd.Series],
    focus_buckets: List[str]
) -> pd.Series:
    """
    Calculate weighted inflation across buckets.

    Args:
        pi_buckets: Dict mapping bucket name to inflation series
        weights: Dict mapping bucket name to weight series
        focus_buckets: List of bucket names to include

    Returns:
        Weighted inflation series
    """
    result = pd.Series(0.0, index=pi_buckets[focus_buckets[0]].index)

    for bucket in focus_buckets:
        if bucket in pi_buckets and bucket in weights:
            # Align weights to inflation index
            w = weights[bucket].reindex(result.index, method='ffill')
            result += w * pi_buckets[bucket]

    return result
```
</implementation>

</weighted_inflation>

<weight_effect_proxy>

<formula name="weight_effect">
**權重效應近似**

$$\Delta_{weight}(t) = \sum_b \left(w_b^{PCE}(t) - w_b^{FIX}\right) \cdot \pi_b(t)$$

這量化了「因為 PCE 使用動態權重，而 CPI 使用固定權重」所造成的通膨差異。
</formula>

<implementation>
```python
def calc_weight_effect(
    pi_buckets: Dict[str, pd.Series],
    w_pce: Dict[str, pd.Series],
    w_fix: Dict[str, float],
    focus_buckets: List[str]
) -> pd.Series:
    """
    Calculate weight effect proxy.

    This measures how much of the CPI-PCE divergence
    is attributable to weight differences.
    """
    result = pd.Series(0.0, index=pi_buckets[focus_buckets[0]].index)

    for bucket in focus_buckets:
        w_pce_aligned = w_pce[bucket].reindex(result.index, method='ffill')
        delta_w = w_pce_aligned - w_fix[bucket]
        result += delta_w * pi_buckets[bucket]

    return result * 100  # Convert to bps
```
</implementation>

</weight_effect_proxy>

<volatility_analysis>

<formula name="rolling_volatility">
**滾動波動度**

$$\sigma_b(t) = \text{std}\left(\pi_b(t-n+1), \ldots, \pi_b(t)\right)$$

其中 $n$ 是視窗大小（月數）。
</formula>

<implementation>
```python
def calc_rolling_volatility(
    series: pd.Series,
    window: int = 24
) -> pd.Series:
    """
    Calculate rolling standard deviation of inflation.

    Args:
        series: Inflation rate series
        window: Rolling window in months

    Returns:
        Rolling volatility series
    """
    return series.rolling(window).std()


def identify_low_vol_high_weight_buckets(
    pi_buckets: Dict[str, pd.Series],
    weights: Dict[str, pd.Series],
    vol_window: int = 24,
    vol_quantile: float = 0.4
) -> List[str]:
    """
    Identify buckets with low volatility and high weight.

    These are the buckets that, if they re-accelerate,
    would push PCE higher even if CPI looks calm.
    """
    # Calculate latest volatility and weight for each bucket
    vol = {
        b: calc_rolling_volatility(pi_buckets[b], vol_window).iloc[-1]
        for b in pi_buckets
    }
    latest_w = {
        b: weights[b].iloc[-1]
        for b in weights
    }

    # Determine thresholds
    vol_threshold = np.quantile(list(vol.values()), vol_quantile)
    weight_median = np.median(list(latest_w.values()))

    # Filter: low vol AND high weight
    candidates = [
        b for b in pi_buckets
        if vol[b] <= vol_threshold and latest_w[b] > weight_median
    ]

    # Sort by (low vol, high weight)
    candidates.sort(key=lambda b: (vol[b], -latest_w[b]))

    return candidates
```
</implementation>

</volatility_analysis>

<baseline_adjustment>

<formula name="subtract_mean">
**減去基準期平均**

$$\pi_b^{adj}(t) = \pi_b(t) - \bar{\pi}_b(\text{baseline})$$

其中 $\bar{\pi}_b(\text{baseline})$ 是基準期內的平均通膨率。
</formula>

<formula name="subtract_end">
**減去基準期末值**

$$\pi_b^{adj}(t) = \pi_b(t) - \pi_b(t_{\text{end}})$$

其中 $t_{\text{end}}$ 是基準期的最後一天。
</formula>

<implementation>
```python
def apply_baseline_adjustment(
    series: pd.Series,
    baseline_start: str,
    baseline_end: str,
    mode: Literal["subtract_mean", "subtract_end"] = "subtract_mean"
) -> pd.Series:
    """
    Adjust inflation series relative to a baseline period.

    Args:
        series: Inflation series
        baseline_start: Start of baseline period (YYYY-MM-DD)
        baseline_end: End of baseline period (YYYY-MM-DD)
        mode: "subtract_mean" or "subtract_end"

    Returns:
        Adjusted inflation series
    """
    mask = (series.index >= baseline_start) & (series.index <= baseline_end)
    baseline_data = series[mask]

    if mode == "subtract_mean":
        baseline_level = baseline_data.mean()
    else:  # subtract_end
        baseline_level = baseline_data.iloc[-1]

    return series - baseline_level
```
</implementation>

</baseline_adjustment>

<contribution_analysis>

<formula name="weighted_contribution">
**加權通膨貢獻**

$$C_b(t) = w_b(t) \cdot \pi_b(t)$$

這表示 bucket $b$ 對總體通膨的貢獻（以百分點計）。
</formula>

<implementation>
```python
def calc_contributions(
    pi_buckets: Dict[str, pd.Series],
    weights: Dict[str, pd.Series],
    focus_buckets: List[str]
) -> Dict[str, float]:
    """
    Calculate weighted inflation contribution for each bucket.

    Returns the latest contribution value for each bucket.
    """
    contributions = {}

    for bucket in focus_buckets:
        if bucket in pi_buckets and bucket in weights:
            w = weights[bucket].iloc[-1]
            pi = pi_buckets[bucket].iloc[-1]
            contributions[bucket] = w * pi

    return contributions


def get_top_contributors(
    contributions: Dict[str, float],
    n: int = 5
) -> List[tuple]:
    """Get top N contributors by absolute contribution."""
    return sorted(
        contributions.items(),
        key=lambda kv: abs(kv[1]),
        reverse=True
    )[:n]
```
</implementation>

</contribution_analysis>

<signal_detection>

<implementation>
```python
def detect_upside_signals(
    pi_buckets: Dict[str, pd.Series],
    pi_adjusted: Dict[str, pd.Series],
    low_vol_high_weight: List[str],
    threshold_bps: float = 50
) -> List[dict]:
    """
    Detect PCE upside risk signals in low-vol high-weight buckets.

    Args:
        pi_buckets: Original inflation series
        pi_adjusted: Baseline-adjusted inflation series
        low_vol_high_weight: List of identified buckets
        threshold_bps: Meaningful upside threshold in bps

    Returns:
        List of signal dictionaries
    """
    signals = []

    for bucket in low_vol_high_weight:
        latest = pi_buckets[bucket].iloc[-1]
        prev_3m = pi_buckets[bucket].iloc[-4] if len(pi_buckets[bucket]) > 3 else None
        momentum_3m = latest - prev_3m if prev_3m else None

        # Check baseline deviation
        if bucket in pi_adjusted:
            deviation = pi_adjusted[bucket].iloc[-1]
            if deviation > threshold_bps / 100:
                signals.append({
                    'bucket': bucket,
                    'signal': 'upside',
                    'deviation_pct': deviation,
                    'deviation_bps': deviation * 100,
                    'momentum_3m': momentum_3m,
                    'latest_inflation': latest
                })
        elif momentum_3m and momentum_3m > 0:
            # Fallback: use momentum if no baseline
            signals.append({
                'bucket': bucket,
                'signal': 'accelerating',
                'momentum_3m': momentum_3m,
                'latest_inflation': latest
            })

    return signals
```
</implementation>

</signal_detection>

<full_analysis_class>

```python
class CPIPCEComparator:
    """
    CPI-PCE Comparator for analyzing inflation divergence.
    """

    def __init__(self, fred_api_key: str):
        self.fred = Fred(api_key=fred_api_key)

    def fetch_data(
        self,
        start_date: str,
        end_date: str,
        price_indexes: dict,
        focus_buckets: List[str]
    ) -> dict:
        """Fetch all required data from FRED."""
        data = {}

        # Headline indexes
        data['cpi'] = self.fred.get_series(
            price_indexes['cpi_series'], start_date, end_date
        )
        data['pce'] = self.fred.get_series(
            price_indexes['pce_series'], start_date, end_date
        )

        if 'pce_core_series' in price_indexes:
            data['pce_core'] = self.fred.get_series(
                price_indexes['pce_core_series'], start_date, end_date
            )

        # Bucket series (implement based on bucket definitions)
        # data['buckets'] = self._fetch_bucket_series(focus_buckets, ...)

        return data

    def analyze(
        self,
        start_date: str,
        end_date: str,
        inflation_measure: str,
        price_indexes: dict,
        focus_buckets: List[str],
        weight_source: str,
        baseline_period: Optional[dict] = None,
        vol_window_months: int = 24,
        signal_thresholds: Optional[dict] = None
    ) -> dict:
        """Run full CPI-PCE comparison analysis."""

        # 1. Fetch data
        data = self.fetch_data(start_date, end_date, price_indexes, focus_buckets)

        # 2. Calculate inflation
        pi_cpi = calc_inflation(data['cpi'], inflation_measure)
        pi_pce = calc_inflation(data['pce'], inflation_measure)

        # 3. Calculate bucket-level inflation
        pi_buckets = {
            b: calc_inflation(data['buckets'][b], inflation_measure)
            for b in focus_buckets
        }

        # 4. Load weights
        weights = self._load_weights(weight_source, focus_buckets)

        # 5. Calculate weighted inflation and divergence
        pi_pce_weighted = calc_weighted_inflation(pi_buckets, weights, focus_buckets)
        # ... (continue with full analysis)

        return output
```

</full_analysis_class>

<error_handling>

```python
import time
from functools import wraps

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator


@retry_with_backoff(max_retries=3)
def fetch_fred_series(fred: Fred, series_id: str, start: str, end: str):
    """Fetch FRED series with retry logic."""
    return fred.get_series(series_id, start, end)
```

</error_handling>
