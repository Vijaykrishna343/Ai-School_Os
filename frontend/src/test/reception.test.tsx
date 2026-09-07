import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReceptionPage } from '@/pages/ReceptionPage';
import { receptionApi } from '@/services/api/receptionApi';

// Mock receptionApi
vi.mock('@/services/api/receptionApi', () => ({
  receptionApi: {
    getVisitors: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'vis-1',
          school_id: 'sch-1',
          visitor_name: 'John Smith',
          phone: '9876543210',
          email: 'john@example.com',
          id_proof_type: 'AADHAAR',
          purpose: 'Parent-Teacher Meeting',
          host_type: 'TEACHER',
          host_id: 'teach-1',
          check_in_time: '2026-09-07T10:00:00Z',
          check_out_time: null,
          status: 'CHECKED_IN',
          pass_number: 'GP-20260907-001',
          created_at: '2026-09-07T10:00:00Z',
          updated_at: '2026-09-07T10:00:00Z',
        },
        {
          id: 'vis-2',
          school_id: 'sch-1',
          visitor_name: 'Alice Brown',
          phone: '9123456789',
          email: 'alice@example.com',
          id_proof_type: 'DRIVING_LICENSE',
          purpose: 'Fee Payment Inquiry',
          host_type: 'STAFF',
          host_id: 'staff-1',
          check_in_time: '2026-09-07T09:00:00Z',
          check_out_time: '2026-09-07T09:45:00Z',
          status: 'CHECKED_OUT',
          pass_number: 'GP-20260907-002',
          created_at: '2026-09-07T09:00:00Z',
          updated_at: '2026-09-07T09:45:00Z',
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),

    getVisitor: vi.fn().mockResolvedValue({
      id: 'vis-1',
      school_id: 'sch-1',
      visitor_name: 'John Smith',
      phone: '9876543210',
      email: 'john@example.com',
      id_proof_type: 'AADHAAR',
      id_proof_number: '1234-5678-9012',
      purpose: 'Parent-Teacher Meeting',
      host_type: 'TEACHER',
      host_id: 'teach-1',
      check_in_time: '2026-09-07T10:00:00Z',
      check_out_time: null,
      status: 'CHECKED_IN',
      pass_number: 'GP-20260907-001',
      remarks: 'Verified Aadhaar card at main gate',
      created_at: '2026-09-07T10:00:00Z',
      updated_at: '2026-09-07T10:00:00Z',
    }),

    checkInVisitor: vi.fn().mockResolvedValue({
      id: 'vis-3',
      school_id: 'sch-1',
      visitor_name: 'Robert Davis',
      phone: '9988776655',
      purpose: 'Vendor Delivery',
      status: 'CHECKED_IN',
      pass_number: 'GP-20260907-003',
      created_at: '2026-09-07T11:00:00Z',
      updated_at: '2026-09-07T11:00:00Z',
    }),

    checkOutVisitor: vi.fn().mockResolvedValue({
      id: 'vis-1',
      status: 'CHECKED_OUT',
      check_out_time: '2026-09-07T11:30:00Z',
    }),

    getInquiries: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'inq-1',
          school_id: 'sch-1',
          visitor_id: 'vis-1',
          contact_name: 'David Wilson',
          contact_phone: '9888877777',
          contact_email: 'david@example.com',
          subject: 'Admission Inquiry for Grade 6',
          details: 'Looking for syllabus details and fee breakdown',
          host_type: 'STAFF',
          host_id: 'staff-2',
          appointment_time: '2026-09-08T10:00:00Z',
          status: 'PENDING',
          notes: 'Follow up tomorrow',
          created_at: '2026-09-07T10:30:00Z',
          updated_at: '2026-09-07T10:30:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),

    getInquiry: vi.fn().mockResolvedValue({
      id: 'inq-1',
      school_id: 'sch-1',
      contact_name: 'David Wilson',
      contact_phone: '9888877777',
      subject: 'Admission Inquiry for Grade 6',
      status: 'PENDING',
      notes: 'Follow up tomorrow',
      created_at: '2026-09-07T10:30:00Z',
      updated_at: '2026-09-07T10:30:00Z',
    }),

    createInquiry: vi.fn().mockResolvedValue({
      id: 'inq-2',
      school_id: 'sch-1',
      contact_name: 'Sarah Miller',
      contact_phone: '9777766666',
      subject: 'Transport Route Query',
      status: 'PENDING',
      created_at: '2026-09-07T11:15:00Z',
      updated_at: '2026-09-07T11:15:00Z',
    }),

    updateInquiry: vi.fn().mockResolvedValue({
      id: 'inq-1',
      subject: 'Admission Inquiry for Grade 6',
      status: 'RESOLVED',
      notes: 'Provided brochure and fee slip',
    }),

    getAnalytics: vi.fn().mockResolvedValue({
      period: { start_date: '2026-08-09', end_date: '2026-09-07' },
      visitors: { total: 25, checked_in: 5, checked_out: 20, currently_active: 5 },
      inquiries: { total: 18, pending: 4, in_progress: 3, resolved: 10, cancelled: 1 },
      appointments: { total: 8, upcoming: 3, completed: 5 },
      operational_metrics: {
        avg_visitor_duration_minutes: 45.5,
        peak_checkin_hour: 10,
        visitors_by_purpose: [
          { purpose: 'Parent Meeting', count: 12 },
          { purpose: 'Fee Payment', count: 8 },
        ],
        visitors_by_host_type: [
          { host_type: 'TEACHER', count: 15 },
          { host_type: 'STAFF', count: 10 },
        ],
      },
      visitor_trend: [
        { date: '2026-09-06', count: 10 },
        { date: '2026-09-07', count: 15 },
      ],
      inquiry_trend: [
        { date: '2026-09-06', count: 8 },
        { date: '2026-09-07', count: 10 },
      ],
    }),
  },
}));

