// Web Speech API TTS服务
class TTSService {
  private synthesis: SpeechSynthesis;
  private enabled: boolean = true;
  private queue: string[] = [];
  private isSpeaking: boolean = false;

  constructor() {
    this.synthesis = window.speechSynthesis;
  }

  /**
   * 设置TTS是否启用
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled;
    if (!enabled) {
      this.stop();
    }
  }

  /**
   * 播放文本
   */
  speak(text: string, lang: string = 'en-US') {
    if (!this.enabled || !text.trim()) {
      return;
    }

    // 添加到队列
    this.queue.push(text.trim());

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
      return;
    }

    this.isSpeaking = true;
    const text = this.queue.shift()!;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1.0; // 语速
    utterance.pitch = 1.0; // 音调
    utterance.volume = 1.0; // 音量

    utterance.onend = () => {
      // 继续播放队列中的下一个
      this.processQueue(lang);
    };

    utterance.onerror = (event) => {
      console.error('[TTS] Error:', event);
      // 出错时也要继续播放队列
      this.processQueue(lang);
    };

    this.synthesis.speak(utterance);
  }

  /**
   * 停止播放
   */
  stop() {
    this.synthesis.cancel();
    this.queue = [];
    this.isSpeaking = false;
  }

  /**
   * 暂停播放
   */
  pause() {
    this.synthesis.pause();
  }

  /**
   * 恢复播放
   */
  resume() {
    this.synthesis.resume();
  }

  /**
   * 获取可用的语音列表
   */
  getVoices(): SpeechSynthesisVoice[] {
    return this.synthesis.getVoices();
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
