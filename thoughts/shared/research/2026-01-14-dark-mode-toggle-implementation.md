---
title: 網站右上方新增日間/夜間模式切換功能研究報告
date: 2026-01-14
author: Claude (codebase-researcher)
tags:
  - frontend
  - dark-mode
  - theme-toggle
  - ui-enhancement
  - react
  - tailwindcss
status: completed
related_files:
  - frontend/src/components/layout/Header.tsx
  - frontend/src/components/layout/Layout.tsx
  - frontend/tailwind.config.js
  - frontend/src/index.css
  - frontend/src/App.tsx
  - frontend/src/main.tsx
last_updated: 2026-01-14
last_updated_by: Claude
---

# 網站右上方新增日間/夜間模式切換功能研究報告

## 研究問題

分析 Macro Skills 前端專案，研究如何在網站右上方新增「夜間和日間模式切換」功能。

**需求：**
- 在網站右上方新增兩個 icon 按鈕（日間/夜間模式切換）
- 點擊即可切換主題

**研究重點：**
1. 前端專案結構（React/Vue/其他框架）
2. 現有的樣式系統（CSS/Tailwind/其他）
3. 找到 Header/導航列組件的位置
4. 現有的主題/顏色變數定義
5. 是否已有深色模式相關設定
6. 建議的實作方式

## 摘要

本研究深入分析了 Macro Skills 前端專案的技術架構與樣式系統，確定該專案使用 **React 18 + TypeScript + Vite + Tailwind CSS** 技術棧。專案目前**沒有任何深色模式相關設定**，Header 組件位於 `frontend/src/components/layout/Header.tsx`，右上方目前有 Discord 和 GitHub 圖標連結。

Tailwind CSS 配置中未啟用 `darkMode` 選項（預設為 `media`），色彩系統主要使用 `primary` 藍色系列與灰階系統。專案採用元件化架構，已有完善的 Layout > Header 結構，使用 React Hooks 進行狀態管理，並使用 HashRouter 作為路由方案。

實作深色模式切換功能需要：(1) 啟用 Tailwind 的 `class` 策略深色模式，(2) 建立主題狀態管理（使用 Context 或 localStorage），(3) 在 Header 右上方新增太陽/月亮圖標按鈕，(4) 為所有元件新增深色模式樣式類別（`dark:` 前綴），(5) 實作使用者偏好持久化。

建議採用 **Tailwind CSS 原生深色模式 + React Context** 方案，使用 `localStorage` 持久化使用者偏好，並在 Header 右上方插入圖標切換按鈕。此方案無需額外套件依賴，與現有技術棧完美整合，實作成本低且維護性高。

## 詳細發現

### 1. 前端專案結構分析

#### 1.1 技術棧識別

**C:\Users\fatfi\works\macro-skills\frontend\package.json**（第 1-37 行）

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.22.0",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.18",
    "tailwindcss": "^3.4.1",
    "typescript": "~5.6.2",
    "vite": "^6.0.5"
  }
}
```

**確認的技術棧**：
- **框架**: React 18.3.1（使用 JSX/TSX）
- **語言**: TypeScript 5.6.2
- **建置工具**: Vite 6.0.5
- **路由**: React Router DOM 6.22.0
- **樣式系統**: Tailwind CSS 3.4.1 + PostCSS + Autoprefixer
- **Markdown 渲染**: React Markdown 9.0.1 + remark-gfm

**關鍵發現**：
- 專案使用現代化的 React + Vite 開發環境
- Tailwind CSS 為主要樣式解決方案
- 無狀態管理庫（Redux/Zustand），使用 React 內建 Hooks
- 無現有 UI 元件庫（Material-UI/Ant Design），使用自訂元件

#### 1.2 專案目錄結構

**C:\Users\fatfi\works\macro-skills\frontend\src**

```
frontend/src/
├── App.tsx                          # 應用程式入口（路由定義）
├── main.tsx                         # React 根組件掛載
├── index.css                        # 全域樣式（Tailwind 導入）
├── vite-env.d.ts                    # Vite 型別定義
├── components/
│   ├── layout/
│   │   ├── Layout.tsx              # 主要版面配置元件
│   │   ├── Header.tsx              # 頂部導航列 ← **目標元件**
│   │   ├── Footer.tsx              # 頁尾
│   │   └── Sidebar.tsx             # 側邊欄
│   ├── common/
│   │   ├── Button.tsx              # 按鈕元件
│   │   ├── Badge.tsx               # 徽章元件
│   │   ├── Pagination.tsx          # 分頁元件
│   │   └── SearchInput.tsx         # 搜尋輸入元件
│   └── skills/
│       ├── SkillCard.tsx           # 技能卡片
│       ├── SkillGrid.tsx           # 技能網格
│       ├── InstallModal.tsx        # 安裝彈窗
│       └── [其他技能相關元件]
├── pages/
│   ├── HomePage.tsx                # 首頁
│   ├── SkillsPage.tsx              # 技能列表頁
│   ├── SkillDetailPage.tsx         # 技能詳情頁
│   ├── DocsPage.tsx                # 文件頁
│   └── SubmitPage.tsx              # 提交頁
├── hooks/
│   └── useCopyToClipboard.ts       # 複製功能 Hook
├── services/
│   └── skillService.ts             # 技能資料服務
├── types/
│   └── skill.ts                    # TypeScript 型別定義
└── data/
    └── categories.ts               # 分類資料
