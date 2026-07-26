export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  message?: string;
  details?: Record<string, any>;
}

export interface ServiceStats {
  total_requests?: number;
  active_users?: number;
  success_rate?: number;
  average_response_time?: number;
  uptime?: number;
  error_count?: number;
  last_updated: string;
}

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  children?: NavItem[];
}

export interface TableColumn<T = any> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export type ServiceType = 'payment' | 'auth' | 'streamer' | 'widget';

export interface ServiceInfo {
  id: ServiceType;
  name: string;
  description: string;
  endpoint: string;
  health: ServiceHealth | null;
  stats: ServiceStats | null;
}

export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  user_id?: string;
  streamer_id?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  status: string;
  created_at: string;
  last_login?: string;
}

export interface Streamer {
  id: string;
  username: string;
  display_name: string;
  status: string;
  followers_count: number;
  created_at: string;
  is_live: boolean;
}

export interface Widget {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  streamer_id: string;
  created_at: string;
  is_active: boolean;
}

export interface ServiceFilter {
  status?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface ServiceSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface BalanceItem {
  id: string;
  streamer_id: number;
  streamer_login?: string;
  operation_type: 'DONAT' | 'WITHDRAW' | 'REFUND' | 'STAKE' | 'UNSTAKE';
  balance_diff: number;
  balance_total: number;
  transaction_id?: string;
  created_at: string;
}

export interface BalancesResponse {
  items: BalanceItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TransactionsTodayStats {
  total_count: number;
  total_amount: number;
  completed_count: number;
  completed_amount: number;
  pending_count: number;
  pending_amount: number;
  failed_count: number;
  failed_amount: number;
  by_operation_type: Record<string, {count: number; amount: number}>;
  by_payment_provider: Record<string, {count: number; amount: number}>;
  by_hour: Array<{hour: number; count: number; amount: number}>;
}

export interface CommissionItem {
  streamer_id: number;
  streamer_login?: string;
  withdraw_commission_sbp?: number;
  withdraw_commission_card?: number;
  viewer_commission_sbp?: number;
  viewer_commission_card?: number;
}

export interface CommissionsResponse {
  items: CommissionItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface BalancesFilter {
  streamer_id?: number;
  operation_type?: 'DONAT' | 'WITHDRAW' | 'REFUND' | 'STAKE' | 'UNSTAKE';
  min_amount?: number;
  max_amount?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface WithdrawMethodItem {
  id: string;
  type: 'card' | 'sbp';
  bank_name: string;
  phone?: string;
  card_pan?: string;
  is_main: boolean;
}

export interface PaymentUserItem {
  streamer_id: number;
  login: string;
  is_active?: boolean;
  withdraw_methods: WithdrawMethodItem[];
}

export interface UsersWithMethodsResponse {
  items: PaymentUserItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface WidgetItem {
  id: number;
  streamer_id: number;
  template_id?: number;
  group_id: number;
  is_active: boolean;
  is_deleted: boolean;
  name: string;
  image?: string;
  audio?: string;
  duration: number;
  min_amount: number;
  max_amount: number;
  volume_percent: number;
  created_at: string;
  updated_at: string;
}

export interface WidgetsResponse {
  items: WidgetItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DonatItem {
  id: number;
  streamer_id: number;
  widget_id?: number;
  order_id: string;
  target_id?: number;
  paid_time?: string;
  is_test: boolean;
  status: 'PENDING' | 'PAID' | 'ACCEPTED' | 'REJECTED' | 'SHOWED';
  text?: string;
  amount: number;
  donat_user?: string;
  accepted_time?: string;
  rejected_time?: string;
  showed_time?: string;
  created_at: string;
}

export interface DonatsResponse {
  items: DonatItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DonatTodayStats {
  total_count: number;
  total_amount: number;
  paid_count: number;
  paid_amount: number;
  by_status: Record<string, {count: number; amount: number}>;
}

export interface WidgetsFilter {
  streamer_id?: number;
  is_active?: boolean;
  include_deleted?: boolean;
}

export interface DonatsFilter {
  streamer_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
}

export interface AccountItem {
  id: number;
  login: string;
  avatar: string;
  email?: string;
  is_active: boolean;
  vk_enabled: boolean;
  google_enabled: boolean;
  twitch_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountsResponse {
  items: AccountItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface StreamerTodayStats {
  new_registrations: number;
}

export interface AccountsFilter {
  search?: string;
  is_active?: boolean;
}

export interface StatisticsFilter {
  date_from?: string;
  date_to?: string;
  grouping?: 'day' | 'week' | 'month' | 'year';
  operation_type?: string;
  payment_provider?: string;
  status?: string;
  streamer_id?: number;
}

export interface BreakdownItem {
  key: string;
  count: number;
  amount: number;
}

export interface TopStreamerItem {
  streamer_id: number;
  streamer_login: string | null;
  transaction_count: number;
  total_amount: number;
  commission_amount: number;
}

export interface TimeseriesPoint {
  period: string;
  transaction_count: number;
  total_amount: number;
  commission_amount: number;
  donat_count: number;
  donat_amount: number;
  avg_transaction: number;
}

export interface StatisticsSummary {
  total_volume: number;
  total_volume_count: number;
  total_commission: number;
  total_commission_count: number;
  total_donats_amount: number;
  total_donats_count: number;
  total_withdrawals_amount: number;
  total_withdrawals_count: number;
  unique_streamers: number;
  new_streamers: number;
  by_operation_type: BreakdownItem[];
  by_payment_provider: BreakdownItem[];
  by_status: BreakdownItem[];
  top_streamers: TopStreamerItem[];
  table_items: TimeseriesPoint[];
  table_total: number;
  table_page: number;
  table_page_size: number;
  table_pages: number;
}

export interface StatisticsTimeseries {
  points: TimeseriesPoint[];
  grouping: string;
}