// 翻译状态管理
import { create } from 'zustand';
import type { TranscriptItem, TranslationConfig, SourceTextItem } from '@/types';
import { apiService } from '@/services/api';
import { wsService } from '@/services/websocket';

interface TranslationState {
  isTranslating: boolean;
  isPaused: boolean;  // 是否暂停（不停止后端服务）
  config: TranslationConfig;
  transcripts: TranscriptItem[];
  sourceTexts: SourceTextItem[];  // 浏览器语音识别的原文（独立流）
  currentSourceText: string;  // 当前正在识别的临时文本
  currentSessionId: number | null;
  sessionStartTime: Date | null;  // 会话开始时间
  error: string | null;

  setConfig: (config: Partial<TranslationConfig>) => void;
  startTranslation: () => Promise<void>;
  stopTranslation: () => Promise<void>;
  pauseTranslation: () => void;
  resumeTranslation: () => void;
  addTranscript: (transcript: Omit<TranscriptItem, 'id'>) => void;
  addSourceText: (text: string, isFinal: boolean) => void;  // 添加原文
  setCurrentSourceText: (text: string) => void;  // 设置临时识别文本
  clearTranscripts: () => void;
  downloadTranscript: (type: 'source' | 'translation') => Promise<void>;
}

export const useTranslationStore = create<TranslationState>((set, get) => ({
  isTranslating: false,
  isPaused: false,
  config: {
    target_language: 'en',
    source_language: 'zh',  // 默认源语言为中文
    voice: 'Cherry',
    audio_enabled: true,
    tts_engine: 'alibaba', // 默认使用阿里云TTS
    browser_asr_enabled: true, // 默认启用浏览器语音识别
  },
  transcripts: [],
  sourceTexts: [],
  currentSourceText: '',
  currentSessionId: null,
  sessionStartTime: null,
  error: null,

  setConfig: (newConfig) => {
    set((state) => ({
      config: { ...state.config, ...newConfig },
    }));
  },

  startTranslation: async () => {
    set({ error: null });
    try {
      const config = get().config;
      console.log('[Translation] Starting with config:', JSON.stringify(config, null, 2));
      const response = await apiService.startTranslation(config);
      console.log('[Translation] Started successfully, session_id:', response.session_id);
      set({
        isTranslating: true,
        currentSessionId: response.session_id,
        sessionStartTime: new Date(),
        transcripts: [],
      });

      // 连接WebSocket
      const token = apiService.getToken();
      if (token) {
        wsService.connect(token);
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to start translation';
      set({ error: message });
      throw error;
    }
  },

  stopTranslation: async () => {
    try {
      await apiService.stopTranslation();
      set({ isTranslating: false, isPaused: false });

      // 断开WebSocket
      wsService.disconnect();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to stop translation';
      set({ error: message });
      throw error;
    }
  },

  pauseTranslation: () => {
    // 暂停翻译（不停止后端服务）
    set({ isPaused: true });
  },

  resumeTranslation: () => {
    // 恢复翻译
    set({ isPaused: false });
  },

  addTranscript: (transcript) => {
    set((state) => ({
      transcripts: [
        ...state.transcripts,
        { ...transcript, id: state.transcripts.length + 1 },
      ],
    }));
  },

  addSourceText: (text, isFinal) => {
    if (!text.trim()) return;
    set((state) => ({
      sourceTexts: [
        ...state.sourceTexts,
        {
          id: state.sourceTexts.length + 1,
          timestamp: new Date().toISOString(),
          text: text.trim(),
          isFinal,
        },
      ],
      currentSourceText: '',  // 清除临时文本
    }));
  },

  setCurrentSourceText: (text) => {
    set({ currentSourceText: text });
  },

  clearTranscripts: () => {
    set({ transcripts: [], sourceTexts: [], currentSourceText: '' });
  },

  downloadTranscript: async (type) => {
    const { transcripts, sourceTexts, currentSessionId } = get();

    // 根据类型选择数据源
    if (type === 'source') {
      // 下载原文（来自浏览器语音识别）
      if (sourceTexts.length === 0) {
        throw new Error('No source texts to download');
      }

      try {
        const content = sourceTexts
          .map((t) => {
            const timestamp = new Date(t.timestamp).toLocaleTimeString();
            return `[${timestamp}] ${t.text}`;
          })
          .join('\n');

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript_source_${currentSessionId || Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error: any) {
        const message = error.message || 'Failed to download source transcript';
        set({ error: message });
        throw error;
      }
    } else {
      // 下载译文
      if (transcripts.length === 0) {
        throw new Error('No transcripts to download');
      }

      try {
        const content = transcripts
          .map((t) => {
            const timestamp = new Date(t.timestamp).toLocaleTimeString();
            return t.translated_text ? `[${timestamp}] ${t.translated_text}` : null;
          })
          .filter(Boolean)
          .join('\n');

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript_translation_${currentSessionId || Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error: any) {
        const message = error.message || 'Failed to download transcript';
        set({ error: message });
        throw error;
      }
    }
  },
}));
