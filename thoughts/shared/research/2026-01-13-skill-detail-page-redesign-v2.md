---
title: 技能詳情頁面重新設計研究報告 v2
date: 2026-01-13
author: Claude (codebase-researcher)
tags:
  - frontend
  - ui-redesign
  - skill-detail-page
  - skillstore-io
  - react
  - typescript
status: completed
related_files:
  - frontend/src/pages/SkillDetailPage.tsx
  - frontend/src/types/skill.ts
  - frontend/src/components/skills/InstallGuide.tsx
  - frontend/src/components/skills/TestQuestionsSection.tsx
  - frontend/src/components/skills/DataLevelCard.tsx
  - frontend/src/hooks/useCopyToClipboard.ts
  - marketplace/skills/economic-indicator-analyst/SKILL.md
  - scripts/build-marketplace.ts
last_updated: 2026-01-13
last_updated_by: Claude
---

# 技能詳情頁面重新設計研究報告 v2

## 研究問題

使用者希望重新設計技能詳情頁面（SkillDetailPage），參考 https://skillstore.io/zh-hans/skills/egadams-receipt-scanning-tools 的設計風格，實作以下需求：

1. **新增技能特色** - 類似 skillstore 的質量評分區塊
2. **新增最佳實踐與避免事項** - 兩個欄位展示使用建議
3. **新增常見問題（FAQ）** - 常見問題區塊
4. **新增「關於」區塊** - 開發者詳情資訊
5. **移除現有的「其他說明」和「技能全文」** - 改用 card 的 info 方式呈現

## 摘要

本研究深入分析了 macro-skills 專案的技能詳情頁面架構，並對照 SkillStore.io 的參考設計與使用者新需求。研究發現專案已完成初步改版（參考 `2026-01-13-skill-detail-page-redesign.md` 和 `2026-01-13-skill-detail-page-redesign.md` 開發總結），成功實作了 InstallGuide、TestQuestionsSection 與 DataLevelCard 三個新元件。

目前架構已具備良好的元件化基礎、完整的型別系統（支援 `testQuestions`）、以及可重用的 `useCopyToClipboard` Hook。使用者的新需求需要進一步擴充資料結構，新增 `qualityScore`（質量評分）、`bestPractices`（最佳實踐）、`pitfalls`（避免事項）、`faq`（常見問題）與 `about`（關於）欄位。

視覺風格採用現代化的卡片式設計，使用 Tailwind CSS 的設計系統，色彩以灰階為主、primary 藍色為強調色。技術棧為 React 18 + TypeScript + Vite + React Router + React Markdown，支援完整的型別檢查與模組化開發。

## 詳細發現

### 1. 現有架構分析

#### 1.1 已實作的元件（來自前次改版）

**C:\Users\fatfi\works\macro-skills\frontend\src\pages\SkillDetailPage.tsx**（第 36-210 行）

目前頁面結構：

```
SkillDetailPage
├── 麵包屑導航（第 78-89 行）
├── 頂部資訊卡片（第 92-146 行）
│   ├── Emoji + 顯示名稱
│   ├── 描述文字
│   ├── DataLevel Badge + 分類
│   ├── 標籤列表
│   ├── 安裝按鈕
│   └── Meta 資訊（版本、作者、授權）
├── InstallGuide 元件（第 149-151 行）✅ 已實作
├── TestQuestionsSection 元件（第 154-158 行）✅ 已實作
├── DataLevelCard 元件（第 161-163 行）✅ 已實作
├── Markdown 內容區（第 166-170 行）
└── 技能原文檢視器（第 173-202 行）
```

**關鍵發現**：
- 頁面已完成模組化重構
- 新元件使用條件渲染（testQuestions 有資料才顯示）
- 使用 `useCopyToClipboard` Hook 統一複製功能
- 保留原有的 Markdown 內容區與技能原文檢視器

#### 1.2 已實作的新元件

**C:\Users\fatfi\works\macro-skills\frontend\src\components\skills\InstallGuide.tsx**（第 1-102 行）

功能特點：
- 三步驟安裝指引（新增 Marketplace、啟用技能、開始使用）
- 每個步驟都有可複製的指令
- 圓形步驟編號 + 深色程式碼區塊
- 整合 `generateMarketplaceInstallCommand()` 與 `generateSkillEnableCommand()`

**C:\Users\fatfi\works\macro-skills\frontend\src\components\skills\TestQuestionsSection.tsx**（第 1-95 行）

功能特點：
- 顯示測試問題列表（來自 `skill.testQuestions`）
- 每個問題獨立的複製按鈕
- 預期結果可摺疊展開
- 底部藍色提示區塊引導使用
- 無測試問題時自動隱藏（條件渲染）

**C:\Users\fatfi\works\macro-skills\frontend\src\components\skills\DataLevelCard.tsx**（第 1-46 行）

功能特點：
- 顯示數據源完整資訊（emoji、名稱、成本、描述）
- 整合 `getDataLevelInfo()` 函數
- 底部說明文字解釋數據源等級意義
- 統一的卡片式布局

#### 1.3 現有資料結構

**C:\Users\fatfi\works\macro-skills\frontend\src\types\skill.ts**（第 1-52 行）

```typescript
export interface TestQuestion {
  question: string;
  expectedResult?: string;
}

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
  dataLevel: DataLevel;
  tools: Tool[];
  featured: boolean;
  installCount: number;
  content: string;
  testQuestions?: TestQuestion[];  // ✅ 已新增
}
```

**缺少的欄位**（對應新需求）：
- ❌ `qualityScore` - 質量評分（對應需求 1）
- ❌ `bestPractices` - 最佳實踐（對應需求 2）
- ❌ `pitfalls` - 避免事項（對應需求 2）
- ❌ `faq` - 常見問題（對應需求 3）
- ❌ `about` - 關於資訊（對應需求 4）

#### 1.4 SkillService 與建置流程

**C:\Users\fatfi\works\macro-skills\frontend\src\services\skillService.ts**（第 1-87 行）

已實作的函數：
- `fetchSkills()` - 從 JSON 載入技能資料（第 5-11 行）
- `filterSkills()` - 過濾技能（第 13-34 行）
- `sortSkills()` - 排序技能（第 36-51 行）
- `generateInstallCommand()` - 生成安裝指令（第 76-78 行）
- `generateMarketplaceInstallCommand()` - 生成 marketplace 安裝指令（第 80-82 行）
- `generateSkillEnableCommand()` - 生成技能啟用指令（第 84-86 行）

**C:\Users\fatfi\works\macro-skills\scripts\build-marketplace.ts**（第 1-120 行）

