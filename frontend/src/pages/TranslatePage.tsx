// 主翻译页面
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/hooks/useAuthStore';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import { LanguageSelector } from '@/components/LanguageSelector';
import { AudioDeviceSelector } from '@/components/AudioDeviceSelector';
import { TranslationControls } from '@/components/TranslationControls';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { Header } from '@/components/Header';
import { wsService } from '@/services/websocket';
// 注意：TTS 现在由后端 PyAudio 处理，不再使用前端 ttsService

export const TranslatePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();
  const { addTranscript } = useTranslationStore();

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
        {/* 语言选择和控制面板 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <LanguageSelector />
          <div className="mt-4">
            <AudioDeviceSelector />
          </div>
          <div className="mt-6">
            <TranslationControls />
          </div>
        </div>

        {/* 转录面板 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <TranscriptPanel />
        </div>
      </main>
    </div>
  );
};