// Mock auth store
vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: () => ({
    user: { id: 'usr-1', email: 'receptionist@school.com', school_id: 'sch-1' },
    permissions: ['visitors.view', 'visitors.checkin', 'visitors.checkout', 'reception.view', 'reception.create', 'reception.update'],
    roles: [{ name: 'Receptionist' }],
  }),
}));

describe('ReceptionPage Workstation UI', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  it('1. Renders Reception Workstation header and summary cards on Overview tab', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Reception Workstation')).toBeInTheDocument();
    expect(screen.getByText('Check-In Visitor')).toBeInTheDocument();
    expect(screen.getByText('Log Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Active Visitors')).toBeInTheDocument();
    expect(screen.getByText('Checked Out Today')).toBeInTheDocument();
    expect(screen.getByText('Pending Inquiries')).toBeInTheDocument();
  });

  it('2. Switches to Campus Visitors tab and renders visitors table', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const visitorsTab = await screen.findByRole('button', { name: /Campus Visitors/i });
    fireEvent.click(visitorsTab);

    expect(await screen.findByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('GP-20260907-001')).toBeInTheDocument();
    expect(screen.getByText('Parent-Teacher Meeting')).toBeInTheDocument();
    expect(screen.getByText('Alice Brown')).toBeInTheDocument();
  });

  it('3. Opens Check-In modal, fills required fields, and triggers visitor check-in', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const checkInBtn = await screen.findByText('Check-In Visitor');
    fireEvent.click(checkInBtn);

    expect(screen.getByText('Campus Visitor Check-In')).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText('Full Name');
    const phoneInput = screen.getByPlaceholderText('+91 98765 43210');
    const purposeInput = screen.getByPlaceholderText('e.g. Parent-Teacher Meeting, Fee Payment, Vendor Delivery');

    fireEvent.change(nameInput, { target: { value: 'Robert Davis' } });
    fireEvent.change(phoneInput, { target: { value: '9988776655' } });
    fireEvent.change(purposeInput, { target: { value: 'Vendor Delivery' } });

    const submitBtn = screen.getByRole('button', { name: /Confirm & Issue Gate Pass/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(receptionApi.checkInVisitor).toHaveBeenCalledWith(
        expect.objectContaining({
          visitor_name: 'Robert Davis',
          phone: '9988776655',
          purpose: 'Vendor Delivery',
        })
      );
    });
  });

  it('4. Triggers visitor check-out action when Check Out button is clicked', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const visitorsTab = await screen.findByRole('button', { name: /Campus Visitors/i });
    fireEvent.click(visitorsTab);

    const checkOutBtn = await screen.findByRole('button', { name: /Check Out/i });
    fireEvent.click(checkOutBtn);

    expect(screen.getByText('Confirm Visitor Departure')).toBeInTheDocument();

    const confirmOutBtn = screen.getByRole('button', { name: /Complete Check-Out/i });
    fireEvent.click(confirmOutBtn);

    await waitFor(() => {
      expect(receptionApi.checkOutVisitor).toHaveBeenCalledWith('vis-1', expect.anything());
    });
  });

  it('5. Displays Visitor Detail dossier modal with masked/authorized identity proof details', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const visitorsTab = await screen.findByRole('button', { name: /Campus Visitors/i });
    fireEvent.click(visitorsTab);

    const viewDetailBtns = await screen.findAllByTitle('View Details');
    fireEvent.click(viewDetailBtns[0]);

    await waitFor(() => {
      expect(receptionApi.getVisitor).toHaveBeenCalledWith('vis-1');
    });

    expect(await screen.findByText('Visitor Identity Dossier')).toBeInTheDocument();
    expect(screen.getByText('Verified Aadhaar card at main gate')).toBeInTheDocument();
  });

  it('6. Switches to Inquiries & Appointments tab and logs a new reception inquiry', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const inquiriesTab = await screen.findByRole('button', { name: /Inquiries & Appointments/i });
    fireEvent.click(inquiriesTab);

    expect(await screen.findByText('Admission Inquiry for Grade 6')).toBeInTheDocument();

    const logInquiryBtn = screen.getByText('Log Inquiry');
    fireEvent.click(logInquiryBtn);

    expect(screen.getByText('Log Reception Inquiry / Appointment')).toBeInTheDocument();

    const contactNameInput = screen.getByPlaceholderText('Full Name');
    const contactPhoneInput = screen.getByPlaceholderText('+91 98765 43210');
    const subjectInput = screen.getByPlaceholderText('e.g. Admission Inquiry Grade 5, Fee Structure Clarification');

    fireEvent.change(contactNameInput, { target: { value: 'Sarah Miller' } });
    fireEvent.change(contactPhoneInput, { target: { value: '9777766666' } });
    fireEvent.change(subjectInput, { target: { value: 'Transport Route Query' } });

    const submitInquiryBtn = screen.getByRole('button', { name: /Log Inquiry \(PENDING\)/i });
    fireEvent.click(submitInquiryBtn);

    await waitFor(() => {
      expect(receptionApi.createInquiry).toHaveBeenCalledWith(
        expect.objectContaining({
          contact_name: 'Sarah Miller',
          contact_phone: '9777766666',
          subject: 'Transport Route Query',
        })
      );
    });
  });

  it('7. Opens Inquiry status management modal and updates status to RESOLVED', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const inquiriesTab = await screen.findByRole('button', { name: /Inquiries & Appointments/i });
    fireEvent.click(inquiriesTab);

    const manageBtn = await screen.findByRole('button', { name: /Manage/i });
    fireEvent.click(manageBtn);

    expect(screen.getByText('Inquiry Status & Resolution')).toBeInTheDocument();

    const statusSelects = screen.getAllByRole('combobox');
    fireEvent.change(statusSelects[statusSelects.length - 1], { target: { value: 'RESOLVED' } });


    const saveBtn = screen.getByRole('button', { name: /Save Updates/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(receptionApi.updateInquiry).toHaveBeenCalledWith('inq-1', expect.objectContaining({ status: 'RESOLVED' }));
    });
  });

  it('8. Renders Analytics & Reporting tab with operational metrics and trends', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const analyticsTab = await screen.findByRole('button', { name: /Analytics & Reporting/i });
    fireEvent.click(analyticsTab);

    await waitFor(() => {
      expect(receptionApi.getAnalytics).toHaveBeenCalled();
    });

    expect(screen.getByText('Reception Analytics & Operational Trends')).toBeInTheDocument();
    expect(screen.getByText('Visitor Check-In Activity Trend')).toBeInTheDocument();
    expect(screen.getByText('Inquiry Volume Activity Trend')).toBeInTheDocument();
    expect(screen.getByText('Inquiry Status Distribution')).toBeInTheDocument();
    expect(screen.getByText('Top Visitor Purposes')).toBeInTheDocument();
    expect(screen.getByText('Visitors by Host Category')).toBeInTheDocument();
  });

  it('9. Handles date range preset filtering in Analytics tab', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ReceptionPage />
      </QueryClientProvider>
    );

    const analyticsTab = await screen.findByRole('button', { name: /Analytics & Reporting/i });
    fireEvent.click(analyticsTab);

    const todayBtn = await screen.findByRole('button', { name: /^Today$/i });
    fireEvent.click(todayBtn);

    await waitFor(() => {
      const todayStr = new Date().toISOString().split('T')[0];
      expect(receptionApi.getAnalytics).toHaveBeenCalledWith(
        expect.objectContaining({ start_date: todayStr, end_date: todayStr })
      );
    });
  });
});