```

**元件化架構特點**：
- 清晰的三層結構：layout（版面）、common（通用）、domain-specific（領域專屬）
- Layout > Header 的階層關係明確
- 已有完善的自訂元件系統（Button、Badge 等）
- 使用自訂 Hooks 模式（useCopyToClipboard）

#### 1.3 應用程式結構

**C:\Users\fatfi\works\macro-skills\frontend\src\App.tsx**（第 1-24 行）

```typescript
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import SkillsPage from './pages/SkillsPage';
import SkillDetailPage from './pages/SkillDetailPage';
import DocsPage from './pages/DocsPage';
import SubmitPage from './pages/SubmitPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/skills/:skillId" element={<SkillDetailPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/submit" element={<SubmitPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
```

**C:\Users\fatfi\works\macro-skills\frontend\src\main.tsx**（第 1-14 行）

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>,
)
```

**架構特點**：
- Layout 元件包裹所有頁面（Header 在此渲染）
- 使用 HashRouter（適合 GitHub Pages 部署）
- 使用 StrictMode（開發模式雙重渲染檢查）
- 單一入口點掛載至 `#root`

**關鍵發現**：主題狀態管理可在以下層級實作：
1. **main.tsx 層級** - 全域 Context Provider（推薦）
2. **Layout.tsx 層級** - Layout 內部狀態
3. **Header.tsx 層級** - 僅 Header 內部狀態（不推薦，狀態作用域太小）

### 2. Header 元件現況分析

#### 2.1 Header 元件完整程式碼

**C:\Users\fatfi\works\macro-skills\frontend\src\components\layout\Header.tsx**（第 1-82 行）

```typescript
import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/skills', label: '技能 Skills' },
  { path: '/docs', label: '說明 Docs' },
  { path: '/submit', label: '提交 Submit' },
];

export default function Header() {
  const location = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">📈</span>
            <span className="font-bold text-xl text-gray-900">Macro Skills</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition-colors ${
                  location.pathname === item.path ||
                  (item.path === '/skills' && location.pathname.startsWith('/skills'))
                    ? 'text-primary-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            <a
              href="https://discord.gg/SDWSGXrhYq"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700"
              title="Discord"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515..." />
              </svg>
            </a>
            <a
              href="https://github.com/fatfingererr/macro-skills"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700"
              title="GitHub"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425..."
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button className="text-gray-500 hover:text-gray-700">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
```

**Header 結構分析**：

```
Header
├── Logo（左側）
│   ├── 📈 Emoji
│   └── "Macro Skills" 文字
├── Navigation（中間，桌面版）
│   ├── 技能 Skills
│   ├── 說明 Docs
│   └── 提交 Submit
├── Right Side（右側）← **插入點**
│   ├── Discord 圖標連結
│   ├── GitHub 圖標連結
│   └── ← **此處新增主題切換按鈕**
└── Mobile Menu Button（右側，行動版）
```

**關鍵發現**：
- Right Side 區塊（第 40-67 行）使用 `flex items-center space-x-4`
- 目前有兩個圖標連結（Discord、GitHub）
- 圖標統一使用 `h-6 w-6` 尺寸與 SVG 格式
- 顏色使用 `text-gray-500 hover:text-gray-700`
- 響應式設計：行動版顯示 Hamburger Menu（第 70-76 行）

**插入位置建議**：
在 Discord 圖標之前或 GitHub 圖標之後新增主題切換按鈕。

#### 2.2 Layout 元件結構

**C:\Users\fatfi\works\macro-skills\frontend\src\components\layout\Layout.tsx**（第 1-18 行）

```typescript
import { ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
```

**Layout 特點**：
- 簡潔的三段式布局（Header、Main、Footer）
- 根容器使用 `bg-white` ← **深色模式需修改此處**
- 使用 `min-h-screen flex flex-col` 實現 Sticky Footer
- Header 固定在頂部（`sticky top-0`）

