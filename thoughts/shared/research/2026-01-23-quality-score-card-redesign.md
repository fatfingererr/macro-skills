# QualityScoreCard 六維度重新設計研究報告

---
title: QualityScoreCard 六維度重新設計研究報告
date: 2026-01-23
author: Claude Code Researcher
tags: [frontend, quality-score, ui-design, skill-quality]
status: completed
related_files:
  - frontend/src/components/skills/QualityScoreCard.tsx
  - frontend/src/types/skill.ts
  - frontend/src/pages/SkillDetailPage.tsx
  - thoughts/shared/guide/skill-quality-guide.md
last_updated: 2026-01-23
last_updated_by: Claude Code Researcher
---

## 研究問題

基於 `thoughts/shared/guide/skill-quality-guide.md` 定義的新六維度品質評估標準，分析現有 `frontend/` 中 `QualityScoreCard` 相關實作，並設計符合新框架的呈現方式。

---

## 摘要

本研究分析了現有 QualityScoreCard 元件的實作方式，發現其使用舊有的六維度（architecture、maintainability、content、community、security、compliance），與新定義的六維度（problemFit、correctness、dataGovernance、robustness、maintainability、usability）不符。

現有實作採用簡單的 2x3 或 3x2 網格呈現各維度分數，視覺層次不夠豐富，缺乏整體徽章（Badge）的顯著呈現、雷達圖等進階視覺化，以及升級路徑的引導。

本報告提出完整的重新設計方案，包含新的 TypeScript 型別定義、skill.yaml 結構、以及更豐富的前端元件設計。

---

## 1. 現有實作分析

### 1.1 QualityScoreCard 元件現況

**檔案位置**：`C:\Users\fatfi\works\macro-skills\frontend\src\components\skills\QualityScoreCard.tsx`

**元件結構**：

```typescript
interface QualityScoreCardProps {
  qualityScore: QualityScore;
}
```

**現有功能**：

| 功能項目 | 現況描述                                                                              |
|----------|---------------------------------------------------------------------------------------|
| 維度指標 | 6 個舊維度（architecture, maintainability, content, community, security, compliance） |
| 分數呈現 | 2x3 或 3x2 網格，每格顯示 emoji + 分數 + 名稱                                         |
| 顏色邏輯 | 僅三階段：>=80 黃色、>=60 灰色、<60 橘色                                              |
| 詳情展開 | 可摺疊的 Markdown 詳情區塊                                                            |
| 整體分數 | **未顯示** overall 和 badge                                                           |

**現有配色邏輯**（第 14-18 行）：

```typescript
const getBadgeColor = (score: number) => {
  if (score >= 80) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  if (score >= 60) return 'bg-gray-100 text-gray-800 border-gray-300';
  return 'bg-orange-100 text-orange-800 border-orange-300';
};
```

**現有 metricConfig**（第 21-28 行）：

```typescript
const metricConfig: Record<string, { name: string; emoji: string }> = {
  architecture: { name: '架構', emoji: '🏗️' },
  maintainability: { name: '可維護性', emoji: '🔧' },
  content: { name: '內容', emoji: '📝' },
  community: { name: '社區', emoji: '👥' },
  security: { name: '安全', emoji: '🔒' },
  compliance: { name: '規範', emoji: '📋' },
};
```

### 1.2 TypeScript 型別定義現況

**檔案位置**：`C:\Users\fatfi\works\macro-skills\frontend\src\types\skill.ts`（第 11-23 行）

```typescript
export interface QualityScore {
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
```

### 1.3 現有 skill.yaml qualityScore 結構

以 `compute-precious-miner-gross-margin` 為例（第 32-66 行）：

```yaml
qualityScore:
  overall: 65
  badge: 白銀
  metrics:
    architecture: 75
    maintainability: 70
    content: 80
    community: 20
    security: 85
    compliance: 80
  details: |
    **架構（75/100）**
    - 清晰的路由器模式
    ...
```

### 1.4 現況問題總結

