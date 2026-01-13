import { getDataLevelInfo } from '../../data/categories';
import type { DataLevel } from '../../types/skill';

interface DataLevelCardProps {
  dataLevel: DataLevel;
}

export default function DataLevelCard({ dataLevel }: DataLevelCardProps) {
  const levelInfo = getDataLevelInfo(dataLevel);

  if (!levelInfo) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">🗂️</span>
        <h2 className="text-xl font-bold text-gray-900">數據源</h2>
      </div>

      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 text-4xl">
          {levelInfo.emoji}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{levelInfo.name}</h3>
            <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
              {levelInfo.cost}
            </span>
          </div>
          <p className="text-gray-600">{levelInfo.description}</p>
        </div>
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <span className="font-medium">說明：</span>
          數據源等級代表此技能所需的資料來源成本與取得難度。
        </p>
      </div>
    </div>
  );
}
