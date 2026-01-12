import { Link } from 'react-router-dom';
import { categories } from '../data/categories';

export default function DocsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">文件說明</h1>

      <div className="prose prose-gray max-w-none">
        <h2>什麼是 Macro Skills？</h2>
        <p>
          Macro Skills 是一個專為 Claude Code 設計的技能市集，專注於宏觀經濟分析領域。
          透過安裝這些技能，你可以讓 Claude Code 具備專業的經濟數據分析、央行政策解讀、
          市場週期判斷等能力。
        </p>

        <h2>如何安裝技能？</h2>
        <ol>
          <li>瀏覽<Link to="/skills" className="text-primary-600">技能列表</Link>，找到你需要的技能</li>
          <li>點擊「安裝」按鈕</li>
          <li>複製彈出的安裝指令</li>
          <li>在終端機中執行該指令</li>
        </ol>

        <h3>安裝指令範例</h3>
        <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
          <code>claude mcp add economic-indicator-analyst https://github.com/fatfingererr/macro-skills/marketplace/skills/economic-indicator-analyst</code>
        </pre>

        <h2>技能風險等級</h2>
        <p>每個技能都有對應的風險等級標示：</p>
        <table>
          <thead>
            <tr>
              <th>等級</th>
              <th>說明</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-sm">安全</span></td>
              <td>僅執行分析與建議，不會修改任何檔案或系統</td>
            </tr>
            <tr>
              <td><span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-sm">低風險</span></td>
              <td>可能讀取本地檔案進行分析</td>
            </tr>
            <tr>
              <td><span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-sm">中風險</span></td>
              <td>可能修改本地檔案</td>
            </tr>
            <tr>
              <td><span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-sm">高風險</span></td>
              <td>可能執行系統指令</td>
            </tr>
            <tr>
              <td><span className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-sm">關鍵</span></td>
              <td>具有完整系統存取權限</td>
            </tr>
          </tbody>
        </table>

        <h2>技能格式</h2>
        <p>每個技能都使用 <code>SKILL.md</code> 格式定義，包含 YAML frontmatter 和 Markdown 內容：</p>
        <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
{`---
name: my-skill
displayName: 我的技能
description: 技能簡短描述
emoji: 📊
version: v1.0.0
license: MIT
author: 作者名稱
tags:
  - 標籤1
  - 標籤2
category: indicator-monitoring
riskLevel: safe
tools:
  - claude-code
featured: false
---

# 技能名稱

詳細說明...

## 使用時機

- 情境 1
- 情境 2

## 使用方式

\`\`\`
範例指令
\`\`\``}
        </pre>

        <h2>支援的分類</h2>
        <table className="text-sm">
          <thead>
            <tr>
              <th>ID</th>
              <th>中文</th>
              <th>English</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat.id}>
                <td><code>{cat.id}</code></td>
                <td>{cat.name}</td>
                <td>{cat.nameEn}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>需要協助？</h2>
        <p>
          如有任何問題，歡迎在{' '}
          <a
            href="https://github.com/fatfingererr/macro-skills/issues"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub Issues
          </a>{' '}
          提出。
        </p>
      </div>
    </div>
  );
}
