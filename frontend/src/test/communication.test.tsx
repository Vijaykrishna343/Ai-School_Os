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
    fetchDeliveryLogs: vi.fn().mockResolvedValue({
      items: [],
      total: 0,
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
});
