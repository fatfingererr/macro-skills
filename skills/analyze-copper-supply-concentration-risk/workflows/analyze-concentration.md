# Workflow: 銅供應集中度分析

<required_reading>
**讀取以下參考文件：**
1. references/data-sources.md
2. references/concentration-metrics.md
</required_reading>

<process>

## Step 1: 確認分析參數

收集或確認以下參數：

```yaml
start_year: 1970          # 分析起始年
end_year: 2023            # 分析結束年（最新可用年）
concentration_metric: "HHI"  # HHI | CR4 | CR8
```

**若用戶未提供參數**，使用上述預設值並告知。

## Step 2: 數據擷取（Chrome CDP）

**Step 2a: 啟動 Chrome 調試模式**

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile" ^
  "https://en.macromicro.me/charts/91500/wbms-copper-mine-production-total-world"
```

**Step 2b: 等待圖表完全載入**（約 35 秒）

**Step 2c: 執行數據擷取**

```bash
cd scripts
python fetch_copper_production.py --cdp
```

## Step 3: 執行集中度分析

**快速檢查（最新年度）**：
```bash
python copper_concentration_analyzer.py --quick
```

**完整趨勢分析**：
```bash
python copper_concentration_analyzer.py --start 1970 --end 2023
```

## Step 4: 生成視覺化圖表

```bash
python visualize_copper_concentration.py \
  --cache cache/copper_production.csv \
  --output ../../output/copper_concentration.png
```

## Step 5: 輸出結果

**JSON 輸出範例：**

```json
{
  "period": {"start_year": 1970, "end_year": 2023},
  "hhi_latest": 1820,
  "hhi_first": 1650,
  "trend_direction": "上升",
  "cr4_latest": 0.562,
  "cr8_latest": 0.734,
  "market_structure": "中等集中 (Moderately Concentrated)",
  "chile_share_latest": 0.268,
  "top_producers": [
    {"country": "Chile", "share": 0.268, "production_mt": 5.26},
    {"country": "Peru", "share": 0.102, "production_mt": 2.00},
    {"country": "DRC", "share": 0.095, "production_mt": 1.86}
  ]
}
```

**關鍵觀察點：**
- HHI 是上升還是下降趨勢？
- 智利份額在哪些年份達到峰值？
- 是否有明顯的結構變化年份？

</process>

<success_criteria>
此 workflow 完成時：
- [ ] 數據已從 MacroMicro 成功抓取
- [ ] 計算 HHI, CR4, CR8 指標
- [ ] 生成國家份額排名表
- [ ] 包含時序趨勢分析
- [ ] 生成視覺化圖表
- [ ] 標註數據口徑為 mined copper content
</success_criteria>