**深色模式實作考量**：
- 根容器的 `bg-white` 需改為 `bg-white dark:bg-gray-900`
- Header 的 `bg-white` 需改為 `bg-white dark:bg-gray-800`
- 所有文字顏色需新增 `dark:` 前綴變體

### 3. 樣式系統分析

#### 3.1 Tailwind CSS 配置

**C:\Users\fatfi\works\macro-skills\frontend\tailwind.config.js**（第 1-27 行）

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
  plugins: [],
}
```

**關鍵發現**：
- **未啟用 `darkMode` 選項** ← Tailwind 預設為 `'media'`（系統偏好）
- 自訂色彩系統：`primary` 藍色系列（50-900）
- 未使用其他 Tailwind 插件
- 內容掃描路徑正確（包含所有 TSX/JSX 檔案）

**需要的修改**：
```javascript
export default {
  darkMode: 'class', // ← 新增此行，啟用 class 策略
  // ... 其他配置
}
```

#### 3.2 全域樣式

**C:\Users\fatfi\works\macro-skills\frontend\src\index.css**（第 1-108 行）

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color: #213547;
  background-color: #ffffff;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

/* Prose table styling */
.prose table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.prose thead {
  background-color: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.prose th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
}

.prose td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.prose tbody tr:hover {
  background-color: #f9fafb;
}

.prose code:not(pre code) {
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  color: #1f2937;
}

.prose pre {
  background-color: #1f2937;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
}

.prose pre code {
  background-color: transparent;
  padding: 0;
  color: #e5e7eb;
}

/* ... 其他 prose 樣式 */
```

**關鍵發現**：
- `:root` 定義硬編碼的顏色值（`color: #213547`、`background-color: #ffffff`）
- `.prose` 自訂樣式使用硬編碼的灰階顏色
- 無深色模式相關的 CSS 變數或 class

**需要的修改**：
- `:root` 的顏色改用 Tailwind 的 `@apply` 或移除（讓 Tailwind 處理）
- `.prose` 樣式新增 `dark:` 變體
- 或使用 CSS 變數（`--color-bg`、`--color-text`）動態切換

#### 3.3 色彩使用模式分析

**搜尋專案中的色彩類別使用情況**：

常見的色彩類別：
- **背景色**：`bg-white`、`bg-gray-50`、`bg-gray-100`、`bg-gray-900`
- **文字色**：`text-gray-900`、`text-gray-600`、`text-gray-500`
- **邊框色**：`border-gray-200`、`border-gray-300`
- **Primary 色**：`bg-primary-600`、`text-primary-600`、`hover:text-primary-700`

**深色模式需要的映射**：
| 日間模式 | 夜間模式 |
|---------|---------|
| `bg-white` | `dark:bg-gray-900` |
| `bg-gray-50` | `dark:bg-gray-800` |
| `bg-gray-100` | `dark:bg-gray-700` |
| `text-gray-900` | `dark:text-gray-100` |
| `text-gray-600` | `dark:text-gray-400` |
| `text-gray-500` | `dark:text-gray-500` |
| `border-gray-200` | `dark:border-gray-700` |
| `border-gray-300` | `dark:border-gray-600` |

**Primary 色在深色模式的調整**：
- `bg-primary-600` → `dark:bg-primary-500`（稍微減淡以提升對比）
- `text-primary-600` → `dark:text-primary-400`（提升可讀性）

### 4. 現有元件參考分析

#### 4.1 Button 元件

**C:\Users\fatfi\works\macro-skills\frontend\src\components\common\Button.tsx**（第 1-44 行）

```typescript
import { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  children: ReactNode;
}

const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-primary-500',
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center font-medium rounded-lg
        focus:outline-none focus:ring-2 focus:ring-offset-2
        transition-colors disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}
```

**Button 設計模式**：
- 使用 variant 系統（primary、secondary、outline）
- 可配置尺寸（sm、md、lg）
- 可擴充 className（支援外部覆寫）
- TypeScript 型別完整（extends HTMLButtonElement）

**深色模式調整需求**：
```typescript
const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800',
};
```

#### 4.2 自訂 Hook 範例

**C:\Users\fatfi\works\macro-skills\frontend\src\hooks\useCopyToClipboard.ts**（第 1-18 行）

