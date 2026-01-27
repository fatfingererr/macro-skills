# Markdown 報告模板

本文件定義技能的 Markdown 輸出格式，供人類閱讀。

---

## 報告結構

```markdown
# 殖利率利差 → 板塊相對報酬 預測報告

**生成時間**：{generated_at}
**數據截止**：{as_of_date}

---

## TL;DR（一句話結論）

{summary}

---

## 當前利差狀態

| 指標               | 數值      | 解讀                 |
|--------------------|-----------|----------------------|
| 2Y-10Y 殖利率利差  | {spread}% | {spread_interpretation} |
| 歷史分位數         | {spread_percentile}% | {percentile_interpretation} |
| 近 3 個月變化      | {spread_3m_change}% | {trend_interpretation} |

**趨勢判斷**：{spread_trend}

---

## 領先關係驗證

### 模型設定

- **模型類型**：{model_type}
- **領先期**：{lead_months} 個月
- **回測期間**：{lookback_years} 年（{date_range}）

### 模型結果

| 指標         | 數值    | 解讀                           |
|--------------|---------|--------------------------------|
| 相關係數     | {corr}  | {corr_interpretation}          |
| R²           | {r_sq}  | spread 解釋約 {r_sq_pct}% 變異 |
| Beta 係數    | {beta}  | {beta_interpretation}          |
| p-value      | {p_val} | {significance_interpretation}  |

### 穩定性驗證

| 子樣本       | 期間                 | 相關係數 |
|--------------|----------------------|----------|
| 前半段       | {first_half_period}  | {first_half_corr} |
| 後半段       | {second_half_period} | {second_half_corr} |

**一致性判斷**：{consistency}

---

## 預測結果

### 未來 {horizon_months} 個月相對報酬預測

| 指標                 | 數值                        |
|----------------------|-----------------------------|
| 點估計（QQQ 相對 XLV） | {future_rel_return_pct}%  |
| {confidence_level}% 區間 | [{interval_lo}%, {interval_hi}%] |
| XLV 跑贏機率         | {defensive_outperform_prob}% |

### 解讀

{interpretation}

---

## 領先掃描結果

（若執行）

| 領先期（月） | 相關係數 | 備註     |
|--------------|----------|----------|
| 6            | {corr_6} |          |
| 12           | {corr_12}|          |
| 18           | {corr_18}|          |
| 24           | {corr_24}| ← 最佳   |
| 30           | {corr_30}|          |

**最佳領先期**：{best_lead_months} 個月

---

## 風險提示

1. **統計限制**：R² 僅 {r_sq}，spread 不是主導因子
2. **歷史不保證未來**：領先關係可能因政策框架變化而失效
3. **區間寬度**：{interval_lo}% 到 {interval_hi}% 跨度大，方向有不確定性
4. **數據挖掘風險**：最佳領先期可能是過度擬合結果

---

## 後續研究建議

### 若預測 XLV 跑贏

- [ ] 檢查經濟領先指標（ISM、消費者信心）
- [ ] 觀察 Healthcare 防禦需求
- [ ] 評估成長股估值分位

### 若預測 QQQ 跑贏

- [ ] 檢查經濟復甦訊號
- [ ] 觀察科技股資金流入
- [ ] 評估利率對估值影響

### 通用驗證

- [ ] 比較其他利差組合（3M-10Y, 2Y-30Y）
- [ ] 檢查 COT 持倉（利率期貨）
- [ ] 3 個月後重新驗證

---

## 圖表

（若生成）

![利差與相對報酬對齊圖]({chart_path})

---

## 數據來源

| 數據         | 來源         | 代碼        |
|--------------|--------------|-------------|
| 短端殖利率   | FRED         | {short_code}|
| 長端殖利率   | FRED         | {long_code} |
| 成長股價格   | Yahoo Finance| {risk_ticker}|
| 防禦股價格   | Yahoo Finance| {defensive_ticker}|

---

## 免責聲明

本報告僅供參考，不構成投資建議。歷史統計規律不保證未來表現。投資決策應結合多種因素並諮詢專業顧問。
```

---

## 欄位填充說明

| 佔位符                     | 來源                              | 範例               |
|----------------------------|-----------------------------------|--------------------|
| {generated_at}             | 報告生成時間                      | 2026-01-27 10:30   |
| {as_of_date}               | current_state.as_of_date          | 2026-01-24         |
| {summary}                  | summary 欄位                      | 見範例             |
| {spread}                   | current_state.spread              | -0.35              |
| {spread_percentile}        | current_state.spread_percentile   | 35                 |
| {spread_3m_change}         | current_state.spread_3m_change    | +0.25              |
| {spread_trend}             | current_state.spread_trend        | steepening         |
| {model_type}               | model.type                        | lagged_regression  |
| {lead_months}              | inputs.lead_months                | 24                 |
| {lookback_years}           | inputs.lookback_years             | 12                 |
| {corr}                     | model.fit_quality.corr_x_y        | -0.32              |
| {r_sq}                     | model.fit_quality.r_squared       | 0.10               |
| {beta}                     | model.coefficients.beta           | -0.45              |
| {future_rel_return_pct}    | forecast.future_relative_return.pct | -7.7             |
| {interval_lo}              | forecast.interval.pct[0]          | -22                |
| {interval_hi}              | forecast.interval.pct[1]          | +4                 |
| {defensive_outperform_prob}| forecast.direction.defensive_outperform_prob | 70    |
| {chart_path}               | artifacts[0].path                 | output/xxx.png     |

---

## 解讀文字生成規則

### spread_interpretation

```python
if spread > 0:
    return "曲線倒掛（短端高於長端）"
elif spread > -0.5:
    return "曲線輕微倒掛"
else:
    return "曲線正常（短端低於長端）"
```

### percentile_interpretation

```python
if percentile < 20:
    return "處於歷史低位"
elif percentile < 40:
    return "處於歷史中等偏低"
elif percentile < 60:
    return "處於歷史中位"
elif percentile < 80:
    return "處於歷史中等偏高"
else:
    return "處於歷史高位"
```

### corr_interpretation

```python
corr_abs = abs(corr)
direction = "負" if corr < 0 else "正"
if corr_abs > 0.5:
    strength = "較強"
elif corr_abs > 0.3:
    strength = "中等"
else:
    strength = "較弱"
return f"{strength}{direction}相關"
```

### beta_interpretation

```python
if beta < 0:
    return f"spread 每上升 1%，未來相對報酬預期下降 {abs(beta):.2f}%"
else:
    return f"spread 每上升 1%，未來相對報酬預期上升 {beta:.2f}%"
```
