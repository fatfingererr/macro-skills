import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MethodologySectionProps {
  methodology: string;
}

export default function MethodologySection({ methodology }: MethodologySectionProps) {
  const [expanded, setExpanded] = useState(false);

  // 預覽模式下只顯示前 500 個字元
  const previewLength = 500;
  const needsTruncate = methodology.length > previewLength;
  const displayContent = expanded ? methodology : methodology.slice(0, previewLength);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">📖</span>
        <h2 className="text-xl font-bold text-gray-900">原理應用</h2>
      </div>

      <div className="prose prose-sm prose-gray max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // 自定義 table 樣式
            table: ({ children }) => (
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse border border-gray-300">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border border-gray-300 bg-gray-100 px-3 py-2 text-left text-sm font-semibold">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-gray-300 px-3 py-2 text-sm">
                {children}
              </td>
            ),
            // 自定義 code 區塊樣式
            code: ({ className, children, ...props }) => {
              const isInline = !className;
              if (isInline) {
                return (
                  <code className="bg-gray-100 px-1 py-0.5 rounded text-sm text-gray-800" {...props}>
                    {children}
                  </code>
                );
              }
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
            pre: ({ children }) => (
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                {children}
              </pre>
            ),
          }}
        >
          {displayContent + (needsTruncate && !expanded ? '...' : '')}
        </ReactMarkdown>
      </div>

      {needsTruncate && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-4 flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium text-sm"
        >
          <span>{expanded ? '收起內容' : '展開完整內容'}</span>
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      )}
    </div>
  );
}