```typescript
import { useState } from 'react';

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

**Hook 設計模式**：
- 簡潔的狀態管理
- 自動重置機制（timeout）
- 錯誤處理
- 可重用於多個元件

**參考此模式建立 `useTheme` Hook**：
```typescript
export function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return { theme, toggleTheme };
}
```

### 5. 深色模式實作方案

#### 5.1 方案比較

**方案 A：Tailwind CSS 原生深色模式（推薦）**

**優點**：
- 無需額外套件依賴
- 與現有 Tailwind 生態完美整合
- 使用 `dark:` 前綴即可定義深色樣式
- 支援 `class` 或 `media` 策略
- 效能佳（純 CSS 實作）

**缺點**：
- 需要逐一為元件新增 `dark:` 樣式
- 初期工作量較大（需審視所有元件）

**實作步驟**：
1. 修改 `tailwind.config.js` 啟用 `darkMode: 'class'`
2. 建立 `useTheme` Hook 管理主題狀態
3. 在 `<html>` 或根元素新增/移除 `dark` class
4. 為所有元件新增 `dark:` 樣式變體
5. 使用 `localStorage` 持久化使用者偏好

---

**方案 B：CSS 變數 + JavaScript 切換**

**優點**：
- 集中管理顏色定義（單一來源）
- 易於動態調整顏色
- 可支援多主題（不僅限日間/夜間）

**缺點**：
- 需要重構現有的 Tailwind 色彩使用
- 增加 CSS 變數定義與維護成本
- 與 Tailwind 的整合較不直觀

**實作步驟**：
1. 定義 CSS 變數（`:root` 與 `[data-theme="dark"]`）
2. 修改 Tailwind 配置使用 CSS 變數
3. 使用 JavaScript 切換 `data-theme` 屬性
4. 更新所有元件使用變數

---

**方案 C：第三方套件（如 next-themes）**

**優點**：
- 開箱即用，功能完整
- 處理 SSR、系統偏好同步等複雜情境
- 社區維護

**缺點**：
- 增加套件依賴
- next-themes 主要為 Next.js 設計（本專案使用 Vite）
- 可能包含用不到的功能（過度設計）

**適用情境**：
- 需要複雜的主題管理（多主題、主題繼承）
- 使用 Next.js 框架

---

**推薦方案**：**方案 A（Tailwind 原生深色模式）**

**理由**：
- 與現有技術棧完美契合
- 無額外依賴，維護成本低
- Tailwind 3.4.1 原生支援完善
- 實作直觀，`dark:` 前綴易於理解
- 效能最佳（編譯時處理）

#### 5.2 推薦方案詳細設計

**階段 1：啟用 Tailwind 深色模式**

修改 `frontend/tailwind.config.js`：

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // ← 新增此行
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
  plugins: [],
}
```

**階段 2：建立主題管理系統**

**2.1 建立 ThemeContext**

新建檔案：`frontend/src/contexts/ThemeContext.tsx`

```typescript
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    // 1. 檢查 localStorage
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme) return savedTheme;

    // 2. 檢查系統偏好
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    // 3. 預設為日間模式
    return 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

**2.2 整合 ThemeProvider 至應用程式**

修改 `frontend/src/main.tsx`：

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext' // ← 新增
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider> {/* ← 包裹 ThemeProvider */}
      <HashRouter>
        <App />
      </HashRouter>
    </ThemeProvider>
  </React.StrictMode>,
)
```

**階段 3：建立主題切換按鈕元件**

新建檔案：`frontend/src/components/common/ThemeToggle.tsx`

```typescript
import { useTheme } from '../../contexts/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
      title={theme === 'light' ? '切換至夜間模式' : '切換至日間模式'}
      aria-label={theme === 'light' ? '切換至夜間模式' : '切換至日間模式'}
    >
      {theme === 'light' ? (
        // 月亮圖標（夜間模式）
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      ) : (
        // 太陽圖標（日間模式）
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      )}
    </button>
  );
}
```

**設計要點**：
- 使用 Heroicons 的太陽/月亮圖標
- 尺寸與 Discord/GitHub 圖標一致（`h-6 w-6`）
- 顏色使用 `text-gray-500` 系列（與現有圖標一致）
- 已新增 `dark:` 樣式變體
- 提供 `title` 與 `aria-label` 無障礙標籤

**階段 4：整合至 Header**

修改 `frontend/src/components/layout/Header.tsx`（第 40-67 行）：

