# 單資產偵測工作流

偵測單一資產是否處於 ATR 擠壓行情。

## 前置條件

- 使用者提供了資產代碼（symbol）
- 或使用預設資產（SI=F 白銀期貨）

## 步驟

### Step 1: 確認參數

從使用者輸入解析以下參數：

| 參數       | 來源       | 預設值          |
|------------|------------|-----------------|
| symbol     | 使用者提供 | SI=F            |
| start_date | 使用者提供 | today - 5 years |
| end_date   | 使用者提供 | today           |
| timeframe  | 使用者提供 | 1d              |

若使用者未提供，使用預設值。

### Step 2: 執行偵測腳本

```bash
cd skills/detect-atr-squeeze-regime
python scripts/atr_squeeze.py \
  --symbol {symbol} \
  --start {start_date} \
  --end {end_date} \
  --timeframe {timeframe}
```

### Step 3: 解讀輸出

腳本輸出 JSON 格式結果，包含：

```json
{
  "symbol": "SI=F",
  "as_of": "2026-01-14",
  "regime": "volatility_dominated_squeeze",
  "atr_pct": 7.23,
  "atr_ratio_to_baseline": 2.41,
  "baseline_atr_pct": 3.0,
  "tech_level_reliability": "low",
  "tech_level_reliability_score": 28,
  "risk_adjustments": {
    "suggested_stop_atr_mult": 2.5,
    "position_scale": 0.41,
    "recommended_timeframe": "weekly",
    "instrument_suggestion": "options_or_spreads"
  },
  "interpretation": {
    "regime_explanation": "...",
    "tactics": ["...", "..."]
  },
  "rsi": 72.5
}
```

### Step 4: 生成報告

根據 `templates/output-markdown.md` 模板格式化報告。

報告應包含：

1. **當前狀態表格**
   - ATR% 數值
   - 對基準倍率
   - 行情判定

2. **技術位可靠度評分**
   - 0-100 分
   - 對應文字描述（高/中/低）

3. **風控調整建議**
   - 停損倍數
   - 倉位縮放
   - 時間框架建議
   - 工具選擇建議

4. **行情解讀**
   - 當前市場特徵
   - 被迫流解釋（如適用）

5. **戰術建議清單**

## 行情判定邏輯

```python
if atr_pct >= 6.0 and ratio >= 2.0:
    regime = "volatility_dominated_squeeze"
    reliability = "low"
elif ratio >= 1.2:
    regime = "elevated_volatility_trend"
    reliability = "medium"
else:
    regime = "orderly_market"
    reliability = "high"
```

## 技術位可靠度評分

```python
if regime == "volatility_dominated_squeeze":
    score = max(0, 50 - (ratio - 2.0) * 20)  # 2.0x -> 50, 4.5x -> 0
elif regime == "elevated_volatility_trend":
    score = 50 + (2.0 - ratio) * 50 / 0.8   # 1.2x -> 100, 2.0x -> 50
else:
    score = 100 - (ratio - 0.8) * 25        # 0.8x -> 100, 1.2x -> 90
```

## 風控建議規則

| Regime   | 停損倍數    | 倉位縮放 | 時間框架 | 工具         |
|----------|-------------|----------|----------|--------------|
| orderly  | 1.0-1.5 ATR | 1.0      | 任意     | 裸倉位       |
| elevated | 1.5-2.0 ATR | 0.6-0.8  | 日線以上 | 裸倉位或期權 |
| squeeze  | 2.0-3.0 ATR | 0.3-0.5  | 週線以上 | 期權/價差    |

## 錯誤處理

- 若無法取得資料，提示使用者檢查 symbol 是否正確
- 若資料不足（< 756 天），警告基準期可能不準確
- 若 yfinance 失敗，建議使用 Stooq 替代

## 輸出範例

見 `examples/xagusd-squeeze-2024.json`