| 問題類別         | 具體問題                                                                                                    |
|------------------|-------------------------------------------------------------------------------------------------------------|
| **維度不匹配**   | 舊維度與新六維度（problemFit, correctness, dataGovernance, robustness, maintainability, usability）完全不同 |
| **Badge 未顯示** | 雖然 skill.yaml 有 badge 欄位，但元件未顯示整體徽章                                                         |
| **配色粗糙**     | 僅三階段配色，未對應新的五等級（白金/黃金/白銀/青銅/入門）                                                  |
| **視覺單調**     | 僅網格呈現，缺乏雷達圖、進度條、趨勢等視覺元素                                                              |
| **無升級指引**   | 缺乏「如何從白銀升到黃金」的升級路徑提示                                                                    |

---

## 2. 新 skill.yaml qualityScore 結構設計

### 2.1 新型別定義（TypeScript）

```typescript
// frontend/src/types/skill.ts

// 新六維度指標
export interface QualityMetrics {
  problemFit: number;       // 任務適配度與問題定義（0-100）
  correctness: number;      // 正確性與可驗證性（0-100）
  dataGovernance: number;   // 資料來源品質與資料治理（0-100）
  robustness: number;       // 穩健性與容錯（0-100）
  maintainability: number;  // 可重現性與可維護性（0-100）
  usability: number;        // 輸出可用性與決策支援（0-100）
}

// Badge 等級
export type QualityBadge = '白金' | '黃金' | '白銀' | '青銅' | '入門';

// 單一維度詳情
export interface MetricDetail {
  score: number;
  strengths: string[];      // 優點
  improvements?: string[];  // 待改進項目（可選）
}

// 升級建議
export interface UpgradeNote {
  targetBadge: QualityBadge;
  requirements: {
    metric: keyof QualityMetrics;
    currentScore: number;
    targetScore: number;
    suggestion: string;
  }[];
}

// 完整品質評分介面
export interface QualityScore {
  overall: number;                    // 整體分數（六維度平均）
  badge: QualityBadge;                // 等級徽章
  metrics: QualityMetrics;            // 六維度分數
  details?: string;                   // Markdown 格式的詳細說明
  metricDetails?: Record<keyof QualityMetrics, MetricDetail>;  // 各維度詳情
  upgradeNotes?: UpgradeNote;         // 升級建議
  evaluatedAt?: string;               // 評估日期 (ISO 8601)
}
```

### 2.2 新 skill.yaml 結構範例

```yaml
qualityScore:
  overall: 70
  badge: 白銀
  evaluatedAt: "2026-01-23"

  metrics:
    problemFit: 75        # 任務適配度與問題定義
    correctness: 80       # 正確性與可驗證性
    dataGovernance: 65    # 資料來源品質與資料治理
    robustness: 65        # 穩健性與容錯
    maintainability: 70   # 可重現性與可維護性
    usability: 75         # 輸出可用性與決策支援

  metricDetails:
    problemFit:
      score: 75
      strengths:
        - SKILL.md 有清晰的一句話目標
        - workflows/analyze.md 覆蓋主路徑
      improvements:
        - 缺少不適用情境說明

    correctness:
      score: 80
      strengths:
        - methodology.md 有完整公式推導
        - examples/ 有 1 個 golden case
      improvements:
        - 可增加更多邊界案例

    dataGovernance:
      score: 65
      strengths:
        - data-sources.md 有來源清單
      improvements:
        - 缺少 fallback 替代方案
        - fetch 有 cache 但無 timestamp

    robustness:
      score: 65
      strengths:
        - 有基本的錯誤處理
      improvements:
        - 缺值處理策略不明確
        - 無降級輸出機制

    maintainability:
      score: 70
      strengths:
        - manifest.json 有 version
        - 無重複文件
      improvements:
        - 部分 magic numbers 分散

    usability:
      score: 75
      strengths:
        - output-markdown.md 有 TL;DR 和依據
        - 有基本可視化
      improvements:
        - 缺少下一步建議
        - 缺歷史對照

  details: |
    **任務適配度（75/100）**
    - SKILL.md 有清晰的一句話目標
    - workflows/analyze.md 覆蓋主路徑
    - input-schema.md 欄位定義大致清楚
    - 待改進：缺少不適用情境說明

    **正確性（80/100）**
    - methodology.md 有完整公式推導
    - scripts/ 實作與文檔吻合
    - examples/ 有 1 個 golden case
    - 待改進：可增加更多邊界案例

    **資料治理（65/100）**
    - data-sources.md 有來源清單
    - 待改進：缺少 fallback 替代方案
    - 待改進：fetch 有 cache 但無 timestamp 記錄

    **穩健性（65/100）**
    - 有基本的錯誤處理
    - 待改進：缺值處理策略不明確
    - 待改進：無降級輸出機制

    **可維護性（70/100）**
    - manifest.json 有 version
    - 無重複文件
    - 待改進：部分 magic numbers 分散

    **輸出可用性（75/100）**
    - output-markdown.md 有 TL;DR 和依據
    - 有基本可視化
    - 待改進：缺少下一步建議
    - 待改進：缺歷史對照

  upgradeNotes:
    targetBadge: 黃金
    requirements:
      - metric: dataGovernance
        currentScore: 65
        targetScore: 70
        suggestion: 增加 fallback 來源，fetch 輸出增加 timestamp
      - metric: robustness
        currentScore: 65
        targetScore: 70
        suggestion: 明確缺值處理策略，增加降級輸出機制
```

