---
name: us-cpi-pce-comparator
displayName: 美國 CPI/PCE 通膨比較器
description: 自動比較美國 CPI（固定權重）與 PCE（動態權重）的通膨訊號，識別低波動高權重桶位的 PCE 上行風險。用於分析 Fed 關注的 PCE 是否正在 re-accelerate，即使 CPI 看似降溫。
emoji: "\U0001F4CA"
version: v0.1.0
license: MIT
author: Ricky Wang
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - CPI
  - PCE
  - 通貨膨脹
  - 美聯儲
  - 權重差異
  - FRED
  - BLS
  - 風險訊號
  - 宏觀經濟
category: inflation-analytics
dataLevel: free-nolimit
tools:
  - claude-code
featured: false
installCount: 0
testQuestions:
  - question: '分析當前 CPI 與 PCE 的分歧情況'
    expectedResult: |
      此分析器會：
      1. 從 FRED 抓取最新 CPI 和 PCE 數據
      2. 計算 headline 層級的 YoY 分歧（bps）
      3. 識別低波動高權重桶位的風險訊號
      4. 輸出結構化 JSON 結果
  - question: '為什麼 PCE 比 CPI 更高？Fed 關注哪個指標？'
    expectedResult: |
      解釋 CPI/PCE 五大差異：
      - 權重方法（固定 vs 動態）
      - 涵蓋範圍（PCE 更廣）
      - 公式差異
      - 住房計算
      - 人口覆蓋
qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 80
    maintainability: 80
    content: 85
    community: 20
    security: 95
    compliance: 85
  details: |
    **架構（80/100）**
    - 清晰的三層訊號架構
    - 模組化腳本設計
    - 無需 API key 的數據獲取

    **可維護性（80/100）**
    - 工作流程分離清晰
    - 參數定義完整
    - 多數據源支援

    **內容（85/100）**
    - 完整的方法論文檔
    - CPI/PCE 差異深度解析
    - 實用的 CLI 工具

    **社區（20/100）**
    - 新技能，尚無社區貢獻

    **安全（95/100）**
    - 僅讀取公開經濟數據
    - 無需 API key

    **規範符合性（85/100）**
    - 遵循 Claude Code 規範
    - 完整的文件結構

bestPractices:
  - title: 關注 Core 而非 Headline
    description: Core CPI/PCE 排除食品與能源，更能反映趨勢性通膨
  - title: 使用 3M SAAR 觀察動量
    description: YoY 有滯後性，3 個月 SAAR 更能捕捉拐點
  - title: 理解權重效應
    description: PCE 動態權重會自動降低高通膨項目的權重（替代效應）
  - title: 結合兩個指標
    description: CPI 反映消費者體感，PCE 是 Fed 目標，兩者都重要

pitfalls:
  - title: 只看 Headline
    description: Headline 受能源價格波動影響大
    consequence: 錯過核心通膨趨勢
  - title: 忽略權重差異
    description: CPI/PCE 在醫療、住房等項目權重差異顯著
    consequence: 無法解釋分歧來源
  - title: 過度解讀單月數據
    description: 月度數據波動大，容易被噪音誤導
    consequence: 錯誤判斷通膨趨勢

faq:
  - question: Fed 主要看哪個通膨指標？
    answer: |
      Fed 的 2% 目標是針對 **Core PCE YoY**。
      但 Fed 也關注 CPI，因為它是市場預期的錨定點。

  - question: 為什麼 PCE 通常比 CPI 低？
    answer: |
      主要原因：
      1. PCE 動態權重會因替代效應自動降低高通膨項目權重
      2. PCE 包含第三方支付的醫療，這部分通膨通常較溫和
      3. PCE 住房權重較低（約 15% vs CPI 約 33%）

  - question: 如何判斷 PCE 是否在 re-accelerate？
    answer: |
      觀察指標：
      1. 3M SAAR 是否高於 YoY
      2. 低波動高權重桶位是否出現加速
      3. Core Services ex-Housing 是否持續偏高

