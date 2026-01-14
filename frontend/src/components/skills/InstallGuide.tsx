import { useCopyToClipboard } from '../../hooks/useCopyToClipboard';
import { generateMarketplaceAddCommand, generateSkillInstallCommand } from '../../services/skillService';

interface InstallGuideProps {
  skillId: string;
}

interface InstallStep {
  number: number;
  title: string;
  description: string;
  command?: string;
}

export default function InstallGuide({ skillId }: InstallGuideProps) {
  const { copied: copiedStep1, copy: copyStep1 } = useCopyToClipboard();
  const { copied: copiedStep2, copy: copyStep2 } = useCopyToClipboard();

  const steps: InstallStep[] = [
    {
      number: 1,
      title: '新增市集 (Marketplace)',
      description: '執行以下指令將技能市集加入 Claude Code',
      command: generateMarketplaceAddCommand(),
    },
    {
      number: 2,
      title: '安裝技能 (Skill)',
      description: '安裝指定的技能',
      command: generateSkillInstallCommand(skillId),
    },
    {
      number: 3,
      title: '開始使用',
      description: '在 Claude Code 中輸入下方宏觀分析課題',
    },
  ];

  const getCopyState = (stepNum: number) => {
    if (stepNum === 1) return { copied: copiedStep1, copy: copyStep1 };
    if (stepNum === 2) return { copied: copiedStep2, copy: copyStep2 };
    return { copied: false, copy: async () => { } };
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">🛠️</span>
        <h2 className="text-xl font-bold text-gray-900">如何安裝與使用</h2>
      </div>

      <div className="space-y-6">
        {steps.map((step) => {
          const { copied, copy } = getCopyState(step.number);

          return (
            <div key={step.number} className="flex gap-4">
              {/* Step Number */}
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center">
                  {step.number}
                </div>
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">{step.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{step.description}</p>

                {step.command && (
                  <div className="relative">
                    <div className="bg-gray-900 rounded-lg p-4 pr-12">
                      <code className="text-sm text-green-400 break-all">
                        {step.command}
                      </code>
                    </div>
                    <button
                      onClick={() => copy(step.command!)}
                      className="absolute top-3 right-3 text-gray-400 hover:text-gray-200 transition-colors"
                      title="複製指令"
                    >
                      {copied ? (
                        <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
