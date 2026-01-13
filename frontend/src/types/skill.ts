export type DataLevel = 'free-nolimit' | 'free-limit' | 'low-cost' | 'high-cost' | 'enterprise';
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
  dataLevel: DataLevel;
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
