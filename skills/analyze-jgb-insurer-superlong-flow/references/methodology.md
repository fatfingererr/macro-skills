# 方法論與計算邏輯

## 1. 核心指標定義

### 1.1 淨賣出 (Net Sale)

**重要**：JSDA 使用「賣出 - 買入」計算差引：

```
net_sale = 売付額 - 買付額 = gross_sales - gross_purchases
```

| 值  | 意義                      |
|-----|---------------------------|
| > 0 | 淨賣出（賣出 > 買入，需求減少）|
| < 0 | 淨買入（買入 > 賣出，需求增加）|
| = 0 | 買賣相抵                  |

**單位**：億日圓（100 million yen）

**注意**：此符號慣例與部分新聞報導相反，需特別留意。

### 1.2 連續淨賣出月數 (Streak)

從最新月份往回數，連續滿足「淨賣出 > 0」條件的月數。

**計算邏輯**：
```python
def calc_streak(series: pd.Series) -> int:
    """
    計算連續淨賣出月數

    Args:
        series: 淨賣出時間序列，index 為日期，正值 = 淨賣出

    Returns:
        連續月數
    """
    streak = 0
    for v in reversed(series.values):
        if v > 0:  # 正值 = 淨賣出
            streak += 1
        else:
            break
    return streak
```

**範例**：
```
月份:    2025-08  2025-09  2025-10  2025-11  2025-12
淨賣出:     259    2,258    2,767      451    8,224
streak:                                         → 5 個月
```

### 1.3 本輪累積 (Cumulative over Streak)

連續淨賣出期間的淨賣出總和。

```python
def calc_cumulative(series: pd.Series, streak_len: int) -> float:
    """
    計算本輪累積淨賣出

    Args:
        series: 淨賣出時間序列
        streak_len: 連續月數

    Returns:
        累積金額（億日圓）
    """
    return series.tail(streak_len).sum()
```

### 1.4 歷史極值判斷 (Record Detection)

判斷最新月份是否為歷史最大淨賣出（正值最大）。

```python
def is_record_sale(series: pd.Series) -> dict:
    """
    判斷是否創下歷史最大淨賣出

    Args:
        series: 淨賣出時間序列

    Returns:
        dict: 包含 is_record, record_sale, record_date
    """
    latest = series.iloc[-1]
    record_high = series.max()  # 最大淨賣出（正值最大）
    record_date = series.idxmax()

    return {
        "is_record_sale": (latest == record_high) and (latest > 0),
        "record_sale_100m_yen": float(record_high),
        "record_date": str(record_date),
        "lookback_period": f"全樣本 ({len(series)} 個月)"
    }
```

**注意**：
- 數據起點會影響「歷史紀錄」的含義，輸出必須說明樣本期間
- 若僅為近期極值，需標註「近 N 個月新高」

---

## 2. 統計指標

### 2.1 歷史分布

```python
def calc_historical_stats(series: pd.Series) -> dict:
    """計算歷史統計"""
    return {
        "count": len(series),
        "mean": series.mean(),
        "std": series.std(),
        "min": series.min(),  # 最大淨買入（負值最小）
        "max": series.max(),  # 最大淨賣出（正值最大）
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

**解讀**：
- Z-score > 2：極端淨賣出（超過 2 個標準差）
- Z-score < -2：極端淨買入

### 2.3 歷史分位數

```python
def calc_percentile(series: pd.Series, value: float) -> float:
    """計算數值在歷史中的分位數"""
    return (series <= value).mean()
