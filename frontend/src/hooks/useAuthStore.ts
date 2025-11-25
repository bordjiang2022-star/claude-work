// 用户认证状态管理
import { create } from 'zustand';
import type { User } from '@/types';
import { apiService } from '@/services/api';
import { useTranslationStore } from './useTranslationStore';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.login({ email, password });
      const user = await apiService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  register: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.register({ email, password });
      const user = await apiService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    // 如果有活跃的翻译会话，先停止它
    const { isTranslating, stopTranslation } = useTranslationStore.getState();
    if (isTranslating) {
      try {
        await stopTranslation();
      } catch (error) {
        console.error('Failed to stop translation during logout:', error);
      }
    }

    apiService.logout();
    set({ user: null, isAuthenticated: false });
  },

  fetchCurrentUser: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await apiService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({ isLoading: false, isAuthenticated: false });
    }
  },

  clearError: () => set({ error: null }),
}));
