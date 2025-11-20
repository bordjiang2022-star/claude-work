// 主翻译页面
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/hooks/useAuthStore';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import { LanguageSelector } from '@/components/LanguageSelector';
import { TranslationControls } from '@/components/TranslationControls';
import { TranscriptPanel } from '@/components/TranscriptPanel';
import { Header } from '@/components/Header';
import { wsService } from '@/services/websocket';

export const TranslatePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
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
        addTranscript({
          timestamp: new Date().toISOString(),
          source_text: message.data.source_text,
          translated_text: message.data.translated_text,
        });
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
