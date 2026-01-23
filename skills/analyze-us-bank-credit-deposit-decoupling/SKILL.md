---
name: analyze-us-bank-credit-deposit-decoupling
description: 分析銀行貸款與存款之間的「信貸創造脫鉤」現象，用以辨識聯準會緊縮政策在銀行體系內部的真實傳導效果。用於判斷「金融環境是否正在發生隱性緊縮」，並驗證市場對 QT 效果的宏觀敘事是否有數據支撐。
---

<essential_principles>

<principle name="credit_deposit_accounting">
**信貸創造的基本會計邏輯**

傳統銀行體系下，貸款創造存款：
- 銀行發放貸款 → 借款人帳戶增加存款
- 理論上：新增貸款 ≈ 新增存款

當這個關係「脫鉤」時：
- 貸款持續擴張，但存款沒有等比例增加
- 代表有「力量」在抽走體系內的存款
- QT 環境下，這個力量通常來自 RRP（逆回購工具）
</principle>

<principle name="decoupling_gap_definition">
**信貸存款落差（Decoupling Gap）定義**

核心公式：
```
decoupling_gap = 累積新增貸款 − 累積新增存款
```

解讀：
- **Gap > 0**：貸款創造的存款「消失」了，被某處吸走
- **Gap ≈ RRP 累積吸收量**：證明 Fed 透過 RRP 抽走流動性
- **Gap 持續擴大**：銀行負債端壓力增加，需要「搶存款」
</principle>

<principle name="rrp_neutralization">
**RRP 的中和效果**

聯準會隔夜逆回購（RRP）是「資金被吸出銀行體系」的 proxy：
- 貨幣市場基金將資金存入 Fed RRP → 資金離開商業銀行
- RRP 規模增加 → 銀行存款減少
- 這是 QT 的「隱性管道」，不直接縮貸但壓縮銀行負債端

關鍵驗證：
```
decoupling_gap ≈ 累積 RRP 吸收量
```
若高度相關，代表「QT 並非透過縮貸，而是透過存款被抽走來實現緊縮」
</principle>

<principle name="hidden_tightening">
**隱性緊縮（Hidden Tightening）判定**

當觀察到以下條件：
1. 貸款持續上升（銀行仍在放貸）
2. 存款成長顯著落後貸款
3. decoupling_gap 與 RRP 累積量高度相關

→ 判定為「非典型 QT」或「隱性緊縮」（Hidden Balance Sheet Tightening）

這意味著：
- 緊縮並非來自銀行不放貸
- 而是來自負債端（存款）被政策工具抽乾
- 市場需要額外搶存款來支撐既有負債結構
</principle>

<principle name="data_sources">
**數據來源（全部使用 FRED）**

| 指標         | FRED Series ID | 說明                                                  |
|--------------|----------------|-------------------------------------------------------|
| 銀行貸款總量 | TOTLL          | Loans and Leases in Bank Credit, All Commercial Banks |
| 銀行存款總量 | DPSACBW027SBOG | Deposits, All Commercial Banks                        |
| 隔夜逆回購   | RRPONTSYD      | Overnight Reverse Repurchase Agreements               |

資料頻率：Weekly（週頻）
對齊方式：以最新共同日期為準
</principle>

</essential_principles>

<objective>
分析銀行信貸與存款的脫鉤現象，判斷金融環境的隱性緊縮狀態。

輸出三層訊號：
1. **Decoupling Status**: 信貸-存款落差狀態與趨勢
2. **RRP Correlation**: 與 RRP 吸收量的相關性驗證
3. **Tightening Assessment**: 隱性緊縮訊號判斷與壓力指標
</objective>

<quick_start>

**最快的方式：使用 FRED API 抓取數據**

**Step 1：安裝依賴**
```bash
pip install pandas numpy fredapi matplotlib
```

**Step 2：設定 FRED API Key**
```bash
# 從 https://fred.stlouisfed.org/docs/api/api_key.html 取得 API Key
export FRED_API_KEY="your_api_key_here"
```

