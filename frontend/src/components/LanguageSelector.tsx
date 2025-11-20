// 语言和音色选择组件
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { Language, Voice } from '@/types';

export const LanguageSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig, isTranslating } = useTranslationStore();

  const languages: Language[] = ['en', 'zh', 'ja', 'ko'];
  const voices: Voice[] = ['Cherry', 'Nofish', 'Sunny', 'Jada', 'Dylan', 'Peter', 'Eric', 'Kiki'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* 目标语言选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('translation.targetLanguage')}
        </label>
        <select
          value={config.target_language}
          onChange={(e) => setConfig({ target_language: e.target.value })}
          disabled={isTranslating}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {languages.map((lang) => (
            <option key={lang} value={lang}>
              {t(`languages.${lang}`)}
            </option>
          ))}
        </select>
      </div>

      {/* TTS音色选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('translation.ttsVoice')}
        </label>
        <select
          value={config.voice || 'Cherry'}
          onChange={(e) => setConfig({ voice: e.target.value })}
          disabled={isTranslating || !config.audio_enabled}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {voices.map((voice) => (
            <option key={voice} value={voice}>
              {t(`voices.${voice}`)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
