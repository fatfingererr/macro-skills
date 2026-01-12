import type { SortOption } from '../../types/skill';

interface SortSelectorProps {
  value: SortOption;
  onChange: (value: SortOption) => void;
}

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'recommended', label: '推薦' },
  { value: 'popular', label: '熱門' },
  { value: 'recent', label: '最新' },
];

export default function SortSelector({ value, onChange }: SortSelectorProps) {
  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-500">排序：</span>
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {sortOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              value === option.value
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
