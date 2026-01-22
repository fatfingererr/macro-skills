# 輸入參數定義

本文件定義 `detect-shanghai-silver-stock-drain` skill 的完整輸入參數。

---

## 核心參數

### start_date

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 格式 | YYYY-MM-DD |
| 必填 | 否 |
| 預設 | 3 年前 |

分析起始日期。建議至少涵蓋 3 年以確保 Z 分數計算有足夠樣本。

### end_date

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 格式 | YYYY-MM-DD |
| 必填 | 否 |
| 預設 | today |

分析結束日期。

### frequency

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 可選值 | `weekly`, `daily` |
| 預設 | `weekly` |

數據頻率。建議使用 `weekly` 與 SGE 周報對齊，減少噪音。

### include_sources

| 屬性 | 值 |
|------|-----|
| 類型 | array[string] |
| 可選值 | `["SGE"]`, `["SHFE"]`, `["SGE", "SHFE"]` |
| 預設 | `["SGE", "SHFE"]` |

納入的庫存來源。建議使用兩者合併以獲得更完整的視角。

### unit

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 可選值 | `tonnes`, `kg`, `troy_oz` |
| 預設 | `tonnes` |

輸出單位。

轉換公式：
- kg → tonnes: `/1000`
- tonnes → troy_oz: `*32150.7466`

---

## 分析參數

### smoothing_window_weeks

| 屬性 | 值 |
|------|-----|
| 類型 | integer |
| 範圍 | 1-12 |
| 預設 | 4 |

平滑視窗（週數）。用於減少單週數據噪音。

**建議**：
- 4 週（預設）：平衡敏感度與穩定性
- 2 週：更敏感，可能有更多假訊號
- 8 週：更穩定，可能延遲訊號

### z_score_window_weeks

| 屬性 | 值 |
|------|-----|
| 類型 | integer |
| 範圍 | 52-260 |
| 預設 | 156 |

Z 分數計算的歷史視窗（週數）。

**建議**：
- 156 週（3 年，預設）：涵蓋多個市場週期
- 104 週（2 年）：更敏感於近期變化
- 260 週（5 年）：更穩定的基準

### drain_threshold_z

| 屬性 | 值 |
|------|-----|
| 類型 | float |
| 範圍 | -3.0 至 -1.0 |
| 預設 | -1.5 |

判定「異常耗盡」的 Z 分數門檻。

**解讀**：
- -1.5（預設）：約有 6.7% 的觀測值會低於此門檻
- -2.0：約有 2.3% 會低於此門檻（更嚴格）
- -1.0：約有 15.9% 會低於此門檻（更寬鬆）

### accel_threshold_z

| 屬性 | 值 |
|------|-----|
| 類型 | float |
| 範圍 | 0.5 至 2.0 |
| 預設 | 1.0 |

判定「耗盡加速」的 Z 分數門檻。

**解讀**：
- +1.0（預設）：約有 15.9% 的觀測值會高於此門檻
- +1.5：約有 6.7% 會高於此門檻（更嚴格）
- +0.5：約有 30.9% 會高於此門檻（更寬鬆）

### level_percentile_threshold

| 屬性 | 值 |
|------|-----|
| 類型 | float |
| 範圍 | 0.05 至 0.50 |
| 預設 | 0.20 |

判定「庫存水位偏低」的歷史分位數門檻。

**解讀**：
- 0.20（預設）：庫存低於歷史 20% 分位
- 0.10：更嚴格，僅最低 10%
- 0.30：更寬鬆，最低 30%

---

## 交叉驗證參數

### confirm_with_markets

| 屬性 | 值 |
|------|-----|
| 類型 | boolean |
| 預設 | true |

是否使用市場側資料做交叉驗證。

### cross_validation_indicators

| 屬性 | 值 |
|------|-----|
| 類型 | array[string] |
| 可選值 | `["comex", "slv", "futures_structure", "spot_premium"]` |
| 預設 | `["comex", "slv", "futures_structure"]` |

啟用的交叉驗證指標。

| 指標 | 說明 | 數據來源 |
|------|------|----------|
| comex | COMEX 庫存變化 | CME Group |
| slv | SLV ETF 持倉變化 | MacroMicro |
| futures_structure | 期貨結構 | Yahoo Finance |
| spot_premium | 現貨溢價 | 第三方 |

---

## 輸出參數

### output_format

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 可選值 | `json`, `markdown`, `both` |
| 預設 | `json` |

輸出格式。

### output_path

| 屬性 | 值 |
|------|-----|
| 類型 | string |
| 預設 | `result.json` |

輸出檔案路徑。

### include_narrative

| 屬性 | 值 |
|------|-----|
| 類型 | boolean |
| 預設 | true |

是否包含中文敘事解讀。

### include_caveats

| 屬性 | 值 |
|------|-----|
| 類型 | boolean |
| 預設 | true |

是否包含數據口徑與限制說明。

---

## 完整範例

### 最小配置（使用預設值）

```bash
python scripts/drain_detector.py --quick
```

### 完整配置

```bash
python scripts/drain_detector.py \
  --start 2020-01-01 \
  --end 2026-01-16 \
  --frequency weekly \
  --sources SGE SHFE \
  --unit tonnes \
  --smoothing-window 4 \
  --z-window 156 \
  --drain-threshold -1.5 \
  --accel-threshold 1.0 \
  --level-threshold 0.20 \
  --cross-validate \
  --output-format both \
  --output result.json
```

### Python API 呼叫

```python
from drain_detector import DrainDetector

detector = DrainDetector(
    start_date="2020-01-01",
    end_date="2026-01-16",
    frequency="weekly",
    include_sources=["SGE", "SHFE"],
    unit="tonnes",
    smoothing_window_weeks=4,
    z_score_window_weeks=156,
    drain_threshold_z=-1.5,
    accel_threshold_z=1.0,
    level_percentile_threshold=0.20,
    confirm_with_markets=True
)

result = detector.analyze()
print(result.signal)
print(result.narrative)
```
