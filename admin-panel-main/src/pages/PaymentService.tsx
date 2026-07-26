import React, { useState, useEffect } from 'react';
import { CreditCardIcon, ArrowPathIcon, MagnifyingGlassIcon, PencilIcon, CheckIcon, PlusIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useDebounce } from '../hooks/useDebounce';
import { 
  ServiceStats, 
  TableColumn, 
  BalanceItem,
  BalancesFilter,
  BalancesResponse,
  TransactionsTodayStats,
  CommissionItem,
  CommissionsResponse,
  PaymentUserItem,
  UsersWithMethodsResponse
} from '../types';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';

type TabType = 'balances' | 'transactions' | 'commissions' | 'withdraw_methods';

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
  { label: 'Откат вывода СБП', value: 't_withdraw_sbp_rollback' },
  { label: 'Откат вывода карта', value: 't_withdraw_card_rollback' },
  { label: 'Откат комиссии СБП', value: 't_withdraw_sbp_rollback_fee' },
  { label: 'Откат комиссии карта', value: 't_withdraw_card_rollback_fee' },
  { label: 'Инициализация', value: 'init' },
  { label: 'Вывод', value: 'withdraw' },
  { label: 'Зачисление', value: 'credit' },
];

const OPERATION_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  OPERATION_TYPE_OPTIONS.filter(o => o.value).map(o => [o.value, o.label])
);

