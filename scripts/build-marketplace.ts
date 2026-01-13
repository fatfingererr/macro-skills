import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { glob } from 'glob';
import { execSync } from 'child_process';

interface TestQuestion {
  question: string;
  expectedResult?: string;
}

interface QualityScore {
  overall: number;
  badge: string;
  metrics: {
    architecture?: number;
    maintainability?: number;
    content?: number;
    community?: number;
    security?: number;
    compliance?: number;
  };
  details?: string;
}

interface BestPractice {
  title: string;
  description?: string;
}

interface Pitfall {
  title: string;
  description?: string;
  consequence?: string;
}

interface FAQ {
  question: string;
  answer: string;
}

interface About {
  author: string;
  authorUrl?: string;
  license: string;
  repository?: string;
  branch?: string;
  additionalInfo?: string;
}

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
  directoryStructure?: string;
  lastUpdated?: string;
  rating?: number;
  testQuestions?: TestQuestion[];
  qualityScore?: QualityScore;
  bestPractices?: BestPractice[];
  pitfalls?: Pitfall[];
  faq?: FAQ[];
  about?: About;
}

// 取得檔案最新 commit 日期
function getLastCommitDate(filePath: string): string | undefined {
  try {
    const result = execSync(`git log -1 --format=%ci "${filePath}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
    if (result) {
      // 轉換為 ISO 日期格式
      const date = new Date(result);
      return date.toISOString().split('T')[0]; // 只取日期部分 YYYY-MM-DD
    }
  } catch {
    // 如果 git 命令失敗，使用檔案修改時間
    try {
      const stats = fs.statSync(filePath);
      return stats.mtime.toISOString().split('T')[0];
    } catch {
      return undefined;
    }
  }
  return undefined;
}

// 生成目錄結構的函式
function getDirectoryStructure(dirPath: string, prefix: string = ''): string {
  const items = fs.readdirSync(dirPath, { withFileTypes: true });
  const lines: string[] = [];

  items.forEach((item, index) => {
    const isLast = index === items.length - 1;
    const connector = isLast ? '└── ' : '├── ';
    const extension = isLast ? '    ' : '│   ';

    lines.push(`${prefix}${connector}${item.name}`);

    if (item.isDirectory()) {
      const subPath = path.join(dirPath, item.name);
      const subLines = getDirectoryStructure(subPath, `${prefix}${extension}`);
      if (subLines) {
        lines.push(subLines);
      }
    }
  });

  return lines.join('\n');
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
      const skillDir = path.dirname(file);

      // 生成目錄結構
      const dirStructure = getDirectoryStructure(skillDir);

      // 取得最新更新日期
      const lastUpdated = getLastCommitDate(file);

      const skill: Skill = {
        id: data.name || skillName,
        name: data.name || skillName,
        displayName: data.displayName || data.name,
        description: data.description || '',
        emoji: data.emoji || '🛠️',
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
        directoryStructure: `${skillName}/\n${dirStructure}`,
        lastUpdated,
        rating: data.rating || 3,
        testQuestions: data.testQuestions,
        qualityScore: data.qualityScore,
        bestPractices: data.bestPractices,
        pitfalls: data.pitfalls,
        faq: data.faq,
        about: data.about,
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
