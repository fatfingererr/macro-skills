import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { glob } from 'glob';

interface Skill {
  id: string;
  name: string;
  displayName: string;
  description: string;
  emoji: string;
  version: string;
  license: string;
  author: string;
  authorUrl?: string;
  tags: string[];
  category: string;
  dataLevel: string;
  tools: string[];
  featured: boolean;
  installCount: number;
  content: string;
  path: string;
}

async function buildMarketplace() {
  const skillsDir = path.join(process.cwd(), 'marketplace/skills');
  const outputDir = path.join(process.cwd(), 'frontend/public/data');

  // 確保輸出目錄存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 尋找所有 SKILL.md 檔案
  const skillFiles = await glob('marketplace/skills/*/SKILL.md');
  const skills: Skill[] = [];

  console.log(`找到 ${skillFiles.length} 個技能檔案`);

  for (const file of skillFiles) {
    try {
      const content = fs.readFileSync(file, 'utf-8');
      const { data, content: body } = matter(content);
      const skillName = path.basename(path.dirname(file));

      const skill: Skill = {
        id: data.name || skillName,
        name: data.name || skillName,
        displayName: data.displayName || data.name,
        description: data.description || '',
        emoji: data.emoji || '📦',
        version: data.version || 'v1.0.0',
        license: data.license || 'MIT',
        author: data.author || 'Unknown',
        authorUrl: data.authorUrl,
        tags: data.tags || [],
        category: data.category || 'other',
        dataLevel: data.dataLevel || 'free-nolimit',
        tools: data.tools || ['claude-code'],
        featured: data.featured || false,
        installCount: data.installCount || 0,
        content: body.trim(),
        path: `skills/${skillName}/SKILL.md`,
      };

      skills.push(skill);
      console.log(`✓ 載入: ${skill.displayName}`);
    } catch (error) {
      console.error(`✗ 錯誤處理 ${file}:`, error);
    }
  }

  // 排序：精選優先，然後按安裝次數
  skills.sort((a, b) => {
    if (a.featured !== b.featured) return b.featured ? 1 : -1;
    return b.installCount - a.installCount;
  });

  // 1. 生成前端用的 skills.json
  const frontendOutput = path.join(outputDir, 'skills.json');
  fs.writeFileSync(frontendOutput, JSON.stringify(skills, null, 2), 'utf-8');

  // 2. 生成 marketplace/index.json（技能索引）
  const index = {
    version: '1.0.0',
    lastUpdated: new Date().toISOString(),
    totalSkills: skills.length,
    skills: skills.map(s => ({
      id: s.id,
      displayName: s.displayName,
      description: s.description,
      emoji: s.emoji,
      version: s.version,
      author: s.author,
      category: s.category,
      dataLevel: s.dataLevel,
      tags: s.tags.slice(0, 5),
      featured: s.featured,
      path: s.path,
    })),
  };

  const indexPath = path.join(process.cwd(), 'marketplace/index.json');
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf-8');

  console.log(`\n✓ 已產生 ${frontendOutput}`);
  console.log(`✓ 已產生 ${indexPath}`);
  console.log(`  共 ${skills.length} 個技能`);
}

buildMarketplace().catch(console.error);
