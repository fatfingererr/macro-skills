---
title: 技能呈現頁面改版研究報告
date: 2026-01-13
author: Claude (codebase-researcher)
tags:
  - frontend
  - ui-redesign
  - skill-detail-page
  - skillstore-io
status: completed
related_files:
  - frontend/src/pages/SkillDetailPage.tsx
  - frontend/src/components/skills/InstallModal.tsx
  - frontend/src/types/skill.ts
  - frontend/src/services/skillService.ts
  - frontend/public/data/skills.json
last_updated: 2026-01-13
last_updated_by: Claude
---

# 技能呈現頁面改版研究報告

## 研究問題

使用者希望改版技能呈現頁面（例如：https://fatfingererr.github.io/macro-skills/#/skills/economic-indicator-analyst），參考 https://skillstore.io/zh-hans/skills/egadams-receipt-scanning-tools 的設計風格與功能區塊，新增 Claude Code 操作教學與測試問題區塊，同時調整資料呈現邏輯。

## 摘要

本研究分析了目前 macro-skills 專案中的技能詳情頁面架構，並對照 SkillStore.io 的參考設計，提出改版方案。目前的實作採用簡潔的卡片式布局，包含技能基本資訊、Markdown 內容展示與原文檢視器。改版需要新增兩個主要功能區塊：Claude Code 操作教學（包含 marketplace add 和 enable 指令）以及可互動的測試問題區塊。此外，需將安全審計欄位替換為數據源（dataLevel）呈現，並移除 ZIP 下載與 Codex 支援功能。

研究發現現有架構已具備良好的元件化基礎，包含可重用的 Button、Badge 元件，以及完整的型別定義。SkillService 已提供指令生成函數，可直接整合至新的操作教學區塊。主要挑戰在於技能資料結構需擴充以支援測試問題清單，以及設計符合參考網站風格的卡片式區塊佈局。

## 詳細發現

### 1. 現有架構分析

#### 1.1 SkillDetailPage.tsx 結構（第 32-193 行）

**ANALYZER MODE**: 理解現有頁面結構

目前的技能詳情頁面採用以下結構：

```
SkillDetailPage
├── 麵包屑導航（第 75-85 行）
├── 頂部資訊卡片（第 88-142 行）
│   ├── Emoji + 顯示名稱
│   ├── 描述文字
│   ├── Badge（dataLevel + category）
│   ├── 標籤列表
│   ├── 安裝按鈕
│   └── Meta 資訊（版本、作者、授權）
├── Markdown 內容區（第 145-149 行）
└── 技能原文檢視器（第 152-185 行）
    └── 複製按鈕功能
```

**關鍵元件與邏輯**：
- 使用 `react-router-dom` 的 `useParams` 取得 `skillId`（第 33 行）
- 透過 `fetchSkills()` 載入所有技能後篩選（第 40-46 行）
- 使用 `ReactMarkdown` 渲染技能內容（第 146-148 行）
- `generateSkillSource()` 函數生成包含 YAML frontmatter 的完整技能原始碼（第 12-30 行）

**複製功能實作**（第 156-178 行）：
```typescript
const [copied, setCopied] = useState(false);

onClick={() => {
  navigator.clipboard.writeText(generateSkillSource(skill));
  setCopied(true);
  setTimeout(() => setCopied(false), 2000);
}}
```

#### 1.2 Skill 型別定義（frontend/src/types/skill.ts）

**LOCATOR MODE**: 識別資料結構

```typescript
export interface Skill {
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
  dataLevel: DataLevel;      // ← 已存在，需在 UI 中突顯
  tools: Tool[];
  featured: boolean;
  installCount: number;
  content: string;           // ← 目前為純 Markdown
}
```

**DataLevel 型別**（第 1 行）：
```typescript
export type DataLevel = 'free-nolimit' | 'free-limit' | 'low-cost' | 'high-cost' | 'enterprise';
```

**缺少的欄位**：
- ❌ `testQuestions` - 測試問題清單
- ❌ `examplePrompts` - 範例提示詞
- ❌ `expectedResults` - 預期結果說明

#### 1.3 SkillService 指令生成函數（frontend/src/services/skillService.ts）

**ANALYZER MODE**: 理解現有服務層能力

已實作的指令生成函數：

