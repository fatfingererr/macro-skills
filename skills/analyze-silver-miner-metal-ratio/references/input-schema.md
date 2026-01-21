# 輸入參數定義

## 核心參數

### miner_proxy

| 屬性   | 值                                  |
|--------|-------------------------------------|
| 類型   | string                              |
| 必要性 | Required                            |
| 預設值 | SIL                                 |
| 說明   | 銀礦股代表（ETF/指數/股票籃子代號） |

**可用選項：**
- `SIL` - Global X Silver Miners ETF（建議）
- `SILJ` - ETFMG Prime Junior Silver Miners ETF
- `GDXJ` - VanEck Junior Gold Miners ETF（含部分銀礦股）

**自建指數範例：**
```
CDE,HL,AG,PAAS,MAG  # 以逗號分隔的股票代號
```

---

### metal_proxy

| 屬性   | 值                                 |
|--------|------------------------------------|
| 類型   | string                             |
| 必要性 | Required                           |
| 預設值 | SI=F                               |
| 說明   | 白銀價格代表（現貨/期貨/ETF 代號） |

**可用選項：**
- `SI=F` - COMEX 白銀期貨近月（建議）
- `XAGUSD=X` - 白銀現貨/美元
- `SLV` - iShares Silver Trust ETF

---

### start_date

| 屬性   | 值                  |
|--------|---------------------|
| 類型   | string (YYYY-MM-DD) |
| 必要性 | Required            |
| 預設值 | 10 年前             |
| 說明   | 歷史回溯起點        |

**建議：**
- 至少 10 年以涵蓋多輪循環
- SIL ETF 成立於 2010 年，最早可用 2010-04-19

---

### end_date

| 屬性   | 值                  |
|--------|---------------------|
| 類型   | string (YYYY-MM-DD) |
| 必要性 | Optional            |
| 預設值 | 今日                |
| 說明   | 分析終點            |

---

### freq

| 屬性   | 值       |
|--------|----------|
| 類型   | string   |
| 必要性 | Optional |
| 預設值 | 1wk      |
| 說明   | 取樣頻率 |

**可用選項：**
- `1d` - 日頻
- `1wk` - 週頻（建議）
- `1mo` - 月頻

---

## 進階參數

### smoothing_window

| 屬性   | 值                        |
|--------|---------------------------|
| 類型   | int                       |
| 必要性 | Optional                  |
| 預設值 | 4                         |
| 說明   | 比率平滑視窗（週數/月數） |

**建議：**
- 週頻數據：4（約 1 個月）
- 月頻數據：3

設為 1 則不平滑。

---

### bottom_quantile

| 屬性   | 值                   |
|--------|----------------------|
| 類型   | float (0-1)          |
| 必要性 | Optional             |
| 預設值 | 0.20                 |
| 說明   | 底部估值區分位數門檻 |

**建議範圍：** 0.10 - 0.25

較小的值（如 0.10）定義更極端的底部區間。

---

### top_quantile

| 屬性   | 值                   |
|--------|----------------------|
| 類型   | float (0-1)          |
| 必要性 | Optional             |
| 預設值 | 0.80                 |
| 說明   | 頂部估值區分位數門檻 |

**建議範圍：** 0.75 - 0.90

較大的值（如 0.90）定義更極端的頂部區間。

---

### min_separation_days

| 屬性   | 值                     |
|--------|------------------------|
| 類型   | int                    |
| 必要性 | Optional               |
| 預設值 | 180                    |
| 說明   | 類比事件去重間隔（天） |

**用途：** 避免同一段低估區間被多次計算。

**建議：** 180（約 6 個月）

---

### forward_horizons

| 屬性   | 值                       |
|--------|--------------------------|
| 類型   | list[int]                |
| 必要性 | Optional                 |
| 預設值 | [252, 504, 756]          |
| 說明   | 驗證用的前瞻期（交易日） |

**對應關係：**
- 252 交易日 ≈ 1 年
- 504 交易日 ≈ 2 年
- 756 交易日 ≈ 3 年

---

### scenario_target

| 屬性   | 值            |
|--------|---------------|
| 類型   | string        |
| 必要性 | Optional      |
| 預設值 | return_to_top |
| 說明   | 情境推演目標  |

**可用選項：**
- `return_to_top` - 回到歷史頂部門檻
- `return_to_median` - 回到歷史中位數

---

## 參數組合範例

### 快速分析（所有預設）

```bash
python scripts/ratio_analyzer.py --quick
```

### 保守分析（更極端門檻）

```bash
python scripts/ratio_analyzer.py \
  --bottom-quantile 0.10 \
  --top-quantile 0.90 \
  --min-separation-days 365
```

### 短期交易訊號

```bash
python scripts/ratio_analyzer.py \
  --freq 1d \
  --smoothing-window 20 \
  --forward-horizons 21,63,126
```

### 長期循環研究

```bash
python scripts/ratio_analyzer.py \
  --freq 1mo \
  --smoothing-window 3 \
  --start-date 2010-01-01 \
  --forward-horizons 12,24,36
```
