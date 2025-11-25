import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTranslationStore } from '../hooks/useTranslationStore';
import LanguageSelector from '../components/LanguageSelector';
import AudioDeviceSelector from '../components/AudioDeviceSelector';

const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { config, updateConfig } = useTranslationStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              {t('settings.title')}
            </h1>
            <p className="text-gray-600">
              {t('translation.settings')}
            </p>
          </div>

          {/* TTS Settings Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
              {t('settings.ttsSettings')}
            </h2>
            <LanguageSelector />
          </div>

          {/* Audio Device Settings Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
              {t('settings.audioDevice')}
            </h2>
            <AudioDeviceSelector />
          </div>

          {/* Back Button */}
          <div className="flex justify-center">
            <button
              onClick={() => window.history.back()}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition duration-200 shadow-md"
            >
              {t('common.close')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
