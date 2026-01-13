---
title: Claude Plugin Marketplace 架構設計研究 - 基於 Macro Skills
date: 2026-01-13
author: Claude Code (Opus 4.5)
tags:
  - claude-plugin
  - marketplace
  - 架構設計
  - 技能系統
status: completed
related_files:
  - frontend/src/types/skill.ts
  - marketplace/marketplace.json
  - marketplace/skills/*/SKILL.md
  - scripts/build-marketplace.ts
  - frontend/src/services/skillService.ts
last_updated: 2026-01-13
last_updated_by: Claude Code
---

# Claude Plugin Marketplace 架構設計研究報告

## 研究問題

設計一個 Claude Plugin Marketplace，讓使用者可以透過以下指令快速安裝整個技能市集：

```bash
/plugin marketplace add macroskills/marketplace
```

## 摘要總結

本研究提出一套基於 Claude Plugin Marketplace 的技能分發架構，與 MCP 方式不同，採用原生 plugin marketplace 機制，讓使用者能夠：

1. **一鍵安裝整個市集**：`/plugin marketplace add macroskills/marketplace`
2. **瀏覽並啟用特定技能**：透過 marketplace 介面選擇需要的技能
3. **自動同步更新**：marketplace 更新時自動獲取最新技能

## 核心設計：Plugin Marketplace 架構

### 安裝指令設計

**主要安裝方式**：
```bash
/plugin marketplace add macroskills/marketplace
```

**進階操作**：
```bash
# 列出所有可用技能
/plugin marketplace list macroskills

# 啟用特定技能
/plugin marketplace enable macroskills/economic-indicator-analyst

# 停用特定技能
/plugin marketplace disable macroskills/economic-indicator-analyst

# 更新 marketplace
/plugin marketplace update macroskills

# 移除 marketplace
/plugin marketplace remove macroskills
```

### 目錄結構設計

```
macro-skills/
├── .claude-plugin/                     # Claude Plugin 根目錄
│   ├── manifest.json                   # Plugin 清單（必要）
│   ├── marketplace.json                # Marketplace 定義（必要）
│   └── README.md                       # Plugin 說明
├── marketplace/                        # 技能倉庫
│   ├── skills/                         # 技能目錄
│   │   ├── economic-indicator-analyst/
│   │   │   └── SKILL.md
│   │   ├── central-bank-policy-decoder/
│   │   │   └── SKILL.md
│   │   └── market-cycle-judge/
│   │       └── SKILL.md
│   └── index.json                      # 技能索引（自動生成）
├── frontend/                           # 前端網站（現有）
└── scripts/                            # 建置腳本
    └── build-marketplace.ts
```

## 核心檔案設計

### 1. manifest.json（Plugin 清單）

這是 Claude Plugin 的入口檔案，定義 plugin 的基本資訊與能力。

**檔案位置**：`.claude-plugin/manifest.json`

```json
{
  "$schema": "https://claude.ai/schemas/plugin-manifest.json",
  "id": "macroskills",
  "name": "Macro Skills",
  "displayName": "宏觀經濟技能市集",
  "version": "1.0.0",
  "description": "專為宏觀經濟分析設計的 Claude 技能集合，涵蓋經濟指標、央行政策、景氣循環等領域",
  "author": {
    "name": "Macro Skills Team",
    "url": "https://github.com/fatfingererr/macro-skills"
  },
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/fatfingererr/macro-skills.git"
  },
  "homepage": "https://fatfingererr.github.io/macro-skills/",
  "type": "marketplace",
  "marketplace": {
    "configPath": "marketplace.json",
    "skillsPath": "../marketplace/skills",
    "indexPath": "../marketplace/index.json"
  },
  "compatibility": {
    "claude": ">=1.0.0"
  },
  "keywords": [
    "economics",
    "macro",
    "finance",
    "analysis",
    "indicators"
  ]
}
```

### 2. marketplace.json（Marketplace 定義）

定義 marketplace 的完整結構，包含分類、資料等級、技能索引等。

**檔案位置**：`.claude-plugin/marketplace.json`

```json
{
  "$schema": "https://claude.ai/schemas/marketplace.json",
  "id": "macroskills/marketplace",
  "name": "Macro Skills Marketplace",
  "displayName": "宏觀經濟技能市集",
  "version": "1.0.0",
  "description": "專為宏觀經濟分析設計的 Claude 技能集合",
  "installCommand": "/plugin marketplace add macroskills/marketplace",
  "metadata": {
    "totalSkills": 3,
    "lastUpdated": "2026-01-13T00:00:00Z",
    "language": "zh-TW"
  },
  "categories": [
    {
      "id": "data-processing",
      "name": "資料處理",
      "description": "資料擷取、清理、轉換相關技能",
      "icon": "📊",
      "order": 1
    },
    {
      "id": "indicator-monitoring",
      "name": "指標監控",
      "description": "經濟指標追蹤與分析",
      "icon": "📈",
      "order": 2
    },
    {
      "id": "nowcasting",
      "name": "即時預測",
      "description": "即時經濟預測模型",
      "icon": "🔮",
      "order": 3
    },
    {
      "id": "business-cycles",
      "name": "景氣週期",
      "description": "景氣循環與經濟週期分析",
      "icon": "🔄",
      "order": 4
    },
    {
      "id": "inflation-analytics",
      "name": "通膨分析",
      "description": "通貨膨脹追蹤與預測",
      "icon": "💹",
      "order": 5
    },
    {
      "id": "labor-market",
      "name": "勞動市場",
      "description": "就業數據與勞動市場分析",
      "icon": "👷",
      "order": 6
    },
    {
      "id": "consumption-demand",
      "name": "消費需求",
      "description": "消費者行為與需求分析",
      "icon": "🛒",
      "order": 7
    },
    {
      "id": "production-investment",
      "name": "產業景氣",
      "description": "生產與投資活動分析",
      "icon": "🏭",
      "order": 8
    },
    {
      "id": "housing-shelter",
      "name": "房市居住",
      "description": "房地產市場與居住成本",
      "icon": "🏠",
      "order": 9
    },
    {
      "id": "central-bank-policy",
      "name": "央行操作",
      "description": "央行政策訊號解讀",
      "icon": "🏦",
      "order": 10
    },
    {
      "id": "policy-modeling",
      "name": "政策模型",
      "description": "經濟政策模擬與分析",
      "icon": "📋",
      "order": 11
    },
    {
      "id": "interest-rates",
      "name": "存貸利率",
      "description": "利率走勢與影響分析",
      "icon": "💰",
      "order": 12
    },
    {
      "id": "fx-factors",
      "name": "外匯因子",
      "description": "外匯市場驅動因素",
      "icon": "💱",
      "order": 13
    },
    {
      "id": "capital-flows",
      "name": "跨境金流",
      "description": "國際資本流動分析",
      "icon": "🌐",
      "order": 14
    },
    {
      "id": "credit-risk",
      "name": "信用風險",
      "description": "信用市場與風險評估",
      "icon": "⚠️",
      "order": 15
    },
    {
      "id": "liquidity-fci",
      "name": "流動性條件",
      "description": "金融流動性與條件指數",
      "icon": "💧",
      "order": 16
    },
    {
      "id": "commodity-sd",
      "name": "商品供需",
      "description": "大宗商品供需分析",
      "icon": "🛢️",
      "order": 17
    },
    {
      "id": "event-scenario",
      "name": "事件情境",
      "description": "事件風險與情境分析",
      "icon": "🎯",
      "order": 18
    }
  ],
  "dataLevels": [
    {
      "id": "free-nolimit",
      "name": "免費不限量",
      "color": "green",
      "cost": "$0",
      "description": "無 API key 需求、寬鬆存取限制、或可離線資料"
    },
    {
      "id": "free-limit",
      "name": "免費有限制",
      "color": "yellow",
      "cost": "$0",
      "description": "有 API 呼叫次數限制、日配額、延遲、或資料範圍限制"
    },
    {
      "id": "low-cost",
      "name": "小額付費",
      "color": "blue",
      "cost": "$5-$50/月",
      "description": "較高配額、更少延遲、更多資料欄位"
    },
    {
      "id": "high-cost",
      "name": "高額付費",
      "color": "purple",
      "cost": "$100-$1000+/月",
      "description": "更完整資料覆蓋、即時資料、深度分析、SLA 保證"
    },
    {
      "id": "enterprise",
      "name": "企業授權",
      "color": "red",
      "cost": "合約制",
      "description": "合約授權、終端機存取、企業級 SLA"
    }
  ],
  "skills": {
    "indexPath": "../marketplace/index.json",
    "basePath": "../marketplace/skills"
  }
}
```

### 3. index.json（技能索引）

自動生成的技能索引檔案，供 plugin marketplace 快速載入。

**檔案位置**：`marketplace/index.json`

```json
{
  "version": "1.0.0",
  "lastUpdated": "2026-01-13T00:00:00Z",
  "totalSkills": 3,
  "skills": [
    {
      "id": "economic-indicator-analyst",
      "displayName": "經濟指標分析師",
      "description": "分析 GDP、CPI、失業率、PMI 等經濟指標，提供專業解讀與市場影響評估",
      "emoji": "📊",
      "version": "v1.0.0",
      "author": "Macro Skills Team",
      "category": "indicator-monitoring",
      "dataLevel": "free-nolimit",
      "tags": ["經濟指標", "GDP", "CPI", "PMI"],
      "featured": true,
      "path": "skills/economic-indicator-analyst/SKILL.md"
    },
    {
      "id": "central-bank-policy-decoder",
      "displayName": "央行政策解碼器",
      "description": "解讀央行聲明、會議紀要、政策訊號，預測貨幣政策走向",
      "emoji": "🏦",
      "version": "v1.0.0",
      "author": "Macro Skills Team",
      "category": "central-bank-policy",
      "dataLevel": "free-nolimit",
      "tags": ["央行", "Fed", "ECB", "貨幣政策"],
      "featured": true,
      "path": "skills/central-bank-policy-decoder/SKILL.md"
    },
    {
      "id": "market-cycle-judge",
      "displayName": "景氣循環判官",
      "description": "判斷當前景氣位置、預測週期轉折點、提供投資建議",
      "emoji": "🔄",
      "version": "v1.0.0",
      "author": "Macro Skills Team",
      "category": "business-cycles",
      "dataLevel": "free-nolimit",
      "tags": ["景氣循環", "週期分析", "投資策略"],
      "featured": true,
      "path": "skills/market-cycle-judge/SKILL.md"
    }
  ]
}
```

## 安裝流程設計

### 使用者安裝流程

```
┌─────────────────────────────────────────────────────────────┐
│  使用者執行：/plugin marketplace add macroskills/marketplace │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude 解析指令                                              │
│  - 識別 marketplace ID: macroskills/marketplace              │
│  - 查找 GitHub repo: fatfingererr/macro-skills              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  讀取 .claude-plugin/manifest.json                           │
│  - 驗證 plugin 格式                                          │
│  - 確認相容性                                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  載入 .claude-plugin/marketplace.json                        │
│  - 讀取分類定義                                              │
│  - 讀取資料等級定義                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  載入 marketplace/index.json                                 │
│  - 取得所有技能清單                                          │
│  - 建立技能索引                                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  安裝完成！                                                   │
│  - 所有技能已可用                                            │
│  - 使用者可直接呼叫技能                                       │
└─────────────────────────────────────────────────────────────┘
```

### 技能呼叫方式

安裝 marketplace 後，使用者可以直接呼叫任何技能：

```
# 方式 1：直接對話
「請幫我分析最新的 CPI 數據」
→ Claude 自動使用「經濟指標分析師」技能

# 方式 2：明確指定技能
「使用經濟指標分析師，分析最新的非農就業報告」

# 方式 3：透過指令
/skill economic-indicator-analyst 分析 GDP 數據
```

## 技能定義格式

### SKILL.md 格式（維持現有格式）

```yaml
---
name: economic-indicator-analyst
displayName: 經濟指標分析師
description: 分析 GDP、CPI、失業率、PMI 等經濟指標，提供專業解讀與市場影響評估
emoji: 📊
version: v1.0.0
license: MIT
author: Macro Skills Team
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - 經濟指標
  - GDP
  - CPI
  - PMI
  - 失業率
  - 宏觀經濟
category: indicator-monitoring
dataLevel: free-nolimit
tools:
  - claude-code
featured: true
---

# 經濟指標分析師

專業的經濟指標分析助手，幫助你快速理解各類經濟數據的意義與市場影響。

## 功能特色

- 即時解讀經濟數據公布
- 分析指標之間的關聯性
- 評估對市場的潛在影響
- 提供歷史比較與趨勢分析

## 使用範例

### 分析 CPI 數據
「最新 CPI 年增率 3.2%，核心 CPI 4.1%，這對聯準會政策有什麼影響？」

### 比較多項指標
「請比較最近三個月的 PMI、就業數據、零售銷售，判斷經濟動能」
```

## 建置腳本設計

### 更新 build-marketplace.ts

需要修改建置腳本以生成 plugin 所需的檔案。

```typescript
import fs from 'fs';
import path from 'path';
import { glob } from 'glob';
import matter from 'gray-matter';

interface Skill {
  id: string;
  name: string;
  displayName: string;
  description: string;
  emoji: string;
  version: string;
  license: string;
  author: string;
  authorUrl?: string;
  tags: string[];
  category: string;
  dataLevel: string;
  tools: string[];
  featured: boolean;
  installCount: number;
  content: string;
  path: string;
}

async function buildMarketplace() {
  const skillFiles = await glob('marketplace/skills/*/SKILL.md');
  const skills: Skill[] = [];

  for (const file of skillFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const { data, content: body } = matter(content);
    const skillName = path.basename(path.dirname(file));

    const skill: Skill = {
      id: data.name || skillName,
      name: data.name || skillName,
      displayName: data.displayName || data.name,
      description: data.description || '',
      emoji: data.emoji || '📦',
      version: data.version || 'v1.0.0',
      license: data.license || 'MIT',
      author: data.author || 'Unknown',
      authorUrl: data.authorUrl,
      tags: data.tags || [],
      category: data.category || 'other',
      dataLevel: data.dataLevel || 'free-nolimit',
      tools: data.tools || ['claude-code'],
      featured: data.featured || false,
      installCount: data.installCount || 0,
      content: body.trim(),
      path: `skills/${skillName}/SKILL.md`,
    };

    skills.push(skill);
  }

  // 排序：精選優先，然後按安裝次數
  skills.sort((a, b) => {
    if (a.featured !== b.featured) return b.featured ? 1 : -1;
    return b.installCount - a.installCount;
  });

  // 1. 生成前端用的 skills.json
  const frontendOutput = path.join('frontend/public/data/skills.json');
  fs.mkdirSync(path.dirname(frontendOutput), { recursive: true });
  fs.writeFileSync(frontendOutput, JSON.stringify(skills, null, 2));

  // 2. 生成 marketplace/index.json（技能索引）
  const index = {
    version: '1.0.0',
    lastUpdated: new Date().toISOString(),
    totalSkills: skills.length,
    skills: skills.map(s => ({
      id: s.id,
      displayName: s.displayName,
      description: s.description,
      emoji: s.emoji,
      version: s.version,
      author: s.author,
      category: s.category,
      dataLevel: s.dataLevel,
      tags: s.tags.slice(0, 5),
      featured: s.featured,
      path: s.path,
    })),
  };

  fs.writeFileSync('marketplace/index.json', JSON.stringify(index, null, 2));

  console.log(`✓ 已建置 ${skills.length} 個技能`);
  console.log(`  - frontend/public/data/skills.json`);
  console.log(`  - marketplace/index.json`);
}

