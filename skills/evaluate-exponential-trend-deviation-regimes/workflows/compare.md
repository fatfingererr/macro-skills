# 歷史對照分析工作流

將當前偏離度與歷史峰值（2011/1980）進行詳細比較。

## 前置條件

- 使用者已執行基本偵測，或直接請求歷史對照
- 有足夠的歷史數據（建議從 1970 年開始）

## 步驟

### Step 1: 確認參數

| 參數 | 來源 | 預設值 |
|------|------|--------|
| symbol | 使用者提供 | GC=F |
| compare_peak_dates | 使用者提供 | ["2011-09-06", "1980-01-21"] |
| output_format | 使用者提供 | markdown |

### Step 2: 執行對照腳本

```bash
cd skills/evaluate-exponential-trend-deviation-regimes
python scripts/trend_deviation.py \
  --symbol {symbol} \
  --start 1970-01-01 \
  --compare-peaks "2011-09-06,1980-01-21" \
  --detailed
```

### Step 3: 解讀歷史對照結果

腳本輸出包含詳細的歷史比較：

```json
{
  "historical_comparison": {
    "current": {
      "date": "2026-01-14",
      "distance_pct": 92.4,
      "percentile": 97.8
    },
    "reference_peaks": {
      "2011-09-06": {
        "distance_pct": 85.1,
        "context": "Post-GFC QE fears, safe haven demand",
        "aftermath": "Multi-year bear market followed"
      },
      "1980-01-21": {
        "distance_pct": 320.7,
        "context": "1970s high inflation finale",
        "aftermath": "20-year bear market followed"
      }
    },
    "verdicts": {
      "surpassed_2011": true,
      "distance_to_1980_pct_points": 228.3,
      "percentile_vs_2011": "higher",
      "percentile_vs_1980": "lower"
    }
  }
}
```

### Step 4: 生成對照報告

報告應包含：

1. **對照表格**

```
┌──────────────────┬────────┬────────────────────────────────┐
│ 時點             │ 偏離度 │ 歷史脈絡                       │
├──────────────────┼────────┼────────────────────────────────┤
│ 當前 (2026-01)   │ 92.4%  │ --                             │
├──────────────────┼────────┼────────────────────────────────┤
│ 2011-09 峰值     │ 85.1%  │ 後金融危機 QE 擔憂             │
├──────────────────┼────────┼────────────────────────────────┤
│ 1980-01 峰值     │ 320.7% │ 1970s 高通膨終局               │
└──────────────────┴────────┴────────────────────────────────┘
```

2. **視覺化描述**
   - 當前位置在歷史分布中的位置
   - 與兩個峰值的距離

3. **脈絡解讀**
   - 2011 之後發生了什麼
   - 1980 之後發生了什麼
   - 當前情況的相似與差異

## 歷史峰值判定邏輯

```python
def find_historical_peaks(distance_series: pd.Series, years: list[int]) -> dict:
    """找出指定年份的偏離度峰值"""
    peaks = {}
    for year in years:
        year_data = distance_series[distance_series.index.year == year]
        if not year_data.empty:
            peak_idx = year_data.idxmax()
            peaks[str(year)] = {
                "date": peak_idx.strftime("%Y-%m-%d"),
                "distance_pct": float(year_data.loc[peak_idx]),
            }
    return peaks
```

## 脈絡資訊

### 2011 峰值脈絡

- **驅動因素**：
  - 2008 金融危機後的避險需求
  - 美聯儲量化寬鬆（QE1, QE2）
  - 歐債危機
  - 美國債務上限危機

- **後續發展**：
  - 2011-2015：黃金熊市，跌幅約 45%
  - 2015-2018：底部盤整
  - 2019 起：新一輪牛市

### 1980 峰值脈絡

- **驅動因素**：
  - 1970s 高通膨（CPI 曾達 14%）
  - 石油危機
  - 美元脫鉤黃金（1971 布雷頓森林體系瓦解）
  - Volcker 尚未大幅升息

- **後續發展**：
  - Volcker 大幅升息（聯邦基金利率達 20%）
  - 通膨被壓制
  - 黃金進入長達 20 年的熊市

## 風險提示

當前偏離度若已超過 2011：
- 不代表必然下跌，需看行情體質
- 1970s-like 體質下，可以延續更久
- 2000s-like 體質下，回歸風險較高

## 輸出範例

見 `templates/output-markdown.md` 中的歷史對照報告模板