```typescript
// 第 76-78 行：通用安裝指令
export function generateInstallCommand(_skill: Skill): string {
  return '/plugin marketplace add fatfingererr/macro-skills';
}

// 第 80-82 行：Marketplace 安裝指令
export function generateMarketplaceInstallCommand(): string {
  return '/plugin marketplace add fatfingererr/macro-skills';
}

// 第 84-86 行：技能啟用指令
export function generateSkillEnableCommand(skillId: string): string {
  return `/plugin marketplace enable macroskills/${skillId}`;
}
```

**關鍵發現**：
- ✅ 已有 `generateSkillEnableCommand()` 可直接使用
- ✅ Marketplace add 指令為固定格式
- ⚠️ 目前 `InstallModal` 僅使用 `generateInstallCommand()`（第 13 行）

#### 1.4 InstallModal 元件（frontend/src/components/skills/InstallModal.tsx）

**ANALYZER MODE**: 理解現有安裝流程

目前的安裝 Modal 結構：

```typescript
// 第 11-72 行
export default function InstallModal({ skill, onClose }: InstallModalProps) {
  const [copied, setCopied] = useState(false);
  const installCommand = generateInstallCommand(skill);

  // 複製功能（第 15-23 行）
  const handleCopy = async () => {
    await navigator.clipboard.writeText(installCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // UI 結構（第 25-71 行）
  return (
    // Modal backdrop + container
    <div className="fixed inset-0 z-50">
      // 標題 + 關閉按鈕
      // 說明文字
      // 指令展示區塊（深色背景）
      // 關閉 + 複製按鈕
    </div>
  );
}
```

**視覺風格**：
- 使用固定定位的遮罩層（`fixed inset-0 bg-black bg-opacity-25`）
- 卡片式 Modal（`bg-white rounded-xl shadow-xl`）
- 深色程式碼區塊（`bg-gray-900` + `text-green-400`）

#### 1.5 Badge 元件（frontend/src/components/common/Badge.tsx）

**ANALYZER MODE**: 理解現有 Badge 樣式系統

支援三種類型的 Badge：

```typescript
interface BadgeProps {
  type: 'dataLevel' | 'tool' | 'tag';
  value: string;
}
```

**DataLevel 顏色配置**（第 9-15 行）：
```typescript
const dataLevelColors: Record<string, string> = {
  'free-nolimit': 'bg-green-100 text-green-800',
  'free-limit': 'bg-yellow-100 text-yellow-800',
  'low-cost': 'bg-blue-100 text-blue-800',
  'high-cost': 'bg-purple-100 text-purple-800',
  'enterprise': 'bg-red-100 text-red-800',
};
```

**DataLevel 完整資訊**（frontend/src/data/categories.ts 第 24-70 行）：
```typescript
export const dataLevels: DataLevelInfo[] = [
  {
    id: 'free-nolimit',
    name: '免費不限量',
    emoji: '🟢',
    cost: '$0',
    description: '無 key、寬鬆 rate limit、或可離線資料',
  },
  // ... 其他級別
];
```

#### 1.6 技能資料範例（frontend/public/data/skills.json）

**LOCATOR MODE**: 識別實際資料結構

以 `economic-indicator-analyst` 為例（第 2-29 行）：

```json
{
  "id": "economic-indicator-analyst",
  "displayName": "經濟指標分析師",
  "description": "分析 GDP、CPI、失業率、PMI 等經濟指標...",
  "emoji": "📊",
  "version": "v1.0.0",
  "license": "MIT",
  "author": "fatfingererr",
  "authorUrl": "https://github.com/fatfingererr/macro-skills",
  "tags": ["經濟指標", "GDP", "CPI", "PMI", "失業率", "宏觀經濟"],
  "category": "indicator-monitoring",
  "dataLevel": "free-nolimit",
  "tools": ["claude-code"],
  "featured": true,
  "installCount": 1250,
  "content": "# 經濟指標分析師\n\n專業的經濟指標分析助手...",
  "path": "skills/economic-indicator-analyst/SKILL.md"
}
```

**關鍵觀察**：
- `content` 欄位為完整的 Markdown 文字
- 無測試問題或範例提示詞欄位
- `dataLevel` 已存在但在 UI 中不夠突顯

### 2. SkillStore.io 參考設計分析

#### 2.1 頁面整體布局

**PATTERN MODE**: 識別設計模式

從 WebFetch 結果分析，SkillStore.io 採用以下結構：

