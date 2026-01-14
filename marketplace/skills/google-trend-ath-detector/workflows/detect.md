<required_reading>
**執行此工作流程前，請先閱讀：**
1. references/input-schema.md - 了解輸入參數
2. references/signal-types.md - 了解訊號分型
3. references/data-sources.md - 了解 Selenium 爬取方式
</required_reading>

<objective>
快速偵測指定主題是否創下 ATH（歷史新高）或出現異常飆升。
使用 Selenium 模擬真人瀏覽器行為抓取 Google Trends 數據。
</objective>

<prerequisites>
**環境準備：**

```bash
# 安裝依賴
pip install selenium webdriver-manager beautifulsoup4 lxml loguru
```

確保系統已安裝 Chrome 瀏覽器。
</prerequisites>

<process>
**Step 1: 確認參數**

詢問或確認以下必要參數：

```yaml
required:
  topic: "要分析的 Google Trends 主題"
  geo: "地區代碼（如 US, TW, JP）"
  timeframe: "時間範圍（如 2004-01-01 2025-12-31）"

optional:
  anomaly_threshold: 2.5  # z-score 門檻
  headless: true          # 是否隱藏瀏覽器
  debug: false            # 調試模式
```

**Step 2: 使用 trend_fetcher.py 抓取數據並分析**

```python
from scripts.trend_fetcher import fetch_trends, analyze_ath

# 抓取 Google Trends 數據（Selenium 自動處理 session）
data = fetch_trends(
    topic="Health Insurance",
    geo="US",
    timeframe="2004-01-01 2025-12-31",
    headless=True,   # 隱藏瀏覽器
    debug=False      # 調試模式
)

# ATH 分析（跳過 related queries 以加速）
result = analyze_ath(data, threshold=2.5, include_related=False)
```

或使用 CLI：

```bash
python scripts/trend_fetcher.py \
  --topic "Health Insurance" \
  --geo US \
  --no-related \
  --output ./output/quick_detect.json
```

**Step 3: 解讀結果**

```json
{
  "topic": "Health Insurance",
  "geo": "US",
  "analysis": {
    "latest_value": 100,
    "historical_max": 100,
    "zscore": 3.1,
    "is_all_time_high": true,
    "is_anomaly": true,
    "signal_type": "regime_shift"
  },
  "recommendation": "搜尋趨勢創下歷史新高且異常飆升，建議進一步分析驅動因素"
}
```
</process>

<decision_tree>
**根據結果決定下一步：**

| is_ath | is_anomaly | 建議 |
|--------|------------|------|
| true | true | 確認異常高點，建議 analyze workflow 深度分析 |
| true | false | 可能是季節性高點，建議檢查季節性 |
| false | true | 異常但非 ATH，可能是局部飆升 |
| false | false | 正常波動，無需進一步分析 |
</decision_tree>

<success_criteria>
此工作流程成功完成時：
- [ ] Selenium 成功啟動 Chrome 瀏覽器
- [ ] 成功抓取 Google Trends 時間序列
- [ ] 判定 ATH 狀態
- [ ] 計算異常分數
- [ ] 給出下一步建議
</success_criteria>

<error_handling>
**錯誤處理：**

1. **ChromeDriver 版本問題**
   ```bash
   pip install --upgrade webdriver-manager
   ```

2. **429 Too Many Requests / 被封鎖**
   - 等待後重試（建議 24 小時）
   - 使用 VPN 或代理
   - 增加請求間隔

3. **數據不足**
   - 縮短時間範圍
   - 確認主題名稱正確

4. **請求失敗**
   - 使用 `--debug --no-headless` 查看問題
   ```bash
   python scripts/trend_fetcher.py --topic "test" --debug --no-headless
   ```

5. **記憶體問題（Linux/Docker）**
   - 確保安裝 chromium-browser
   - 使用 `--no-sandbox` 選項（已內建）
</error_handling>

<debug_tips>
**調試技巧：**

```bash
# 顯示瀏覽器視窗觀察行為
python scripts/trend_fetcher.py --topic "test" --no-headless

# 啟用調試模式（保存 HTML、輸出日誌）
python scripts/trend_fetcher.py --topic "test" --debug

# 結合兩者
python scripts/trend_fetcher.py --topic "test" --debug --no-headless
```

調試模式會：
- 保存 `debug_page.html` 供檢查
- 輸出詳細日誌到 `trend_fetcher.log`
</debug_tips>
