import type { Skill } from '../../types/skill';
import SkillCard from './SkillCard';

interface SkillGridProps {
  skills: Skill[];
  onInstall?: (skill: Skill) => void;
}

export default function SkillGrid({ skills, onInstall }: SkillGridProps) {
  if (skills.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">🔍</div>
        <p className="text-gray-600">找不到符合條件的技能</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {skills.map((skill) => (
        <SkillCard key={skill.id} skill={skill} onInstall={onInstall} />
      ))}
    </div>
  );
}
