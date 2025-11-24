// Web Speech API 语音识别 hook
// 用于在浏览器端进行语音识别，获取原文文字
import { useState, useRef, useCallback, useEffect } from 'react';

// Web Speech API 类型定义
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResultItem;
  [index: number]: SpeechRecognitionResultItem;
}

interface SpeechRecognitionResultItem {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export interface SpeechRecognitionResult {
  text: string;
  isFinal: boolean;
  timestamp: string;
}

interface UseSpeechRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (result: SpeechRecognitionResult) => void;
  onError?: (error: string) => void;
}

// 语言代码映射：我们的语言代码 -> Web Speech API 语言代码
const languageCodeMap: Record<string, string> = {
  'zh': 'zh-CN',
  'en': 'en-US',
  'ja': 'ja-JP',
  'ko': 'ko-KR',
  'ru': 'ru-RU',
  'fr': 'fr-FR',
  'de': 'de-DE',
  'pt': 'pt-BR',
  'es': 'es-ES',
  'it': 'it-IT',
  'yue': 'zh-HK', // 粤语
};

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const {
    language = 'zh',
    continuous = true,
    interimResults = true,
    onResult,
    onError,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const shouldRestartRef = useRef(false);

  // 检查浏览器支持
  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognitionAPI);
  }, []);

  // 初始化语音识别
  const initRecognition = useCallback(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      return null;
    }

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = languageCodeMap[language] || language;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('[SpeechRecognition] Started, language:', recognition.lang);
      setIsListening(true);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;

        if (result.isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      // 更新当前临时文本（用于显示正在识别的内容）
      setCurrentTranscript(interimTranscript);

      // 如果有最终结果，回调
      if (finalTranscript && onResult) {
        onResult({
          text: finalTranscript,
          isFinal: true,
          timestamp: new Date().toISOString(),
        });
        setCurrentTranscript('');
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('[SpeechRecognition] Error:', event.error, event.message);

      // 某些错误不需要停止（如 no-speech）
      if (event.error === 'no-speech') {
        // 没有检测到语音，继续监听
        return;
      }

      if (event.error === 'aborted') {
        // 被主动停止，不报错
        return;
      }

      if (onError) {
        onError(event.error);
      }
    };

    recognition.onend = () => {
      console.log('[SpeechRecognition] Ended, shouldRestart:', shouldRestartRef.current);
      setIsListening(false);

      // 如果应该继续监听（用户没有主动停止），则重新开始
      if (shouldRestartRef.current) {
        setTimeout(() => {
          if (shouldRestartRef.current && recognitionRef.current) {
            try {
              recognitionRef.current.start();
            } catch (e) {
              console.error('[SpeechRecognition] Restart failed:', e);
            }
          }
        }, 100);
      }
    };

    return recognition;
  }, [language, continuous, interimResults, onResult, onError]);

  // 开始监听
  const startListening = useCallback(() => {
    if (!isSupported) {
      console.error('[SpeechRecognition] Not supported in this browser');
      if (onError) {
        onError('Speech recognition is not supported in this browser');
      }
      return;
    }

    // 停止之前的实例
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        // ignore
      }
    }

    // 创建新实例
    const recognition = initRecognition();
    if (!recognition) {
      return;
    }

    recognitionRef.current = recognition;
    shouldRestartRef.current = true;

    try {
      recognition.start();
    } catch (e) {
      console.error('[SpeechRecognition] Start failed:', e);
      if (onError) {
        onError('Failed to start speech recognition');
      }
    }
  }, [isSupported, initRecognition, onError]);

  // 停止监听
  const stopListening = useCallback(() => {
    shouldRestartRef.current = false;
    setCurrentTranscript('');

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
      recognitionRef.current = null;
    }

    setIsListening(false);
  }, []);

  // 更新语言
  useEffect(() => {
    if (recognitionRef.current && isListening) {
      // 语言变化时，重新启动识别
      stopListening();
      setTimeout(() => {
        startListening();
      }, 100);
    }
  }, [language]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      shouldRestartRef.current = false;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // ignore
        }
      }
    };
  }, []);

  return {
    isListening,
    isSupported,
    currentTranscript,
    startListening,
    stopListening,
  };
}