```typescript
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from '../common/ThemeToggle'; // ← 新增

const navItems = [
  { path: '/skills', label: '技能 Skills' },
  { path: '/docs', label: '說明 Docs' },
  { path: '/submit', label: '提交 Submit' },
];

export default function Header() {
  const location = useLocation();

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      {/* ↑ 新增 dark: 樣式 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">📈</span>
            <span className="font-bold text-xl text-gray-900 dark:text-gray-100">
              {/* ↑ 新增 dark: 樣式 */}
              Macro Skills
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition-colors ${
                  location.pathname === item.path ||
                  (item.path === '/skills' && location.pathname.startsWith('/skills'))
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
                {/* ↑ 新增 dark: 樣式 */}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* 主題切換按鈕 */}
            <ThemeToggle /> {/* ← 新增 */}

            <a
              href="https://discord.gg/SDWSGXrhYq"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              {/* ↑ 新增 dark: 樣式 */}
              title="Discord"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515..." />
              </svg>
            </a>
            <a
              href="https://github.com/fatfingererr/macro-skills"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              {/* ↑ 新增 dark: 樣式 */}
              title="GitHub"
            >
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425..."
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
              {/* ↑ 新增 dark: 樣式 */}
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
```

**視覺位置**：

```
┌────────────────────────────────────────────────────────┐
│  📈 Macro Skills    技能 說明 提交     ☀️ 🎮 🐙       │
│                                       ↑  ↑  ↑         │
│                              主題切換 Discord GitHub  │
└────────────────────────────────────────────────────────┘
```

**階段 5：為核心元件新增深色模式樣式**

**5.1 Layout 元件**

修改 `frontend/src/components/layout/Layout.tsx`：

```typescript
export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900">
      {/* ↑ 新增 dark:bg-gray-900 */}
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
```

**5.2 Footer 元件**

修改 `frontend/src/components/layout/Footer.tsx`（需新增 `dark:` 樣式）：

```typescript
<footer className="bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
  {/* 所有文字色改為：text-gray-900 dark:text-gray-100 或 text-gray-600 dark:text-gray-400 */}
</footer>
```

**5.3 Button 元件**

修改 `frontend/src/components/common/Button.tsx`：

```typescript
const variants = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 dark:bg-primary-500 dark:hover:bg-primary-600',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-primary-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800',
};
```

**5.4 SkillCard 元件**

修改卡片背景與邊框：

```typescript
<div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 hover:shadow-lg transition-shadow">
  {/* 標題 */}
  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
    {skill.displayName}
  </h3>

  {/* 描述 */}
  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
    {skill.description}
  </p>
</div>
```

**階段 6：更新全域樣式**

修改 `frontend/src/index.css`（移除硬編碼顏色）：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* 移除 color 與 background-color，讓 Tailwind 處理 */
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

/* Prose styles - 新增深色模式變體 */
.prose table {
  @apply w-full border-collapse my-6;
}

.prose thead {
  @apply bg-gray-50 dark:bg-gray-800 border-b-2 border-gray-200 dark:border-gray-700;
}

.prose th {
  @apply px-4 py-3 text-left font-semibold text-gray-700 dark:text-gray-300;
}

.prose td {
  @apply px-4 py-3 border-b border-gray-200 dark:border-gray-700;
}

.prose tbody tr:hover {
  @apply bg-gray-50 dark:bg-gray-800;
}

.prose code:not(pre code) {
  @apply bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm text-gray-900 dark:text-gray-100;
}

.prose pre {
  @apply bg-gray-900 dark:bg-gray-950 rounded-lg p-4 overflow-x-auto;
}

.prose pre code {
  @apply bg-transparent p-0 text-gray-100;
}

.prose h2 {
  @apply mt-8 mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100;
}

.prose h3 {
  @apply mt-6 mb-3 text-xl font-semibold text-gray-900 dark:text-gray-100;
}

