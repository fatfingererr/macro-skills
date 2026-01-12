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
  riskLevel: string;
  tools: string[];
  featured: boolean;
  installCount: number;
  content: string;
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

      const skill: Skill = {
        id: data.name,
        name: data.name,
        displayName: data.displayName || data.name,
        description: data.description || '',
        emoji: data.emoji || '📦',
        version: data.version || 'v1.0.0',
        license: data.license || 'MIT',
        author: data.author || 'Unknown',
        authorUrl: data.authorUrl,
        tags: data.tags || [],
        category: data.category || 'other',
        riskLevel: data.riskLevel || 'safe',
        tools: data.tools || ['claude-code'],
        featured: data.featured || false,
        installCount: data.installCount || 0,
        content: body.trim(),
      };

      skills.push(skill);
      console.log(`✓ 載入: ${skill.displayName}`);
    } catch (error) {
      console.error(`✗ 錯誤處理 ${file}:`, error);
    }
  }

  // 按安裝次數排序
  skills.sort((a, b) => b.installCount - a.installCount);

  // 寫入 skills.json
  const outputPath = path.join(outputDir, 'skills.json');
  fs.writeFileSync(outputPath, JSON.stringify(skills, null, 2), 'utf-8');

  console.log(`\n✓ 已產生 ${outputPath}`);
  console.log(`  共 ${skills.length} 個技能`);
}

buildMarketplace().catch(console.error);
