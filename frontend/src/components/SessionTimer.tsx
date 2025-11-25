import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';

interface SessionTimerProps {
  isTranslating: boolean;
  sessionStartTime: Date | null;
}

const SessionTimer: React.FC<SessionTimerProps> = ({ isTranslating, sessionStartTime }) => {
  const { t } = useTranslation();
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (!isTranslating || !sessionStartTime) {
      return;
    }

    // Update elapsed time every second
    const interval = setInterval(() => {
      const now = new Date();
      const elapsed = Math.floor((now.getTime() - sessionStartTime.getTime()) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [isTranslating, sessionStartTime]);

  const formatElapsedTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}${t('history.hours')}`);
    parts.push(`${minutes}${t('history.minutes')}`);
    parts.push(`${secs}${t('history.seconds')}`);

    return parts.join(' ');
  };

  // 只在翻译中且有开始时间时显示计时器
  if (!isTranslating || !sessionStartTime) {
    return null;
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">{t('translation.sessionElapsedTime')}</p>
          <p className="text-2xl font-semibold text-green-700">
            {formatElapsedTime(elapsedTime)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SessionTimer;
