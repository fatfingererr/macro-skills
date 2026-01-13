import { useState } from 'react';
import { useCopyToClipboard } from '../../hooks/useCopyToClipboard';
import type { TestQuestion } from '../../types/skill';

interface TestQuestionsSectionProps {
  questions: TestQuestion[];
}

interface QuestionItemProps {
  question: TestQuestion;
}

function QuestionItem({ question }: QuestionItemProps) {
  const [showResult, setShowResult] = useState(false);
  const { copied, copy } = useCopyToClipboard();

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <p className="text-gray-900 leading-relaxed">{question.question}</p>
        </div>
        <button
          onClick={() => copy(question.question)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          title="複製問題"
        >
          {copied ? (
            <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          )}
        </button>
      </div>

      {question.expectedResult && (
        <div className="mt-3">
          <button
            onClick={() => setShowResult(!showResult)}
            className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span>預期結果</span>
            <svg
              className={`w-4 h-4 transition-transform ${showResult ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showResult && (
            <div className="mt-2 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.expectedResult}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function TestQuestionsSection({ questions }: TestQuestionsSectionProps) {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">💭</span>
        <h2 className="text-xl font-bold text-gray-900">分析課題</h2>
      </div>

      <div className="space-y-3">
        {questions.map((question, index) => (
          <QuestionItem key={index} question={question} />
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-800">
          <span className="font-medium">提示：</span>
          點擊複製按鈕後，將問題貼上至 Claude Code 即可測試此技能的功能。
        </p>
      </div>
    </div>
  );
}