```
頁面結構
├── 頂部導航欄（品牌 Logo + 語言切換 + 登入）
├── 麵包屑導航
├── 技能資訊區
├── Claude Code 操作教學區塊 ← 新增
│   ├── 步驟 1：下載 ZIP（不需要）
│   ├── 步驟 2：匯入設定
│   └── 步驟 3：啟用使用
├── 測試問題區塊 ← 新增
│   ├── 問題示例
│   ├── 複製按鈕
│   └── 預期結果
├── 快速參考提示（不需要）
├── 最佳實踐/禁止做法（不需要）
├── 安全審計（改為數據源）
└── 品質評分（不需要）
```

#### 2.2 Claude Code 操作教學區塊

**DOCUMENTATION MODE**: 參考設計細節

根據 WebFetch 結果，該區塊採用「三步驟指引設計」：

**參考網站的步驟**：
1. 下載技能的 ZIP 檔案 ← ❌ 不需要
2. 進入設定 → 功能 → 技能 → 匯入技能 ← ⚠️ 調整為 marketplace add
3. 測試按鈕觸發試用 ← ⚠️ 調整為 marketplace enable

**本專案應採用的步驟**：
1. **新增 Marketplace**：執行 `/plugin marketplace add fatfingererr/macro-skills`
2. **啟用技能**：執行 `/plugin marketplace enable macroskills/{skillId}`
3. **開始使用**：在 Claude Code 中輸入測試問題

**設計特點**：
- 清晰編號（1、2、3）
- 簡潔說明文字
- 線性流程引導
- 可複製的指令區塊

#### 2.3 測試問題區塊

**DOCUMENTATION MODE**: 參考互動設計

參考網站的測試區塊特點：

**結構**：
```
測試問題區塊
├── 問題示例：「如何在資料庫中記錄新支出？」
├── 複製按鈕（複製貼上互動模式）
└── 預期結果：展示虛擬環境啟用、手動錄入工具執行...
```

**互動方式**：
- 點擊複製問題文字
- 使用者貼上至 Claude Code
- 展示預期執行流程或輸出結果

**視覺設計**：
- 卡片式區塊
- 問題文字突顯
- 預期結果使用較淺的背景色

#### 2.4 視覺設計風格

**PATTERN MODE**: 識別設計系統

參考網站的設計特點：

- ✅ **現代化極簡風格**
- ✅ **Emoji 增強視覺辨識**（📋、🥉、🎯）
- ✅ **灰階按鈕與對比色強調**
- ✅ **規則的卡片式區塊分層**
- ✅ **響應式佈局**
- ✅ **清晰的資訊層級**

**與現有設計的契合度**：
- 目前的 macro-skills 已使用卡片式設計（`border border-gray-200 rounded-xl`）
- 已使用 Emoji 作為視覺識別
- 已有 Button 元件支援多種 variant
- 整體風格相近，易於整合

### 3. 資料結構擴充需求

#### 3.1 Skill 型別擴充

**需新增的欄位**：

```typescript
export interface Skill {
  // ... 現有欄位

  // 新增：測試問題清單
  testQuestions?: Array<{
    question: string;        // 問題文字
    expectedResult?: string; // 預期結果說明（選填）
  }>;

  // 新增：快速參考提示詞（選填，未來擴充用）
  quickPrompts?: string[];

  // 新增：最佳實踐（選填，未來擴充用）
  bestPractices?: string[];
}
```

#### 3.2 SkillService 擴充

**需新增的函數**：

```typescript
// 生成完整的安裝步驟說明
export function generateInstallSteps(skillId: string): Array<{
  title: string;
  command?: string;
  description: string;
}>;

// 格式化測試問題（供複製使用）
export function formatTestQuestion(question: string): string;
```

### 4. 元件設計方案

#### 4.1 新元件清單

**需建立的新元件**：

1. **InstallGuide.tsx** - Claude Code 操作教學區塊
   - 顯示三個步驟
   - 每個步驟包含指令 + 複製按鈕
   - 使用 Badge 或編號標示步驟

2. **TestQuestionsSection.tsx** - 測試問題區塊
   - 顯示測試問題清單
   - 每個問題附帶複製按鈕
   - 選填的預期結果展示

3. **DataLevelCard.tsx** - 數據源資訊卡片（選填）
   - 取代安全審計區塊
   - 顯示 dataLevel 的詳細資訊
   - 包含 emoji、成本、描述

