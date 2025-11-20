// 实时转录面板组件
import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import { format } from 'date-fns';

export const TranscriptPanel: React.FC = () => {
  const { t } = useTranslation();
  const { transcripts, clearTranscripts, downloadTranscript, isTranslating } = useTranslationStore();
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
  }, [transcripts]);

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

  const sourceCharCount = transcripts.reduce(
    (sum, t) => sum + (t.source_text?.length || 0),
    0
  );
  const translationCharCount = transcripts.reduce(
    (sum, t) => sum + (t.translated_text?.length || 0),
    0
  );

  return (
    <div className="space-y-4">
      {/* 标题和操作按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          📝 {t('transcript.title')}
        </h2>

        <div className="flex space-x-2">
          <button
            onClick={clearTranscripts}
            disabled={transcripts.length === 0}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            🗑️ {t('transcript.clear')}
          </button>

          <button
            onClick={() => handleDownload('source')}
            disabled={transcripts.length === 0}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ⬇️ {t('transcript.downloadSource')}
          </button>

          <button
            onClick={() => handleDownload('translation')}
            disabled={transcripts.length === 0}
            className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ⬇️ {t('transcript.downloadTranslation')}
          </button>
        </div>
      </div>

      {/* 双栏显示 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 原文面板 */}
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-3 border-b border-gray-300">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-700">{t('translation.source')}</h3>
              <span className="text-sm text-gray-500">
                {t('translation.characterCount', { count: sourceCharCount })}
              </span>
            </div>
          </div>

          <div
            ref={sourceRef}
            className="h-[500px] overflow-y-auto p-4 bg-white"
          >
            {transcripts.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-400">
                {isTranslating
                  ? t('translation.waitingForInput')
                  : t('transcript.noData')}
              </div>
            ) : (
              <div className="space-y-3">
                {transcripts.map((transcript) => (
                  <div key={transcript.id} className="border-l-4 border-blue-500 pl-3">
                    <div className="text-xs text-gray-500 mb-1">
                      {formatTime(transcript.timestamp)}
                    </div>
                    <div className="text-gray-800">
                      {transcript.source_text || (
                        <span className="text-gray-400 italic">—</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 译文面板 */}
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          <div className="bg-green-50 px-4 py-3 border-b border-gray-300">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-700">{t('translation.translation')}</h3>
              <span className="text-sm text-gray-500">
                {t('translation.characterCount', { count: translationCharCount })}
              </span>
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
