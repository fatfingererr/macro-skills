---
name: google-trends-ath-detector
displayName: Google Trends 歷史新高 (ATH) 偵測器
description: 專注於 Google Trends 數據擷取與分析，使用 Selenium 模擬真人瀏覽器行為抓取數據，自動判定搜尋趨勢是否創下歷史新高（ATH）或出現異常飆升，並提供訊號分型（季節性/事件驅動/結構性轉變）。
emoji: "\U0001F4C8"
version: v0.1.1
license: MIT
author: Ricky Wang
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - Google Trends
  - 歷史新高
  - 情緒指標
  - 異常偵測
  - 搜尋趨勢
  - 訊號分型
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
      1. 使用 Selenium 模擬真人瀏覽器抓取 Google Trends 數據
      2. 抓取 2004-至今的時間序列
      3. 計算 z-score 異常分數
      4. 判定是否為 ATH
      5. 識別訊號類型 (seasonal_spike/event_driven_shock/regime_shift)
      6. 提取 related queries 作為驅動因素參考
  - question: '比較 "Unemployment" 和 "Health Insurance" 的趨勢共振'
    expectedResult: |
      分析兩個主題的相關性，判斷是「單點焦慮」還是「系統性焦慮」，
      並透過相關性分析輸出解讀。
qualityScore:
  overall: 85
  badge: 黃金
  metrics:
    architecture: 90
    maintainability: 85
    content: 90
    community: 30
    security: 95
    compliance: 90
  details: |
    **架構（90/100）**
    - Selenium 模擬真人瀏覽器行為
    - 多層防偵測策略（User-Agent 輪換、隨機延遲）
    - 清晰的訊號分型流程
    - 完整的爬蟲核心類設計

    **可維護性（85/100）**
    - 工作流程分離清晰
    - 參數定義完整
    - 專注單一數據源
    - 模組化爬蟲設計

    **內容（90/100）**
    - 完整的訊號分析框架
    - 詳細的參考文件
    - 實用的 CLI 工具

    **社區（30/100）**
    - 新技能，尚無社區貢獻

    **安全（95/100）**
    - 僅讀取公開 Google Trends 數據
    - 模擬正常瀏覽器行為

    **規範符合性（90/100）**
    - 遵循 Claude Code 規範
    - 完整的文件結構
    - 基於 design-human-like-crawler.md 設計

bestPractices:
  - title: 使用 Topic Entity 而非純關鍵字
    description: Topic Entity 可避免同名歧義（如 "Apple" 公司 vs 水果）
  - title: 關注去季節化後的殘差
    description: 單看絕對值可能被季節性誤導，殘差才是真正的「異常」
  - title: 結合 related queries 識別驅動
    description: Rising queries 能揭示「為什麼」搜尋量上升
  - title: 不要只看是否 ATH
    description: 重要的是「是否異常」而非「是否最高」
  - title: 區分訊號類型再做解讀
    description: 季節性尖峰、事件衝擊、結構轉變需要不同的解讀方式
  - title: 適當控制請求頻率
    description: 使用隨機延遲避免被 Google 偵測為機器人

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
  - title: 請求過於頻繁
    description: 短時間內大量請求會被 Google 封鎖
    consequence: 返回 429 錯誤或被要求驗證碼

faq:
  - question: Google Trends 的 0-100 指數代表什麼？
    answer: |
      這是相對指數，100 表示該時間範圍內的最高點。
      不同時間範圍或不同主題的 100 不能直接比較。

  - question: 如何區分季節性尖峰和真正的異常？
    answer: |
      本技能透過訊號分型來區分：
      - seasonal_spike：每年重複的週期性高點
      - event_driven_shock：短期異常飆升
      - regime_shift：長期結構性上升

  - question: 為什麼使用 Selenium 而非 requests/pytrends？
    answer: |
      本技能的 trend_fetcher.py 使用 Selenium 模擬真人瀏覽器行為：
      - **防偵測**：移除自動化標記、輪換 User-Agent、隨機延遲
      - **執行 JavaScript**：確保動態內容正確載入
      - **穩定性**：避免被 Google 封鎖
      - **維護 Session**：自動處理 cookies 和 tokens

  - question: 被 Google 封鎖怎麼辦？
    answer: |
      如果遇到 429 錯誤或驗證碼：
      1. 等待 24 小時後重試
      2. 增加請求間隔（使用 --no-related 減少請求）
      3. 使用 VPN 更換 IP
      4. 降低爬取頻率

  - question: 如何調試抓取問題？
    answer: |
      使用 debug 模式：
      ```bash
      python scripts/trend_fetcher.py --topic "test" --debug --no-headless
      ```
      這會：
      - 顯示瀏覽器視窗（非 headless）
      - 保存 debug_page.html 供檢查
      - 輸出詳細日誌到 trend_fetcher.log

about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 數據來源

    **專注於 Google Trends**
    - 官網：https://trends.google.com
    - 數據範圍：2004 年至今
    - 更新頻率：接近即時（2-3 天延遲）

    ## 技術架構

    基於 [design-human-like-crawler.md](thoughts/shared/guide/design-human-like-crawler.md) 設計：
    - Selenium + Chrome headless 模擬真人瀏覽器
    - BeautifulSoup 解析 HTML
    - 多層防偵測策略
---

<essential_principles>
**Google Trends ATH Detector 核心原則**

**1. 模擬真人瀏覽器行為抓取 Google Trends**

本技能使用 Selenium 模擬真人瀏覽器：
- 移除 `navigator.webdriver` 自動化標記
- 隨機輪換 User-Agent（Chrome/Firefox/Safari）
- 請求間隨機延遲（0.5-2 秒）
- 先訪問首頁建立 session，再抓取數據

