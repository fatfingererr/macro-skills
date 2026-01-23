---
name: detect-freight-led-inflation-turn
description: 透過美國卡斯貨運指數 (CASS Freight Index) 的週期轉折，偵測美國通膨壓力是否進入放緩或反轉階段。用於判斷「通膨是否正在降溫」，並驗證市場對降息、通膨回落的宏觀敘事是否有實體經濟數據支撐。
---

<essential_principles>

<principle name="cass_freight_index">
**CASS Freight Index 是最權威的貨運指標**

CASS Freight Index 由 Cass Information Systems 編制，追蹤北美地區的貨運出貨量與支出：

| 指標                   | 說明         | 用途                         |
|------------------------|--------------|------------------------------|
| **Shipments Index**    | 出貨量指數   | 衡量實體經濟需求強度         |
| **Expenditures Index** | 運費支出指數 | 衡量物流成本壓力             |
| **Shipments YoY**      | 出貨量年增率 | 偵測週期轉折（主要分析指標） |
| **Expenditures YoY**   | 支出年增率   | 驗證成本傳導                 |

數據來源：MacroMicro (透過 Highcharts 爬取)
</principle>

<principle name="freight_leads_inflation">
**貨運量是通膨的領先指標**

核心邏輯：
- 貨運量 ≈ 實體經濟需求強度
- 出貨量下降 → 終端需求減弱 → 定價能力下降
- 歷史上 CASS 指標對 CPI 具有約 4-6 個月的領先性

關鍵訊號不是單月變化，而是「週期轉折」：
- 年增率轉負 (turned negative)
- 創週期新低 (new cycle low)
</principle>

<principle name="signal_interpretation">
**訊號解讀：通膨緩解而非通縮**

當偵測到 CASS 週期轉折：
- 結論是「通膨壓力緩解」而非「通縮」
- 屬於 inflation easing / disinflation regime
- 支持市場對降息或政策轉向的預期

這是跨週期關係辨識：「物流需求動能 → 通膨方向」
</principle>

<principle name="multi_indicator">
**多指標交叉驗證**

建議同時觀察四個 CASS 指標：
1. **Shipments YoY**（主要）：需求端訊號
2. **Expenditures YoY**：成本端訊號
3. **Shipments Index**：絕對水準
4. **Expenditures Index**：運費壓力

當 Shipments 和 Expenditures 同時轉負，訊號更為可靠。
</principle>

</essential_principles>

<objective>
偵測 CASS Freight Index 的週期轉折，判斷通膨是否正在放緩。

輸出三層訊號：
1. **Freight Status**: CASS 各指標狀態與週期位置
2. **Lead Alignment**: 與 CPI YoY 的領先對齊分析
3. **Signal Assessment**: 通膨緩解訊號判斷與信心水準
</objective>

<quick_start>

**最快的方式：執行快速檢查**

```bash
cd skills/detect-freight-led-inflation-turn
pip install pandas numpy requests selenium webdriver-manager  # 首次使用
python scripts/freight_inflation_detector.py --quick
```

輸出範例：
```json
{
  "signal": "inflation_easing",
  "confidence": "high",
  "freight_yoy": -2.9,
  "cycle_status": "new_cycle_low",
  "indicator": "shipments_yoy",
  "macro_implication": "通膨壓力正在放緩，未來 CPI 下行風險上升"
}
```

**完整分析**：
```bash
python scripts/freight_inflation_detector.py --start 2010-01-01 --indicator shipments_yoy
```

**查看所有四個 CASS 指標**：
```bash
python scripts/fetch_cass_freight.py --cache-dir ./cache
```

</quick_start>

<intake>
需要進行什麼分析？

1. **快速檢查** - 查看最新的 CASS 指標與通膨先行訊號
2. **完整分析** - 執行完整的週期轉折偵測與領先性分析
3. **方法論學習** - 了解 CASS 指標與通膨的領先關係

**請選擇或直接提供分析參數。**
</intake>

<routing>
| Response                     | Action                                                      |
|------------------------------|-------------------------------------------------------------|
| 1, "快速", "quick", "check"  | 執行 `python scripts/freight_inflation_detector.py --quick` |
| 2, "完整", "full", "analyze" | 閱讀 `workflows/analyze.md` 並執行                          |
| 3, "學習", "方法論", "why"   | 閱讀 `references/methodology.md`                            |
| 提供參數 (如日期範圍)        | 閱讀 `workflows/analyze.md` 並使用參數執行                  |

