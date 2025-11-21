import { audioDeviceService } from './audioDevice';

// TTS服务 - 使用HTMLAudioElement + setSinkId实现音频设备路由
class TTSService {
  private enabled: boolean = true;
  private queue: Array<{ text: string; lang: string }> = [];
  private isSpeaking: boolean = false;
  private currentAudio: HTMLAudioElement | null = null;
  private useGoogleTTS: boolean = true; // 使用Google TTS API代替Web Speech API

  constructor() {
    console.log('[TTS] Service initialized with audio device routing');
  }

  /**
   * 设置TTS是否启用
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled;
    console.log('[TTS] Enabled:', enabled);
    if (!enabled) {
      this.stop();
    }
  }

  /**
   * 播放文本
   */
  speak(text: string, lang: string = 'en-US') {
    // 清理文本：去除换行符和多余空格
    const cleanText = text.replace(/\n/g, ' ').trim();

    if (!this.enabled) {
      console.log('[TTS] Skipped (disabled):', cleanText);
      return;
    }

    if (!cleanText) {
      console.log('[TTS] Skipped (empty text)');
      return;
    }

    console.log('[TTS] Queuing text:', cleanText, 'lang:', lang);

    // 添加到队列
    this.queue.push({ text: cleanText, lang });

    // 如果没有正在播放，开始播放
    if (!this.isSpeaking) {
      this.processQueue();
    }
  }

  /**
   * 处理播放队列
   */
  private async processQueue() {
    if (this.queue.length === 0) {
      this.isSpeaking = false;
      this.currentAudio = null;
      console.log('[TTS] Queue empty, stopped');
      return;
    }

    this.isSpeaking = true;
    const item = this.queue.shift()!;
    const { text, lang } = item;

    console.log('[TTS] Speaking:', text.substring(0, 50) + '...', 'lang:', lang);

    try {
      if (this.useGoogleTTS) {
        await this.speakWithGoogleTTS(text, lang);
      } else {
        await this.speakWithWebSpeech(text, lang);
      }
    } catch (error) {
      console.error('[TTS] Error:', error);
    }

    // 继续播放队列中的下一个
    this.processQueue();
  }

  /**
   * 使用Google TTS API播放（支持setSinkId）
   */
  private async speakWithGoogleTTS(text: string, lang: string): Promise<void> {
    return new Promise(async (resolve, reject) => {
      try {
        // 将语言代码转换为Google TTS格式（去掉地区代码）
        const langCode = lang.split('-')[0];

        // 使用后端代理来避免CORS问题
        // 文本长度限制：每次最多200字符
        const maxLength = 200;
        const chunks = this.splitTextIntoChunks(text, maxLength);

        // 获取后端API地址
        const isDev = window.location.port === '3000';
        const apiHost = isDev ? 'localhost:8000' : window.location.host;
        const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';

        for (let i = 0; i < chunks.length; i++) {
          const chunk = chunks[i];
          const encodedText = encodeURIComponent(chunk);
          // 使用后端代理端点
          const audioUrl = `${protocol}//${apiHost}/api/tts/proxy?text=${encodedText}&lang=${langCode}`;

          try {
            await this.playAudioUrl(audioUrl);
          } catch (audioError) {
            console.error('[TTS] Google TTS audio failed, falling back to Web Speech API:', audioError);
            // 如果 Google TTS 失败，回退到 Web Speech API
            await this.speakWithWebSpeech(chunk, lang);
          }
        }

        resolve();
      } catch (error) {
        console.error('[TTS] Google TTS error:', error);
        reject(error);
      }
    });
  }

