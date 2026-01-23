import { useState } from 'react';
import type { QualityMetrics, MetricDetail } from '../../types/skill';

// 維度配置
interface MetricConfig {
  name: string;
  shortName: string;
  icon: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  progressColor: string;
}

export const metricConfigMap: Record<keyof QualityMetrics, MetricConfig> = {
  problemFit: {
    name: '任務適配度',
    shortName: '適配',
    icon: '🎯',
    description: '問題定義與工作流閉環',
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    progressColor: 'bg-blue-500',
  },
  correctness: {
    name: '正確性',
    shortName: '正確',
    icon: '✅',
    description: '方法論可重現與驗證',
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    progressColor: 'bg-green-500',
  },
  dataGovernance: {
    name: '資料治理',
    shortName: '資料',
    icon: '📊',
    description: '來源品質與可追溯性',
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
    progressColor: 'bg-purple-500',
  },
  robustness: {
    name: '穩健性',
    shortName: '穩健',
    icon: '🛡️',
    description: '失敗模式與容錯處理',
    color: 'orange',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-700',
    progressColor: 'bg-orange-500',
  },
  maintainability: {
    name: '可維護性',
    shortName: '維護',
    icon: '🔧',
    description: '版本管理與模板穩定',
    color: 'gray',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    textColor: 'text-gray-700',
    progressColor: 'bg-gray-500',
  },
  usability: {
    name: '輸出可用性',
    shortName: '可用',
    icon: '📋',
    description: '決策支援與歷史對照',
    color: 'teal',
    bgColor: 'bg-teal-50',
    borderColor: 'border-teal-200',
    textColor: 'text-teal-700',
    progressColor: 'bg-teal-500',
  },
};

// 根據分數取得等級文字
function getScoreLevel(score: number): { text: string; color: string } {
  if (score >= 90) return { text: '優秀', color: 'text-emerald-600' };
  if (score >= 80) return { text: '良好', color: 'text-green-600' };
  if (score >= 60) return { text: '中等', color: 'text-yellow-600' };
  if (score >= 40) return { text: '待改進', color: 'text-orange-600' };
  return { text: '需加強', color: 'text-red-600' };
}

interface QualityMetricCardProps {
  metricKey: keyof QualityMetrics;
  score: number;
  detail?: MetricDetail;
  compact?: boolean;
}

export default function QualityMetricCard({
  metricKey,
  score,
  detail,
  compact = false,
}: QualityMetricCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = metricConfigMap[metricKey];
  const level = getScoreLevel(score);
  const hasDetail = detail && (detail.strengths?.length > 0 || (detail.improvements && detail.improvements.length > 0));

  if (compact) {
    // 精簡版本，用於小螢幕或緊湊佈局
    return (
      <div
        className={`
          px-3 py-2 rounded-lg border
          ${config.bgColor} ${config.borderColor}
          transition-all duration-200
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-base">{config.icon}</span>
            <span className={`text-sm font-medium ${config.textColor}`}>
              {config.shortName}
            </span>
          </div>
          <span className={`text-lg font-bold ${config.textColor}`}>
            {score}
          </span>
        </div>
        {/* 進度條 */}
        <div className="mt-1.5 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${config.progressColor} rounded-full transition-all duration-300`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        rounded-lg border overflow-hidden
        ${config.bgColor} ${config.borderColor}
        transition-all duration-200
        ${hasDetail ? 'cursor-pointer hover:shadow-md' : ''}
      `}
      onClick={() => hasDetail && setExpanded(!expanded)}
    >
      {/* 主內容 */}
      <div className="px-4 py-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">{config.icon}</span>
            <div>
              <h4 className={`font-semibold ${config.textColor}`}>
                {config.name}
              </h4>
              <p className="text-xs text-gray-500 mt-0.5">
                {config.description}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${config.textColor}`}>
              {score}
            </div>
            <div className={`text-xs font-medium ${level.color}`}>
              {level.text}
            </div>
          </div>
        </div>

        {/* 進度條 */}
        <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${config.progressColor} rounded-full transition-all duration-300`}
            style={{ width: `${score}%` }}
          />
        </div>

        {/* 展開提示 */}
        {hasDetail && (
          <div className="mt-2 flex items-center justify-end">
            <span className="text-xs text-gray-400 flex items-center gap-1">
              {expanded ? '收合詳情' : '展開詳情'}
              <svg
                className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          </div>
        )}
      </div>

      {/* 展開後的詳情 */}
      {expanded && hasDetail && detail && (
        <div className="px-4 py-3 bg-white border-t border-gray-100">
          {/* 優點清單 */}
          {detail.strengths && detail.strengths.length > 0 && (
            <div className="mb-3">
              <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                優點
              </h5>
              <ul className="space-y-1">
                {detail.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 待改進清單 */}
          {detail.improvements && detail.improvements.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                待改進
              </h5>
              <ul className="space-y-1">
                {detail.improvements.map((improvement, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="text-amber-500 mt-0.5">!</span>
                    <span>{improvement}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export { getScoreLevel };
