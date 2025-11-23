// 语言和音色选择组件
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { Language, Voice, TtsEngine } from '@/types';

export const LanguageSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig, isTranslating } = useTranslationStore();

  const languages: Language[] = ['en', 'zh', 'ja', 'ko'];
  const voices: Voice[] = ['Cherry', 'Nofish', 'Sunny', 'Jada', 'Dylan', 'Peter', 'Eric', 'Kiki'];
  const ttsEngines: TtsEngine[] = ['alibaba', 'windows'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

      {/* TTS引擎选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('translation.ttsEngine')}
        </label>
        <select
          value={config.tts_engine || 'alibaba'}
          onChange={(e) => setConfig({ tts_engine: e.target.value as TtsEngine })}
          disabled={isTranslating || !config.audio_enabled}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {ttsEngines.map((engine) => (
            <option key={engine} value={engine}>
              {t(`ttsEngines.${engine}`)}
            </option>
          ))}
        </select>
      </div>

      {/* TTS音色选择 - 只在阿里云引擎时显示 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('translation.ttsVoice')}
        </label>
        <select
          value={config.voice || 'Cherry'}
          onChange={(e) => setConfig({ voice: e.target.value })}
          disabled={isTranslating || !config.audio_enabled || config.tts_engine === 'windows'}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {voices.map((voice) => (
            <option key={voice} value={voice}>
              {t(`voices.${voice}`)}
            </option>
          ))}
        </select>
        {config.tts_engine === 'windows' && (
          <p className="text-xs text-gray-500 mt-1">{t('translation.windowsTtsNote')}</p>
        )}
      </div>
    </div>
  );
};
