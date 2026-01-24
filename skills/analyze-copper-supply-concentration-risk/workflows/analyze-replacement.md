# Workflow: 秘魯/DRC 替代依賴度分析

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/replacement-countries.md
</required_reading>

<process>
## Step 1: 確認分析參數

收集或確認以下參數：

```yaml
start_year: 2010          # 歷史分析起始年
end_year: 2023            # 分析結束年
horizon_years: 10         # 未來預測年限
chile_decline_assumption: "trend"  # trend | fixed | scenario
replacement_countries:
  - Peru
  - Democratic Republic of Congo
```

**chile_decline_assumption 說明：**
- `trend`：延續近 N 年趨勢斜率
- `fixed`：使用固定百分比（如 -2%/年）
- `scenario`：多情境分析

## Step 2: 擷取歷史產量數據

從 OWID 擷取智利、秘魯、DRC 歷年產量：

```bash
python scripts/fetch_owid.py --commodity=copper \
  --countries=Chile,Peru,"Democratic Republic of Congo" \
  --start={start_year} --end={end_year}
```

## Step 3: 計算歷史增量

```python
def compute_historical_increment(df, country, n_years=10):
    """
    計算國家近 N 年的產量增量

    Returns:
    --------
    dict with total_increment, cagr, annual_increments
    """
    country_data = df[df.country == country].sort_values("year")

    # 取近 N 年
    recent = country_data.tail(n_years + 1)

    start_prod = recent.iloc[0].production
    end_prod = recent.iloc[-1].production

    total_increment = end_prod - start_prod
    cagr = (end_prod / start_prod) ** (1 / n_years) - 1

    annual_increments = recent.production.diff().dropna().tolist()

    return {
        "country": country,
        "period": f"{recent.iloc[0].year}-{recent.iloc[-1].year}",
        "start_production": start_prod,
        "end_production": end_prod,
        "total_increment": total_increment,
        "cagr": cagr,
        "annual_increments": annual_increments
    }

chile_hist = compute_historical_increment(df, "Chile", n_years=10)
peru_hist = compute_historical_increment(df, "Peru", n_years=10)
drc_hist = compute_historical_increment(df, "Democratic Republic of Congo", n_years=10)
```

## Step 4: 估算智利未來缺口

```python
def estimate_chile_decline(df, method="trend", horizon=10):
    """
    估算智利未來 N 年的產量下滑量

    Parameters:
    -----------
    method : str
        "trend" - 延續歷史趨勢斜率
        "fixed" - 固定年化下滑率
        "scenario" - 多情境

    Returns:
    --------
    dict with expected_decline, scenarios
    """
    chile = df[df.country == "Chile"].sort_values("year")
    latest_prod = chile.iloc[-1].production

    if method == "trend":
        # 使用近 10 年斜率
        recent = chile.tail(11)
        x = recent.year.values
        y = recent.production.values
        slope = np.polyfit(x, y, 1)[0]

        # 預測 horizon 年後
        future_prod = latest_prod + slope * horizon
        expected_decline = latest_prod - future_prod if future_prod < latest_prod else 0

        return {
            "method": "trend",
            "slope_t_per_year": slope,
            "latest_production": latest_prod,
            "expected_decline": expected_decline,
            "scenarios": None
        }

    elif method == "fixed":
        decline_rate = 0.02  # 年化 -2%
        future_prod = latest_prod * (1 - decline_rate) ** horizon
        expected_decline = latest_prod - future_prod

        return {
            "method": "fixed",
            "decline_rate": decline_rate,
            "latest_production": latest_prod,
            "expected_decline": expected_decline,
            "scenarios": None
        }

    elif method == "scenario":
        scenarios = []
        for rate in [-0.01, -0.02, -0.03]:  # -1%, -2%, -3%
            future_prod = latest_prod * (1 + rate) ** horizon
            decline = latest_prod - future_prod
            scenarios.append({
                "name": f"{rate*100:.0f}%/年",
                "decline_rate": rate,
                "expected_decline": decline
            })

        return {
            "method": "scenario",
            "latest_production": latest_prod,
            "scenarios": scenarios
        }

chile_decline = estimate_chile_decline(df, method=chile_decline_assumption, horizon=horizon_years)
```

## Step 5: 估算替代國增量潛力

