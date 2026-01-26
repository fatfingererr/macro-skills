---
name: analyze-jgb-insurer-superlong-flow
description: 從日本保險公司對長端/超長端 JGB 的淨買入(淨賣出) 時間序列，自動產出「本月是否創紀錄賣超、連續賣超月數、期間累積賣超」等結論。
---

# 分析日本保險公司超長債淨買賣流量 Skill

以 JSDA 公開數據驗證「保險公司長端需求崩潰、創紀錄賣超」等敘事，提供可複製的摘要（含 streak / record / 累積值）。

<essential_principles>

<principle name="jsda_data_source">
**核心數據來源：JSDA 投資人別交易統計**

日本證券業協會（JSDA）公開發布的「Trends in Bond Transactions (by investor type)」XLS 是唯一可公開下載、可重建的保險公司債券交易數據來源。

**數據特徵**：
- 頻率：月度
- 分類：投資人類型 × 天期桶
- 單位：十億日圓（¥B）或兆日圓（¥T）
- 延遲：約 T+1 個月

**注意**：Bloomberg 等終端的數據也是引用 JSDA，但經過加工。本 Skill 直接使用原始來源以確保可重建性。
</principle>

<principle name="maturity_bucket_mapping">
**天期桶口徑對齊（關鍵）**

新聞/圖表常見口徑不一致：

| 新聞用語   | JSDA 可能對應 | 說明                |
|------------|---------------|---------------------|
| 10+ years  | 10年以上      | 需確認是否有合併桶  |
| super-long | 超長端        | 通常指 20Y+ 或 30Y+ |
| long-term  | 長端          | 通常指 10Y 左右     |

**實作建議**：
1. 先讀取 JSDA XLS 的 sheet 結構，確認實際可用的天期桶
2. 若只有 long + super-long 分開，需詢問用戶是否要合併
3. 輸出時必須標註實際使用的口徑
</principle>

<principle name="net_purchases_definition">
**淨買入/淨賣出定義**

`net_purchases = 買入金額 - 賣出金額`

- 正值 = 淨買入（需求增加）
- 負值 = 淨賣出（需求減少 / 拋售）

**連續賣超（streak）**：從最近月份往回數，連續 `net_purchases < 0` 的月數。
</principle>

<principle name="record_detection">
**歷史極值判斷邏輯**

```
record_low = min(series[lookback_start : end_date])
is_record_sale = (latest == record_low) AND (latest < 0)
```

**注意事項**：
- `lookback` 可設定回溯年數（預設全樣本）
- 若是近期極值但非歷史極值，需標註「近 N 年新低」
- 數據起點會影響「歷史紀錄」的判定，必須說明
</principle>

<principle name="output_transparency">
**輸出透明原則**

所有輸出必須標示：
- 天期桶口徑（long / super-long / 10y_plus）
- 投資人分類（insurance_companies / life / non-life）
- 數據期間與最新可用月份
- 若新聞口徑與實際不完全一致，必須標註警示
</principle>

<principle name="unrealized_loss_caveat">
**未實現損失數據說明**

新聞常引用「四大壽險未實現損失 ¥11.3 兆」等數字，這類數據：
- **來源**：Bloomberg 彙整（付費）或各公司財報
- **公開替代**：需逐家抓取公開財報/IR 簡報
- **口徑差異**：可能是「全證券」、「日圓債」或「國內債券」

本 Skill 專注於 JSDA 交易流量，未實現損失需另行處理。
</principle>

</essential_principles>

<objective>
驗證「日本保險公司創紀錄賣超長端 JGB」等敘事，並提供：
1. **本月淨買入/賣出**：最新月份數值（JPY）
2. **是否創紀錄**：判斷是否為樣本最低（最負）
3. **連續賣超月數**：streak_len
4. **本輪累積賣超**：cum_over_streak
5. **口徑警示**：若新聞口徑與數據不一致需標註
</objective>

<quick_start>

**最快的方式：執行快速分析**

```bash
cd skills/analyze-jgb-insurer-superlong-flow
pip install pandas numpy requests openpyxl  # 首次使用
python scripts/jsda_flow_analyzer.py --quick
```

