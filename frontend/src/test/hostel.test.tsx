import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HostelPage } from '@/pages/HostelPage';

// Mock hostel API
vi.mock('@/api/hostel', () => ({
  hostelApi: {
    getDashboard: vi.fn().mockResolvedValue({
      total_hostels: 2,
      total_rooms: 10,
      total_beds: 40,
      occupied_beds: 25,
      available_beds: 15,
      occupancy_percentage: 62.5,
      today_present_count: 24,
      pending_outpasses: 3,
      checked_out_students: 1,
    }),
    getBuildings: vi.fn().mockResolvedValue([
      { id: 'b1', name: 'Boys Hostel Block A', code: 'BHA', gender_designation: 'BOYS', capacity: 20, is_active: true },
    ]),
    getOutpasses: vi.fn().mockResolvedValue([]),
    getFeeStructures: vi.fn().mockResolvedValue([]),
  },
}));

describe('HostelPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  it('renders Hostel Management header and tabs correctly', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <HostelPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Hostel Management')).toBeInTheDocument();
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    expect(screen.getByText('Buildings & Rooms')).toBeInTheDocument();
    expect(screen.getByText('Outpass Requests')).toBeInTheDocument();
    expect(screen.getByText('Hostel Fees')).toBeInTheDocument();
  });
});
