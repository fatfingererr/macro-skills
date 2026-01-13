import { Link, useSearchParams } from 'react-router-dom';
import { categories } from '../../data/categories';

interface SidebarProps {
  showOnMobile?: boolean;
}

export default function Sidebar({ showOnMobile = false }: SidebarProps) {
  const [searchParams] = useSearchParams();
  const currentCategory = searchParams.get('category');

  return (
    <aside
      className={`w-32 flex-shrink-0 ${
        showOnMobile ? 'block' : 'hidden lg:block'
      }`}
    >
      <div className="sticky top-20">
        <h3 className="font-semibold text-gray-900 mb-4">分類</h3>
        <nav className="space-y-1">
          <Link
            to="/skills"
            className={`block px-3 py-2 text-sm rounded-lg transition-colors ${
              !currentCategory
                ? 'bg-primary-50 text-primary-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            全部技能
          </Link>
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/skills?category=${category.id}`}
              className={`block px-3 py-2 text-sm rounded-lg transition-colors ${
                currentCategory === category.id
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {category.name}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
