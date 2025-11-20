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
      const response = await apiService.startTranslation(get().config);
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
    const { currentSessionId } = get();
    if (!currentSessionId) {
      throw new Error('No active session');
    }

    try {
      const blob = await apiService.downloadTranscript(currentSessionId, type);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transcript_${type}_${currentSessionId}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to download transcript';
      set({ error: message });
      throw error;
    }
  },
}));