---

## 3. 新前端元件設計建議

### 3.1 整體設計概念

新設計採用「漸進式揭露」原則：

1. **第一層**：Badge 徽章 + 總分 + 雷達圖（一目了然）
2. **第二層**：六維度分數卡（點擊展開詳情）
3. **第三層**：升級路徑（可選顯示）

### 3.2 元件結構設計

```
QualityScoreCard/
├── QualityScoreCard.tsx          # 主容器
├── QualityBadge.tsx              # 徽章元件
├── QualityRadarChart.tsx         # 雷達圖（SVG 或 Canvas）
├── QualityMetricGrid.tsx         # 六維度網格
├── QualityMetricCard.tsx         # 單一維度卡片
├── QualityUpgradePath.tsx        # 升級路徑
└── types.ts                      # 相關型別
```

### 3.3 Badge 徽章設計

#### 3.3.1 五等級配色方案

| Badge | 分數區間 | 主色      | 背景色                                          | 邊框色              | 圖示 |
|-------|----------|-----------|-------------------------------------------------|---------------------|------|
| 白金  | 90-100   | `#1e3a5f` | `bg-gradient-to-r from-slate-100 to-slate-200`  | `border-slate-400`  | 鑽石 |
| 黃金  | 80-89    | `#92400e` | `bg-gradient-to-r from-amber-100 to-yellow-100` | `border-amber-400`  | 獎盃 |
| 白銀  | 60-79    | `#374151` | `bg-gradient-to-r from-gray-100 to-slate-100`   | `border-gray-400`   | 銀牌 |
| 青銅  | 40-59    | `#78350f` | `bg-gradient-to-r from-orange-100 to-amber-100` | `border-orange-400` | 銅牌 |
| 入門  | 0-39     | `#1f2937` | `bg-gray-50`                                    | `border-gray-300`   | 起步 |

#### 3.3.2 Badge 元件設計

```tsx
// QualityBadge.tsx
interface QualityBadgeProps {
  badge: QualityBadge;
  overall: number;
  size?: 'sm' | 'md' | 'lg';
}

const badgeConfig: Record<QualityBadge, BadgeStyle> = {
  '白金': {
    icon: '💎',
    gradient: 'from-slate-100 to-slate-200',
    border: 'border-slate-400',
    text: 'text-slate-800',
    glow: 'shadow-slate-200',
  },
  '黃金': {
    icon: '🏆',
    gradient: 'from-amber-100 to-yellow-100',
    border: 'border-amber-400',
    text: 'text-amber-800',
    glow: 'shadow-amber-200',
  },
  '白銀': {
    icon: '🥈',
    gradient: 'from-gray-100 to-slate-100',
    border: 'border-gray-400',
    text: 'text-gray-700',
    glow: 'shadow-gray-200',
  },
  '青銅': {
    icon: '🥉',
    gradient: 'from-orange-100 to-amber-100',
    border: 'border-orange-400',
    text: 'text-orange-800',
    glow: 'shadow-orange-200',
  },
  '入門': {
    icon: '🌱',
    gradient: 'from-gray-50 to-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-600',
    glow: 'shadow-gray-100',
  },
};
```

