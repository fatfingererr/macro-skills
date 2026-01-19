# 債務動態分析工作流 (Debt Dynamics Workflow)

## 概述
專注於政府債務可持續性分析，深入探討 r-g 缺口、債務軌跡演化、以及財政空間評估。

## 前置條件
- 已確認分析實體
- 已確認時間區間
- 債務與利率資料可用

## 執行步驟

### Step 1: 債務存量分析
```
擷取並分析：
- 政府債務/GDP 水準
- 債務結構（若可用）：內債 vs 外債、短期 vs 長期
- 5年債務軌跡斜率
```

### Step 2: 利息負擔分析
```
計算：
- 隱含利率 = 利息支出 / 債務存量（若資料可用）
- 或使用 10年公債殖利率作為邊際成本代理
- 利息支出/GDP 比率
```

### Step 3: r-g 缺口分析
```python
# 名義 r-g
r_nominal = yield_10y[end_year]
g_nominal = nominal_gdp_growth[end_year]
rg_nominal = r_nominal - g_nominal

# 實質 r-g（若通膨資料可用）
r_real = yield_10y - cpi
g_real = real_gdp_growth
rg_real = r_real - g_real

# r-g 持續性（5年平均）
rg_avg_5y = (yield_10y - nominal_gdp_growth)[end_year-5:end_year].mean()
```

### Step 4: 債務動態方程式
```
標準債務動態：
Δd = (r - g) × d_{t-1} + pb

其中：
- d = 債務/GDP
- r = 名義利率
- g = 名義成長率
- pb = 基本財政餘額/GDP（支出 - 收入，不含利息）

若 r > g 且 pb >= 0（赤字），債務比率將自動膨脹。
```

### Step 5: 債務穩定條件
```python
# 計算穩定債務所需的基本盈餘
required_pb = (r - g) * debt_level

# 實際基本餘額（估算）
actual_pb = (gov_expenditure - interest_payments) - gov_revenue

# 財政調整缺口
fiscal_gap = required_pb - actual_pb
```

### Step 6: 情境分析
```
模擬三種情境：

1. 基準情境：r-g 維持當前水準
   - 5年後債務/GDP 預測

2. 利率上升情境：r 上升 100bps
   - 評估債務軌跡惡化程度

3. 成長下滑情境：g 下降 100bps
   - 評估成長衝擊影響
```

### Step 7: 評分與分類
```python
debt_dynamics_score = (
    zscore(debt_level) * 0.40 +
    zscore(debt_slope_5y) * 0.25 +
    zscore(rg_nominal) * 0.20 +
    zscore(fiscal_gap) * 0.15
)

# 分類
if debt_dynamics_score > 2.0:
    debt_status = "CRITICAL"  # 債務危機風險
elif debt_dynamics_score > 1.0:
    debt_status = "ELEVATED"  # 需關注
elif debt_dynamics_score > 0:
    debt_status = "MODERATE"  # 中等壓力
else:
    debt_status = "SUSTAINABLE"  # 可持續
```

## 輸出格式
```json
{
  "entity": "JPN",
  "debt_dynamics": {
    "debt_to_gdp_level": 262.5,
    "debt_to_gdp_slope_5y": 2.3,
    "r_nominal": 0.8,
    "g_nominal": 2.1,
    "r_minus_g": -1.3,
    "r_minus_g_5y_avg": -0.8,
    "required_primary_balance": -3.4,
    "fiscal_gap_estimate": 1.2
  },
  "score": 1.85,
  "status": "ELEVATED",
  "scenarios": {
    "baseline_5y": 275.0,
    "rate_shock_5y": 290.0,
    "growth_shock_5y": 285.0
  },
  "interpretation": "日本債務水準極高但 r-g 為負，短期自動穩定；然而超低利率環境不可持續，利率正常化將造成顯著壓力"
}
```

## 注意事項
- 日本等特殊案例：雖債務極高，但央行持有大量國債，有效利率極低
- 新興市場：需考慮外幣計價債務的匯率風險
- 資料頻率：年度資料可能遺漏季度波動
