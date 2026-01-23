import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Skill } from '../types/skill';
import { fetchSkills } from '../services/skillService';
import { getCategoryName } from '../data/categories';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import InstallModal from '../components/skills/InstallModal';
import InstallGuide from '../components/skills/InstallGuide';
import TestQuestionsSection from '../components/skills/TestQuestionsSection';
import DataLevelCard from '../components/skills/DataLevelCard';
import QualityScoreCard from '../components/skills/QualityScoreCard';
import BestPracticesSection from '../components/skills/BestPracticesSection';
import PitfallsSection from '../components/skills/PitfallsSection';
import FAQSection from '../components/skills/FAQSection';
import AboutSection from '../components/skills/AboutSection';
import MethodologySection from '../components/skills/MethodologySection';

export default function SkillDetailPage() {
  const { skillId } = useParams<{ skillId: string }>();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    fetchSkills()
      .then((skills) => {
        const found = skills.find((s) => s.id === skillId);
        setSkill(found || null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skillId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  if (!skill) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="text-4xl mb-4">😕</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">找不到技能</h1>
        <p className="text-gray-600 mb-6">
          此技能可能已被移除或網址有誤
        </p>
        <Link to="/skills">
          <Button>返回技能列表</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <ol className="flex items-center space-x-2 text-sm">
          <li>
            <Link to="/skills" className="text-gray-500 hover:text-gray-700">
              技能
            </Link>
          </li>
          <li className="text-gray-400">/</li>
          <li className="text-gray-900 font-medium">{skill.displayName}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start space-x-4 max-w-[80%]">
            <span className="text-5xl flex-shrink-0 mt-8">{skill.emoji}</span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                {getCategoryName(skill.category)}
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {skill.displayName}
              </h1>
              <p className="text-gray-600 mb-4">{skill.description}</p>

              <div className="flex flex-wrap items-center gap-2 mb-4">
                <small>數據源需求 :</small><Badge type="dataLevel" value={skill.dataLevel} />
              </div>

              <div className="flex flex-wrap gap-1">
                {skill.tags.map((tag) => (
                  <Badge key={tag} type="tag" value={tag} />
                ))}
              </div>
            </div>
          </div>

          <Button className="flex-shrink-0" onClick={() => setShowInstall(true)}>安裝</Button>
        </div>

        {/* Meta */}
        <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">版本</p>
            <p className="font-medium">{skill.version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">日期</p>
            <p className="font-medium">{skill.lastUpdated || '未知'}</p>
          </div>
          <div className="flex items-center gap-2">
            {skill.downloadUrl ? (
              <a
                href={skill.downloadUrl}
                download
                className="inline-flex items-center gap-1 px-3 py-1 bg-blue-600 text-white text-md font-medium rounded-lg hover:bg-primary-700 transition-colors"
              >
                下載壓縮檔 (.zip)
              </a>
            ) : (
              <span className="text-gray-400 text-sm">暫無</span>
            )}
          </div>
        </div>
      </div>

      {/* Install Guide */}
      <div className="mt-8">
        <InstallGuide skillId={skill.id} />
      </div>

      {/* Test Questions */}
      {skill.testQuestions && skill.testQuestions.length > 0 && (
        <div className="mt-8">
          <TestQuestionsSection questions={skill.testQuestions} />
        </div>
      )}

      {/* Methodology / 原理應用 */}
      {skill.methodology && (
        <div className="mt-8">
          <MethodologySection methodology={skill.methodology} />
        </div>
      )}

      {/* Best Practices & Pitfalls - 並排兩欄 */}
      {((skill.bestPractices && skill.bestPractices.length > 0) ||
        (skill.pitfalls && skill.pitfalls.length > 0)) && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            {skill.bestPractices && skill.bestPractices.length > 0 && (
              <BestPracticesSection practices={skill.bestPractices} />
            )}
            {skill.pitfalls && skill.pitfalls.length > 0 && (
              <PitfallsSection pitfalls={skill.pitfalls} />
            )}
          </div>
        )}

      {/* FAQ */}
      {skill.faq && skill.faq.length > 0 && (
        <div className="mt-8">
          <FAQSection faqs={skill.faq} />
        </div>
      )}

      {/* Data Level Info */}
      <div className="mt-8">
        <DataLevelCard dataLevel={skill.dataLevel} />
      </div>

      {/* Quality Score */}
      {skill.qualityScore && (
        <div className="mt-8">
          <QualityScoreCard qualityScore={skill.qualityScore} />
        </div>
      )}

      {/* About */}
      <div className="mt-8">
        <AboutSection
          about={skill.about}
          author={skill.author}
          authorUrl={skill.authorUrl}
          license={skill.license}
          directoryStructure={skill.directoryStructure}
        />
      </div>

      {/* Install Modal */}
      {showInstall && (
        <InstallModal skill={skill} onClose={() => setShowInstall(false)} />
      )}
    </div>
  );
}
