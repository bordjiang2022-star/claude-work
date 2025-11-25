// 翻译控制按钮组件
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';

export const TranslationControls: React.FC = () => {
  const { t } = useTranslation();
  const {
    isTranslating,
    isPaused,
    startTranslation,
    pauseTranslation,
    resumeTranslation,
    error,
    config
  } = useTranslationStore();

  const handleStart = async () => {
    try {
      await startTranslation();
    } catch (err) {
      console.error('Failed to start translation:', err);
    }
  };

  const handlePause = () => {
    // 暂停翻译（不停止后端服务）
    pauseTranslation();
  };

  const handleResume = () => {
    // 恢复翻译
    resumeTranslation();
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
                : 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl'
            }
          `}
        >
          {t('translation.start')}
        </button>

        {/* PAUSE/RESUME按钮 */}
        {isTranslating && !isPaused && (
          <button
            onClick={handlePause}
            className="px-8 py-4 rounded-lg font-semibold text-lg transition duration-200 min-w-[150px] bg-yellow-600 hover:bg-yellow-700 text-white shadow-lg hover:shadow-xl"
          >
            {t('translation.pause')}
          </button>
        )}

        {isTranslating && isPaused && (
          <button
            onClick={handleResume}
            className="px-8 py-4 rounded-lg font-semibold text-lg transition duration-200 min-w-[150px] bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl"
          >
            {t('translation.resume')}
          </button>
        )}
      </div>

      {/* 状态指示 */}
      {isTranslating && !isPaused && (
        <div className="mt-4 flex items-center space-x-2 text-green-600">
          <div className="w-3 h-3 bg-green-600 rounded-full animate-pulse"></div>
          <span className="font-medium">{t('translation.translating')}</span>
        </div>
      )}

      {isTranslating && isPaused && (
        <div className="mt-4 flex items-center space-x-2 text-yellow-600">
          <div className="w-3 h-3 bg-yellow-600 rounded-full"></div>
          <span className="font-medium">{t('translation.paused')}</span>
        </div>
      )}

      {/* TTS 状态提示 */}
      {config.audio_enabled && (
        <div className="mt-4 text-center text-sm text-gray-600 bg-blue-50 px-4 py-2 rounded">
          TTS audio will play through the selected output device (backend PyAudio)
        </div>
      )}

      {/* 提示信息 */}
      <div className="mt-4 text-center text-sm text-gray-500">
        {t('app.subtitle')}
      </div>
    </div>
  );
};
