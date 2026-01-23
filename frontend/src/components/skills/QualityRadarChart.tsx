import type { QualityMetrics, LegacyQualityMetrics } from '../../types/skill';
import { metricConfigMap } from './QualityMetricCard';

// 六維度順序（順時針方向，從頂部開始）
const METRIC_ORDER: (keyof QualityMetrics)[] = [
  'problemFit',      // 12 點鐘方向
  'correctness',     // 2 點鐘方向
  'dataGovernance',  // 4 點鐘方向
  'robustness',      // 6 點鐘方向
  'maintainability', // 8 點鐘方向
  'usability',       // 10 點鐘方向
];

// 判斷是否為新版六維度
function isNewMetrics(metrics: QualityMetrics | LegacyQualityMetrics): metrics is QualityMetrics {
  return 'problemFit' in metrics || 'correctness' in metrics || 'dataGovernance' in metrics;
}

interface QualityRadarChartProps {
  metrics: QualityMetrics | LegacyQualityMetrics;
  size?: number;
  showLabels?: boolean;
  showScores?: boolean;
  fillColor?: string;
  strokeColor?: string;
}

export default function QualityRadarChart({
  metrics,
  size = 200,
  showLabels = true,
  showScores = true,
  fillColor = 'rgba(59, 130, 246, 0.2)',
  strokeColor = 'rgb(59, 130, 246)',
}: QualityRadarChartProps) {
  // 如果不是新版六維度，不渲染雷達圖
  if (!isNewMetrics(metrics)) {
    return null;
  }

  const centerX = size / 2;
  const centerY = size / 2;
  const radius = size * 0.35; // 主要半徑
  const labelOffset = size * 0.12; // 標籤偏移量

  // 計算某個維度在六邊形上的座標
  const getPoint = (index: number, value: number) => {
    const angle = (Math.PI * 2 * index) / 6 - Math.PI / 2; // 從頂部開始
    const normalizedValue = value / 100;
    const x = centerX + Math.cos(angle) * radius * normalizedValue;
    const y = centerY + Math.sin(angle) * radius * normalizedValue;
    return { x, y };
  };

  // 取得標籤位置
  const getLabelPosition = (index: number) => {
    const angle = (Math.PI * 2 * index) / 6 - Math.PI / 2;
    const x = centerX + Math.cos(angle) * (radius + labelOffset);
    const y = centerY + Math.sin(angle) * (radius + labelOffset);
    return { x, y };
  };

  // 產生六邊形的路徑（用於背景網格）
  const generateHexagonPath = (scale: number) => {
    const points = Array.from({ length: 6 }, (_, i) => {
      const angle = (Math.PI * 2 * i) / 6 - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius * scale;
      const y = centerY + Math.sin(angle) * radius * scale;
      return `${x},${y}`;
    });
    return `M ${points.join(' L ')} Z`;
  };

  // 產生資料多邊形的路徑
  const generateDataPath = () => {
    const points = METRIC_ORDER.map((key, index) => {
      const value = metrics[key] ?? 0;
      const { x, y } = getPoint(index, value);
      return `${x},${y}`;
    });
    return `M ${points.join(' L ')} Z`;
  };

  // 產生從中心到各頂點的線條
  const generateAxisLines = () => {
    return METRIC_ORDER.map((_, index) => {
      const { x, y } = getPoint(index, 100);
      return `M ${centerX},${centerY} L ${x},${y}`;
    });
  };

  // 背景網格層級（20, 40, 60, 80, 100）
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="transition-all duration-300"
    >
      {/* 背景網格 - 同心六邊形 */}
      {gridLevels.map((level, index) => (
        <path
          key={`grid-${index}`}
          d={generateHexagonPath(level)}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="1"
        />
      ))}

      {/* 從中心到各頂點的輔助線 */}
      {generateAxisLines().map((d, index) => (
        <path
          key={`axis-${index}`}
          d={d}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="1"
        />
      ))}

      {/* 資料區域填充 */}
      <path
        d={generateDataPath()}
        fill={fillColor}
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinejoin="round"
      />

      {/* 資料點 */}
      {METRIC_ORDER.map((key, index) => {
        const value = metrics[key] ?? 0;
        const { x, y } = getPoint(index, value);
        return (
          <circle
            key={`point-${key}`}
            cx={x}
            cy={y}
            r={4}
            fill={strokeColor}
            stroke="white"
            strokeWidth="2"
          />
        );
      })}

      {/* 標籤 */}
      {showLabels && METRIC_ORDER.map((key, index) => {
        const config = metricConfigMap[key];
        const value = metrics[key] ?? 0;
        const { x, y } = getLabelPosition(index);

        // 根據位置調整文字對齊
        let textAnchor: 'start' | 'middle' | 'end' = 'middle';
        let dy = 0;

        if (index === 0) {
          // 頂部
          dy = -8;
        } else if (index === 3) {
          // 底部
          dy = 16;
        } else if (index === 1 || index === 2) {
          // 右側
          textAnchor = 'start';
          dy = 4;
        } else {
          // 左側
          textAnchor = 'end';
          dy = 4;
        }

        return (
          <g key={`label-${key}`}>
            <text
              x={x}
              y={y}
              dy={dy}
              textAnchor={textAnchor}
              className="text-xs font-medium fill-gray-600"
              style={{ fontSize: '11px' }}
            >
              {config.icon} {config.shortName}
            </text>
            {showScores && (
              <text
                x={x}
                y={y}
                dy={dy + 14}
                textAnchor={textAnchor}
                className="text-xs font-bold fill-gray-800"
                style={{ fontSize: '11px' }}
              >
                {value}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
