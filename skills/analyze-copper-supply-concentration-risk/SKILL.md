---
name: analyze-copper-supply-concentration-risk
description: 用公開資料量化「銅供應是否過度集中、主要產地是否結構性衰退、替代增量是否依賴少數國家」，並輸出可行的中期供應風險結論與情境推演。
---

<essential_principles>
**銅供應集中度風險分析 核心原則**

<principle name="narrative_to_metrics">
**敘事轉指標（Narrative to Metrics）**

市場敘事必須可量化驗證。五大命題對應五組指標：

| 命題 | 核心問題 | 量化指標 |
|------|----------|----------|
| A. 集中度 | 供應是否過度集中？ | HHI, CR4, CR8, 份額排名 |
| B. 結構衰退 | 智利是否結構性衰退？ | 趨勢斜率、斷點年、峰值回撤 |
| C. 替代依賴 | 是否依賴秘魯/DRC？ | replacement_ratio |
| D. 供應慣性 | 價格能快速帶來供應嗎？ | 10年lead time下的缺口 |
| E. 地緣風險 | 慢變量風險多大？ | geo_risk_z, system_risk |

**強制規則**：任何敘事主張必須對應至少一個指標，無指標支撐的結論標記為 `speculative`。
</principle>

<principle name="data_caliber_first">
**口徑先行（Data Caliber First）**

銅數據存在多種口徑，分析前必須明確：

| 口徑 | 說明 | 典型來源 |
|------|------|----------|
| `mined_production` | 礦場產量（銅金屬含量）- **本 Skill 預設** | OWID, USGS |
| `refined_production` | 精煉產量 | ICSG, USGS |
| `reserves` | 儲量（不等於可開採供應） | USGS |
| `ore_grades` | 礦石品位（%銅含量） | 礦業公司報告 |

**警告**：儲量大 ≠ 供應安全。智利儲量全球第一，但產量可能下滑。
</principle>

<principle name="concentration_metrics">
**集中度指標定義**

| 指標 | 公式 | 解讀 |
|------|------|------|
| HHI | `Σ (share_i × 100)²` | 0-10000，>2500 高集中 |
| CR4/CR8 | `Σ top_n_share` | 前 4/8 國份額加總 |
| Chile Share | `chile_prod / world_prod` | >25% 視為單點風險 |

**HHI 判讀**：
- < 1500：低集中（競爭市場）
- 1500-2500：中等集中
- > 2500：高集中（寡占市場）
</principle>

<principle name="structural_break_detection">
**結構斷點偵測（Structural Break Detection）**

智利產量趨勢分析使用三指標組合：

1. **Rolling Slope**：近 N 年趨勢斜率（t/年）
2. **Structural Break**：使用 Bai-Perron 或簡易雙線段回歸偵測轉折點
3. **Drawdown**：從峰值到現在的回撤幅度

**解讀規則**：
- slope < 0 + break_detected + drawdown > 10% → 結構性衰退
- slope ≈ 0 + no_break → 高原期
- slope > 0 → 仍在增長
</principle>

<principle name="replacement_ratio">
**替代依賴度（Replacement Ratio）**

衡量秘魯與 DRC 能否填補智利缺口：

```python
replacement_ratio = (expected_increment_peru + expected_increment_drc) / expected_chile_decline
```

**解讀**：
- < 1.0：替代不足，供應缺口擴大
- ≈ 1.0：剛好填補，但風險集中於兩國
- > 1.0：有餘裕，但需考慮兩國執行風險
</principle>

<principle name="supply_lead_time">
**供應反應時間（Supply Lead Time）**

新增大型礦場從發現到投產約需 10-15 年。在此約束下：

- **短期（0-3年）**：只能靠現有產能擴建
- **中期（3-7年）**：在建項目可釋放
- **長期（7-15年）**：新發現可開發

情境分析使用 `supply_lead_time_years` 參數（預設 10 年）約束可行增量。
</principle>

<principle name="data_tiering">
**數據分層策略（Data Tiering）**

| Tier | 特性 | 來源 | 用途 |
|------|------|------|------|
| 0 | 免費、穩定、長序列 | OWID Minerals, USGS | 主幹 baseline |
| 1 | 免費但分散 | 礦業公司年報 | mine-level 錨點 |
| 2 | 付費、更即時 | S&P Global, Wood Mac | 精度驗證 |
| 3 | 事件驅動 | GDELT, 新聞 | 地緣風險指數 |

**優先順序**：Tier 0 建立 baseline → Tier 1 補充細節 → Tier 2 驗證 → Tier 3 風險疊加
</principle>
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **Analyze** - 計算銅供應集中度指標與國家份額排名（HHI, CR4, CR8）
2. **Trend** - 分析智利產量結構性趨勢（斜率、斷點、峰值回撤）
3. **Replacement** - 評估秘魯/DRC 替代依賴度與缺口情境
4. **Scenario** - 模擬供需缺口與系統風險分數
5. **Full Report** - 完整五命題分析報告

**等待回應後再繼續。**
</intake>

<routing>
| Response | Workflow | Description |
|----------|----------|-------------|
| 1, "analyze", "concentration", "hhi", "集中度", "份額" | workflows/analyze-concentration.md | 集中度指標計算 |
| 2, "trend", "chile", "智利", "結構", "衰退", "斜率" | workflows/analyze-chile-trend.md | 智利產量趨勢分析 |
| 3, "replacement", "替代", "秘魯", "drc", "剛果" | workflows/analyze-replacement.md | 替代依賴度評估 |
| 4, "scenario", "情境", "缺口", "風險" | workflows/scenario-analysis.md | 供需缺口情境模擬 |
| 5, "full", "完整", "report", "五命題" | workflows/full-report.md | 完整五命題報告 |