建置流程：
1. 使用 `glob` 找出所有 `marketplace/skills/*/SKILL.md` 檔案（第 42 行）
2. 使用 `gray-matter` 解析 YAML frontmatter（第 50 行）
3. 建構 Skill 物件（第 53-72 行）
4. 產生 `frontend/public/data/skills.json`（第 88-89 行）
5. 產生 `marketplace/index.json`（第 92-112 行）

**關鍵發現**：建置腳本已支援 `testQuestions` 欄位（第 71 行），新增欄位需同步更新。

#### 1.5 技能資料範例

**C:\Users\fatfi\works\macro-skills\marketplace\skills\economic-indicator-analyst\SKILL.md**（第 1-104 行）

YAML frontmatter 結構：

```yaml
---
name: economic-indicator-analyst
displayName: 經濟指標分析師
description: 分析 GDP、CPI、失業率、PMI 等經濟指標...
emoji: 📊
version: v1.0.0
license: MIT
author: Macro Skills Team
authorUrl: https://github.com/fatfingererr/macro-skills
tags:
  - 經濟指標
  - GDP
  - CPI
category: indicator-monitoring
dataLevel: free-nolimit
tools:
  - claude-code
featured: true
installCount: 1250
testQuestions:
  - question: '請分析最新公佈的美國 CPI 數據...'
    expectedResult: |
      分析師會提供：
      1. 數據解讀...
---
```

Markdown 內容包含：
- 使用時機
- 支援的經濟指標
- 使用方式
- 分析框架
- 範例輸出

**關鍵觀察**：
- YAML frontmatter 結構化元數據
- Markdown 內容為技能詳細說明
- testQuestions 已整合至 frontmatter

### 2. SkillStore.io 參考設計分析

#### 2.1 頁面整體結構（WebFetch 分析結果）

參考網站的主要區塊：

1. **頂部導航** - Skillstore 標誌、語言切換、登入選項
2. **麵包屑導航** - 首頁 > 技能 > 本技能名稱
3. **標題區** - 技能名稱、emoji、描述與支援平台
4. **下載與測試區** - ZIP 下載、上傳指引、使用案例演示
5. **安全審計區** - 掃描結果與風險評級
6. **質量評分區** ← **需求 1**
7. **功能區塊** - 可建構內容、提示範本、最佳實踐
8. **最佳實踐與避免事項** ← **需求 2**
9. **FAQ 與開發者資訊** ← **需求 3 & 4**

#### 2.2 質量評分區塊設計（需求 1）

**呈現方式**：
- 總體評分：「70 青銅」徽章
- 六項評分指標：
  - 架構（25 分）
  - 可維護性（100 分）
  - 內容（100 分）
  - 社區（50 分）
  - 安全（100 分）
  - 規範符合性（70 分）
- 折疊式詳情：點選「顯示詳情」可展開各項評分的檢查項目與得分

**設計特點**：
- 多維度評分系統
- 視覺化的分數呈現
- 可展開的詳細說明

#### 2.3 最佳實踐與避免事項設計（需求 2）

**呈現方式**：
- 採用分立的兩欄式或上下區塊呈現
- 最佳實踐區塊：列舉建議做法（例：「運行 Python 收據工具前始終激活虛擬環境」）
- 避免區塊：列舉注意事項（例：「跳過虛擬環境激活會導致 ModuleNotFoundError」）
- 文字採用列表格式，易於掃讀

**設計特點**：
- 清晰的正反對比
- 簡潔的列表式呈現
- 實務導向的建議

#### 2.4 FAQ 設計（需求 3）

**呈現方式**：
- 結構化問答設計
- 六組常見問題與答案對
- 問題採粗體突出
- 答案提供簡潔的技術說明
- 涵蓋環境設置、資料庫、安全性等實務面向

**設計特點**：
- 問答格式清晰
- 可能支援摺疊/展開
- 實用性導向

#### 2.5 關於區塊設計（需求 4）

**呈現方式**：
- 作者：「EGAdams」（可連結至作者頁面）
- 授權：「MIT」
- 儲存庫連結：指向 GitHub 完整項目路徑
- 參考分支：「main」

**設計特點**：
- 開發者資訊集中呈現
- 可連結至外部資源
- 簡潔的卡片式布局

#### 2.6 視覺風格總結

- **色彩系統**：簡潔的中性色調，藍色連結突出
- **排版層級**：大標題、中級標題、列表項目呈現清晰的視覺優先級
- **空間利用**：適當留白，增強可讀性
- **互動元素**：按鈕位置明確、互動回饋清晰
- **響應式設計**：結構適合多種螢幕尺寸瀏覽

### 3. UI 元件庫與樣式系統

#### 3.1 Tailwind CSS 設計系統

**C:\Users\fatfi\works\macro-skills\frontend\tailwind.config.js**（第 1-27 行）

色彩系統：

```javascript
colors: {
  primary: {
    50: '#f0f9ff',   // 極淺藍
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',  // 主要藍
    600: '#0284c7',  // 深藍（常用於按鈕 hover）
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
}
```

**標準樣式模式**：
- 卡片容器：`bg-white border border-gray-200 rounded-xl p-6`
- 標題樣式：`text-xl font-bold text-gray-900`
- 次要文字：`text-sm text-gray-600`
- 深色程式碼區塊：`bg-gray-900 text-gray-100`
- 按鈕：使用 Button 元件的 variant 系統

#### 3.2 現有共用元件

**Button 元件**（C:\Users\fatfi\works\macro-skills\frontend\src\components\common\Button.tsx，第 1-44 行）

支援的 variant：
- `primary` - 藍色主按鈕（`bg-primary-600`）
- `secondary` - 灰色次要按鈕（`bg-gray-100`）
- `outline` - 外框按鈕（`border border-gray-300`）

支援的 size：
- `sm` - 小型（`px-3 py-1.5`）
- `md` - 中型（`px-4 py-2`）
- `lg` - 大型（`px-6 py-3`）

**Badge 元件**（C:\Users\fatfi\works\macro-skills\frontend\src\components\common\Badge.tsx，第 1-43 行）

支援的 type：
- `dataLevel` - 數據源等級（有顏色映射）
- `tool` - 工具類型（紫色）
- `tag` - 標籤（灰色）

DataLevel 顏色映射：
- `free-nolimit` → 綠色（`bg-green-100 text-green-800`）
- `free-limit` → 黃色（`bg-yellow-100 text-yellow-800`）
- `low-cost` → 藍色（`bg-blue-100 text-blue-800`）
- `high-cost` → 紫色（`bg-purple-100 text-purple-800`）
- `enterprise` → 紅色（`bg-red-100 text-red-800`）

#### 3.3 useCopyToClipboard Hook

**C:\Users\fatfi\works\macro-skills\frontend\src\hooks\useCopyToClipboard.ts**（第 1-18 行）