**2. 訊號分型（Signal Typing）**

搜尋趨勢飆升分為三種類型：

| 類型               | 特徵                 | 解讀                         |
|--------------------|----------------------|------------------------------|
| Seasonal spike     | 每年固定月份重複     | 制度性週期（投保季、報稅季） |
| Event-driven shock | 短期尖峰、z-score 高 | 新聞/政策/突發事件           |
| Regime shift       | 趨勢線上移、持續高位 | 結構性關注上升               |

**3. 分析公式**

```
ATH 判定：latest_value >= max(history) * 0.98
異常判定：zscore >= threshold (default: 2.5)
訊號分型：based on (is_ath, is_anomaly, trend_direction)
```

**4. 描述性分析優先**

本技能提供**客觀的數學分析結果**：
- 輸出訊號類型、異常分數等量化指標
- 提取 related queries 作為驅動因素參考
- 由用戶根據專業知識自行解讀
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **Detect** - 快速偵測是否創下 ATH 或出現異常
2. **Analyze** - 深度分析訊號類型與驅動因素
3. **Compare** - 比較多個主題的趨勢共振

**等待回應後再繼續。**
</intake>

<routing>
| Response                                  | Workflow             | Description         |
|-------------------------------------------|----------------------|---------------------|
| 1, "detect", "ath", "check", "是否創新高" | workflows/detect.md  | 快速偵測 ATH 與異常 |
| 2, "analyze", "deep", "分析", "訊號"      | workflows/analyze.md | 深度分析與訊號分型  |
| 3, "compare", "對照", "共振"              | workflows/compare.md | 多主題趨勢比較      |

**讀取工作流程後，請完全遵循其步驟。**
</routing>

<reference_index>
**參考文件** (`references/`)

| 文件                 | 內容                                       |
|----------------------|--------------------------------------------|
| input-schema.md      | 完整輸入參數定義與預設值                   |
| data-sources.md      | Google Trends 數據來源與 Selenium 爬取指南 |
| signal-types.md      | 訊號分型定義與判定邏輯                     |
| seasonality-guide.md | 季節性分解方法與解讀                       |
</reference_index>

<workflows_index>
| Workflow   | Purpose                      |
|------------|------------------------------|
| detect.md  | 快速偵測 ATH 與異常分數      |
| analyze.md | 深度分析、訊號分型、驅動詞彙 |
| compare.md | 多主題趨勢共振分析           |
</workflows_index>

<templates_index>
| Template           | Purpose              |
|--------------------|----------------------|
| output-schema.yaml | 標準輸出 JSON schema |
</templates_index>

<scripts_index>
| Script           | Purpose                           |
|------------------|-----------------------------------|
| trend_fetcher.py | 核心爬蟲與分析邏輯（Selenium 版） |
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
**快速開始：安裝依賴**

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

**Python API：**

```python
from scripts.trend_fetcher import fetch_trends, analyze_ath

# 抓取數據（使用 Selenium 模擬瀏覽器）
data = fetch_trends(
    topic="Health Insurance",
    geo="US",
    timeframe="2004-01-01 2025-12-31"
)

# ATH 分析
result = analyze_ath(data, threshold=2.5)

print(f"Is ATH: {result['analysis']['is_all_time_high']}")
print(f"Signal Type: {result['analysis']['signal_type']}")
print(f"Z-Score: {result['analysis']['zscore']}")
```

**CLI 快速開始：**

```bash
# 基本分析
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --geo US \
  --output ./output/health_insurance.json

# 比較多個主題
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --compare "Unemployment,Inflation" \
  --geo US \
  --output ./output/comparison.json

# 跳過 related queries（更快、更少請求）
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --no-related \
  --output ./output/health_insurance.json

# Debug 模式（顯示瀏覽器、保存 HTML）
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --debug \
  --no-headless
```

**CLI 參數說明：**

| 參數            | 說明                 | 預設值                |
|-----------------|----------------------|-----------------------|
| `--topic`       | 搜尋主題（必要）     | -                     |
| `--geo`         | 地區代碼             | US                    |
| `--timeframe`   | 時間範圍             | 2004-01-01 2025-12-31 |
| `--threshold`   | 異常 z-score 門檻    | 2.5                   |
| `--compare`     | 比較主題（逗號分隔） | -                     |
| `--no-related`  | 跳過 related queries | false                 |
| `--no-headless` | 顯示瀏覽器視窗       | false                 |
| `--debug`       | 啟用調試模式         | false                 |
| `--output`      | 輸出 JSON 檔案路徑   | -                     |
</quick_start>

<success_criteria>
Skill 成功執行時：
- [ ] Selenium 成功啟動並模擬瀏覽器
- [ ] 正確抓取 Google Trends 時間序列
- [ ] 判定 ATH 狀態與異常分數
- [ ] 識別訊號類型（seasonal/event/regime）
- [ ] 提取 related queries 驅動詞彙（若啟用）
- [ ] 輸出結構化 JSON 結果
</success_criteria>

<anti_detection_strategy>
**防偵測策略摘要**

本技能實現以下防偵測措施（基於 design-human-like-crawler.md）：

| 策略                       | 效果               | 優先級  |
|----------------------------|--------------------|---------|
| 移除 `navigator.webdriver` | 核心，防止 JS 偵測 | 🔴 必要 |
| 隨機 User-Agent            | 避免固定 UA 被識別 | 🔴 必要 |
| 請求前隨機延遲             | 模擬人類行為       | 🔴 必要 |
| 禁用自動化擴展             | 移除 Chrome 痕跡   | 🟡 建議 |
| 先訪問首頁再 API           | 建立正常 session   | 🟡 建議 |

**Chrome 選項配置：**

```python
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
```
</anti_detection_strategy>
