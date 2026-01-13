import type { Skill, SkillFilters, SortOption } from '../types/skill';

const BASE_URL = import.meta.env.BASE_URL;

export async function fetchSkills(): Promise<Skill[]> {
  const response = await fetch(`${BASE_URL}data/skills.json`);
  if (!response.ok) {
    throw new Error('Failed to fetch skills');
  }
  return response.json();
}

export function filterSkills(skills: Skill[], filters: SkillFilters): Skill[] {
  return skills.filter(skill => {
    if (filters.category && skill.category !== filters.category) {
      return false;
    }
    if (filters.dataLevel && skill.dataLevel !== filters.dataLevel) {
      return false;
    }
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const matchesName = skill.displayName.toLowerCase().includes(searchLower);
      const matchesDesc = skill.description.toLowerCase().includes(searchLower);
      const matchesTags = skill.tags.some(tag =>
        tag.toLowerCase().includes(searchLower)
      );
      if (!matchesName && !matchesDesc && !matchesTags) {
        return false;
      }
    }
    return true;
  });
}

export function sortSkills(skills: Skill[], sortBy: SortOption): Skill[] {
  const sorted = [...skills];
  switch (sortBy) {
    case 'popular':
      return sorted.sort((a, b) => b.installCount - a.installCount);
    case 'recommended':
      return sorted.sort((a, b) => {
        if (a.featured && !b.featured) return -1;
        if (!a.featured && b.featured) return 1;
        return b.installCount - a.installCount;
      });
    case 'recent':
    default:
      return sorted;
  }
}

export function paginateSkills(
  skills: Skill[],
  page: number,
  perPage: number
): { skills: Skill[]; totalPages: number } {
  const start = (page - 1) * perPage;
  const end = start + perPage;
  return {
    skills: skills.slice(start, end),
    totalPages: Math.ceil(skills.length / perPage),
  };
}

export function getFeaturedSkills(skills: Skill[]): Skill[] {
  return skills.filter(s => s.featured);
}

export function getPopularSkills(skills: Skill[], limit = 6): Skill[] {
  return [...skills]
    .sort((a, b) => b.installCount - a.installCount)
    .slice(0, limit);
}

export function generateInstallCommand(skill: Skill): string {
  return '/plugin marketplace add macroskills/marketplace';
}

export function generateMarketplaceInstallCommand(): string {
  return '/plugin marketplace add macroskills/marketplace';
}

export function generateSkillEnableCommand(skillId: string): string {
  return `/plugin marketplace enable macroskills/${skillId}`;
}
