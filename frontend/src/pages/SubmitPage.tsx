import { Link } from 'react-router-dom';
import Button from '../components/common/Button';

export default function SubmitPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">提交技能</h1>

      <div className="prose prose-gray max-w-none">
        <p className="text-lg text-gray-600 mb-8">
          歡迎提交你的技能到 Macro Skills 市集！請按照以下步驟操作：
        </p>

        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 mt-0">提交流程</h2>

          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                1
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mt-0 mb-1">建立技能檔案</h3>
                <p className="text-gray-600 m-0">
                  建立一個 <code className="bg-gray-100 px-1 rounded">SKILL.md</code> 檔案，
                  包含完整的 frontmatter 和說明文件。
                  請參考<Link to="/docs" className="text-primary-600">文件說明</Link>了解格式要求。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                2
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mt-0 mb-1">Fork 專案</h3>
                <p className="text-gray-600 m-0">
                  Fork{' '}
                  <a
                    href="https://github.com/fatfingererr/macro-skills"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600"
                  >
                    macro-skills
                  </a>{' '}
                  專案到你的 GitHub 帳號。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                3
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mt-0 mb-1">新增你的技能</h3>
                <p className="text-gray-600 m-0">
                  在 <code className="bg-gray-100 px-1 rounded">marketplace/skills/</code> 目錄下
                  建立新資料夾，放入你的 <code className="bg-gray-100 px-1 rounded">SKILL.md</code>。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                4
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mt-0 mb-1">提交 Pull Request</h3>
                <p className="text-gray-600 m-0">
                  向原專案提交 Pull Request，並在描述中說明你的技能功能。
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                5
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mt-0 mb-1">等待審核</h3>
                <p className="text-gray-600 m-0">
                  我們會審核你的技能，確認格式正確且內容適當後即會合併。
                </p>
              </div>
            </div>
          </div>
        </div>

        <h2>技能範本</h2>
        <p>你可以使用以下範本開始：</p>
        <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
{`---
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
riskLevel: safe
tools:
  - claude-code
featured: false
installCount: 0
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

展示技能的實際使用範例和預期輸出。`}
        </pre>

        <h2>審核標準</h2>
        <ul>
          <li>技能必須與宏觀經濟分析相關（或其他對使用者有價值的功能）</li>
          <li>說明文件必須清楚完整</li>
          <li>風險等級必須如實標示</li>
          <li>不得包含惡意或有害內容</li>
        </ul>

        <div className="mt-8">
          <a
            href="https://github.com/fatfingererr/macro-skills/fork"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="lg">前往 GitHub Fork 專案</Button>
          </a>
        </div>
      </div>
    </div>
  );
}
