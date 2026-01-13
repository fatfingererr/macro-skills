---
name: cost-density-net-rr-calculator
displayName: 成本密度淨風報比計算器
description: 計算交易成本對風險報酬比的非線性衰減影響。將固定佣金與點差整合為「成本密度」指標，揭示停損大小與策略效率的雙曲線關係，識別「獲利事件視界」閾值。
emoji: "🧮"
version: v0.1.0
license: MIT
author: Ricky Wang
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - 市場微結構
  - 交易成本
  - 風險報酬比
  - 勝率
  - 點差與手續費
  - 倉位規模
  - 交易成本
  - 風險報酬比
  - 勝率
  - 部位規模
category: data-processing
dataLevel: free-nolimit
tools:
  - claude-code
featured: false
installCount: 0
testQuestions:
  - question: '計算 XAU/USD 在停損 20 pips 時的淨風險報酬比（佣金 $7，點差 1.5 pips）'
    expectedResult: |
      此技能會：
      1. 計算成本密度 = (7/10 + 1.5) = 2.2 pips
      2. 計算負載係數 x = 2.2/20 = 0.11
      3. 計算 RR_net = (3.0 - 0.11)/(1 + 0.11) = 2.60
      4. 計算 WR_min = (1 + 0.11)/(1 + 3.0) = 27.7%
  - question: '掃描停損從 5 到 50 pips，找出 RR_net 下降 20% 的臨界點'
    expectedResult: |
      此技能會產生 P vs RR_net 表格，標記：
      - RR_net > 0 的最小 P
      - Loss_RR 達到 20%、40% 的 P 值
      - P_critical（效率減半點）
  - question: '分析為何微型時間框架策略難以獲利'
    expectedResult: |
      此技能會解釋：
      - 縮小停損導致成本雙曲線增長
      - 精確度需求與訊號品質的「剪刀效應」
      - 建議在回測中用 RR_net 替代 RR_g

qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 85
    maintainability: 80
    content: 90
    community: 30
    security: 100
    compliance: 80
  details: |
    **架構（85/100）**
    - ✅ 模組化 router pattern 設計
    - ✅ 清晰的公式與理論分離
    - ⚠️ Alpha 階段

    **可維護性（80/100）**
    - ✅ 工作流程分離（計算/掃描/分析）
    - ✅ 公式參考文件獨立

    **內容（90/100）**
    - ✅ 完整的數學推導
    - ✅ 實際案例（XAU/USD）

    **社區（30/100）**
    - ⚠️ 新技能，尚無社區貢獻

    **安全（100/100）**
    - ✅ 純計算，無外部數據依賴

    **規範符合性（80/100）**
    - ✅ 遵循 Claude Code 規範

bestPractices:
  - title: 確保單位一致性
    description: P（停損）和 s（點差）必須使用相同的 pip/point 基準
  - title: 使用 RR_net 進行回測
    description: 微型時間框架回測應使用 RR_net 而非 RR_g
  - title: 監控 P_critical 閾值
    description: 停損低於 P_critical 時，策略進入高摩擦區
  - title: 考慮滑點影響
    description: 此模型假設理想執行，實際交易需額外考慮滑點

pitfalls:
  - title: 單位混淆
    description: P 使用 pips 但 s 使用 points，或 c 不是 round-turn
    consequence: 計算結果完全錯誤
  - title: 忽略 R 的無關性
    description: 誤以為改變固定風險 R 會影響 RR_net
    consequence: 錯誤的部位規模決策
  - title: 線性外推
    description: 假設縮小停損會線性降低效率
    consequence: 低估微型時間框架的成本衝擊

faq:
  - question: 為什麼 RR_net 與 R（固定風險）無關？
    answer: |
      在固定風險框架中，部位規模 = R / (P × V)。
      當推導 RR_net 時，R 在分子分母同時出現並抵消，
      證明效率衰減與帳戶規模無關，僅取決於 RR_g、P 和成本密度。

  - question: 什麼是「獲利事件視界」？
    answer: |
      當停損縮小到某個臨界值以下，無論預測準確度多高，
      正期望值都變得統計上不可能達成。這個閾值稱為「事件視界」，
      類似於黑洞的概念——一旦越過，就無法逃脫負期望值。

  - question: P_critical 如何計算？
    answer: |
      P_critical = CostDensity × (RR_g + 2) / RR_g

      這是策略效率減半（RR_net = 0.5 × RR_g）時的停損大小。
      低於此值進入高摩擦區，效率急劇下降。

