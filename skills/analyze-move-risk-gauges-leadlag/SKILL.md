---
name: analyze-move-risk-gauges-leadlag
description: 用公開市場數據檢查「利率波動率（MOVE）是否對利率事件（如 JGB 殖利率變動）不恐慌，並且是否領先帶動 VIX / 信用利差走低」。
---

<essential_principles>

<principle name="move_as_leading_indicator">
**MOVE 作為利率波動率領先指標**

MOVE Index（美林期權波動率指數）是衡量美國國債選擇權隱含波動率的指標：
- **MOVE 低/下降**：利率市場對未來波動預期降低，風險偏好上升
- **MOVE 高/上升**：利率市場恐慌，避險需求增加

MOVE 常被視為「債市的 VIX」，可作為其他風險指標的領先訊號。
</principle>

<principle name="leadlag_cross_correlation">
**交叉相關判斷領先落後**

使用 Cross-Correlation 判斷兩序列的領先/落後關係：
- 在 [-L, +L] 位移範圍內計算相關係數
- **最大相關出現在 lag > 0**：X 領先 Y
- **最大相關出現在 lag < 0**：X 落後 Y
- **最大相關出現在 lag ≈ 0**：同步移動

典型設定：L = 20（交易日），配合平滑處理降低噪音。
</principle>

<principle name="shock_event_reaction">
**事件窗檢定：是否被嚇到**

檢驗「利率事件（如 JGB 殖利率跳升）發生時，MOVE 是否恐慌」：
1. 定義衝擊事件：|ΔY[t-k:t]| ≥ threshold（如 15bp）
2. 檢查事件窗內 MOVE 變化
3. 若 MOVE 反應 < 歷史分布中位數 → "not spooked"

此邏輯可驗證「利率波動率對某事件不敏感」的敘事。
</principle>

<principle name="data_access">
**資料取得方式**

本 skill 使用**無需 API key** 的公開資料來源：
- **FRED CSV**: 殖利率、信用利差（OAS）代理
- **Yahoo Finance**: VIX
- **MacroMicro/Investing.com**: MOVE Index、JGB 10Y（需爬蟲）

資料替代方案詳見 `references/data-sources.md`。
</principle>

</essential_principles>

<objective>
實作利率波動率與風險指標的領先落後分析：

1. **數據抓取**：從公開來源取得 MOVE、VIX、信用利差、JGB 殖利率
2. **標準化處理**：Z 分數、平滑處理、頻率對齊
3. **領先落後分析**：交叉相關找出 MOVE vs VIX / 信用利差的 lead/lag
4. **事件窗檢定**：JGB 衝擊事件中 MOVE 是否「不恐慌」
5. **方向一致性**：MOVE 下行時，其他風險指標是否同步下行

輸出：領先落後判定、恐慌檢定結果、方向一致性比例、量化證據。
</objective>

<quick_start>

**最快的方式：執行預設分析**

```bash
cd skills/analyze-move-risk-gauges-leadlag
pip install pandas numpy yfinance requests  # 首次使用
python scripts/analyze.py --quick
```

輸出範例：
```json
{
  "status": "ok",
  "headline": "MOVE not spooked by JGB yield moves and appears to lead VIX/Credit lower.",
  "leadlag": {
    "MOVE_vs_VIX": {"best_lag_days": 6, "corr": 0.72},
    "MOVE_vs_CREDIT": {"best_lag_days": 4, "corr": 0.61}
  },
  "spooked_check": {
    "shock_count": 3,
    "mean_MOVE_reaction_on_shocks": 0.8,
    "MOVE_zscore_now": -0.4
  }
}
```

**完整分析**：
```bash
python scripts/analyze.py --start 2024-01-01 --end 2026-01-01 --output result.json
```

</quick_start>

<intake>
需要進行什麼操作？

1. **快速檢查** - 查看目前 MOVE 的領先落後狀態與恐慌程度
2. **完整分析** - 執行完整的領先落後與事件窗分析
3. **視覺化圖表** - 生成多面板分析結果圖表
4. **方法論學習** - 了解 Lead/Lag 分析與事件窗檢定的邏輯

**請選擇或直接提供分析參數。**
</intake>

<routing>
| Response                     | Action                                     |
|------------------------------|--------------------------------------------|
| 1, "快速", "quick", "check"  | 執行 `python scripts/analyze.py --quick`   |
| 2, "完整", "full", "analyze" | 閱讀 `workflows/analyze.md` 並執行         |
| 3, "視覺化", "chart", "plot" | 閱讀 `workflows/visualize.md` 並執行       |
| 4, "學習", "方法論", "why"   | 閱讀 `references/methodology.md`           |
| 提供參數 (如日期範圍)        | 閱讀 `workflows/analyze.md` 並使用參數執行 |

**路由後，閱讀對應文件並執行。**
</routing>

