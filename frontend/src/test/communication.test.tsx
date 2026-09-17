import { render, screen } from '@testing-library/react';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: () => ({
    user: { id: 'user-1', name: 'Test Admin', roles: ['School Admin'] },
    permissions: ['notification.view', 'notification.send', 'notification.manage', 'notification.delivery.view'],
  }),
}));

vi.mock('@/api/communication', () => ({
  communicationApi: {
    fetchUserInbox: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'n1',
          title: 'Welcome Notification',
          body: 'Welcome to AI School OS Communication Center.',
          channel: 'IN_APP',
          status: 'SENT',
          is_read: false,
          created_at: '2026-08-25T10:00:00Z',
        },
      ],
      total: 1,
      unread_count: 1,
    }),
    fetchUserPreferences: vi.fn().mockResolvedValue({
      id: 'pref-1',
      school_id: 'school-1',
      user_id: 'user-1',
      enable_in_app: true,
      enable_email: true,
      enable_sms: true,
      enable_whatsapp: true,
      enable_attendance: true,
      enable_fees: true,
      enable_exams: true,
      enable_events: true,
      enable_hostel: true,
      enable_leave: true,
      enable_emergency: true,
      enable_announcements: true,
    }),
    fetchNotificationAnalytics: vi.fn().mockResolvedValue({
      total_notifications: 10,
      sent_count: 9,
      delivered_count: 0,
      failed_count: 1,
      pending_count: 0,
      cancelled_count: 0,
      success_rate_percent: 90.0,
      failure_rate_percent: 10.0,
      pending_rate_percent: 0.0,
      by_channel: { IN_APP: 5, EMAIL: 3, SMS: 1, WHATSAPP: 1 },
      by_event: { general_announcement: 8, visitor_checkin: 2 },
      daily_volume: [{ date: '2026-09-09', count: 10, sent: 9, failed: 1 }],
      providers: [],
    }),
    fetchNotificationDetail: vi.fn().mockResolvedValue({
      id: 'n1',
      school_id: 'school-1',
      recipient_type: 'STAFF',
      recipient_id: 'user-1',
      recipient_name: 'Test Staff',
      recipient_contact: 'staff@school.com',
      channel: 'IN_APP',
      template_key: 'general_announcement',
      title: 'Welcome Notification',
      body: 'Welcome to AI School OS Communication Center.',
      status: 'SENT',
      retry_count: 0,
      max_retries: 3,
    }),
    fetchDeliveryLogs: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'n1',
          recipient_name: 'Test Staff',
          recipient_contact: 'staff@school.com',
          channel: 'IN_APP',
          template_key: 'general_announcement',
          title: 'Welcome Notification',
          body: 'Welcome to AI School OS Communication Center.',
          status: 'SENT',
          retry_count: 0,
          max_retries: 3,
        },
      ],
      total: 1,
    }),
    fetchDeliveryMetrics: vi.fn().mockResolvedValue({
      total_notifications: 10,
      sent_count: 9,
      failed_count: 1,
      pending_count: 0,
      cancelled_count: 0,
      failure_rate_percent: 10.0,
      by_channel: { IN_APP: 5, EMAIL: 3, SMS: 1, WHATSAPP: 1 },
      providers: [],
    }),
    fetchTemplates: vi.fn().mockResolvedValue([]),
    fetchProviderStatuses: vi.fn().mockResolvedValue([]),
    fetchSchoolCommunicationConfig: vi.fn().mockResolvedValue({
      id: 'cfg-1',
      school_id: 'school-1',
      sms_provider: 'FAST2SMS',
      whatsapp_provider: 'META_WHATSAPP_CLOUD',
      sms_enabled: true,
      whatsapp_enabled: true,
      sms_sender_id: 'SCHLOB',
      sms_entity_id: '17011599',
      whatsapp_phone_number_id: '1001',
      whatsapp_business_account_id: '2001',
      sms_configured: true,
      whatsapp_configured: true,
      sms_api_key_masked: '••••••••',
      whatsapp_access_token_masked: '••••••••',
      sms_monthly_quota: 10000,
      sms_sent_this_month: 0,
      created_at: '2026-08-25T10:00:00Z',
      updated_at: '2026-08-25T10:00:00Z',
    }),
    updateSchoolCommunicationConfig: vi.fn().mockResolvedValue({}),
  },
}));

describe('NotificationsPage Component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  it('renders communication center heading and user inbox', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NotificationsPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Communication & Notification Center/i)).toBeInTheDocument();
    expect(await screen.findByText('Welcome Notification')).toBeInTheDocument();
    expect(screen.getByText('Welcome to AI School OS Communication Center.')).toBeInTheDocument();
  });

  it('renders admin analytics KPI summaries and tabs', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NotificationsPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText('Delivery Logs & History')).toBeInTheDocument();
    expect(screen.getByText('Analytics & Reports')).toBeInTheDocument();
    expect(await screen.findByText('Total Notifications')).toBeInTheDocument();
  });
});
