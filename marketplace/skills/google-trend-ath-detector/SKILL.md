---
name: google-trend-ath-detector
displayName: Google Trend 歷史新高 (ATH) 偵測器
description: 自動抓取 Google Trends 指標，判定是否出現「歷史新高（ATH）」或異常飆升，並把這個搜尋情緒訊號映射到可檢驗的宏觀驅動假說與後續驗證清單。
emoji: "\U0001F4C8"
version: v0.1.0
license: MIT
author: Ricky Wang
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - Google Trends
  - ATH
  - 歷史新高
  - 情緒指標
  - 異常偵測
  - 宏觀
  - 搜尋趨勢
  - 假說生成
  - 季節性分析
category: indicator-monitoring
dataLevel: free-nolimit
tools:
  - claude-code
featured: true
installCount: 0
testQuestions:
  - question: '分析 "Health Insurance" 在美國的搜尋趨勢是否創下歷史新高'
    expectedResult: |
      此偵測器會：
      1. 抓取 2004-至今的 Google Trends 時間序列
      2. 進行 STL 季節性分解
      3. 判定是否為 ATH 並計算異常分數
      4. 提取 related queries 識別驅動因素
      5. 生成可檢驗假說與下一步驗證清單
  - question: '比較 "Unemployment" 和 "Health Insurance" 的趨勢共振'
    expectedResult: |
      分析兩個主題的相關性，判斷是「單點焦慮」還是「整體經濟焦慮」，
      並給出對應的宏觀解讀框架。
  - question: '這張 Google Trends 圖表是否真的創新高？'
    expectedResult: |
      若提供圖表圖片，會走數據擷取流程驗證貼文主張，
      並給出「是否真的破表」的判定與解釋。

qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 85
    maintainability: 80
    content: 90
    community: 30
    security: 100
    compliance: 75
  details: |
    **架構（85/100）**
    - ✅ 模組化 router pattern 設計
    - ✅ 清晰的訊號分型與假說生成流程
    - ⚠️ Alpha 階段

    **可維護性（80/100）**
    - ✅ 工作流程分離清晰
    - ✅ 參數定義完整

    **內容（90/100）**
    - ✅ 完整的訊號分析框架
    - ✅ 可檢驗假說模板
    - ✅ 下一步驗證清單

    **社區（30/100）**
    - ⚠️ 新技能，尚無社區貢獻

    **安全（100/100）**
    - ✅ 僅讀取公開 Google Trends 數據

    **規範符合性（75/100）**
    - ✅ 遵循 Claude Code 規範
    - ⚠️ Alpha 階段

bestPractices:
  - title: 使用 Topic Entity 而非純關鍵字
    description: Topic Entity 可避免同名歧義（如 "Apple" 公司 vs 水果）
  - title: 關注去季節化後的殘差
    description: 單看絕對值可能被季節性誤導，殘差才是真正的「異常」
  - title: 結合 related queries 識別驅動
    description: Rising queries 能揭示「為什麼」搜尋量上升
  - title: 不要只看是否 ATH
    description: 重要的是「是否異常」而非「是否最高」
  - title: 生成假說而非下結論
    description: 趨勢只是訊號，需要其他數據驗證

pitfalls:
  - title: 忽略季節性
    description: 很多搜尋有固定的年度週期（報稅季、投保季）
    consequence: 把正常季節性尖峰誤判為異常
  - title: 過度解讀 Google Trends 指數
    description: 0-100 是相對指數，不是絕對搜尋量
    consequence: 錯誤比較不同主題或不同時間範圍
  - title: 忽略數據延遲
    description: Google Trends 有 2-3 天的數據延遲
    consequence: 誤以為「今天」的數據已更新
  - title: 單一關鍵字偏差
    description: 只看一個關鍵字可能錯過更廣泛的趨勢
    consequence: 錯誤歸因（單點焦慮 vs 系統性焦慮）

faq:
  - question: Google Trends 的 0-100 指數代表什麼？
    answer: |
      這是相對指數，100 表示該時間範圍內的最高點。
      不同時間範圍或不同主題的 100 不能直接比較。

  - question: 如何區分季節性尖峰和真正的異常？
    answer: |
      使用 STL 分解或類似方法，分離出 trend/seasonal/residual。
      如果殘差的 z-score 顯著高於歷史，才是真正的異常。

  - question: pytrends 有什麼限制？
    answer: |
      - 非官方 API，可能被 rate limit
      - 每次只能查 5 個關鍵字
      - 長時間範圍只能取得週/月數據
      - 建議用 Topic Entity 而非純關鍵字

about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 數據來源

    - Google Trends：https://trends.google.com
    - pytrends（Python 介面）：https://pypi.org/project/pytrends/
---

<essential_principles>
**Google Trend ATH Detector 核心原則**

**1. 訊號分型（Signal Typing）**

搜尋趨勢飆升有三種不同的結構性解釋：

| 類型               | 特徵                             | 解讀                         |
|--------------------|----------------------------------|------------------------------|
| Seasonal spike     | 每年固定月份重複、殘差不高       | 制度性週期（投保季、報稅季） |
| Event-driven shock | 短期尖峰、z-score 高、事件詞上升 | 新聞/政策/系統性故障         |
| Regime shift       | 變點成立、趨勢線上移             | 結構性關注上升               |