輸出範例：
```json
{
  "end_date": "2025-12",
  "investor_group": "insurance_companies",
  "maturity_bucket": "super_long",
  "latest_net_purchases_trillion_jpy": -0.8224,
  "is_record_sale": true,
  "consecutive_negative_months": 5,
  "cumulative_net_purchases_over_streak_trillion_jpy": -1.37,
  "data_source": "JSDA Trends in Bond Transactions (by investor type)"
}
```

**完整分析（含歷史比較）**：
```bash
python scripts/jsda_flow_analyzer.py --full --start 2015-01 --end 2025-12
```

**生成視覺化圖表**：
```bash
python scripts/generate_flow_chart.py --output-dir ../../output
```

</quick_start>

<intake>
您想要執行什麼操作？

1. **快速檢查** - 查看最新月份的淨買賣與連續賣超狀態
2. **完整分析** - 執行完整的歷史比較與極值判斷
3. **驗證新聞** - 輸入新聞的數字，對比 JSDA 原始數據
4. **生成圖表** - 生成淨買賣流量歷史走勢圖
5. **方法論學習** - 了解指標計算與數據來源

**請選擇或直接提供分析參數（如日期範圍、天期桶）。**
</intake>

<routing>
| Response                        | Workflow                    | Description      |
|---------------------------------|-----------------------------|------------------|
| 1, "快速", "quick", "check"     | workflows/quick-check.md    | 快速狀態檢查     |
| 2, "完整", "full", "analyze"    | workflows/full-analysis.md  | 完整分析工作流   |
| 3, "驗證", "verify", "新聞"     | workflows/verify-claim.md   | 驗證新聞數字     |
| 4, "圖表", "chart", "visualize" | workflows/generate-chart.md | 生成視覺化圖表   |
| 5, "學習", "方法論", "why"      | references/methodology.md   | 方法論說明       |
| 提供參數 (如日期、天期桶)       | workflows/full-analysis.md  | 使用參數執行分析 |

**路由後，閱讀對應工作流程並完全遵循其步驟。**
</routing>

<input_schema>

<parameter name="start_date" required="true">
**Type**: string (YYYY-MM)
**Description**: 分析起始年月
**Example**: "2020-01"
</parameter>

<parameter name="end_date" required="true">
**Type**: string (YYYY-MM)
**Description**: 分析結束年月
**Example**: "2025-12"
</parameter>

<parameter name="investor_group" required="true" default="insurance_companies">
**Type**: string
**Options**: `insurance_companies` | `life_insurance` | `non_life_insurance`
**Description**: 投資人分類（JSDA 定義）
</parameter>

<parameter name="maturity_bucket" required="true" default="super_long">
**Type**: string
**Options**: `super_long` | `long` | `10y_plus` | `long_plus_super_long`
**Description**: 天期區間（需對應 JSDA XLS 實際可用的桶）
</parameter>

<parameter name="measure" required="true" default="net_purchases">
**Type**: string
**Options**: `net_purchases` | `gross_purchases` | `gross_sales`
**Description**: 指標類型（淨買入為核心）
</parameter>

<parameter name="frequency" required="true" default="monthly">
**Type**: string
**Options**: `monthly`
**Description**: 頻率（JSDA 目前僅提供月度）
</parameter>

<parameter name="currency" required="false" default="JPY">
**Type**: string
**Options**: `JPY` | `USD`
**Description**: 輸出幣別
</parameter>

<parameter name="usd_fx_source" required="false">
**Type**: string
**Options**: `fred` | `boe` | `stooq`
**Description**: 若要換算 USD，匯率來源
</parameter>

<parameter name="record_lookback_years" required="false" default="999">
**Type**: int
**Description**: 計算「歷史新高/新低」的回溯年數（999 = 全樣本）
</parameter>

<parameter name="streak_sign" required="false" default="negative">
**Type**: string
**Options**: `negative` | `positive`
**Description**: 連續判斷的符號（negative = 連續淨賣出）
</parameter>

<parameter name="output_format" required="false" default="markdown">
**Type**: string
**Options**: `json` | `markdown`
</parameter>

</input_schema>

<output_schema>
參見 `templates/output-json.md` 的完整結構定義。