about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 數據來源

    **FRED（免費，無需 API key）**
    - CPI: CPIAUCSL, CPILFESL
    - PCE: PCEPI, PCEPILFE
    - 使用 CSV endpoint 直接下載

    **BLS Public API**
    - 詳細 CPI 分項數據
    - 權重與相對重要性
---

<essential_principles>

<principle name="weight_difference">
**CPI vs PCE 權重差異是核心**

- **CPI（固定權重）**: BLS Relative Importance，每年或每兩年更新，反映「固定籃子」
- **PCE（動態/鏈結權重）**: BEA 名目支出占比，每月隨實際消費行為調整

關鍵洞見：當消費者把錢花在「價格較不波動」的品項時，若這些品項的通膨走高，PCE 會比 CPI 更敏感地反映這個上行壓力。
</principle>

<principle name="volatility_matters">
**低波動 + 高權重 = PCE 上行風險訊號**

識別邏輯：
1. 找出 PCE 權重較高的消費桶（consumer spending buckets）
2. 在這些桶中，篩選價格波動度較低者
3. 若這些桶的通膨近期轉正或加速，標記為 PCE upside risk
</principle>

<principle name="scope_difference">
**CPI 與 PCE 的範圍差異**

PCE 涵蓋項目比 CPI 更廣：
- 第三方支付的醫療費用（employer-paid healthcare）
- 非營利機構對家庭的服務
- 某些金融服務的隱含費用

這些 scope 差異也會造成 CPI/PCE 分歧。詳見 `references/cpi-pce-methodology.md`。
</principle>

<principle name="data_access">
**資料取得方式**

本 skill 使用**無需 API key** 的資料來源：
- **FRED CSV**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}`
- **BLS Public API**: `https://api.bls.gov/publicAPI/v2/timeseries/data/`

腳本位於 `scripts/` 目錄，可直接執行。
</principle>

</essential_principles>

<objective>
比較 CPI 與 PCE 通膨訊號的分歧，並識別「低波動、高 PCE 權重」的消費桶是否正在推升 Fed 關注的 PCE 通膨路徑。

輸出三層訊號：
1. **Headline level**: CPI vs PCE divergence（bps）
2. **Attribution**: 哪些 buckets 在推升 PCE（weighted contribution）
3. **Risk framing**: 觀察點與延續性風險評估
</objective>

<quick_start>

**最快的方式：執行快速檢查**

```bash
cd skills/us-cpi-pce-comparator
pip install pandas numpy requests  # 首次使用
python scripts/cpi_pce_analyzer.py --quick
```

輸出範例：
```json
{
  "headline": {"cpi_yoy": 2.65, "pce_yoy": 2.79, "gap_bps": 14},
  "core": {"cpi_core_yoy": 2.65, "pce_core_yoy": 2.83, "gap_bps": 18},
  "momentum": {"cpi_3m_saar": 2.07, "pce_3m_saar": 2.82}
}
```

**完整分析**：
```bash
python scripts/cpi_pce_analyzer.py --start 2020-01-01 --measure yoy
```

</quick_start>

<intake>
需要進行什麼分析？

1. **快速檢查** - 查看最新的 CPI/PCE 分歧數據
2. **完整分析** - 執行完整的三步驟分析工作流
3. **方法論學習** - 了解 CPI/PCE 差異的深層原因

**請選擇或直接提供分析參數。**
</intake>

<routing>
| Response                     | Action                                            |
|------------------------------|---------------------------------------------------|
| 1, "快速", "quick", "check"  | 執行 `python scripts/cpi_pce_analyzer.py --quick` |
| 2, "完整", "full", "analyze" | 閱讀 `workflows/analyze.md` 並執行                |
| 3, "學習", "方法論", "why"   | 閱讀 `references/cpi-pce-methodology.md`          |
| 提供參數 (如日期範圍)        | 閱讀 `workflows/analyze.md` 並使用參數執行        |

