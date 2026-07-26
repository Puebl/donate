import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  ApiResponse, 
  ServiceHealth, 
  ServiceStats, 
  ServiceType, 
  Pagination,
  ServiceFilter, 
  ServiceSort,
  BalancesFilter,
  BalancesResponse,
  TransactionsTodayStats,
  CommissionsResponse,
  CommissionItem,
  AccountsFilter,
  AccountsResponse,
  StreamerTodayStats,
  WidgetsFilter,
  WidgetsResponse,
  DonatsFilter,
  DonatsResponse,
  DonatTodayStats,
  PaymentUserItem,
  UsersWithMethodsResponse,
  StatisticsFilter,
  StatisticsSummary,
  StatisticsTimeseries
} from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get<ApiResponse<T>>(endpoint);
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  private async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(endpoint, data);
    return response.data;
  }

  private async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put<ApiResponse<T>>(endpoint, data);
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }



  private handleError(error: any): void {
    console.error('API Error:', error);
    
    if (error.response) {
      const message = error.response.data?.message || 'Server error occurred';
      throw new Error(message);
    } else if (error.request) {
      throw new Error('Network error. Please check your connection.');
    } else {
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }

  async getServiceHealth(serviceType: ServiceType): Promise<ServiceHealth> {
    const response = await this.client.get<ServiceHealth>(`/${serviceType}/health`);
    return response.data;
  }

  async getAllServiceHealth(): Promise<Record<ServiceType, ServiceHealth>> {
    const services: ServiceType[] = ['payment', 'auth', 'streamer', 'widget'];
    const healthPromises = services.map(service => 
      this.getServiceHealth(service).then(health => ({ [service]: health }))
    );
    
    const healthResults = await Promise.allSettled(healthPromises);
    const health: Partial<Record<ServiceType, ServiceHealth>> = {};
    
    services.forEach((service, index) => {
      const result = healthResults[index];
      if (result.status === 'fulfilled') {
        Object.assign(health, result.value);
      } else {
        health[service] = {
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          message: 'Failed to fetch health status'
        };
      }
    });
    
    return health as Record<ServiceType, ServiceHealth>;
  }

  async getServiceStats(serviceType: ServiceType): Promise<ServiceStats> {
    const response = await this.client.get<ServiceStats>(`/${serviceType}/stats`);
    return response.data;
  }

  async getAllServiceStats(): Promise<Record<ServiceType, ServiceStats>> {
    const services: ServiceType[] = ['payment', 'auth', 'streamer', 'widget'];
    const statsPromises = services.map(service => 
      this.getServiceStats(service).then(stats => ({ [service]: stats }))
    );
    
    const statsResults = await Promise.allSettled(statsPromises);
    const stats: Partial<Record<ServiceType, ServiceStats>> = {};
    
    services.forEach((service, index) => {
      const result = statsResults[index];
      if (result.status === 'fulfilled') {
        Object.assign(stats, result.value);
      } else {
        stats[service] = {
          last_updated: new Date().toISOString(),
          total_requests: 0,
          success_rate: 0
        };
      }
    });
    
    return stats as Record<ServiceType, ServiceStats>;
  }

  async getPayments(filter?: ServiceFilter, sort?: ServiceSort, pagination?: Partial<Pagination>) {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    if (sort) {
      params.append('sort_field', sort.field);
      params.append('sort_direction', sort.direction);
    }
    
    if (pagination) {
      params.append('page', pagination.page?.toString() || '1');
      params.append('limit', pagination.limit?.toString() || '10');
    }
    
    const endpoint = `/payment/data${params.toString() ? `?${params.toString()}` : ''}`;
    return this.get(endpoint);
  }

  async getUsers(filter?: ServiceFilter, sort?: ServiceSort, pagination?: Partial<Pagination>) {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    if (sort) {
      params.append('sort_field', sort.field);
      params.append('sort_direction', sort.direction);
    }
    
    if (pagination) {
      params.append('page', pagination.page?.toString() || '1');
      params.append('limit', pagination.limit?.toString() || '10');
    }
    
    const endpoint = `/auth/users${params.toString() ? `?${params.toString()}` : ''}`;
    return this.get(endpoint);
  }

  async getStreamers(filter?: ServiceFilter, sort?: ServiceSort, pagination?: Partial<Pagination>) {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    if (sort) {
      params.append('sort_field', sort.field);
      params.append('sort_direction', sort.direction);
    }
    
    if (pagination) {
      params.append('page', pagination.page?.toString() || '1');
      params.append('limit', pagination.limit?.toString() || '10');
    }
    
    const endpoint = `/streamer/data${params.toString() ? `?${params.toString()}` : ''}`;
    return this.get(endpoint);
  }

  async getWidgets(filter?: ServiceFilter, sort?: ServiceSort, pagination?: Partial<Pagination>) {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    if (sort) {
      params.append('sort_field', sort.field);
      params.append('sort_direction', sort.direction);
    }
    
    if (pagination) {
      params.append('page', pagination.page?.toString() || '1');
      params.append('limit', pagination.limit?.toString() || '10');
    }
    
    const endpoint = `/widget/data${params.toString() ? `?${params.toString()}` : ''}`;
    return this.get(endpoint);
  }

  
  async getBalances(filter?: BalancesFilter, page: number = 1, pageSize: number = 20): Promise<BalancesResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    if (filter) {
      if (filter.streamer_id !== undefined) params.append('streamer_id', filter.streamer_id.toString());
      if (filter.operation_type) params.append('operation_type', filter.operation_type);
      if (filter.min_amount !== undefined) params.append('min_amount', filter.min_amount.toString());
      if (filter.max_amount !== undefined) params.append('max_amount', filter.max_amount.toString());
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
      if (filter.search) params.append('search', filter.search);
    }
    
    const endpoint = `/payment/balances${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.client.get<BalancesResponse>(endpoint);
    return response.data;
  }

  async searchUsers(query: string, limit: number = 10): Promise<PaymentUserItem[]> {
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('limit', limit.toString());
    
    const endpoint = `/payment/users/search?${params.toString()}`;
    const response = await this.client.get<PaymentUserItem[]>(endpoint);
    return response.data;
  }

  async getUserByLogin(login: string): Promise<PaymentUserItem> {
    const response = await this.client.get<PaymentUserItem>(`/payment/users/by-login/${encodeURIComponent(login)}`);
    return response.data;
  }

  async getUsersWithMethods(page: number = 1, pageSize: number = 20, search?: string): Promise<UsersWithMethodsResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (search) params.append('search', search);
    
    const endpoint = `/payment/users/with-methods?${params.toString()}`;
    const response = await this.client.get<UsersWithMethodsResponse>(endpoint);
    return response.data;
  }

  async getTransactionsTodayStats(): Promise<TransactionsTodayStats> {
    const response = await this.client.get<TransactionsTodayStats>('/payment/transactions/today-stats');
    return response.data;
  }

  async getCommissions(page: number = 1, pageSize: number = 20, search?: string): Promise<CommissionsResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (search) params.append('search', search);
    
    const endpoint = `/payment/commissions${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.client.get<CommissionsResponse>(endpoint);
    return response.data;
  }

  async getCommission(streamerId: number): Promise<CommissionItem> {
    const response = await this.client.get<CommissionItem>(`/payment/commissions/${streamerId}`);
    return response.data;
  }

  async updateCommission(streamerId: number, commissionData: Partial<CommissionItem>): Promise<CommissionItem> {
    const response = await this.client.put<CommissionItem>(`/payment/commissions/${streamerId}`, commissionData);
    return response.data;
  }

  async createCommission(commissionData: CommissionItem): Promise<CommissionItem> {
    const response = await this.client.post<CommissionItem>('/payment/commissions', commissionData);
    return response.data;
  }

  
  async getAccounts(filter?: AccountsFilter, page: number = 1, pageSize: number = 20): Promise<AccountsResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    if (filter) {
      if (filter.search) params.append('search', filter.search);
      if (filter.is_active !== undefined) params.append('is_active', filter.is_active.toString());
    }
    
    const endpoint = `/streamer/accounts${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.client.get(endpoint);
    return response.data;
  }

  async getStreamerTodayStats(): Promise<StreamerTodayStats> {
    const response = await this.client.get('/streamer/accounts/today-stats');
    return response.data;
  }

  async getWidgetList(filter?: WidgetsFilter, page: number = 1, pageSize: number = 20): Promise<WidgetsResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    if (filter) {
      if (filter.streamer_id !== undefined) params.append('streamer_id', filter.streamer_id.toString());
      if (filter.is_active !== undefined) params.append('is_active', filter.is_active.toString());
      if (filter.include_deleted !== undefined) params.append('include_deleted', filter.include_deleted.toString());
    }
    
    const endpoint = `/widget/widgets${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.client.get(endpoint);
    return response.data;
  }

  async getDonats(filter?: DonatsFilter, page: number = 1, pageSize: number = 20): Promise<DonatsResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    if (filter) {
      if (filter.streamer_id !== undefined) params.append('streamer_id', filter.streamer_id.toString());
      if (filter.status) params.append('status', filter.status);
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
    }
    
    const endpoint = `/widget/donats${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.client.get(endpoint);
    return response.data;
  }

  async getDonatsTodayStats(): Promise<DonatTodayStats> {
    const response = await this.client.get('/widget/donats/today-stats');
    return response.data;
  }

  async getStatisticsSummary(filter?: StatisticsFilter, page: number = 1, pageSize: number = 20): Promise<StatisticsSummary> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());

    if (filter) {
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
      if (filter.grouping) params.append('grouping', filter.grouping);
      if (filter.operation_type) params.append('operation_type', filter.operation_type);
      if (filter.payment_provider) params.append('payment_provider', filter.payment_provider);
      if (filter.status) params.append('status', filter.status);
      if (filter.streamer_id !== undefined) params.append('streamer_id', filter.streamer_id.toString());
    }

    const endpoint = `/statistics/summary?${params.toString()}`;
    const response = await this.client.get<StatisticsSummary>(endpoint);
    return response.data;
  }

  async getStatisticsTimeseries(filter?: StatisticsFilter): Promise<StatisticsTimeseries> {
    const params = new URLSearchParams();

    if (filter) {
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
      if (filter.grouping) params.append('grouping', filter.grouping);
      if (filter.operation_type) params.append('operation_type', filter.operation_type);
      if (filter.payment_provider) params.append('payment_provider', filter.payment_provider);
      if (filter.status) params.append('status', filter.status);
      if (filter.streamer_id !== undefined) params.append('streamer_id', filter.streamer_id.toString());
    }

    const endpoint = `/statistics/timeseries?${params.toString()}`;
    const response = await this.client.get<StatisticsTimeseries>(endpoint);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;