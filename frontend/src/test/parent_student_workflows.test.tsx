import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '@/pages/DashboardPage';
import { dashboardApi } from '@/services/api/dashboardApi';
import { paymentsApi } from '@/services/api/paymentsApi';
import { feesApi } from '@/services/api/feesApi';
import { homeworkApi } from '@/services/api/homeworkApi';
import { reportCardsApi } from '@/services/api/reportCardsApi';
import { timetableApi } from '@/services/api/timetableApi';
import { libraryApi } from '@/services/api/libraryApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/dashboardApi', () => ({
  dashboardApi: {
    getAdminSummary: vi.fn(),
    getTeacherSummary: vi.fn(),
    getParentSummary: vi.fn(),
    getStudentSummary: vi.fn(),
  },
}));

vi.mock('@/services/api/paymentsApi', () => ({
  paymentsApi: {
    createOrder: vi.fn(),
    verifyPayment: vi.fn(),
  },
}));

vi.mock('@/services/api/feesApi', () => ({
  feesApi: {
    getStudentFeeAssignments: vi.fn(),
    getFeePayments: vi.fn(),
    getPaymentReceipt: vi.fn(),
  },
}));

vi.mock('@/services/api/homeworkApi', () => ({
  homeworkApi: {
    submitWork: vi.fn(),
  },
}));

vi.mock('@/services/api/reportCardsApi', () => ({
  reportCardsApi: {
    getReportCards: vi.fn(),
    getReportCard: vi.fn(),
  },
}));

vi.mock('@/services/api/timetableApi', () => ({
  timetableApi: {
    getTimetables: vi.fn(),
    getTimetable: vi.fn(),
    getSectionTimetable: vi.fn(),
  },
}));

