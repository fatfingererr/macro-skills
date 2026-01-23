import { Link } from 'react-router-dom';
import { categories, dataLevels } from '../data/categories';

export default function DocsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">使用說明</h1>
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
              /plugin marketplace add fatfingererr/macro-skills
              <br />
              /plugin install economic-indicator-analyst@macro-skills
            </code>
          </div>
        </section>

        {/* Data Levels */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📊</span>
            資料等級 (DataLevel)
          </h2>
          <p className="text-gray-600 mb-4">每個技能都標示其資料來源的成本與限制等級：</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">等級</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">成本</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">說明</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dataLevels.map((level) => {
                  const colorMap: Record<string, string> = {
                    green: 'bg-green-100 text-green-800',
                    yellow: 'bg-yellow-100 text-yellow-800',
                    blue: 'bg-blue-100 text-blue-800',
                    purple: 'bg-purple-100 text-purple-800',
                    red: 'bg-red-100 text-red-800',
                  };
                  return (
                    <tr key={level.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 ${colorMap[level.color]} rounded-full text-sm font-medium`}>
                          {level.emoji} {level.name}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700 font-mono text-sm">{level.cost}</td>
                      <td className="px-4 py-3 text-gray-600">{level.description}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* Quality Badge */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">✨</span>
            技能品質等級 (Quality Badge)
          </h2>
          <p className="text-gray-600 mb-4">每個技能根據六項維度評分（任務適配度、正確性、資料治理、穩健性、可維護性、輸出可用性）的平均分數，分為五個品質等級：</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">等級</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">分數範圍</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">說明</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-purple-100 text-purple-800 border border-purple-300 rounded-full text-sm font-medium">
                      💎 頂級
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-sm">90-100</td>
                  <td className="px-4 py-3 text-gray-600">最高品質，完整文檔與測試，可直接用於生產環境</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-amber-100 text-amber-800 border border-amber-300 rounded-full text-sm font-medium">
                      🏆 高級
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-sm">80-89</td>
                  <td className="px-4 py-3 text-gray-600">高品質，具備完整工作流程與參考文檔</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-blue-100 text-blue-700 border border-blue-300 rounded-full text-sm font-medium">
                      🥈 中高級
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-sm">60-79</td>
                  <td className="px-4 py-3 text-gray-600">標準品質，功能完整但可能缺少部分文檔</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-orange-100 text-orange-800 border border-orange-300 rounded-full text-sm font-medium">
                      🥉 中級
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-sm">40-59</td>
                  <td className="px-4 py-3 text-gray-600">基本可用，但穩定性或文檔有待加強</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-gray-50 text-gray-600 border border-gray-200 rounded-full text-sm font-medium">
                      🌱 初級
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-sm">0-39</td>
                  <td className="px-4 py-3 text-gray-600">早期開發階段，功能可能不完整</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">💡 提示：</span>
              技能詳情頁面可查看各維度的詳細評分與改進建議。
            </p>
          </div>
        </section>

        {/* Categories */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📂</span>
            支援的分類 (Category)
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



        {/* Skill Structure */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📁</span>
            技能目錄結構
          </h2>
          <p className="text-gray-600 mb-4">
            每個技能由三個核心檔案組成，各司其職：
          </p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto mb-4">
            <pre className="text-gray-100 text-sm leading-relaxed">{`skills/{skill-name}/
├── SKILL.md          # 技能內容（Claude 執行用）
├── skill.yaml        # 前端展示設定
├── manifest.json     # 技能元資料
├── workflows/        # 工作流程定義
├── references/       # 參考文件
├── templates/        # 輸出模板
├── scripts/          # 執行腳本
└── examples/         # 範例輸出（選用）`}</pre>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">檔案</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">用途</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">讀取者</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-2.5"><code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">SKILL.md</code></td>
                  <td className="px-4 py-2.5 text-gray-700">技能執行邏輯與內容</td>
                  <td className="px-4 py-2.5 text-gray-500">Claude Code</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-2.5"><code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">skill.yaml</code></td>
                  <td className="px-4 py-2.5 text-gray-700">前端展示設定</td>
                  <td className="px-4 py-2.5 text-gray-500">Frontend</td>
                </tr>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-2.5"><code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">manifest.json</code></td>
                  <td className="px-4 py-2.5 text-gray-700">技能元資料</td>
                  <td className="px-4 py-2.5 text-gray-500">Frontend + Claude Code</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* SKILL.md Format */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📝</span>
            SKILL.md 格式
          </h2>
          <p className="text-gray-600 mb-4">
            SKILL.md 的 frontmatter 只放 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">name</code> 和 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">description</code>，其他元資料都在 manifest.json 或 skill.yaml：
          </p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-gray-100 text-sm leading-relaxed">{`---
name: my-skill
description: 技能的一句話描述
---

<essential_principles>
**技能名稱 核心原則**

<principle name="principle_1">
**原則標題**
原則內容說明...
</principle>
</essential_principles>

<intake>
**您想要執行什麼操作？**

1. **操作一** - 操作描述
2. **操作二** - 操作描述

**等待回應後再繼續。**
</intake>

<routing>
| Response              | Workflow         | Description |
|-----------------------|------------------|-------------|
| 1, "keyword1"         | workflows/xxx.md | 操作描述    |
| 2, "keyword2"         | workflows/yyy.md | 操作描述    |

**讀取工作流程後，請完全遵循其步驟。**
</routing>`}</pre>
          </div>
        </section>

        {/* manifest.json Format */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">📦</span>
            manifest.json 格式
          </h2>
          <p className="text-gray-600 mb-4">
            manifest.json 存放技能元資料，供 Claude Code 和前端共同使用：
          </p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-gray-100 text-sm leading-relaxed">{`{
  "name": "my-skill",
  "version": "0.1.0",
  "displayName": "我的技能",
  "description": "技能的完整描述",
  "author": "作者名稱",
  "license": "MIT",
  "category": "indicator-monitoring",
  "tags": ["標籤1", "標籤2"],
  "dataLevel": "free-nolimit",
  "dependencies": {
    "python": ">=3.8",
    "packages": ["pandas>=1.5.0"]
  },
  "entryPoints": {
    "skill": "SKILL.md",
    "mainScript": "scripts/main.py"
  },
  "workflows": [
    {
      "id": "analyze",
      "name": "分析",
      "file": "workflows/analyze.md"
    }
  ]
}`}</pre>
          </div>
        </section>

        {/* skill.yaml Format */}
        <section className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-2xl">🎨</span>
            skill.yaml 格式
          </h2>
          <p className="text-gray-600 mb-4">
            skill.yaml 存放前端展示專用設定，不影響 Claude Code 執行：
          </p>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-gray-100 text-sm leading-relaxed">{`# 前端展示專用
displayName: 我的技能
emoji: "📊"
authorUrl: https://github.com/username/repo

tools:
  - claude-code

featured: false
installCount: 0

testQuestions:
  - question: '範例問題'
    expectedResult: |
      預期結果說明...
    imagePath: 'images/example.png'

qualityScore:
  overall: 75
  badge: 白銀
  metrics:
    architecture: 80
    maintainability: 80

bestPractices:
  - title: 最佳實踐
    description: 說明...

pitfalls:
  - title: 常見陷阱
    description: 陷阱描述
    consequence: 導致的後果

faq:
  - question: 常見問題？
    answer: 回答內容...`}</pre>
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
              href="https://discord.gg/SDWSGXrhYq"
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