```python
def estimate_replacement_capacity(hist_increment, multiplier=1.0):
    """
    基於歷史增速估算未來增量潛力

    Parameters:
    -----------
    hist_increment : dict
        compute_historical_increment 的輸出
    multiplier : float
        調整係數（考慮執行風險、產能上限等）

    Returns:
    --------
    dict with expected_increment, assumptions
    """
    # 使用歷史 CAGR 外推
    base_cagr = hist_increment["cagr"]
    latest_prod = hist_increment["end_production"]

    # 假設未來維持相同增速（可調整）
    future_prod = latest_prod * (1 + base_cagr) ** horizon_years
    expected_increment = (future_prod - latest_prod) * multiplier

    return {
        "country": hist_increment["country"],
        "historical_cagr": base_cagr,
        "latest_production": latest_prod,
        "expected_increment": expected_increment,
        "multiplier": multiplier,
        "assumptions": [
            f"基於 {hist_increment['period']} 歷史增速 ({base_cagr:.1%}/年)",
            f"執行調整係數 {multiplier}",
            f"未考慮產能天花板"
        ]
    }

peru_capacity = estimate_replacement_capacity(peru_hist, multiplier=0.8)
drc_capacity = estimate_replacement_capacity(drc_hist, multiplier=0.7)
```

## Step 6: 計算替代依賴度

```python
def compute_replacement_ratio(chile_decline, peru_capacity, drc_capacity):
    """
    計算替代依賴度

    replacement_ratio = (秘魯增量 + DRC增量) / 智利缺口
    """
    if chile_decline["method"] == "scenario":
        # 多情境計算
        results = []
        for scenario in chile_decline["scenarios"]:
            decline = scenario["expected_decline"]
            peru_inc = peru_capacity["expected_increment"]
            drc_inc = drc_capacity["expected_increment"]

            ratio = (peru_inc + drc_inc) / max(decline, 1)  # 避免除以 0

            results.append({
                "scenario": scenario["name"],
                "chile_decline": decline,
                "peru_increment": peru_inc,
                "drc_increment": drc_inc,
                "total_replacement": peru_inc + drc_inc,
                "replacement_ratio": ratio,
                "gap": decline - (peru_inc + drc_inc)
            })
        return results

    else:
        decline = chile_decline["expected_decline"]
        peru_inc = peru_capacity["expected_increment"]
        drc_inc = drc_capacity["expected_increment"]

        ratio = (peru_inc + drc_inc) / max(decline, 1)
        gap = decline - (peru_inc + drc_inc)

        return {
            "chile_decline": decline,
            "peru_increment": peru_inc,
            "drc_increment": drc_inc,
            "total_replacement": peru_inc + drc_inc,
            "replacement_ratio": ratio,
            "gap": gap,
            "interpretation": interpret_ratio(ratio)
        }

def interpret_ratio(ratio):
    if ratio < 0.8:
        return "嚴重不足 - 供應缺口將擴大"
    elif ratio < 1.0:
        return "略有不足 - 缺口需其他來源填補"
    elif ratio < 1.2:
        return "剛好填補 - 但風險集中於兩國"
    else:
        return "有餘裕 - 但需考慮執行風險"

replacement_result = compute_replacement_ratio(chile_decline, peru_capacity, drc_capacity)
```

## Step 7: 風險因素分析

```python
def assess_replacement_risks():
    """評估秘魯與DRC的替代風險因素"""
    return {
        "Peru": {
            "political_risk": {
                "level": "中",
                "factors": ["社會衝突頻繁", "礦業稅制不穩定", "社區抗議"]
            },
            "operational_risk": {
                "level": "中",
                "factors": ["水資源限制", "高海拔作業", "基礎設施瓶頸"]
            },
            "track_record": {
                "recent_disruptions": ["2023 年多次罷工", "Las Bambas 衝突持續"],
                "production_volatility": "高"
            }
        },
        "DRC": {
            "political_risk": {
                "level": "高",
                "factors": ["政治不穩定", "武裝衝突", "礦權爭議"]
            },
            "operational_risk": {
                "level": "高",
                "factors": ["電力供應不穩", "物流困難", "ESG爭議"]
            },
            "track_record": {
                "recent_disruptions": ["Mutanda 礦山關閉", "政府審查礦權"],
                "production_volatility": "極高"
            }
        }
    }
```

## Step 8: 生成視覺化圖表

