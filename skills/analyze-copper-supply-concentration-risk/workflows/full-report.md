# Workflow: 完整五命題分析報告

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/concentration-metrics.md
3. references/chile-supply-dynamics.md
4. references/replacement-countries.md
5. references/geopolitics-risk.md
</required_reading>

<process>
## Step 1: 確認完整分析參數

收集或確認以下參數：

```yaml
# 必要參數
start_year: 1970
end_year: 2023

# 分析參數
commodity: "copper"
top_n_producers: 12
concentration_metric: "HHI"

focus_countries:
  - Chile
  - Peru
  - Democratic Republic of Congo
  - China
  - United States
  - Russia
  - Australia
  - Mexico
  - Kazakhstan
  - Canada

# 趨勢分析
structural_break: true
ore_grade_mode: "country_proxy"
rolling_window: 10

# 情境分析
demand_scenarios:
  - name: "base"
    demand_cagr: 0.03
    horizon_years: 10

supply_lead_time_years: 10

# 地緣風險
geopolitics_mode: "gdelt"

# 輸出
output_format: "markdown"  # markdown | json
```

## Step 2: 執行數據擷取

使用 Chrome CDP 方式從 MacroMicro 擷取數據：

**Step 2.1: 啟動 Chrome 調試模式**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"
```

**Step 2.2: 等待圖表完全載入**（約 35 秒）

**Step 2.3: 執行數據擷取**
```bash
python scripts/copper_pipeline.py ingest --start={start_year} --end={end_year}
```

等待數據擷取完成，確認：
- MacroMicro (WBMS) 銅產量數據已下載
- 數據已標準化為統一 schema

## Step 3: 執行命題 A - 集中度分析

調用 `workflows/analyze-concentration.md` 流程：

```python
from copper_pipeline import compute_concentration

concentration_result = compute_concentration(
    df=normalized_data,
    start_year=start_year,
    end_year=end_year,
    metric=concentration_metric,
    top_n=top_n_producers
)
```

**輸出要點**：
- HHI 最新值與 10 年前對比
- CR4, CR8 數值
- 智利份額與歷史分位數
- 時序趨勢

## Step 4: 執行命題 B - 智利趨勢分析

調用 `workflows/analyze-chile-trend.md` 流程：

```python
from copper_pipeline import compute_chile_trend

chile_trend = compute_chile_trend(
    df=normalized_data,
    country="Chile",
    rolling_window=rolling_window,
    structural_break=structural_break,
    ore_grade_mode=ore_grade_mode
)
```

**輸出要點**：
- 峰值年份與產量
- 近 N 年趨勢斜率
- 結構斷點年份
- 峰值回撤幅度
- 趨勢分類（structural_decline/plateau/growth）

## Step 5: 執行命題 C - 替代依賴度分析

調用 `workflows/analyze-replacement.md` 流程：

```python
from copper_pipeline import compute_replacement

replacement_result = compute_replacement(
    df=normalized_data,
    chile_decline=chile_trend["expected_decline"],
    replacement_countries=["Peru", "Democratic Republic of Congo"],
    horizon_years=10
)
```

**輸出要點**：
- 秘魯與 DRC 歷史增量
- 未來增量潛力估算
- replacement_ratio
- 缺口判定

## Step 6: 執行命題 D & E - 情境與風險分析

調用 `workflows/scenario-analysis.md` 流程：

```python
from copper_pipeline import run_scenario_analysis

scenario_result = run_scenario_analysis(
    baseline=baseline_data,
    demand_scenarios=demand_scenarios,
    supply_constraints=supply_model,
    geo_countries=focus_countries,
    geopolitics_mode=geopolitics_mode
)
```

**輸出要點**：
- 各情境供需缺口
- 地緣風險指數
- 系統風險分數

## Step 7: 綜合生成完整報告

整合所有分析結果，生成完整五命題報告：

```python
def generate_full_report(concentration, chile_trend, replacement, scenario, output_format):
    """
    生成完整五命題報告

    報告結構：
    1. 執行摘要
    2. 命題 A: 供應是否高度集中？
    3. 命題 B: 智利是否結構性衰退？
    4. 命題 C: 是否被迫依賴秘魯與 DRC？
    5. 命題 D: 價格能快速帶來供應嗎？
    6. 命題 E: 地緣風險有多大？
    7. 綜合結論與系統風險評估
    8. 數據來源與方法說明
    """
    pass
