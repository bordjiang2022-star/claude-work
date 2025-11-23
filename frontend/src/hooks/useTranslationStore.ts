// 翻译状态管理
import { create } from 'zustand';
import type { TranscriptItem, TranslationConfig } from '@/types';
import { apiService } from '@/services/api';
import { wsService } from '@/services/websocket';

interface TranslationState {
  isTranslating: boolean;
  config: TranslationConfig;
  transcripts: TranscriptItem[];
  currentSessionId: number | null;
  error: string | null;

  setConfig: (config: Partial<TranslationConfig>) => void;
  startTranslation: () => Promise<void>;
  stopTranslation: () => Promise<void>;
  addTranscript: (transcript: Omit<TranscriptItem, 'id'>) => void;
  clearTranscripts: () => void;
  downloadTranscript: (type: 'source' | 'translation') => Promise<void>;
}

export const useTranslationStore = create<TranslationState>((set, get) => ({
  isTranslating: false,
  config: {
    target_language: 'en',
    voice: 'Cherry',
    audio_enabled: true,
    tts_engine: 'alibaba', // 默认使用阿里云TTS
  },
  transcripts: [],
  currentSessionId: null,
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
      set({ isTranslating: false });

      // 断开WebSocket
      wsService.disconnect();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to stop translation';
      set({ error: message });
      throw error;
    }
  },

  addTranscript: (transcript) => {
    set((state) => ({
      transcripts: [
        ...state.transcripts,
        { ...transcript, id: state.transcripts.length + 1 },
      ],
    }));
  },

  clearTranscripts: () => {
    set({ transcripts: [] });
  },

  downloadTranscript: async (type) => {
    const { transcripts, currentSessionId } = get();

    if (transcripts.length === 0) {
      throw new Error('No transcripts to download');
    }

    try {
      // 生成文本内容
      const content = transcripts
        .map((t) => {
          const timestamp = new Date(t.timestamp).toLocaleTimeString();
          const text = type === 'source' ? t.source_text : t.translated_text;
          return text ? `[${timestamp}] ${text}` : null;
        })
        .filter(Boolean)
        .join('\n');

      // 创建Blob并下载
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transcript_${type}_${currentSessionId || Date.now()}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      const message = error.message || 'Failed to download transcript';
      set({ error: message });
      throw error;
    }
  },
}));
