// 类型定义

export interface User {
  id: number;
  email: string;
  created_at: string;
  last_login: string | null;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface TranslationConfig {
  target_language: string;
  voice?: string;
  audio_enabled: boolean;
  input_device_index?: number;  // 输入设备（麦克风/虚拟音频线缆）
  output_device_index?: number; // 输出设备（扬声器，用于TTS播放）
}

export interface AudioDevice {
  index: number;
  name: string;
  sample_rate: number;
}

export interface AudioDevicesResponse {
  input_devices: AudioDevice[];
  output_devices: AudioDevice[];
}

export interface TranscriptItem {
  id: number;
  timestamp: string;
  source_text: string | null;
  translated_text: string | null;
}

export interface Session {
  id: number;
  source_language: string | null;
  target_language: string;
  voice: string | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
}

export interface Statistics {
  total_sessions: number;
  total_duration_seconds: number;
  total_characters_translated: number;
  last_updated: string;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
}

export type Language = 'en' | 'zh' | 'ja' | 'ko' | 'ru' | 'fr' | 'de' | 'pt' | 'es' | 'it' | 'yue';

export type Voice = 'Cherry' | 'Nofish' | 'Sunny' | 'Jada' | 'Dylan' | 'Peter' | 'Eric' | 'Kiki';
