import { Link } from 'react-router-dom';
import { categories } from '../data/categories';

export default function DocsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">文件說明</h1>
      <p className="text-gray-600 mb-8">了解如何使用 Macro Skills 技能市集</p>

      <div className="space-y-8">
        {/* What is Macro Skills */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📈</span>
            什麼是 Macro Skills？
          </h2>
          <p className="text-gray-600 leading-relaxed">
            Macro Skills 是一個專為 Claude Code 設計的技能市集，專注於宏觀經濟分析領域。
            透過安裝這些技能，你可以讓 Claude Code 具備專業的經濟數據分析、央行政策解讀、
            市場週期判斷等能力。
          </p>
        </section>

        {/* How to Install */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">⚡</span>
            如何安裝技能？
          </h2>
          <ol className="space-y-3 text-gray-600 mb-6">
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-semibold">1</span>
              <span>瀏覽<Link to="/skills" className="text-primary-600 hover:underline">技能列表</Link>，找到你需要的技能</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-semibold">2</span>
              <span>點擊「安裝」按鈕</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-semibold">3</span>
              <span>複製彈出的安裝指令</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-semibold">4</span>
              <span>在終端機中執行該指令</span>
            </li>
          </ol>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <code className="text-green-400 text-sm">
              claude mcp add economic-indicator-analyst https://github.com/fatfingererr/macro-skills/marketplace/skills/economic-indicator-analyst
            </code>
          </div>
        </section>

        {/* Risk Levels */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">🛡️</span>
            技能風險等級
          </h2>
          <p className="text-gray-600 mb-4">每個技能都有對應的風險等級標示：</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">等級</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">說明</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">安全</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">僅執行分析與建議，不會修改任何檔案或系統</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">低風險</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">可能讀取本地檔案進行分析</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">中風險</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">可能修改本地檔案</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">高風險</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">可能執行系統指令</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">關鍵</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">具有完整系統存取權限</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Skill Format */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📝</span>
            技能格式
          </h2>
          <p className="text-gray-600 mb-4">
            每個技能都使用 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">SKILL.md</code> 格式定義，包含 YAML frontmatter 和 Markdown 內容：
          </p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-gray-100 text-sm leading-relaxed">{`---
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
\`\`\``}</pre>
          </div>
        </section>

        {/* Categories */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📂</span>
            支援的分類
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">ID</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">中文</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">English</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {categories.map((cat) => (
                  <tr key={cat.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5">
                      <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{cat.id}</code>
                    </td>
                    <td className="px-4 py-2.5 text-gray-700">{cat.name}</td>
                    <td className="px-4 py-2.5 text-gray-500">{cat.nameEn}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Help */}
        <section className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-100 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
            <span className="text-2xl">💬</span>
            需要協助？
          </h2>
          <p className="text-gray-600">
            如有任何問題，歡迎在{' '}
            <a
              href="https://github.com/fatfingererr/macro-skills/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline font-medium"
            >
              GitHub Issues
            </a>{' '}
            提出，或加入我們的{' '}
            <a
              href="https://discord.gg/zReHspPEzZ"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline font-medium"
            >
              Discord
            </a>{' '}
            社群。
          </p>
        </section>
      </div>
    </div>
  );
}
