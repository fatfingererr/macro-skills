import type { QualityBadge as QualityBadgeType } from '../../types/skill';

interface BadgeStyle {
  icon: string;
  gradient: string;
  border: string;
  text: string;
  glow: string;
  label: string;
}

interface QualityBadgeProps {
  badge: QualityBadgeType | string;
  overall: number;
  size?: 'sm' | 'md' | 'lg';
}

// 五等級配色方案
const badgeConfig: Record<QualityBadgeType, BadgeStyle> = {
  '頂級': {
    icon: '💎',
    gradient: 'from-purple-100 to-purple-200',
    border: 'border-purple-400',
    text: 'text-purple-800',
    glow: 'shadow-purple-200',
    label: '頂級',
  },
  '高級': {
    icon: '🏆',
    gradient: 'from-amber-100 to-yellow-100',
    border: 'border-amber-400',
    text: 'text-amber-800',
    glow: 'shadow-amber-200',
    label: '高級',
  },
  '中高級': {
    icon: '🥈',
    gradient: 'from-blue-100 to-blue-200',
    border: 'border-blue-400',
    text: 'text-blue-700',
    glow: 'shadow-blue-200',
    label: '中高級',
  },
  '中級': {
    icon: '🥉',
    gradient: 'from-orange-100 to-amber-100',
    border: 'border-orange-400',
    text: 'text-orange-800',
    glow: 'shadow-orange-200',
    label: '中級',
  },
  '初級': {
    icon: '🌱',
    gradient: 'from-gray-50 to-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-600',
    glow: 'shadow-gray-100',
    label: '初級',
  },
};

// 根據分數推斷 Badge（向後相容）
function inferBadgeFromScore(score: number): QualityBadgeType {
  if (score >= 90) return '頂級';
  if (score >= 80) return '高級';
  if (score >= 60) return '中高級';
  if (score >= 40) return '中級';
  return '初級';
}

// 判斷是否為有效的 QualityBadge
function isValidBadge(badge: string): badge is QualityBadgeType {
  return ['頂級', '高級', '中高級', '中級', '初級'].includes(badge);
}

export default function QualityBadge({ badge, overall, size = 'md' }: QualityBadgeProps) {
  // 取得有效的 badge 類型
  const validBadge: QualityBadgeType = isValidBadge(badge) ? badge : inferBadgeFromScore(overall);
  const config = badgeConfig[validBadge];

  // 尺寸配置
  const sizeClasses = {
    sm: {
      container: 'px-3 py-1.5',
      icon: 'text-lg',
      score: 'text-lg font-bold',
      badge: 'text-xs',
      label: 'text-[10px]',
    },
    md: {
      container: 'px-4 py-2',
      icon: 'text-2xl',
      score: 'text-2xl font-bold',
      badge: 'text-sm font-medium',
      label: 'text-xs',
    },
    lg: {
      container: 'px-6 py-3',
      icon: 'text-3xl',
      score: 'text-3xl font-bold',
      badge: 'text-base font-semibold',
      label: 'text-sm',
    },
  };

  const sizeClass = sizeClasses[size];

  return (
    <div
      className={`
        inline-flex items-center gap-2
        bg-gradient-to-r ${config.gradient}
        border-2 ${config.border}
        rounded-xl ${sizeClass.container}
        shadow-md ${config.glow}
        transition-all duration-200
        hover:shadow-lg
      `}
    >
      <span className={sizeClass.icon}>{config.icon}</span>
      <div className="flex flex-col items-end">
        <div className={`${sizeClass.score} ${config.text}`}>
          {overall}
        </div>
        <div className={`${sizeClass.label} ${config.text} opacity-70 tracking-wider`}>
          {config.label}
        </div>
      </div>
    </div>
  );
}

// 導出輔助函式供其他元件使用
export { inferBadgeFromScore, isValidBadge, badgeConfig };
export type { BadgeStyle };