```typescript
export function useCopyToClipboard(timeout = 2000) {
  const [copied, setCopied] = useState(false);

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), timeout);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return { copied, copy };
}
```

**優勢**：
- 統一的複製狀態管理
- 自動重置（可配置超時時間）
- 錯誤處理
- 可重用於所有需要複製功能的元件

### 4. 資料結構擴充方案

#### 4.1 新增欄位定義

根據使用者需求，需要在 Skill 介面新增以下欄位：

```typescript
// frontend/src/types/skill.ts

// 質量評分（需求 1）
export interface QualityScore {
  overall: number;          // 總體分數（0-100）
  badge: string;           // 徽章（如：「青銅」「白銀」「黃金」）
  metrics: {
    architecture?: number;      // 架構（0-100）
    maintainability?: number;   // 可維護性（0-100）
    content?: number;           // 內容（0-100）
    community?: number;         // 社區（0-100）
    security?: number;          // 安全（0-100）
    compliance?: number;        // 規範符合性（0-100）
  };
  details?: string;        // 詳細說明（可選，支援 Markdown）
}

// 最佳實踐項目（需求 2）
export interface BestPractice {
  title: string;           // 標題
  description?: string;    // 詳細說明（可選）
}

// 避免事項（需求 2）
export interface Pitfall {
  title: string;           // 標題
  description?: string;    // 詳細說明（可選）
  consequence?: string;    // 後果說明（可選）
}

// 常見問題（需求 3）
export interface FAQ {
  question: string;        // 問題
  answer: string;          // 答案（支援 Markdown）
}

// 關於資訊（需求 4）
export interface About {
  author: string;          // 作者名稱（複製自頂層）
  authorUrl?: string;      // 作者連結（複製自頂層）
  license: string;         // 授權（複製自頂層）
  repository?: string;     // 儲存庫連結
  branch?: string;         // 參考分支
  additionalInfo?: string; // 額外資訊（支援 Markdown）
}

// 擴充後的 Skill 介面
export interface Skill {
  // ... 現有欄位
  testQuestions?: TestQuestion[];

  // 新增欄位
  qualityScore?: QualityScore;     // 質量評分（需求 1）
  bestPractices?: BestPractice[];  // 最佳實踐（需求 2）
  pitfalls?: Pitfall[];            // 避免事項（需求 2）
  faq?: FAQ[];                     // 常見問題（需求 3）
  about?: About;                   // 關於資訊（需求 4）
}
```

#### 4.2 YAML Frontmatter 格式範例

```yaml
---
name: economic-indicator-analyst
displayName: 經濟指標分析師
# ... 現有欄位

# 質量評分（需求 1）
qualityScore:
  overall: 70
  badge: 青銅
  metrics:
    architecture: 25
    maintainability: 100
    content: 100
    community: 50
    security: 100
    compliance: 70
  details: |
    本技能在可維護性、內容與安全方面表現優異，但架構與社區參與仍有成長空間。

# 最佳實踐（需求 2）
bestPractices:
  - title: 確認數據來源時效性
    description: 使用即時或近期數據以確保分析準確性
  - title: 比對多個數據源
    description: 交叉驗證不同來源的數據以提升可信度
  - title: 考慮季節調整因素
    description: 某些經濟指標有季節性波動，需使用季調後數據

# 避免事項（需求 2）
pitfalls:
  - title: 忽略數據修正值
    description: 經濟數據常有後續修正，應追蹤修正情況
    consequence: 可能導致分析結論偏差
  - title: 過度依賴單一指標
    description: 單一指標無法反映全貌
    consequence: 可能錯失重要市場訊號
  - title: 忽略地緣政治因素
    description: 經濟數據需搭配地緣政治環境解讀
    consequence: 分析可能缺乏全面性

# 常見問題（需求 3）
faq:
  - question: 此技能支援哪些國家的經濟數據？
    answer: 主要支援美國、歐元區、中國、日本等主要經濟體，可根據需求擴充其他國家。
  - question: 如何取得即時經濟數據？
    answer: 建議使用 FRED API、Bloomberg Terminal 或各國央行官網提供的數據。
  - question: 分析結果是否包含投資建議？
    answer: 本技能僅提供數據解讀與市場影響分析，不構成投資建議，投資決策需自行評估。
  - question: 如何判斷數據的可信度？
    answer: 應交叉驗證多個權威來源，並注意數據發布單位、統計方法與樣本範圍。

# 關於資訊（需求 4）
about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    本技能由 Macro Skills Team 維護，持續更新以涵蓋最新的經濟分析方法。
    歡迎提交 Issue 或 PR 貢獻改進建議。
---
```

#### 4.3 資料遷移策略

**向後相容原則**：
- 所有新欄位都設為選填（`?`）
- 現有技能無新欄位時不會出錯
- 逐步為現有技能補充新欄位資料

**優先順序**：
1. 先實作元件與型別定義
2. 為 `economic-indicator-analyst` 補充完整資料作為範例
3. 逐步為其他技能補充資料

### 5. 元件設計方案

#### 5.1 需要新建的元件

根據使用者需求，需要建立以下新元件：

1. **QualityScoreCard.tsx** - 質量評分卡片（需求 1）
2. **BestPracticesSection.tsx** - 最佳實踐區塊（需求 2）
3. **PitfallsSection.tsx** - 避免事項區塊（需求 2）
4. **FAQSection.tsx** - 常見問題區塊（需求 3）
5. **AboutSection.tsx** - 關於資訊區塊（需求 4）

#### 5.2 QualityScoreCard 元件設計

**檔案位置**：`frontend/src/components/skills/QualityScoreCard.tsx`

**功能需求**：
- 接收 `qualityScore` 作為 props
- 顯示總體分數與徽章
- 顯示六項評分指標（雷達圖或進度條）
- 詳細說明可展開/收合
- 空狀態處理（無評分時隱藏）

**介面設計**：

```typescript
interface QualityScoreCardProps {
  qualityScore: QualityScore;
}
```

**視覺結構**：

