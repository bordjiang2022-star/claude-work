// API服务层
import axios, { AxiosInstance } from 'axios';
import type {
  User,
  LoginData,
  RegisterData,
  TokenResponse,
  TranslationConfig,
  TranscriptItem,
  Session,
  Statistics,
  AudioDevicesResponse
} from '@/types';

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器：添加认证token
    this.api.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // 响应拦截器：处理401错误
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Token管理
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('token');
  }

  // 认证API
  async register(data: RegisterData): Promise<TokenResponse> {
    const response = await this.api.post<TokenResponse>('/auth/register', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async login(data: LoginData): Promise<TokenResponse> {
    const response = await this.api.post<TokenResponse>('/auth/login', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  logout() {
    this.clearToken();
  }

  // 翻译API
  async startTranslation(config: TranslationConfig): Promise<any> {
    const response = await this.api.post('/translation/start', config);
    return response.data;
  }

  async stopTranslation(): Promise<any> {
    const response = await this.api.post('/translation/stop');
    return response.data;
  }

  async getTranslationStatus(): Promise<any> {
    const response = await this.api.get('/translation/status');
    return response.data;
  }

  // 会话API
  async getSessions(limit: number = 10): Promise<Session[]> {
    const response = await this.api.get<Session[]>(`/sessions?limit=${limit}`);
    return response.data;
  }

  async getTranscripts(sessionId: number): Promise<TranscriptItem[]> {
    const response = await this.api.get<TranscriptItem[]>(`/sessions/${sessionId}/transcripts`);
    return response.data;
  }

  async downloadTranscript(sessionId: number, type: 'source' | 'translation'): Promise<Blob> {
    const response = await this.api.get(`/sessions/${sessionId}/download/${type}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // 统计API
  async getStatistics(): Promise<Statistics> {
    const response = await this.api.get<Statistics>('/statistics');
    return response.data;
  }

  // 音频设备API
  async getAudioDevices(): Promise<AudioDevicesResponse> {
    const response = await this.api.get<AudioDevicesResponse>('/audio/devices');
    return response.data;
  }
}

export const apiService = new ApiService();
