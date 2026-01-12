import { Link } from 'react-router-dom';
import type { Skill } from '../../types/skill';
import Badge from '../common/Badge';
import Button from '../common/Button';

interface SkillCardProps {
  skill: Skill;
  onInstall?: (skill: Skill) => void;
}

export default function SkillCard({ skill, onInstall }: SkillCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow">
      <Link to={`/skills/${skill.id}`}>
        <div className="flex items-start justify-between mb-3">
          <span className="text-3xl">{skill.emoji}</span>
          <Badge type="risk" value={skill.riskLevel} />
        </div>

        <h3 className="font-semibold text-gray-900 mb-2 hover:text-primary-600 transition-colors">
          {skill.displayName}
        </h3>

        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {skill.description}
        </p>
      </Link>

      <div className="flex flex-wrap gap-1 mb-4">
        {skill.tools.map((tool) => (
          <Badge key={tool} type="tool" value={tool} />
        ))}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {skill.installCount.toLocaleString()} 次安裝
        </span>
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