.prose a {
  @apply text-primary-600 dark:text-primary-400 no-underline hover:underline;
}
```

#### 5.3 實作優先順序

**第一階段：核心功能（必須）**
1. ✅ 修改 `tailwind.config.js` 啟用 `darkMode: 'class'`
2. ✅ 建立 `ThemeContext.tsx`
3. ✅ 修改 `main.tsx` 整合 ThemeProvider
4. ✅ 建立 `ThemeToggle.tsx` 元件
5. ✅ 修改 `Header.tsx` 整合主題切換按鈕
6. ✅ 修改 `Layout.tsx` 新增深色背景

**第二階段：元件適配（重要）**
7. 修改 `Footer.tsx` 新增深色樣式
8. 修改 `Button.tsx` 新增深色變體
9. 修改 `Badge.tsx` 新增深色變體
10. 修改 `SkillCard.tsx` 新增深色樣式
11. 修改 `HomePage.tsx` 的漸層背景（`bg-gradient-to-br from-primary-50 to-white`）

**第三階段：頁面適配（逐步進行）**
12. 修改 `SkillsPage.tsx`
13. 修改 `SkillDetailPage.tsx`
14. 修改 `DocsPage.tsx`
15. 修改 `SubmitPage.tsx`
16. 更新 `index.css` 的 `.prose` 樣式

**第四階段：精細調整（可選）**
17. 檢查所有邊框、陰影顏色
18. 調整 hover 狀態對比度
19. 檢查表單元件（SearchInput、Pagination）
20. 無障礙測試（顏色對比度）

### 6. 實作步驟詳解

#### 6.1 完整實作檢查清單

**步驟 1：配置 Tailwind 深色模式**
- [ ] 修改 `frontend/tailwind.config.js` 新增 `darkMode: 'class'`
- [ ] 執行 `npm run dev` 確認編譯無誤

**步驟 2：建立主題管理系統**
- [ ] 建立 `frontend/src/contexts/ThemeContext.tsx`
- [ ] 實作 ThemeProvider 與 useTheme Hook
- [ ] 新增 localStorage 持久化
- [ ] 新增系統偏好檢測

**步驟 3：整合 ThemeProvider**
- [ ] 修改 `frontend/src/main.tsx`
- [ ] 將 ThemeProvider 包裹在 HashRouter 外層
- [ ] 測試初始化流程

**步驟 4：建立主題切換按鈕**
- [ ] 建立 `frontend/src/components/common/ThemeToggle.tsx`
- [ ] 實作太陽/月亮圖標切換
- [ ] 新增無障礙標籤（aria-label、title）
- [ ] 新增 hover 效果

**步驟 5：整合至 Header**
- [ ] 修改 `frontend/src/components/layout/Header.tsx`
- [ ] 在右側圖標區塊新增 ThemeToggle
- [ ] 為 Header 背景新增 `dark:bg-gray-800`
- [ ] 為 Logo 文字新增 `dark:text-gray-100`
- [ ] 為導航連結新增深色樣式
- [ ] 為社交圖標新增深色樣式

**步驟 6：更新核心元件**
- [ ] 修改 `Layout.tsx` 根容器背景
- [ ] 修改 `Footer.tsx` 所有文字與背景色
- [ ] 修改 `Button.tsx` 三種 variant 的深色樣式
- [ ] 修改 `Badge.tsx` DataLevel 顏色映射

**步驟 7：更新頁面元件**
- [ ] 修改 `HomePage.tsx` 漸層背景與卡片
- [ ] 修改 `SkillsPage.tsx` 搜尋區與卡片
- [ ] 修改 `SkillCard.tsx` 卡片背景與邊框
- [ ] 修改其他頁面的深色樣式

**步驟 8：更新全域樣式**
- [ ] 修改 `index.css` 移除 `:root` 硬編碼顏色
- [ ] 使用 `@apply` 重寫 `.prose` 樣式
- [ ] 新增所有 `.prose` 的深色變體

**步驟 9：測試與驗證**
- [ ] 測試主題切換功能
- [ ] 測試 localStorage 持久化
- [ ] 測試所有頁面的深色模式顯示
- [ ] 檢查顏色對比度（WCAG AA 標準）
- [ ] 測試行動版響應式
- [ ] 測試瀏覽器相容性

**步驟 10：優化與打磨**
- [ ] 新增主題切換過渡動畫
- [ ] 優化初始化閃爍問題（FOUC）
- [ ] 新增系統偏好自動同步
- [ ] 文件更新（README）

#### 6.2 關鍵技術挑戰與解決方案

**挑戰 1：初始化閃爍（Flash of Unstyled Content）**

**問題**：頁面載入時，可能先顯示日間模式，再切換至深色模式，造成閃爍。

**解決方案**：在 HTML 載入前執行腳本

修改 `frontend/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Macro Skills | 宏觀分析技能市集</title>
  <meta name="description" content="探索並安裝 Claude Code 的技能，提升你的開發效率" />

  <!-- 防止深色模式閃爍 -->
  <script>
    (function() {
      const theme = localStorage.getItem('theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      }
    })();
  </script>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

---

**挑戰 2：系統偏好自動同步**

**問題**：使用者更改系統深色模式偏好後，網站未自動同步。

**解決方案**：監聽 `prefers-color-scheme` 變化

修改 `ThemeContext.tsx`：

```typescript
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme) return savedTheme;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  // 監聽系統偏好變化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        // 只在使用者未手動設定時才同步
        setTheme(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // ... 其他邏輯
}
```

---

**挑戰 3：深色模式下的顏色對比度**

**問題**：某些顏色在深色模式下可讀性不佳。

**解決方案**：使用 Tailwind 的色彩系統對應

| 元素類型 | 日間模式 | 夜間模式 | 對比度檢查 |
|---------|---------|---------|-----------|
| 主要文字 | `text-gray-900` | `dark:text-gray-100` | ✅ AAA |
| 次要文字 | `text-gray-600` | `dark:text-gray-400` | ✅ AA |
| 淡化文字 | `text-gray-500` | `dark:text-gray-500` | ✅ AA |
| 連結 | `text-primary-600` | `dark:text-primary-400` | ✅ AA |
| 背景 | `bg-white` | `dark:bg-gray-900` | - |
| 卡片背景 | `bg-white` | `dark:bg-gray-800` | - |
| 邊框 | `border-gray-200` | `dark:border-gray-700` | ✅ |

**工具推薦**：
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Chrome DevTools > Lighthouse（無障礙審查）

---

**挑戰 4：過渡動畫不流暢**

**問題**：切換主題時，元素顏色變化生硬。

**解決方案**：新增全域過渡效果

修改 `index.css`：

```css
/* 深色模式過渡動畫 */
* {
  @apply transition-colors duration-200;
}

/* 排除不需要過渡的元素 */
button,
a,
input,
textarea,
select {
  @apply transition-all duration-200;
}
```

**注意**：過度使用過渡可能影響效能，建議僅針對背景、文字色套用。

#### 6.3 測試策略

**功能測試**
1. **主題切換**
   - [ ] 點擊按鈕可正常切換
   - [ ] 圖標正確顯示（太陽/月亮）
   - [ ] 整個頁面樣式正確變化

2. **持久化**
   - [ ] 重新整理頁面後主題保持
   - [ ] 關閉分頁後重新開啟主題保持
   - [ ] localStorage 正確儲存

3. **系統偏好**
   - [ ] 初次訪問時根據系統偏好顯示
   - [ ] 手動切換後不再跟隨系統偏好
   - [ ] 系統偏好變化時（未手動設定時）自動同步

**視覺測試**
1. **所有頁面**
   - [ ] 首頁
   - [ ] 技能列表頁
   - [ ] 技能詳情頁
   - [ ] 文件頁
   - [ ] 提交頁

2. **所有元件**
   - [ ] Header
   - [ ] Footer
   - [ ] Button（三種 variant）
   - [ ] Badge（所有類型）
   - [ ] SkillCard
   - [ ] Pagination
   - [ ] SearchInput
   - [ ] Modal

3. **響應式**
   - [ ] 桌面版（> 1024px）
   - [ ] 平板版（640px - 1024px）
   - [ ] 行動版（< 640px）

**無障礙測試**
- [ ] 鍵盤導航（Tab、Enter）
- [ ] 螢幕閱讀器（NVDA/VoiceOver）
- [ ] 顏色對比度（WCAG AA）
- [ ] Focus 狀態可見

**瀏覽器相容性**
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### 7. 圖標設計選項

#### 7.1 Heroicons（推薦）

**太陽圖標（日間模式）**：
```html
<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path
    strokeLinecap="round"
    strokeLinejoin="round"
    strokeWidth={2}
    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
  />
</svg>
```

**月亮圖標（夜間模式）**：
```html
<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path
    strokeLinecap="round"
    strokeLinejoin="round"
    strokeWidth={2}
    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
  />
</svg>
```

**優點**：
- 與 Discord/GitHub 圖標風格一致（outline 風格）
- 無需額外依賴
- 尺寸可調（使用 `currentColor`）
- MIT 授權

#### 7.2 其他選項

**選項 A：Lucide Icons**
- 與 Heroicons 風格類似
- 提供 React 元件包裝
- 需要安裝 `lucide-react`

**選項 B：Phosphor Icons**
- 提供 fill 與 outline 兩種風格
- 圖標更豐富
- 需要安裝 `phosphor-react`

**選項 C：自訂 Emoji**
- 使用 ☀️ 和 🌙 emoji
- 無需 SVG
- 風格與 Logo（📈）一致
- 尺寸與顏色控制受限

**推薦**：使用 **Heroicons**（選項 1），因為：
- 無需額外套件
- 風格與現有圖標一致
- 可控性高（顏色、尺寸）

### 8. 進階功能（可選）

#### 8.1 主題切換過渡動畫

新增優雅的過渡效果：

```typescript
// ThemeContext.tsx
const toggleTheme = () => {
  const newTheme = theme === 'light' ? 'dark' : 'light';

  // 新增過渡 class
  document.documentElement.classList.add('theme-transition');

  setTheme(newTheme);

  // 移除過渡 class（避免影響其他動畫）
  setTimeout(() => {
    document.documentElement.classList.remove('theme-transition');
  }, 300);
};
```

```css
/* index.css */
.theme-transition,
.theme-transition *,
.theme-transition *::before,
.theme-transition *::after {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
}
```

#### 8.2 主題選擇器（三種模式）

擴充為「日間 / 夜間 / 自動」三種模式：

```typescript
type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  mode: ThemeMode;
  theme: Theme; // 實際使用的主題
  setMode: (mode: ThemeMode) => void;
}
```

新增下拉選單：

```typescript
<select onChange={(e) => setMode(e.target.value as ThemeMode)}>
  <option value="light">☀️ 日間模式</option>
  <option value="dark">🌙 夜間模式</option>
  <option value="system">💻 跟隨系統</option>
</select>
```

#### 8.3 多主題支援

支援自訂顏色主題（如「藍色」、「綠色」、「紫色」）：

```typescript
type ColorTheme = 'blue' | 'green' | 'purple';

// Tailwind 配置中定義多組 primary 色
colors: {
  primary: {
    blue: { /* ... */ },
    green: { /* ... */ },
    purple: { /* ... */ },
  }
}
```

使用 CSS 變數動態切換。

## 程式碼引用

### 現有架構

- **Header.tsx**（第 1-82 行）- 頂部導航列元件
- **Layout.tsx**（第 1-18 行）- 主要版面配置元件
- **tailwind.config.js**（第 1-27 行）- Tailwind CSS 配置
- **index.css**（第 1-108 行）- 全域樣式
- **App.tsx**（第 1-24 行）- 應用程式路由定義
- **main.tsx**（第 1-14 行）- React 根元件掛載

### 元件範例

- **Button.tsx**（第 1-44 行）- 按鈕元件（variant 系統）
- **useCopyToClipboard.ts**（第 1-18 行）- 自訂 Hook 範例

### 配置檔案

- **package.json**（第 1-37 行）- 專案依賴與腳本
- **vite.config.ts**（第 1-18 行）- Vite 配置

## 相關研究

- **前端專案結構**: `frontend/` 目錄
- **技能詳情頁重新設計**: `thoughts/shared/research/2026-01-13-skill-detail-page-redesign-v2.md`

## 開放問題

1. **主題切換按鈕位置**
   - 建議：Discord 圖標之前
   - 備選：GitHub 圖標之後
   - 決策：需視視覺平衡而定

2. **初始主題偏好**
   - 優先順序：localStorage > 系統偏好 > 預設（日間）
   - 或：系統偏好 > localStorage > 預設
   - 建議：前者（使用者手動選擇優先）

3. **行動版顯示**
   - 主題切換按鈕是否顯示在 Hamburger Menu 內
   - 或固定顯示在右上方
   - 建議：固定顯示（提升可及性）

4. **過渡動畫強度**
   - 快速切換（100ms）vs 流暢過渡（300ms）
   - 或不使用過渡（立即切換）
   - 建議：200ms 中等速度

5. **深色模式預設啟用**
   - 是否預設為深色模式（考慮目標使用者）
   - 建議：跟隨系統偏好

## 結論

本研究詳細分析了 Macro Skills 前端專案的技術架構與樣式系統，確定專案使用 React 18 + TypeScript + Vite + Tailwind CSS 技術棧，目前完全沒有深色模式相關設定。

實作深色模式切換功能的建議方案為 **Tailwind CSS 原生深色模式 + React Context**，使用 `class` 策略控制深色模式，搭配 `localStorage` 持久化使用者偏好。主題切換按鈕將插入至 Header 右上方的社交圖標區域，使用太陽/月亮圖標表示當前模式。

實作流程分為十個步驟：(1) 啟用 Tailwind 深色模式配置，(2) 建立 ThemeContext 與 useTheme Hook，(3) 整合 ThemeProvider，(4) 建立 ThemeToggle 元件，(5) 整合至 Header，(6) 更新核心元件，(7) 更新頁面元件，(8) 更新全域樣式，(9) 測試與驗證，(10) 優化與打磨。

關鍵技術挑戰包括防止初始化閃爍（FOUC）、系統偏好自動同步、深色模式顏色對比度確保、以及過渡動畫流暢度。所有挑戰均有明確的解決方案，包括在 HTML 載入前執行腳本、監聽 `prefers-color-scheme` 變化、使用 Tailwind 標準色彩映射、以及新增全域過渡效果。

預估實作時間：
- 核心功能（第 1-6 階段）：2-3 小時
- 元件適配（第 7-11 階段）：3-4 小時
- 頁面適配（第 12-16 階段）：2-3 小時
- 精細調整（第 17-20 階段）：1-2 小時
- **總計**：8-12 小時

此方案無需額外套件依賴，與現有技術棧完美整合，實作成本低且維護性高，是最適合 Macro Skills 專案的深色模式實作方案。
