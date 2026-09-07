import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EventsPage } from '@/pages/EventsPage';

// Mock events API
vi.mock('@/api/events', () => ({
  eventsApi: {
    getEvents: vi.fn().mockResolvedValue([
      {
        id: 'evt-1',
        title: 'Annual Sports Meet 2026',
        event_type: 'SPORTS',
        start_datetime: '2026-08-30T09:00:00Z',
        end_datetime: '2026-08-30T17:00:00Z',
        all_day: false,
        venue: 'Main School Ground',
        audience_scope: 'SCHOOL',
        status: 'PUBLISHED',
      },
    ]),
    createEvent: vi.fn().mockResolvedValue({ id: 'evt-2', title: 'New Event', status: 'DRAFT' }),
    publishEvent: vi.fn().mockResolvedValue({ id: 'evt-1', status: 'PUBLISHED' }),
    cancelEvent: vi.fn().mockResolvedValue({ id: 'evt-1', status: 'CANCELLED' }),
  },
}));

describe('EventsPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  it('renders School Events & Calendar header and filters', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <EventsPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText('School Events & Calendar')).toBeInTheDocument();
    expect(screen.getByText('Create Event')).toBeInTheDocument();
    expect(await screen.findByText('Annual Sports Meet 2026')).toBeInTheDocument();
  });
});
