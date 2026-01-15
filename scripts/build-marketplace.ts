import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { glob } from 'glob';
import { execSync } from 'child_process';
import yaml from 'js-yaml';

interface TestQuestion {
  question: string;
  expectedResult?: string;
  imagePath?: string;
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
  methodology?: string;
  downloadUrl?: string;
}

// manifest.json 的欄位定義（技能元數據）
interface ManifestJson {
  name: string;
  displayName?: string;
  description?: string;
  version?: string;
  author?: string | { name: string };
  license?: string;
  category?: string;
  tags?: string[];
  dataLevel?: string;
}

// skill.yaml 的欄位定義（前端展示專用）
interface SkillYaml {
  displayName?: string;  // 可覆蓋 manifest 的 displayName
  emoji?: string;
  authorUrl?: string;
  tools?: string[];
  featured?: boolean;
  installCount?: number;
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

// 讀取 manifest.json（技能元數據）
function loadManifestJson(skillDir: string): ManifestJson | null {
  const manifestPath = path.join(skillDir, 'manifest.json');
  if (fs.existsSync(manifestPath)) {
    try {
      const content = fs.readFileSync(manifestPath, 'utf-8');
      return JSON.parse(content) as ManifestJson;
    } catch (error) {
      console.warn(`  ⚠ 無法解析 manifest.json: ${error}`);
      return null;
    }
  }
  return null;
}

// 讀取 skill.yaml（前端展示專用）
function loadSkillYaml(skillDir: string): SkillYaml | null {
  const yamlPath = path.join(skillDir, 'skill.yaml');
  if (fs.existsSync(yamlPath)) {
    try {
      const content = fs.readFileSync(yamlPath, 'utf-8');
      return yaml.load(content) as SkillYaml;
    } catch (error) {
      console.warn(`  ⚠ 無法解析 skill.yaml: ${error}`);
      return null;
    }
  }
  return null;
}

// 讀取 methodology.md（原理應用文件）
function loadMethodology(skillDir: string): string | undefined {
  // 優先檢查 references/methodology.md
  const refPath = path.join(skillDir, 'references', 'methodology.md');
  if (fs.existsSync(refPath)) {
    try {
      return fs.readFileSync(refPath, 'utf-8');
    } catch {
      return undefined;
    }
  }
  // 備選：根目錄的 methodology.md
  const rootPath = path.join(skillDir, 'methodology.md');
  if (fs.existsSync(rootPath)) {
    try {
      return fs.readFileSync(rootPath, 'utf-8');
    } catch {
      return undefined;
    }
  }
  return undefined;
}

async function buildMarketplace() {
  const skillsDir = path.join(process.cwd(), 'skills');
  const outputDir = path.join(process.cwd(), 'frontend/public/data');

  // 確保輸出目錄存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 尋找所有 SKILL.md 檔案
  const skillFiles = await glob('skills/*/SKILL.md');
  const skills: Skill[] = [];

  console.log(`找到 ${skillFiles.length} 個技能檔案`);

  for (const file of skillFiles) {
    try {
      const content = fs.readFileSync(file, 'utf-8');
      const { data: mdData, content: body } = matter(content);
      const skillName = path.basename(path.dirname(file));
      const skillDir = path.dirname(file);

      // 讀取 manifest.json（技能元數據）和 skill.yaml（前端展示）
      const manifest = loadManifestJson(skillDir);
      const yamlData = loadSkillYaml(skillDir);
      const methodology = loadMethodology(skillDir);
      const hasManifest = manifest !== null;
      const hasYaml = yamlData !== null;
      const hasMethodology = methodology !== undefined;

      // 從 manifest.json 提取 author（處理 string 或 {name: string} 格式）
      const manifestAuthor = manifest?.author
        ? (typeof manifest.author === 'string' ? manifest.author : manifest.author.name)
        : undefined;

      // 生成目錄結構
      const dirStructure = getDirectoryStructure(skillDir);

      // 取得最新更新日期（優先使用 manifest.json 的時間）
      const manifestPath = path.join(skillDir, 'manifest.json');
      const lastUpdated = hasManifest && fs.existsSync(manifestPath)
        ? getLastCommitDate(manifestPath)
        : getLastCommitDate(file);

      // 數據來源優先級：
      // - 基礎元數據：manifest.json > SKILL.md frontmatter > 預設值
      // - 前端展示：skill.yaml > 預設值
      // - displayName：skill.yaml > manifest.json > SKILL.md name
      const skill: Skill = {
        id: manifest?.name || mdData.name || skillName,
        name: manifest?.name || mdData.name || skillName,
        displayName: yamlData?.displayName || manifest?.displayName || mdData.name || skillName,
        description: manifest?.description || mdData.description || '',
        emoji: yamlData?.emoji || '🛠️',
        version: manifest?.version || 'v1.0.0',
        license: manifest?.license || 'MIT',
        author: manifestAuthor || 'Unknown',
        authorUrl: yamlData?.authorUrl,
        tags: manifest?.tags || [],
        category: manifest?.category || 'other',
        dataLevel: manifest?.dataLevel || 'free-nolimit',
        tools: yamlData?.tools || ['claude-code'],
        featured: yamlData?.featured || false,
        installCount: yamlData?.installCount || 0,
        content: body.trim(),
        path: `skills/${skillName}/SKILL.md`,
        directoryStructure: `${skillName}/\n${dirStructure}`,
        lastUpdated,
        rating: yamlData?.rating || 3,
        testQuestions: yamlData?.testQuestions,
        qualityScore: yamlData?.qualityScore,
        bestPractices: yamlData?.bestPractices,
        pitfalls: yamlData?.pitfalls,
        faq: yamlData?.faq,
        about: yamlData?.about,
        methodology,
        downloadUrl: `downloads/${skillName}-${(manifest?.version || 'v1.0.0').replace(/^v/, '')}.zip`,
      };

      skills.push(skill);
      const sources: string[] = [];
      if (hasManifest) sources.push('manifest');
      if (hasYaml) sources.push('yaml');
      if (hasMethodology) sources.push('method');
      const source = sources.length > 0 ? `(${sources.join('+')})` : '(md)';
      console.log(`✓ 載入: ${skill.displayName} ${source}`);
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

  const indexPath = path.join(process.cwd(), '.claude-plugin/index.json');
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf-8');

  // 3. 同步更新 .claude-plugin/marketplace.json
  const claudePluginPath = path.join(process.cwd(), '.claude-plugin/marketplace.json');
  const existingPluginConfig = JSON.parse(fs.readFileSync(claudePluginPath, 'utf-8'));

  const updatedPluginConfig = {
    ...existingPluginConfig,
    plugins: skills.map(s => ({
      name: s.id,
      description: s.description,
      version: s.version.replace(/^v/, ''), // 移除 v 前綴
      author: {
        name: s.author,
      },
      source: `./skills/${s.id}`,
      category: s.category,
      tags: s.tags.slice(0, 6),
    })),
  };

  fs.writeFileSync(claudePluginPath, JSON.stringify(updatedPluginConfig, null, 2), 'utf-8');

  console.log(`\n✓ 已產生 ${frontendOutput}`);
  console.log(`✓ 已產生 ${indexPath}`);
  console.log(`✓ 已同步 ${claudePluginPath}`);
  console.log(`  共 ${skills.length} 個技能`);
}

buildMarketplace().catch(console.error);
