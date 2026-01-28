# 指數 Top N 分析工作流程

分析指數成分股的累積報酬率，找出表現最佳的 Top N 標的。

---

## 使用場景

- 找出某指數中表現最好的股票
- 了解指數內部的分化情況
- 識別龍頭股與落後股
- 評估「打敗指數」的難度

---

## 支援的指數

| 代碼      | 名稱              | 成分股數 |
|-----------|-------------------|----------|
| nasdaq100 | 納斯達克 100 指數 | ~100     |
| sp100     | 標普 100 指數     | 100      |
| dow30     | 道瓊工業 30 指數  | 30       |
| sox       | 費城半導體指數    | 30       |

---

## 執行步驟

### 1. 基本分析

```bash
cd skills/track-equity-cumulative-return/scripts

# Nasdaq 100 Top N
python index_component_analyzer.py --index nasdaq100 --year 2022

# S&P 100 Top N
python index_component_analyzer.py --index sp100 --year 2022

# 費城半導體 Top N
python index_component_analyzer.py --index sox --year 2022
```

### 2. 調整 Top N

```bash
# Top 10
python index_component_analyzer.py --index nasdaq100 --year 2022 --top 10

# Top 30
python index_component_analyzer.py --index nasdaq100 --year 2022 --top 30
```

### 3. 生成視覺化圖表

```bash
# Nasdaq 100 Top N 圖表
python visualize_cumulative.py --mode top20 --index nasdaq100 --year 2022

# S&P 100 Top N 圖表
python visualize_cumulative.py --mode top20 --index sp100 --year 2022

# 費城半導體 Top 15 圖表
python visualize_cumulative.py --mode top20 --index sox --year 2022 --top 15
```

### 4. 輸出 JSON

```bash
python index_component_analyzer.py --index nasdaq100 --year 2022 --output result.json
```

---

## 輸出範例

### 文字報告

```
====================================================================================================
Nasdaq 100 成分股績效排名
分析期間: 2022-01-03 ~ 2026-01-28 (4.07 年)
====================================================================================================

排名   代碼     名稱                       累積報酬率     vs 基準
--------------------------------------------------------------------------------
1     NVDA     NVIDIA (NVDA)               +320.50%     +275.30% ✓
2     META     Meta (META)                 +250.20%     +205.00% ✓
3     AMD      AMD (AMD)                   +180.20%     +135.00% ✓
4     AVGO     Broadcom (AVGO)             +120.50%      +75.30% ✓
5     NFLX     Netflix (NFLX)              +110.30%      +65.10% ✓
...
20    AAPL     Apple (AAPL)                 +65.30%      +20.10% ✓
--------------------------------------------------------------------------------
基準   ^GSPC    S&P 500                      +45.20%
================================================================================

統計:
  - 分析股票數: 98 / 100
  - 打敗基準: 45 支 (45.9%)
  - Top N 平均報酬: +145.60%
  - 全體平均報酬: +52.30%
```

### 圖表輸出

圖表會儲存到指定路徑（預設 `output/{index}_top{n}_YYYY-MM-DD.png`），特點：

- 深色主題
- Top N 條報酬率線
- 基準線以粗虛線顯示
- 圖例顯示各股最終報酬率

---

## 分析解讀

### 打敗基準比例

| 比例  | 解讀                               |
|-------|------------------------------------|
| > 50% | 多數成分股表現優於基準，市場氣氛佳 |
| = 50% | 均衡                               |
| < 50% | 少數股票拉動指數，集中度高         |

### Top N vs 全體平均

| 情況              | 解讀                         |
|-------------------|------------------------------|
| Top N >> 全體平均 | 龍頭股領跑，指數依賴少數股票 |
| Top N ≈ 全體平均  | 分化不明顯，普漲行情         |

### 龍頭股佔比

觀察前幾名是否過度集中：
- 若第一名報酬率遠超第二名，表示單一股票主導
- 若前五名報酬率接近，表示多頭氣氛廣泛

---

## 進階應用

### 季度追蹤

```bash
# 每季執行一次，觀察排名變化
python index_component_analyzer.py --index nasdaq100 --year 2025 --output result_2025Q1.json
```

### 跨指數比較

```bash
# 分別分析不同指數
python index_component_analyzer.py --index nasdaq100 --year 2022
python index_component_analyzer.py --index sp100 --year 2022
python index_component_analyzer.py --index sox --year 2022
```

### 特定產業深入

若發現某產業表現突出，可進一步比較：

```bash
# 半導體股詳細比較
python cumulative_return_analyzer.py --ticker NVDA AMD AVGO INTC TSM QCOM MU AMAT --year 2022 --benchmark ^SOX
```

---

## 注意事項

1. **執行時間**：分析 100 支股票需要較長時間（約 2-3 分鐘）
2. **API 限制**：Yahoo Finance 可能有速率限制，使用快取可加速
3. **資料缺失**：部分股票可能因上市時間不足而被跳過
4. **倖存者偏差**：成分股列表是當前的，歷史成分可能不同

---

## 下一步

- 找到感興趣的股票後，可使用 [compare.md](compare.md) 進行詳細比較
- 單一股票詳情請參考 [quick-check.md](quick-check.md)