**Step 3：執行快速分析**
```bash
cd scripts
python decoupling_analyzer.py --quick
```

**Step 4：執行完整分析（含視覺化）**
```bash
python decoupling_analyzer.py \
  --start 2022-06-01 \
  --end 2026-01-23 \
  --output ../../output/decoupling_$(date +%Y-%m-%d).json
```

**Step 5：生成視覺化圖表**
```bash
python visualize_decoupling.py \
  --start 2022-06-01 \
  --output ../../output/decoupling_chart_$(date +%Y-%m-%d).png
```

**輸出範例**：
- JSON 分析結果：
```json
{
  "period": "2022-06 to 2026-01",
  "new_loans_trillion_usd": 2.1,
  "new_deposits_trillion_usd": 0.5,
  "decoupling_gap_trillion_usd": 1.6,
  "deposit_stress_ratio": 0.76,
  "rrp_correlation": 0.89,
  "tightening_type": "hidden_balance_sheet_tightening",
  "primary_driver": "RRP_liquidity_absorption"
}
```
- 視覺化圖表：`output/decoupling_chart_2026-01-23.png`

</quick_start>

<intake>
需要進行什麼分析？

1. **快速檢查** - 查看最新的信貸-存款脫鉤狀態與壓力指標
2. **完整分析** - 執行完整的脫鉤偵測與 RRP 相關性分析
3. **方法論學習** - 了解信貸創造脫鉤的會計邏輯與宏觀意義

**請選擇或直接提供分析參數。**
</intake>

<routing>
| Response                     | Action                                               |
|------------------------------|------------------------------------------------------|
| 1, "快速", "quick", "check"  | 執行 `python scripts/decoupling_analyzer.py --quick` |
| 2, "完整", "full", "analyze" | 閱讀 `workflows/analyze.md` 並執行                   |
| 3, "學習", "方法論", "why"   | 閱讀 `references/methodology.md`                     |
| 提供參數 (如日期範圍)        | 閱讀 `workflows/analyze.md` 並使用參數執行           |

**路由後，閱讀對應文件並執行。**
</routing>

<directory_structure>
```
analyze-us-bank-credit-deposit-decoupling/
├── SKILL.md                           # 本文件（路由器）
├── skill.yaml                         # 前端展示元數據
├── manifest.json                      # 技能元資料
├── workflows/
│   ├── analyze.md                     # 完整分析工作流
│   └── quick-check.md                 # 快速檢查工作流
├── references/
│   ├── data-sources.md                # FRED 數據來源說明
│   ├── methodology.md                 # 信貸脫鉤方法論解析
│   └── historical-episodes.md         # 歷史案例對照
├── templates/
│   ├── output-json.md                 # JSON 輸出模板
│   └── output-markdown.md             # Markdown 報告模板
├── scripts/
│   ├── decoupling_analyzer.py         # 主分析腳本
│   └── visualize_decoupling.py        # 脫鉤狀態視覺化
└── examples/
    └── sample_output.json             # 範例輸出
```
</directory_structure>

<reference_index>

**方法論**: references/methodology.md
- 信貸創造的會計邏輯
- Decoupling Gap 計算與解讀
- RRP 中和效果驗證
- 隱性緊縮判定標準

**資料來源**: references/data-sources.md
- FRED API 使用說明
- 三個核心指標定義
- 數據頻率與對齊方式
- 快取策略與更新頻率

**歷史案例**: references/historical-episodes.md
- 2017-2019 首次 QT 週期
- 2022-2026 當前 QT 週期
- RRP 高峰與銀行壓力事件

</reference_index>

<workflows_index>
| Workflow       | Purpose      | 使用時機           |
|----------------|--------------|--------------------|
| analyze.md     | 完整脫鉤分析 | 需要深度分析時     |
| quick-check.md | 快速檢查訊號 | 日常監控或快速回答 |
</workflows_index>

<templates_index>
| Template           | Purpose           |
|--------------------|-------------------|
| output-json.md     | JSON 輸出結構定義 |
| output-markdown.md | Markdown 報告模板 |
</templates_index>

