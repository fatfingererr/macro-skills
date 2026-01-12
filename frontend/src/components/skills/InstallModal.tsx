import { useState } from 'react';
import type { Skill } from '../../types/skill';
import { generateInstallCommand } from '../../services/skillService';
import Button from '../common/Button';

interface InstallModalProps {
  skill: Skill;
  onClose: () => void;
}

export default function InstallModal({ skill, onClose }: InstallModalProps) {
  const [copied, setCopied] = useState(false);
  const installCommand = generateInstallCommand(skill);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(installCommand);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-25"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              安裝 {skill.displayName}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            在終端機中執行以下指令來安裝此技能：
          </p>

          <div className="bg-gray-900 rounded-lg p-4 mb-4">
            <code className="text-sm text-green-400 break-all">
              {installCommand}
            </code>
          </div>

          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose}>
              關閉
            </Button>
            <Button onClick={handleCopy}>
              {copied ? '已複製！' : '複製指令'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