### 3.4 雷達圖設計

#### 3.4.1 純 SVG 實作（無需額外套件）

考量到專案目前僅使用 React + Tailwind，建議使用純 SVG 實作雷達圖，避免引入 Chart.js 或 D3.js 等大型套件。

```tsx
// QualityRadarChart.tsx
interface QualityRadarChartProps {
  metrics: QualityMetrics;
  size?: number;
  showLabels?: boolean;
}

// 六邊形座標計算
const calculatePolygonPoints = (metrics: QualityMetrics, radius: number) => {
  const order: (keyof QualityMetrics)[] = [
    'problemFit',
    'correctness',
    'dataGovernance',
    'robustness',
    'maintainability',
    'usability',
  ];

  return order.map((key, index) => {
    const angle = (Math.PI * 2 * index) / 6 - Math.PI / 2;
    const value = metrics[key] / 100;
    const x = Math.cos(angle) * radius * value;
    const y = Math.sin(angle) * radius * value;
    return `${x},${y}`;
  }).join(' ');
};
```

#### 3.4.2 雷達圖視覺元素

| 元素     | 樣式                              |
|----------|-----------------------------------|
| 背景網格 | 5 層同心六邊形（20/40/60/80/100） |
| 資料區域 | 半透明填充 + 邊框線               |
| 頂點標籤 | 維度中文名稱 + 分數               |
| 參考線   | 中心到各頂點的輔助線              |

### 3.5 六維度網格設計

#### 3.5.1 維度配置

```typescript
const metricConfig: Record<keyof QualityMetrics, MetricConfig> = {
  problemFit: {
    name: '任務適配度',
    shortName: '適配',
    icon: '🎯',
    description: '問題定義與工作流閉環',
    color: 'blue',
  },
  correctness: {
    name: '正確性',
    shortName: '正確',
    icon: '✅',
    description: '方法論可重現與驗證',
    color: 'green',
  },
  dataGovernance: {
    name: '資料治理',
    shortName: '資料',
    icon: '📊',
    description: '來源品質與可追溯性',
    color: 'purple',
  },
  robustness: {
    name: '穩健性',
    shortName: '穩健',
    icon: '🛡️',
    description: '失敗模式與容錯處理',
    color: 'orange',
  },
  maintainability: {
    name: '可維護性',
    shortName: '維護',
    icon: '🔧',
    description: '版本管理與模板穩定',
    color: 'gray',
  },
  usability: {
    name: '輸出可用性',
    shortName: '可用',
    icon: '📋',
    description: '決策支援與歷史對照',
    color: 'teal',
  },
};
```

#### 3.5.2 單一維度卡片

```tsx
// QualityMetricCard.tsx
interface QualityMetricCardProps {
  metricKey: keyof QualityMetrics;
  score: number;
  detail?: MetricDetail;
  expanded?: boolean;
  onToggle?: () => void;
}
```

視覺元素：
- 圖示 + 維度名稱
- 環形進度指示器（或進度條）
- 分數顯示（大字）
- 等級色塊（根據分數）
- 展開箭頭（若有詳情）

展開後顯示：
- 優點清單（綠色勾號）
- 待改進清單（黃色警示）

### 3.6 升級路徑設計

```tsx
// QualityUpgradePath.tsx
interface QualityUpgradePathProps {
  currentBadge: QualityBadge;
  upgradeNotes?: UpgradeNote;
}
```

視覺元素：
- 當前等級 → 目標等級的箭頭指示
- 各維度升級需求卡片
- 進度指示器（距離目標多遠）

### 3.7 完整元件範例