<scripts_index>
| Script                  | Command                   | Purpose          |
|-------------------------|---------------------------|------------------|
| decoupling_analyzer.py  | `--quick`                 | 快速檢查最新訊號 |
| decoupling_analyzer.py  | `--start DATE --end DATE` | 完整分析         |
| visualize_decoupling.py | `--start DATE`            | 繪製脫鉤狀態圖   |
</scripts_index>

<visualization>

**視覺化輸出：信貸-存款脫鉤分析圖**

核心特徵（參考 Bloomberg/Refinitiv 風格）：
1. **累積變化量對比**：貸款 vs 存款 vs RRP 累積變化
2. **Decoupling Gap**：落差區域以陰影標示
3. **壓力指標**：deposit_stress_ratio 時序圖
4. **深色風格**：深藍背景、高對比度配色

**快速繪圖**：
```bash
cd scripts
python visualize_decoupling.py \
  --start 2022-06-01 \
  --output ../../output/decoupling_chart_YYYY-MM-DD.png
```

**輸出路徑**：`output/decoupling_chart_YYYY-MM-DD.png`（根目錄）

**圖表解讀**：
- 當 Gap 與 RRP 走勢高度相關 → 證明 RRP 是主要抽水來源
- 當 deposit_stress_ratio 超過 0.5 → 銀行負債端壓力顯著
- 當 Gap 持續擴大但 RRP 下降 → 需注意其他流動性吸收來源

</visualization>

<input_schema>

<parameter name="start_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析起始日期
**Example**: "2022-06-01"
</parameter>

<parameter name="end_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析結束日期
**Example**: "2026-01-23"
</parameter>

<parameter name="frequency" required="false" default="weekly">
**Type**: string
**Options**: `weekly` | `monthly`
**Description**: 資料頻率
</parameter>

<parameter name="loan_series_id" required="false" default="TOTLL">
**Type**: string
**Description**: 銀行貸款資料的 FRED Series ID
</parameter>

<parameter name="deposit_series_id" required="false" default="DPSACBW027SBOG">
**Type**: string
**Description**: 銀行存款資料的 FRED Series ID
</parameter>

<parameter name="rrp_series_id" required="false" default="RRPONTSYD">
**Type**: string
**Description**: 逆回購工具（RRP）使用量的 FRED Series ID
</parameter>

</input_schema>

<output_schema>
參見 `templates/output-json.md` 的完整結構定義。

**摘要**：
```json
{
  "status": "success",
  "analysis_period": {
    "start": "2022-06-01",
    "end": "2026-01-23"
  },
  "cumulative_changes": {
    "new_loans_trillion_usd": 2.1,
    "new_deposits_trillion_usd": 0.5,
    "rrp_change_trillion_usd": 1.5
  },
  "decoupling_metrics": {
    "decoupling_gap_trillion_usd": 1.6,
    "deposit_stress_ratio": 0.76,
    "rrp_gap_correlation": 0.89
  },
  "assessment": {
    "tightening_type": "hidden_balance_sheet_tightening",
    "primary_driver": "RRP_liquidity_absorption",
    "confidence": "high"
  },
  "macro_implication": "本次緊縮並非來自銀行縮手放貸，而是聯準會透過 RRP 抽走體系存款，導致市場必須爭奪有限的存款來支撐既有負債結構，屬於「隱性金融緊縮」狀態。"
}
```
</output_schema>

<success_criteria>
分析成功時應產出：

- [ ] 銀行貸款、存款、RRP 三個指標的時序數據
- [ ] 累積變化量計算
- [ ] Decoupling Gap 與 deposit_stress_ratio
- [ ] RRP 與 Gap 的相關性驗證
- [ ] 隱性緊縮訊號判定與信心水準
- [ ] **脫鉤狀態分析圖**（output/decoupling_chart_YYYY-MM-DD.png）
- [ ] 可操作的宏觀解讀
- [ ] 明確標註資料限制與假設
</success_criteria>