```
┌─────────────────────────────────────────────────┐
│ 🏆 質量評分                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│   ┌─────────────┐                              │
│   │  70 青銅    │  總體評分                     │
│   └─────────────┘                              │
│                                                 │
│   評分細項：                                     │
│   架構          ████░░░░░░ 25/100              │
│   可維護性      ██████████ 100/100             │
│   內容          ██████████ 100/100             │
│   社區          █████░░░░░ 50/100              │
│   安全          ██████████ 100/100             │
│   規範符合性    ███████░░░ 70/100              │
│                                                 │
│   [顯示詳情 ▼]                                  │
│   本技能在可維護性、內容與安全方面表現優異...   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**技術要點**：
- 使用 Tailwind 的 flex 與 grid 系統排版
- 進度條使用相對寬度（`width: ${score}%`）
- 徽章顏色根據分數區間映射（0-40 青銅、41-70 白銀、71-100 黃金）
- 詳細說明支援 Markdown（使用 ReactMarkdown）

#### 5.3 BestPracticesSection 元件設計

**檔案位置**：`frontend/src/components/skills/BestPracticesSection.tsx`

**功能需求**：
- 接收 `bestPractices` 陣列作為 props
- 顯示最佳實踐列表
- 每個項目包含標題與可選的詳細說明
- 使用綠色主題（表示正面建議）
- 空狀態處理

**介面設計**：

```typescript
interface BestPracticesSectionProps {
  practices: BestPractice[];
}
```

**視覺結構**：

```
┌─────────────────────────────────────────────────┐
│ ✅ 最佳實踐                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✓ 確認數據來源時效性                            │
│   使用即時或近期數據以確保分析準確性             │
│                                                 │
│ ✓ 比對多個數據源                                │
│   交叉驗證不同來源的數據以提升可信度             │
│                                                 │
│ ✓ 考慮季節調整因素                              │
│   某些經濟指標有季節性波動，需使用季調後數據     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**技術要點**：
- 使用綠色打勾符號（✓）或綠色圓點
- 標題使用 `font-semibold`
- 說明使用 `text-sm text-gray-600`
- 整體使用淺綠色背景（`bg-green-50`）或保持白底

#### 5.4 PitfallsSection 元件設計

**檔案位置**：`frontend/src/components/skills/PitfallsSection.tsx`

**功能需求**：
- 接收 `pitfalls` 陣列作為 props
- 顯示避免事項列表
- 每個項目包含標題、說明與後果
- 使用橙色/紅色主題（表示警告）
- 空狀態處理

**介面設計**：

```typescript
interface PitfallsSectionProps {
  pitfalls: Pitfall[];
}
```

**視覺結構**：

```
┌─────────────────────────────────────────────────┐
│ ⚠️ 避免事項                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✗ 忽略數據修正值                                │
│   經濟數據常有後續修正，應追蹤修正情況           │
│   ⚠️ 後果：可能導致分析結論偏差                  │
│                                                 │
│ ✗ 過度依賴單一指標                              │
│   單一指標無法反映全貌                           │
│   ⚠️ 後果：可能錯失重要市場訊號                  │
│                                                 │
│ ✗ 忽略地緣政治因素                              │
│   經濟數據需搭配地緣政治環境解讀                 │
│   ⚠️ 後果：分析可能缺乏全面性                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

**技術要點**：
- 使用紅色/橙色警告符號（✗ 或 ⚠️）
- 後果說明使用橙色文字（`text-orange-700`）
- 整體使用淺橙色背景（`bg-orange-50`）或保持白底
- 與 BestPracticesSection 對應呈現

#### 5.5 FAQSection 元件設計

**檔案位置**：`frontend/src/components/skills/FAQSection.tsx`

**功能需求**：
- 接收 `faq` 陣列作為 props
- 顯示常見問題列表
- 每個問答可獨立展開/收合
- 答案支援 Markdown 格式
- 空狀態處理

**介面設計**：

```typescript
interface FAQSectionProps {
  faqs: FAQ[];
}
```

**視覺結構**：

```
┌─────────────────────────────────────────────────┐
│ ❓ 常見問題                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ▼ 此技能支援哪些國家的經濟數據？                │
│   主要支援美國、歐元區、中國、日本等主要經濟體， │
│   可根據需求擴充其他國家。                       │
│                                                 │
│ ▶ 如何取得即時經濟數據？                        │
│                                                 │
│ ▶ 分析結果是否包含投資建議？                    │
│                                                 │
│ ▶ 如何判斷數據的可信度？                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

**技術要點**：
- 使用 `useState` 管理每個問答的展開狀態
- 問題使用 `font-semibold text-gray-900`
- 答案使用 ReactMarkdown 渲染
- 展開/收合動畫使用 CSS transition
- 參考 TestQuestionsSection 的摺疊設計

#### 5.6 AboutSection 元件設計

**檔案位置**：`frontend/src/components/skills/AboutSection.tsx`

**功能需求**：
- 接收 `about` 物件作為 props
- 顯示作者、授權、儲存庫資訊
- 外部連結可點擊跳轉
- 額外資訊支援 Markdown
- 空狀態處理（顯示基本資訊）

**介面設計**：

```typescript
interface AboutSectionProps {
  about?: About;
  // Fallback props（從 Skill 頂層欄位取得）
  author: string;
  authorUrl?: string;
  license: string;
}
```

**視覺結構**：

```
┌─────────────────────────────────────────────────┐
│ 📄 關於此技能                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 作者：Macro Skills Team ↗                       │
│ 授權：MIT                                       │
│ 儲存庫：github.com/fatfingererr/macro-skills ↗  │
│ 分支：main                                      │
│                                                 │
│ 本技能由 Macro Skills Team 維護，持續更新以涵蓋  │
│ 最新的經濟分析方法。歡迎提交 Issue 或 PR 貢獻    │
│ 改進建議。                                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

**技術要點**：
- 外部連結使用 `text-primary-600 hover:text-primary-700`
- 連結後附加 ↗ 符號表示外部連結
- 額外資訊使用 ReactMarkdown 渲染
- 若無 `about` prop，使用 fallback 顯示基本資訊（作者、授權）

### 6. 頁面布局調整方案

#### 6.1 調整後的頁面結構

```
SkillDetailPage
├── 麵包屑導航（維持不變）
├── 頂部資訊卡片（維持不變）
├── InstallGuide 元件（維持不變）
├── TestQuestionsSection 元件（維持不變）
├── QualityScoreCard 元件 ← 新增（需求 1）
├── BestPracticesSection 元件 ← 新增（需求 2）
├── PitfallsSection 元件 ← 新增（需求 2）
├── DataLevelCard 元件（維持不變）
├── FAQSection 元件 ← 新增（需求 3）
├── AboutSection 元件 ← 新增（需求 4）
├── Markdown 內容區 ← 考慮移除或精簡
└── 技能原文檢視器 ← 考慮移除
```

#### 6.2 關於「移除其他說明與技能全文」的建議

使用者需求提到：「移除現有的『其他說明』和『技能全文』- 改用 card 的 info 方式呈現」

**現有的「其他說明」與「技能全文」**：
- **Markdown 內容區**（第 166-170 行）：顯示 `skill.content` 的完整 Markdown 內容
- **技能原文檢視器**（第 173-202 行）：顯示包含 YAML frontmatter 的完整原始碼，附帶複製功能

**建議做法**：

**選項 1：完全移除**
- 優點：簡化頁面、聚焦於結構化資訊卡片
- 缺點：失去詳細說明與開發者查看原始碼的便利性

**選項 2：摺疊隱藏**
- 將 Markdown 內容區與技能原文檢視器改為摺疊區塊
- 預設收合，使用者可點擊「顯示詳細說明」或「顯示技能原文」展開
- 優點：保留功能但不佔據版面
- 缺點：增加一次點擊成本

**選項 3：移動至「關於」區塊**
- 將 Markdown 內容整合至 AboutSection 的「額外資訊」
- 技能原文改為「下載」或「查看原文」連結
- 優點：整合至統一的資訊卡片系統
- 缺點：AboutSection 可能變得過長

**推薦做法**：**選項 2（摺疊隱藏）**

理由：
- 保留現有功能，避免資訊遺失
- 符合「card 的 info 方式」理念（可視為一個摺疊卡片）
- 給予使用者選擇權（需要時展開）
- 實作成本低（添加 `useState` 與摺疊 UI）

#### 6.3 元件插入位置

在 SkillDetailPage.tsx 中的插入點：

```typescript
// 在現有的 DataLevelCard 之前插入新元件

