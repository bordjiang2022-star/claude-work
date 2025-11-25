import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import zh from './locales/zh.json';
import zhTW from './locales/zh-TW.json';
import ja from './locales/ja.json';
import ko from './locales/ko.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
      'zh-TW': { translation: zhTW },
      ja: { translation: ja },
      ko: { translation: ko },
    },
    lng: 'ja', // 默认语言
    fallbackLng: 'ja',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
