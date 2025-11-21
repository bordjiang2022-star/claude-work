// Web Speech API TTS服务
class TTSService {
  private synthesis: SpeechSynthesis;
  private enabled: boolean = true;
  private queue: string[] = [];
  private isSpeaking: boolean = false;

  constructor() {
    this.synthesis = window.speechSynthesis;
    console.log('[TTS] Service initialized');
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
    this.queue.push(cleanText);

    // 如果没有正在播放，开始播放
    if (!this.isSpeaking) {
      this.processQueue(lang);
    }
  }

  /**
   * 处理播放队列
   */
  private processQueue(lang: string) {
    if (this.queue.length === 0) {
      this.isSpeaking = false;
      console.log('[TTS] Queue empty, stopped');
      return;
    }

    this.isSpeaking = true;
    const text = this.queue.shift()!;

    console.log('[TTS] Speaking:', text.substring(0, 50) + '...', 'lang:', lang);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1.0; // 语速
    utterance.pitch = 1.0; // 音调
    utterance.volume = 1.0; // 音量

    // 尝试使用本地语音（更可靠，避免在线TTS的问题）
    const voices = this.synthesis.getVoices();
    const localVoice = voices.find(v => v.lang.startsWith(lang.split('-')[0]) && v.localService);
    if (localVoice) {
      utterance.voice = localVoice;
      console.log('[TTS] Using LOCAL voice:', localVoice.name);
    } else {
      console.log('[TTS] No local voice found, using default');
    }

    utterance.onstart = () => {
      console.log('[TTS] Started speaking');
    };

    utterance.onend = () => {
      console.log('[TTS] Finished speaking');
      // 继续播放队列中的下一个
      this.processQueue(lang);
    };

    utterance.onerror = (event) => {
      console.error('[TTS] Error:', event.error, event);
      // 出错时也要继续播放队列
      this.processQueue(lang);
    };

    // 使用setTimeout确保在用户交互后执行
    setTimeout(() => {
      this.synthesis.speak(utterance);
      console.log('[TTS] Synthesis.speak() called');
    }, 100);
  }

  /**
   * 停止播放
   */
  stop() {
    console.log('[TTS] Stopping all speech');
    this.synthesis.cancel();
    this.queue = [];
    this.isSpeaking = false;
  }

  /**
   * 暂停播放
   */
  pause() {
    console.log('[TTS] Pausing');
    this.synthesis.pause();
  }

  /**
   * 恢复播放
   */
  resume() {
    console.log('[TTS] Resuming');
    this.synthesis.resume();
  }

  /**
   * 获取可用的语音列表
   */
  getVoices(): SpeechSynthesisVoice[] {
    const voices = this.synthesis.getVoices();
    console.log('[TTS] Available voices:', voices.length);
    return voices;
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