const PaymentService: React.FC = () => {
  const { showToast } = useToast();
  const [stats, setStats] = useState<ServiceStats | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('balances');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Balances state
  const [balancesData, setBalancesData] = useState<BalancesResponse | null>(null);
  const [balancesFilters, setBalancesFilters] = useState<BalancesFilter>({});
  const [balancesPage, setBalancesPage] = useState(1);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [balancesSearch, setBalancesSearch] = useState('');
  const debouncedBalancesSearch = useDebounce(balancesSearch, 300);

  // Transactions stats state
  const [transactionsStats, setTransactionsStats] = useState<TransactionsTodayStats | null>(null);
  const [transactionsLoading, setTransactionsLoading] = useState(false);

  // Commissions state
  const [commissionsData, setCommissionsData] = useState<CommissionsResponse | null>(null);
  const [commissionsPage, setCommissionsPage] = useState(1);
  const [commissionsSearch, setCommissionsSearch] = useState('');
  const debouncedCommissionsSearch = useDebounce(commissionsSearch, 300);
  const [commissionsLoading, setCommissionsLoading] = useState(false);
  const [editingCommission, setEditingCommission] = useState<CommissionItem | null>(null);
  const [commissionModalOpen, setCommissionModalOpen] = useState(false);
  const [isCreatingCommission, setIsCreatingCommission] = useState(false);
  const [createCommissionError, setCreateCommissionError] = useState<string | null>(null);
  const [loginSearch, setLoginSearch] = useState('');
  const debouncedLoginSearch = useDebounce(loginSearch, 300);
  const [loginSearchResults, setLoginSearchResults] = useState<PaymentUserItem[]>([]);
  const [selectedUser, setSelectedUser] = useState<PaymentUserItem | null>(null);
  const [loginSearchLoading, setLoginSearchLoading] = useState(false);

  const [withdrawMethodsData, setWithdrawMethodsData] = useState<UsersWithMethodsResponse | null>(null);
  const [withdrawMethodsPage, setWithdrawMethodsPage] = useState(1);
  const [withdrawMethodsSearch, setWithdrawMethodsSearch] = useState('');
  const debouncedWithdrawMethodsSearch = useDebounce(withdrawMethodsSearch, 300);
  const [withdrawMethodsLoading, setWithdrawMethodsLoading] = useState(false);

  useEffect(() => {
    fetchServiceData();
    const interval = setInterval(fetchServiceData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'balances') {
      fetchBalances();
    } else if (activeTab === 'transactions') {
      fetchTransactionsStats();
    } else if (activeTab === 'commissions') {
      fetchCommissions();
    } else if (activeTab === 'withdraw_methods') {
      fetchWithdrawMethods();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'balances') {
      fetchBalances();
    }
  }, [balancesFilters, balancesPage]);

  useEffect(() => {
    if (activeTab === 'balances') {
      setBalancesPage(1);
      setBalancesFilters(prev => ({ ...prev, search: debouncedBalancesSearch || undefined }));
    }
  }, [debouncedBalancesSearch]);

  useEffect(() => {
    if (activeTab === 'commissions') {
      setCommissionsPage(1);
      fetchCommissions();
    }
  }, [debouncedCommissionsSearch]);

  useEffect(() => {
    if (activeTab === 'commissions') {
      fetchCommissions();
    }
  }, [commissionsPage]);

  useEffect(() => {
    if (debouncedLoginSearch && debouncedLoginSearch.length >= 2 && isCreatingCommission) {
      searchUsers();
    } else {
      setLoginSearchResults([]);
    }
  }, [debouncedLoginSearch, isCreatingCommission]);

  useEffect(() => {
    if (activeTab === 'withdraw_methods') {
      setWithdrawMethodsPage(1);
      fetchWithdrawMethods();
    }
  }, [debouncedWithdrawMethodsSearch]);

  useEffect(() => {
    if (activeTab === 'withdraw_methods') {
      fetchWithdrawMethods();
    }
  }, [withdrawMethodsPage]);

  const searchUsers = async () => {
    try {
      setLoginSearchLoading(true);
      const results = await apiClient.searchUsers(debouncedLoginSearch, 10);
      setLoginSearchResults(results);
    } catch (err) {
      console.error('Error searching users:', err);
      setLoginSearchResults([]);
    } finally {
      setLoginSearchLoading(false);
    }
  };

  const fetchServiceData = async () => {
    try {
      setLoading(true);
      setError(null);
      const statsData = await apiClient.getServiceStats('payment');
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service data');
      console.error('Error fetching payment service data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBalances = async () => {
    try {
      setBalancesLoading(true);
      const data = await apiClient.getBalances(balancesFilters, balancesPage, 20);
      setBalancesData(data);
    } catch (err) {
      console.error('Error fetching balances:', err);
    } finally {
      setBalancesLoading(false);
    }
  };

  const fetchTransactionsStats = async () => {
    try {
      setTransactionsLoading(true);
      const data = await apiClient.getTransactionsTodayStats();
      setTransactionsStats(data);
    } catch (err) {
      console.error('Error fetching transactions stats:', err);
    } finally {
      setTransactionsLoading(false);
    }
  };

  const fetchCommissions = async () => {
    try {
      setCommissionsLoading(true);
      const data = await apiClient.getCommissions(commissionsPage, 20, debouncedCommissionsSearch);
      setCommissionsData(data);
    } catch (err) {
      console.error('Error fetching commissions:', err);
    } finally {
      setCommissionsLoading(false);
    }
  };

  const fetchWithdrawMethods = async () => {
    try {
      setWithdrawMethodsLoading(true);
      const data = await apiClient.getUsersWithMethods(withdrawMethodsPage, 20, debouncedWithdrawMethodsSearch);
      setWithdrawMethodsData(data);
    } catch (err) {
      console.error('Error fetching withdraw methods:', err);
    } finally {
      setWithdrawMethodsLoading(false);
    }
  };

  const handleEditCommission = async (commission: CommissionItem) => {
    try {
      setIsCreatingCommission(false);
      setCreateCommissionError(null);
      setEditingCommission(commission);
      const fullCommission = await apiClient.getCommission(commission.streamer_id);
      setEditingCommission(fullCommission);
      setCommissionModalOpen(true);
    } catch (err) {
      console.error('Error fetching commission details:', err);
    }
  };

  const handleAddCommission = () => {
    setIsCreatingCommission(true);
    setCreateCommissionError(null);
    setLoginSearch('');
    setLoginSearchResults([]);
    setSelectedUser(null);
    setEditingCommission({
      streamer_id: 0,
      withdraw_commission_sbp: undefined,
      withdraw_commission_card: undefined,
      viewer_commission_sbp: undefined,
      viewer_commission_card: undefined,
    });
    setCommissionModalOpen(true);
  };

  const handleSaveCommission = async () => {
    if (!editingCommission) return;

    try {
      setCreateCommissionError(null);
      
      if (isCreatingCommission) {
        if (!selectedUser) {
          setCreateCommissionError('Выберите стримера из списка');
          return;
        }
        await apiClient.createCommission({ ...editingCommission, streamer_id: selectedUser.streamer_id });
        showToast('success', 'Комиссия успешно создана');
      } else {
        await apiClient.updateCommission(editingCommission.streamer_id, editingCommission);
        showToast('success', 'Комиссия успешно обновлена');
      }
      
      setCommissionModalOpen(false);
      setEditingCommission(null);
      setIsCreatingCommission(false);
      setLoginSearch('');
      setLoginSearchResults([]);
      setSelectedUser(null);
      fetchCommissions();
    } catch (err: any) {
      console.error('Error saving commission:', err);
      if (err.response?.data?.detail) {
        setCreateCommissionError(err.response.data.detail);
        showToast('error', err.response.data.detail);
      } else {
        setCreateCommissionError('Ошибка при сохранении');
        showToast('error', 'Ошибка при сохранении комиссии');
      }
    }
  };

  const balancesColumns: TableColumn<BalanceItem>[] = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'streamer_id', label: 'ID стримера', sortable: true },
    { key: 'streamer_login', label: 'Логин', sortable: true },
    { 
      key: 'operation_type', 
      label: 'Тип операции', 
      sortable: true,
      render: (value) => (
        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
          {OPERATION_TYPE_LABELS[value] || value}
        </span>
      )
    },
    { 
      key: 'balance_diff', 
      label: 'Изменение', 
      sortable: true,
      render: (value) => (
        <span className={value >= 0 ? 'text-green-400' : 'text-red-400'}>
          {value >= 0 ? '+' : ''}{(value / 100).toFixed(2)} ₽
        </span>
      )
    },
    { 
      key: 'balance_total', 
      label: 'Баланс', 
      sortable: true,
      render: (value) => `${(value / 100).toFixed(2)} ₽`
    },
    { key: 'transaction_id', label: 'ID транзакции', sortable: true },
    { 
      key: 'created_at', 
      label: 'Дата создания', 
      sortable: true,
      render: (value) => new Date(value).toLocaleString('ru-RU')
    },
  ];

  // Дефолтные комиссии (из payment/src/api/billing/constants.py)
  const DEFAULT_COMMISSIONS = {
    withdraw_sbp: 2.5,    // 25 / 10
    withdraw_card: 5,     // 50 / 10
    viewer_sbp: 2.5,      // 25 / 10
    viewer_card: 5,       // 50 / 10
  };

  const formatCommission = (value: number | null | undefined, defaultVal: number) => {
    if (value === null || value === undefined) {
      return <span className="text-gray-500">По умолч. ({defaultVal}%)</span>;
    }
    if (value === 0) {
      return <span className="text-green-400">0%</span>;
    }
    return `${(value / 10).toFixed(1)}%`;
  };

  const commissionsColumns: TableColumn<CommissionItem & { actions?: any }>[] = [
    { key: 'streamer_id', label: 'ID стримера', sortable: true },
    { key: 'streamer_login', label: 'Логин', sortable: true },
    { 
      key: 'withdraw_commission_sbp', 
      label: 'Вывод СБП %', 
      sortable: true,
      render: (value) => formatCommission(value, DEFAULT_COMMISSIONS.withdraw_sbp)
    },
    { 
      key: 'withdraw_commission_card', 
      label: 'Вывод карта %', 
      sortable: true,
      render: (value) => formatCommission(value, DEFAULT_COMMISSIONS.withdraw_card)
    },
    { 
      key: 'viewer_commission_sbp', 
      label: 'Донат СБП %', 
      sortable: true,
      render: (value) => formatCommission(value, DEFAULT_COMMISSIONS.viewer_sbp)
    },
    { 
      key: 'viewer_commission_card', 
      label: 'Донат карта %', 
      sortable: true,
      render: (value) => formatCommission(value, DEFAULT_COMMISSIONS.viewer_card)
    },
    {
      key: 'actions',
      label: '',
      render: (_, row) => (
        <button
          onClick={() => handleEditCommission(row)}
          className="p-1 text-gray-400 hover:text-white transition-colors"
        >
          <PencilIcon className="h-4 w-4" />
        </button>
      )
    }
  ];

  const renderBarChart = (data: Record<string, {count: number; amount: number}>, title: string) => {
    const maxValue = Math.max(...Object.values(data).map(d => d.count));
    const totalCount = Object.values(data).reduce((sum, d) => sum + d.count, 0);
    const totalAmount = Object.values(data).reduce((sum, d) => sum + d.amount, 0);
    
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-300">{title}</h4>
          <div className="text-xs text-gray-500">
            Всего: {totalCount.toLocaleString('ru-RU')} · {(totalAmount / 100).toLocaleString('ru-RU')} ₽
          </div>
        </div>
        <div className="space-y-2">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="group relative">
              <div className="flex items-center gap-2">
                <div className="w-28 text-xs text-gray-400 truncate" title={key}>{key}</div>
                <div className="flex-1 bg-gray-700 rounded-full h-7 relative overflow-hidden">
                  <div 
                    className="bg-blue-500 hover:bg-blue-400 h-full rounded-full transition-all duration-300"
                    style={{ width: `${maxValue > 0 ? (value.count / maxValue) * 100 : 0}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-between px-3 text-xs">
                    <span className="text-white font-medium">{value.count.toLocaleString('ru-RU')}</span>
                    <span className="text-gray-300">{(value.amount / 100).toLocaleString('ru-RU')} ₽</span>
                  </div>
                </div>
              </div>
              <div className="absolute left-32 -top-8 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                <div className="font-medium mb-1">{key}</div>
                <div>Кол-во: {value.count.toLocaleString('ru-RU')}</div>
                <div>Сумма: {(value.amount / 100).toLocaleString('ru-RU')} ₽</div>
                <div>Доля: {totalCount > 0 ? ((value.count / totalCount) * 100).toFixed(1) : 0}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderHourlyChart = (data: Array<{hour: number; count: number; amount: number}>) => {
    const maxCount = Math.max(...data.map(d => d.count), 1);
    const totalCount = data.reduce((sum, d) => sum + d.count, 0);
    const totalAmount = data.reduce((sum, d) => sum + d.amount, 0);
    
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-300">По часам</h4>
          <div className="text-xs text-gray-500">
            Всего: {totalCount.toLocaleString('ru-RU')} · {(totalAmount / 100).toLocaleString('ru-RU')} ₽
          </div>
        </div>
        <div className="flex items-end gap-1 h-36">
          {data.map((item) => (
            <div key={item.hour} className="group flex-1 flex flex-col items-center relative">
              <div 
                className="w-full bg-green-500 hover:bg-green-400 rounded-t transition-all duration-300 cursor-pointer"
                style={{ 
                  height: `${(item.count / maxCount) * 100}%`,
                  minHeight: item.count > 0 ? '4px' : '2px',
                  backgroundColor: item.count === 0 ? '#374151' : undefined
                }}
              />
              <div className="text-[10px] text-gray-500 mt-1">
                {item.hour.toString().padStart(2, '0')}
              </div>
              <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                <div className="font-medium mb-1">{item.hour.toString().padStart(2, '0')}:00</div>
                <div>Кол-во: {item.count.toLocaleString('ru-RU')}</div>
                <div>Сумма: {(item.amount / 100).toLocaleString('ru-RU')} ₽</div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-gray-500">
          <span>00:00</span>
          <span>06:00</span>
          <span>12:00</span>
          <span>18:00</span>
          <span>23:00</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gray-800 rounded-lg">
            <CreditCardIcon className="h-8 w-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Платежи</h1>
            <p className="text-gray-400 mt-1">Балансы, транзакции и комиссии</p>
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

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Записей балансов</h3>
          <div className="text-3xl font-bold text-white">
            {(stats as any)?.tables?.balances?.toLocaleString('ru-RU') || '0'}
          </div>
          <p className="text-sm text-gray-500 mt-1">Всего операций с балансами</p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Транзакций</h3>
          <div className="text-3xl font-bold text-white">
            {(stats as any)?.tables?.transactions?.toLocaleString('ru-RU') || '0'}
          </div>
          <p className="text-sm text-gray-500 mt-1">Всего транзакций в системе</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-800">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('balances')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'balances'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700'
            }`}
          >
            Балансы
          </button>
          <button
            onClick={() => setActiveTab('transactions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'transactions'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700'
            }`}
          >
            Статистика транзакций
          </button>
          <button
            onClick={() => setActiveTab('commissions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'commissions'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700'
            }`}
          >
            Комиссии
          </button>
          <button
            onClick={() => setActiveTab('withdraw_methods')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'withdraw_methods'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-700'
            }`}
          >
            Способы вывода
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'balances' && (
        <div className="space-y-4">
          {/* Search */}
          <div className="card">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={balancesSearch}
                  onChange={(e) => setBalancesSearch(e.target.value)}
                  placeholder="Поиск по логину стримера..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Фильтры</h3>
              {(Object.values(balancesFilters).some(v => v !== undefined) || balancesSearch) && (
                <button
                  onClick={() => {
                    setBalancesFilters({});
                    setBalancesSearch('');
                    setBalancesPage(1);
                  }}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <FunnelIcon className="h-4 w-4" />
                  Сбросить
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">ID стримера</label>
                <input
                  type="number"
                  value={balancesFilters.streamer_id || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    streamer_id: e.target.value ? parseInt(e.target.value) : undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Введите ID"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Тип операции</label>
                <select
                  value={balancesFilters.operation_type || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    operation_type: e.target.value ? e.target.value as any : undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {OPERATION_TYPE_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Сумма от</label>
                <input
                  type="number"
                  value={balancesFilters.min_amount || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    min_amount: e.target.value ? parseFloat(e.target.value) : undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Мин. сумма"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Сумма до</label>
                <input
                  type="number"
                  value={balancesFilters.max_amount || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    max_amount: e.target.value ? parseFloat(e.target.value) : undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Макс. сумма"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Дата от</label>
                <input
                  type="date"
                  value={balancesFilters.date_from || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    date_from: e.target.value || undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Дата до</label>
                <input
                  type="date"
                  value={balancesFilters.date_to || ''}
                  onChange={(e) => setBalancesFilters(prev => ({ 
                    ...prev, 
                    date_to: e.target.value || undefined 
                  }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Balances Table */}
          <DataTable
            data={balancesData?.items || []}
            columns={balancesColumns}
            loading={balancesLoading}
            pagination={balancesData ? {
              page: balancesData.page,
              limit: balancesData.page_size,
              total: balancesData.total,
              totalPages: balancesData.pages
            } : undefined}
            onPageChange={setBalancesPage}
            emptyMessage="Записи не найдены"
          />
        </div>
      )}

      {activeTab === 'transactions' && (
        <div className="space-y-6">
          {transactionsLoading ? (
            <div className="card">
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                <span className="ml-3 text-gray-400">Загрузка статистики...</span>
              </div>
            </div>
          ) : transactionsStats ? (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Всего за сегодня</h3>
                  <div className="text-2xl font-bold text-white">{transactionsStats.total_count.toLocaleString('ru-RU')}</div>
                  <div className="text-sm text-gray-500">{(transactionsStats.total_amount / 100).toLocaleString('ru-RU')} ₽</div>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Завершено</h3>
                  <div className="text-2xl font-bold text-green-400">{transactionsStats.completed_count.toLocaleString('ru-RU')}</div>
                  <div className="text-sm text-gray-500">{(transactionsStats.completed_amount / 100).toLocaleString('ru-RU')} ₽</div>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">В обработке</h3>
                  <div className="text-2xl font-bold text-yellow-400">{transactionsStats.pending_count.toLocaleString('ru-RU')}</div>
                  <div className="text-sm text-gray-500">{(transactionsStats.pending_amount / 100).toLocaleString('ru-RU')} ₽</div>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Ошибки</h3>
                  <div className="text-2xl font-bold text-red-400">{transactionsStats.failed_count.toLocaleString('ru-RU')}</div>
                  <div className="text-sm text-gray-500">{(transactionsStats.failed_amount / 100).toLocaleString('ru-RU')} ₽</div>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {renderBarChart(transactionsStats.by_operation_type, 'По типу операции')}
                {renderBarChart(transactionsStats.by_payment_provider, 'По платёжной системе')}
              </div>

              {/* Hourly Chart */}
              {renderHourlyChart(transactionsStats.by_hour)}
            </>
          ) : (
            <div className="card">
              <div className="text-center text-gray-500 py-8">
                Нет данных о транзакциях
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'commissions' && (
        <div className="space-y-4">
          {/* Search and Add Button */}
          <div className="card">
            <div className="flex items-center gap-4">
              <div className="flex-1 max-w-md">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={commissionsSearch}
                    onChange={(e) => setCommissionsSearch(e.target.value)}
                    placeholder="Поиск по логину или ID стримера..."
                    className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
              <button
                onClick={handleAddCommission}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                Добавить
              </button>
            </div>
          </div>

          {/* Commissions Table */}
          <DataTable
            data={commissionsData?.items || []}
            columns={commissionsColumns}
            loading={commissionsLoading}
            pagination={commissionsData ? {
              page: commissionsData.page,
              limit: commissionsData.page_size,
              total: commissionsData.total,
              totalPages: commissionsData.pages
            } : undefined}
            onPageChange={setCommissionsPage}
            emptyMessage="Комиссии не найдены"
          />
        </div>
      )}

      {activeTab === 'withdraw_methods' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={withdrawMethodsSearch}
                  onChange={(e) => setWithdrawMethodsSearch(e.target.value)}
                  placeholder="Поиск по логину или ID стримера..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="card overflow-hidden">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Логин</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Статус</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Способы вывода</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {withdrawMethodsLoading ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
                        <span className="ml-2">Загрузка...</span>
                      </div>
                    </td>
                  </tr>
                ) : withdrawMethodsData?.items.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      Пользователи не найдены
                    </td>
                  </tr>
                ) : (
                  withdrawMethodsData?.items.map((user) => (
                    <tr key={user.streamer_id} className="hover:bg-gray-800/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.streamer_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">{user.login}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-xs px-2 py-1 rounded-full ${user.is_active ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {user.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {user.withdraw_methods.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {user.withdraw_methods.map((method) => (
                              <span
                                key={method.id}
                                className={`text-xs px-2 py-1 rounded ${method.type === 'card' ? 'bg-blue-900/50 text-blue-300' : 'bg-purple-900/50 text-purple-300'}`}
                              >
                                {method.type === 'card' 
                                  ? `Карта *${method.card_pan || '****'}` 
                                  : `СБП ${method.bank_name}`}
                                {method.phone && ` (${method.phone})`}
                                {method.is_main && ' ★'}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-500">Нет способов вывода</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {withdrawMethodsData && withdrawMethodsData.pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 bg-gray-800 rounded-lg">
              <div className="text-sm text-gray-400">
                Показано {((withdrawMethodsData.page - 1) * withdrawMethodsData.page_size) + 1} - {Math.min(withdrawMethodsData.page * withdrawMethodsData.page_size, withdrawMethodsData.total)} из {withdrawMethodsData.total}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setWithdrawMethodsPage(p => Math.max(1, p - 1))}
                  disabled={withdrawMethodsData.page <= 1}
                  className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded"
                >
                  Назад
                </button>
                <span className="px-3 py-1 text-sm text-gray-300">
                  {withdrawMethodsData.page} / {withdrawMethodsData.pages}
                </span>
                <button
                  onClick={() => setWithdrawMethodsPage(p => Math.min(withdrawMethodsData.pages, p + 1))}
                  disabled={withdrawMethodsData.page >= withdrawMethodsData.pages}
                  className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded"
                >
                  Вперёд
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <Modal
        isOpen={commissionModalOpen && !!editingCommission}
        onClose={() => {
          setCommissionModalOpen(false);
          setIsCreatingCommission(false);
          setCreateCommissionError(null);
          setLoginSearch('');
          setLoginSearchResults([]);
          setSelectedUser(null);
        }}
        title={isCreatingCommission 
          ? 'Добавить комиссию' 
          : `Комиссии — ${editingCommission?.streamer_login || `ID: ${editingCommission?.streamer_id}`}`
        }
      >
        {editingCommission && (
          <>
            {createCommissionError && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
                {createCommissionError}
              </div>
            )}

            <div className="space-y-4">
              {isCreatingCommission && (
                <div className="relative">
                  <label className="block text-sm font-medium text-gray-400 mb-1">Стример</label>
                  {selectedUser ? (
                    <div className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-100 font-medium">{selectedUser.login}</span>
                          <span className="text-gray-500 text-sm">(ID: {selectedUser.streamer_id})</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${selectedUser.is_active ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                            {selectedUser.is_active ? 'Активен' : 'Неактивен'}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedUser(null);
                            setLoginSearch('');
                          }}
                          className="text-gray-400 hover:text-white text-sm"
                        >
                          Изменить
                        </button>
                      </div>
                      {selectedUser.withdraw_methods && selectedUser.withdraw_methods.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {selectedUser.withdraw_methods.map((method) => (
                            <span
                              key={method.id}
                              className={`text-xs px-1.5 py-0.5 rounded ${method.type === 'card' ? 'bg-blue-900/50 text-blue-300' : 'bg-purple-900/50 text-purple-300'}`}
                            >
                              {method.type === 'card' ? `Карта *${method.card_pan || '****'}` : `СБП ${method.bank_name}`}
                              {method.is_main && ' (осн.)'}
                            </span>
                          ))}
                        </div>
                      )}
                      {(!selectedUser.withdraw_methods || selectedUser.withdraw_methods.length === 0) && (
                        <div className="mt-2 text-xs text-gray-500">Нет способов вывода</div>
                      )}
                    </div>
                  ) : (
                    <>
                      <div className="relative">
                        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          value={loginSearch}
                          onChange={(e) => setLoginSearch(e.target.value)}
                          placeholder="Введите логин стримера..."
                          className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                      {loginSearchLoading && (
                        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg p-3 text-center text-gray-400 text-sm">
                          Поиск...
                        </div>
                      )}
                      {!loginSearchLoading && loginSearchResults.length > 0 && (
                        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg max-h-64 overflow-y-auto">
                          {loginSearchResults.map((user) => (
                            <button
                              key={user.streamer_id}
                              type="button"
                              onClick={() => {
                                setSelectedUser(user);
                                setLoginSearchResults([]);
                              }}
                              className="w-full px-3 py-2 text-left hover:bg-gray-600 transition-colors first:rounded-t-lg last:rounded-b-lg border-b border-gray-600 last:border-b-0"
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <span className="text-gray-100 font-medium">{user.login}</span>
                                  <span className="text-gray-500 text-sm ml-2">(ID: {user.streamer_id})</span>
                                </div>
                                <span className={`text-xs px-2 py-0.5 rounded-full ${user.is_active ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                                  {user.is_active ? 'Активен' : 'Неактивен'}
                                </span>
                              </div>
                              {user.withdraw_methods && user.withdraw_methods.length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {user.withdraw_methods.map((method) => (
                                    <span
                                      key={method.id}
                                      className={`text-xs px-1.5 py-0.5 rounded ${method.type === 'card' ? 'bg-blue-900/50 text-blue-300' : 'bg-purple-900/50 text-purple-300'}`}
                                    >
                                      {method.type === 'card' ? `Карта *${method.card_pan || '****'}` : `СБП ${method.bank_name}`}
                                      {method.is_main && ' (осн.)'}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {(!user.withdraw_methods || user.withdraw_methods.length === 0) && (
                                <div className="mt-1 text-xs text-gray-500">Нет способов вывода</div>
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                      {!loginSearchLoading && loginSearch.length >= 2 && loginSearchResults.length === 0 && (
                        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg p-3 text-center text-gray-400 text-sm">
                          Пользователи не найдены
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Комиссия вывода СБП (%) <span className="text-gray-500 text-xs">пусто = по умолч. {DEFAULT_COMMISSIONS.withdraw_sbp}%</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={editingCommission.withdraw_commission_sbp !== null && editingCommission.withdraw_commission_sbp !== undefined 
                    ? (editingCommission.withdraw_commission_sbp / 10) 
                    : ''}
                  onChange={(e) => setEditingCommission(prev => ({
                    ...prev!,
                    withdraw_commission_sbp: e.target.value === '' ? undefined : Math.round(parseFloat(e.target.value) * 10)
                  }))}
                  placeholder={`По умолч. ${DEFAULT_COMMISSIONS.withdraw_sbp}%`}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Комиссия вывода карта (%) <span className="text-gray-500 text-xs">пусто = по умолч. {DEFAULT_COMMISSIONS.withdraw_card}%</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={editingCommission.withdraw_commission_card !== null && editingCommission.withdraw_commission_card !== undefined 
                    ? (editingCommission.withdraw_commission_card / 10) 
                    : ''}
                  onChange={(e) => setEditingCommission(prev => ({
                    ...prev!,
                    withdraw_commission_card: e.target.value === '' ? undefined : Math.round(parseFloat(e.target.value) * 10)
                  }))}
                  placeholder={`По умолч. ${DEFAULT_COMMISSIONS.withdraw_card}%`}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Комиссия доната СБП (%) <span className="text-gray-500 text-xs">пусто = по умолч. {DEFAULT_COMMISSIONS.viewer_sbp}%</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={editingCommission.viewer_commission_sbp !== null && editingCommission.viewer_commission_sbp !== undefined 
                    ? (editingCommission.viewer_commission_sbp / 10) 
                    : ''}
                  onChange={(e) => setEditingCommission(prev => ({
                    ...prev!,
                    viewer_commission_sbp: e.target.value === '' ? undefined : Math.round(parseFloat(e.target.value) * 10)
                  }))}
                  placeholder={`По умолч. ${DEFAULT_COMMISSIONS.viewer_sbp}%`}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Комиссия доната карта (%) <span className="text-gray-500 text-xs">пусто = по умолч. {DEFAULT_COMMISSIONS.viewer_card}%</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={editingCommission.viewer_commission_card !== null && editingCommission.viewer_commission_card !== undefined 
                    ? (editingCommission.viewer_commission_card / 10) 
                    : ''}
                  onChange={(e) => setEditingCommission(prev => ({
                    ...prev!,
                    viewer_commission_card: e.target.value === '' ? undefined : Math.round(parseFloat(e.target.value) * 10)
                  }))}
                  placeholder={`По умолч. ${DEFAULT_COMMISSIONS.viewer_card}%`}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleSaveCommission}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <CheckIcon className="h-4 w-4" />
                {isCreatingCommission ? 'Добавить' : 'Сохранить'}
              </button>
              <button
                onClick={() => {
                  setCommissionModalOpen(false);
                  setIsCreatingCommission(false);
                  setCreateCommissionError(null);
                  setLoginSearch('');
                  setLoginSearchResults([]);
                  setSelectedUser(null);
                }}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Отмена
              </button>
            </div>
          </>
        )}
      </Modal>

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
    </div>
  );
};

export default PaymentService;