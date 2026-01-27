# 輸入參數定義

本文件定義 `forecast-sector-relative-return-from-yield-spread` 技能的所有輸入參數。

---

## 必要參數 (Required)

| 參數             | 類型   | 說明                                | 範例          |
|------------------|--------|-------------------------------------|---------------|
| risk_ticker      | string | 代表成長股/風險資產的標的           | "QQQ", "^NDX" |
| defensive_ticker | string | 代表防禦股/安全資產的標的           | "XLV", "VHT"  |
| lead_months      | int    | 領先期（月），即 spread 領先多少月   | 24            |
| lookback_years   | int    | 回測/估計領先關係的歷史年數         | 12, 15        |

---

## 選用參數 (Optional)

### 殖利率相關

| 參數        | 類型   | 預設值 | 說明                   | 有效值                    |
|-------------|--------|--------|------------------------|---------------------------|
| short_tenor | string | "2Y"   | 短端殖利率期限         | "3M", "1Y", "2Y", "3Y"    |
| long_tenor  | string | "10Y"  | 長端殖利率期限         | "5Y", "7Y", "10Y", "30Y"  |

**殖利率期限對應 FRED 代碼：**
| 期限 | FRED 代碼 |
|------|-----------|
| 3M   | DGS3MO    |
| 1Y   | DGS1      |
| 2Y   | DGS2      |
| 3Y   | DGS3      |
| 5Y   | DGS5      |
| 7Y   | DGS7      |
| 10Y  | DGS10     |
| 30Y  | DGS30     |

### 數據處理相關

| 參數             | 類型   | 預設值   | 說明                       | 有效值                   |
|------------------|--------|----------|----------------------------|--------------------------|
| freq             | string | "weekly" | 資料頻率                   | "daily", "weekly", "monthly" |
| smoothing_window | int    | 13       | spread 平滑視窗（單位同 freq）| 0（不平滑）, 4, 13, 26   |

**頻率說明：**
- **daily**：最細緻，但雜訊大，適合短期分析
- **weekly**：建議預設，平衡細緻度與穩定性
- **monthly**：最穩定，但數據點較少

### 預測相關

| 參數                  | 類型   | 預設值            | 說明                       | 有效值                              |
|-----------------------|--------|-------------------|----------------------------|-------------------------------------|
| return_horizon_months | int    | 24                | 預測的相對報酬視窗（月）   | 6, 12, 18, 24, 30, 36               |
| model_type            | string | "lagged_regression"| 預測模型類型               | "corr_scan", "lagged_regression", "ridge" |
| confidence_level      | float  | 0.80              | 區間估計信心水準           | 0.80, 0.90, 0.95                    |

**模型類型說明：**
- **corr_scan**：僅計算相關性，不做預測
- **lagged_regression**：簡單 OLS 迴歸（預設）
- **ridge**：Ridge 迴歸（加入 L2 正則化，防止過擬合）

### 領先掃描相關

| 參數       | 類型      | 預設值           | 說明                   |
|------------|-----------|------------------|------------------------|
| lead_scan  | bool      | false            | 是否執行領先期掃描     |
| scan_range | list[int] | [6,12,18,24,30]  | 掃描的領先期列表（月） |

---

## 參數組合範例

### 範例 1：快速預設分析

```python
params = {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "lead_months": 24,
    "lookback_years": 12
}
```

### 範例 2：自訂利差組合

```python
params = {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "short_tenor": "3M",
    "long_tenor": "10Y",
    "lead_months": 18,
    "lookback_years": 15
}
```

### 範例 3：完整領先掃描

```python
params = {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "lookback_years": 15,
    "lead_scan": True,
    "scan_range": [6, 12, 18, 24, 30, 36],
    "freq": "monthly",
    "smoothing_window": 3
}
```

### 範例 4：保守區間估計

```python
params = {
    "risk_ticker": "QQQ",
    "defensive_ticker": "XLV",
    "lead_months": 24,
    "lookback_years": 12,
    "confidence_level": 0.90,
    "model_type": "ridge"
}
```

---

## 參數驗證規則

### 必要條件

1. `risk_ticker` 和 `defensive_ticker` 必須是有效的 Yahoo Finance 代碼
2. `lead_months` 必須 > 0 且 < lookback_years * 12 / 2
3. `lookback_years` 必須 >= 5（至少半個景氣週期）

### 建議範圍

| 參數             | 建議最小值 | 建議最大值 | 理由                     |
|------------------|------------|------------|--------------------------|
| lead_months      | 6          | 36         | 超過 3 年的領先較不可靠 |
| lookback_years   | 10         | 20         | 涵蓋 1-2 個景氣週期     |
| smoothing_window | 4          | 26         | 過長會失去時效性         |
| confidence_level | 0.80       | 0.95       | 過高區間太寬無意義       |

### 警告條件

- `lookback_years` < 10：警告樣本量可能不足
- `lead_months` > lookback_years * 6：警告可用數據點過少
- `smoothing_window` > lead_months / 2：警告可能過度平滑

---

## CLI 參數對應

```bash
python scripts/spread_forecaster.py \
  --risk-ticker QQQ \
  --defensive-ticker XLV \
  --short-tenor 2Y \
  --long-tenor 10Y \
  --lead-months 24 \
  --lookback-years 12 \
  --freq weekly \
  --smoothing-window 13 \
  --model-type lagged_regression \
  --confidence-level 0.80 \
  --lead-scan \
  --scan-range 6,12,18,24,30 \
  --output result.json
```

**快速執行：**
```bash
python scripts/spread_forecaster.py --quick
# 等同於使用所有預設值
```