```tsx
// QualityScoreCard.tsx
import { useState } from 'react';
import QualityBadge from './QualityBadge';
import QualityRadarChart from './QualityRadarChart';
import QualityMetricGrid from './QualityMetricGrid';
import QualityUpgradePath from './QualityUpgradePath';
import type { QualityScore } from '../../types/skill';

interface QualityScoreCardProps {
  qualityScore: QualityScore;
}

export default function QualityScoreCard({ qualityScore }: QualityScoreCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      {/* Header: Badge + Title */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-2xl">✨</span>
          <h2 className="text-xl font-bold text-gray-900">品質評估</h2>
        </div>
        <QualityBadge
          badge={qualityScore.badge}
          overall={qualityScore.overall}
        />
      </div>

      {/* Main Content: Radar + Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Radar Chart */}
        <div className="flex justify-center items-center">
          <QualityRadarChart
            metrics={qualityScore.metrics}
            size={200}
          />
        </div>

        {/* Score Summary */}
        <div className="flex flex-col justify-center">
          <div className="text-center md:text-left">
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {qualityScore.overall}
            </div>
            <div className="text-gray-500 mb-4">
              總分（六維度平均）
            </div>
            {qualityScore.evaluatedAt && (
              <div className="text-xs text-gray-400">
                評估日期：{qualityScore.evaluatedAt}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Metric Grid */}
      <QualityMetricGrid
        metrics={qualityScore.metrics}
        metricDetails={qualityScore.metricDetails}
      />

      {/* Toggle Buttons */}
      <div className="flex gap-4 mt-6">
        {qualityScore.details && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            {showDetails ? '隱藏詳情' : '查看詳情'}
          </button>
        )}
        {qualityScore.upgradeNotes && (
          <button
            onClick={() => setShowUpgrade(!showUpgrade)}
            className="text-amber-600 hover:text-amber-700 font-medium text-sm"
          >
            {showUpgrade ? '隱藏升級路徑' : '查看升級路徑'}
          </button>
        )}
      </div>

      {/* Expandable Details */}
      {showDetails && qualityScore.details && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {qualityScore.details}
          </ReactMarkdown>
        </div>
      )}

      {/* Upgrade Path */}
      {showUpgrade && qualityScore.upgradeNotes && (
        <div className="mt-4">
          <QualityUpgradePath
            currentBadge={qualityScore.badge}
            upgradeNotes={qualityScore.upgradeNotes}
          />
        </div>
      )}
    </div>
  );
}
```

### 3.8 響應式設計考量

| 斷點               | 佈局調整                         |
|--------------------|----------------------------------|
| < 640px (mobile)   | 雷達圖置頂、網格 1 欄            |
| 640-768px (tablet) | 雷達圖 + 摘要左右排列、網格 2 欄 |
| >= 768px (desktop) | 雷達圖 + 摘要左右排列、網格 3 欄 |

---

## 4. 實作計畫

### 4.1 階段一：型別與資料遷移（1-2 天）

| 任務                   | 說明                                         |
|------------------------|----------------------------------------------|
| 更新 TypeScript 型別   | 修改 `frontend/src/types/skill.ts`           |
| 更新 skill.yaml schema | 所有 skills 目錄下的 skill.yaml 遷移至新結構 |
| 資料轉換工具           | 建立舊維度 → 新維度的對應腳本（若需要）      |

**維度對應建議**：

| 舊維度          | 新維度          | 對應理由             |
|-----------------|-----------------|----------------------|
| architecture    | problemFit      | 架構設計反映任務適配 |
| content         | correctness     | 內容品質反映正確性   |
| security        | dataGovernance  | 安全性與資料治理相關 |
| compliance      | robustness      | 規範遵循反映穩健性   |
| maintainability | maintainability | 維持不變             |
| community       | usability       | 社區反饋反映可用性   |

### 4.2 階段二：基礎元件開發（2-3 天）

| 順序 | 元件               | 優先級 |
|------|--------------------|--------|
| 1    | QualityBadge       | 高     |
| 2    | QualityMetricCard  | 高     |
| 3    | QualityMetricGrid  | 高     |
| 4    | QualityRadarChart  | 中     |
| 5    | QualityUpgradePath | 低     |

