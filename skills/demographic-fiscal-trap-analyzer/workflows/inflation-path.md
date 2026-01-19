# 通膨路徑分析工作流 (Inflation Path Workflow)

## 概述
專注於分析政府選擇「通膨稀釋」(inflation erosion) 或「金融抑制」(financial repression) 路徑的動機與歷史軌跡，評估實質利率環境與貨幣稀釋風險。

## 前置條件
- 已確認分析實體
- 通膨 (CPI) 與利率資料可用
- 債務與財政資料可用

## 執行步驟

### Step 1: 實質利率計算
```python
# 基本實質利率（費雪方程式）
real_rate = nominal_yield_10y - cpi_yoy

# 事前 vs 事後實質利率
# 事後 (ex-post): 使用已實現通膨
real_rate_ex_post = nominal_yield - realized_cpi

# 事前 (ex-ante): 使用通膨預期（若可用）
real_rate_ex_ante = nominal_yield - inflation_expectations
```

### Step 2: 負實質利率歷史分析
```python
# 計算負實質利率持續性
real_rate_series = real_rate[start_year:end_year]

# 負實質利率年份佔比
neg_real_years = (real_rate_series < 0).sum()
neg_real_share = neg_real_years / len(real_rate_series)

# 負實質利率深度（平均負值）
neg_real_depth = real_rate_series[real_rate_series < 0].mean()

# 當前狀態
current_real_rate = real_rate_series[end_year]
is_currently_negative = current_real_rate < 0

# 連續負實質利率年數
consecutive_neg_years = count_consecutive_negative(real_rate_series, end_year)
```

### Step 3: 金融抑制指數
```python
# 金融抑制指數 (Financial Repression Index)
# 結合多個金融抑制信號

financial_repression_index = (
    0.30 * zscore(-current_real_rate) +           # 負實質利率深度
    0.25 * zscore(neg_real_share) +               # 負實質利率持續性
    0.20 * zscore(central_bank_holdings_pct) +    # 央行持有國債比例（若可用）
    0.15 * zscore(bank_regulation_intensity) +    # 銀行監管強度（代理）
    0.10 * zscore(capital_control_index)          # 資本管制程度（若可用）
)
```

### Step 4: 通膨激勵指數計算
```python
# 通膨激勵指數 (Inflation Incentive Score)
# 衡量政府選擇通膨路徑的動機

debt_level = debt_to_gdp[end_year]
r_minus_g = nominal_yield[end_year] - nominal_gdp_growth[end_year]

inflation_incentive = (
    0.40 * zscore(debt_level) +           # 高債務 → 強動機
    0.20 * zscore(r_minus_g) +            # r > g → 難自然去槓桿
    0.20 * zscore(neg_real_share) +       # 已有負實質利率歷史
    0.20 * zscore(bloat_index)            # 高支出剛性 → 難削減
)
```

### Step 5: 債務稀釋效果評估
```python
# 通膨對實質債務的稀釋效果

# 歷史稀釋量估算
# 若實質利率為負，債務的實質負擔被侵蝕
cumulative_erosion = 0
for year in range(start_year, end_year+1):
    if real_rate[year] < 0:
        erosion = debt_to_gdp[year] * abs(real_rate[year])
        cumulative_erosion += erosion

# 相對於名義債務的稀釋比例
erosion_pct = cumulative_erosion / debt_to_gdp[end_year]

# 前瞻情境：若維持負 2% 實質利率 5 年
projected_erosion_5y = debt_to_gdp[end_year] * 0.02 * 5
```

### Step 6: 通膨突破風險評估
```python
# 評估通膨失控風險信號

# 通膨波動性
cpi_volatility_5y = cpi[end_year-5:end_year].std()

# 通膨預期錨定程度（若有調查資料）
# expectation_anchoring = long_term_expectations - target

# 貨幣成長與通膨關係
# m2_cpi_correlation = correlation(m2_growth, cpi, lag=12)

# 財政主導指標
fiscal_dominance_risk = (
    zscore(debt_level) * 0.4 +
    zscore(deficit_to_gdp) * 0.3 +
    zscore(central_bank_holdings_pct) * 0.3
)
```

### Step 7: 政策路徑分類
```python
# 基於指標組合分類政策路徑

if inflation_incentive > 1.5 and financial_repression_index > 1.0:
    policy_path = "ACTIVE_REPRESSION"  # 主動金融抑制
    description = "政府積極維持負實質利率環境，實質債務負擔持續被侵蝕"

elif inflation_incentive > 1.0 and current_real_rate < 0:
    policy_path = "PASSIVE_REPRESSION"  # 被動金融抑制
    description = "負實質利率環境存在但非刻意維持，可能隨通膨下降而結束"

elif inflation_incentive > 1.0 and current_real_rate > 0:
    policy_path = "LATENT_PRESSURE"  # 潛在壓力
    description = "有稀釋動機但尚未執行，需關注未來政策轉向"

elif fiscal_dominance_risk > 1.5:
    policy_path = "FISCAL_DOMINANCE_RISK"  # 財政主導風險
    description = "央行獨立性可能受威脅，通膨錨定風險上升"

else:
    policy_path = "ORTHODOX"  # 正統路徑
    description = "財政政策正常，無明顯通膨稀釋傾向"
```

## 輸出格式
```json
{
  "entity": "JPN",
  "inflation_path_analysis": {
    "real_rate": {
      "current": -1.2,
      "5y_average": -0.8,
      "10y_average": -0.5
    },
    "negative_real_rate": {
      "share_of_years": 0.70,
      "current_consecutive_years": 8,
      "average_depth_when_negative": -0.9
    },
    "scores": {
      "inflation_incentive": 1.85,
      "financial_repression_index": 1.45
    },
    "debt_erosion": {
      "cumulative_erosion_pct_gdp": 45.0,
      "erosion_relative_to_debt": 0.17,
      "projected_5y_erosion_at_neg2pct": 26.0
    },
    "policy_path": "ACTIVE_REPRESSION",
    "policy_description": "日本央行維持超寬鬆政策，實質利率長期為負，政府債務的實質負擔持續被侵蝕",
    "fiscal_dominance_risk": 1.65
  },
  "asset_allocation_implications": {
    "nominal_bonds": "UNDERWEIGHT - 實質報酬長期承壓",
    "inflation_linked_bonds": "OVERWEIGHT - 提供通膨保護",
    "real_assets": "OVERWEIGHT - 受益於名義價格上漲",
    "currency": "CAUTION - 長期購買力可能持續流失"
  },
  "interpretation": "日本呈現典型的金融抑制格局：超高債務、長期負實質利率、央行大量持有國債。過去10年約17%的債務實質負擔被通膨侵蝕。投資者應預期此環境將持續。"
}
```

## 注意事項
- 通膨預期資料（如調查或市場隱含）品質差異大
- 央行持有國債比例在部分國家為敏感資訊
- 資本管制指數需使用 IMF AREAER 或 Chinn-Ito 指數
- 日本、歐元區等負利率國家需特別處理名義利率下限