```

## Step 8: 生成視覺化圖表

```bash
python scripts/visualize_analysis.py --mode=full-report
```

**生成的圖表**：
1. `copper_concentration_summary_YYYYMMDD.png` - 集中度摘要儀表板
2. `copper_chile_trend_YYYYMMDD.png` - 智利趨勢分析
3. `copper_replacement_analysis_YYYYMMDD.png` - 替代依賴度分析
4. `copper_scenario_dashboard_YYYYMMDD.png` - 情境分析儀表板
5. `copper_system_risk_radar_YYYYMMDD.png` - 系統風險雷達圖

## Step 9: 輸出完整報告

**Markdown 報告結構：**

```markdown
# 銅供應「集中 + 失速 + 依賴」快速檢核（{start_year}-{end_year}）

## 執行摘要

本報告使用公開數據量化驗證市場常見的銅供應風險敘事。主要發現：

- **供應集中**：HHI {hhi:.0f}，市場結構為{market_structure}
- **智利失速**：產量趨勢斜率 {slope:+,.0f} t/年，{trend_classification}
- **替代依賴**：replacement_ratio = {ratio:.2f}，{dependency_interpretation}
- **供應慣性**：10 年 lead time 下，基準情境缺口 {gap:.1f} Mt
- **系統風險**：綜合分數 {system_risk:.1f}/100（{risk_interpretation}）

---

## 1) 供應是否高度集中？

> 推文主張：「只有 10-12 國有顯著產量，智利像 OPEC」

### 驗證結果

| 指標 | {end_year}年值 | 解讀 |
|------|----------------|------|
| HHI | {hhi:.0f} | {hhi_interpretation} |
| CR4 | {cr4:.1%} | 前四國控制{cr4:.1%}供應 |
| CR8 | {cr8:.1%} | 前八國控制{cr8:.1%}供應 |
| 智利份額 | {chile_share:.1%} | 高於{percentile:.0f}%歷史年份 |

### 國家份額排名（{end_year}年）

| 排名 | 國家 | 產量 (Mt) | 份額 | 累積份額 |
|------|------|-----------|------|----------|
{country_table}

### 時序趨勢

{concentration_trend_chart}

**含義**：供應更像「少數國家的系統性依賴」，不是分散式供應鏈。

---

## 2) 智利是「儲量大但供應不安全」嗎？

> 推文主張：「品位下滑 → 成本上升 → 產量衰退」

### 驗證結果

| 指標 | 數值 | 解讀 |
|------|------|------|
| 峰值年份 | {peak_year} | 產量達到 {peak_prod:.2f} Mt |
| 最新產量 | {latest_prod:.2f} Mt | 較峰值下滑 {drawdown:.1%} |
| 近 {window} 年斜率 | {slope:+,.0f} t/年 | {slope_interpretation} |
| 結構斷點 | {break_year} | 趨勢由升轉{break_direction} |

### 判定邏輯

- slope < 0 : {slope_check}
- structural_break detected : {break_check}
- drawdown > 10% : {drawdown_check}

**結論**：{chile_conclusion}

### 品位推斷（{ore_grade_mode} 模式）

{grade_inference}

**含義**：如果產量進入結構性停滯/下滑，單看儲量會高估供應安全。

---

## 3) 世界是否被迫依賴秘魯與 DRC 擴產？

> 推文主張：「near/medium term path 只能靠秘魯和剛果金」

### 驗證結果

| 項目 | 數量 | 說明 |
|------|------|------|
| 智利預期減產 | {chile_decline:.2f} Mt | 延續趨勢 |
| 秘魯預期增量 | {peru_inc:.2f} Mt | CAGR {peru_cagr:.1%}，執行係數 0.8 |
| DRC 預期增量 | {drc_inc:.2f} Mt | CAGR {drc_cagr:.1%}，執行係數 0.7 |
| **替代依賴度** | **{ratio:.2f}** | {ratio_interpretation} |
| **淨缺口** | {gap:.2f} Mt | 需其他來源填補 |

### 風險因素

| 國家 | 政治風險 | 主要因素 |
|------|----------|----------|
| 秘魯 | {peru_risk} | 社會衝突、礦業稅制、社區抗議 |
| DRC | {drc_risk} | 政治不穩定、武裝衝突、ESG爭議 |

**含義**：若 ratio < 1，兩國擴產不足補位；若 ≈1，仍需考慮兩國風險與執行難度。

---

## 4) 為何價格訊號不一定能快速解決缺口？

> 推文主張：「歷史上沒有銅短缺，但這次供應反應慢」

### 供應約束分析

**新增大型礦場供應反應時間**：約 {lead_time} 年