buildMarketplace().catch(console.error);
```

## 前端安裝指令更新

### 更新 skillService.ts

```typescript
export function generateInstallCommand(): string {
  return '/plugin marketplace add macroskills/marketplace';
}

export function generateSkillEnableCommand(skillId: string): string {
  return `/plugin marketplace enable macroskills/${skillId}`;
}
```

### 更新 InstallModal.tsx

顯示的安裝指令應改為：

```
/plugin marketplace add macroskills/marketplace
```

並說明安裝後所有技能都會可用。

## 與 MCP 方式的比較

| 項目 | MCP 方式 | Plugin Marketplace 方式 |
|------|----------|------------------------|
| 安裝指令 | `claude mcp add {skill} {url}` | `/plugin marketplace add macroskills/marketplace` |
| 安裝粒度 | 單一技能 | 整個市集 |
| 更新方式 | 手動逐一更新 | 一次更新全部 |
| 管理複雜度 | 高（多個技能要分別管理）| 低（統一管理）|
| 使用體驗 | 需記住各技能名稱 | 自動識別並使用適合的技能 |
| 離線支援 | 依技能而定 | 統一快取機制 |

## 實作步驟

### 階段 1：基礎結構（優先）

1. [ ] 建立 `.claude-plugin/` 目錄
2. [ ] 建立 `manifest.json`
3. [ ] 建立 `marketplace.json`

### 階段 2：建置整合

1. [ ] 更新 `scripts/build-marketplace.ts`
2. [ ] 生成 `marketplace/index.json`
3. [ ] 更新 CI/CD 流程

### 階段 3：前端更新

1. [ ] 更新安裝指令顯示
2. [ ] 更新安裝說明文件
3. [ ] 更新 DocsPage 說明

### 階段 4：測試驗證

1. [ ] 測試 plugin 安裝流程
2. [ ] 測試技能呼叫
3. [ ] 測試更新機制

## 開放問題

1. **Plugin Marketplace 規範**：Claude 官方是否有 plugin marketplace 的正式規範？需要確認 manifest.json 的確切格式。

2. **技能衝突處理**：當多個技能都能處理同一請求時，如何決定使用哪個？

3. **版本相容性**：marketplace 更新時，如何處理技能的向後相容？

4. **私有 Marketplace**：是否需要支援企業內部的私有 marketplace？

5. **技能依賴**：技能之間是否可能有依賴關係？

## 結論

透過 Plugin Marketplace 架構，使用者只需一個指令即可安裝整個宏觀經濟技能市集：

```bash
/plugin marketplace add macroskills/marketplace
```

這種設計相比 MCP 方式有以下優勢：

1. **簡單易用**：一個指令安裝所有技能
2. **統一管理**：所有技能作為一個整體管理
3. **自動更新**：marketplace 更新時自動同步
4. **智慧匹配**：Claude 自動選擇適合的技能處理請求
5. **一致體驗**：統一的分類和資料等級標示

建議優先實作 manifest.json 和 marketplace.json，建立基礎結構後再逐步完善其他功能。
