// 实时转录面板组件
import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import { format } from 'date-fns';

export const TranscriptPanel: React.FC = () => {
  const { t } = useTranslation();
  const {
    transcripts,
    sourceTexts,
    currentSourceText,
    clearTranscripts,
    downloadTranscript,
    isTranslating,
    config,
  } = useTranslationStore();
  const sourceRef = useRef<HTMLDivElement>(null);
  const translationRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (sourceRef.current) {
      sourceRef.current.scrollTop = sourceRef.current.scrollHeight;
    }
    if (translationRef.current) {
      translationRef.current.scrollTop = translationRef.current.scrollHeight;
    }
  }, [transcripts, sourceTexts, currentSourceText]);

  const handleDownload = async (type: 'source' | 'translation') => {
    try {
      await downloadTranscript(type);
    } catch (err) {
      console.error('Failed to download transcript:', err);
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'HH:mm:ss');
    } catch {
      return '';
    }
  };

  // 原文字符计数（来自浏览器语音识别）
  const sourceCharCount = sourceTexts.reduce(
    (sum, t) => sum + t.text.length,
    0
  ) + currentSourceText.length;

  const translationCharCount = transcripts.reduce(
    (sum, t) => sum + (t.translated_text?.length || 0),
    0
  );

  return (
    <div className="space-y-4">
      {/* 标题和清除按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          📝 {t('transcript.title')}
        </h2>

        <button
          onClick={clearTranscripts}
          disabled={transcripts.length === 0}
          className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          🗑️ {t('transcript.clear')}
        </button>
      </div>

      {/* 双栏显示 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 原文面板 */}
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          {/* 原文面板标题栏 - 包含下载按钮 */}
          <div className="bg-gray-100 px-4 py-3 border-b border-gray-300">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-700">{t('translation.source')}</h3>
              <span className="text-sm text-gray-500">
                {t('translation.characterCount', { count: sourceCharCount })}
              </span>
            </div>
            <div className="flex justify-start">
              <button
                onClick={() => handleDownload('source')}
                disabled={sourceTexts.length === 0}
                className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⬇️ {t('transcript.downloadSource')}
              </button>
            </div>
          </div>

          <div
            ref={sourceRef}
            className="h-[500px] overflow-y-auto p-4 bg-white"
          >
            {sourceTexts.length === 0 && !currentSourceText ? (
              <div className="h-full flex items-center justify-center text-gray-400">
                {isTranslating
                  ? (config.browser_asr_enabled
                      ? t('translation.waitingForSpeech')
                      : t('translation.browserAsrDisabled'))
                  : t('transcript.noData')}
              </div>
            ) : (
              <div className="space-y-3">
                {/* 已识别的原文 */}
                {sourceTexts.map((item) => (
                  <div key={item.id} className="border-l-4 border-blue-500 pl-3">
                    <div className="text-xs text-gray-500 mb-1">
                      {formatTime(item.timestamp)}
                    </div>
                    <div className="text-gray-800">
                      {item.text}
                    </div>
                  </div>
                ))}
                {/* 正在识别的临时文本 */}
                {currentSourceText && (
                  <div className="border-l-4 border-blue-300 pl-3 opacity-70">
                    <div className="text-xs text-gray-400 mb-1">
                      {t('translation.recognizing')}
                    </div>
                    <div className="text-gray-600 italic">
                      {currentSourceText}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 译文面板 */}
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          {/* 译文面板标题栏 - 包含下载按钮 */}
          <div className="bg-green-50 px-4 py-3 border-b border-gray-300">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-700">{t('translation.translation')}</h3>
              <span className="text-sm text-gray-500">
                {t('translation.characterCount', { count: translationCharCount })}
              </span>
            </div>
            <div className="flex justify-start">
              <button
                onClick={() => handleDownload('translation')}
                disabled={transcripts.length === 0}
                className="px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white text-sm rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ⬇️ {t('transcript.downloadTranslation')}
              </button>
            </div>
          </div>

          <div
            ref={translationRef}
            className="h-[500px] overflow-y-auto p-4 bg-white"
          >
            {transcripts.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">
                {isTranslating
                  ? t('translation.waitingForTranslation')
                  : t('transcript.noData')}
              </div>
            ) : (
              <div className="space-y-3">
                {transcripts.map((transcript) => (
                  <div key={transcript.id} className="border-l-4 border-green-500 pl-3">
                    <div className="text-xs text-gray-500 mb-1">
                      {formatTime(transcript.timestamp)}
                    </div>
                    <div className="text-gray-800">
                      {transcript.translated_text || (
                        <span className="text-gray-400 italic">—</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
