# Workflow: Visualize Valuation Analysis

<required_reading>
**執行前閱讀：**
1. references/methodology.md - 了解分位數計算邏輯
2. references/valuation-metrics.md - 估值指標定義
</required_reading>

<process>

## Step 1: 確認環境

確保已安裝所需套件：

```bash
pip install pandas numpy matplotlib yfinance openpyxl xlrd
```

## Step 2: 執行視覺化分析

```bash
cd skills/detect-us-equity-valuation-percentile-extreme
python scripts/visualize_valuation.py -o output
```

**參數說明**：
- `-o, --output_dir`: 輸出目錄（預設 `output`）
- `-d, --as_of_date`: 評估日期（預設今日）
- `--show`: 顯示圖表視窗

## Step 3: 輸出檔案

執行成功後，輸出目錄會包含：

```
output/
├── us_valuation_percentile_YYYY-MM-DD.png   # 主要走勢圖
├── us_valuation_breakdown_YYYY-MM-DD.png    # 指標分解圖
└── us_valuation_analysis_YYYY-MM-DD.json    # JSON 結果
```

### 主要走勢圖說明

圖表參考 @ekwufinance 風格，包含：

1. **主軸（橙色）**：合成分位數時間序列
   - 使用擴展視窗（expanding window）計算滾動分位數
   - 每個時間點用該點之前所有歷史計算

2. **次軸（藍色）**：S&P 500 指數（對數刻度）
   - 顯示價格走勢與估值的對應關係

3. **歷史峰值標記**：
   - 1929：大蕭條前夕
   - 1965：Nifty Fifty 時期
   - 1999：科技泡沫頂點
   - 2021：疫情後牛市頂點

4. **當前位置標註**：
   - 若處於極端高估，標註「New high as of [日期]」

### 指標分解圖說明

橫向條形圖，顯示各指標當前的歷史分位數：

- **紅色**：>= 95%（極端高估）
- **橙色**：>= 80%（高估）
- **藍色**：< 80%（正常或偏低）

包含的指標：
- CAPE
- Trailing P/E
- Forward P/E
- P/B
- P/S
- EV/EBITDA
- Q Ratio
- Mkt Cap to GDP

## Step 4: 解讀結果

檢查 JSON 結果中的關鍵欄位：

```json
{
  "summary": {
    "composite_percentile": 98.4,
    "is_extreme": true,
    "status": "EXTREME_OVERVALUED"
  },
  "interpretation": {
    "headline": "美股估值處於歷史極端高估區間（第 98 分位）",
    "key_points": [...]
  }
}
```

</process>

<success_criteria>
- [ ] 主要走勢圖已生成，包含歷史峰值標記
- [ ] 指標分解圖已生成，顏色正確反映分位數水平
- [ ] JSON 結果包含完整的分析數據
- [ ] 當前位置已正確標註（若為極端）
</success_criteria>

<error_handling>

| 錯誤 | 原因 | 解決方案 |
|------|------|----------|
| Shiller 資料抓取失敗 | 網路問題或 Excel 格式變更 | 安裝 `xlrd` 和 `openpyxl` |
| 圖表字體問題 | 系統缺少中文字體 | 使用英文標題或安裝字體 |
| 資料日期不匹配 | Shiller 資料有延遲 | 腳本會自動補充最新估計值 |

</error_handling>
