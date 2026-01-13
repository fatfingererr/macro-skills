import { useState } from 'react';
import type { Skill } from '../../types/skill';
import {
  generateInstallCommand,
  generateSkillEnableCommand,
} from '../../services/skillService';
import Button from '../common/Button';

interface InstallModalProps {
  skill: Skill;
  onClose: () => void;
}

export default function InstallModal({ skill, onClose }: InstallModalProps) {
  const [copiedAdd, setCopiedAdd] = useState(false);
  const [copiedEnable, setCopiedEnable] = useState(false);

  const addCommand = generateInstallCommand(skill);
  const enableCommand = generateSkillEnableCommand(skill.id);

  const handleCopyAdd = async () => {
    try {
      await navigator.clipboard.writeText(addCommand);
      setCopiedAdd(true);
      setTimeout(() => setCopiedAdd(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleCopyEnable = async () => {
    try {
      await navigator.clipboard.writeText(enableCommand);
      setCopiedEnable(true);
      setTimeout(() => setCopiedEnable(false), 2000);
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
        <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              安裝【{skill.displayName}】技能
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

          {/* Step 1: Add Marketplace */}
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-medium">步驟 1：</span>添加技能市集 (Marketplace)
            </p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-900 rounded-lg p-3">
                <code className="text-sm text-green-400 break-all">
                  {addCommand}
                </code>
              </div>
              <Button size="sm" onClick={handleCopyAdd}>
                {copiedAdd ? '已複製' : '複製'}
              </Button>
            </div>
          </div>

          {/* Step 2: Enable Skill */}
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-medium">步驟 2：</span>啟用指定技能 (Skill)
            </p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-900 rounded-lg p-3">
                <code className="text-sm text-green-400 break-all">
                  {enableCommand}
                </code>
              </div>
              <Button size="sm" onClick={handleCopyEnable}>
                {copiedEnable ? '已複製' : '複製'}
              </Button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
