import type { DataLevel } from '../../types/skill';
import { getDataLevelInfo } from '../../data/categories';

interface BadgeProps {
  type: 'dataLevel' | 'tool' | 'tag';
  value: string;
}

const dataLevelColors: Record<string, string> = {
  'free-nolimit': 'bg-green-100 text-green-800',
  'free-limit': 'bg-yellow-100 text-yellow-800',
  'low-cost': 'bg-blue-100 text-blue-800',
  'high-cost': 'bg-purple-100 text-purple-800',
  'enterprise': 'bg-red-100 text-red-800',
};

export default function Badge({ type, value }: BadgeProps) {
  if (type === 'dataLevel') {
    const dataLevelInfo = getDataLevelInfo(value as DataLevel);
    const colorClass = dataLevelColors[value] || 'bg-gray-100 text-gray-800';
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
        {dataLevelInfo?.name || value}
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