vi.mock('@/services/api/libraryApi', () => ({
  libraryApi: {
    getLoans: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('Parent & Student Self-Service Workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Parent Workstation Workflows', () => {
    const mockParentSummaryWard1 = {
      parent_name: 'John Doe',
      children: [
        { id: 'ward-1', first_name: 'Tommy', last_name: 'Doe', admission_number: 'ADM001', school_class_name: 'Grade 8', section_name: 'A' },
        { id: 'ward-2', first_name: 'Sally', last_name: 'Doe', admission_number: 'ADM002', school_class_name: 'Grade 6', section_name: 'B' },
      ],
      selected_child_id: 'ward-1',
      attendance_summary: {
        attendance_percentage: 96.5,
        present_days: 96,
        absent_days: 3,
        late_days: 1,
      },
      fees_summary: {
        status: 'PENDING',
        total_due: '5000.00',
        next_due_date: '2026-10-31',
      },
      academics_summary: {
        latest_term_gpa: '9.6',
        rank: 1,
      },
      recent_homework: [
        {
          id: 'hw-1',
          title: 'Quadratic Equations Exercise',
          subject_name: 'Mathematics',
          due_date: '2026-10-15',
          is_submitted: false,
        },
      ],
      upcoming_exams: [],
    };

    const mockParentSummaryWard2 = {
      parent_name: 'John Doe',
      children: [
        { id: 'ward-1', first_name: 'Tommy', last_name: 'Doe', admission_number: 'ADM001', school_class_name: 'Grade 8', section_name: 'A' },
        { id: 'ward-2', first_name: 'Sally', last_name: 'Doe', admission_number: 'ADM002', school_class_name: 'Grade 6', section_name: 'B' },
      ],
      selected_child_id: 'ward-2',
      attendance_summary: {
        attendance_percentage: 100.0,
        present_days: 100,
        absent_days: 0,
        late_days: 0,
      },
      fees_summary: {
        status: 'PAID',
        total_due: '0.00',
        next_due_date: null,
      },
      academics_summary: {
        latest_term_gpa: '10.0',
        rank: 1,
      },
      recent_homework: [],
      upcoming_exams: [],
    };

    const mockFeeAssignments = {
      items: [
        {
          id: 'fee-assign-1',
          school_id: 'school-1',
          student_id: 'ward-1',
          student: { first_name: 'Tommy', last_name: 'Doe' },
          fee_structure: { name: 'Grade 8 Standard Tuition' },
          status: 'PENDING',
          gross_amount: '5000.00',
          total_paid: '0.00',
          outstanding_due: '5000.00',
          due_date: '2026-10-31',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
    };

    const mockReportCards = [
      {
        id: 'rc-101',
        student_id: 'ward-1',
        academic_term_name: 'First Term Assessment',
        academic_year_name: '2026-2027',
        status: 'PUBLISHED',
        total_obtained_marks: 480,
        total_max_marks: 500,
        percentage: 96.0,
        overall_grade: 'A+',
        gpa: '9.6',
        is_passed: true,
        attendance_percentage: 98.0,
        teacher_remarks: 'Consistently exceptional performance in analytical sciences.',
        items: [
          { subject_name: 'Mathematics', max_marks: 100, obtained_marks: 98, grade: 'A+' },
        ],
      },
    ];

    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: 'parent-user-1',
          school_id: 'school-1',
          email: 'john.doe@family.com',
          first_name: 'John',
          last_name: 'Doe',
          is_active: true,
          roles: [{ id: 'r-parent', name: 'Parent' }] as any,
        },
        permissions: ['dashboard.parent.view', 'report_card.view', 'timetable.view'],
        isAuthenticated: true,
        isLoading: false,
      });

      vi.mocked(dashboardApi.getParentSummary).mockResolvedValue(mockParentSummaryWard1 as any);
      vi.mocked(feesApi.getStudentFeeAssignments).mockResolvedValue(mockFeeAssignments as any);
      vi.mocked(feesApi.getFeePayments).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 } as any);
      vi.mocked(reportCardsApi.getReportCards).mockResolvedValue({
        items: mockReportCards,
        total: 1,
        page: 1,
        page_size: 50,
      } as any);
      vi.mocked(libraryApi.getLoans).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 } as any);
    });

    it('renders parent workstation with ward switcher and fees balance', async () => {
      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Parent Command Center/i)).toBeInTheDocument();
        expect(screen.getByText('Tommy Doe')).toBeInTheDocument();
        expect(screen.getByText('Pay Online Now')).toBeInTheDocument();
        expect(screen.getByText('₹5000.00')).toBeInTheDocument();
      });
    });

    it('allows switching wards to inspect another child', async () => {
      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Tommy Doe')).toBeInTheDocument();
        expect(screen.getByText('Sally Doe')).toBeInTheDocument();
      });

      // Switch to Sally Doe tab
      vi.mocked(dashboardApi.getParentSummary).mockResolvedValue(mockParentSummaryWard2 as any);
      fireEvent.click(screen.getByText('Sally Doe'));

      await waitFor(() => {
        expect(dashboardApi.getParentSummary).toHaveBeenCalledWith('ward-2');
      });
    });

    it('opens online payment checkout modal and initiates order', async () => {
      vi.mocked(paymentsApi.createOrder).mockResolvedValue({
        id: 'po-123',
        school_id: 'school-1',
        student_fee_assignment_id: 'fee-assign-1',
        amount: 5000,
        currency: 'INR',
        provider: 'MOCK',
        status: 'CREATED',
        gateway_order_id: 'order_rzp_12345',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as any);
      vi.mocked(paymentsApi.verifyPayment).mockResolvedValue({
        id: 'pay-v-1',
        payment_order_id: 'po-123',
        status: 'PAID',
        success: true,
        receipt_number: 'RCP-ONLINE-001',
      } as any);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Pay Online Now')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Pay Online Now'));

      await waitFor(() => {
        expect(screen.getByText(/Online Fee Settlement Checkout/i)).toBeInTheDocument();
      });

      // Proceed with Payment Confirmation
      const payButton = screen.getByRole('button', { name: /Confirm & Pay/i });
      fireEvent.click(payButton);

      await waitFor(() => {
        expect(paymentsApi.createOrder).toHaveBeenCalledWith({
          student_fee_assignment_id: 'fee-assign-1',
          provider: 'MOCK',
        });
      });
    });

    it('opens published report card modal for ward', async () => {
      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('View Published Report Cards')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View Published Report Cards'));

      await waitFor(() => {
        expect(screen.getByText(/Official Published Report Cards/i)).toBeInTheDocument();
        expect(screen.getByText(/First Term Assessment/i)).toBeInTheDocument();
      });
    });
  });

  describe('Student Workstation Workflows', () => {
    const mockStudentSummary = {
      student_info: {
        id: 'student-1',
        first_name: 'Tommy',
        last_name: 'Doe',
        admission_number: 'ADM001',
        school_class_name: 'Grade 8',
        section_name: 'A',
        section_id: 'sec-8a',
      },
      attendance_summary: {
        attendance_percentage: 96.5,
        present_days: 96,
        absent_days: 3,
        late_days: 1,
      },
      fees_summary: {
        status: 'PENDING',
        total_due: '5000.00',
      },
      academics_summary: {
        latest_term_gpa: '9.6',
      },
      recent_homework: [
        {
          id: 'hw-101',
          subject_name: 'Mathematics',
          title: 'Quadratic Equations Practice',
          description: 'Solve exercises 4.1 to 4.5',
          due_date: '2027-12-31',
          is_submitted: false,
        },
      ],
      recent_exam_results: [],
      announcements: [],
      unread_notifications_count: 0,
    };

    const mockLibraryLoans = {
      items: [
        {
          id: 'loan-1',
          book_title: 'Advanced Algebra',
          book_author: 'Leonhard Euler',
          accession_number: 'ACC-001',
          issue_date: '2026-07-01',
          due_date: '2026-07-15',
          status: 'ISSUED',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
    };

    const mockTimetableList = {
      items: [
        {
          id: 'tt-1',
          school_id: 'school-1',
          academic_year_id: 'ay-1',
          school_class_id: 'cls-1',
          section_id: 'sec-8a',
          is_active: true,
          status: 'PUBLISHED',
        },
      ],
      total: 1,
      page: 1,
      page_size: 1,
    };

    const mockTimetableDetail = {
      id: 'tt-1',
      is_active: true,
      entries: [
        {
          id: 'tt-entry-1',
          day_of_week: 'MONDAY',
          period_name: 'Period 1',
          subject_name: 'Mathematics',
          teacher_name: 'Alice Smith',
          classroom_name: '101',
          start_time: '09:00:00',
          end_time: '09:45:00',
        },
      ],
    };

    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: 'student-user-1',
          school_id: 'school-1',
          email: 'tommy@school.com',
          first_name: 'Tommy',
          last_name: 'Doe',
          is_active: true,
          roles: [{ id: 'r-student', name: 'Student' }] as any,
        },
        permissions: ['dashboard.student.view', 'timetable.view', 'report_card.view'],
        isAuthenticated: true,
        isLoading: false,
      });

      vi.mocked(dashboardApi.getStudentSummary).mockResolvedValue(mockStudentSummary as any);
      vi.mocked(libraryApi.getLoans).mockResolvedValue(mockLibraryLoans as any);
      vi.mocked(timetableApi.getTimetables).mockResolvedValue(mockTimetableList as any);
      vi.mocked(timetableApi.getTimetable).mockResolvedValue(mockTimetableDetail as any);
      vi.mocked(reportCardsApi.getReportCards).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 } as any);
    });

    it('renders student workstation with schedule, homework, and library loans', async () => {
      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Student Workstation/i)).toBeInTheDocument();
        expect(screen.getByText('Quadratic Equations Practice')).toBeInTheDocument();
        expect(screen.getByText('Advanced Algebra')).toBeInTheDocument();
        expect(screen.getByText('Alice Smith')).toBeInTheDocument();
      });
    });

    it('allows student to submit homework directly from workstation modal', async () => {
      vi.mocked(homeworkApi.submitWork).mockResolvedValue({
        id: 'sub-1',
        homework_id: 'hw-101',
        student_id: 'student-1',
        submitted_at: new Date().toISOString(),
        content_text: 'Attached solution notes for exercises 4.1 to 4.5',
        status: 'SUBMITTED',
      } as any);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Quadratic Equations Practice')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Quadratic Equations Practice'));

      await waitFor(() => {
        expect(screen.getByText(/Homework Submission Workspace/i)).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Enter your completed response/i);
      fireEvent.change(textarea, { target: { value: 'Attached solution notes for exercises 4.1 to 4.5' } });

      const submitBtn = screen.getByRole('button', { name: /Submit Work/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(homeworkApi.submitWork).toHaveBeenCalledWith(
          'hw-101',
          'Attached solution notes for exercises 4.1 to 4.5'
        );
      });
    });
  });
});
