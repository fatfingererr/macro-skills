# Workflow: Execute Valuation Analysis

<required_reading>
**執行前閱讀：**
1. references/data-sources.md - 了解資料來源
2. references/valuation-metrics.md - 估值指標定義
3. references/input-schema.md - 完整參數說明
</required_reading>

<process>

## Step 1: 確認分析參數

**必要參數**：
- `as_of_date`: 評估日期（預設今日）
- `universe`: 市場代碼（預設 ^GSPC，標普500）

**可選參數**：
- `metrics`: 要納入的估值指標（預設 cape, mktcap_to_gdp, trailing_pe）
- `aggregation`: 合成方法（mean/median/trimmed_mean）
- `extreme_threshold`: 極端門檻（預設 95）

若用戶未指定，使用預設參數執行。

## Step 2: 抓取估值資料

執行資料抓取腳本：

```bash
cd skills/detect-us-equity-valuation-percentile-extreme
python scripts/fetch_valuation_data.py --metrics "cape,mktcap_to_gdp,trailing_pe,pb"
```

資料來源：
- **CAPE**: Shiller Online Data（http://www.econ.yale.edu/~shiller/data.htm）
- **市值/GDP**: FRED WILL5000PRFC / GDP
- **PE/PB**: Yahoo Finance 或公開 API

## Step 3: 執行分位數計算

執行主分析腳本：

```bash
python scripts/valuation_percentile.py \
  --as_of_date "2026-01-21" \
  --universe "^GSPC" \
  --metrics "cape,mktcap_to_gdp,trailing_pe" \
  --aggregation "mean" \
  --extreme_threshold 95 \
  --output "output/analysis_result.json"
```

**核心計算流程**：

1. **對齊頻率**：將所有指標對齊至月末資料
2. **計算分位數**：
   ```python
   percentile = 100.0 * (history <= current_value).sum() / len(history)
   ```
3. **合成總分**：
   ```python
   composite = np.mean([cape_pct, mktcap_gdp_pct, pe_pct])
   ```
4. **判定極端**：
   ```python
   is_extreme = composite >= extreme_threshold
   ```

## Step 4: 識別歷史類比事件

若 `is_extreme == True`，自動執行歷史事件識別：

```python
# 找出歷史上合成分位數超過門檻的峰值
peaks = find_extreme_episodes(
    composite_series,
    threshold=95,
    min_gap_days=3650  # 10 年內只保留最高點
)
```

預期輸出的歷史事件：
- 1929-09: 大蕭條前夕
- 1965-01: 60 年代牛市頂點
- 1999-12: 科技泡沫頂點
- 2021-12: 疫情後牛市頂點

## Step 5: 計算事後統計

對每個歷史極端事件，計算事後表現：

```python
forward_windows = [180, 365, 1095]  # 6個月、1年、3年

for event_date in historical_episodes:
    for window in forward_windows:
        # 計算未來 X 天報酬
        future_return = price[event_date + window] / price[event_date] - 1
        # 計算區間最大回撤
        max_drawdown = calculate_max_drawdown(price[event_date:event_date+window])
```

輸出統計：
- 未來報酬：中位數、25 分位、10 分位
- 最大回撤：中位數、75 分位、最差情境
- 波動變化：事件後 6-12 月波動上升機率

## Step 6: 產生報告

**JSON 輸出**（參照 templates/output-json.md）：
```bash
cat output/analysis_result.json
```

**Markdown 報告**（可選）：
```bash
python scripts/valuation_percentile.py --output_format markdown > output/report.md
```

報告應包含：
1. 當前結論（是否極端、綜合分位數）
2. 各指標分位數明細
3. 歷史類比事件
4. 事後統計
5. 風險解讀框架
6. 資料品質說明

## Step 7: 驗證輸出

檢查輸出完整性：
- [ ] 綜合分位數在 0-100 範圍
- [ ] 各指標分位數均已計算
- [ ] 歷史事件日期合理
- [ ] 事後統計有數據
- [ ] 資料品質說明已揭露

</process>

<success_criteria>
工作流程完成時：

- [ ] 成功抓取所有指定的估值指標資料
- [ ] 計算出綜合估值分位數
- [ ] 判定是否處於極端高估區間
- [ ] 識別歷史類比事件（若為極端）
- [ ] 計算事後統計
- [ ] 產生完整的 JSON 或 Markdown 報告
- [ ] 揭露資料品質與限制說明
</success_criteria>

<error_handling>

**常見錯誤與處理**：

| 錯誤 | 原因 | 解決方案 |
|------|------|----------|
| 資料抓取失敗 | 網路問題或資料源變更 | 使用備用資料源或本地快取 |
| 指標歷史過短 | 某些指標只有 30 年歷史 | 揭露限制，或使用可得期間最長的指標 |
| 分位數計算異常 | 資料有空值 | 先執行 dropna()，並記錄缺失比例 |
| 歷史事件為空 | 門檻設太高或資料期間太短 | 降低門檻或擴展資料期間 |

</error_handling>
