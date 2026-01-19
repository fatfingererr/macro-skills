---
name: demographic-fiscal-trap-analyzer
description: 分析人口老化、債務動態、官僚膨脹與通膨稀釋交互作用下的「財政陷阱」風險，量化各國/地區的財政脆弱度並識別潛在的貨幣稀釋路徑
---

<essential_principles>

<principle name="fiscal_trap_definition">
**財政陷阱定義**

「人口-財政陷阱」(Demographic-Fiscal Trap) 是指：當高齡化撫養比持續攀升、政府債務/GDP 居高不下、官僚體系低效膨脹、且名義成長無法覆蓋利息支出時，政府傾向透過「金融抑制」(financial repression) 或「通膨稀釋」(inflation erosion) 來削減實質負債。

此陷阱的核心特徵：
1. **人口結構剛性**：老年撫養比上升是不可逆的長期趨勢
2. **債務自我強化**：r > g 時債務比率自動膨脹
3. **政治阻力**：削減福利支出的政治成本極高
4. **貨幣出口**：當財政改革無路可走，貨幣稀釋成為「最小阻力路徑」
</principle>

<principle name="four_pillar_framework">
**四支柱分析架構**

本技能採用四維度評分框架：

| 支柱 | 權重(預設) | 核心指標 |
|------|-----------|----------|
| 老化壓力 (Aging Pressure) | 35% | 老年撫養比水準 + 10年斜率 |
| 債務動態 (Debt Dynamics) | 35% | 債務/GDP + 5年斜率 + (r-g) |
| 官僚膨脹 (Bloat Index) | 15% | 政府消費/GDP + 政府支出/GDP |
| 成長拖累 (Growth Drag) | 15% | 名義GDP成長率（負向計分）|

最終 `fiscal_trap_score` = Σ(權重 × z-score) 加權總和
</principle>

<principle name="inflation_incentive">
**通膨激勵指數**

通膨激勵指數 (Inflation Incentive Score) 衡量政府選擇「通膨稀釋」路徑的動機強度：

```
inflation_incentive =
    0.40 × zscore(debt_level)           # 高債務 → 強動機
  + 0.20 × zscore(r - g)                # r > g → 難以自然去槓桿
  + 0.20 × zscore(neg_real_rate_share)  # 負實質利率持續 → 已在執行
  + 0.20 × zscore(bloat_index)          # 高官僚膨脹 → 難以削減支出
```

當此指數 > 1.5 時，表示該經濟體有強烈動機維持負實質利率環境。
</principle>

<principle name="data_hierarchy">
**資料來源層級**

本技能採用公開可重現的資料源：

| 資料類型 | 首選來源 | 次選來源 | API/下載方式 |
|----------|----------|----------|--------------|
| 撫養比 | World Bank WDI | UN WPP | API / CSV |
| 政府債務 | IMF WEO | World Bank | API / CSV |
| 政府支出 | IMF GFS | World Bank | API / CSV |
| 健康支出 | WHO GHED | World Bank | API / CSV |
| 名義GDP成長 | World Bank | IMF WEO | API |
| CPI通膨 | World Bank | IMF | API |
| 10年公債殖利率 | OECD / 各國央行 | Trading Economics | API / 爬蟲 |

所有指標均可透過 `wbdata`、`imfpy` 或直接 API 取得。
</principle>

<principle name="zscore_normalization">
**Z-Score 標準化**

為使跨國比較有意義，所有原始指標均轉換為 z-score：

```python
zscore(x) = (x - μ_cross_section) / σ_cross_section
```

其中 μ 和 σ 為同期跨國截面統計量。

這使得：
- z > 1.5 → 顯著高於平均（警戒）
- z > 2.0 → 極端值（紅燈）
- z < -1.0 → 顯著優於平均
</principle>

<principle name="quadrant_classification">
**象限分類系統**

根據 Aging Pressure 和 Debt Dynamics 兩主軸，將經濟體分為四象限：