**讀取工作流程後，請完全遵循其步驟。**
</routing>

<reference_index>
**參考文件** (`references/`)

| 文件 | 內容 |
|------|------|
| data-sources.md | 所有數據來源詳細說明與 URL |
| concentration-metrics.md | 集中度指標詳細計算方法 |
| chile-supply-dynamics.md | 智利銅供應結構與品位問題 |
| replacement-countries.md | 秘魯與 DRC 產能擴張分析 |
| geopolitics-risk.md | 地緣風險指數計算方法 |
| failure-modes.md | 失敗模式與緩解策略 |
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| analyze-concentration.md | 供應集中度指標計算（HHI, CR4, CR8） |
| analyze-chile-trend.md | 智利產量結構性趨勢分析 |
| analyze-replacement.md | 秘魯/DRC 替代依賴度評估 |
| scenario-analysis.md | 供需缺口與系統風險情境模擬 |
| full-report.md | 完整五命題分析報告 |
| ingest-data.md | 數據擷取與標準化 |
</workflows_index>

<templates_index>
| Template | Purpose |
|----------|---------|
| output-json.md | JSON 輸出結構模板 |
| output-markdown.md | Markdown 報告模板 |
| config.yaml | 分析參數配置模板 |
</templates_index>

<scripts_index>
| Script | Purpose |
|--------|---------|
| copper_pipeline.py | 核心數據管線與分析入口 |
| fetch_owid.py | OWID 銅產量數據擷取 |
| compute_concentration.py | 集中度指標計算 |
| compute_chile_trend.py | 智利趨勢與斷點分析 |
| compute_replacement.py | 替代依賴度計算 |
| scenario_engine.py | 情境模擬引擎 |
| visualize_analysis.py | 分析視覺化圖表生成 |
</scripts_index>

<quick_start>
**CLI 快速開始：**

```bash
# 分析 1970-2023 銅供應集中度
python scripts/copper_pipeline.py analyze --start=1970 --end=2023

# 分析智利產量趨勢與結構斷點
python scripts/copper_pipeline.py trend --country=Chile --window=10

# 計算秘魯/DRC 替代依賴度
python scripts/copper_pipeline.py replacement --horizon=10

# 完整五命題報告
python scripts/copper_pipeline.py full-report --start=1970 --end=2023 --output=markdown

# 生成視覺化圖表
python scripts/visualize_analysis.py
```

**Library 快速開始：**

```python
from copper_pipeline import CopperSupplyAnalyzer

analyzer = CopperSupplyAnalyzer(
    start_year=1970,
    end_year=2023,
    concentration_metric="HHI",
    structural_break=True,
    geopolitics_mode="gdelt"
)

# 計算集中度
result = analyzer.compute_concentration()
print(f"HHI (2023): {result['hhi_latest']:.0f}")
print(f"Chile share: {result['chile_share_latest']:.1%}")

# 完整報告
report = analyzer.generate_full_report(output_format="markdown")
```
</quick_start>

<input_schema>
**輸入參數定義**

```yaml
# 必要參數
start_year: int          # 分析起始年（例如 1970）
end_year: int            # 分析結束年（例如 2023）

# 選用參數
commodity: string        # 礦種，預設 "copper"
top_n_producers: int     # 前 N 大產銅國，預設 12
focus_countries:         # 重點國家清單
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

concentration_metric: string  # "HHI" | "CR4" | "CR8"，預設 "HHI"
structural_break: bool        # 是否做結構斷點偵測，預設 true
ore_grade_mode: string        # "none" | "country_proxy" | "mine_level"，預設 "country_proxy"

demand_scenarios:             # 需求情境（可多個）
  - name: string              # 情境名稱
    demand_cagr: float        # 需求年複合成長率
    horizon_years: int        # 預測年限

supply_lead_time_years: int   # 供應反應時間，預設 10
geopolitics_mode: string      # "none" | "gdelt" | "news_count"，預設 "gdelt"
output_format: string         # "markdown" | "json"，預設 "markdown"
```
</input_schema>

<success_criteria>
Skill 成功執行時：
- [ ] 正確計算集中度指標（HHI, CR4, CR8, 國家份額）
- [ ] 智利趨勢分析包含斜率、斷點、回撤三指標
- [ ] 替代依賴度計算 replacement_ratio
- [ ] 情境分析輸出供需缺口與系統風險分數
- [ ] 輸出包含數據來源與口徑說明
- [ ] 可回答五大命題對應的核心問題
</success_criteria>

<data_pipeline_architecture>
**數據流水線架構**

```
[Data Sources]
     |
     v
+-------------------+
|   fetch_owid      |  --> OWID Minerals (主要)
|   fetch_usgs      |  --> USGS MCS (驗證)
|   fetch_gdelt     |  --> GDELT Events (地緣)
+-------------------+
     |
     v
+-------------------+
|   normalize       |  --> 統一 schema + 單位標註
+-------------------+      (year, country, production, unit, source)
     |
     +-----+-----+-----+-----+
     |     |     |     |     |
     v     v     v     v     v
[命題A] [命題B] [命題C] [命題D] [命題E]
 集中度  智利趨勢 替代度  供應慣性 地緣風險
     |     |     |     |     |
     +-----+-----+-----+-----+
           |
           v
+-------------------+
|  insight_synthesis |  --> 系統風險分數
+-------------------+
     |
     v
+-------------------+
|   generate_output |  --> JSON + Markdown
+-------------------+
```

**標準化欄位 Schema：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| year | int | 年度 |
| country | string | 國家 |
| production | float | 產量（公噸） |
| unit | string | t_Cu_content（銅金屬含量） |
| source_id | string | OWID/USGS/Company |
| confidence | float | 來源品質評分 (0-1) |
</data_pipeline_architecture>
