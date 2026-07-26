import React, { useState, useEffect, useCallback } from 'react';
import { ChartBarIcon, ArrowPathIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useDebounce } from '../hooks/useDebounce';
import {
  StatisticsFilter,
  StatisticsSummary,
  StatisticsTimeseries,
  BreakdownItem,
  TopStreamerItem,
  TimeseriesPoint,
  TableColumn,
} from '../types';
import DataTable from '../components/DataTable';

type PeriodPreset = 'today' | 'yesterday' | 'week' | 'month' | 'year' | 'all';
type Grouping = 'day' | 'week' | 'month' | 'year';

const OPERATION_TYPE_OPTIONS: { label: string; value: string }[] = [
  { label: 'Все', value: '' },
  { label: 'Пополнение СБП', value: 't_deposit_sbp' },
  { label: 'Пополнение карта', value: 't_deposit_card' },
  { label: 'Вывод СБП', value: 't_withdraw_sbp' },
  { label: 'Вывод карта', value: 't_withdraw_card' },
  { label: 'Комиссия пополнения СБП', value: 't_deposit_sbp_fee' },
  { label: 'Комиссия пополнения карта', value: 't_deposit_card_fee' },
  { label: 'Комиссия вывода СБП', value: 't_withdraw_sbp_fee' },
  { label: 'Комиссия вывода карта', value: 't_withdraw_card_fee' },
];

const PAYMENT_PROVIDER_OPTIONS: { label: string; value: string }[] = [
  { label: 'Все', value: '' },
  { label: 'Tinkoff', value: 'tinkoff' },
  { label: 'Oxypay', value: 'oxypay' },
];

const STATUS_OPTIONS: { label: string; value: string }[] = [
  { label: 'Все', value: '' },
  { label: 'Завершено', value: 'completed' },
  { label: 'В обработке', value: 'pending' },
  { label: 'Ошибка', value: 'failed' },
];

const PERIOD_PRESETS: { key: PeriodPreset; label: string }[] = [
  { key: 'today', label: 'Сегодня' },
  { key: 'yesterday', label: 'Вчера' },
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
  { key: 'year', label: 'Год' },
  { key: 'all', label: 'Всё время' },
];

const GROUPING_OPTIONS: { key: Grouping; label: string }[] = [
  { key: 'day', label: 'День' },
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
  { key: 'year', label: 'Год' },
];

const formatAmount = (kopecks: number): string =>
  `${(kopecks / 100).toLocaleString('ru-RU')} ₽`;

const toISODate = (d: Date): string => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getPresetDates = (preset: PeriodPreset): { date_from?: string; date_to?: string } => {
  const now = new Date();
  const today = toISODate(now);

  switch (preset) {
    case 'today':
      return { date_from: today, date_to: today };
    case 'yesterday': {
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      const yd = toISODate(yesterday);
      return { date_from: yd, date_to: yd };
    }
    case 'week': {
      const dayOfWeek = now.getDay();
      const diffToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
      const monday = new Date(now);
      monday.setDate(monday.getDate() - diffToMonday);
      return { date_from: toISODate(monday), date_to: today };
    }
    case 'month': {
      const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      return { date_from: toISODate(firstOfMonth), date_to: today };
    }
    case 'year': {
      const firstOfYear = new Date(now.getFullYear(), 0, 1);
      return { date_from: toISODate(firstOfYear), date_to: today };
    }
    case 'all':
      return { date_from: undefined, date_to: undefined };
  }
};

