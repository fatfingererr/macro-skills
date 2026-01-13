import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { QualityScore } from '../../types/skill';

interface QualityScoreCardProps {
  qualityScore: QualityScore;
}

export default function QualityScoreCard({ qualityScore }: QualityScoreCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  // 根據分數決定徽章顏色
  const getBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (score >= 60) return 'bg-gray-100 text-gray-800 border-gray-300';
    return 'bg-orange-100 text-orange-800 border-orange-300';
  };

  // 指標名稱與 emoji 映射
  const metricConfig: Record<string, { name: string; emoji: string }> = {
    architecture: { name: '架構', emoji: '🏗️' },
    maintainability: { name: '可維護性', emoji: '🔧' },
    content: { name: '內容', emoji: '📝' },
    community: { name: '社區', emoji: '👥' },
    security: { name: '安全', emoji: '🔒' },
    compliance: { name: '規範', emoji: '📋' },
  };

  // 過濾出有值的指標
  const metrics = Object.entries(qualityScore.metrics)
    .filter(([_, value]) => value !== undefined)
    .map(([key, value]) => ({
      key,
      name: metricConfig[key]?.name || key,
      emoji: metricConfig[key]?.emoji || '📊',
      value: value as number,
    }));

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">✨</span>
        <h2 className="text-xl font-bold text-gray-900">技能特色</h2>
      </div>

      {/* 6 個指標方框 */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {metrics.map(({ key, name, emoji, value }) => (
          <div
            key={key}
            className={`px-4 py-3 rounded-lg border ${getBadgeColor(value)}`}
          >
            <div className="text-center">
              <div className="text-lg mb-1">{emoji}</div>
              <div className="text-2xl font-bold mb-1">{value}</div>
              <div className="text-xs font-medium">{name}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 詳細說明（可摺疊） */}
      {qualityScore.details && (
        <div className="mt-6">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            <span>{showDetails ? '隱藏詳情' : '顯示詳情'}</span>
            <svg
              className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showDetails && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="prose prose-sm prose-gray max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {qualityScore.details}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