| 象限 | 老化壓力 | 債務動態 | 典型國家 | 政策空間 |
|------|----------|----------|----------|----------|
| Q1: 雙高危機 | 高 (>1) | 高 (>1) | 日本、義大利、希臘 | 極窄 |
| Q2: 老化主導 | 高 (>1) | 低 (<1) | 德國、南韓 | 中等（債務可用） |
| Q3: 債務主導 | 低 (<1) | 高 (>1) | 美國、巴西 | 中等（人口紅利） |
| Q4: 相對健康 | 低 (<1) | 低 (<1) | 印度、印尼 | 寬廣 |

Q1 象限國家最可能進入「財政陷阱」並選擇通膨稀釋路徑。
</principle>

</essential_principles>

<objective>
本技能的目標是：

1. **量化財政脆弱度**：計算各國/地區的 `fiscal_trap_score` 與 `inflation_incentive_score`
2. **識別結構風險**：透過四支柱分解，診斷哪個維度貢獻最大風險
3. **象限定位**：將經濟體歸類至四象限，判斷其政策空間
4. **趨勢預警**：利用撫養比預測至 2050 年，前瞻性評估陷阱演化
5. **跨國比較**：支援多國並排比較，識別相對風險排序
</objective>

<quick_start>
## 快速開始

**單一國家分析**
```
請分析日本的人口-財政陷阱風險，使用 2010-2023 年資料，預測至 2050 年
```

**多國比較**
```
比較 G7 國家的財政陷阱分數，並按通膨激勵指數排序
```

**自訂權重**
```
分析台灣的財政陷阱，使用自訂權重：老化 40%、債務 40%、膨脹 10%、成長 10%
```
</quick_start>

<parameters>
## 參數說明

| 參數 | 型別 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| entities | list[string] | 是 | - | 國家/地區代碼 (ISO3 或區域如 OECD, EU, WORLD) |
| start_year | int | 是 | - | 歷史資料起始年 |
| end_year | int | 是 | - | 歷史資料結束年（通常=最近一年） |
| forecast_end_year | int | 否 | 2050 | 撫養比預測結束年 |
| dependency_components | list[string] | 否 | ["old_age","youth","total"] | 撫養比分解項目 |
| fiscal_modules | list[string] | 否 | ["debt","spending","health"] | 啟用的財政模組 |
| bureaucracy_proxies | list[string] | 否 | ["gov_wage_bill","public_employment_share","gov_consumption"] | 官僚膨脹代理指標 |
| inflation_channel | string | 否 | "real_rates" | 通膨路徑分析方式 |
| weights | dict | 否 | {"aging":0.35,"debt":0.35,"bloat":0.15,"growth_drag":0.15} | 各支柱權重 |
</parameters>

<workflows_overview>
## 可用工作流

1. **full-analysis.md** - 完整分析：執行所有模組並產出綜合報告
2. **debt-dynamics.md** - 債務動態專題：深入分析 r-g 缺口與債務軌跡
3. **aging-projection.md** - 老化投影：撫養比預測與財政壓力前瞻
4. **cross-country.md** - 跨國比較：多國並排評分與排名
5. **inflation-path.md** - 通膨路徑：分析負實質利率持續性與貨幣稀釋動機
</workflows_overview>

<interpretation_guide>
## 結果解讀指南

### Fiscal Trap Score 解讀
| 分數區間 | 風險等級 | 建議關注 |
|----------|----------|----------|
| < 0 | 低風險 | 財政健全，政策空間充裕 |
| 0 - 1 | 中等風險 | 需監控特定支柱惡化 |
| 1 - 2 | 高風險 | 結構性問題顯著，改革窗口收窄 |
| > 2 | 極高風險 | 財政陷阱風險極高，通膨稀釋概率上升 |

### Inflation Incentive Score 解讀
| 分數區間 | 政策傾向 | 對資產配置意涵 |
|----------|----------|----------------|
| < 0.5 | 正統財政 | 名義債券相對安全 |
| 0.5 - 1.5 | 溫和金融抑制 | 實質報酬承壓 |
| > 1.5 | 強烈稀釋動機 | 應考慮通膨保值資產 |
</interpretation_guide>
