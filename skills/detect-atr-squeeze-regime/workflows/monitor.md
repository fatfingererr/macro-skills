# 多資產監控工作流

持續監控多個資產的 ATR 擠壓行情狀態，識別進入或退出擠壓行情的資產。

## 前置條件

- 使用者提供了資產清單
- 或使用預設的貴金屬/能源清單

## 預設監控清單

### 貴金屬
- SI=F（白銀期貨）
- GC=F（黃金期貨）

### 能源
- CL=F（原油期貨）
- NG=F（天然氣期貨）

### 股指期貨
- ES=F（S&P 500 期貨）
- NQ=F（Nasdaq 100 期貨）

## 步驟

### Step 1: 確認監控清單

從使用者輸入解析資產清單：

```
--scan SI=F,GC=F,CL=F
```

或使用預設清單。

### Step 2: 批次執行偵測

```bash
cd skills/detect-atr-squeeze-regime
python scripts/atr_squeeze.py --scan SI=F,GC=F,CL=F,NG=F
```

### Step 3: 彙整結果

輸出格式：

```json
{
  "scan_results": [
    {
      "symbol": "SI=F",
      "regime": "volatility_dominated_squeeze",
      "atr_pct": 7.23,
      "ratio": 2.41,
      "reliability_score": 28
    },
    {
      "symbol": "GC=F",
      "regime": "orderly_market",
      "atr_pct": 2.85,
      "ratio": 1.15,
      "reliability_score": 85
    }
  ],
  "summary": {
    "squeeze_count": 1,
    "elevated_count": 1,
    "orderly_count": 2,
    "highest_ratio": {"symbol": "SI=F", "ratio": 2.41},
    "lowest_ratio": {"symbol": "GC=F", "ratio": 1.15}
  }
}
```

### Step 4: 生成摘要表格

```
┌────────┬────────┬────────┬─────────────────────────────┬──────────┐
│ Symbol │ ATR%   │ Ratio  │ Regime                      │ 信任度   │
├────────┼────────┼────────┼─────────────────────────────┼──────────┤
│ SI=F   │ 7.23%  │ 2.41x  │ volatility_dominated_squeeze│ 28       │
│ GC=F   │ 2.85%  │ 1.15x  │ orderly_market              │ 85       │
│ CL=F   │ 4.12%  │ 1.48x  │ elevated_volatility_trend   │ 62       │
│ NG=F   │ 5.80%  │ 1.95x  │ elevated_volatility_trend   │ 52       │
└────────┴────────┴────────┴─────────────────────────────┴──────────┘
```

### Step 5: 識別警報條件

標記以下情況：

1. **新進入擠壓行情**
   - 前一日為 elevated 或 orderly
   - 今日為 squeeze

2. **退出擠壓行情**
   - 前一日為 squeeze
   - 今日為 elevated 或 orderly

3. **極端倍率**
   - ratio > 3.0（極端警報）

4. **倍率快速上升**
   - 5 日內 ratio 上升 > 0.5

### Step 6: 生成建議

對每個行情狀態的資產給出對應建議：

**擠壓行情資產**：
- 降槓桿、放寬停損、改用期權
- 避免短線交易

**波動偏高資產**：
- 適度放寬停損
- 注意波動擴大風險

**秩序市場資產**：
- 正常交易策略可用
- 技術分析有效

## 持續監控模式

若使用者要求持續監控：

```bash
python scripts/atr_squeeze.py --monitor --interval 3600 --webhook URL
```

- `--interval`：檢查間隔（秒）
- `--webhook`：狀態變化時發送通知

## 輸出報告結構

1. **掃描摘要表格**
2. **按行情分組的資產清單**
3. **最需關注的資產**（ratio 最高）
4. **整體建議**

## 錯誤處理

- 若某個 symbol 無法取得資料，跳過並記錄警告
- 繼續處理其他資產
- 在最終報告中標註失敗的資產