<directory_structure>
```
analyze-move-risk-gauges-leadlag/
├── SKILL.md                           # 本文件（路由器）
├── skill.yaml                         # 前端展示元數據
├── manifest.json                      # 技能元數據
├── workflows/
│   ├── analyze.md                     # 完整分析工作流
│   └── visualize.md                   # 視覺化工作流
├── references/
│   ├── data-sources.md                # 資料來源與替代方案
│   ├── methodology.md                 # Lead/Lag 與事件窗方法論
│   └── input-schema.md                # 完整輸入參數定義
├── templates/
│   ├── output-json.md                 # JSON 輸出模板
│   └── output-markdown.md             # Markdown 報告模板
└── scripts/
    ├── analyze.py                     # 主分析腳本
    ├── fetch_data.py                  # 數據抓取工具
    └── visualize.py                   # 視覺化繪圖工具
```
</directory_structure>

<reference_index>

**方法論**: references/methodology.md
- Lead/Lag 交叉相關分析
- Z 分數標準化
- 事件窗檢定邏輯

**資料來源**: references/data-sources.md
- MOVE Index 公開替代
- VIX、信用利差、JGB 殖利率來源
- 數據頻率與對齊

**輸入參數**: references/input-schema.md
- 完整參數定義
- 預設值與建議範圍

</reference_index>

<workflows_index>
| Workflow     | Purpose          | 使用時機           |
|--------------|------------------|--------------------|
| analyze.md   | 完整領先落後分析 | 需要詳細分析報告時 |
| visualize.md | 生成視覺化圖表   | 需要圖表展示時     |
</workflows_index>

<templates_index>
| Template           | Purpose           |
|--------------------|-------------------|
| output-json.md     | JSON 輸出結構定義 |
| output-markdown.md | Markdown 報告模板 |
</templates_index>

<scripts_index>
| Script        | Command                        | Purpose          |
|---------------|--------------------------------|------------------|
| analyze.py    | `--quick`                      | 快速檢查當前狀態 |
| analyze.py    | `--start DATE --end DATE`      | 完整分析         |
| fetch_data.py | `--series MOVE,VIX,CREDIT,JGB` | 抓取公開資料     |
| visualize.py  | `-i result.json -o chart.png`  | 生成視覺化圖表   |
</scripts_index>

<input_schema_summary>

**核心參數**

| 參數                 | 類型   | 預設值       | 說明                  |
|----------------------|--------|--------------|-----------------------|
| start_date           | string | -            | 起始日期 (YYYY-MM-DD) |
| end_date             | string | -            | 結束日期 (YYYY-MM-DD) |
| rates_vol_symbol     | string | MOVE         | 利率波動率指標        |
| equity_vol_symbol    | string | VIX          | 股市波動率指標        |
| credit_spread_symbol | string | CDX_IG_PROXY | 信用利差/風險指標     |
| jgb_yield_symbol     | string | JGB10Y       | 日本 10Y 殖利率       |

**分析參數**

| 參數                | 類型   | 預設值   | 說明                 |
|---------------------|--------|----------|----------------------|
| freq                | string | D        | 頻率（D=日 / W=週）  |
| smooth_window       | int    | 5        | 平滑移動平均窗       |
| zscore_window       | int    | 60       | Z 分數回看窗         |
| lead_lag_max_days   | int    | 20       | 交叉相關最大位移天數 |
| shock_window_days   | int    | 5        | 事件窗天數           |
| shock_threshold_bps | float  | 15       | JGB 衝擊門檻 (bps)   |
| output_mode         | string | markdown | 輸出格式             |

完整參數定義見 `references/input-schema.md`。

</input_schema_summary>

<output_schema_summary>
```json
{
  "skill": "analyze-move-risk-gauges-leadlag",
  "as_of": "2026-01-23",
  "status": "ok",
  "headline": "MOVE not spooked by JGB yield moves and appears to lead VIX/Credit lower.",
  "leadlag": {
    "MOVE_vs_VIX": {"best_lag_days": 6, "corr": 0.72},
    "MOVE_vs_CREDIT": {"best_lag_days": 4, "corr": 0.61}
  },
  "spooked_check": {
    "shock_definition": "abs(JGB10Y change over 5d) >= 15bp",
    "shock_count": 3,
    "mean_MOVE_reaction_on_shocks": 0.8,
    "MOVE_zscore_now": -0.4
  },
  "direction_alignment": {
    "MOVE_down_and_VIX_down_ratio": 0.58,
    "MOVE_down_and_CREDIT_down_ratio": 0.55
  }
}
```

完整輸出結構見 `templates/output-json.md`。
</output_schema_summary>

<success_criteria>
執行成功時應產出：

- [ ] MOVE vs VIX / Credit 的最佳領先天數與相關係數
- [ ] JGB 衝擊事件數量與 MOVE 平均反應
- [ ] MOVE 當前 Z 分數（恐慌程度）
- [ ] 方向一致性比例
- [ ] 一句話結論與量化證據
- [ ] 視覺化圖表（可選）
</success_criteria>
