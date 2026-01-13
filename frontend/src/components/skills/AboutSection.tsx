import type { About } from '../../types/skill';

interface AboutSectionProps {
  about?: About;
  author: string;
  authorUrl?: string;
  license: string;
  directoryStructure?: string;
}

export default function AboutSection({
  about,
  author,
  authorUrl,
  license,
  directoryStructure,
}: AboutSectionProps) {
  // 使用 about 提供的資料，如果沒有則使用 fallback
  const displayAuthor = about?.author || author;
  const displayAuthorUrl = about?.authorUrl || authorUrl;
  const displayLicense = about?.license || license;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">📄</span>
        <h2 className="text-xl font-bold text-gray-900">關於此技能</h2>
      </div>

      {/* 兩欄布局 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* 作者 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">👤 作者</p>
          {displayAuthorUrl ? (
            <a
              href={displayAuthorUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              {displayAuthor}
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          ) : (
            <p className="text-sm font-medium text-gray-900">{displayAuthor}</p>
          )}
        </div>

        {/* 授權 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">📜 授權</p>
          <p className="text-sm font-medium text-gray-900">{displayLicense}</p>
        </div>

        {/* 程式碼 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">🔗 程式碼</p>
          {about?.repository ? (
            <a
              href={about.repository}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1 break-all"
            >
              GitHub
              <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          ) : (
            <p className="text-sm text-gray-400">未提供</p>
          )}
        </div>

        {/* 分支 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">🌿 分支</p>
          <p className="text-sm font-medium text-gray-900">{about?.branch || 'main'}</p>
        </div>
      </div>

      {/* 目錄結構 */}
      {directoryStructure && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>📁</span>
            目錄結構
          </h3>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-100 font-mono whitespace-pre">
              {directoryStructure}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
