# Workflow: Sweep Grid

<required_reading>
**Read these reference files NOW:**
1. references/formulas.md
</required_reading>

<process>
## Step 1: 解析網格參數

從 `grid` 物件提取：
```python
P_min = grid.get("P_min", 1)      # 最小停損
P_max = grid.get("P_max", 100)    # 最大停損
steps = grid.get("steps", 20)     # 步數
```

驗證：
```python
assert P_min > 0, "P_min must be positive"
assert P_max > P_min, "P_max must be greater than P_min"
assert 3 <= steps <= 2000, "steps must be between 3 and 2000"
```

## Step 2: 生成 P 序列

```python
import numpy as np

P_values = np.linspace(P_min, P_max, steps)
# 或使用對數刻度更清楚顯示低 P 區域
P_values = np.logspace(np.log10(P_min), np.log10(P_max), steps)
```

## Step 3: 批量計算

```python
results = []
for P in P_values:
    x = cost_density / P
    RR_net = (RR_g - x) / (1 + x)
    WR_min = (1 + x) / (1 + RR_g)
    Loss_RR = (x * (RR_g + 1)) / (RR_g * (1 + x))

    results.append({
        "P": round(P, 2),
        "x": round(x, 4),
        "RR_net": round(RR_net, 3),
        "WR_min": round(WR_min, 4),
        "Loss_RR": round(Loss_RR, 4)
    })
```

## Step 4: 識別關鍵閾值

```python
thresholds = {}

# RR_net > 0 的最小 P
for r in results:
    if r["RR_net"] > 0:
        thresholds["P_breakeven"] = r["P"]
        break

# WR_min 達到特定水平的 P
for target_wr in [0.35, 0.40, 0.50]:
    for r in results:
        if r["WR_min"] <= target_wr:
            thresholds[f"P_WR_{int(target_wr*100)}"] = r["P"]
            break

# Loss_RR 達到特定水平的 P
for target_loss in [0.20, 0.40, 0.60]:
    for r in results:
        if r["Loss_RR"] <= target_loss:
            thresholds[f"P_Loss_{int(target_loss*100)}"] = r["P"]
            break
```

## Step 5: 選取代表性數據點

選擇 5-8 個關鍵點用於報表：
```python
key_indices = [0, len(results)//4, len(results)//2,
               3*len(results)//4, len(results)-1]
summary_table = [results[i] for i in key_indices]
```

## Step 6: 組裝輸出

```json
{
  "cost_density": 2.2,
  "P_critical": 3.67,
  "thresholds": {
    "P_breakeven": 2.2,
    "P_WR_35": 5.5,
    "P_WR_40": 8.8,
    "P_Loss_20": 11.0
  },
  "summary_table": [
    {"P": 5, "x": 0.44, "RR_net": 1.78, "WR_min": 0.36, "Loss_RR": 0.41},
    {"P": 10, "x": 0.22, "RR_net": 2.28, "WR_min": 0.31, "Loss_RR": 0.24},
    {"P": 20, "x": 0.11, "RR_net": 2.60, "WR_min": 0.28, "Loss_RR": 0.13},
    {"P": 50, "x": 0.044, "RR_net": 2.83, "WR_min": 0.26, "Loss_RR": 0.06}
  ],
  "full_results": [...],
  "notes": [
    "停損從 20 降至 5 pips，效率損失從 13% 增至 41%",
    "P < 3.67 pips 進入高摩擦區",
    "建議停損維持在 10 pips 以上以保持 Loss_RR < 25%"
  ]
}
```
</process>

<success_criteria>
此工作流程完成時：
- [ ] 網格參數正確解析
- [ ] P 序列正確生成
- [ ] 批量計算正確執行
- [ ] 關鍵閾值正確識別
- [ ] 輸出包含 summary_table 和 thresholds
- [ ] 提供 zh-TW 策略建議 notes
</success_criteria>