**路由後，閱讀對應文件並執行。**
</routing>

<directory_structure>
```
detect-freight-led-inflation-turn/
├── SKILL.md                           # 本文件（路由器）
├── skill.yaml                         # 前端展示元數據
├── manifest.json                      # 技能元資料
├── workflows/
│   ├── analyze.md                     # 完整分析工作流
│   └── quick-check.md                 # 快速檢查工作流
├── references/
│   ├── data-sources.md                # CASS 數據來源與爬蟲說明
│   ├── methodology.md                 # 領先性方法論解析
│   └── historical-episodes.md         # 歷史案例對照
├── templates/
│   ├── output-json.md                 # JSON 輸出模板
│   └── output-markdown.md             # Markdown 報告模板
├── scripts/
│   ├── fetch_cass_freight.py          # MacroMicro CASS 爬蟲
│   └── freight_inflation_detector.py  # 主分析腳本
└── examples/
    └── sample_output.json             # 範例輸出
```
</directory_structure>

<reference_index>

**方法論**: references/methodology.md
- CASS Freight Index 與 CPI 的領先性關係
- 週期轉折偵測邏輯
- 訊號強度評估標準

**資料來源**: references/data-sources.md
- MacroMicro Highcharts 爬蟲說明
- CASS 四個指標定義
- 快取策略與更新頻率

**歷史案例**: references/historical-episodes.md
- 2008 金融危機前後
- 2020 疫情期間
- 2022 通膨高峰期

</reference_index>

<workflows_index>
| Workflow       | Purpose          | 使用時機           |
|----------------|------------------|--------------------|
| analyze.md     | 完整週期轉折分析 | 需要深度分析時     |
| quick-check.md | 快速檢查訊號     | 日常監控或快速回答 |
</workflows_index>

<templates_index>
| Template           | Purpose           |
|--------------------|-------------------|
| output-json.md     | JSON 輸出結構定義 |
| output-markdown.md | Markdown 報告模板 |
</templates_index>

<scripts_index>
| Script                        | Command                      | Purpose            |
|-------------------------------|------------------------------|--------------------|
| freight_inflation_detector.py | `--quick`                    | 快速檢查最新訊號   |
| freight_inflation_detector.py | `--start DATE --indicator X` | 完整分析           |
| fetch_cass_freight.py         | `--cache-dir ./cache`        | 爬取 CASS 四個指標 |
</scripts_index>

<input_schema>

<parameter name="start_date" required="true">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析起始日期
**Example**: "2010-01-01"
</parameter>

<parameter name="end_date" required="false" default="today">
**Type**: string (ISO YYYY-MM-DD)
**Description**: 分析結束日期
</parameter>

<parameter name="indicator" required="false" default="shipments_yoy">
**Type**: string
**Options**: `shipments_index` | `expenditures_index` | `shipments_yoy` | `expenditures_yoy`
**Description**: CASS 指標選擇
- `shipments_yoy`: 出貨量年增率（推薦，主要分析指標）
- `expenditures_yoy`: 支出年增率
- `shipments_index`: 出貨量指數
- `expenditures_index`: 支出指數
</parameter>

<parameter name="lead_months" required="false" default="6">
**Type**: integer
**Description**: 領先 CPI 的月份數
**Range**: 3-12
</parameter>

<parameter name="yoy_threshold" required="false" default="0.0">
**Type**: float
**Description**: 年增率警戒門檻（如 0 表示轉負）
</parameter>

</input_schema>

<output_schema>
參見 `templates/output-json.md` 的完整結構定義。

**摘要**：
```json
{
  "signal": "inflation_easing | inflation_rising | neutral",
  "confidence": "high | medium | low",
  "freight_yoy": -2.9,
  "cycle_status": "new_cycle_low | negative | positive",
  "indicator": "shipments_yoy",
  "macro_implication": "通膨壓力正在放緩，未來 CPI 下行風險上升",
  "all_indicators": {
    "shipments_index": {...},
    "expenditures_index": {...},
    "shipments_yoy": {...},
    "expenditures_yoy": {...}
  }
}
```
</output_schema>

<success_criteria>
分析成功時應產出：

- [ ] CASS 四個指標的最新數值
- [ ] 選定指標的 YoY 與週期狀態
- [ ] 與 CPI 的領先對齊驗證
- [ ] 通膨緩解訊號與信心水準
- [ ] 可操作的宏觀解讀
- [ ] 明確標註資料限制與假設
</success_criteria>
