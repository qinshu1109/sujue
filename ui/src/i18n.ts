import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import zhCN from './locales/zh_CN';
import enUS from './locales/en_US';

const resources = {
  zh: {
    translation: zhCN
  },
  en: {
    translation: enUS
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('i18nextLng') || 'zh', // 从localStorage读取语言设置
    fallbackLng: 'zh',
    interpolation: {
      escapeValue: false
    },
    react: {
      useSuspense: true  // 启用Suspense避免闪烁
    },
    // 语言检测配置
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage']
    }
  });

export default i18n;