{/* Quality Score - 新增（需求 1） */}
{skill.qualityScore && (
  <div className="mt-8">
    <QualityScoreCard qualityScore={skill.qualityScore} />
  </div>
)}

{/* Best Practices - 新增（需求 2） */}
{skill.bestPractices && skill.bestPractices.length > 0 && (
  <div className="mt-8">
    <BestPracticesSection practices={skill.bestPractices} />
  </div>
)}

{/* Pitfalls - 新增（需求 2） */}
{skill.pitfalls && skill.pitfalls.length > 0 && (
  <div className="mt-8">
    <PitfallsSection pitfalls={skill.pitfalls} />
  </div>
)}

{/* Data Level Info - 維持 */}
<div className="mt-8">
  <DataLevelCard dataLevel={skill.dataLevel} />
</div>

{/* FAQ - 新增（需求 3） */}
{skill.faq && skill.faq.length > 0 && (
  <div className="mt-8">
    <FAQSection faqs={skill.faq} />
  </div>
)}

{/* About - 新增（需求 4） */}
<div className="mt-8">
  <AboutSection
    about={skill.about}
    author={skill.author}
    authorUrl={skill.authorUrl}
    license={skill.license}
  />
</div>

{/* Content - 改為摺疊 */}
<div className="mt-8">
  <CollapsibleContent content={skill.content} />
</div>

{/* Skill Source - 改為摺疊 */}
<div className="mt-8">
  <CollapsibleSkillSource source={generateSkillSource(skill)} />
</div>
```

### 7. 建置流程更新

#### 7.1 build-marketplace.ts 需要的變更

**C:\Users\fatfi\works\macro-skills\scripts\build-marketplace.ts**

需要更新的地方：

1. **型別定義擴充**（第 6-30 行）

```typescript
// 新增型別定義
interface QualityScore {
  overall: number;
  badge: string;
  metrics: {
    architecture?: number;
    maintainability?: number;
    content?: number;
    community?: number;
    security?: number;
    compliance?: number;
  };
  details?: string;
}

interface BestPractice {
  title: string;
  description?: string;
}

interface Pitfall {
  title: string;
  description?: string;
  consequence?: string;
}

interface FAQ {
  question: string;
  answer: string;
}

interface About {
  author: string;
  authorUrl?: string;
  license: string;
  repository?: string;
  branch?: string;
  additionalInfo?: string;
}

// 更新 Skill 介面
interface Skill {
  // ... 現有欄位
  testQuestions?: TestQuestion[];
  qualityScore?: QualityScore;
  bestPractices?: BestPractice[];
  pitfalls?: Pitfall[];
  faq?: FAQ[];
  about?: About;
}
```

2. **技能物件建構擴充**（第 53-72 行）

```typescript
const skill: Skill = {
  // ... 現有欄位
  testQuestions: data.testQuestions,
  qualityScore: data.qualityScore,
  bestPractices: data.bestPractices,
  pitfalls: data.pitfalls,
  faq: data.faq,
  about: data.about,
};
```

#### 7.2 技能資料更新流程

1. 編輯 `marketplace/skills/{skill-name}/SKILL.md`
2. 在 YAML frontmatter 中新增對應欄位
3. 執行 `npm run build:marketplace`
4. 檢查 `frontend/public/data/skills.json` 是否正確產生

### 8. 實作步驟建議

#### 階段 1：資料結構準備（預估 1 小時）

1. **修改型別定義**（`frontend/src/types/skill.ts`）
   - 新增 `QualityScore`、`BestPractice`、`Pitfall`、`FAQ`、`About` 介面
   - 更新 `Skill` 介面，新增五個新欄位

2. **更新建置腳本**（`scripts/build-marketplace.ts`）
   - 新增型別定義（與 frontend 保持一致）
   - 更新技能物件建構邏輯

3. **為範例技能新增資料**（`marketplace/skills/economic-indicator-analyst/SKILL.md`）
   - 在 YAML frontmatter 新增所有新欄位
   - 執行 `npm run build:marketplace` 驗證

#### 階段 2：元件開發（預估 4-5 小時）

4. **建立 QualityScoreCard 元件**
   - 建立 `frontend/src/components/skills/QualityScoreCard.tsx`
   - 實作總體評分與徽章顯示
   - 實作六項評分指標（進度條）
   - 實作詳細說明摺疊功能

5. **建立 BestPracticesSection 元件**
   - 建立 `frontend/src/components/skills/BestPracticesSection.tsx`
   - 實作列表展示
   - 使用綠色主題

6. **建立 PitfallsSection 元件**
   - 建立 `frontend/src/components/skills/PitfallsSection.tsx`
   - 實作列表展示
   - 使用橙色/紅色警告主題

7. **建立 FAQSection 元件**
   - 建立 `frontend/src/components/skills/FAQSection.tsx`
   - 實作問答列表
   - 實作摺疊/展開功能
   - 整合 ReactMarkdown

8. **建立 AboutSection 元件**
   - 建立 `frontend/src/components/skills/AboutSection.tsx`
   - 實作作者、授權、儲存庫資訊顯示
   - 實作外部連結
   - 整合 ReactMarkdown 顯示額外資訊

9. **建立摺疊元件**（選填）
   - 建立 `frontend/src/components/common/Collapsible.tsx`
   - 可重用的摺疊容器元件
   - 用於摺疊 Markdown 內容區與技能原文

#### 階段 3：頁面整合（預估 1-2 小時）

10. **修改 SkillDetailPage**
    - 引入所有新元件
    - 調整頁面布局，插入新元件
    - 實作條件渲染（有資料才顯示）
    - 調整 Markdown 內容區與技能原文為摺疊式（選填）

11. **測試與調整**
    - 測試所有新元件正常顯示
    - 測試空狀態處理（無資料時不顯示）
    - 測試摺疊/展開功能
    - 測試外部連結

#### 階段 4：樣式優化與測試（預估 1-2 小時）

12. **視覺調整**
    - 確保卡片間距一致（`mt-8`）
    - 調整色彩對比
    - 優化進度條視覺效果
    - 確保響應式設計正常

13. **無障礙檢查**
    - 鍵盤導航測試
    - 顏色對比度檢查
    - 添加適當的 ARIA 屬性

14. **完整測試**
    - 測試所有技能頁面
    - 測試有/無新欄位的技能
    - 測試建置流程（`npm run build:marketplace`）
    - 測試前端建置（`npm run build`）

#### 階段 5：資料補充（持續進行）

15. **為其他技能補充資料**
    - 逐步為 `central-bank-policy-decoder` 補充新欄位
    - 逐步為 `market-cycle-judge` 補充新欄位
    - 根據實際需求調整資料結構

### 9. 技術挑戰與注意事項

#### 9.1 質量評分視覺化

**挑戰**：如何呈現六項評分指標

**選項 1：進度條**
- 簡單直觀
- 易於實作（使用 Tailwind 的 width 百分比）
- 適合比較不同指標

**選項 2：雷達圖**
- 視覺效果佳
- 需要引入圖表庫（如 Chart.js、Recharts）
- 增加套件依賴

**建議**：先使用進度條，未來可選擇性升級為雷達圖

#### 9.2 Markdown 渲染一致性

**注意事項**：
- FAQ 答案、About 額外資訊、QualityScore 詳細說明都支援 Markdown
- 需確保 ReactMarkdown 的 `remarkPlugins` 一致（使用 `remarkGfm`）
- 統一樣式（使用 `prose` class 或自訂樣式）

**建議做法**：
- 建立可重用的 `MarkdownContent` 元件
- 統一配置 ReactMarkdown 選項

```typescript
// frontend/src/components/common/MarkdownContent.tsx
interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`prose prose-sm prose-gray max-w-none ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
```

