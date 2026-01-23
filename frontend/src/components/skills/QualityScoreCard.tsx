import type { QualityScore, QualityMetrics } from '../../types/skill';
import QualityBadge from './QualityBadge';
import QualityRadarChart from './QualityRadarChart';
import QualityMetricGrid, { isNewMetrics } from './QualityMetricGrid';

interface QualityScoreCardProps {
  qualityScore: QualityScore;
}

export default function QualityScoreCard({ qualityScore }: QualityScoreCardProps) {
  const hasNewMetrics = isNewMetrics(qualityScore.metrics);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      {/* Header: Badge + Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <span className="text-2xl">✨</span>
          <h2 className="text-xl font-bold text-gray-900">技能品質</h2>
        </div>
        <QualityBadge
          badge={qualityScore.badge}
          overall={qualityScore.overall}
          size="md"
        />
      </div>

      {/* Main Content: Radar + Summary (只有新版六維度才顯示雷達圖) */}
      {hasNewMetrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Radar Chart */}
          <div className="flex justify-center items-center p-4 bg-gray-50 rounded-lg">
            <QualityRadarChart
              metrics={qualityScore.metrics as QualityMetrics}
              size={240}
              showLabels={true}
              showScores={true}
            />
          </div>

          {/* Score Summary */}
          <div className="flex flex-col justify-center">
            <div className="text-center md:text-left">
              <div className="text-5xl font-bold text-gray-900 mb-2">
                {qualityScore.overall}
              </div>
              <div className="text-gray-500 mb-4">
                總分（六維度平均）
              </div>

              {/* 維度快速摘要 */}
              <div className="space-y-2">
                {(['problemFit', 'correctness', 'dataGovernance', 'robustness', 'maintainability', 'usability'] as const).map((key) => {
                  const metrics = qualityScore.metrics as QualityMetrics;
                  const score = metrics[key];
                  if (score === undefined) return null;

                  const getColor = (s: number) => {
                    if (s >= 80) return 'bg-green-500';
                    if (s >= 60) return 'bg-yellow-500';
                    return 'bg-orange-500';
                  };

                  return (
                    <div key={key} className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getColor(score)} rounded-full`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8">{score}</span>
                    </div>
                  );
                })}
              </div>

              {qualityScore.evaluatedAt && (
                <div className="text-xs text-gray-400 mt-4">
                  評估日期：{qualityScore.evaluatedAt}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        // 舊版顯示整體分數
        <div className="text-center mb-6">
          <div className="text-5xl font-bold text-gray-900 mb-2">
            {qualityScore.overall}
          </div>
          <div className="text-gray-500">整體分數</div>
        </div>
      )}

      {/* Metric Grid */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          維度評分
        </h3>
        <QualityMetricGrid
          metrics={qualityScore.metrics}
          metricDetails={qualityScore.metricDetails}
        />
      </div>
    </div>
  );
}
