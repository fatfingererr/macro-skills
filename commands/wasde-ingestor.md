---
description: 下載並解析 USDA WASDE 報告，擷取穀物、油籽、棉花、畜產品供需平衡表
argument-hint: [商品類型，如 corn, wheat, soybeans]
allowed-tools:
  - Read
  - Bash
  - Write
  - WebFetch
---

Read the skill file at `~/.claude/plugins/marketplaces/macro-skills/skills/wasde-ingestor/SKILL.md` and follow its instructions to help the user with: $ARGUMENTS

If user did not specify arguments, ask what commodity data they want to ingest.
