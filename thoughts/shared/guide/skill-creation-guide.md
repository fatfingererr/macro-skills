# Skill 建立規範指南

本指南定義 macro-skills 專案中 Skill 的標準目錄結構與檔案規範，確保所有技能具有一致的架構。

## 目錄結構

每個 Skill 應遵循以下目錄結構：

```
skills/{skill-name}/
├── SKILL.md                    # 技能內容（Claude 執行用）
├── skill.yaml                  # 前端展示設定
├── manifest.json               # 技能元資料
├── workflows/                  # 工作流程定義
│   ├── {workflow-1}.md
│   └── {workflow-2}.md
├── references/                 # 參考文件
│   ├── {reference-1}.md
│   └── {reference-2}.md
├── templates/                  # 輸出模板
│   ├── output-json.md
│   └── output-markdown.md
├── scripts/                    # 執行腳本
│   └── {main-script}.py
└── examples/                   # 範例輸出（選用）
    └── {example}.json
```

## 檔案職責分離

### 三檔案分工原則

| 檔案 | 用途 | 讀取者 |
|------|------|--------|
| `SKILL.md` | 技能執行邏輯與內容 | Claude Code |
| `skill.yaml` | 前端展示設定 | Frontend + build-marketplace.ts |
| `manifest.json` | 技能元資料 | Frontend + build-marketplace.ts + Claude Code |

---

## SKILL.md 規範

### Frontmatter（僅兩個欄位）

```yaml
---
name: skill-name-in-kebab-case
description: 技能的一句話描述，說明這個技能做什麼
---
```

**重要**：SKILL.md 的 frontmatter 只放 `name` 和 `description`，其他元資料都在 `manifest.json` 或 `skill.yaml`。

### 內容區塊

SKILL.md 應包含以下 XML 區塊（依實際需求選用）：

#### 必要區塊

```xml
<essential_principles>
**技能名稱 核心原則**

<principle name="principle_1">
**原則標題**
原則內容說明...
</principle>

<principle name="principle_2">
...
</principle>
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **操作一** - 操作描述
2. **操作二** - 操作描述
3. **操作三** - 操作描述

**等待回應後再繼續。**
</intake>

<routing>
| Response                    | Workflow           | Description |
|-----------------------------|--------------------|-------------|
| 1, "keyword1", "keyword2"   | workflows/xxx.md   | 操作描述    |
| 2, "keyword3", "keyword4"   | workflows/yyy.md   | 操作描述    |

**讀取工作流程後，請完全遵循其步驟。**
</routing>
```

#### 索引區塊

```xml
<reference_index>
**參考文件** (`references/`)

| 文件 | 內容 |
|------|------|
| xxx.md | 文件描述 |
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| xxx.md   | 工作流程描述 |
</workflows_index>

<templates_index>
| Template | Purpose |
|----------|---------|
| output-json.md | JSON 輸出模板 |
</templates_index>

<scripts_index>
| Script | Purpose |
|--------|---------|
| main.py | 主要腳本描述 |
</scripts_index>
```

#### 選用區塊

```xml
<quick_start>
**快速開始**

```bash
# 安裝依賴
pip install xxx

# 執行
python scripts/main.py --quick
```
</quick_start>

<success_criteria>
Skill 成功執行時：
- [ ] 條件一
- [ ] 條件二
- [ ] 條件三
</success_criteria>

<examples_index>
**範例輸出** (`examples/`)

| 文件 | 內容 |
|------|------|
| example.json | 範例描述 |
</examples_index>
```

---

## manifest.json 規範

manifest.json 存放**技能元資料**，供 Claude Code 和前端共同使用。

### 必要欄位

```json
{
  "name": "skill-name",
  "description": "技能描述",
  "version": "0.1.0",
  "author": "作者名稱"
}
```

### 完整欄位範例

