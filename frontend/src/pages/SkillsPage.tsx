import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Skill, SortOption } from '../types/skill';
import {
  fetchSkills,
  filterSkills,
  sortSkills,
  paginateSkills,
} from '../services/skillService';
import Sidebar from '../components/layout/Sidebar';
import SkillGrid from '../components/skills/SkillGrid';
import SortSelector from '../components/skills/SortSelector';
import SearchInput from '../components/common/SearchInput';
import Pagination from '../components/common/Pagination';
import InstallModal from '../components/skills/InstallModal';

const ITEMS_PER_PAGE = 9;

export default function SkillsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [installSkill, setInstallSkill] = useState<Skill | null>(null);

  // URL params
  const category = searchParams.get('category') || '';
  const search = searchParams.get('search') || '';
  const sort = (searchParams.get('sort') as SortOption) || 'recommended';
  const page = parseInt(searchParams.get('page') || '1', 10);

  useEffect(() => {
    fetchSkills()
      .then(setAllSkills)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Filter and sort
  const filteredSkills = useMemo(() => {
    const filtered = filterSkills(allSkills, { category, search });
    return sortSkills(filtered, sort);
  }, [allSkills, category, search, sort]);

  // Paginate
  const { skills: paginatedSkills, totalPages } = useMemo(() => {
    return paginateSkills(filteredSkills, page, ITEMS_PER_PAGE);
  }, [filteredSkills, page]);

  const handleSearchChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set('search', value);
    } else {
      newParams.delete('search');
    }
    newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handleSortChange = (value: SortOption) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('sort', value);
    newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', String(newPage));
    setSearchParams(newParams);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex gap-8">
        {/* Sidebar */}
        <Sidebar />

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div className="flex-1 max-w-md">
              <SearchInput value={search} onChange={handleSearchChange} />
            </div>
            <SortSelector value={sort} onChange={handleSortChange} />
          </div>

          {/* Results count */}
          <p className="text-sm text-gray-500 mb-4">
            找到 {filteredSkills.length} 個技能
          </p>

          {/* Skills grid */}
          <SkillGrid skills={paginatedSkills} onInstall={setInstallSkill} />

          {/* Pagination */}
          <div className="mt-8">
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </div>
        </div>
      </div>

      {/* Install Modal */}
      {installSkill && (
        <InstallModal
          skill={installSkill}
          onClose={() => setInstallSkill(null)}
        />
      )}
    </div>
  );
}