**摘要**：
```json
{
  "skill": "analyze_jgb_insurer_superlong_flow",
  "as_of": "2026-01-26",
  "data_source": "JSDA Trends in Bond Transactions (by investor type)",
  "investor_group": "insurance_companies",
  "maturity_bucket": "super_long",
  "analysis_period": {
    "start": "2020-01",
    "end": "2025-12"
  },
  "latest_month": {
    "date": "2025-12",
    "net_purchases_trillion_jpy": -0.8224,
    "interpretation": "淨賣出 ¥8,224 億"
  },
  "record_analysis": {
    "is_record_sale": true,
    "record_low_trillion_jpy": -0.8224,
    "record_date": "2025-12",
    "lookback_period": "全樣本 (2015-01 至今)"
  },
  "streak_analysis": {
    "consecutive_negative_months": 5,
    "streak_start": "2025-08",
    "cumulative_over_streak_trillion_jpy": -1.37
  },
  "notes": [
    "負值 = 淨賣出",
    "口徑：super_long（超長端），需確認是否與新聞 10+ years 完全對應"
  ]
}
```
</output_schema>

<reference_index>
**參考文件** (`references/`)

| 文件              | 內容                                     |
|-------------------|------------------------------------------|
| data-sources.md   | JSDA 數據來源與 XLS 下載說明             |
| methodology.md    | 計算方法論（streak、record、cumulative） |
| input-schema.md   | 輸入參數詳細定義                         |
| jsda-structure.md | JSDA XLS 結構與投資人分類說明            |
</reference_index>

<workflows_index>
| Workflow          | Purpose                  |
|-------------------|--------------------------|
| quick-check.md    | 快速狀態檢查（最新月份） |
| full-analysis.md  | 完整歷史分析工作流       |
| verify-claim.md   | 驗證新聞/媒體報導數字    |
| generate-chart.md | 生成視覺化圖表           |
</workflows_index>

<templates_index>
| Template           | Purpose           |
|--------------------|-------------------|
| output-json.md     | JSON 輸出結構定義 |
| output-markdown.md | Markdown 報告模板 |
</templates_index>

<scripts_index>
| Script                 | Command                    | Purpose            |
|------------------------|----------------------------|--------------------|
| jsda_flow_analyzer.py  | `--quick`                  | 快速檢查           |
| jsda_flow_analyzer.py  | `--full --start M --end M` | 完整分析           |
| jsda_flow_analyzer.py  | `--verify CLAIM`           | 驗證新聞數字       |
| generate_flow_chart.py | `--output-dir DIR`         | 生成視覺化圖表     |
| fetch_jsda_data.py     | `--refresh`                | 抓取 JSDA XLS 數據 |
</scripts_index>

<success_criteria>
Skill 成功執行時：

- [ ] 輸出最新月份淨買入/賣出數值
- [ ] 判斷是否為歷史極值（含回溯期間說明）
- [ ] 計算連續賣超月數與累積金額
- [ ] 明確標示天期桶口徑
- [ ] 若新聞口徑不一致，提供警示與替代數值
- [ ] 可操作的 headline takeaways
</success_criteria>

<directory_structure>
```
analyze-jgb-insurer-superlong-flow/
├── SKILL.md                           # 本文件（路由器）
├── skill.yaml                         # 前端展示元數據
├── manifest.json                      # 技能元資料
├── workflows/
│   ├── quick-check.md                 # 快速檢查工作流
│   ├── full-analysis.md               # 完整分析工作流
│   ├── verify-claim.md                # 驗證新聞工作流
│   └── generate-chart.md              # 圖表生成工作流
├── references/
│   ├── data-sources.md                # 資料來源說明
│   ├── methodology.md                 # 方法論與公式
│   ├── input-schema.md                # 輸入參數詳細定義
│   └── jsda-structure.md              # JSDA XLS 結構說明
├── templates/
│   ├── output-json.md                 # JSON 輸出模板
│   └── output-markdown.md             # Markdown 報告模板
├── scripts/
│   ├── jsda_flow_analyzer.py          # 主分析腳本
│   ├── generate_flow_chart.py         # 視覺化圖表生成
│   └── fetch_jsda_data.py             # JSDA 數據抓取
├── data/
│   └── cache/                         # 自動緩存目錄（gitignore）
└── examples/
    └── sample-output.json             # 範例輸出
```
</directory_structure>