#### 4.2 InstallGuide 元件設計

**檔案位置**：`frontend/src/components/skills/InstallGuide.tsx`

**功能需求**：
- 接收 `skillId` 作為 props
- 顯示三個安裝步驟
- 每個步驟包含可複製的指令
- 使用卡片式布局

**介面設計**：
```typescript
interface InstallGuideProps {
  skillId: string;
}

interface InstallStep {
  number: number;
  title: string;
  description: string;
  command?: string;
}
```

**視覺結構**：
```
卡片標題：「如何安裝與使用」
├── 步驟 1
│   ├── 編號標記
│   ├── 標題：「新增 Marketplace」
│   ├── 說明：「執行以下指令將技能市集加入 Claude Code」
│   └── 指令區塊 + 複製按鈕
├── 步驟 2
│   ├── 編號標記
│   ├── 標題：「啟用技能」
│   ├── 說明：「啟用指定的技能」
│   └── 指令區塊 + 複製按鈕
└── 步驟 3
    ├── 編號標記
    ├── 標題：「開始使用」
    └── 說明：「在 Claude Code 中輸入下方測試問題」
```

#### 4.3 TestQuestionsSection 元件設計

**檔案位置**：`frontend/src/components/skills/TestQuestionsSection.tsx`

**功能需求**：
- 接收測試問題陣列作為 props
- 每個問題可獨立複製
- 顯示預期結果（若有提供）
- 空狀態處理（無測試問題時隱藏）

**介面設計**：
```typescript
interface TestQuestion {
  question: string;
  expectedResult?: string;
}

interface TestQuestionsSectionProps {
  questions: TestQuestion[];
}
```

**視覺結構**：
```
卡片標題：「測試問題」
├── 問題卡片 1
│   ├── 問題文字
│   ├── 複製按鈕
│   └── 預期結果（選填，可摺疊）
├── 問題卡片 2
│   └── ...
└── 問題卡片 N
```

#### 4.4 DataLevelCard 元件設計（選填）

**檔案位置**：`frontend/src/components/skills/DataLevelCard.tsx`

**功能需求**：
- 接收 `dataLevel` 作為 props
- 顯示數據源的完整資訊
- 包含 emoji、等級名稱、成本、描述

**視覺結構**：
```
卡片標題：「數據源」
├── Emoji 圖示
├── 等級名稱（例：免費不限量）
├── 成本標籤（例：$0）
└── 詳細說明
```

### 5. 頁面布局重構方案

#### 5.1 新的頁面結構

**ANALYZER MODE**: 設計新架構

```
SkillDetailPage
├── 麵包屑導航（維持不變）
├── 頂部資訊卡片（調整 Badge 呈現）
│   ├── Emoji + 顯示名稱
│   ├── 描述文字
│   ├── Badge 列（突顯 dataLevel）
│   ├── 標籤列表
│   ├── 安裝按鈕
│   └── Meta 資訊
├── InstallGuide 元件 ← 新增
├── TestQuestionsSection 元件 ← 新增（有資料時才顯示）
├── DataLevelCard 元件 ← 新增（選填）
├── Markdown 內容區（維持不變）
└── 技能原文檢視器（維持不變）
```

#### 5.2 頂部資訊卡片調整

**需要的變更**：

1. **突顯 DataLevel**（第 98-103 行調整）：
   ```typescript
   // 原：
   <div className="flex flex-wrap items-center gap-2 mb-4">
     <Badge type="dataLevel" value={skill.dataLevel} />
     <span className="text-sm text-gray-500">
       {getCategoryName(skill.category)}
     </span>
   </div>

   // 改為：
   <div className="space-y-2 mb-4">
     <div className="flex items-center gap-2">
       <span className="text-sm font-medium text-gray-700">數據源：</span>
       <Badge type="dataLevel" value={skill.dataLevel} />
       <DataLevelInfoPopover level={skill.dataLevel} />
     </div>
     <div className="flex items-center gap-2">
       <span className="text-sm font-medium text-gray-700">分類：</span>
       <span className="text-sm text-gray-600">
         {getCategoryName(skill.category)}
       </span>
     </div>
   </div>
   ```

2. **移除安裝 Modal**（第 188-190 行）：
   - 不再使用 `InstallModal` 元件
   - 安裝說明整合至 `InstallGuide` 元件中