```json
{
  "name": "skill-name",
  "version": "0.1.0",
  "displayName": "技能顯示名稱",
  "description": "技能的完整描述",
  "author": "Ricky Wang",
  "license": "MIT",
  "category": "category-name",
  "tags": [
    "標籤1",
    "標籤2",
    "標籤3"
  ],
  "dataLevel": "free-nolimit",
  "dependencies": {
    "python": ">=3.8",
    "packages": [
      "pandas>=1.5.0",
      "numpy>=1.20.0"
    ],
    "optional": [
      "matplotlib>=3.5.0"
    ]
  },
  "entryPoints": {
    "skill": "SKILL.md",
    "mainScript": "scripts/main.py"
  },
  "workflows": [
    {
      "id": "workflow-id",
      "name": "工作流程名稱",
      "description": "工作流程描述",
      "file": "workflows/xxx.md"
    }
  ],
  "references": [
    "references/xxx.md",
    "references/yyy.md"
  ],
  "templates": [
    "templates/output-json.md"
  ],
  "examples": [
    "examples/example.json"
  ],
  "dataSources": [
    {
      "name": "數據源名稱",
      "type": "primary",
      "url": "https://example.com",
      "api": "API 說明"
    }
  ]
}
```

### 欄位說明

| 欄位 | 類型 | 必要 | 說明 |
|------|------|------|------|
| `name` | string | ✅ | 技能 ID（kebab-case） |
| `description` | string | ✅ | 技能描述 |
| `version` | string | ✅ | 版本號（semver） |
| `author` | string \| {name} | ✅ | 作者名稱或物件 |
| `displayName` | string | ❌ | 顯示名稱（中文） |
| `license` | string | ❌ | 授權條款（預設 MIT） |
| `category` | string | ❌ | 分類 |
| `tags` | string[] | ❌ | 標籤陣列 |
| `dataLevel` | string | ❌ | 資料等級 |
| `dependencies` | object | ❌ | 依賴套件 |
| `entryPoints` | object | ❌ | 進入點定義 |
| `workflows` | array | ❌ | 工作流程清單 |
| `references` | array | ❌ | 參考文件清單 |
| `templates` | array | ❌ | 模板清單 |
| `examples` | array | ❌ | 範例清單 |
| `dataSources` | array | ❌ | 資料來源 |

### category 可用值

| Category | 說明 |
|----------|------|
| `business-cycles` | 景氣循環 |
| `indicator-monitoring` | 指標監控 |
| `inflation-analytics` | 通膨分析 |
| `data-processing` | 資料處理 |
| `macro-indicator` | 宏觀指標 |

### dataLevel 可用值

| dataLevel | 說明 |
|-----------|------|
| `free-nolimit` | 免費、無限制 |
| `free-limited` | 免費、有限制 |
| `paid` | 付費 |

---

## skill.yaml 規範

skill.yaml 存放**前端展示專用**設定，不影響 Claude Code 執行。

### 基本結構

```yaml
# 前端展示專用（元資料從 manifest.json 讀取）
displayName: 技能顯示名稱（可覆蓋 manifest）
emoji: "🔧"
authorUrl: https://github.com/username/repo

tools:
  - claude-code

featured: false
installCount: 0
```

### 完整欄位

```yaml
# 前端展示專用（元資料從 manifest.json 讀取）
displayName: 技能顯示名稱
emoji: "🔧"
authorUrl: https://github.com/fatfingererr/macro-skills

tools:
  - claude-code

featured: false
installCount: 0

testQuestions:
  - question: '範例問題一'
    expectedResult: |
      預期結果說明...
    imagePath: 'images/example.png'  # 選用
  - question: '範例問題二'
    expectedResult: |
      預期結果說明...

qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 80
    maintainability: 80
    content: 85
    community: 20
    security: 95
    compliance: 85
  details: |
    **架構（80/100）**
    - 說明一
    - 說明二

    **可維護性（80/100）**
    - 說明...

bestPractices:
  - title: 最佳實踐標題
    description: 最佳實踐說明
  - title: 另一個最佳實踐
    description: 說明...

pitfalls:
  - title: 常見陷阱標題
    description: 陷阱描述
    consequence: 導致的後果

faq:
  - question: 常見問題一？
    answer: |
      回答內容...

  - question: 常見問題二？
    answer: |
      回答內容...

about:
  repository: https://github.com/fatfingererr/macro-skills
  branch: main
  additionalInfo: |
    ## 額外資訊

    詳細說明...
```

### 欄位說明