#### 9.3 資料結構的彈性

**挑戰**：不同技能可能需要不同的質量評分指標

**建議**：
- `metrics` 物件的所有欄位都設為選填
- 前端元件自動過濾 `undefined` 指標
- 支援自訂指標名稱（未來擴充）

#### 9.4 摺疊狀態管理

**挑戰**：FAQSection 中每個問答都有獨立的展開狀態

**建議做法**：

```typescript
// FAQSection.tsx
const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

const toggleFAQ = (index: number) => {
  const newExpanded = new Set(expandedIds);
  if (newExpanded.has(index)) {
    newExpanded.delete(index);
  } else {
    newExpanded.add(index);
  }
  setExpandedIds(newExpanded);
};
```

或使用陣列儲存：

```typescript
const [expandedIndices, setExpandedIndices] = useState<number[]>([]);

const toggleFAQ = (index: number) => {
  setExpandedIndices(prev =>
    prev.includes(index)
      ? prev.filter(i => i !== index)
      : [...prev, index]
  );
};
```

#### 9.5 響應式設計

**需測試的斷點**：
- 手機（< 640px）：單欄布局、進度條可能換行
- 平板（640px - 1024px）：調整卡片寬度
- 桌面（> 1024px）：現有的 `max-w-4xl` 容器

**注意事項**：
- BestPractices 與 Pitfalls 在大螢幕可能採用並排布局
- 質量評分的進度條在小螢幕需要垂直排列
- FAQ 摺疊區塊需要適當的觸控區域

### 10. 範例資料完整格式

#### 10.1 完整的 SKILL.md 範例

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
installCount: 1250

# 測試問題（已實作）
testQuestions:
  - question: '請分析最新公佈的美國 CPI 數據：整體 CPI 年增 3.2%、核心 CPI 年增 4.0%、月增 0.4%'
    expectedResult: |
      分析師會提供：
      1. 數據解讀（與預期值、前值比較）
      2. 趨勢分析（短期與長期趨勢判斷）
      3. 結構分析（主要驅動因素拆解）
      4. 市場影響評估（股市、債市、匯市）
      5. 政策啟示（對 Fed 政策的潛在影響）
  - question: '比較最新的 PMI 製造業與服務業指數，分析經濟景氣狀況'
    expectedResult: '會分析兩個指數的相對強弱，判斷經濟擴張或收縮趨勢，並評估製造業與服務業的相對表現'

# 質量評分（需求 1）
qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 60
    maintainability: 90
    content: 95
    community: 50
    security: 100
    compliance: 80
  details: |
    **架構（60/100）**
    - ✅ 模組化設計良好
    - ⚠️ 可進一步抽象化數據處理邏輯

    **可維護性（90/100）**
    - ✅ 程式碼清晰易讀
    - ✅ 適當的註解與文件

    **內容（95/100）**
    - ✅ 涵蓋主要經濟指標
    - ✅ 範例豐富實用

    **社區（50/100）**
    - ⚠️ 尚無社區貢獻
    - ⚠️ 可增加討論區或 Wiki

    **安全（100/100）**
    - ✅ 無已知安全問題
    - ✅ 無敏感資料處理

    **規範符合性（80/100）**
    - ✅ 遵循 Claude Code 規範
    - ⚠️ 可補充更多元數據

# 最佳實踐（需求 2）
bestPractices:
  - title: 確認數據來源時效性
    description: 使用即時或近期數據以確保分析準確性，避免使用過期資料
  - title: 比對多個數據源
    description: 交叉驗證不同來源（如 FRED、Bloomberg、各國央行）的數據以提升可信度
  - title: 考慮季節調整因素
    description: 某些經濟指標有季節性波動（如零售銷售），應優先使用季調後（SA）數據
  - title: 關注數據修正值
    description: 經濟數據常有後續修正（如非農就業），應追蹤修正情況並更新分析
  - title: 結合前瞻性指引
    description: 解讀數據時需搭配央行的前瞻性指引與市場預期

# 避免事項（需求 2）
pitfalls:
  - title: 忽略數據修正值
    description: 經濟數據初值常有後續修正，僅依據初值可能得出錯誤結論
    consequence: 可能導致分析結論偏差，影響投資決策
  - title: 過度依賴單一指標
    description: 單一指標無法反映經濟全貌，應綜合多項指標判斷
    consequence: 可能錯失重要市場訊號或誤判經濟趨勢
  - title: 忽略地緣政治因素
    description: 經濟數據需搭配地緣政治環境解讀（如貿易戰、地區衝突）
    consequence: 分析可能缺乏全面性，無法預測非經濟因素的影響
  - title: 混淆名目與實質數據
    description: 需區分名目數據與實質數據（扣除通膨），避免錯誤比較
    consequence: 可能高估或低估實際經濟成長
  - title: 忽略基期效應
    description: 年增率受基期影響大，需搭配絕對值或其他比較基準
    consequence: 可能誤判經濟趨勢的真實強度