#### 5.3 元件插入位置

**在 SkillDetailPage.tsx 中的插入點**：

```typescript
// 第 142 行之後插入
</div>

{/* Install Guide - 新增 */}
<div className="mt-8">
  <InstallGuide skillId={skill.id} />
</div>

{/* Test Questions - 新增（條件渲染） */}
{skill.testQuestions && skill.testQuestions.length > 0 && (
  <div className="mt-8">
    <TestQuestionsSection questions={skill.testQuestions} />
  </div>
)}

{/* Data Level Info - 新增（選填） */}
<div className="mt-8">
  <DataLevelCard dataLevel={skill.dataLevel} />
</div>

{/* Content - 現有 */}
<div className="prose prose-gray max-w-none">
  ...
</div>
```

### 6. 程式碼參考與位置

#### 6.1 關鍵檔案清單

| 檔案路徑 | 功能 | 需修改 |
|---------|------|--------|
| `frontend/src/pages/SkillDetailPage.tsx` | 技能詳情頁面主元件 | ✅ 是 |
| `frontend/src/types/skill.ts` | Skill 型別定義 | ✅ 是 |
| `frontend/src/services/skillService.ts` | 技能服務層 | ✅ 是 |
| `frontend/src/components/common/Badge.tsx` | Badge 元件 | ❌ 否 |
| `frontend/src/components/common/Button.tsx` | Button 元件 | ❌ 否 |
| `frontend/src/components/skills/InstallModal.tsx` | 安裝 Modal | ⚠️ 可能廢棄 |
| `frontend/src/data/categories.ts` | 分類與 DataLevel 資料 | ❌ 否 |
| `frontend/public/data/skills.json` | 技能資料 | ✅ 是 |

#### 6.2 可重用的程式碼片段

**複製功能邏輯**（來自 SkillDetailPage.tsx 第 156-160 行）：
```typescript
const [copied, setCopied] = useState(false);

const handleCopy = () => {
  navigator.clipboard.writeText(textToCopy);
  setCopied(true);
  setTimeout(() => setCopied(false), 2000);
};
```

**複製按鈕 UI**（來自 SkillDetailPage.tsx 第 163-177 行）：
```typescript
<button
  onClick={handleCopy}
  className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
>
  {copied ? (
    <>
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
      已複製
    </>
  ) : (
    <>
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
      複製
    </>
  )}
</button>
```

**卡片式容器樣式**（來自 SkillDetailPage.tsx 第 88 行）：
```typescript
className="bg-white border border-gray-200 rounded-xl p-6 mb-8"
```

**深色程式碼區塊**（來自 SkillDetailPage.tsx 第 180-184 行）：
```typescript
<div className="bg-gray-900 rounded-xl overflow-hidden">
  <pre className="p-4 overflow-x-auto text-sm">
    <code className="text-gray-100 whitespace-pre">{code}</code>
  </pre>
</div>
```

### 7. 實作步驟建議

**DOCUMENTATION MODE**: 提供實作指引

#### 階段 1：資料結構準備

1. **修改 Skill 型別**（`frontend/src/types/skill.ts`）
   - 新增 `testQuestions` 欄位
   - 定義 `TestQuestion` 介面

2. **更新 skills.json**（`frontend/public/data/skills.json`）
   - 為現有技能新增測試問題範例
   - 至少為 `economic-indicator-analyst` 新增 2-3 個測試問題

3. **擴充 SkillService**（`frontend/src/services/skillService.ts`）
   - 新增 `generateInstallSteps()` 函數
   - 確認 `generateSkillEnableCommand()` 正確運作

#### 階段 2：元件開發

4. **建立 InstallGuide 元件**
   - 建立 `frontend/src/components/skills/InstallGuide.tsx`
   - 實作三步驟展示
   - 整合複製功能

5. **建立 TestQuestionsSection 元件**
   - 建立 `frontend/src/components/skills/TestQuestionsSection.tsx`
   - 實作問題列表與複製按鈕
   - 實作預期結果展示（可摺疊）

6. **建立 DataLevelCard 元件**（選填）
   - 建立 `frontend/src/components/skills/DataLevelCard.tsx`
   - 整合 `getDataLevelInfo()` 函數

#### 階段 3：頁面整合

