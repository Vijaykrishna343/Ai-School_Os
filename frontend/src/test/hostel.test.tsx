import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HostelPage } from '@/pages/HostelPage';
import { hostelApi } from '@/api/hostel';
import { PermissionRoute } from '@/components/auth/PermissionRoute';
import { useAuthStore } from '@/store/useAuthStore';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// Mock hostel API
vi.mock('@/api/hostel', () => ({
  hostelApi: {
    getDashboard: vi.fn(),
    getBuildings: vi.fn(),
    createBuilding: vi.fn(),
    getOutpasses: vi.fn(),
    createOutpass: vi.fn(),
    approveOutpass: vi.fn(),
    getFeeStructures: vi.fn(),
    getFeeAllocations: vi.fn(),
    allocateFee: vi.fn(),
    payFeeAllocation: vi.fn(),
  },
}));

describe('HostelPage & Routing Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    (hostelApi.getDashboard as any).mockResolvedValue({
      total_hostels: 2,
      total_rooms: 10,
      total_beds: 40,
      occupied_beds: 25,
      available_beds: 15,
      occupancy_percentage: 62.5,
      today_present_count: 24,
      pending_outpasses: 3,
      checked_out_students: 1,
    });

    (hostelApi.getBuildings as any).mockResolvedValue([
      {
        id: 'bldg-1',
        name: 'Boys Hostel Block A',
        code: 'BHA',
        gender_designation: 'BOYS',
        capacity: 20,
        is_active: true,
        description: 'Main residential block',
      },
    ]);

    (hostelApi.getOutpasses as any).mockResolvedValue([
      {
        id: 'outpass-1',
        student_id: 'student-1',
        building_id: 'bldg-1',
        room_id: 'room-1',
        reason: 'Medical Appointment',
        destination: 'City Hospital',
        departure_time: '2026-09-15T10:00:00Z',
        expected_return_time: '2026-09-15T16:00:00Z',
        status: 'PENDING',
      },
    ]);

    (hostelApi.getFeeStructures as any).mockResolvedValue([
      {
        id: 'fee-1',
        academic_year_id: 'ay-1',
        name: 'Standard Boarding Fee',
        amount: 1500,
        description: 'Semester boarding & lodging structure',
      },
    ]);

    (hostelApi.getFeeAllocations as any).mockResolvedValue([
      {
        id: 'alloc-1',
        student_id: '11111111-2222-3333-4444-555555555555',
        fee_structure_id: 'fee-1',
        due_date: '2026-10-15',
        amount_due: 1500,
        paid_amount: 500,
        status: 'PARTIAL',
      },
    ]);
  });

  it('renders Hostel Management header, tabs, and dashboard metrics correctly', async () => {
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

    expect(await screen.findByText('62.5%')).toBeInTheDocument();
    expect(screen.getByText('25 Occupied / 15 Available')).toBeInTheDocument();
  });

  it('switches to Buildings tab and displays building cards', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <HostelPage />
      </QueryClientProvider>
    );

    const bldgTab = screen.getByText('Buildings & Rooms');
    fireEvent.click(bldgTab);

    expect(await screen.findByText('Boys Hostel Block A')).toBeInTheDocument();
    expect(screen.getByText('BHA')).toBeInTheDocument();
    expect(screen.getByText('BOYS')).toBeInTheDocument();
    expect(screen.getByText('20 Students')).toBeInTheDocument();
  });

  it('switches to Outpasses tab and handles approval action', async () => {
    (hostelApi.approveOutpass as any).mockResolvedValue({ status: 'APPROVED' });

    render(
      <QueryClientProvider client={queryClient}>
        <HostelPage />
      </QueryClientProvider>
    );

    const outpassTab = screen.getByText('Outpass Requests');
    fireEvent.click(outpassTab);

    expect(await screen.findByText('City Hospital')).toBeInTheDocument();
    expect(screen.getByText('Medical Appointment')).toBeInTheDocument();
    expect(screen.getByText('PENDING')).toBeInTheDocument();

    const approveBtn = screen.getByRole('button', { name: /approve/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(hostelApi.approveOutpass).toHaveBeenCalledWith('outpass-1', true);
    });
  });

  it('switches to Fees tab and renders fee structures and allocations', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <HostelPage />
      </QueryClientProvider>
    );

    const feeTab = screen.getByText('Hostel Fees');
    fireEvent.click(feeTab);

    expect(await screen.findByText('Standard Boarding Fee')).toBeInTheDocument();
    expect(screen.getByText('$1,500')).toBeInTheDocument();
    expect(screen.getByText('Student Hostel Fee Allocations & Central Ledger')).toBeInTheDocument();
    expect(screen.getByText('$1500.00')).toBeInTheDocument();
    expect(screen.getByText('$500.00')).toBeInTheDocument();
    expect(screen.getByText('$1000.00')).toBeInTheDocument();
    expect(screen.getByText('PARTIAL')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /record payment/i })).toBeInTheDocument();
  });

  it('opens record payment modal on payment button click', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <HostelPage />
      </QueryClientProvider>
    );

    const feeTab = screen.getByText('Hostel Fees');
    fireEvent.click(feeTab);

    const payBtn = await screen.findByRole('button', { name: /record payment/i });
    fireEvent.click(payBtn);

    expect(await screen.findByText('Record Hostel Fee Payment')).toBeInTheDocument();
    expect(screen.getByText(/Remaining Due:/i)).toBeInTheDocument();
  });

  it('allows access to /app/hostel when user has hostel.view permission', async () => {
    useAuthStore.setState({
      user: { id: 'u1', is_super_admin: false } as any,
      permissions: ['hostel.view'],
      roles: [],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/app/hostel']}>
          <Routes>
            <Route
              path="/app/hostel"
              element={
                <PermissionRoute permission="hostel.view">
                  <HostelPage />
                </PermissionRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText('Hostel Management')).toBeInTheDocument();
  });

  it('renders ForbiddenPage when user lacks hostel.view permission', async () => {
    useAuthStore.setState({
      user: { id: 'u2', is_super_admin: false } as any,
      permissions: ['student.view'],
      roles: [],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/app/hostel']}>
          <Routes>
            <Route
              path="/app/hostel"
              element={
                <PermissionRoute permission="hostel.view">
                  <HostelPage />
                </PermissionRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.queryByText('Hostel Management')).not.toBeInTheDocument();
    expect(await screen.findByText(/Access Forbidden/i)).toBeInTheDocument();
    expect(screen.getByText(/Required Permission: hostel.view/i)).toBeInTheDocument();
  });
});
