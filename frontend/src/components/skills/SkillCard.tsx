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
          <div className="flex items-center gap-1 text-xs text-gray-600">
            <span>數據：</span>
            <Badge type="dataLevel" value={skill.dataLevel} />
          </div>
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
