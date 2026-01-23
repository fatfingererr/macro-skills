import type { QualityMetrics, MetricDetail, LegacyQualityMetrics } from '../../types/skill';
import QualityMetricCard from './QualityMetricCard';

// 新六維度的鍵值順序
const NEW_METRIC_KEYS: (keyof QualityMetrics)[] = [
  'problemFit',
  'correctness',
  'dataGovernance',
  'robustness',
  'maintainability',
  'usability',
];

// 舊維度的鍵值
const LEGACY_METRIC_KEYS = [
  'architecture',
  'maintainability',
  'content',
  'community',
  'security',
  'compliance',
];

// 舊維度配置
const legacyMetricConfigMap: Record<string, { name: string; icon: string }> = {
  architecture: { name: '架構', icon: '🏗️' },
  maintainability: { name: '可維護性', icon: '🔧' },
  content: { name: '內容', icon: '📝' },
  community: { name: '社區', icon: '👥' },
  security: { name: '安全', icon: '🔒' },
  compliance: { name: '規範', icon: '📋' },
};

// 判斷是否為新版六維度
function isNewMetrics(metrics: QualityMetrics | LegacyQualityMetrics): metrics is QualityMetrics {
  return 'problemFit' in metrics || 'correctness' in metrics || 'dataGovernance' in metrics;
}

interface QualityMetricGridProps {
  metrics: QualityMetrics | LegacyQualityMetrics;
  metricDetails?: Record<keyof QualityMetrics, MetricDetail>;
  compact?: boolean;
}

export default function QualityMetricGrid({
  metrics,
  metricDetails,
  compact = false,
}: QualityMetricGridProps) {
  const isNew = isNewMetrics(metrics);

  if (isNew) {
    // 新版六維度佈局
    return (
      <div
        className={`
          grid gap-4
          ${compact
            ? 'grid-cols-2 sm:grid-cols-3'
            : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
          }
        `}
      >
        {NEW_METRIC_KEYS.map((key) => {
          const score = metrics[key];
          if (score === undefined) return null;

          return (
            <QualityMetricCard
              key={key}
              metricKey={key}
              score={score}
              detail={metricDetails?.[key]}
              compact={compact}
            />
          );
        })}
      </div>
    );
  }

  // 舊版維度佈局（向後相容）
  const legacyMetrics = metrics as LegacyQualityMetrics;
  const validMetrics = LEGACY_METRIC_KEYS.filter(
    (key) => legacyMetrics[key as keyof LegacyQualityMetrics] !== undefined
  );

  // 根據分數決定徽章顏色（舊版邏輯）
  const getBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (score >= 60) return 'bg-gray-100 text-gray-800 border-gray-300';
    return 'bg-orange-100 text-orange-800 border-orange-300';
  };

  return (
    <div
      className={`
        grid gap-4
        ${compact
          ? 'grid-cols-2 sm:grid-cols-3'
          : 'grid-cols-2 md:grid-cols-3'
        }
      `}
    >
      {validMetrics.map((key) => {
        const score = legacyMetrics[key as keyof LegacyQualityMetrics];
        if (score === undefined) return null;

        const config = legacyMetricConfigMap[key];

        return (
          <div
            key={key}
            className={`px-4 py-3 rounded-lg border ${getBadgeColor(score)}`}
          >
            <div className="text-center">
              <div className="text-lg mb-1">{config.icon}</div>
              <div className="text-2xl font-bold mb-1">{score}</div>
              <div className="text-xs font-medium">{config.name}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export { isNewMetrics, NEW_METRIC_KEYS, LEGACY_METRIC_KEYS };