# 常見問題（需求 3）
faq:
  - question: 此技能支援哪些國家的經濟數據？
    answer: |
      主要支援以下國家/地區的經濟數據：
      - 🇺🇸 美國（GDP、CPI、非農、PMI、ISM 等）
      - 🇪🇺 歐元區（GDP、CPI、PMI 等）
      - 🇨🇳 中國（GDP、CPI、PMI、社會融資規模等）
      - 🇯🇵 日本（GDP、CPI、Tankan 等）
      - 🇬🇧 英國（GDP、CPI、PMI 等）

      可根據需求擴充其他國家，歡迎提交 Issue 建議。

  - question: 如何取得即時經濟數據？
    answer: |
      推薦以下數據來源：

      **免費來源**：
      - [FRED](https://fred.stlouisfed.org/) - 美國聖路易斯聯邦準備銀行資料庫
      - 各國央行官網（Fed、ECB、BOJ、PBOC 等）
      - [Trading Economics](https://tradingeconomics.com/) - 全球經濟指標

      **付費來源**：
      - Bloomberg Terminal
      - Refinitiv Eikon
      - FactSet

      建議優先使用 FRED API，提供完整的歷史數據與 API 接口。

  - question: 分析結果是否包含投資建議？
    answer: |
      **本技能僅提供數據解讀與市場影響分析，不構成投資建議。**

      輸出內容包括：
      - 數據解讀（與預期值、前值比較）
      - 趨勢判斷（短期與長期）
      - 市場影響評估（股市、債市、匯市）
      - 政策啟示（央行可能的應對）

      投資決策需自行評估風險承受能力、投資目標與市場環境，建議諮詢專業財務顧問。

  - question: 如何判斷數據的可信度？
    answer: |
      評估數據可信度的關鍵要點：

      1. **來源權威性** - 優先使用官方機構（央行、統計局）發布的數據
      2. **統計方法** - 了解數據的統計方法、樣本範圍與調整方式
      3. **修正歷史** - 檢查該指標是否常有大幅修正
      4. **交叉驗證** - 比對多個來源的數據是否一致
      5. **時效性** - 確認數據的發布時間與涵蓋期間

      對於有爭議的數據（如中國 GDP），建議搭配其他間接指標（如電力消耗、貨運量）交叉驗證。

  - question: 此技能是否支援歷史數據回測？
    answer: |
      目前版本主要聚焦於**即時數據解讀**，暫不內建歷史回測功能。

      若需歷史分析，建議：
      - 使用 FRED API 取得歷史數據
      - 搭配 Python（pandas、matplotlib）進行回測
      - 或使用專業回測平台（如 QuantConnect、Backtrader）

      未來版本可能新增歷史數據分析模組，歡迎提交功能需求。

  - question: 如何處理數據異常值或極端情況？
    answer: |
      遇到異常值時的處理步驟：

      1. **確認數據正確性** - 檢查是否為數據錯誤或發布錯誤
      2. **了解背景因素** - 調查是否有特殊事件（如疫情、政策變動）
      3. **使用穩健統計量** - 考慮使用中位數而非平均值
      4. **剔除異常值** - 在有充分理由的情況下排除極端值
      5. **情境分析** - 分別評估包含/排除異常值的情境

      對於黑天鵝事件（如 COVID-19），建議單獨分析該時期的數據特徵，避免汙染長期趨勢判斷。

# 關於資訊（需求 4）
about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 維護團隊

    本技能由 **Macro Skills Team** 開發與維護，持續更新以涵蓋最新的經濟分析方法與數據源。

    ## 貢獻指南

    歡迎社區貢獻！您可以透過以下方式參與：
    - 🐛 提交 Bug Report 或 Feature Request
    - 📝 改進文件與範例
    - 🔧 提交 Pull Request 改善技能邏輯
    - 💬 在 Discussions 分享使用心得

    ## 授權說明

    本技能採用 MIT 授權，可自由使用、修改與分發。詳見 [LICENSE](https://github.com/fatfingererr/macro-skills/blob/main/LICENSE)。

    ## 致謝

    感謝以下資源與社區的支持：
    - [FRED API](https://fred.stlouisfed.org/docs/api/) 提供豐富的經濟數據
    - Claude Code 團隊的技術支援
    - 所有提供回饋與建議的使用者
---

# 經濟指標分析師

專業的經濟指標分析助手，幫助你快速理解各類經濟數據的意義與市場影響。

## 使用時機

- 當新的經濟數據公佈時，需要快速解讀其意義
- 分析多個經濟指標之間的關聯性
- 評估經濟數據對金融市場的潛在影響
- 撰寫經濟分析報告時需要專業解讀

[以下為現有的 Markdown 內容...]
```

### 11. 視覺設計 Mock

#### 11.1 QualityScoreCard 區塊

```
┌─────────────────────────────────────────────────┐
│ 🏆 質量評分                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│     ┌──────────────────┐                       │
│     │   75  白銀       │                       │
│     │   ⭐⭐⭐⭐☆       │                       │
│     └──────────────────┘                       │
│                                                 │
│ 評分細項：                                       │
│                                                 │
│ 架構                                             │
│ ████████░░░░░░░░░░ 60/100                      │
│                                                 │
│ 可維護性                                         │
│ ██████████████████░░ 90/100                    │
│                                                 │
│ 內容                                             │
│ ███████████████████░ 95/100                    │
│                                                 │
│ 社區                                             │
│ ██████████░░░░░░░░░░ 50/100                    │
│                                                 │
│ 安全                                             │
│ ████████████████████ 100/100                   │
│                                                 │
│ 規範符合性                                       │
│ ████████████████░░░░ 80/100                    │
│                                                 │
│ [顯示詳情 ▼]                                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 11.2 BestPractices 與 Pitfalls 並排（大螢幕）

```
┌──────────────────────────┬──────────────────────────┐
│ ✅ 最佳實踐              │ ⚠️ 避免事項              │
├──────────────────────────┼──────────────────────────┤
│                          │                          │
│ ✓ 確認數據來源時效性     │ ✗ 忽略數據修正值         │
│   使用即時或近期數據以   │   經濟數據常有後續修正，  │
│   確保分析準確性         │   應追蹤修正情況         │
│                          │   ⚠️ 可能導致分析偏差    │
│                          │                          │
│ ✓ 比對多個數據源         │ ✗ 過度依賴單一指標       │
│   交叉驗證不同來源的數據  │   單一指標無法反映全貌   │
│   以提升可信度           │   ⚠️ 可能錯失市場訊號    │
│                          │                          │
│ ✓ 考慮季節調整因素       │ ✗ 忽略地緣政治因素       │
│   某些經濟指標有季節性   │   經濟數據需搭配地緣政治  │
│   波動，需使用季調後數據  │   環境解讀               │
│                          │   ⚠️ 分析可能缺乏全面性  │
│                          │                          │
└──────────────────────────┴──────────────────────────┘
```

#### 11.3 FAQSection 區塊

```
┌─────────────────────────────────────────────────┐
│ ❓ 常見問題                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ▼ 此技能支援哪些國家的經濟數據？                │
│                                                 │
│   主要支援以下國家/地區的經濟數據：              │
│   - 🇺🇸 美國（GDP、CPI、非農、PMI、ISM 等）     │
│   - 🇪🇺 歐元區（GDP、CPI、PMI 等）              │
│   - 🇨🇳 中國（GDP、CPI、PMI、社會融資規模等）   │
│   - 🇯🇵 日本（GDP、CPI、Tankan 等）             │
│   - 🇬🇧 英國（GDP、CPI、PMI 等）                │
│                                                 │
│ ▶ 如何取得即時經濟數據？                        │
│                                                 │
│ ▶ 分析結果是否包含投資建議？                    │
│                                                 │
│ ▶ 如何判斷數據的可信度？                        │
│                                                 │
│ ▶ 此技能是否支援歷史數據回測？                  │
│                                                 │
│ ▶ 如何處理數據異常值或極端情況？                │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 11.4 AboutSection 區塊

```
┌─────────────────────────────────────────────────┐
│ 📄 關於此技能                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 👤 作者：Macro Skills Team ↗                    │
│ 📜 授權：MIT                                     │
│ 🔗 儲存庫：github.com/fatfingererr/macro-skills ↗│
│ 🌿 分支：main                                    │
│                                                 │
│ ─────────────────────────────────────────────   │
│                                                 │
│ ## 維護團隊                                      │
│                                                 │
│ 本技能由 Macro Skills Team 開發與維護，持續更新  │
│ 以涵蓋最新的經濟分析方法與數據源。               │
│                                                 │
│ ## 貢獻指南                                      │
│                                                 │
│ 歡迎社區貢獻！您可以透過以下方式參與：           │
│ - 🐛 提交 Bug Report 或 Feature Request         │
│ - 📝 改進文件與範例                              │
│ - 🔧 提交 Pull Request 改善技能邏輯              │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 程式碼引用

### 現有架構（已實作）

- **SkillDetailPage.tsx**（第 36-210 行）- 頁面主元件結構
- **InstallGuide.tsx**（第 1-102 行）- 安裝指引元件
- **TestQuestionsSection.tsx**（第 1-95 行）- 測試問題元件
- **DataLevelCard.tsx**（第 1-46 行）- 數據源卡片元件
- **useCopyToClipboard.ts**（第 1-18 行）- 複製功能 Hook

### 資料結構

- **skill.ts**（第 1-52 行）- Skill 型別定義與介面
- **categories.ts**（第 1-85 行）- 分類與 DataLevel 資料

### 建置流程

- **build-marketplace.ts**（第 1-120 行）- Marketplace 建置腳本
- **SKILL.md**（第 1-104 行）- 技能資料格式範例

### UI 元件庫

- **Button.tsx**（第 1-44 行）- 按鈕元件
- **Badge.tsx**（第 1-43 行）- 徽章元件
- **tailwind.config.js**（第 1-27 行）- Tailwind 配置

## 相關研究

- **前次改版研究報告**: `thoughts/shared/research/2026-01-13-skill-detail-page-redesign.md`
- **前次改版開發總結**: `thoughts/shared/coding/2026-01-13-skill-detail-page-redesign.md`

## 開放問題

1. **質量評分視覺化方式**
   - 進度條 vs 雷達圖
   - 建議：先使用進度條，未來可升級

2. **最佳實踐與避免事項的呈現方式**
   - 並排（大螢幕）vs 上下排列（小螢幕）
   - 建議：使用響應式布局

3. **Markdown 內容區與技能原文的去留**
   - 完全移除 vs 摺疊隱藏 vs 整合至 About
   - 建議：摺疊隱藏（保留功能但不佔版面）

4. **徽章等級定義**
   - 0-40 青銅、41-70 白銀、71-100 黃金
   - 或其他分級方式
   - 建議：可配置的分級閾值

5. **質量評分指標的標準化**
   - 六項指標是否為固定欄位
   - 或允許自訂指標名稱
   - 建議：先固定欄位，未來可擴充

6. **FAQ 的預設展開狀態**
   - 全部收合 vs 第一個展開
   - 建議：全部收合，使用者按需展開

## 結論

本研究詳細分析了技能詳情頁面重新設計的需求與實作方案。主要發現包括：

1. **現有基礎完善**：前次改版已實作 InstallGuide、TestQuestionsSection、DataLevelCard 與 useCopyToClipboard Hook，建立良好的元件化基礎。

2. **資料結構需擴充**：需要在 Skill 介面新增五個欄位（`qualityScore`、`bestPractices`、`pitfalls`、`faq`、`about`），對應使用者的五項需求。

3. **五個新元件**：需建立 QualityScoreCard、BestPracticesSection、PitfallsSection、FAQSection、AboutSection 五個新元件。

4. **建置流程同步**：需更新 `build-marketplace.ts` 以支援新欄位的解析。

5. **視覺風格一致**：參考 SkillStore.io 的設計，使用卡片式布局、適當留白、清晰的視覺層級，與現有設計系統相容。

6. **向後相容**：所有新欄位都設為選填，現有技能無新欄位時不會出錯，可逐步補充資料。

實作建議分為五個階段：資料結構準備（1 小時）、元件開發（4-5 小時）、頁面整合（1-2 小時）、樣式優化與測試（1-2 小時）、資料補充（持續進行）。預估總工作量約 8-10 小時可完成核心功能。

主要技術挑戰在於質量評分的視覺化、Markdown 渲染一致性、摺疊狀態管理與響應式設計，但均有明確的解決方案。建議優先實作 QualityScoreCard、FAQSection 與 AboutSection，BestPracticesSection 與 PitfallsSection 可視需求延後或合併實作。

對於「移除其他說明與技能全文」的需求，建議採用**摺疊隱藏**方式，既符合「card 的 info 方式」理念，又保留現有功能，給予使用者選擇權。