```

**解讀**：
- 分位數 > 0.95：歷史前 5% 的淨賣出
- 分位數 < 0.05：歷史前 5% 的淨買入

---

## 3. 數據結構

### 3.1 JSDA Excel 結構

**來源 URL**：
- 當前財年：`https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai.xlsx`
- 歷史財年：`https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/koushasai{YYYY}.xlsx`

**關鍵 Sheet**：`(Ｊ)合計差引`

**欄位結構**：

| 欄位位置 | 內容 |
|----------|------|
| 第 0 列 | 年/月（如 2025/12）|
| 第 1 列 | 投資人類型（日文）|
| 第 2 列 | 投資人類型（英文）|
| 第 3 列 | 國債總計 |
| **第 4 列** | **超長期（Interest-bearing Long-term over 10-year）** |
| 第 5 列 | 利付長期 |
| 第 6 列 | 利付中期 |
| 第 7 列 | 割引 |
| 第 8 列 | 國庫短期證券等 |

### 3.2 投資人分類

| JSDA 分類 | 英文 | 說明 |
|-----------|------|------|
| **生保・損保** | **Life & Non-Life Insurance Companies** | 壽險 + 產險（本 Skill 使用）|
| 都市銀行 | City Banks | 大型商業銀行 |
| 地方銀行 | Regional Banks | 區域性銀行 |
| 信託銀行 | Trust Banks | 含年金管理 |
| 外国人 | Foreigners | 海外投資者 |

### 3.3 天期桶定義

| 天期桶 | 英文 | 說明 |
|--------|------|------|
| **超長期** | Interest-bearing Long-term (over 10-year) | 10 年以上利付債（本 Skill 使用）|
| 利付長期 | Interest-bearing Long-term | 5-10 年利付債 |
| 利付中期 | Interest-bearing Medium-term | 2-5 年利付債 |
| 割引 | Zero-Coupon | 零息債 |

---

## 4. 輸出格式

### 4.1 核心輸出結構

```json
{
  "skill": "analyze_jgb_insurer_superlong_flow",
  "version": "1.0.0",
  "as_of": "2026-01-26",
  "data_source": {
    "name": "JSDA Trading Volume of OTC Bonds (公社債店頭売買高)",
    "url": "https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/",
    "sheet": "(Ｊ)合計差引"
  },
  "parameters": {
    "investor_group": "life_and_nonlife_insurance",
    "investor_label": "生保・損保 (Life & Non-Life Insurance Companies)",
    "maturity_bucket": "super_long",
    "maturity_label": "超長期 (Interest-bearing Long-term over 10-year)",
    "sign_convention": "正值=淨賣出 (Sell-Purchase), 負值=淨買入",
    "unit": "100 million yen (億円)"
  },
  "analysis_period": {
    "start": "2021-04",
    "end": "2025-12",
    "months": 57
  },
  "latest_month": {
    "date": "2025-12",
    "net_sale_100m_yen": 8224,
    "net_sale_trillion_yen": 0.8224,
    "interpretation": "淨賣出"
  },
  "record_analysis": {
    "is_record_sale": true,
    "record_sale_100m_yen": 8224,
    "record_sale_date": "2025-12",
    "lookback_period": "全樣本 (57 個月)"
  },
  "streak_analysis": {
    "consecutive_net_sale_months": 5,
    "streak_start": "2025-08",
    "cumulative_net_sale_100m_yen": 13959,
    "cumulative_net_sale_trillion_yen": 1.3959
  },
  "historical_stats": {
    "count": 57,
    "mean_100m_yen": -2872,
    "std_100m_yen": 3830,
    "latest_zscore": 2.90,
    "latest_percentile": 0.9825
  },
  "headline_takeaways": [
    "✓ 驗證屬實：日本保險公司在 2025/12 創下歷史最大單月淨賣出（8,224 億日圓）",
    "已連續 5 個月淨賣出超長期國債，累積金額 13,959 億日圓（1.40 兆日圓）",
    "當前淨賣出規模處於歷史極端區間（Z-score: 2.90，超過 2 個標準差）"
  ]
}
```

---

## 5. 注意事項

### 5.1 單位轉換

| 原始單位 | 目標單位 | 轉換 |
|----------|----------|------|
| 億日圓 | 兆日圓 | ÷ 10,000 |
| 億日圓 | 十億日圓 | ÷ 10 |

### 5.2 時間對齊

- JSDA 月度數據以月末為基準
- 日本財年從 4 月開始，歷史檔案依財年分割
- 數據延遲約 T+1 個月

### 5.3 邊界處理

- 若 `streak_len = 0`，表示最新月份為淨買入
- 若 `streak_len = 全樣本長度`，表示整個樣本期間都是淨賣出（極端情況）

### 5.4 數據範圍限制

- 僅包含店頭（OTC）交易，不含交易所交易
- 「生保・損保」為壽險 + 產險合計，無法分拆
- 2018/05 前的數據格式不同，需特別處理
