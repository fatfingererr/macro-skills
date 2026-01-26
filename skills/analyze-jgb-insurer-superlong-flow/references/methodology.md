### 1.1 淨買入 (Net Purchases)

```
net_purchases = gross_purchases - gross_sales
```

| 值  | 意義                      |
|-----|---------------------------|
| > 0 | 淨買入（需求增加）        |
| < 0 | 淨賣出（需求減少 / 拋售） |
| = 0 | 買賣相抵                  |

**單位**：十億日圓（¥B）或兆日圓（¥T）

### 1.2 連續賣超月數 (Streak)

從最新月份往回數，連續滿足條件的月數。

**計算邏輯**：
```python
def calc_streak(series: pd.Series, sign: str = "negative") -> int:
    """
    計算連續賣超（或買超）月數

    Args:
        series: 淨買入時間序列，index 為日期
        sign: "negative"（連續賣超）或 "positive"（連續買超）

    Returns:
        連續月數
    """
    s = series.dropna()
    streak = 0

    for v in reversed(s.values):
        if sign == "negative" and v < 0:
            streak += 1
        elif sign == "positive" and v > 0:
            streak += 1
        else:
            break

    return streak
```

**範例**：
```
月份:    2025-08  2025-09  2025-10  2025-11  2025-12
淨買入:    -100     -200     -150     -300     -800
streak:                                         → 5 個月
```

### 1.3 本輪累積 (Cumulative over Streak)

連續賣超期間的淨買入總和。

```python
def calc_cumulative(series: pd.Series, end_date: str, streak_len: int) -> float:
    """
    計算本輪累積淨買入

    Args:
        series: 淨買入時間序列
        end_date: 結束日期
        streak_len: 連續月數

    Returns:
        累積金額
    """
    streak_window = series.loc[:end_date].tail(streak_len)
    return streak_window.sum()
```

### 1.4 歷史極值判斷 (Record Detection)

判斷最新月份是否為歷史最低（最大淨賣出）。

```python
def is_record_sale(series: pd.Series, end_date: str, lookback_years: int = 999) -> dict:
    """
    判斷是否創下歷史最大淨賣出

    Args:
        series: 淨買入時間序列
        end_date: 結束日期
        lookback_years: 回溯年數（999 = 全樣本）

    Returns:
        dict: 包含 is_record, record_low, record_date
    """
    if lookback_years < 999:
        lookback_start = pd.Timestamp(end_date) - pd.DateOffset(years=lookback_years)
        sample = series.loc[lookback_start:end_date]
    else:
        sample = series.loc[:end_date]

    latest = series.loc[end_date]
    record_low = sample.min()
    record_date = sample.idxmin()

    return {
        "is_record": (latest == record_low) and (latest < 0),
        "record_low": float(record_low),
        "record_date": str(record_date),
        "lookback_period": f"{lookback_years} years" if lookback_years < 999 else "全樣本"
    }
```

**注意**：
- `lookback_years = 999` 表示使用全樣本
- 若資料起點較晚，「歷史紀錄」的含義需說明

---

## 2. 統計指標

### 2.1 歷史分布

```python
def calc_historical_stats(series: pd.Series) -> dict:
    """計算歷史統計"""
    return {
        "mean": series.mean(),
        "std": series.std(),
        "min": series.min(),
        "max": series.max(),
        "median": series.median(),
        "percentile_25": series.quantile(0.25),
        "percentile_75": series.quantile(0.75)
    }
```

### 2.2 Z-score

```python
def calc_zscore(value: float, mean: float, std: float) -> float:
    """計算 Z-score"""
    if std == 0:
        return 0
    return (value - mean) / std
```

### 2.3 歷史分位數

```python
def calc_percentile(series: pd.Series, value: float) -> float:
    """計算數值在歷史中的分位數"""
    return (series < value).mean()  # 比例低於該值的觀察數
```

---

## 3. 口徑對齊邏輯

### 3.1 天期桶映射

```python
MATURITY_MAPPING = {
    "super_long": ["超長期", "super-long", "20Y+", "30Y+"],
    "long": ["長期", "long-term", "10Y"],
    "10y_plus": ["10年以上", "10+ years"],  # 可能需要合併 long + super_long
    "long_plus_super_long": None  # 需手動計算
}

def get_maturity_bucket(xls_data, bucket_name: str):
    """從 XLS 中提取對應的天期桶數據"""
    if bucket_name == "long_plus_super_long":
        return xls_data["long"] + xls_data["super_long"]

    for jsda_name in MATURITY_MAPPING.get(bucket_name, []):
        if jsda_name in xls_data.columns:
            return xls_data[jsda_name]

    raise ValueError(f"未找到對應的天期桶: {bucket_name}")
```

### 3.2 投資人分類映射

```python
INVESTOR_MAPPING = {
    "insurance_companies": ["保險公司", "Insurance"],
    "life_insurance": ["壽險", "Life Insurance"],
    "non_life_insurance": ["產險", "Non-life Insurance"]
}
```

---

## 4. 輸出格式

### 4.1 核心輸出結構

```python
def analyze(
    series: pd.Series,
    end_date: str,
    investor_group: str,
    maturity_bucket: str,
    lookback_years: int = 999
) -> dict:
    """執行完整分析"""

    latest = series.loc[end_date]
    streak_len = calc_streak(series.loc[:end_date], sign="negative")
    cum = calc_cumulative(series, end_date, streak_len)
    record_info = is_record_sale(series, end_date, lookback_years)
    stats = calc_historical_stats(series)

    return {
        "skill": "analyze_jgb_insurer_superlong_flow",
        "as_of": str(pd.Timestamp.now().date()),
        "data_source": "JSDA Trends in Bond Transactions (by investor type)",
        "investor_group": investor_group,
        "maturity_bucket": maturity_bucket,
        "latest_month": {
            "date": end_date,
            "net_purchases_trillion_jpy": round(latest / 1000, 4),  # 轉換為兆
            "interpretation": "淨賣出" if latest < 0 else "淨買入"
        },
        "record_analysis": record_info,
        "streak_analysis": {
            "consecutive_negative_months": streak_len,
            "streak_start": str(series.loc[:end_date].tail(streak_len).index[0]),
            "cumulative_over_streak_trillion_jpy": round(cum / 1000, 4)
        },
        "historical_stats": {
            "mean_billion_jpy": round(stats["mean"], 2),
            "std_billion_jpy": round(stats["std"], 2),
            "zscore": round(calc_zscore(latest, stats["mean"], stats["std"]), 2)
        }
    }
```

---

## 5. 注意事項

### 5.1 單位轉換

| JSDA 原始單位  | 常見報導單位 | 轉換   |
|----------------|--------------|--------|
| 十億日圓（¥B） | 兆日圓（¥T） | ÷ 1000 |
| 十億日圓（¥B） | 億日圓       | × 10   |

### 5.2 時間對齊

- JSDA 月度數據以月末為基準
- 匯率換算若需使用月均值，需另行計算

### 5.3 邊界處理

- 若 `streak_len = 0`，表示最新月份為淨買入
- 若 `streak_len = 全樣本長度`，表示從未有淨買入月份（極端情況）
