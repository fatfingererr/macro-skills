# Workflow: Analyze & Interpret

<required_reading>
**Read these reference files NOW:**
1. references/formulas.md
2. references/theory.md
</required_reading>

<process>
## Step 1: 執行計算

根據輸入決定執行 compute 或 sweep 工作流程，取得計算結果。

## Step 2: 診斷當前狀態

基於計算結果，診斷策略狀態：

```python
def diagnose(results):
    diagnosis = {
        "status": None,
        "severity": None,
        "issues": [],
        "recommendations": []
    }

    # 檢查是否在高摩擦區
    if results["P"] < results["P_critical"]:
        diagnosis["status"] = "critical"
        diagnosis["severity"] = "high"
        diagnosis["issues"].append(
            f"停損 {results['P']} pips 低於臨界值 {results['P_critical']:.1f} pips"
        )

    # 檢查效率損失
    if results["Loss_RR"] > 0.40:
        diagnosis["severity"] = "high"
        diagnosis["issues"].append(
            f"效率損失 {results['Loss_RR']*100:.1f}% 超過 40%"
        )
    elif results["Loss_RR"] > 0.20:
        diagnosis["severity"] = "medium"
        diagnosis["issues"].append(
            f"效率損失 {results['Loss_RR']*100:.1f}% 介於 20-40%"
        )

    # 檢查勝率需求
    if results["WR_min"] > 0.50:
        diagnosis["issues"].append(
            f"需要 {results['WR_min']*100:.1f}% 勝率才能打平，難以實現"
        )

    return diagnosis
```

## Step 3: 生成策略建議

```python
def generate_recommendations(diagnosis, results):
    recs = []

    if diagnosis["severity"] == "high":
        recs.append({
            "priority": "urgent",
            "action": "增加停損大小",
            "target": f"至少 {results['P_critical'] * 1.5:.1f} pips",
            "reason": "目前處於高摩擦區，成本侵蝕過度"
        })

    if results["Loss_RR"] > 0.20:
        recs.append({
            "priority": "important",
            "action": "在回測中使用 RR_net",
            "target": f"將 RR 從 {results['RR_g']} 調整為 {results['RR_net']:.2f}",
            "reason": "確保回測結果反映實際成本影響"
        })

    if results["WR_min"] > 0.40:
        recs.append({
            "priority": "important",
            "action": "提高毛 RR 目標",
            "target": "考慮 RR_g >= 4.0",
            "reason": "降低勝率門檻，增加策略容錯空間"
        })

    # 通用建議
    recs.append({
        "priority": "standard",
        "action": "選擇低成本經紀商",
        "target": "降低 c 或 s",
        "reason": "直接減少成本密度"
    })

    return recs
```

## Step 4: 解釋理論背景

提供易懂的理論解釋：

**雙曲線衰減現象**
```
當停損從 20 pips 縮小到 10 pips（減半），
成本負載 x 從 0.11 增加到 0.22（翻倍）。
這不是線性關係，而是反比關係：x = CostDensity / P

這就是為什麼微型時間框架策略特別困難：
1. 停損必須縮小以適應較小波動
2. 成本負載因此非線性增加
3. 同時訊號雜訊比下降（剪刀效應）
```

**事件視界概念**
```
P_critical 是策略的「事件視界」：
- 低於此值，RR_net 衰減加速
- 接近 P = CostDensity 時，RR_net → 0
- 低於 CostDensity，RR_net 變為負值

這是數學上的硬限制，與交易技術無關。
```

## Step 5: 組裝分析報告

```json
{
  "summary": {
    "status": "warning",
    "headline": "效率損失 24%，建議增加停損"
  },
  "diagnosis": {
    "severity": "medium",
    "issues": [
      "效率損失 24% 介於 20-40%",
      "停損接近臨界區域"
    ]
  },
  "metrics": {
    "RR_g": 3.0,
    "RR_net": 2.28,
    "efficiency": 0.76,
    "WR_min": 0.31,
    "P_current": 10,
    "P_critical": 3.67
  },
  "recommendations": [
    {
      "priority": "important",
      "action": "在回測中使用 RR_net",
      "target": "將 RR 從 3.0 調整為 2.28"
    },
    {
      "priority": "standard",
      "action": "考慮增加停損至 15-20 pips"
    }
  ],
  "theory_explanation": "...",
  "notes": [
    "您的策略目前在可接受範圍內，但接近警戒線",
    "如果進一步縮小停損，效率會急劇下降",
    "建議監控實際滑點，此模型假設理想執行"
  ]
}
```
</process>

<success_criteria>
此工作流程完成時：
- [ ] 正確診斷策略狀態（severity: low/medium/high）
- [ ] 識別所有問題點
- [ ] 生成優先級排序的建議
- [ ] 提供易懂的理論解釋
- [ ] 輸出完整的分析報告 JSON
- [ ] 所有說明使用 zh-TW
</success_criteria>