**2. 平衡公式**

```
Attention Signal = f(Raw Trend, Seasonality, Baseline, Anomaly Score)

判定邏輯：
- is_ath = latest_value >= max(history)
- is_anomaly = zscore(deseasonalized_residual) >= threshold
- signal_type = classify(is_ath, is_anomaly, seasonality_strength)
```

**3. 假說優先於結論**

此技能**不**直接下結論，而是生成**可檢驗假說**：
- 每個假說配對「下一步該查的數據」
- 讓用戶自己驗證因果關係

**4. 數據層級**

- **必要**：Google Trends 時間序列
- **輔助**：Related queries（識別驅動詞彙）
- **對照**：Compare terms（區分單點 vs 系統性焦慮）
- **驗證**：宏觀數據（FRED、BLS、政策日曆）
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **Detect** - 偵測指定主題是否創下 ATH 或出現異常飆升
2. **Analyze** - 深度分析訊號類型、驅動因素與假說生成
3. **Verify** - 驗證社群貼文/圖表的主張是否屬實
4. **Compare** - 比較多個主題的趨勢共振

**等待回應後再繼續。**
</intake>

<routing>
| Response                                  | Workflow             | Description         |
|-------------------------------------------|----------------------|---------------------|
| 1, "detect", "ath", "check", "是否創新高" | workflows/detect.md  | 快速偵測 ATH 與異常 |
| 2, "analyze", "deep", "分析", "假說"      | workflows/analyze.md | 深度分析與假說生成  |
| 3, "verify", "check", "驗證", "圖表"      | workflows/verify.md  | 驗證貼文主張        |
| 4, "compare", "對照", "共振"              | workflows/compare.md | 多主題趨勢比較      |

**讀取工作流程後，請完全遵循其步驟。**
</routing>

<reference_index>
**參考文件** (`references/`)

| 文件                    | 內容                                     |
|-------------------------|------------------------------------------|
| input-schema.md         | 完整輸入參數定義與預設值                 |
| hypothesis-templates.md | 假說模板與驗證數據映射                   |
| data-sources.md         | 數據來源清單（Google Trends、FRED、BLS） |
| signal-types.md         | 訊號分型定義與判定邏輯                   |
| seasonality-guide.md    | 季節性分解方法與解讀                     |
</reference_index>

<workflows_index>
| Workflow   | Purpose                      |
|------------|------------------------------|
| detect.md  | 快速偵測 ATH 與異常分數      |
| analyze.md | 深度分析、假說生成、驗證清單 |
| verify.md  | 驗證社群貼文/圖表主張        |
| compare.md | 多主題趨勢共振分析           |
</workflows_index>

<templates_index>
| Template               | Purpose              |
|------------------------|----------------------|
| output-schema.yaml     | 標準輸出 JSON schema |
| hypothesis-output.yaml | 假說生成輸出格式     |
</templates_index>

<scripts_index>
| Script                | Purpose                          |
|-----------------------|----------------------------------|
| trend_analyzer.py     | 核心分析邏輯（抓取、分解、偵測） |
| hypothesis_builder.py | 假說生成與驗證清單建構           |
</scripts_index>

<examples_index>
**範例輸出** (`examples/`)

| 文件                        | 內容                          |
|-----------------------------|-------------------------------|
| health_insurance_ath.json   | Health Insurance ATH 偵測範例 |
| seasonal_vs_anomaly.json    | 季節性 vs 異常判定範例        |
| multi_topic_comparison.json | 多主題比較範例                |
</examples_index>

<quick_start>
**快速開始：**

```python
# 偵測 Health Insurance 是否創 ATH
from scripts.trend_analyzer import analyze_google_trends_ath_signal

result = analyze_google_trends_ath_signal(
    topic="Health Insurance",
    geo="US",
    timeframe="2004-01-01 2025-12-31",
    granularity="weekly",
    seasonality_method="stl",
    anomaly_method="zscore",
    anomaly_threshold=2.5,
    related_queries=True
)

print(f"Is ATH: {result['is_all_time_high']}")
print(f"Signal Type: {result['signal_type']}")
print(f"Hypotheses: {result['hypotheses']}")
```

**CLI 快速開始：**

```bash
# 分析單一主題
python scripts/trend_analyzer.py \
  --topic "Health Insurance" \
  --geo US \
  --timeframe "2004-01-01 2025-12-31" \
  --output ./output/health_insurance.json

# 比較多個主題
python scripts/trend_analyzer.py \
  --topic "Health Insurance" \
  --compare "Unemployment,Inflation,Medicare" \
  --geo US \
  --output ./output/comparison.json
```
</quick_start>

<success_criteria>
Skill 成功執行時：
- [ ] 正確抓取 Google Trends 時間序列
- [ ] 完成季節性分解（若啟用）
- [ ] 判定 ATH 狀態與異常分數
- [ ] 識別訊號類型（seasonal/event/regime）
- [ ] 提取 related queries 驅動詞彙
- [ ] 生成可檢驗假說清單
- [ ] 輸出下一步驗證數據建議
</success_criteria>
