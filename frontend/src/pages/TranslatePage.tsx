// 主翻译页面
import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/hooks/useAuthStore';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import { useSpeechRecognition, SpeechRecognitionResult } from '@/hooks/useSpeechRecognition';
import { TranslationControls } from '@/components/TranslationControls';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { Header } from '@/components/Header';
import SessionTimer from '@/components/SessionTimer';
import { MainLanguageSelector } from '@/components/MainLanguageSelector';
import { wsService } from '@/services/websocket';
// 注意：TTS 现在由后端 PyAudio 处理，不再使用前端 ttsService

export const TranslatePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();
  const {
    addTranscript,
    addSourceText,
    setCurrentSourceText,
    isTranslating,
    sessionStartTime,
    config,
  } = useTranslationStore();

  // 语音识别结果回调
  const handleSpeechResult = useCallback((result: SpeechRecognitionResult) => {
    console.log('[SpeechRecognition] Result:', result.text, 'isFinal:', result.isFinal);
    if (result.isFinal) {
      addSourceText(result.text, true);
    }
  }, [addSourceText]);

  // 语音识别错误回调
  const handleSpeechError = useCallback((error: string) => {
    console.error('[SpeechRecognition] Error:', error);
  }, []);

  // 初始化语音识别
  const {
    isListening,
    isSupported: isSpeechSupported,
    currentTranscript,
    startListening,
    stopListening,
  } = useSpeechRecognition({
    language: config.source_language || 'zh',
    continuous: true,
    interimResults: true,
    onResult: handleSpeechResult,
    onError: handleSpeechError,
  });

  // 更新临时识别文本
  useEffect(() => {
    setCurrentSourceText(currentTranscript);
  }, [currentTranscript, setCurrentSourceText]);

  // 翻译状态变化时，启动/停止语音识别
  useEffect(() => {
    if (isTranslating && config.browser_asr_enabled && isSpeechSupported) {
      console.log('[TranslatePage] Starting speech recognition...');
      startListening();
    } else {
      if (isListening) {
        console.log('[TranslatePage] Stopping speech recognition...');
        stopListening();
      }
    }
  }, [isTranslating, config.browser_asr_enabled, isSpeechSupported]);

  // 组件卸载时停止语音识别
  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  useEffect(() => {
    // 检查认证状态
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // WebSocket消息处理
    const handleMessage = (message: any) => {
      if (message.type === 'transcript') {
        const translatedText = message.data.translated_text;

        // 添加到转录列表
        addTranscript({
          timestamp: new Date().toISOString(),
          source_text: message.data.source_text,
          translated_text: translatedText,
        });

        // 注意：TTS 现在由后端 PyAudio 直接播放到扬声器
        // 不再需要前端播放，因为：
        // 1. 浏览器的 Web Speech API 不支持音频设备路由
        // 2. Google TTS 有 CORS 问题且不稳定
        // 3. 后端 PyAudio 可以直接控制输出设备
        console.log('[Transcript] Received:', translatedText?.substring(0, 50));
      }
    };

    wsService.addMessageHandler(handleMessage);

    return () => {
      wsService.removeMessageHandler(handleMessage);
    };
  }, [addTranscript]);

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <Header />

      {/* 主内容区 */}
      <main className="container mx-auto px-4 py-6">
        {/* 控制面板 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {t('app.title')}
            </h2>
            <button
              onClick={() => navigate('/settings')}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition duration-200 shadow-sm flex items-center space-x-2"
              disabled={isTranslating}
            >
              <span>⚙️</span>
              <span>{t('translation.settings')}</span>
            </button>
          </div>

          {/* 语言选择器 */}
          <MainLanguageSelector />

          {/* 会话计时器 */}
          <SessionTimer isTranslating={isTranslating} sessionStartTime={sessionStartTime} />

          {/* 翻译控制按钮 */}
          <TranslationControls />
        </div>

        {/* 转录面板 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <TranscriptPanel />
        </div>

        {/* 版权信息 */}
        <div className="text-center text-gray-500 text-sm mt-6 py-4">
          {t('footer.copyright')}
        </div>
      </main>
    </div>
  );
};
