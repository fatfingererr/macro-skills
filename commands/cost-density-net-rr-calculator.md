---
description: 計算交易成本對風險報酬比的非線性衰減影響，識別獲利事件視界閾值
argument-hint: [交易參數，如 停損 pips, 佣金, 點差]
allowed-tools:
  - Read
  - Bash
  - Write
---

Read the skill file at `marketplace/skills/cost-density-net-rr-calculator/SKILL.md` and follow its instructions to help the user with: $ARGUMENTS

If user did not specify arguments, ask for the trading parameters (stop loss, commission, spread).
