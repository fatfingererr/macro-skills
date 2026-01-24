# 集中度指標計算方法

## 核心指標定義

### Herfindahl-Hirschman Index (HHI)

**公式**：
```
HHI = Σ (share_i × 100)²
```

其中 `share_i` 為第 i 個國家的市場份額（0-1）。

**範圍**：0 - 10,000

**解讀**：

| HHI 範圍 | 市場結構 | 說明 |
|----------|----------|------|
| < 1,500 | 低集中 (Unconcentrated) | 競爭市場 |
| 1,500 - 2,500 | 中等集中 (Moderately Concentrated) | 寡占傾向 |
| > 2,500 | 高集中 (Highly Concentrated) | 寡占市場 |

**計算範例**：
```python
# 假設 4 國各 25% 份額
shares = [0.25, 0.25, 0.25, 0.25]
hhi = sum((s * 100) ** 2 for s in shares)
# hhi = 625 + 625 + 625 + 625 = 2,500

# 假設 1 國 70% + 3 國各 10%
shares = [0.70, 0.10, 0.10, 0.10]
hhi = sum((s * 100) ** 2 for s in shares)
# hhi = 4,900 + 100 + 100 + 100 = 5,200
```

---

### 集中比率 (Concentration Ratio, CR_n)

**公式**：
```
CR_n = Σ top_n_share
```

**常用指標**：
- **CR4**：前 4 大生產國份額加總
- **CR8**：前 8 大生產國份額加總

**解讀**：

| CR4 範圍 | 市場結構 |
|----------|----------|
| < 40% | 低集中 |
| 40% - 60% | 中等集中 |
| > 60% | 高集中 |

---

### 單國份額 (Country Share)

**公式**：
```
share_i = production_i / world_production
```

**關鍵閾值**（智利專用）：

| 智利份額 | 風險等級 | 說明 |
|----------|----------|------|
| < 20% | 低 | 分散化較好 |
| 20% - 30% | 中 | 顯著依賴 |
| > 30% | 高 | 單點風險 |

---

## Python 實作

```python
import pandas as pd
import numpy as np

def compute_shares(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    計算各國市場份額

    Parameters:
    -----------
    df : pd.DataFrame
        標準化產量數據（含 year, country, production）
    year : int
        目標年份

    Returns:
    --------
    pd.DataFrame : 排序後的份額表
    """
    year_data = df[df.year == year].copy()

    # 取得世界總量
    world_row = year_data[year_data.country == "World"]
    if world_row.empty:
        # 如果沒有 World 行，自己加總
        world_total = year_data.production.sum()
    else:
        world_total = world_row.production.values[0]
        year_data = year_data[year_data.country != "World"]

    # 計算份額
    year_data["share"] = year_data.production / world_total
    year_data["share_pct"] = year_data.share * 100

    # 排序
    year_data = year_data.sort_values("share", ascending=False).reset_index(drop=True)

    # 計算累積份額
    year_data["cumulative_share"] = year_data.share.cumsum()

    return year_data


def compute_hhi(shares_df: pd.DataFrame) -> float:
    """
    計算 Herfindahl-Hirschman Index

    Parameters:
    -----------
    shares_df : pd.DataFrame
        compute_shares 的輸出

    Returns:
    --------
    float : HHI 值（0-10000）
    """
    return ((shares_df["share"] * 100) ** 2).sum()


def compute_cr_n(shares_df: pd.DataFrame, n: int) -> float:
    """
    計算前 N 大國家集中度

    Parameters:
    -----------
    shares_df : pd.DataFrame
        compute_shares 的輸出
    n : int
        前 N 大國家

    Returns:
    --------
    float : CR_n 值（0-1）
    """
    return shares_df.head(n)["share"].sum()


def classify_market_structure(hhi: float) -> str:
    """
    根據 HHI 分類市場結構
    """
    if hhi < 1500:
        return "低集中 (Unconcentrated)"
    elif hhi < 2500:
        return "中等集中 (Moderately Concentrated)"
    else:
        return "高集中 (Highly Concentrated)"


def compute_all_metrics(df: pd.DataFrame, year: int) -> dict:
    """
    計算所有集中度指標

    Returns:
    --------
    dict : 完整指標集
    """
    shares = compute_shares(df, year)

    hhi = compute_hhi(shares)
    cr4 = compute_cr_n(shares, 4)
    cr8 = compute_cr_n(shares, 8)

    chile_row = shares[shares.country == "Chile"]
    chile_share = chile_row["share"].values[0] if not chile_row.empty else 0

    return {
        "year": year,
        "hhi": round(hhi, 0),
        "cr4": round(cr4, 4),
        "cr8": round(cr8, 4),
        "chile_share": round(chile_share, 4),
        "market_structure": classify_market_structure(hhi),
        "top_3": shares.head(3)[["country", "share"]].to_dict("records"),
        "top_producer": shares.iloc[0]["country"],
        "top_producer_share": round(shares.iloc[0]["share"], 4)
    }
```

---

## 時序分析

```python
def compute_concentration_timeseries(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """
    計算多年份集中度指標

    Returns:
    --------
    pd.DataFrame : 年度指標時序
    """
    results = []

    for year in range(start_year, end_year + 1):
        try:
            metrics = compute_all_metrics(df, year)
            results.append(metrics)
        except Exception as e:
            print(f"Warning: {year} 年計算失敗 - {e}")
            continue

    return pd.DataFrame(results)


def analyze_trend(timeseries: pd.DataFrame, window: int = 10) -> dict:
    """
    分析集中度趨勢

    Returns:
    --------
    dict : 趨勢分析結果
    """
    recent = timeseries.tail(window)

    hhi_change = recent.hhi.iloc[-1] - recent.hhi.iloc[0]
    chile_change = recent.chile_share.iloc[-1] - recent.chile_share.iloc[0]

    return {
        "hhi_latest": recent.hhi.iloc[-1],
        "hhi_10y_ago": recent.hhi.iloc[0],
        "hhi_change": hhi_change,
        "hhi_trend": "上升" if hhi_change > 0 else "下降",
        "chile_share_latest": recent.chile_share.iloc[-1],
        "chile_share_10y_ago": recent.chile_share.iloc[0],
        "chile_change": chile_change,
        "chile_trend": "上升" if chile_change > 0 else "下降"
    }
```

---

## 歷史分位數

```python
def compute_percentile(timeseries: pd.DataFrame, country: str, current_share: float) -> float:
    """
    計算當前份額在歷史分布中的分位數

    Parameters:
    -----------
    timeseries : pd.DataFrame
        歷史時序數據
    country : str
        國家名稱
    current_share : float
        當前份額

    Returns:
    --------
    float : 分位數（0-100）
    """
    historical_shares = timeseries[f"{country.lower()}_share"].dropna()
    percentile = (historical_shares < current_share).mean() * 100
    return round(percentile, 0)
```

---

## 視覺化建議

### HHI 時序圖
- X 軸：年份
- Y 軸：HHI 值
- 標記 1,500 和 2,500 門檻線
- 標記當前值

### 國家份額餅圖
- 最新年度
- 前 N 大國家 + "Other"
- 標註份額百分比

### CR 指標演進圖
- X 軸：年份
- Y 軸：CR 值（0-1）
- 多線：CR4、CR8
- 對比智利單國份額
