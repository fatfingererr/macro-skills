<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 了解輸入參數
2. references/signal-types.md - 了解訊號分型
3. references/data-sources.md - Selenium 爬取方式與速率限制
</required_reading>

<objective>
比較多個 Google Trends 主題的趨勢，識別共振模式，區分「單點焦慮」與「系統性焦慮」。
使用 Selenium 模擬真人瀏覽器行為抓取數據。
</objective>

<prerequisites>
**環境準備：**

```bash
# 安裝依賴
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

確保系統已安裝 Chrome 瀏覽器。

**重要警告：**
比較分析會為每個主題分別抓取數據，請求數量較多。
建議：
- 限制比較主題數量（≤3 個）
- 在非高峰時段執行
- 若被封鎖，等待 24 小時後重試
</prerequisites>

<use_cases>
**適用場景：**

1. 「Health Insurance 上升是因為整體經濟焦慮，還是醫療特定問題？」
2. 「多個經濟相關搜尋是否同時上升？」
3. 「這個訊號是孤立現象還是更廣泛趨勢的一部分？」
</use_cases>

<process>
**Step 1: 確認比較參數**

```yaml
parameters:
  primary_topic: "主要分析主題"
  compare_topics: ["對照主題1", "對照主題2", "對照主題3"]  # 建議 ≤3 個
  geo: "US"
  timeframe: "2019-01-01 2025-12-31"
```

**Step 2: 使用 trend_fetcher.py 進行比較**

```python
from scripts.trend_fetcher import compare_trends

# 比較多個主題（每個主題會分別抓取）
# 注意：會為每個主題啟動一次瀏覽器，並有隨機延遲
result = compare_trends(
    topic="Health Insurance",
    compare_terms=["Unemployment", "Inflation", "Medicare"],
    geo="US",
    timeframe="2019-01-01 2025-12-31"
)
```

或使用 CLI：

```bash
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --compare "Unemployment,Inflation,Medicare" \
  --geo US \
  --timeframe "2019-01-01 2025-12-31" \
  --output ./output/comparison.json
```

**Step 3: 解讀相關性結果**

輸出包含各主題間的 Pearson 相關係數：

```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "timeframe": "2019-01-01 2025-12-31",
  "compare_correlations": {
    "Unemployment": 0.45,
    "Inflation": 0.38,
    "Medicare": 0.72
  },
  "interpretation": "與 Medicare 高度相關（>0.7），可能為系統性焦慮而非單點焦慮",
  "analyzed_at": "2025-12-15T10:30:00"
}
```

**相關性解讀：**

| 相關係數 | 解讀 |
|----------|------|
| > 0.7 | 高度相關，同步移動 |
| 0.4 - 0.7 | 中度相關，部分同步 |
| 0.2 - 0.4 | 弱相關 |
| < 0.2 | 幾乎無關 |

**Step 4: 判定共振模式**

根據相關性組合判定：

| 模式 | 特徵 | 解讀 |
|------|------|------|
| systemic_anxiety | 多個主題同步高相關 | 整體經濟/社會焦慮 |
| isolated_signal | 主題獨立移動 | 特定事件或政策影響 |
| mixed_signal | 部分同步、部分獨立 | 需細分時間段分析 |

**Step 5: 組裝比較報告**

```python
def identify_pattern(correlations):
    high_corr_count = sum(1 for v in correlations.values() if v and v > 0.7)
    if high_corr_count >= 2:
        return "systemic_anxiety"
    elif high_corr_count == 0:
        return "isolated_signal"
    else:
        return "mixed_signal"

def generate_next_steps(result):
    pattern = identify_pattern(result.get("compare_correlations", {}))
    if pattern == "systemic_anxiety":
        return "建議關注宏觀經濟環境變化，多個相關主題同步上升"
    elif pattern == "isolated_signal":
        return "建議深入分析該主題的 related queries，識別特定驅動因素"
    else:
        return "建議分段分析不同時間段的相關性變化"

report = {
    "primary_topic": "Health Insurance",
    "compare_topics": ["Unemployment", "Inflation", "Medicare"],
    "geo": "US",
    "correlations": result["compare_correlations"],
    "interpretation": {
        "pattern": identify_pattern(result["compare_correlations"]),
        "explanation": result.get("interpretation", "")
    },
    "next_steps": generate_next_steps(result)
}
```
</process>

<pattern_interpretation>
**共振模式解讀**

| 模式 | 特徵 | 解讀 | 建議行動 |
|------|------|------|----------|
| systemic_anxiety | 多個主題同步上升 | 整體經濟焦慮，非單一問題 | 關注宏觀環境變化 |
| isolated_signal | 單一主題獨立移動 | 特定事件或政策影響 | 深入分析該主題的 related queries |
| mixed_signal | 部分同步、部分獨立 | 複合因素影響 | 分段分析不同時期 |

**範例解讀：**

- **Health Insurance + Unemployment 高相關**
  → 經濟焦慮驅動（工作不穩定 → 擔心保險）

- **Health Insurance + Medicare 高相關**
  → 醫療系統焦慮（整體醫療關注度上升）

- **Health Insurance 獨立上升**
  → 可能為政策事件（Open Enrollment、法案變動）
</pattern_interpretation>

<success_criteria>
此工作流程成功完成時：
- [ ] Selenium 成功啟動並抓取所有主題數據
- [ ] 抓取所有主題的 Google Trends 時間序列
- [ ] 計算相關係數
- [ ] 識別共振模式
- [ ] 給出解讀與下一步建議
</success_criteria>

<example_output>
```json
{
  "primary_topic": "Health Insurance",
  "compare_topics": ["Unemployment", "Inflation", "Medicare"],
  "geo": "US",
  "timeframe": "2019-01-01 2025-12-31",

  "compare_correlations": {
    "Unemployment": 0.45,
    "Inflation": 0.38,
    "Medicare": 0.72
  },

  "interpretation": "與 Medicare 高度相關（>0.7），可能為系統性焦慮而非單點焦慮",

  "pattern": "mixed_signal",
  "explanation": "Health Insurance 搜尋同時受醫療特定因素（Medicare 高相關）和經濟因素（Unemployment/Inflation 中度相關）影響"
}
```
</example_output>

<rate_limit_warning>
**速率限制警告**

比較分析會為每個主題發送獨立請求：
- 主要主題：1 次請求
- 每個比較主題：1 次請求
- 總計：1 + N 次請求（N = 比較主題數量）

**建議：**
1. 限制比較主題數量（≤3 個）
2. 腳本已內建請求間 3-6 秒隨機延遲
3. 若被封鎖，等待 24 小時後重試
4. 考慮分批執行（每次比較 1-2 個主題）

```bash
# 分批執行範例
python scripts/trend_fetcher.py --topic "Health Insurance" --compare "Unemployment" --output ./output/compare1.json
# 等待幾分鐘
python scripts/trend_fetcher.py --topic "Health Insurance" --compare "Medicare" --output ./output/compare2.json
```
</rate_limit_warning>