7. **修改 SkillDetailPage**
   - 引入新元件
   - 調整頁面布局
   - 調整頂部卡片的 DataLevel 呈現
   - 移除或保留 InstallModal（視需求決定）

8. **測試與調整**
   - 測試複製功能
   - 測試響應式布局
   - 確認所有技能資料正確顯示

#### 階段 4：樣式優化

9. **視覺調整**
   - 確保卡片間距一致
   - 調整 Badge 突顯度
   - 優化深淺色對比

10. **無障礙檢查**
    - 鍵盤導航測試
    - 螢幕閱讀器相容性

### 8. 技術挑戰與注意事項

#### 8.1 資料遷移

**挑戰**：現有 skills.json 沒有測試問題資料

**解決方案**：
- 為新欄位設為選填（`testQuestions?`）
- 逐步為現有技能補充測試問題
- 空狀態時不顯示測試問題區塊

#### 8.2 複製功能一致性

**注意事項**：
- 目前有三處複製功能（原文檢視器、新的安裝指令、測試問題）
- 考慮抽取為自訂 Hook：`useCopyToClipboard()`

**建議的 Hook 設計**：
```typescript
// frontend/src/hooks/useCopyToClipboard.ts
export function useCopyToClipboard(timeout = 2000) {
  const [copied, setCopied] = useState(false);

  const copy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), timeout);
  };

  return { copied, copy };
}
```

#### 8.3 InstallModal 的去留

**選項 1：完全移除**
- 優點：簡化程式碼，避免重複功能
- 缺點：失去 Modal 的快速安裝流程

**選項 2：保留但重構**
- 將 Modal 改為顯示完整的三步驟指引
- 與 InstallGuide 共用邏輯

**建議**：保留 Modal，但內容改為嵌入 `<InstallGuide skillId={skill.id} />`

#### 8.4 響應式設計

**需測試的斷點**：
- 手機（< 640px）：單欄布局，指令區塊可橫向捲動
- 平板（640px - 1024px）：調整卡片寬度
- 桌面（> 1024px）：現有的 `max-w-4xl` 容器

### 9. 範例資料格式

#### 9.1 擴充後的 Skill 資料範例

```json
{
  "id": "economic-indicator-analyst",
  "displayName": "經濟指標分析師",
  "description": "分析 GDP、CPI、失業率、PMI 等經濟指標...",
  "emoji": "📊",
  "version": "v1.0.0",
  "license": "MIT",
  "author": "fatfingererr",
  "authorUrl": "https://github.com/fatfingererr/macro-skills",
  "tags": ["經濟指標", "GDP", "CPI", "PMI"],
  "category": "indicator-monitoring",
  "dataLevel": "free-nolimit",
  "tools": ["claude-code"],
  "featured": true,
  "installCount": 1250,
  "content": "# 經濟指標分析師\n\n...",
  "testQuestions": [
    {
      "question": "請分析最新公佈的美國 CPI 數據：整體 CPI 年增 3.2%、核心 CPI 年增 4.0%、月增 0.4%",
      "expectedResult": "分析師會提供：\n1. 數據解讀（與預期值、前值比較）\n2. 趨勢分析\n3. 市場影響評估（股市、債市、匯市）\n4. 政策啟示"
    },
    {
      "question": "比較最新的 PMI 製造業與服務業指數，分析經濟景氣狀況",
      "expectedResult": "會分析兩個指數的相對強弱，判斷經濟擴張或收縮趨勢"
    },
    {
      "question": "解讀上個月的非農就業報告，包括新增就業人數、失業率與薪資成長",
      "expectedResult": "會提供就業市場健康度評估，並分析對 Fed 政策的潛在影響"
    }
  ]
}
```

### 10. 視覺設計 Mock

#### 10.1 InstallGuide 區塊

