import { Link } from 'react-router-dom';
import type { Skill, QualityBadge as QualityBadgeType } from '../../types/skill';
import Badge from '../common/Badge';
import Button from '../common/Button';

interface SkillCardProps {
  skill: Skill;
  onInstall?: (skill: Skill) => void;
}

// Badge 配色
const badgeColorMap: Record<QualityBadgeType, string> = {
  '頂級': 'bg-purple-100 text-purple-800 border-purple-300',
  '高級': 'bg-amber-100 text-amber-800 border-amber-300',
  '中高級': 'bg-blue-100 text-blue-700 border-blue-300',
  '中級': 'bg-orange-100 text-orange-800 border-orange-300',
  '初級': 'bg-gray-50 text-gray-600 border-gray-200',
};

// 根據分數推斷 Badge
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

export default function SkillCard({ skill, onInstall }: SkillCardProps) {
  // 取得品質等級
  const qualityBadge: QualityBadgeType = skill.qualityScore
    ? (isValidBadge(skill.qualityScore.badge) ? skill.qualityScore.badge : inferBadgeFromScore(skill.qualityScore.overall))
    : '初級';

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow">
      <Link to={`/skills/${skill.id}`}>
        <div className="flex items-start justify-between mb-3">
          <span className="text-3xl">{skill.emoji}</span>
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${badgeColorMap[qualityBadge]}`}>
            {qualityBadge}技能
          </span>
        </div>

        <h3 className="font-semibold text-gray-900 mb-2 hover:text-primary-600 transition-colors">
          {skill.displayName}
        </h3>

        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {skill.description}
        </p>
      </Link>

      <div className="flex flex-wrap gap-1 mb-4">
        {skill.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} type="tag" value={tag} />
        ))}
      </div>

      <div className="flex items-center justify-end">
        <Button
          size="sm"
          onClick={(e) => {
            e.preventDefault();
            onInstall?.(skill);
          }}
        >
          安裝
        </Button>
      </div>
    </div>
  );
}
