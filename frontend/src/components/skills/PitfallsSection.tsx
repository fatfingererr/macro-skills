import type { Pitfall } from '../../types/skill';

interface PitfallsSectionProps {
  pitfalls: Pitfall[];
}

export default function PitfallsSection({ pitfalls }: PitfallsSectionProps) {
  if (!pitfalls || pitfalls.length === 0) {
    return null;
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-6">
        <h2 className="text-xl font-bold text-yellow-900">避免事項</h2>
      </div>

      <div className="space-y-4">
        {pitfalls.map((pitfall, index) => (
          <div key={index} className="flex gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <div className="w-5 h-5 rounded-full bg-yellow-200 flex items-center justify-center">
                <svg className="w-3 h-3 text-yellow-700" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-1">{pitfall.title}</h3>
              {pitfall.description && (
                <p className="text-sm text-yellow-700 leading-relaxed mb-1">{pitfall.description}</p>
              )}
              {pitfall.consequence && (
                <div className="flex gap-2 items-start mt-2">
                  <span className="text-yellow-600 flex-shrink-0">⚠️</span>
                  <p className="text-sm text-yellow-800 leading-relaxed">
                    <span className="font-medium">後果：</span>
                    {pitfall.consequence}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
