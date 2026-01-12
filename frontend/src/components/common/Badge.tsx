import type { RiskLevel } from '../../types/skill';
import { getRiskLevelInfo } from '../../data/categories';

interface BadgeProps {
  type: 'risk' | 'tool' | 'tag';
  value: string;
}

const riskColors: Record<string, string> = {
  safe: 'bg-green-100 text-green-800',
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export default function Badge({ type, value }: BadgeProps) {
  if (type === 'risk') {
    const riskInfo = getRiskLevelInfo(value as RiskLevel);
    const colorClass = riskColors[value] || 'bg-gray-100 text-gray-800';
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
        {riskInfo?.name || value}
      </span>
    );
  }

  if (type === 'tool') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
        {value === 'claude-code' ? 'Claude Code' : value}
      </span>
    );
  }

  // tag
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
      {value}
    </span>
  );
}