**路由後，閱讀對應文件並執行。**
</routing>

<directory_structure>
```
us-cpi-pce-comparator/
├── SKILL.md                           # 本文件（路由器）
├── workflows/
│   ├── analyze.md                     # 完整分析工作流
│   └── quick-check.md                 # 快速檢查工作流
├── references/
│   ├── data-sources.md                # FRED/BLS 系列代碼與資料來源
│   ├── cpi-pce-methodology.md         # CPI/PCE 方法論深度解析
│   └── implementation.md              # 計算公式與程式碼範例
├── templates/
│   ├── output-json.md                 # JSON 輸出模板
│   └── output-markdown.md             # Markdown 報告模板
└── scripts/
    ├── fetch_fred_data.py             # FRED 資料抓取（無需 API key）
    ├── fetch_bls_data.py              # BLS 資料抓取
    └── cpi_pce_analyzer.py            # 主分析腳本
```
</directory_structure>

<reference_index>

**方法論**: references/cpi-pce-methodology.md
- CPI vs PCE 的五大差異（權重、範圍、公式、住房、人口）
- 分歧模式與交易含義
- Fed 如何解讀兩指標

**資料來源**: references/data-sources.md
- FRED CSV endpoint（無需 API key）
- FRED 系列代碼對照表
- 桶位定義與近似計算

**實作指南**: references/implementation.md
- 通膨計算公式（YoY, MoM SAAR, QoQ SAAR）
- 權重效應計算
- 波動度分析

</reference_index>

<workflows_index>
| Workflow       | Purpose        | 使用時機           |
|----------------|----------------|--------------------|
| analyze.md     | 完整三步驟分析 | 需要深度分析時     |
| quick-check.md | 快速檢查分歧   | 日常監控或快速回答 |
</workflows_index>

<templates_index>
| Template           | Purpose           |
|--------------------|-------------------|
| output-json.md     | JSON 輸出結構定義 |
| output-markdown.md | Markdown 報告模板 |
</templates_index>

<scripts_index>
| Script              | Command                      | Purpose           |
|---------------------|------------------------------|-------------------|
| cpi_pce_analyzer.py | `--quick`                    | 快速檢查最新分歧  |
| cpi_pce_analyzer.py | `--start DATE --measure yoy` | 完整分析          |
| fetch_fred_data.py  | `--series CPIAUCSL,PCEPI`    | 抓取 FRED 資料    |
| fetch_bls_data.py   | `--full`                     | 抓取 BLS CPI 資料 |
</scripts_index>

<input_schema>

<parameter name="start_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析起始日
</parameter>

<parameter name="end_date" required="false" default="today">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析結束日
</parameter>

<parameter name="measure" required="false" default="yoy">
**Type**: string
**Options**: `yoy` | `mom_saar` | `qoq_saar`
</parameter>

<parameter name="baseline" required="false">
**Type**: string
**Format**: `YYYY-MM-DD:YYYY-MM-DD`
**Description**: 基準期範圍，用於計算偏離度
</parameter>

</input_schema>

<output_schema>
參見 `templates/output-json.md` 的完整結構定義。

**摘要**：
```json
{
  "headline": {"cpi_yoy": 2.65, "pce_yoy": 2.79, "gap_bps": 14},
  "low_vol_high_weight_buckets": [{"bucket": "...", "signal": "upside"}],
  "attribution": {"top_contributors": [...], "weight_effect_bps": 12},
  "interpretation": ["..."],
  "caveats": ["..."]
}
```
</output_schema>

<success_criteria>
分析成功時應產出：

- [ ] Headline level 的 CPI/PCE 分歧數值（bps）
- [ ] 識別出低波動、高 PCE 權重的桶位
- [ ] 各桶位的加權通膨貢獻（attribution）
- [ ] 若有 baseline，產出「less baseline」偏離度
- [ ] 可操作的解讀與風險提示
- [ ] 明確標註資料限制與近似處理
</success_criteria>