  /**
   * 播放音频URL（使用指定的输出设备）
   */
  private async playAudioUrl(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log('[TTS] Loading audio from:', url);
      const audio = new Audio(url);
      this.currentAudio = audio;

      // 设置输出设备
      const deviceId = audioDeviceService.getSelectedOutputDeviceId();
      if (deviceId && audioDeviceService.supportsSinkId()) {
        (audio as any).setSinkId(deviceId)
          .then(() => {
            console.log('[TTS] Audio output set to:', audioDeviceService.getSelectedDeviceLabel());
          })
          .catch((err: any) => {
            console.warn('[TTS] Failed to set audio output device:', err);
          });
      } else {
        console.warn('[TTS] setSinkId not supported or no device selected');
      }

      // 添加加载进度监听
      audio.onloadstart = () => {
        console.log('[TTS] Audio loading started');
      };

      audio.onloadedmetadata = () => {
        console.log('[TTS] Audio metadata loaded');
      };

      audio.onloadeddata = () => {
        console.log('[TTS] Audio data loaded');
      };

      audio.oncanplay = () => {
        console.log('[TTS] Audio can play');
      };

      audio.oncanplaythrough = () => {
        console.log('[TTS] Audio ready, playing...');
        audio.play().catch(err => {
          console.error('[TTS] Failed to play:', err);
          reject(err);
        });
      };

      audio.onended = () => {
        console.log('[TTS] Audio finished');
        resolve();
      };

      audio.onerror = (err) => {
        console.error('[TTS] Audio error event:', err);
        console.error('[TTS] Audio error details:', {
          error: audio.error,
          code: audio.error?.code,
          message: audio.error?.message,
          networkState: audio.networkState,
          readyState: audio.readyState,
          src: audio.src
        });
        reject(new Error(`Audio load failed: ${audio.error?.message || 'Unknown error'}`));
      };
    });
  }

  /**
   * 将长文本分割成小块
   */
  private splitTextIntoChunks(text: string, maxLength: number): string[] {
    const chunks: string[] = [];
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];

    let currentChunk = '';
    for (const sentence of sentences) {
      if ((currentChunk + sentence).length <= maxLength) {
        currentChunk += sentence;
      } else {
        if (currentChunk) chunks.push(currentChunk.trim());
        currentChunk = sentence;
      }
    }
    if (currentChunk) chunks.push(currentChunk.trim());

    return chunks;
  }

  /**
   * 使用Web Speech API播放（备用方案，不支持setSinkId）
   */
  private async speakWithWebSpeech(text: string, lang: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      utterance.onend = () => {
        console.log('[TTS] Web Speech finished');
        resolve();
      };

      utterance.onerror = (event) => {
        console.error('[TTS] Web Speech error:', event.error);
        reject(event);
      };

      window.speechSynthesis.speak(utterance);
    });
  }

  /**
   * 停止播放
   */
  stop() {
    console.log('[TTS] Stopping all speech');

    // 停止当前音频
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    // 清空队列
    this.queue = [];
    this.isSpeaking = false;

    // 也停止Web Speech API（如果有在使用）
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  /**
   * 暂停播放
   */
  pause() {
    console.log('[TTS] Pausing');
    if (this.currentAudio) {
      this.currentAudio.pause();
    }
  }

  /**
   * 恢复播放
   */
  resume() {
    console.log('[TTS] Resuming');
    if (this.currentAudio) {
      this.currentAudio.play();
    }
  }

  /**
   * 设置是否使用Google TTS
   */
  setUseGoogleTTS(use: boolean) {
    this.useGoogleTTS = use;
    console.log('[TTS] Using Google TTS:', use);
  }

  /**
   * 获取可用的语音列表（仅用于Web Speech API）
   */
  getVoices(): SpeechSynthesisVoice[] {
    if (window.speechSynthesis) {
      const voices = window.speechSynthesis.getVoices();
      console.log('[TTS] Available voices:', voices.length);
      return voices;
    }
    return [];
  }

  /**
   * 根据目标语言获取推荐的语言代码
   */
  getLanguageCode(targetLanguage: string): string {
    const languageMap: Record<string, string> = {
      'en': 'en-US',
      'zh': 'zh-CN',
      'ja': 'ja-JP',
      'ko': 'ko-KR',
      'fr': 'fr-FR',
      'de': 'de-DE',
      'es': 'es-ES',
      'it': 'it-IT',
      'pt': 'pt-PT',
      'ru': 'ru-RU',
      'yue': 'zh-HK', // 粤语
    };
    return languageMap[targetLanguage] || 'en-US';
  }
}

export const ttsService = new TTSService();