```bash
python scripts/visualize_analysis.py --mode=replacement
```

**生成的圖表**：
1. `copper_replacement_bars_YYYYMMDD.png` - 智利缺口 vs 替代增量柱狀圖
2. `copper_country_growth_YYYYMMDD.png` - 三國產量增長對比
3. `copper_replacement_ratio_YYYYMMDD.png` - 替代依賴度指標

## Step 9: 輸出結果

**JSON 輸出：**

```json
{
  "commodity": "copper",
  "analysis_type": "replacement_dependency",
  "period": {
    "historical": "2010-2023",
    "projection": "2023-2033"
  },
  "chile_decline": {
    "method": "trend",
    "expected_decline_mt": 0.82,
    "slope_t_per_year": -47000
  },
  "replacement_capacity": {
    "Peru": {
      "expected_increment_mt": 0.52,
      "historical_cagr": 0.042,
      "multiplier": 0.8
    },
    "DRC": {
      "expected_increment_mt": 0.61,
      "historical_cagr": 0.089,
      "multiplier": 0.7
    }
  },
  "replacement_ratio": 0.88,
  "gap_mt": 0.11,
  "interpretation": "略有不足 - 缺口需其他來源填補",
  "risk_assessment": {
    "Peru": "中",
    "DRC": "高"
  },
  "data_sources": ["OWID Minerals"],
  "generated_at": "2026-01-24"
}
```

**Markdown 報告：**

```markdown
## 秘魯與DRC替代依賴度分析

### 執行摘要

若智利產量延續當前趨勢，未來 {horizon} 年預期減產 {chile_decline:.2f} Mt。
秘魯與DRC合計可提供 {total_replacement:.2f} Mt 增量，
替代依賴度（replacement_ratio）為 **{ratio:.2f}**。

**判定**：{interpretation}

### 歷史產量增量（近 {n_years} 年）

| 國家 | 起始產量 | 最新產量 | 增量 | CAGR |
|------|----------|----------|------|------|
| 智利 | {chile_start} Mt | {chile_end} Mt | {chile_inc:+} Mt | {chile_cagr:.1%} |
| 秘魯 | {peru_start} Mt | {peru_end} Mt | {peru_inc:+} Mt | {peru_cagr:.1%} |
| DRC | {drc_start} Mt | {drc_end} Mt | {drc_inc:+} Mt | {drc_cagr:.1%} |

### 未來預測（{horizon} 年）

| 項目 | 數量 | 說明 |
|------|------|------|
| 智利預期減產 | {chile_decline:.2f} Mt | 延續趨勢斜率 {slope:+,.0f} t/年 |
| 秘魯預期增量 | {peru_inc:.2f} Mt | CAGR {peru_cagr:.1%}，執行係數 0.8 |
| DRC 預期增量 | {drc_inc:.2f} Mt | CAGR {drc_cagr:.1%}，執行係數 0.7 |
| **淨缺口** | {gap:.2f} Mt | 需其他來源填補 |

### 替代依賴度解讀

**replacement_ratio = {ratio:.2f}**

- < 0.8：嚴重不足，供應缺口將擴大
- 0.8-1.0：略有不足，需其他來源
- 1.0-1.2：剛好填補，但風險集中
- > 1.2：有餘裕，但需考慮執行風險

### 風險因素

**秘魯**：
- 政治風險：{peru_political}
- 主要因素：社會衝突、礦業稅制、社區抗議
- 近期事件：2023 年多次罷工、Las Bambas 衝突

**DRC**：
- 政治風險：{drc_political}
- 主要因素：政治不穩定、武裝衝突、ESG爭議
- 近期事件：Mutanda 關閉、政府審查礦權

### 含義

1. 即使 ratio ≈ 1，風險仍集中於兩個高風險國家
2. 秘魯與 DRC 的執行風險可能導致實際增量低於預期
3. 建議關注其他替代來源（印尼、蒙古、贊比亞）

### 數據來源

- OWID Minerals Explorer
- 口徑：mined copper content
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 計算三國歷史產量增量與 CAGR
- [ ] 估算智利未來缺口
- [ ] 估算秘魯/DRC 增量潛力（含執行係數調整）
- [ ] 計算 replacement_ratio
- [ ] 包含風險因素評估
- [ ] 輸出 JSON + Markdown 格式
</success_criteria>
