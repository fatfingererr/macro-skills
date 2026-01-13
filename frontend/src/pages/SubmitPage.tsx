import { Link } from 'react-router-dom';
import Button from '../components/common/Button';

export default function SubmitPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">提交技能</h1>
      <p className="text-gray-600 mb-8">歡迎提交你的技能到 Macro Skills！請按照以下步驟操作</p>

      <div className="space-y-8">
        {/* Submission Steps */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <span className="text-2xl">📋</span>
            提交流程
          </h2>

          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-lg">
                  1
                </div>
              </div>
              <div className="flex-1 pt-1">
                <h3 className="font-semibold text-gray-900 mb-1">建立技能檔案</h3>
                <p className="text-gray-600">
                  建立一個 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">SKILL.md</code> 檔案，
                  包含完整的 frontmatter 和說明文件。
                  請參考<Link to="/docs" className="text-primary-600 hover:underline">文件說明</Link>了解格式要求。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-lg">
                  2
                </div>
              </div>
              <div className="flex-1 pt-1">
                <h3 className="font-semibold text-gray-900 mb-1">Fork 專案</h3>
                <p className="text-gray-600">
                  Fork{' '}
                  <a
                    href="https://github.com/fatfingererr/macro-skills"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:underline"
                  >
                    macro-skills
                  </a>{' '}
                  專案到你的 GitHub 帳號。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-lg">
                  3
                </div>
              </div>
              <div className="flex-1 pt-1">
                <h3 className="font-semibold text-gray-900 mb-1">新增你的技能</h3>
                <p className="text-gray-600">
                  在 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">marketplace/skills/</code> 目錄下
                  建立新資料夾，放入你的 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">SKILL.md</code>。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-lg">
                  4
                </div>
              </div>
              <div className="flex-1 pt-1">
                <h3 className="font-semibold text-gray-900 mb-1">提交 Pull Request</h3>
                <p className="text-gray-600">
                  向原專案提交 Pull Request，並在描述中說明你的技能功能。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-lg">
                  5
                </div>
              </div>
              <div className="flex-1 pt-1">
                <h3 className="font-semibold text-gray-900 mb-1">等待審核</h3>
                <p className="text-gray-600">
                  我們會審核你的技能，確認格式正確且內容適當後即會合併。
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Template */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📝</span>
            技能範本
          </h2>
          <p className="text-gray-600 mb-4">你可以使用以下範本開始：</p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-gray-100 text-sm leading-relaxed">{`---
name: your-skill-name
displayName: 你的技能名稱
description: 簡短描述你的技能功能（1-2 句話）
emoji: 📊
version: v1.0.0
license: MIT
author: 你的名字
authorUrl: https://github.com/your-username
tags:
  - 標籤1
  - 標籤2
category: research
dataLevel: free-nolimit
tools:
  - claude-code
featured: false
---

# 你的技能名稱

詳細說明這個技能的功能與用途。

## 使用時機

- 描述什麼情況下應該使用這個技能
- 另一個使用情境

## 使用方式

在 Claude Code 中輸入：

\`\`\`
你的指令範例
\`\`\`

## 範例

展示技能的實際使用範例和預期輸出。`}</pre>
          </div>
        </section>

        {/* Review Criteria */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">✅</span>
            審核標準
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-600">技能必須與宏觀經濟分析相關（或其他對使用者有價值的功能）</span>
            </div>
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-600">說明文件必須清楚完整</span>
            </div>
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-600">資料等級 (dataLevel) 必須如實標示</span>
            </div>
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-600">不得包含惡意或有害內容</span>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-100 rounded-xl p-6 text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">準備好了嗎？</h2>
          <p className="text-gray-600 mb-6">
            開始 Fork 專案並建立你的第一個技能吧！
          </p>
          <a
            href="https://github.com/fatfingererr/macro-skills/fork"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="lg">
              前往 GitHub Fork 專案
            </Button>
          </a>
        </section>
      </div>
    </div>
  );
}
