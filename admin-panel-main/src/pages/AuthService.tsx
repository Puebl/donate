import React, { useState, useEffect } from 'react';
import { UserIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../api/client';
import { ServiceHealth, ServiceStats } from '../types';

const AuthService: React.FC = () => {
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [stats, setStats] = useState<ServiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statsData] = await Promise.all([
        apiClient.getServiceHealth('auth'),
        apiClient.getServiceStats('auth'),
      ]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service data');
      console.error('Error fetching auth service data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-400 bg-green-900/20 border-green-800';
      case 'degraded':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-800';
      case 'unhealthy':
        return 'text-red-400 bg-red-900/20 border-red-800';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gray-800 rounded-lg">
            <UserIcon className="h-8 w-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Авторизация</h1>
            <p className="text-gray-400 mt-1">Управление пользователями, API-ключами и токенами</p>
          </div>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="btn-secondary disabled:opacity-50 flex items-center gap-2"
        >
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Обновление...' : 'Обновить'}
        </button>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Health Status Card */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Статус сервиса</h3>
          {health ? (
            <div className={`px-4 py-3 rounded-lg border ${getStatusColor(health.status)}`}>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold uppercase">{health.status}</span>
                <span className="text-2xl">
                  {health.status === 'healthy' ? '✓' : health.status === 'degraded' ? '⚠' : '✗'}
                </span>
              </div>
              {health.message && (
                <p className="text-sm mt-2 opacity-80">{health.message}</p>
              )}
              <p className="text-xs mt-2 opacity-60">
                Проверено: {new Date(health.timestamp).toLocaleString('ru-RU')}
              </p>
            </div>
          ) : (
            <div className="text-gray-500">Загрузка...</div>
          )}
        </div>

        {/* Total Requests Card */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Всего запросов</h3>
          <div className="text-3xl font-bold text-white">
            {stats?.total_requests?.toLocaleString('ru-RU') || '0'}
          </div>
          <p className="text-sm text-gray-500 mt-1">За всё время</p>
        </div>

        {/* Success Rate Card */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Успешность</h3>
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold text-white">
              {stats?.success_rate?.toFixed(1) || '0'}%
            </div>
            <div className={`text-sm ${
              (stats?.success_rate || 0) >= 95 ? 'text-green-400' :
              (stats?.success_rate || 0) >= 90 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {(stats?.success_rate || 0) >= 95 ? 'Отлично' :
               (stats?.success_rate || 0) >= 90 ? 'Хорошо' : 'Требует внимания'}
            </div>
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      {stats && (
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Метрики сервиса</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.active_users !== undefined && (
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-400 mb-1">Активных пользователей</p>
                <p className="text-2xl font-bold text-white">{stats.active_users.toLocaleString('ru-RU')}</p>
              </div>
            )}
            {stats.average_response_time !== undefined && (
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-400 mb-1">Среднее время ответа</p>
                <p className="text-2xl font-bold text-white">{stats.average_response_time.toFixed(0)} мс</p>
              </div>
            )}
            {stats.uptime !== undefined && (
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-400 mb-1">Аптайм</p>
                <p className="text-2xl font-bold text-white">{stats.uptime.toFixed(2)}%</p>
              </div>
            )}
            {stats.error_count !== undefined && (
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-400 mb-1">Кол-во ошибок</p>
                <p className="text-2xl font-bold text-white">{stats.error_count.toLocaleString('ru-RU')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="card bg-red-900/20 border-red-800">
          <div className="flex items-center gap-3 text-red-400">
            <span className="text-2xl">⚠</span>
            <div>
              <h3 className="font-semibold">Ошибка загрузки данных</h3>
              <p className="text-sm text-gray-400">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Database Info */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Информация о базе данных</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Сервис</span>
            <span className="text-white font-medium">Авторизация</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">База данных</span>
            <span className="text-white font-medium">PostgreSQL</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Режим сети</span>
            <span className="text-white font-medium">host</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-400">Таблицы</span>
            <span className="text-white font-medium">Пользователи, API-ключи, Токены</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthService;
