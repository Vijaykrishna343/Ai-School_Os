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
  sent_at?: string;
  created_at?: string;
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
}

export interface ProviderStatus {
  channel: string;
  provider_name: string;
  is_configured: boolean;
  status: string;
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

  fetchProviderStatuses: async () => {
    const res = await apiClient.get('/notifications/providers/status');
    return res.data.data as ProviderStatus[];
  },

  fetchDeliveryLogs: async (params?: { page?: number; page_size?: number; status?: string; channel?: string }) => {
    const res = await apiClient.get('/notifications', { params });
    return res.data.data;
  },

  fetchDeliveryMetrics: async () => {
    const res = await apiClient.get('/notifications/delivery-metrics');
    return res.data.data as DeliveryMetrics;
  },

  retryNotification: async (id: string) => {
    const res = await apiClient.post(`/notifications/${id}/retry`);
    return res.data.data;
  },

  fetchTemplates: async () => {
    const res = await apiClient.get('/notifications/templates');
    return res.data.data as NotificationTemplate[];
  },

  createTemplate: async (payload: { template_key: string; name: string; category: string; title_template: string; body_template: string }) => {
    const res = await apiClient.post('/notifications/templates', payload);
    return res.data.data;
  },

  sendAnnouncement: async (payload: { title: string; message: string; recipient_name: string; recipient_contact: string; channel: string }) => {
    const res = await apiClient.post('/notifications/send', payload);
    return res.data.data;
  },
};
