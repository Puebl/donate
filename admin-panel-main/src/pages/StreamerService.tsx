import React, { useState, useEffect } from 'react';
import { VideoCameraIcon, ArrowPathIcon, MagnifyingGlassIcon, UserCircleIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../api/client';
import { useDebounce } from '../hooks/useDebounce';
import { 
  ServiceHealth, 
  ServiceStats, 
  TableColumn,
  AccountItem,
  AccountsResponse,
  AccountsFilter,
  StreamerTodayStats
} from '../types';
import DataTable from '../components/DataTable';

const StreamerService: React.FC = () => {
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [stats, setStats] = useState<ServiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Accounts state
  const [accountsData, setAccountsData] = useState<AccountsResponse | null>(null);
  const [accountsFilters, setAccountsFilters] = useState<AccountsFilter>({});
  const debouncedSearch = useDebounce(accountsFilters.search, 300);
  const [accountsPage, setAccountsPage] = useState(1);
  const [accountsLoading, setAccountsLoading] = useState(false);

  // Today stats state
  const [todayStats, setTodayStats] = useState<StreamerTodayStats | null>(null);
  const [todayStatsLoading, setTodayStatsLoading] = useState(false);

  useEffect(() => {
    fetchServiceData();
    const interval = setInterval(fetchServiceData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [debouncedSearch, accountsFilters.is_active, accountsPage]);

  useEffect(() => {
    fetchTodayStats();
  }, []);

  const fetchServiceData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statsData] = await Promise.all([
        apiClient.getServiceHealth('streamer'),
        apiClient.getServiceStats('streamer'),
      ]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service data');
      console.error('Error fetching streamer service data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      setAccountsLoading(true);
      const filtersToUse = { ...accountsFilters, search: debouncedSearch };
      const data = await apiClient.getAccounts(filtersToUse, accountsPage, 20);
      setAccountsData(data);
    } catch (err) {
      console.error('Error fetching accounts:', err);
    } finally {
      setAccountsLoading(false);
    }
  };

  const fetchTodayStats = async () => {
    try {
      setTodayStatsLoading(true);
      const data = await apiClient.getStreamerTodayStats();
      setTodayStats(data);
    } catch (err) {
      console.error('Error fetching today stats:', err);
    } finally {
      setTodayStatsLoading(false);
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

  const accountsColumns: TableColumn<AccountItem>[] = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'login', label: 'Логин', sortable: true },
    { 
      key: 'avatar', 
      label: 'Аватар', 
      sortable: false,
      render: (value) => (
        <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-700 flex items-center justify-center">
          {value ? (
            <img 
              src={value} 
              alt="Аватар" 
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling?.classList.remove('hidden');
              }}
            />
          ) : null}
          <UserCircleIcon className="h-6 w-6 text-gray-400 hidden" />
        </div>
      )
    },
    { key: 'email', label: 'Email', sortable: true },
    { 
      key: 'is_active', 
      label: 'Статус', 
      sortable: true,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          value 
            ? 'bg-green-100 text-green-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {value ? 'Активен' : 'Неактивен'}
        </span>
      )
    },
    { 
      key: 'vk_enabled', 
      label: 'VK', 
      sortable: true,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          value 
            ? 'bg-blue-100 text-blue-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {value ? 'Вкл' : 'Выкл'}
        </span>
      )
    },
    { 
      key: 'google_enabled', 
      label: 'Google', 
      sortable: true,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          value 
            ? 'bg-green-100 text-green-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {value ? 'Вкл' : 'Выкл'}
        </span>
      )
    },
    { 
      key: 'twitch_enabled', 
      label: 'Twitch', 
      sortable: true,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
          value 
            ? 'bg-purple-100 text-purple-800' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          {value ? 'Вкл' : 'Выкл'}
        </span>
      )
    },
    { 
      key: 'created_at', 
      label: 'Создан', 
      sortable: true,
      render: (value) => new Date(value).toLocaleString('ru-RU')
    },
    { 
      key: 'updated_at', 
      label: 'Обновлён', 
      sortable: true,
      render: (value) => new Date(value).toLocaleString('ru-RU')
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gray-800 rounded-lg">
            <VideoCameraIcon className="h-8 w-8 text-red-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Стримеры</h1>
            <p className="text-gray-400 mt-1">Управление аккаунтами стримеров</p>
          </div>
        </div>
        <button
          onClick={fetchServiceData}
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

      {/* Today Stats Card */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Статистика за сегодня</h3>
        {todayStatsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            <span className="ml-3 text-gray-400">Загрузка статистики...</span>
          </div>
        ) : todayStats ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-400 mb-2">Новые регистрации</h4>
              <div className="text-2xl font-bold text-green-400">{todayStats.new_registrations.toLocaleString('ru-RU')}</div>
              <div className="text-sm text-gray-500">Зарегистрировалось сегодня</div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            Нет статистики за сегодня
          </div>
        )}
      </div>

      {/* Accounts Section */}
      <div className="space-y-4">
        {/* Filters */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Фильтры</h3>
            {(accountsFilters.search || accountsFilters.is_active !== undefined) && (
              <button
                onClick={() => {
                  setAccountsFilters({});
                  setAccountsPage(1);
                }}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <FunnelIcon className="h-4 w-4" />
                Сбросить
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Поиск</label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={accountsFilters.search || ''}
                  onChange={(e) => {
                    setAccountsFilters(prev => ({ ...prev, search: e.target.value }));
                    setAccountsPage(1);
                  }}
                  placeholder="Поиск по логину или email..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Статус</label>
              <select
                value={accountsFilters.is_active === undefined ? 'all' : accountsFilters.is_active.toString()}
                onChange={(e) => {
                  const value = e.target.value;
                  setAccountsFilters(prev => ({ 
                    ...prev, 
                    is_active: value === 'all' ? undefined : value === 'true'
                  }));
                  setAccountsPage(1);
                }}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">Все</option>
                <option value="true">Активные</option>
                <option value="false">Неактивные</option>
              </select>
            </div>
          </div>
        </div>

        {/* Accounts Table */}
        <DataTable
          data={accountsData?.items || []}
          columns={accountsColumns}
          loading={accountsLoading}
          pagination={accountsData ? {
            page: accountsData.page,
            limit: accountsData.page_size,
            total: accountsData.total,
            totalPages: accountsData.pages
          } : undefined}
          onPageChange={setAccountsPage}
          emptyMessage="Аккаунты не найдены"
        />
      </div>

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
            <span className="text-white font-medium">Стримеры</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">База данных</span>
            <span className="text-white font-medium">PostgreSQL</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Порт</span>
            <span className="text-white font-medium">9004</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-400">Таблицы</span>
            <span className="text-white font-medium">Аккаунты стримеров</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamerService;