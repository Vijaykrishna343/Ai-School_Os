import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StaffLeavePage } from '@/pages/StaffLeavePage';

// Mock staffLeave API
vi.mock('@/api/staffLeave', () => ({
  staffLeaveApi: {
    getLeaveTypes: vi.fn().mockResolvedValue([
      {
        id: 'type-1',
        school_id: 'sch-1',
        code: 'CASUAL',
        name: 'Casual Leave',
        max_days_per_year: 12,
        requires_attachment: false,
        is_paid: true,
        is_active: true,
      },
      {
        id: 'type-2',
        school_id: 'sch-1',
        code: 'SICK',
        name: 'Sick Leave',
        max_days_per_year: 10,
        requires_attachment: true,
        is_paid: true,
        is_active: true,
      },
    ]),
    getMyBalances: vi.fn().mockResolvedValue([
      {
        id: 'bal-1',
        school_id: 'sch-1',
        teacher_id: 'tch-1',
        academic_year_id: 'ay-1',
        leave_type_id: 'type-1',
        leave_type_code: 'CASUAL',
        leave_type_name: 'Casual Leave',
        allocated_days: 12,
        used_days: 2,
        pending_days: 0,
        remaining_days: 10,
      },
    ]),
    getLeaveRequests: vi.fn().mockResolvedValue([
      {
        id: 'req-1',
        school_id: 'sch-1',
        teacher_id: 'tch-1',
        teacher_name: 'Jane Doe',
        academic_year_id: 'ay-1',
        leave_type_id: 'type-1',
        leave_type_code: 'CASUAL',
        leave_type_name: 'Casual Leave',
        start_date: '2026-09-01',
        end_date: '2026-09-02',
        requested_days: 2,
        half_day_type: 'FULL_DAY',
        reason: 'Personal medical checkup',
        status: 'APPROVED',
        created_at: '2026-08-25T10:00:00Z',
        updated_at: '2026-08-25T10:00:00Z',
        approval_history: [],
      },
    ]),
    getSummaryReport: vi.fn().mockResolvedValue({
      academic_year_id: 'ay-1',
      total_requests: 5,
      pending_requests: 1,
      approved_today: 1,
      currently_on_leave: 2,
      by_leave_type: { CASUAL: 3, SICK: 2 },
      by_status: { APPROVED: 4, PENDING: 1 },
    }),
    createLeaveRequest: vi.fn().mockResolvedValue({ id: 'req-2', status: 'PENDING' }),
    approveLeaveRequest: vi.fn().mockResolvedValue({ id: 'req-1', status: 'APPROVED' }),
    rejectLeaveRequest: vi.fn().mockResolvedValue({ id: 'req-1', status: 'REJECTED' }),
    cancelLeaveRequest: vi.fn().mockResolvedValue({ id: 'req-1', status: 'CANCELLED' }),
  },
}));

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn().mockResolvedValue([
      { id: 'ay-1', name: '2026-2027', is_current: true },
    ]),
  },
}));

describe('StaffLeavePage', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  it('renders Staff Leave & Approval Workspace title and balance cards', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <StaffLeavePage />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Staff Leave & Approval Workspace')).toBeInTheDocument();
    expect(screen.getByText('Apply for Leave')).toBeInTheDocument();
    const casualLeaves = await screen.findAllByText('Casual Leave');
    expect(casualLeaves.length).toBeGreaterThan(0);
    expect(await screen.findByText('Personal medical checkup')).toBeInTheDocument();
  });
});
