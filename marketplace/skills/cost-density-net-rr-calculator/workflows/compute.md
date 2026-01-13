# Workflow: Compute Single

<required_reading>
**Read these reference files NOW:**
1. references/formulas.md
</required_reading>

<process>
## Step 1: 驗證輸入參數

檢查必要參數：
- `RR_g` (number, >= 0): 毛風險報酬比
- `P` (number, > 0): 停損大小 (pips)
- `c` (number, >= 0): 來回佣金 (帳戶貨幣)
- `s` (number, >= 0): 來回點差 (pips)
- `V` (number, > 0): 每 pip 價值 (帳戶貨幣/pip)

驗證規則：
```python
assert RR_g >= 0, "RR_g must be non-negative"
assert P > 0, "P (stop-loss) must be positive"
assert V > 0, "V (pip value) must be positive"
```

## Step 2: 計算成本密度

```python
cost_density = (c / V) + s  # pips equivalent
```

說明：將佣金轉換為 pips 等效值，加上點差。

## Step 3: 計算負載係數 x

```python
x = cost_density / P
```

說明：x 表示成本相對於停損的比例。P 越小，x 越大。

## Step 4: 計算淨風險報酬比

```python
RR_net = (RR_g - x) / (1 + x)
```

關鍵洞察：
- 當 x → 0 時，RR_net → RR_g
- 當 x → ∞ 時，RR_net → -1

## Step 5: 計算輔助指標

```python
# 效率損失
Loss_RR = (x * (RR_g + 1)) / (RR_g * (1 + x))

# 最低勝率
WR_min = (1 + x) / (1 + RR_g)

# 效率減半點
P_critical = cost_density * (RR_g + 2) / RR_g
```

## Step 6: 判斷摩擦區域

```python
if P < P_critical:
    zone = "high_friction"  # 高摩擦區
    warning = "停損低於 P_critical，效率損失超過 50%"
else:
    zone = "normal"
```

## Step 7: 組裝輸出

```json
{
  "cost_density": 2.2,
  "x": 0.11,
  "RR_net": 2.60,
  "Loss_RR": 0.133,
  "WR_min": 0.277,
  "P_critical": 3.67,
  "zone": "normal",
  "notes": [
    "成本密度 2.2 pips = 佣金等效 0.7 + 點差 1.5",
    "淨 RR 從 3.0 降至 2.60，損失 13.3%",
    "需 27.7% 勝率才能打平"
  ]
}
```
</process>

<success_criteria>
此工作流程完成時：
- [ ] 輸入參數通過驗證
- [ ] cost_density 正確計算
- [ ] x, RR_net, Loss_RR, WR_min, P_critical 正確計算
- [ ] 正確識別摩擦區域
- [ ] 輸出包含 zh-TW 說明 notes
</success_criteria>
