import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import apiService from '../services/api';

interface SessionRecord {
  id: number;
  source_language?: string;
  target_language: string;
  voice?: string;
  started_at: string;
  ended_at?: string;
  duration_seconds: number;
}

const HistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getSessions(100); // Get up to 100 sessions
      setSessions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    const parts = [];
    if (hours > 0) parts.push(`${hours}${t('history.hours')}`);
    if (minutes > 0) parts.push(`${minutes}${t('history.minutes')}`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}${t('history.seconds')}`);

    return parts.join(' ');
  };

  const filteredSessions = sessions.filter(session => {
    if (!fromDate && !toDate) return true;

    const sessionDate = new Date(session.started_at);
    const from = fromDate ? new Date(fromDate) : null;
    const to = toDate ? new Date(toDate) : null;

    if (from && sessionDate < from) return false;
    if (to) {
      const endOfDay = new Date(to);
      endOfDay.setHours(23, 59, 59, 999);
      if (sessionDate > endOfDay) return false;
    }

    return true;
  });

  const totalDuration = filteredSessions.reduce((sum, session) => sum + session.duration_seconds, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              {t('history.title')}
            </h1>

            {/* Date Range Filter */}
            <div className="mt-4 flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('history.from')}
                </label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('history.to')}
                </label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={() => { setFromDate(''); setToDate(''); }}
                className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition duration-200"
              >
                {t('common.cancel')}
              </button>
            </div>

            {/* Summary */}
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">{t('history.sessionCount')}</p>
                  <p className="text-2xl font-bold text-blue-600">{filteredSessions.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">{t('history.totalTime')}</p>
                  <p className="text-2xl font-bold text-blue-600">{formatDuration(totalDuration)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sessions Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">
                {t('common.loading')}
              </div>
            ) : error ? (
              <div className="p-8 text-center text-red-500">
                {t('common.error')}: {error}
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                {t('history.noRecords')}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('history.startTime')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('history.endTime')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('history.duration')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('history.targetLanguage')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredSessions.map((session) => (
                      <tr key={session.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {format(new Date(session.started_at), 'yyyy-MM-dd HH:mm:ss')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {session.ended_at
                            ? format(new Date(session.ended_at), 'yyyy-MM-dd HH:mm:ss')
                            : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDuration(session.duration_seconds)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {t(`languages.${session.target_language}`)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Back Button */}
          <div className="flex justify-center mt-6">
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

export default HistoryPage;