about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 理論來源

    基於 Sergei Sukhov 的論文：
    "Geometry of Advantage Decay: A Quantitative Model for Risk-Reward
    Degradation in High-Friction Trading Environments"

    ## 相關文獻

    - Kyle (1985): Continuous Auctions and Insider Trading
    - Glosten & Milgrom (1985): Bid-ask spread models
    - Easley & O'Hara (1987): Price, trade size, and information
---

<essential_principles>
**成本密度模型核心原則**

**1. 核心公式**

所有計算基於以下關係：

```
Cost Density = (c/V + s)           # 成本密度（pips 等效）
x = Cost Density / P               # 負載係數
RR_net = (RR_g - x) / (1 + x)      # 淨風險報酬比
WR_min = (1 + x) / (1 + RR_g)      # 最低勝率
P_critical = CostDensity × (RR_g + 2) / RR_g  # 效率減半點
```

**2. 參數定義**

| 參數 | 定義                      | 單位         |
|------|---------------------------|--------------|
| RR_g | 毛風險報酬比（目標/停損） | 無單位       |
| P    | 停損大小                  | pips/points  |
| c    | 來回佣金（每手）          | 帳戶貨幣     |
| s    | 來回點差                  | pips/points  |
| V    | 每 pip 價值（每手）       | 帳戶貨幣/pip |
| R    | 固定風險（可選，會抵消）  | 帳戶貨幣     |

**3. 關鍵洞察**

- **雙曲線衰減**: P → 0 時，x → ∞，RR_net → -1
- **R 無關性**: RR_net 不依賴固定風險 R
- **剪刀效應**: 短時間框架同時增加成本負擔與降低訊號品質

**4. 單位一致性規則**

- P 和 s 必須使用相同基準（都是 pips 或都是 points）
- c 必須是 round-turn（來回）佣金
- V 必須是每 pip 每手的價值
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **Compute** - 計算單一參數組合的成本密度與效率指標
2. **Sweep** - 掃描停損範圍，生成 RR_net/WR_min 曲線表
3. **Analyze** - 解讀結果，提供策略建議

**等待回應後再繼續。**
</intake>

<routing>
| Response                             | Workflow             | Description          |
|--------------------------------------|----------------------|----------------------|
| 1, "compute", "calculate", "single"  | workflows/compute.md | 單次計算成本密度指標 |
| 2, "sweep", "grid", "curve", "range" | workflows/sweep.md   | 網格掃描與閾值搜尋   |
| 3, "analyze", "interpret", "explain" | workflows/analyze.md | 結果解讀與策略建議   |

**讀取工作流程後，請完全遵循其步驟。**
</routing>

<reference_index>
**參考文件** (`references/`)

| 文件        | 內容                     |
|-------------|--------------------------|
| formulas.md | 完整公式推導與數學證明   |
| theory.md   | 市場微結構理論背景與文獻 |
</reference_index>

<workflows_index>
| Workflow   | Purpose                    |
|------------|----------------------------|
| compute.md | 單次計算成本密度與效率指標 |
| sweep.md   | 網格掃描與閾值搜尋         |
| analyze.md | 結果解讀與策略建議         |
</workflows_index>

<templates_index>
| Template           | Purpose          |
|--------------------|------------------|
| output-schema.yaml | 輸出 JSON schema |
| input-schema.yaml  | 輸入參數 schema  |
</templates_index>

<scripts_index>
| Script          | Purpose             |
|-----------------|---------------------|
| cost_density.py | Python 計算實作     |
| cost_density.ts | TypeScript 計算實作 |
</scripts_index>

<quick_start>
**快速計算（XAU/USD 範例）：**

輸入：
```json
{
  "RR_g": 3.0,
  "c": 7.0,
  "s": 1.5,
  "V": 10.0,
  "P": 20
}
```

計算：
```python
cost_density = 7.0/10.0 + 1.5  # = 2.2 pips
x = 2.2 / 20                    # = 0.11
RR_net = (3.0 - 0.11) / (1 + 0.11)  # = 2.60
WR_min = (1 + 0.11) / (1 + 3.0)     # = 27.7%
P_critical = 2.2 * (3.0 + 2) / 3.0  # = 3.67 pips
```

輸出：
```json
{
  "cost_density": 2.2,
  "x": 0.11,
  "RR_net": 2.60,
  "WR_min": 0.277,
  "P_critical": 3.67,
  "Loss_RR": 0.133
}
```
</quick_start>

<success_criteria>
Skill 成功執行時：
- [ ] 輸入參數通過驗證（單位一致性）
- [ ] 正確計算 cost_density、x、RR_net、WR_min
- [ ] 識別是否處於高摩擦區（P < P_critical）
- [ ] 輸出符合 outputs_schema
- [ ] 提供 zh-TW 解釋說明
</success_criteria>
