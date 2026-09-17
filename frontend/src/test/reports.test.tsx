import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportsPage } from '@/pages/ReportsPage';
import { reportsApi, ExecutiveSummaryResponse } from '@/services/api/reportsApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/reportsApi', () => ({
  reportsApi: {
    getExecutiveSummary: vi.fn(),
    getStudentReport: vi.fn(),
    getAttendanceReport: vi.fn(),
    getFinanceReport: vi.fn(),
    getAdmissionsReport: vi.fn(),
    getAcademicReport: vi.fn(),
    getOperationsReport: vi.fn(),
    exportCsv: vi.fn(),
  },
}));

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn().mockResolvedValue({ items: [{ id: 'year-1', name: '2026-2027' }], total: 1 }),
  },
}));

vi.mock('@/services/api/academicTermsApi', () => ({
  academicTermsApi: {
    getAcademicTerms: vi.fn().mockResolvedValue({ items: [{ id: 'term-1', name: 'Term 1' }], total: 1 }),
  },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: {
    getSchoolClasses: vi.fn().mockResolvedValue({ items: [{ id: 'class-1', name: 'Grade 10' }], total: 1 }),
  },
}));

vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: {
    getSectionsByClass: vi.fn().mockResolvedValue({ items: [{ id: 'sec-1', name: 'Section A' }], total: 1 }),
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

const mockExecutiveSummary: ExecutiveSummaryResponse = {
  school_id: 'school-123',
  school_name: 'Test Academy',
  generated_at: '2026-09-15T12:00:00Z',
  active_students: 450,
  active_teachers: 35,
  active_classes: 12,
  overall_attendance_pct: 92.4,
  total_fees_assigned: 150000.0,
  total_fees_collected: 120000.0,
  total_fees_outstanding: 30000.0,
  fee_collection_rate_pct: 80.0,
  admissions_inquiries: 65,
  admissions_applicants: 50,
  admissions_enrolled: 40,
  admissions_conversion_pct: 80.0,
  published_report_cards_pct: 95.0,
  kpi_cards: [
    {
      id: 'active_students',
      title: 'Active Students',
      value: '450',
      numeric_value: 450,
      subtext: 'Total enrolled & active',
      trend_direction: 'up',
      status: 'info',
    },
    {
      id: 'attendance_rate',
      title: 'Overall Attendance',
      value: '92.4%',
      numeric_value: 92.4,
      subtext: 'Attendance average',
      trend_direction: 'up',
      status: 'success',
    },
    {
      id: 'fees_collected',
      title: 'Fees Collected',
      value: '$120,000.00',
      numeric_value: 120000.0,
      subtext: '80.0% of assigned fees',
      trend_direction: 'up',
      status: 'success',
    },
  ],
  operations_highlights: {
    active_vehicles: 5,
    active_library_loans: 42,
    low_stock_alerts: 3,
  },
};

describe('ReportsPage Component', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: {
        id: 'user-123',
        school_id: 'school-123',
        email: 'admin@school.com',
        first_name: 'Super',
        last_name: 'Admin',
        is_active: true,
      },
      permissions: ['reports.view', 'reports.export'],
      isAuthenticated: true,
      isLoading: false,
    });
    vi.clearAllMocks();
  });

  it('renders executive summary landing view with KPI cards', async () => {
    vi.mocked(reportsApi.getExecutiveSummary).mockResolvedValue(mockExecutiveSummary);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ReportsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Executive Reports & BI Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Report Filters/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Active Students')).toBeInTheDocument();
      expect(screen.getByText('Overall Attendance')).toBeInTheDocument();
      expect(screen.getAllByText('$120,000.00')[0]).toBeInTheDocument();
      expect(screen.getAllByText(/92\.4%/)[0]).toBeInTheDocument();
    });
  });

  it('switches to Student & Enrollment tab and renders class breakdown', async () => {
    vi.mocked(reportsApi.getExecutiveSummary).mockResolvedValue(mockExecutiveSummary);
    vi.mocked(reportsApi.getStudentReport).mockResolvedValue({
      total_active_students: 450,
      total_inactive_students: 20,
      total_students: 470,
      gender_distribution: { MALE: 230, FEMALE: 220 },
      by_class_section: [
        {
          class_id: 'c1',
          class_name: 'Grade 10',
          section_id: 's1',
          section_name: 'A',
          student_count: 35,
          male_count: 18,
          female_count: 17,
          other_count: 0,
          capacity: 40,
          occupancy_pct: 87.5,
        },
      ],
      enrollment_trends: [],
      total_items: 1,
      page: 1,
      page_size: 20,
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ReportsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const studentTabBtn = screen.getByTestId('tab-students');
    fireEvent.click(studentTabBtn);

    expect(await screen.findByText('Enrollment by Class & Section')).toBeInTheDocument();
    expect(screen.getAllByText('Grade 10').length).toBeGreaterThan(0);
    expect(screen.getByText('87.5%')).toBeInTheDocument();
  });

  it('handles CSV export button click', async () => {
    vi.mocked(reportsApi.getExecutiveSummary).mockResolvedValue(mockExecutiveSummary);
    const mockBlob = new Blob(['Metric,Value\nActive Students,450'], { type: 'text/csv' });
    vi.mocked(reportsApi.exportCsv).mockResolvedValue(mockBlob);

    // Mock URL methods
    window.URL.createObjectURL = vi.fn().mockReturnValue('blob:test');
    window.URL.revokeObjectURL = vi.fn();

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ReportsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    expect(exportBtn).toBeInTheDocument();

    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(reportsApi.exportCsv).toHaveBeenCalledWith('executive', expect.any(Object));
    });
  });
});
