# Macro Skills

Claude Code 技能市集，專注於宏觀經濟分析領域。

## 專案簡介

Macro Skills 是一個為 Claude Code 設計的技能市集網站，提供宏觀經濟分析相關的技能套件。使用者可以瀏覽、搜尋並安裝各種經濟分析技能，提升研究與分析效率。

## 功能特色

- 技能瀏覽與搜尋
- 分類篩選（18 種宏觀經濟分析類別）
- 風險等級標示
- 一鍵複製安裝指令
- 響應式網頁設計
- 支援 GitHub Pages 靜態部署

## 技術架構

| 技術         | 用途               |
|--------------|--------------------|
| React 18     | 前端框架           |
| TypeScript   | 型別安全           |
| Vite         | 建置工具           |
| TailwindCSS  | 樣式框架           |
| React Router | 前端路由           |
| Bun          | 套件管理與執行環境 |

## 目錄結構

```
macro-skills/
├── frontend/                   # 前端應用程式
│   ├── src/
│   │   ├── components/         # React 元件
│   │   │   ├── common/         # 通用元件
│   │   │   ├── layout/         # 版面配置元件
│   │   │   └── skills/         # 技能相關元件
│   │   ├── pages/              # 頁面元件
│   │   ├── services/           # 資料服務
│   │   ├── types/              # TypeScript 型別定義
│   │   └── data/               # 靜態資料
│   └── public/                 # 靜態資源
├── skills/                     # 技能定義檔
├── commands/                   # Slash commands
├── scripts/                    # 建置腳本
└── .github/workflows/          # GitHub Actions 工作流程
```

## 快速開始

### 環境需求

- [Bun](https://bun.sh/) v1.0 或以上

### 安裝與執行

```bash
# 複製專案
git clone https://github.com/fatfingererr/macro-skills.git
cd macro-skills

# 安裝相依套件
bun install

# 啟動開發伺服器
bun run dev
```

開發伺服器啟動後，開啟瀏覽器前往 http://localhost:5173/

### 建置專案

```bash
# 建置 marketplace 資料
bun run build:marketplace

# 建置前端應用程式
cd frontend; bun run build; cd ..
```

建置產出位於 `frontend/dist/` 目錄。

## 部署

本專案支援 GitHub Pages 自動部署。

### 自動部署

推送至 `master` 分支後，GitHub Actions 會自動執行建置與部署流程。

### GitHub 設定

1. 前往儲存庫的 Settings > Pages
2. Source 選擇 GitHub Actions

### 部署網址

```
https://fatfingererr.github.io/macro-skills/
```

## 技能格式

每個技能使用 `SKILL.md` 檔案定義，採用 YAML frontmatter 格式：

```yaml
---
name: skill-name              # 技能識別碼（kebab-case）
displayName: 技能名稱          # 顯示名稱
description: 技能簡短描述       # 一至兩句說明
emoji: 圖示                    # 代表圖示
version: v1.0.0               # 版本號
license: MIT                  # 授權條款
author: 作者名稱               # 作者
tags:                         # 標籤
  - 標籤一
  - 標籤二
category: indicator-monitoring # 類別
riskLevel: safe               # 風險等級
tools:
  - claude-code               # 支援工具
featured: false               # 是否為精選
---

# 技能名稱

詳細說明文件...
```

### 風險等級

| 等級     | 說明                         |
|----------|------------------------------|
| safe     | 僅執行分析，不修改檔案或系統 |
| low      | 可能讀取本地檔案             |
| medium   | 可能修改本地檔案             |
| high     | 可能執行系統指令             |
| critical | 具有完整系統存取權限         |

### 類別

| ID                    | 中文       | English                     |
|-----------------------|------------|-----------------------------|
| data-processing       | 資料處理   | Data Processing             |
| indicator-monitoring  | 指標監控   | Indicator Monitoring        |
| nowcasting            | 即時預測   | Nowcasting                  |
| business-cycles       | 景氣週期   | Business Cycles & Regimes   |
| inflation-analytics   | 通膨分析   | Inflation Analytics         |
| labor-market          | 勞動市場   | Labor Market Analytics      |
| consumption-demand    | 消費需求   | Consumption & Demand        |
| production-investment | 產業景氣   | Production & Investment     |
| housing-shelter       | 房市居住   | Housing & Shelter           |
| central-bank-policy   | 央行操作   | Central Bank Policy Signals |
| policy-modeling       | 政策模型   | Policy Modeling             |
| interest-rates        | 存貸利率   | Interest Rates              |
| fx-factors            | 外匯因子   | FX Factors                  |
| capital-flows         | 跨境金流   | Capital Flows & BoP         |
| credit-risk           | 信用風險   | Credit Risk                 |
| liquidity-fci         | 流動性條件 | Liquidity & FCI             |
| commodity-sd          | 商品供需   | Commodity S&D               |
| event-scenario        | 事件情境   | Event Risk & Scenario       |

## 提交技能

1. Fork 本專案
2. 在 `skills/` 目錄下建立新資料夾
3. 新增 `SKILL.md` 檔案
4. 提交 Pull Request

詳細說明請參閱網站的提交頁面。

## 特別感謝

本 Repository 受 [Skillstore](https://skillstore.io/zh-hans) 啟發而建立，待未來成熟後願合併回 Skillstore。

## 授權條款

MIT License