| 欄位 | 類型 | 必要 | 說明 |
|------|------|------|------|
| `displayName` | string | ❌ | 覆蓋 manifest 的顯示名稱 |
| `emoji` | string | ✅ | 技能圖示（單一 emoji） |
| `authorUrl` | string | ❌ | 作者連結 |
| `tools` | string[] | ✅ | 支援工具（通常 `claude-code`） |
| `featured` | boolean | ✅ | 是否精選 |
| `installCount` | number | ✅ | 安裝次數（初始 0） |
| `testQuestions` | array | ❌ | 分析課題與預期結果 |
| `qualityScore` | object | ❌ | 品質評分 |
| `bestPractices` | array | ❌ | 最佳實踐 |
| `pitfalls` | array | ❌ | 常見陷阱 |
| `faq` | array | ❌ | 常見問題 |
| `about` | object | ❌ | 關於資訊 |

### qualityScore.badge 可用值

| Badge | overall 範圍 |
|-------|-------------|
| `黃金` | 80-100 |
| `白銀` | 60-79 |
| `青銅` | 40-59 |
| `入門` | 0-39 |

---

## 資料讀取優先順序

build-marketplace.ts 會依以下優先順序合併資料：

```
元資料欄位：manifest.json > SKILL.md frontmatter > 預設值
前端欄位：skill.yaml > 預設值
displayName：skill.yaml > manifest.json > SKILL.md name
```

### 欄位來源對照

| 欄位 | 來源 |
|------|------|
| name, description | manifest.json |
| version, license, author | manifest.json |
| category, tags, dataLevel | manifest.json |
| emoji, authorUrl | skill.yaml |
| tools, featured, installCount | skill.yaml |
| testQuestions, qualityScore | skill.yaml |
| bestPractices, pitfalls, faq | skill.yaml |
| about | skill.yaml |

---

## 建立新 Skill 步驟

### 1. 建立目錄結構

```bash
mkdir -p skills/{skill-name}/{workflows,references,templates,scripts,examples}
```

### 2. 建立 manifest.json

```bash
cat > skills/{skill-name}/manifest.json << 'EOF'
{
  "name": "skill-name",
  "version": "0.1.0",
  "displayName": "技能顯示名稱",
  "description": "技能描述",
  "author": "Ricky Wang",
  "license": "MIT",
  "category": "category-name",
  "tags": ["標籤1", "標籤2"],
  "dataLevel": "free-nolimit"
}
EOF
```

### 3. 建立 SKILL.md

```bash
cat > skills/{skill-name}/SKILL.md << 'EOF'
---
name: skill-name
description: 技能描述
---

<essential_principles>
...
</essential_principles>

<intake>
...
</intake>

<routing>
...
</routing>
EOF
```

### 4. 建立 skill.yaml

```bash
cat > skills/{skill-name}/skill.yaml << 'EOF'
displayName: 技能顯示名稱
emoji: "🔧"
authorUrl: https://github.com/fatfingererr/macro-skills

tools:
  - claude-code

featured: false
installCount: 0

testQuestions:
  - question: '範例問題'
    expectedResult: |
      預期結果...
EOF
```

### 5. 執行建構驗證

```bash
bun run scripts/build-marketplace.ts
```

預期輸出：
```
✓ 載入: 技能顯示名稱 (manifest+yaml)
```

---

## 檢查清單

建立新 Skill 時，確認以下項目：

### manifest.json
- [ ] `name` 使用 kebab-case
- [ ] `version` 使用 semver 格式
- [ ] `description` 簡潔明瞭
- [ ] `author` 已填寫

### SKILL.md
- [ ] frontmatter 只有 `name` 和 `description`
- [ ] 包含 `<essential_principles>`
- [ ] 包含 `<intake>` 和 `<routing>`
- [ ] routing 對應的 workflow 檔案存在

### skill.yaml
- [ ] `emoji` 已設定
- [ ] `tools` 包含 `claude-code`
- [ ] `featured` 和 `installCount` 已設定
- [ ] 至少有一個 `testQuestions`

### 目錄結構
- [ ] workflows/ 目錄存在且有內容
- [ ] references/ 目錄存在（如有參考文件）
- [ ] scripts/ 目錄存在（如有腳本）

---

## 範例參考

完整範例可參考以下現有技能：

- `skills/zeberg-salomon-rotator/` - 景氣循環輪換策略
- `skills/google-trends-ath-detector/` - Google Trends ATH 偵測
- `skills/us-cpi-pce-comparator/` - CPI/PCE 通膨比較
- `skills/wasde-ingestor/` - WASDE 報告匯入
- `skills/cost-density-net-rr-calculator/` - 成本密度計算

---

## 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-01-15 | 1.0.0 | 初版建立 |
