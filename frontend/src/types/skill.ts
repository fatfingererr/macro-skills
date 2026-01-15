export type DataLevel = 'free-nolimit' | 'free-limit' | 'low-cost' | 'high-cost' | 'enterprise';
export type Tool = 'claude-code';

export interface TestQuestion {
  question: string;
  expectedResult?: string;
  imagePath?: string;
}

// 質量評分介面
export interface QualityScore {
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

// 最佳實踐介面
export interface BestPractice {
  title: string;
  description?: string;
}

// 避免事項介面
export interface Pitfall {
  title: string;
  description?: string;
  consequence?: string;
}

// 常見問題介面
export interface FAQ {
  question: string;
  answer: string;
}

// 關於資訊介面
export interface About {
  author: string;
  authorUrl?: string;
  license: string;
  repository?: string;
  branch?: string;
  additionalInfo?: string;
}

export interface Skill {
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
  dataLevel: DataLevel;
  tools: Tool[];
  featured: boolean;
  installCount: number;
  content: string;
  path?: string;
  directoryStructure?: string;
  lastUpdated?: string;
  rating?: number;
  testQuestions?: TestQuestion[];
  qualityScore?: QualityScore;
  bestPractices?: BestPractice[];
  pitfalls?: Pitfall[];
  faq?: FAQ[];
  about?: About;
  methodology?: string;      // 原理應用文件內容
  downloadUrl?: string;      // 技能下載 zip 路徑
}

export interface Category {
  id: string;
  name: string;
  nameEn: string;
}

export interface SkillFilters {
  category?: string;
  search?: string;
  dataLevel?: DataLevel;
}

export type SortOption = 'recent' | 'popular' | 'recommended';

export interface DataLevelInfo {
  id: DataLevel;
  name: string;
  nameEn: string;
  color: string;
  emoji: string;
  cost: string;
  description: string;
}
