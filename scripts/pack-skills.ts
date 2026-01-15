import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { glob } from 'glob';

interface ManifestJson {
  name: string;
  version?: string;
}

// 讀取 manifest.json 獲取版本號
function getSkillVersion(skillDir: string): string {
  const manifestPath = path.join(skillDir, 'manifest.json');
  if (fs.existsSync(manifestPath)) {
    try {
      const content = fs.readFileSync(manifestPath, 'utf-8');
      const manifest = JSON.parse(content) as ManifestJson;
      return (manifest.version || 'v1.0.0').replace(/^v/, '');
    } catch {
      return '1.0.0';
    }
  }
  return '1.0.0';
}

// 檢查是否有可用的 zip 命令
function hasZipCommand(): boolean {
  try {
    execSync('where tar', { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

// 使用 tar 創建 zip（Windows 內建支援）
function createZipWithTar(skillDir: string, outputPath: string): boolean {
  try {
    const skillName = path.basename(skillDir);
    const parentDir = path.dirname(skillDir);

    // 使用 tar 創建 zip 格式的壓縮檔
    // Windows 10+ 內建 tar 命令支援 zip 格式
    execSync(
      `tar -a -cf "${outputPath}" -C "${parentDir}" "${skillName}"`,
      { stdio: 'pipe' }
    );
    return true;
  } catch (error) {
    console.error(`  ✗ tar 壓縮失敗: ${error}`);
    return false;
  }
}

// 使用 PowerShell 創建 zip（備選方案）
function createZipWithPowerShell(skillDir: string, outputPath: string): boolean {
  try {
    const psCommand = `Compress-Archive -Path "${skillDir}" -DestinationPath "${outputPath}" -Force`;
    execSync(`powershell -Command "${psCommand}"`, { stdio: 'pipe' });
    return true;
  } catch (error) {
    console.error(`  ✗ PowerShell 壓縮失敗: ${error}`);
    return false;
  }
}

async function packSkills() {
  const skillsDir = path.join(process.cwd(), 'skills');
  const outputDir = path.join(process.cwd(), 'frontend/public/downloads');

  // 確保輸出目錄存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 清除舊的 zip 檔案
  const oldZips = await glob('frontend/public/downloads/*.zip');
  for (const zipFile of oldZips) {
    fs.unlinkSync(zipFile);
  }
  console.log(`已清除 ${oldZips.length} 個舊的 zip 檔案\n`);

  // 找出所有 skill 目錄
  const skillFiles = await glob('skills/*/SKILL.md');
  const skills = skillFiles.map(f => path.dirname(f));

  console.log(`找到 ${skills.length} 個技能待打包\n`);

  let successCount = 0;
  let failCount = 0;

  for (const skillPath of skills) {
    const skillName = path.basename(skillPath);
    const version = getSkillVersion(skillPath);
    const zipFileName = `${skillName}-${version}.zip`;
    const outputPath = path.join(outputDir, zipFileName);

    process.stdout.write(`打包: ${skillName} v${version}... `);

    // 嘗試使用 tar，失敗則用 PowerShell
    let success = createZipWithTar(skillPath, outputPath);
    if (!success) {
      success = createZipWithPowerShell(skillPath, outputPath);
    }

    if (success && fs.existsSync(outputPath)) {
      const stats = fs.statSync(outputPath);
      const sizeKB = (stats.size / 1024).toFixed(1);
      console.log(`✓ ${zipFileName} (${sizeKB} KB)`);
      successCount++;
    } else {
      console.log(`✗ 失敗`);
      failCount++;
    }
  }

  console.log(`\n打包完成:`);
  console.log(`  ✓ 成功: ${successCount}`);
  if (failCount > 0) {
    console.log(`  ✗ 失敗: ${failCount}`);
  }
  console.log(`  輸出目錄: ${outputDir}`);
}

packSkills().catch(console.error);
