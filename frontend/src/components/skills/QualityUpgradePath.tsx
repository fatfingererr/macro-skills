import type { QualityBadge as QualityBadgeType, UpgradeNote, QualityMetrics } from '../../types/skill';
import { badgeConfig, isValidBadge } from './QualityBadge';
import { metricConfigMap } from './QualityMetricCard';

interface QualityUpgradePathProps {
  currentBadge: QualityBadgeType | string;
  upgradeNotes?: UpgradeNote;
}

// 計算進度百分比
function calculateProgress(current: number, target: number): number {
  if (target === 0) return 100;
  return Math.min(100, Math.round((current / target) * 100));
}

export default function QualityUpgradePath({
  currentBadge,
  upgradeNotes,
}: QualityUpgradePathProps) {
  // 驗證並轉換 badge
  const validCurrentBadge: QualityBadgeType = isValidBadge(currentBadge) ? currentBadge : '初級';

  // 如果沒有升級建議或已經是頂級等級，顯示祝賀訊息
  if (!upgradeNotes || validCurrentBadge === '頂級') {
    return (
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 border border-slate-200 rounded-lg p-6 text-center">
        <div className="text-4xl mb-3">🎉</div>
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          {validCurrentBadge === '頂級' ? '已達最高等級!' : '恭喜!'}
        </h3>
        <p className="text-sm text-slate-600">
          {validCurrentBadge === '頂級'
            ? '此技能已達到頂級，品質卓越。'
            : '目前無升級建議，繼續保持良好品質。'
          }
        </p>
      </div>
    );
  }

  const targetBadge = upgradeNotes.targetBadge;
  const validTargetBadge: QualityBadgeType = isValidBadge(targetBadge) ? targetBadge : '高級';

  const currentConfig = badgeConfig[validCurrentBadge];
  const targetConfig = badgeConfig[validTargetBadge];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* 標題區域 */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-xl">📈</span>
        <h3 className="text-lg font-bold text-gray-900">升級路徑</h3>
      </div>

      {/* Badge 進度指示器 */}
      <div className="flex items-center justify-center gap-4 mb-8">
        {/* 當前等級 */}
        <div className="flex flex-col items-center">
          <div
            className={`
              w-16 h-16 rounded-full flex items-center justify-center
              bg-gradient-to-br ${currentConfig.gradient}
              border-2 ${currentConfig.border}
              shadow-md
            `}
          >
            <span className="text-2xl">{currentConfig.icon}</span>
          </div>
          <span className={`mt-2 text-sm font-semibold ${currentConfig.text}`}>
            {validCurrentBadge}
          </span>
          <span className="text-xs text-gray-500">目前</span>
        </div>

        {/* 箭頭 */}
        <div className="flex items-center">
          <div className="w-8 h-0.5 bg-gray-300"></div>
          <svg
            className="w-6 h-6 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <div className="w-8 h-0.5 bg-gray-300"></div>
        </div>

        {/* 目標等級 */}
        <div className="flex flex-col items-center">
          <div
            className={`
              w-16 h-16 rounded-full flex items-center justify-center
              bg-gradient-to-br ${targetConfig.gradient}
              border-2 ${targetConfig.border}
              shadow-md
              ring-2 ring-offset-2 ring-amber-300
            `}
          >
            <span className="text-2xl">{targetConfig.icon}</span>
          </div>
          <span className={`mt-2 text-sm font-semibold ${targetConfig.text}`}>
            {validTargetBadge}
          </span>
          <span className="text-xs text-gray-500">目標</span>
        </div>
      </div>

      {/* 升級需求清單 */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
          升級需求
        </h4>

        {upgradeNotes.requirements.map((req, index) => {
          const metricKey = req.metric as keyof QualityMetrics;
          const config = metricConfigMap[metricKey];
          const progress = calculateProgress(req.currentScore, req.targetScore);
          const gap = req.targetScore - req.currentScore;

          return (
            <div
              key={index}
              className="bg-gray-50 rounded-lg p-4 border border-gray-100"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{config?.icon || '📊'}</span>
                  <div>
                    <h5 className="font-medium text-gray-900">
                      {config?.name || metricKey}
                    </h5>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-500">
                        {req.currentScore}
                      </span>
                      <span className="text-gray-400">→</span>
                      <span className="font-semibold text-amber-600">
                        {req.targetScore}
                      </span>
                      <span className="text-xs text-gray-400">
                        (+{gap})
                      </span>
                    </div>
                  </div>
                </div>

                {/* 進度百分比 */}
                <div className="text-right">
                  <span className={`text-lg font-bold ${progress >= 100 ? 'text-green-600' : 'text-amber-600'}`}>
                    {progress}%
                  </span>
                </div>
              </div>

              {/* 進度條 */}
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    progress >= 100 ? 'bg-green-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* 建議 */}
              <div className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">💡</span>
                <p className="text-sm text-gray-600">{req.suggestion}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* 總結提示 */}
      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <span className="font-semibold">提示：</span>
          完成以上 {upgradeNotes.requirements.length} 項改進後，
          即可從 <span className="font-semibold">{validCurrentBadge}</span> 升級至{' '}
          <span className="font-semibold">{validTargetBadge}</span> 等級。
        </p>
      </div>
    </div>
  );
}
