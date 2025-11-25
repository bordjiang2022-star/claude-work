// 顶部导航栏组件
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/hooks/useAuthStore';
import type { Language } from '@/types';

export const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLangMenu, setShowLangMenu] = useState(false);

  const languages: { code: Language; label: string }[] = [
    { code: 'en', label: 'English' },
    { code: 'zh', label: '简体中文' },
    { code: 'zh-TW', label: '繁體中文' },
    { code: 'ja', label: '日本語' },
    { code: 'ko', label: '한국어' },
  ];

  const changeLanguage = (lang: Language) => {
    i18n.changeLanguage(lang);
    setShowLangMenu(false);
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="bg-primary-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <img src="/MyIcon.png" alt="LiveTranslate" className="w-12 h-12 mr-3" />
            <div>
              <h1 className="text-2xl font-bold">{t('app.title')}</h1>
              <p className="text-sm text-primary-100">{t('app.subtitle')}</p>
            </div>
          </div>

          {/* 右侧菜单 */}
          <div className="flex items-center space-x-4">
            {/* 导航菜单 */}
            <nav className="flex items-center space-x-2">
              <button
                onClick={() => navigate('/')}
                className={`px-4 py-2 rounded-lg transition ${
                  location.pathname === '/'
                    ? 'bg-primary-700 font-semibold'
                    : 'hover:bg-primary-500'
                }`}
              >
                {t('app.title')}
              </button>
              <button
                onClick={() => navigate('/settings')}
                className={`px-4 py-2 rounded-lg transition ${
                  location.pathname === '/settings'
                    ? 'bg-primary-700 font-semibold'
                    : 'hover:bg-primary-500'
                }`}
              >
                {t('settings.title')}
              </button>
              <button
                onClick={() => navigate('/history')}
                className={`px-4 py-2 rounded-lg transition ${
                  location.pathname === '/history'
                    ? 'bg-primary-700 font-semibold'
                    : 'hover:bg-primary-500'
                }`}
              >
                {t('history.menuTitle')}
              </button>
            </nav>

            {/* 语言切换 */}
            <div className="relative">
              <button
                onClick={() => setShowLangMenu(!showLangMenu)}
                className="px-4 py-2 bg-primary-500 hover:bg-primary-700 rounded-lg transition"
              >
                🌍 {languages.find((l) => l.code === i18n.language)?.label || 'English'}
              </button>

              {showLangMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl z-50">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => changeLanguage(lang.code)}
                      className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-primary-50 first:rounded-t-lg last:rounded-b-lg"
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 用户信息 */}
            <div className="flex items-center space-x-2">
              <span className="text-sm">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg transition"
              >
                {t('auth.logout')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
