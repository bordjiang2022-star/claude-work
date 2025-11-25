// 主画面语言选择组件（仅显示源语言和目标语言）
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { Language } from '@/types';

export const MainLanguageSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig, isTranslating } = useTranslationStore();

  const languages: Language[] = ['en', 'zh', 'ja', 'ko'];
  const sourceLanguages: Language[] = ['zh', 'en', 'ja', 'ko'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      {/* 源语言选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('translation.sourceLanguage')}
        </label>
        <select
          value={config.source_language || 'zh'}
          onChange={(e) => setConfig({ source_language: e.target.value })}
          disabled={isTranslating}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {sourceLanguages.map((lang) => (
            <option key={lang} value={lang}>
              {t(`languages.${lang}`)}
            </option>
          ))}
        </select>
      </div>

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
    </div>
  );
};
