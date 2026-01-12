import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { Skill } from '../types/skill';
import { fetchSkills, getFeaturedSkills, getPopularSkills } from '../services/skillService';
import SkillGrid from '../components/skills/SkillGrid';
import InstallModal from '../components/skills/InstallModal';
import Button from '../components/common/Button';

export default function HomePage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [installSkill, setInstallSkill] = useState<Skill | null>(null);

  useEffect(() => {
    fetchSkills()
      .then(setSkills)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const featuredSkills = getFeaturedSkills(skills);
  const popularSkills = getPopularSkills(skills, 6);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Macro Skills
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            投資理財之餘，想刷宏觀研究副本？把技能裝上熱鍵用起來！
          </p>
          <div className="flex justify-center space-x-4">
            <Link to="/skills">
              <Button size="lg">瀏覽技能</Button>
            </Link>
            <Link to="/docs">
              <Button size="lg" variant="outline">
                了解更多
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Skills */}
      {featuredSkills.length > 0 && (
        <section className="py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">精選技能</h2>
              <Link
                to="/skills?featured=true"
                className="text-primary-600 hover:text-primary-700 text-sm font-medium"
              >
                查看全部 →
              </Link>
            </div>
            <SkillGrid skills={featuredSkills} onInstall={setInstallSkill} />
          </div>
        </section>
      )}

      {/* Popular Skills */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">熱門技能</h2>
            <Link
              to="/skills?sort=popular"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              查看全部 →
            </Link>
          </div>
          <SkillGrid skills={popularSkills} onInstall={setInstallSkill} />
        </div>
      </section>

      {/* CTA */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            有好的技能想法？
          </h2>
          <p className="text-gray-600 mb-6">
            歡迎提交你的技能到 Macro Skills
          </p>
          <Link to="/submit">
            <Button>提交技能</Button>
          </Link>
        </div>
      </section>

      {/* Install Modal */}
      {installSkill && (
        <InstallModal
          skill={installSkill}
          onClose={() => setInstallSkill(null)}
        />
      )}
    </div>
  );
}
