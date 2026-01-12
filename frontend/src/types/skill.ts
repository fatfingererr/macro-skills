export type RiskLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical';
export type Tool = 'claude-code';

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
  riskLevel: RiskLevel;
  tools: Tool[];
  featured: boolean;
  installCount: number;
  content: string;
}

export interface Category {
  id: string;
  name: string;
  nameEn: string;
}

export interface SkillFilters {
  category?: string;
  search?: string;
  riskLevel?: RiskLevel;
}

export type SortOption = 'recent' | 'popular' | 'recommended';

export interface RiskLevelInfo {
  id: RiskLevel;
  name: string;
  color: string;
}
