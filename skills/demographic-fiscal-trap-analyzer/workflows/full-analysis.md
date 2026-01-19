# 完整分析工作流 (Full Analysis Workflow)

## 概述
執行完整的人口-財政陷阱分析，包含所有四支柱評分、象限分類、通膨激勵指數、以及趨勢預測。

## 前置條件
- 已確認分析實體（國家/地區代碼）
- 已確認時間區間（start_year, end_year）
- 可選：自訂權重

## 執行步驟

### Step 1: 參數確認
```
確認以下參數：
- entities: [國家代碼列表，如 JPN, USA, DEU]
- start_year: 歷史起始年（建議 2010）
- end_year: 歷史結束年（最近可用年份）
- forecast_end_year: 預測結束年（預設 2050）
- weights: 四支柱權重（預設 aging:0.35, debt:0.35, bloat:0.15, growth_drag:0.15）
```

### Step 2: 資料擷取
執行以下資料擷取模組：

1. **撫養比資料** (World Bank / UN WPP)
   - SP.POP.DPND.OL (老年撫養比)
   - SP.POP.DPND.YG (青年撫養比)
   - SP.POP.DPND (總撫養比)

2. **債務資料** (IMF WEO / World Bank)
   - GC.DOD.TOTL.GD.ZS (政府債務/GDP)
   - 或 IMF GGXWDG_NGDP

3. **支出資料** (World Bank / IMF)
   - NE.CON.GOVT.ZS (政府消費/GDP)
   - GC.XPN.TOTL.GD.ZS (政府支出/GDP)

4. **成長與通膨** (World Bank / IMF)
   - NY.GDP.MKTP.KD.ZG (實質GDP成長)
   - FP.CPI.TOTL.ZG (CPI通膨)

5. **利率資料** (OECD / 各國央行)
   - 10年公債殖利率
   - 或政策利率（回退）

### Step 3: 指標計算

#### 3.1 老化壓力 (Aging Pressure)
```python
aging_level = old_age_dependency[end_year]
aging_slope_10y = linear_slope(old_age_dependency[end_year-10:end_year])
aging_pressure = zscore(aging_level) * 0.5 + zscore(aging_slope_10y) * 0.5
```

#### 3.2 債務動態 (Debt Dynamics)
```python
debt_level = debt_to_gdp[end_year]
debt_slope_5y = linear_slope(debt_to_gdp[end_year-5:end_year])
r = nominal_yield[end_year]
g = nominal_gdp_growth[end_year]
r_minus_g = r - g
debt_dynamics = zscore(debt_level)*0.5 + zscore(debt_slope_5y)*0.3 + zscore(r_minus_g)*0.2
```

#### 3.3 官僚膨脹 (Bloat Index)
```python
bloat_index = zscore(gov_consumption[end_year])*0.6 + zscore(gov_expenditure[end_year])*0.4
```

#### 3.4 成長拖累 (Growth Drag)
```python
growth_drag = zscore(-nominal_gdp_growth[end_year])  # 負向：低成長 = 高拖累
```

### Step 4: 綜合評分

#### 4.1 財政陷阱分數
```python
fiscal_trap_score = (
    weights["aging"] * aging_pressure +
    weights["debt"] * debt_dynamics +
    weights["bloat"] * bloat_index +
    weights["growth_drag"] * growth_drag
)
```

#### 4.2 通膨激勵指數
```python
real_rate = nominal_yield - cpi
neg_real_share_5y = (real_rate[end_year-5:end_year] < 0).mean()

inflation_incentive = (
    0.40 * zscore(debt_level) +
    0.20 * zscore(r_minus_g) +
    0.20 * zscore(neg_real_share_5y) +
    0.20 * zscore(bloat_index)
)
```

### Step 5: 象限分類
```python
if aging_pressure > 1 and debt_dynamics > 1:
    quadrant = "Q1_HighAging_HighDebt"  # 雙高危機
elif aging_pressure > 1 and debt_dynamics <= 1:
    quadrant = "Q2_HighAging_LowDebt"   # 老化主導
elif aging_pressure <= 1 and debt_dynamics > 1:
    quadrant = "Q3_LowAging_HighDebt"   # 債務主導
else:
    quadrant = "Q4_LowAging_LowDebt"    # 相對健康
```

### Step 6: 趨勢預測（可選）
若啟用 `forecast_end_year`，使用 UN WPP 撫養比預測數據，計算未來老化壓力趨勢。

### Step 7: 輸出報告
按照 `templates/output-json.md` 或 `templates/output-markdown.md` 格式輸出結果。

## 錯誤處理
- 資料缺失：記錄缺失指標，使用可用資料計算部分結果
- 殖利率不可用：回退至政策利率
- 跨國截面不足：警告 z-score 計算可能不穩定

## 輸出範例
參見 `examples/japan-full-analysis.json`
