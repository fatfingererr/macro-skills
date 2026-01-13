import type { BestPractice } from '../../types/skill';

interface BestPracticesSectionProps {
  practices: BestPractice[];
}

export default function BestPracticesSection({ practices }: BestPracticesSectionProps) {
  if (!practices || practices.length === 0) {
    return null;
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-6">
        <h2 className="text-xl font-bold text-green-900">最佳實踐</h2>
      </div>

      <div className="space-y-4">
        {practices.map((practice, index) => (
          <div key={index} className="flex gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <div className="w-5 h-5 rounded-full bg-green-200 flex items-center justify-center">
                <svg className="w-3 h-3 text-green-700" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-green-900 mb-1">{practice.title}</h3>
              {practice.description && (
                <p className="text-sm text-green-700 leading-relaxed">{practice.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
