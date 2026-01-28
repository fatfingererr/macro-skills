# 多標的比較工作流程

比較多個股票/指數的累積報酬率表現。

---

## 使用場景

- 比較同類型股票的表現（如多個半導體股）
- 評估投資組合中各持股的貢獻
- 找出表現最佳/最差的標的

---

## 執行步驟

### 1. 基本比較

```bash
cd skills/track-equity-cumulative-return/scripts

# 比較兩支股票
python cumulative_return_analyzer.py --ticker NVDA AMD --year 2022

# 比較多支股票
python cumulative_return_analyzer.py --ticker NVDA AMD AVGO INTC --year 2022
```

### 2. 生成視覺化圖表

```bash
# 基本圖表
python visualize_cumulative.py --ticker NVDA AMD --year 2022

# 指定輸出路徑
python visualize_cumulative.py --ticker NVDA AMD GOOGL --year 2022 --output output/tech_comparison.png

# 更多標的
python visualize_cumulative.py --ticker NVDA AMD AVGO INTC TSM QCOM --year 2022
```

### 3. 科技龍頭比較

```bash
# FAANG + Tesla
python cumulative_return_analyzer.py --ticker AAPL AMZN META NFLX GOOGL TSLA --year 2022

# 生成圖表
python visualize_cumulative.py --ticker AAPL AMZN META NFLX GOOGL TSLA --year 2022
```

### 4. 半導體股比較

```bash
# 主要半導體股
python cumulative_return_analyzer.py --ticker NVDA AMD AVGO INTC TSM QCOM --year 2022 --benchmark ^SOX

# 使用費城半導體作為基準
python visualize_cumulative.py --ticker NVDA AMD AVGO INTC --year 2022 --benchmark ^SOX
```

### 5. 指數比較

```bash
# 比較不同指數
python cumulative_return_analyzer.py --ticker ^SOX ^NDX ^GSPC ^DJI --year 2022

# 圖表
python visualize_cumulative.py --ticker ^SOX ^NDX ^DJI --year 2022 --benchmark ^GSPC
```

---

## 輸出範例

### 文字報告

```
==========================================================================================
累積報酬率分析報告
==========================================================================================
分析期間: 2022-01-03 ~ 2026-01-28 (4.07 年)
基準指數: S&P 500
==========================================================================================

排名   代碼     名稱                  累積報酬率     vs 基準
----------------------------------------------------------------------
1     NVDA     NVIDIA (NVDA)          +320.50%     +275.30% ✓
2     AMD      AMD (AMD)              +180.20%     +135.00% ✓
3     AVGO     Broadcom (AVGO)        +120.50%      +75.30% ✓
4     INTC     Intel (INTC)            -25.30%      -70.50%
----------------------------------------------------------------------
基準   ^GSPC    S&P 500                 +45.20%
======================================================================

統計:
  - 最佳表現: NVDA (+320.50%)
  - 打敗基準: 3 / 4 支
  - 平均報酬: +148.98%
```

### 圖表輸出

圖表會儲存到指定路徑（預設 `output/cumulative_return_YYYY-MM-DD.png`），特點：

- 深色主題
- 每條線標註最終報酬率
- 基準線以虛線顯示
- 零線輔助參考

---

## 建議的比較組合

### 科技龍頭

```bash
python visualize_cumulative.py --ticker AAPL MSFT GOOGL AMZN META --year 2022
```

### AI 概念股

```bash
python visualize_cumulative.py --ticker NVDA AMD GOOGL MSFT META --year 2022
```

### 半導體設備

```bash
python visualize_cumulative.py --ticker AMAT LRCX KLAC ASML --year 2022 --benchmark ^SOX
```

### 電動車

```bash
python visualize_cumulative.py --ticker TSLA RIVN LCID --year 2022
```

---

## 最佳實踐

1. **相似標的比較**：比較同產業或同類型的標的更有意義
2. **適當的基準**：選擇與標的相關的基準（如半導體股用 ^SOX）
3. **合理的標的數量**：建議 2-8 個標的，太多會讓圖表難以閱讀
4. **一致的時間範圍**：確保所有標的都有足夠的歷史數據

---

## 下一步

- 若要分析整個指數的成分股，請參考 [top20.md](top20.md)
