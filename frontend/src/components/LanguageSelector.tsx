// 语言和音色选择组件
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { Language, Voice, TtsEngine } from '@/types';

export const LanguageSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig, isTranslating } = useTranslationStore();

  const languages: Language[] = ['en', 'zh', 'ja', 'ko'];
  const sourceLanguages: Language[] = ['zh', 'en', 'ja', 'ko'];  // 源语言选项
  const voices: Voice[] = ['Cherry', 'Nofish', 'Sunny', 'Jada', 'Dylan', 'Peter', 'Eric', 'Kiki'];
  const ttsEngines: TtsEngine[] = ['alibaba', 'windows'];

  // 检查浏览器是否支持 Web Speech API
  const isSpeechSupported = typeof window !== 'undefined' &&
    (window.SpeechRecognition || (window as any).webkitSpeechRecognition);

  return (
    <div className="space-y-6">
      {/* 第一行：源语言、目标语言 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 源语言选择（用于浏览器语音识别） */}
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

      {/* 第二行：TTS引擎、TTS音色、浏览器语音识别开关 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

        {/* 浏览器语音识别开关 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('translation.browserAsr')}
          </label>
          <div className="flex items-center h-[50px]">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.browser_asr_enabled ?? true}
                onChange={(e) => setConfig({ browser_asr_enabled: e.target.checked })}
                disabled={isTranslating || !isSpeechSupported}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
              <span className="ml-3 text-sm font-medium text-gray-700">
                {config.browser_asr_enabled ? t('common.enabled') : t('common.disabled')}
              </span>
            </label>
          </div>
          {!isSpeechSupported && (
            <p className="text-xs text-orange-500 mt-1">{t('translation.browserAsrNotSupported')}</p>
          )}
          {isSpeechSupported && (
            <p className="text-xs text-gray-500 mt-1">{t('translation.browserAsrNote')}</p>
          )}
        </div>
      </div>
    </div>
  );
};