const StatisticsPage: React.FC = () => {
  const { showToast } = useToast();

  const [filter, setFilter] = useState<StatisticsFilter>({ grouping: 'day' });
  const [summary, setSummary] = useState<StatisticsSummary | null>(null);
  const [timeseries, setTimeseries] = useState<StatisticsTimeseries | null>(null);
  const [loading, setLoading] = useState(true);
  const [tablePage, setTablePage] = useState(1);

  const [activePreset, setActivePreset] = useState<PeriodPreset>('all');
  const [customDateFrom, setCustomDateFrom] = useState('');
  const [customDateTo, setCustomDateTo] = useState('');
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [streamerIdInput, setStreamerIdInput] = useState('');
  const debouncedStreamerId = useDebounce(streamerIdInput, 500);

  const [hoveredBar, setHoveredBar] = useState<number | null>(null);

  useEffect(() => {
    if (debouncedStreamerId) {
      const parsed = parseInt(debouncedStreamerId, 10);
      if (!isNaN(parsed) && parsed > 0) {
        setFilter(prev => ({ ...prev, streamer_id: parsed }));
      }
    } else {
      setFilter(prev => {
        const next = { ...prev };
        delete next.streamer_id;
        return next;
      });
    }
  }, [debouncedStreamerId]);

  const fetchData = useCallback(async (currentFilter: StatisticsFilter, page: number) => {
    try {
      setLoading(true);
      const [summaryData, timeseriesData] = await Promise.all([
        apiClient.getStatisticsSummary(currentFilter, page, 20),
        apiClient.getStatisticsTimeseries(currentFilter),
      ]);
      setSummary(summaryData);
      setTimeseries(timeseriesData);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      showToast('error', 'Ошибка загрузки статистики');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchData(filter, tablePage);
  }, [filter, tablePage, fetchData]);

  const handlePresetClick = (preset: PeriodPreset) => {
    setActivePreset(preset);
    const dates = getPresetDates(preset);
    setCustomDateFrom(dates.date_from || '');
    setCustomDateTo(dates.date_to || '');
    setTablePage(1);
    setFilter(prev => ({
      ...prev,
      date_from: dates.date_from,
      date_to: dates.date_to,
    }));
  };

  const handleCustomDateChange = (field: 'date_from' | 'date_to', value: string) => {
    if (field === 'date_from') {
      setCustomDateFrom(value);
    } else {
      setCustomDateTo(value);
    }
    setActivePreset(undefined as unknown as PeriodPreset);
    setTablePage(1);
    setFilter(prev => ({
      ...prev,
      [field]: value || undefined,
    }));
  };

  const handleGroupingChange = (grouping: Grouping) => {
    setTablePage(1);
    setFilter(prev => ({ ...prev, grouping }));
  };

  const handleFilterChange = (key: keyof StatisticsFilter, value: string) => {
    setTablePage(1);
    setFilter(prev => ({
      ...prev,
      [key]: value || undefined,
    }));
  };

  const hasActiveFilters =
    !!filter.operation_type ||
    !!filter.payment_provider ||
    !!filter.status ||
    !!filter.streamer_id;

  const handleResetFilters = () => {
    setFilter(prev => ({
      date_from: prev.date_from,
      date_to: prev.date_to,
      grouping: prev.grouping,
    }));
    setStreamerIdInput('');
    setTablePage(1);
  };

  const handleRefresh = () => {
    fetchData(filter, tablePage);
  };

  const formatPeriod = (isoString: string): string => {
    const d = new Date(isoString);
    if (filter.grouping === 'year') return d.getFullYear().toString();
    if (filter.grouping === 'month')
      return d.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
    if (filter.grouping === 'week')
      return `${d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })} нед.`;
    return d.toLocaleDateString('ru-RU');
  };

  const renderBreakdownChart = (data: BreakdownItem[], title: string) => {
    const maxValue = Math.max(...data.map(d => d.count), 1);
    const totalCount = data.reduce((sum, d) => sum + d.count, 0);
    const totalAmount = data.reduce((sum, d) => sum + d.amount, 0);

    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-300">{title}</h4>
          <div className="text-xs text-gray-500">
            Всего: {totalCount.toLocaleString('ru-RU')} · {formatAmount(totalAmount)}
          </div>
        </div>
        <div className="space-y-2">
          {data.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-4">Нет данных</div>
          ) : (
            data.map((item) => (
              <div key={item.key} className="group relative">
                <div className="flex items-center gap-2">
                  <div className="w-28 text-xs text-gray-400 truncate" title={item.key}>
                    {item.key}
                  </div>
                  <div className="flex-1 bg-gray-700 rounded-full h-7 relative overflow-hidden">
                    <div
                      className="bg-blue-500 hover:bg-blue-400 h-full rounded-full transition-all duration-300"
                      style={{ width: `${maxValue > 0 ? (item.count / maxValue) * 100 : 0}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-between px-3 text-xs">
                      <span className="text-white font-medium">
                        {item.count.toLocaleString('ru-RU')}
                      </span>
                      <span className="text-gray-300">{formatAmount(item.amount)}</span>
                    </div>
                  </div>
                </div>
                <div className="absolute left-32 -top-8 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                  <div className="font-medium mb-1">{item.key}</div>
                  <div>Кол-во: {item.count.toLocaleString('ru-RU')}</div>
                  <div>Сумма: {formatAmount(item.amount)}</div>
                  <div>
                    Доля: {totalCount > 0 ? ((item.count / totalCount) * 100).toFixed(1) : 0}%
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderTimeseriesChart = (points: TimeseriesPoint[]) => {
    if (points.length === 0) {
      return (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Объём транзакций</h4>
          <div className="text-sm text-gray-500 text-center py-8">Нет данных за выбранный период</div>
        </div>
      );
    }

    const maxAmount = Math.max(...points.map(p => p.total_amount), 1);
    const totalAmount = points.reduce((sum, p) => sum + p.total_amount, 0);
    const totalCommission = points.reduce((sum, p) => sum + p.commission_amount, 0);

    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-300">Объём транзакций</h4>
          <div className="text-xs text-gray-500">
            Объём: {formatAmount(totalAmount)} · Комиссия: {formatAmount(totalCommission)}
          </div>
        </div>
        <div className="flex items-end gap-1 h-48">
          {points.map((point, idx) => {
            const barHeight = (point.total_amount / maxAmount) * 100;
            const commissionHeight =
              point.total_amount > 0
                ? (point.commission_amount / point.total_amount) * barHeight
                : 0;
            const isHovered = hoveredBar === idx;

            return (
              <div
                key={point.period}
                className="group flex-1 flex flex-col items-center relative"
                onMouseEnter={() => setHoveredBar(idx)}
                onMouseLeave={() => setHoveredBar(null)}
              >
                <div className="w-full relative" style={{ height: '192px' }}>
                  <div
                    className="absolute bottom-0 w-full bg-blue-500 hover:bg-blue-400 rounded-t transition-all duration-300 cursor-pointer"
                    style={{
                      height: `${barHeight}%`,
                      minHeight: point.total_amount > 0 ? '4px' : '2px',
                      backgroundColor: point.total_amount === 0 ? '#374151' : undefined,
                    }}
                  >
                    {commissionHeight > 0 && (
                      <div
                        className="absolute bottom-0 w-full bg-green-500 rounded-t opacity-70"
                        style={{ height: `${(point.commission_amount / point.total_amount) * 100}%` }}
                      />
                    )}
                  </div>
                </div>
                {points.length <= 31 && (
                  <div className="text-[9px] text-gray-500 mt-1 truncate w-full text-center">
                    {formatPeriod(point.period)}
                  </div>
                )}
                {isHovered && (
                  <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white shadow-lg z-10 pointer-events-none whitespace-nowrap">
                    <div className="font-medium mb-1">{formatPeriod(point.period)}</div>
                    <div>Транзакций: {point.transaction_count.toLocaleString('ru-RU')}</div>
                    <div>Объём: {formatAmount(point.total_amount)}</div>
                    <div>Комиссия: {formatAmount(point.commission_amount)}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-blue-500" />
            <span>Объём</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-green-500 opacity-70" />
            <span>Комиссия</span>
          </div>
        </div>
      </div>
    );
  };

  const tableColumns: TableColumn<TimeseriesPoint>[] = [
    {
      key: 'period',
      label: 'Период',
      render: (v: string) => formatPeriod(v),
    },
    {
      key: 'transaction_count',
      label: 'Транзакций',
      render: (v: number) => v.toLocaleString('ru-RU'),
    },
    {
      key: 'total_amount',
      label: 'Объём',
      render: (v: number) => formatAmount(v),
    },
    {
      key: 'commission_amount',
      label: 'Комиссия',
      render: (v: number) => formatAmount(v),
    },
    {
      key: 'donat_count',
      label: 'Донатов',
      render: (v: number) => v.toLocaleString('ru-RU'),
    },
    {
      key: 'donat_amount',
      label: 'Сумма донатов',
      render: (v: number) => formatAmount(v),
    },
    {
      key: 'avg_transaction',
      label: 'Средний чек',
      render: (v: number) => formatAmount(v),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gray-800 rounded-lg">
            <ChartBarIcon className="h-8 w-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Статистика</h1>
            <p className="text-gray-400 mt-1">Финансовая аналитика по всем сервисам</p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="btn-secondary disabled:opacity-50 flex items-center gap-2"
        >
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Обновление...' : 'Обновить'}
        </button>
      </div>

      {/* 2. Period Selection */}
      <div className="card">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-400 mr-1">Период:</span>
            {PERIOD_PRESETS.map((preset) => (
              <button
                key={preset.key}
                onClick={() => handlePresetClick(preset.key)}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors duration-200 ${
                  activePreset === preset.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                }`}
              >
                {preset.label}
              </button>
            ))}

            <div className="flex items-center gap-2 ml-4">
              <input
                type="date"
                value={customDateFrom}
                onChange={(e) => handleCustomDateChange('date_from', e.target.value)}
                className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-500">—</span>
              <input
                type="date"
                value={customDateTo}
                onChange={(e) => handleCustomDateChange('date_to', e.target.value)}
                className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-400 mr-1">Группировка:</span>
            {GROUPING_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => handleGroupingChange(opt.key)}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors duration-200 ${
                  filter.grouping === opt.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Filters Card (collapsible) */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            <FunnelIcon className="h-4 w-4" />
            Фильтры
            <svg
              className={`h-4 w-4 transition-transform duration-200 ${filtersExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Сбросить
            </button>
          )}
        </div>

        {filtersExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Тип операции</label>
              <select
                value={filter.operation_type || ''}
                onChange={(e) => handleFilterChange('operation_type', e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {OPERATION_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Платёжная система
              </label>
              <select
                value={filter.payment_provider || ''}
                onChange={(e) => handleFilterChange('payment_provider', e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {PAYMENT_PROVIDER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Статус</label>
              <select
                value={filter.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">ID стримера</label>
              <input
                type="number"
                value={streamerIdInput}
                onChange={(e) => setStreamerIdInput(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Введите ID"
              />
            </div>
          </div>
        )}
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            <span className="ml-3 text-gray-400">Загрузка статистики...</span>
          </div>
        </div>
      ) : summary ? (
        <>
          {/* 4. Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Общий объём</h3>
              <div className="text-2xl font-bold text-white">
                {formatAmount(summary.total_volume)}
              </div>
              <div className="text-sm text-gray-500">
                {summary.total_volume_count.toLocaleString('ru-RU')} операций
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Комиссия</h3>
              <div className="text-2xl font-bold text-green-400">
                {formatAmount(summary.total_commission)}
              </div>
              <div className="text-sm text-gray-500">
                {summary.total_commission_count.toLocaleString('ru-RU')} операций
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Донаты</h3>
              <div className="text-2xl font-bold text-blue-400">
                {formatAmount(summary.total_donats_amount)}
              </div>
              <div className="text-sm text-gray-500">
                {summary.total_donats_count.toLocaleString('ru-RU')} операций
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Выводы</h3>
              <div className="text-2xl font-bold text-yellow-400">
                {formatAmount(summary.total_withdrawals_amount)}
              </div>
              <div className="text-sm text-gray-500">
                {summary.total_withdrawals_count.toLocaleString('ru-RU')} операций
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Уникальные стримеры</h3>
              <div className="text-2xl font-bold text-purple-400">
                {summary.unique_streamers.toLocaleString('ru-RU')}
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Новые стримеры</h3>
              <div className="text-2xl font-bold text-cyan-400">
                {summary.new_streamers.toLocaleString('ru-RU')}
              </div>
            </div>
          </div>

          {/* 5. Timeseries Chart */}
          {timeseries && renderTimeseriesChart(timeseries.points)}

          {/* 6. Breakdown Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {renderBreakdownChart(summary.by_operation_type, 'По типу операции')}
            {renderBreakdownChart(summary.by_payment_provider, 'По платёжной системе')}
            {renderBreakdownChart(summary.by_status, 'По статусу')}
          </div>

          {/* 7. Top Streamers Table */}
          {summary.top_streamers.length > 0 && (
            <div className="card overflow-hidden">
              <h3 className="text-lg font-semibold text-white mb-4">Топ стримеров</h3>
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Логин
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Транзакций
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Объём
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Комиссия
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {summary.top_streamers.slice(0, 10).map((streamer: TopStreamerItem, index: number) => (
                    <tr key={streamer.streamer_id} className="hover:bg-gray-800/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {streamer.streamer_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">
                        {streamer.streamer_login || '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {streamer.transaction_count.toLocaleString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {formatAmount(streamer.total_amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {formatAmount(streamer.commission_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 8. Aggregated Data Table */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Агрегированные данные</h3>
            <DataTable
              data={summary.table_items || []}
              columns={tableColumns}
              loading={loading}
              pagination={{
                page: summary.table_page,
                limit: summary.table_page_size,
                total: summary.table_total,
                totalPages: summary.table_pages,
              }}
              onPageChange={setTablePage}
              emptyMessage="Нет данных за выбранный период"
            />
          </div>
        </>
      ) : (
        <div className="card">
          <div className="text-center text-gray-500 py-8">Нет данных</div>
        </div>
      )}
    </div>
  );
};

export default StatisticsPage;
