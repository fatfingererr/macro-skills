import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Skill } from '../types/skill';
import { fetchSkills } from '../services/skillService';
import { getCategoryName } from '../data/categories';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import InstallModal from '../components/skills/InstallModal';

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
              Skills
            </Link>
          </li>
          <li className="text-gray-400">/</li>
          <li className="text-gray-900 font-medium">{skill.displayName}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <span className="text-5xl">{skill.emoji}</span>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {skill.displayName}
              </h1>
              <p className="text-gray-600 mb-4">{skill.description}</p>

              <div className="flex flex-wrap items-center gap-2 mb-4">
                <Badge type="risk" value={skill.riskLevel} />
                {skill.tools.map((tool) => (
                  <Badge key={tool} type="tool" value={tool} />
                ))}
                <span className="text-sm text-gray-500">
                  {getCategoryName(skill.category)}
                </span>
              </div>

              <div className="flex flex-wrap gap-1">
                {skill.tags.map((tag) => (
                  <Badge key={tag} type="tag" value={tag} />
                ))}
              </div>
            </div>
          </div>

          <Button onClick={() => setShowInstall(true)}>安裝</Button>
        </div>

        {/* Meta */}
        <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">版本</p>
            <p className="font-medium">{skill.version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">作者</p>
            {skill.authorUrl ? (
              <a
                href={skill.authorUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-primary-600 hover:text-primary-700"
              >
                {skill.author}
              </a>
            ) : (
              <p className="font-medium">{skill.author}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">授權</p>
            <p className="font-medium">{skill.license}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">安裝次數</p>
            <p className="font-medium">{skill.installCount.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="prose prose-gray max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {skill.content}
        </ReactMarkdown>
      </div>

      {/* Install Modal */}
      {showInstall && (
        <InstallModal skill={skill} onClose={() => setShowInstall(false)} />
      )}
    </div>
  );
}
