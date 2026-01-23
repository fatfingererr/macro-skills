export type DataLevel = 'free-nolimit' | 'free-limit' | 'low-cost' | 'high-cost' | 'enterprise';
export type Tool = 'claude-code';

export interface TestQuestion {
  question: string;
  expectedResult?: string;
  imagePath?: string;
}

// 新六維度指標
export interface QualityMetrics {
  problemFit: number;       // 任務適配度與問題定義（0-100）
  correctness: number;      // 正確性與可驗證性（0-100）
  dataGovernance: number;   // 資料來源品質與資料治理（0-100）
  robustness: number;       // 穩健性與容錯（0-100）
  maintainability: number;  // 可重現性與可維護性（0-100）
  usability: number;        // 輸出可用性與決策支援（0-100）
}

// Badge 等級
export type QualityBadge = '頂級' | '高級' | '中高級' | '中級' | '初級';

// 單一維度詳情
export interface MetricDetail {
  score: number;
  strengths: string[];      // 優點
  improvements?: string[];  // 待改進項目（可選）
}

// 升級建議
export interface UpgradeNote {
  targetBadge: QualityBadge;
  requirements: {
    metric: keyof QualityMetrics;
    currentScore: number;
    targetScore: number;
    suggestion: string;
  }[];
}

// 舊版指標（向後相容）
export interface LegacyQualityMetrics {
  architecture?: number;
  maintainability?: number;
  content?: number;
  community?: number;
  security?: number;
  compliance?: number;
}

// 質量評分介面
export interface QualityScore {
  overall: number;                    // 整體分數（六維度平均）
  badge: QualityBadge | string;       // 等級徽章（支援新舊格式）
  metrics: QualityMetrics | LegacyQualityMetrics; // 六維度分數（支援新舊格式）
  details?: string;                   // Markdown 格式的詳細說明
  metricDetails?: Record<keyof QualityMetrics, MetricDetail>;  // 各維度詳情
  upgradeNotes?: UpgradeNote;         // 升級建議
  evaluatedAt?: string;               // 評估日期 (ISO 8601)
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