```
┌─────────────────────────────────────────────────┐
│ 📦 如何安裝與使用                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ ① 新增 Marketplace                              │
│   執行以下指令將技能市集加入 Claude Code         │
│   ┌─────────────────────────────────────────┐   │
│   │ /plugin marketplace add fatfingererr... │ 📋│
│   └─────────────────────────────────────────┘   │
│                                                 │
│ ② 啟用技能                                      │
│   啟用指定的技能                                │
│   ┌─────────────────────────────────────────┐   │
│   │ /plugin marketplace enable macroskil... │ 📋│
│   └─────────────────────────────────────────┘   │
│                                                 │
│ ③ 開始使用                                      │
│   在 Claude Code 中輸入下方測試問題              │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 10.2 TestQuestionsSection 區塊

```
┌─────────────────────────────────────────────────┐
│ 🧪 測試問題                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌───────────────────────────────────────────┐   │
│ │ 請分析最新公佈的美國 CPI 數據：整體 CPI   │ 📋│
│ │ 年增 3.2%、核心 CPI 年增 4.0%、月增 0.4%  │   │
│ │                                           │   │
│ │ 預期結果 ▼                                │   │
│ │ 分析師會提供：                            │   │
│ │ 1. 數據解讀（與預期值、前值比較）         │   │
│ │ 2. 趨勢分析                               │   │
│ │ 3. 市場影響評估                           │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ ┌───────────────────────────────────────────┐   │
│ │ 比較最新的 PMI 製造業與服務業指數，分析   │ 📋│
│ │ 經濟景氣狀況                              │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 10.3 調整後的頂部資訊卡片

```
┌─────────────────────────────────────────────────┐
│ 📊  經濟指標分析師                         [安裝]│
│                                                 │
│ 分析 GDP、CPI、失業率、PMI 等經濟指標，提供專業  │
│ 解讀與市場影響評估                               │
│                                                 │
│ 數據源： [🟢 免費不限量] ⓘ                       │
│ 分類： 指標監控                                  │
│                                                 │
│ [經濟指標] [GDP] [CPI] [PMI] [失業率]            │
│                                                 │
├─────────────────────────────────────────────────┤
│ 版本          作者                    授權       │
│ v1.0.0        fatfingererr          MIT        │
└─────────────────────────────────────────────────┘
```

## 相關研究

- 無現有相關研究文件

## 開放問題

1. **InstallModal 元件是否要保留？**
   - 建議：保留，但內容改為嵌入 InstallGuide 元件

2. **測試問題的預期結果是否要支援 Markdown 格式？**
   - 建議：先支援純文字，未來可擴充為 Markdown

3. **是否需要為測試問題新增分類或標籤？**
   - 建議：暫不需要，先實作基本功能

4. **DataLevelCard 元件是否為必要？**
   - 建議：視覺優先度較低，可在第二階段實作

5. **是否需要為操作教學新增影片或動畫？**
   - 建議：暫不需要，先以文字與程式碼區塊呈現

6. **複製功能是否要統一抽取為自訂 Hook？**
   - 建議：是，建立 `useCopyToClipboard` Hook

## 程式碼引用

### SkillDetailPage.tsx（第 32-193 行）
- **用途**：主要頁面元件結構參考
- **關鍵邏輯**：useParams 取得 skillId、fetchSkills 載入資料、ReactMarkdown 渲染內容

### InstallModal.tsx（第 11-72 行）
- **用途**：複製功能實作參考
- **關鍵邏輯**：handleCopy 函數、copied 狀態管理

### skillService.ts（第 76-86 行）
- **用途**：指令生成函數
- **關鍵函數**：generateInstallCommand、generateMarketplaceInstallCommand、generateSkillEnableCommand

### Badge.tsx（第 9-25 行）
- **用途**：DataLevel Badge 樣式參考
- **關鍵資料**：dataLevelColors 顏色配置

### categories.ts（第 24-70 行）
- **用途**：DataLevel 完整資訊
- **關鍵資料**：dataLevels 陣列包含 name、emoji、cost、description

## 結論

本研究詳細分析了技能呈現頁面的現有架構與改版需求。主要發現包括：

1. **現有架構完整**：元件化設計良好，Badge、Button 等可直接重用
2. **指令生成就緒**：SkillService 已提供所需的指令生成函數
3. **資料結構需擴充**：需為 Skill 型別新增 testQuestions 欄位
4. **三個新元件**：InstallGuide、TestQuestionsSection、DataLevelCard
5. **複製功能統一**：建議抽取為 useCopyToClipboard Hook
6. **視覺風格一致**：參考網站與現有設計風格相近，易於整合

實作建議分為四個階段：資料結構準備、元件開發、頁面整合、樣式優化。預估工作量約 1-2 天可完成核心功能，包含測試與調整。

主要技術挑戰在於資料遷移（現有技能無測試問題）與響應式設計測試，但均有明確的解決方案。建議優先實作 InstallGuide 與 TestQuestionsSection，DataLevelCard 可視需求延後。
