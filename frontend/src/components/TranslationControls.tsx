// 翻译控制按钮组件
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';

export const TranslationControls: React.FC = () => {
  const { t } = useTranslation();
  const { isTranslating, startTranslation, stopTranslation, error } = useTranslationStore();

  const handleStart = async () => {
    try {
      await startTranslation();
    } catch (err) {
      console.error('Failed to start translation:', err);
    }
  };

  const handleStop = async () => {
    try {
      await stopTranslation();
    } catch (err) {
      console.error('Failed to stop translation:', err);
    }
  };

  return (
    <div className="flex flex-col items-center">
      {/* 错误提示 */}
      {error && (
        <div className="w-full mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* 控制按钮 */}
      <div className="flex space-x-4">
        {/* START按钮 */}
        <button
          onClick={handleStart}
          disabled={isTranslating}
          className={`
            px-8 py-4 rounded-lg font-semibold text-lg transition duration-200 min-w-[150px]
            ${
              isTranslating
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
            }
          `}
        >
          ▶ {t('translation.start')}
        </button>

        {/* STOP按钮 */}
        <button
          onClick={handleStop}
          disabled={!isTranslating}
          className={`
            px-8 py-4 rounded-lg font-semibold text-lg transition duration-200 min-w-[150px]
            ${
              !isTranslating
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gray-600 hover:bg-gray-700 text-white shadow-lg hover:shadow-xl'
            }
          `}
        >
          ⏸ {t('translation.stop')}
        </button>
      </div>

      {/* 状态指示 */}
      {isTranslating && (
        <div className="mt-4 flex items-center space-x-2 text-primary-600">
          <div className="w-3 h-3 bg-primary-600 rounded-full animate-pulse"></div>
          <span className="font-medium">{t('translation.translating')}</span>
        </div>
      )}

      {/* 提示信息 */}
      <div className="mt-4 text-center text-sm text-gray-500">
        💡 {t('app.subtitle')}
      </div>
    </div>
  );
};