| 增量來源 | 預期增量 | 可行性 |
|----------|----------|--------|
| 現有產能擴建 | +{brownfield:.2f} Mt | 短期可行 |
| 在建項目 | +{construction:.2f} Mt | 中期釋放 |
| 新礦開發 | 受 lead time 約束 | 長期 |
| **供應天花板** | {ceiling:.2f} Mt | 10 年內上限 |

### 情境分析

| 情境 | 需求 CAGR | 10年後需求 | 供需缺口 | 嚴重程度 |
|------|-----------|------------|----------|----------|
| 經濟放緩 | 1.5% | {slow_demand:.1f} Mt | {slow_gap:.1f} Mt | {slow_severity} |
| 基準情境 | 3.0% | {base_demand:.1f} Mt | {base_gap:.1f} Mt | {base_severity} |
| 電氣化加速 | 5.0% | {elec_demand:.1f} Mt | {elec_gap:.1f} Mt | {elec_severity} |

**含義**：供應鏈反應慢，短期價格上漲不等於短期供給彈性。

---

## 5) 地緣政治為何是宏觀供應慢變量風險？

> 推文主張：「peace deal / insurgencies 被市場忽略」

### 地緣風險指數

| 國家 | 事件頻率 Z分數 | 風險等級 | 近期事件 |
|------|----------------|----------|----------|
| 智利 | {chile_z:.1f} | {chile_level} | 水資源爭議、原住民抗議 |
| 秘魯 | {peru_z:.1f} | {peru_level} | 多次罷工、Las Bambas 衝突 |
| DRC | {drc_z:.1f} | {drc_level} | Mutanda 關閉、政府審查礦權 |

*數據來源：GDELT 事件資料庫（近 12 個月）*

### 系統風險評估

**綜合分數：{system_risk:.1f}/100**

| 分項 | 分數 | 權重 |
|------|------|------|
| 集中度分數 | {conc_score:.1f} | HHI 標準化 |
| 依賴度分數 | {dep_score:.2f} | 1 - replacement_ratio |
| 地緣風險加權 | {geo_score:.2f} | 替代國風險加權 |

**解讀**：{system_interpretation}

**含義**：地緣政治是慢變量，市場常忽略，但會放大系統風險。

---

## 綜合結論

本分析驗證了以下五個命題：

| 命題 | 驗證結果 | 關鍵指標 |
|------|----------|----------|
| A. 供應高度集中 | {a_verdict} | HHI={hhi:.0f}, CR4={cr4:.1%} |
| B. 智利結構性衰退 | {b_verdict} | slope={slope:+,.0f}, drawdown={drawdown:.1%} |
| C. 依賴秘魯/DRC | {c_verdict} | ratio={ratio:.2f} |
| D. 供應反應慢 | {d_verdict} | 基準情境缺口={base_gap:.1f} Mt |
| E. 地緣風險被忽略 | {e_verdict} | system_risk={system_risk:.1f}/100 |

### 建議監控

1. 智利產量月度數據與主要礦區動態
2. 秘魯勞工談判與社區衝突
3. DRC 政治穩定性與礦權政策
4. 全球在建項目進度

---

## 數據來源與方法說明

### 數據來源

| 來源 | Tier | 用途 |
|------|------|------|
| MacroMicro (WBMS) | 0 | 主幹產量數據（唯一主要來源） |
| GDELT | 3 | 地緣風險事件 |

### 口徑說明

本分析使用 **mined copper content**（礦場產量的銅金屬含量）：
- ✅ 銅金屬含量（metric tonnes Cu）
- ❌ 非 ore tonnes（礦石噸數）
- ❌ 非 refined production（精煉產量）
- ❌ 非 reserves（儲量）

### 方法論

- 集中度：HHI = Σ (share × 100)²
- 趨勢分析：Rolling linear regression + breakpoint detection
- 替代依賴度：replacement_ratio = (秘魯增量 + DRC增量) / 智利缺口
- 系統風險：concentration × (1 + dependency) × (1 + geo_risk_weighted)

---

*報告生成時間：{generated_at}*
```
</process>

<success_criteria>
此 workflow 完成時：
- [ ] 完成數據擷取與標準化
- [ ] 完成命題 A 集中度分析
- [ ] 完成命題 B 智利趨勢分析
- [ ] 完成命題 C 替代依賴度分析
- [ ] 完成命題 D 供需缺口情境分析
- [ ] 完成命題 E 地緣風險與系統風險評估
- [ ] 生成完整五命題報告（Markdown 或 JSON）
- [ ] 包含所有視覺化圖表
- [ ] 包含數據來源與方法說明
</success_criteria>
