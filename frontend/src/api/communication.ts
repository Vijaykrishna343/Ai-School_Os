import { apiClient } from '@/services/api/client';

export interface UserPreferences {
  id: string;
  school_id: string;
  user_id: string;
  enable_in_app: boolean;
  enable_email: boolean;
  enable_sms: boolean;
  enable_whatsapp: boolean;
  enable_attendance: boolean;
  enable_fees: boolean;
  enable_exams: boolean;
  enable_events: boolean;
  enable_hostel: boolean;
  enable_leave: boolean;
  enable_emergency: boolean;
  enable_announcements: boolean;
}

export interface NotificationItem {
  id: string;
  recipient_type?: string;
  recipient_id?: string | null;
  recipient_name?: string;
  recipient_contact?: string;
  channel: string;
  template_key: string;
  title: string;
  body: string;
  status: string;
  error_message?: string;
  retry_count?: number;
  max_retries?: number;
  is_read?: boolean;
  provider_name?: string | null;
  provider_message_id?: string | null;
  idempotency_key?: string | null;
  sent_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface NotificationDetail extends NotificationItem {
  school_id: string;
}

export interface NotificationTemplate {
  id: string;
  template_key: string;
  name: string;
  category: string;
  title_template: string;
  body_template: string;
  is_active: boolean;
  is_custom: boolean;
  dlt_entity_id?: string | null;
  dlt_template_id?: string | null;
  whatsapp_template_name?: string | null;
  whatsapp_language_code?: string | null;
}

export interface SchoolCommunicationConfig {
  id: string;
  school_id: string;
  sms_provider: 'NONE' | 'FAST2SMS' | 'TWILIO' | 'MOCK';
  whatsapp_provider: 'NONE' | 'META_WHATSAPP_CLOUD' | 'TWILIO_WHATSAPP' | 'MOCK';
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  sms_sender_id?: string | null;
  sms_entity_id?: string | null;
  whatsapp_phone_number_id?: string | null;
  whatsapp_business_account_id?: string | null;
  sms_configured: boolean;
  whatsapp_configured: boolean;
  sms_api_key_masked?: string | null;
  whatsapp_access_token_masked?: string | null;
  sms_monthly_quota: number;
  sms_sent_this_month: number;
  created_at: string;
  updated_at: string;
}

export interface SchoolCommunicationConfigUpdate {
  sms_provider?: 'NONE' | 'FAST2SMS' | 'TWILIO' | 'MOCK';
  whatsapp_provider?: 'NONE' | 'META_WHATSAPP_CLOUD' | 'TWILIO_WHATSAPP' | 'MOCK';
  sms_enabled?: boolean;
  whatsapp_enabled?: boolean;
  sms_api_key?: string | null;
  sms_sender_id?: string | null;
  sms_entity_id?: string | null;
  whatsapp_access_token?: string | null;
  whatsapp_phone_number_id?: string | null;
  whatsapp_business_account_id?: string | null;
  sms_monthly_quota?: number;
}

export interface ProviderStatus {
  channel: string;
  provider_name: string;
  is_configured: boolean;
  status: string;
}

export interface DailyVolumeItem {
  date: string;
  count: number;
  sent: number;
  failed: number;
}

export interface DeliveryMetrics {
  total_notifications: number;
  sent_count: number;
  failed_count: number;
  pending_count: number;
  cancelled_count: number;
  failure_rate_percent: number;
  by_channel: Record<string, number>;
  providers: ProviderStatus[];
}

export interface NotificationAnalytics {
  total_notifications: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  pending_count: number;
  cancelled_count: number;
  success_rate_percent: number;
  failure_rate_percent: number;
  pending_rate_percent: number;
  by_channel: Record<string, number>;
  by_event: Record<string, number>;
  daily_volume: DailyVolumeItem[];
  providers: ProviderStatus[];
}

export interface NotificationFilterParams {
  page?: number;
  page_size?: number;
  status?: string;
  channel?: string;
  event_type?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export const communicationApi = {
  fetchUserInbox: async (page = 1, page_size = 20) => {
    const res = await apiClient.get('/notifications/inbox', { params: { page, page_size } });
    return res.data.data;
  },

  fetchUnreadCount: async () => {
    const res = await apiClient.get('/notifications/unread-count');
    return res.data.data.unread_count as number;
  },

  markNotificationRead: async (id: string) => {
    const res = await apiClient.post(`/notifications/inbox/${id}/read`);
    return res.data;
  },

  markAllNotificationsRead: async () => {
    const res = await apiClient.post('/notifications/inbox/read-all');
    return res.data;
  },

  fetchUserPreferences: async () => {
    const res = await apiClient.get('/notifications/preferences');
    return res.data.data as UserPreferences;
  },

  updateUserPreferences: async (payload: Partial<UserPreferences>) => {
    const res = await apiClient.put('/notifications/preferences', payload);
    return res.data.data as UserPreferences;
  },

  fetchSchoolCommunicationConfig: async () => {
    const res = await apiClient.get('/notifications/config');
    return res.data.data as SchoolCommunicationConfig;
  },

  updateSchoolCommunicationConfig: async (payload: SchoolCommunicationConfigUpdate) => {
    const res = await apiClient.put('/notifications/config', payload);
    return res.data.data as SchoolCommunicationConfig;
  },

  fetchProviderStatuses: async () => {
    const res = await apiClient.get('/notifications/providers/status');
    return res.data.data as ProviderStatus[];
  },

  fetchDeliveryLogs: async (params?: NotificationFilterParams) => {
    const res = await apiClient.get('/notifications', { params });
    return res.data.data;
  },

  fetchNotificationDetail: async (id: string) => {
    const res = await apiClient.get(`/notifications/${id}`);
    return res.data.data as NotificationDetail;
  },

  fetchDeliveryMetrics: async () => {
    const res = await apiClient.get('/notifications/delivery-metrics');
    return res.data.data as DeliveryMetrics;
  },

  fetchNotificationAnalytics: async (params?: { start_date?: string; end_date?: string }) => {
    const res = await apiClient.get('/notifications/analytics', { params });
    return res.data.data as NotificationAnalytics;
  },

  retryNotification: async (id: string) => {
    const res = await apiClient.post(`/notifications/${id}/retry`);
    return res.data.data;
  },

  fetchTemplates: async () => {
    const res = await apiClient.get('/notifications/templates');
    return res.data.data as NotificationTemplate[];
  },

  createTemplate: async (payload: {
    template_key: string;
    name: string;
    category: string;
    title_template: string;
    body_template: string;
    dlt_entity_id?: string;
    dlt_template_id?: string;
    whatsapp_template_name?: string;
    whatsapp_language_code?: string;
  }) => {
    const res = await apiClient.post('/notifications/templates', payload);
    return res.data.data;
  },

  sendAnnouncement: async (payload: { title: string; message: string; recipient_name: string; recipient_contact: string; channel: string }) => {
    const res = await apiClient.post('/notifications/send', payload);
    return res.data.data;
  },
};

