# 快速檢查工作流程

快速查看單一標的從指定年份至今的累積報酬率。

---

## 使用場景

- 快速查看某股票的長期表現
- 確認報酬率與基準的比較
- 獲取 CAGR 年化報酬率

---

## 執行步驟

### 1. 基本查詢

```bash
cd skills/track-equity-cumulative-return/scripts
python cumulative_return_analyzer.py --ticker NVDA --year 2022
```

### 2. 自訂起始年份

```bash
# 從 2020 年開始
python cumulative_return_analyzer.py --ticker NVDA --year 2020

# 從 2023 年開始
python cumulative_return_analyzer.py --ticker NVDA --year 2023
```

### 3. 自訂基準

```bash
# 使用 Nasdaq 100 作為基準
python cumulative_return_analyzer.py --ticker NVDA --year 2022 --benchmark ^NDX

# 使用費城半導體作為基準
python cumulative_return_analyzer.py --ticker NVDA --year 2022 --benchmark ^SOX
```

### 4. 輸出 JSON

```bash
python cumulative_return_analyzer.py --ticker NVDA --year 2022 --output result.json
```

---

## 輸出範例

```
==========================================================================================
累積報酬率追蹤器
標的: NVIDIA (NVDA)
基準: S&P 500
從 2022 年開始至今
==========================================================================================

正在抓取數據...
  [Fetch] NVDA: 1000 筆 (2022-01-03 ~ 2026-01-28)
  [Fetch] S&P 500 (基準)...

正在計算累積報酬率...

==========================================================================================
累積報酬率分析報告
==========================================================================================
分析期間: 2022-01-03 ~ 2026-01-28 (4.07 年)
基準指數: S&P 500
==========================================================================================

排名   代碼     名稱                  累積報酬率     年化報酬率     vs 基準
------------------------------------------------------------------------------------------
1     NVDA     NVIDIA (NVDA)          +320.50%       +52.30%     +275.30% ✓
------------------------------------------------------------------------------------------
基準   ^GSPC    S&P 500                 +45.20%       +10.10%
==========================================================================================

統計:
  - 最佳表現: NVDA (+320.50%)
  - 打敗基準: 1 / 1 支
  - 平均報酬: +320.50%
```

---

## 常見股票代碼

### 科技龍頭

```
AAPL    Apple
MSFT    Microsoft
GOOGL   Google
AMZN    Amazon
META    Meta
NFLX    Netflix
TSLA    Tesla
```

### 半導體

```
NVDA    NVIDIA
AMD     AMD
AVGO    Broadcom
INTC    Intel
TSM     台積電 ADR
QCOM    Qualcomm
```

### 指數

```
^GSPC   S&P 500
^NDX    Nasdaq 100
^DJI    Dow Jones
^SOX    費城半導體
```

---

## 下一步

- 若要比較多個標的，請參考 [compare.md](compare.md)
- 若要分析指數成分股，請參考 [top20.md](top20.md)