### 4.3 階段三：整合與測試（1-2 天）

| 任務                   | 說明                         |
|------------------------|------------------------------|
| 組裝 QualityScoreCard  | 整合所有子元件               |
| SkillDetailPage 整合   | 更新呼叫方式                 |
| SkillCard 整合（可選） | 在列表卡片顯示小型 Badge     |
| 響應式測試             | 各斷點視覺驗證               |
| 資料驗證               | 確認所有 skill.yaml 正確解析 |

### 4.4 階段四：進階功能（可選）

| 功能     | 說明                         |
|----------|------------------------------|
| 動畫效果 | 雷達圖繪製動畫、分數計數動畫 |
| 比較模式 | 多個 Skill 的品質比較視圖    |
| 歷史趨勢 | 品質分數隨版本變化的趨勢圖   |

### 4.5 檔案變更清單

| 操作 | 檔案路徑                                                |
|------|---------------------------------------------------------|
| 修改 | `frontend/src/types/skill.ts`                           |
| 修改 | `frontend/src/components/skills/QualityScoreCard.tsx`   |
| 新增 | `frontend/src/components/skills/QualityBadge.tsx`       |
| 新增 | `frontend/src/components/skills/QualityRadarChart.tsx`  |
| 新增 | `frontend/src/components/skills/QualityMetricGrid.tsx`  |
| 新增 | `frontend/src/components/skills/QualityMetricCard.tsx`  |
| 新增 | `frontend/src/components/skills/QualityUpgradePath.tsx` |
| 新增 | `frontend/src/components/skills/quality/types.ts`       |
| 修改 | `skills/*/skill.yaml`（所有 Skill）                     |

---

## 5. 附錄：視覺設計參考

### 5.1 Badge 視覺示意

```
┌─────────────────────────────────────┐
│  💎  白金   │  整體分數: 95        │
│  ───────────┼─────────────────────  │
│  PLATINUM   │  頂級品質            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  🏆  黃金   │  整體分數: 85        │
│  ───────────┼─────────────────────  │
│  GOLD       │  優質技能            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  🥈  白銀   │  整體分數: 70        │
│  ───────────┼─────────────────────  │
│  SILVER     │  合格技能            │
└─────────────────────────────────────┘
```

### 5.2 雷達圖示意

```
                  任務適配度
                     (75)
                      /\
                     /  \
                    /    \
   輸出可用性 (75) /      \ 正確性 (80)
                  /   70   \
                 /   ____   \
                 \  /    \  /
                  \/      \/
   可維護性 (70) /          \ 資料治理 (65)
                 \          /
                  \   /\   /
                   \ /  \ /
                    \/  \/
                   穩健性
                    (65)
```

### 5.3 網格佈局示意

```
┌────────────────┬────────────────┬────────────────┐
│  🎯 任務適配度  │  ✅ 正確性      │  📊 資料治理    │
│      75       │      80       │      65       │
│   ████████░░   │   ████████░░   │   ██████░░░░   │
│    良好        │    良好        │    待改進      │
├────────────────┼────────────────┼────────────────┤
│  🛡️ 穩健性     │  🔧 可維護性    │  📋 輸出可用性  │
│      65       │      70       │      75       │
│   ██████░░░░   │   ███████░░░   │   ████████░░   │
│    待改進      │    中等        │    良好        │
└────────────────┴────────────────┴────────────────┘
```

---

## 6. 相關研究

- `thoughts/shared/guide/skill-quality-guide.md` - 六維度評估標準定義
- `frontend/src/components/skills/DataLevelCard.tsx` - 類似卡片元件參考

---

## 7. 開放問題

1. **向後相容**：是否需要支援舊維度的 skill.yaml？若需要，解析邏輯如何處理？
2. **評估自動化**：qualityScore 是否由腳本自動評估，還是手動維護？
3. **雷達圖套件**：是否考慮引入輕量圖表套件（如 Recharts）？
4. **Badge 在列表頁**：SkillCard 是否需要顯示簡化版 Badge？

---

*研究完成日期：2026-01-23*
