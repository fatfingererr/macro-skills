<required_reading>
**執行前請先閱讀：**
1. references/data-sources.md - 了解 FRED 系列代碼
2. references/methodology.md - 了解事件識別邏輯
</required_reading>

<objective>
生成三軸視覺化圖表，顯示勞動市場與財政赤字的關聯：
- 歷史數據曲線（職缺、失業、赤字/GDP）
- 歷史 crossover 事件標註（失業 > 職缺時的赤字跳升）
- 情境模擬投影（mild/moderate/severe）
- 衰退期灰色陰影
</objective>

<process>

<step name="1_setup">
**Step 1: 環境準備**

確認 Python 環境與依賴：
```bash
cd skills/analyze-high-unemployment-high-gdp-growth-fiscal-deficit-scenarios
pip install pandas numpy requests matplotlib
```

確認視覺化參數：
```python
params = {
    "years": 25,              # 回看年數
    "scenario": "moderate",   # 情境類型: mild, moderate, severe, none
    "horizon": 24,            # 情境投影月數
    "output": None,           # 輸出路徑（None 則自動生成）
    "show_annotations": True, # 顯示標註
}
```
</step>

<step name="2_fetch_data">
**Step 2: 抓取視覺化所需數據**

主要需要四個 FRED 系列：
- `UNRATE`: 失業率（用於 薩姆規則）
- `UNEMPLOY`: 失業人數（千人）
- `JTSJOL`: 職缺數（千人）
- `FYFSGDA188S`: 財政赤字/GDP（%）

執行：
```bash
python scripts/visualizer.py --years 25
```

或在分析時一併生成：
```bash
python scripts/analyzer.py --visualize --scenario-type moderate
```
</step>

<step name="3_identify_events">
**Step 3: 識別 Crossover 事件**

crossover 事件定義：失業人數 > 職缺數

對每個事件記錄：
- 開始/結束日期
- 事件期間的赤字/GDP 起始值
- 事件期間的赤字/GDP 峰值
- 赤字跳升幅度（bps）

歷史上的主要 crossover 事件：
- 2001-2003：Dot-com 衰退，赤字跳升約 600 bps
- 2008-2010：金融危機，赤字跳升約 800-1200 bps
- 2020-2021：COVID，赤字跳升超過 1000 bps
</step>

<step name="4_generate_scenario">
**Step 4: 生成情境投影**

三種情境類型：

| 情境類型 | 失業峰值倍數 | 職缺谷底倍數 | 赤字跳升(pct) |
|----------|--------------|--------------|---------------|
| mild     | 1.3x         | 0.85x        | +4.0%         |
| moderate | 1.6x         | 0.70x        | +6.0%         |
| severe   | 2.0x         | 0.50x        | +10.0%        |

投影使用 S 曲線（logistic）模擬漸進式變化。
</step>

<step name="5_plot_chart">
**Step 5: 繪製圖表**

圖表元素：
1. **左軸**：失業人數（紅色）、職缺數（藍色）
2. **右軸**：財政赤字/GDP（綠色）
3. **衰退陰影**：灰色背景（NBER 衰退期）
4. **事件標註**：歷史 crossover 事件的赤字跳升幅度
5. **情境投影**：虛線顯示未來路徑

執行完整視覺化：
```bash
python scripts/visualizer.py \
    --scenario moderate \
    --years 25 \
    --output output/my_chart.png
```
</step>

<step name="6_validate">
**Step 6: 驗證輸出**

確認圖表包含：
- [ ] 三條歷史曲線正確顯示
- [ ] 左右軸刻度合理
- [ ] 衰退期陰影正確標記
- [ ] 事件標註文字清晰可讀
- [ ] 情境投影虛線延伸到未來
- [ ] 圖例完整
- [ ] 資料來源標註

確認 JSON 摘要檔案包含：
- [ ] 當前指標數值
- [ ] 歷史事件統計
- [ ] 情境投影參數
</step>

</process>

<scenario_types>

**Mild 情境**
- 假設：勞動市場小幅轉弱，失業增加 30%，職缺減少 15%
- 赤字影響：+400 bps（從 6% 到 10%）
- 適用場景：軟著陸、輕微經濟放緩

**Moderate 情境（預設）**
- 假設：勞動市場明顯轉弱，失業增加 60%，職缺減少 30%
- 赤字影響：+600 bps（從 6% 到 12%）
- 適用場景：典型衰退

**Severe 情境**
- 假設：勞動市場嚴重惡化，失業翻倍，職缺減半
- 赤字影響：+1000 bps（從 6% 到 16%+）
- 適用場景：金融危機級別衰退

</scenario_types>

<command_reference>

**直接使用視覺化腳本**
```bash
# 基本用法
python scripts/visualizer.py

# 指定情境
python scripts/visualizer.py --scenario severe

# 指定輸出路徑
python scripts/visualizer.py --output my_chart.png

# 不顯示標註
python scripts/visualizer.py --no-annotations

# 輸出 JSON 摘要
python scripts/visualizer.py --json summary.json
```

**透過分析器整合**
```bash
# 分析 + 視覺化
python scripts/analyzer.py --visualize

# 完整參數
python scripts/analyzer.py \
    --lookback 30 \
    --visualize \
    --scenario-type moderate \
    --chart-output chart.png \
    --no-show  # 不顯示圖表（僅保存）
```

</command_reference>

<success_criteria>
工作流程完成時：
- [ ] 成功抓取 FRED 數據
- [ ] 識別出歷史 crossover 事件
- [ ] 生成情境投影數據
- [ ] 輸出 PNG 圖表檔案
- [ ] 輸出 JSON 摘要檔案
- [ ] 圖表風格符合 FRED 參考樣式
</success_criteria>
