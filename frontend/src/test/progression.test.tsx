import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProgressionPage } from '@/pages/ProgressionPage';
import { progressionApi } from '@/services/api/progressionApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/progressionApi', () => ({
  progressionApi: {
    getRules: vi.fn(),
    createRule: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn(),
    generatePreview: vi.fn(),
    executeRollover: vi.fn(),
  },
}));

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn(),
  },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: {
    getSchoolClasses: vi.fn(),
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

describe('Academic Progression Workspace Component', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: { id: 'admin-id', email: 'principal@school.com', school_id: 'school-1' } as any,
      roles: [{ id: 'role-1', name: 'Administrator', code: 'admin', permissions: [] }],
      permissions: ['progression.view', 'progression_matrix.view', 'progression_matrix.manage', 'progression.execute'],
      accessToken: 'token',
      isAuthenticated: true,
      isLoading: false,
      authError: null,
    });
    vi.clearAllMocks();

    // Default mocks
    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [
        { id: 'ay-2025', name: '2025-2026', status: 'ACTIVE' },
        { id: 'ay-2026', name: '2026-2027', status: 'UPCOMING' },
      ],
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [
        { id: 'class-nursery', name: 'Nursery' },
        { id: 'class-lkg', name: 'LKG' },
      ],
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(progressionApi.getRules).mockResolvedValue({
      items: [
        {
          id: 'rule-1',
          school_id: 'school-1',
          source_class_id: 'class-nursery',
          target_class_id: 'class-lkg',
          is_terminal: false,
          description: 'Nursery promotes to LKG',
        },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);
  });

  it('renders progression matrix rules in matrix tab', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Academic Progression Workspace')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('Nursery promotes to LKG')).toBeInTheDocument();
    });
  });

  it('hides execution button when user lacks progression.execute permission', async () => {
    useAuthStore.setState({
      permissions: ['progression.view', 'progression_matrix.view'],
    });

    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 10,
        promoted_count: 8,
        graduated_count: 2,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry-Run Tab
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));

    // Select options
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });

    // Click dry-run
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    await waitFor(() => {
      expect(screen.getByText('PLAN_HASH:')).toBeInTheDocument();
      // Commit button should not be rendered
      expect(screen.queryByRole('button', { name: /Commit Rollover Execution/i })).not.toBeInTheDocument();
    });
  });

  it('submits dry run parameters and renders preview items', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 1,
        promoted_count: 1,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 1,
      },
      items: [
        {
          student_id: 'stud-1',
          admission_number: 'ADM-001',
          student_name: 'John Doe',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'PROMOTED',
          target_class_name: 'LKG',
          target_section_name: 'A',
          allocation_status: 'ALLOCATED',
          reason: 'Meets promotional parameters',
          warnings: ["Section 'A' not found in target class. Fallback to section 'B'."],
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));

    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('ADM-001')).toBeInTheDocument();
      expect(screen.getByText(/Section 'A' not found in target class/i)).toBeInTheDocument();
    });
  });

  it('completes rollover execution after entering correct hash and accepting warnings', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 10,
        promoted_count: 10,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    const mockExecutionResponse = {
      execution_id: 'exec-123',
      status: 'COMPLETED',
      source_academic_year_id: 'ay-2025',
      target_academic_year_id: 'ay-2026',
      summary: {
        total_students_evaluated: 10,
        promoted_count: 10,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
      },
      started_at: '2026-08-13T12:00:00Z',
    };
    vi.mocked(progressionApi.executeRollover).mockResolvedValue(mockExecutionResponse as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    // Click commit execution
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Commit Rollover Execution/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Commit Rollover Execution/i }));

    // Confirmation Modal should appear
    expect(screen.getByText('Institutional Rollover Execution Confirmation')).toBeInTheDocument();

    // Check warning acceptance
    fireEvent.click(screen.getByLabelText(/I acknowledge and accept/i));

    // Verify hash matches
    fireEvent.change(screen.getByPlaceholderText('Enter SHA-256 hash value...'), {
      target: { value: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
    });

    // Commit Transaction
    fireEvent.click(screen.getByRole('button', { name: /Confirm and Commit Transaction/i }));

    await waitFor(() => {
      expect(screen.getByText('Atomic Rollover Completed Successfully')).toBeInTheDocument();
      expect(screen.getByText('exec-123')).toBeInTheDocument();
    });
  });

  it('renders error alert when backend returns stale plan error (409 Conflict)', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 10,
        promoted_count: 10,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    // Mock 409 error
    vi.mocked(progressionApi.executeRollover).mockRejectedValue({
      status: 409,
      message: 'Stale plan hash encountered.',
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    // Click commit execution
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Commit Rollover Execution/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Commit Rollover Execution/i }));

    // Confirm checkbox and hash
    fireEvent.click(screen.getByLabelText(/I acknowledge and accept/i));
    fireEvent.change(screen.getByPlaceholderText('Enter SHA-256 hash value...'), {
      target: { value: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
    });

    // Commit Transaction
    fireEvent.click(screen.getByRole('button', { name: /Confirm and Commit Transaction/i }));

    await waitFor(() => {
      expect(
        screen.getByText('Stale plan hash encountered. The underlying registry records have changed. Generate a new preview.')
      ).toBeInTheDocument();
    });
  });

  it('renders error alert on backend 403 Forbidden', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 10,
        promoted_count: 10,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    // Mock 403 error
    vi.mocked(progressionApi.executeRollover).mockRejectedValue({
      status: 403,
      message: 'You do not have permission to execute progression.',
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    // Click commit execution
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Commit Rollover Execution/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Commit Rollover Execution/i }));

    // Confirm checkbox and hash
    fireEvent.click(screen.getByLabelText(/I acknowledge and accept/i));
    fireEvent.change(screen.getByPlaceholderText('Enter SHA-256 hash value...'), {
      target: { value: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
    });

    // Commit Transaction
    fireEvent.click(screen.getByRole('button', { name: /Confirm and Commit Transaction/i }));

    await waitFor(() => {
      expect(screen.getByText('You do not have permission to execute progression.')).toBeInTheDocument();
    });
  });

  it('renders error alert on backend 422 Validation Error', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 10,
        promoted_count: 10,
        graduated_count: 0,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    // Mock 422 error
    vi.mocked(progressionApi.executeRollover).mockRejectedValue({
      status: 422,
      message: 'Unprocessable Entity: Target academic year must be upcoming.',
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    // Click commit execution
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Commit Rollover Execution/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Commit Rollover Execution/i }));

    // Confirm checkbox and hash
    fireEvent.click(screen.getByLabelText(/I acknowledge and accept/i));
    fireEvent.change(screen.getByPlaceholderText('Enter SHA-256 hash value...'), {
      target: { value: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
    });

    // Commit Transaction
    fireEvent.click(screen.getByRole('button', { name: /Confirm and Commit Transaction/i }));

    await waitFor(() => {
      expect(screen.getByText('Unprocessable Entity: Target academic year must be upcoming.')).toBeInTheDocument();
    });
  });

  it('renders all backend decision enums, allocation statuses, and free-form warnings correctly', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 6,
        promoted_count: 2,
        graduated_count: 1,
        retained_count: 1,
        blocked_count: 1,
        excluded_count: 1,
        warning_count: 2,
      },
      items: [
        {
          student_id: 'stud-1',
          admission_number: 'ADM-001',
          student_name: 'John Promoted',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'PROMOTED',
          target_class_name: 'LKG',
          target_section_name: 'A',
          allocation_status: 'PROPOSED',
          reason: 'Meets promotional parameters',
          warnings: ["Section 'A' not found in target class. Fallback to section 'B'."],
        },
        {
          student_id: 'stud-2',
          admission_number: 'ADM-002',
          student_name: 'John Retained',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'RETAINED',
          target_class_name: 'Nursery',
          target_section_name: 'A',
          allocation_status: 'PROPOSED',
          reason: 'Failed academic evaluation parameters',
          warnings: [],
        },
        {
          student_id: 'stud-3',
          admission_number: 'ADM-003',
          student_name: 'John Graduated',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-10',
          current_class_name: 'Class 10',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'GRADUATED',
          target_class_name: null,
          target_section_name: null,
          allocation_status: 'READY',
          reason: 'Terminal class completion',
          warnings: [],
        },
        {
          student_id: 'stud-4',
          admission_number: 'ADM-004',
          student_name: 'John Transferred',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'TRANSFERRED',
          target_class_name: null,
          target_section_name: null,
          allocation_status: 'READY',
          reason: 'TC Issued',
          warnings: [],
        },
        {
          student_id: 'stud-5',
          admission_number: 'ADM-005',
          student_name: 'John Withdrawn',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'WITHDRAWN',
          target_class_name: null,
          target_section_name: null,
          allocation_status: 'READY',
          reason: 'Withdrawn by parent',
          warnings: [],
        },
        {
          student_id: 'stud-6',
          admission_number: 'ADM-006',
          student_name: 'John Blocked',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'PENDING',
          target_class_name: null,
          target_section_name: null,
          allocation_status: 'BLOCKED',
          reason: 'Missing progression rule mapping',
          warnings: ["Missing progression rule"],
        },
        {
          student_id: 'stud-7',
          admission_number: 'ADM-007',
          student_name: 'John Excluded',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'PENDING',
          target_class_name: null,
          target_section_name: null,
          allocation_status: 'EXCLUDED',
          reason: 'Inactive student status',
          warnings: [],
        },
      ],
      total: 7,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Dry Run Tab
    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));
    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    // Verify all outcome decisions are rendered
    await waitFor(() => {
      expect(screen.getByText('John Promoted')).toBeInTheDocument();
      expect(screen.getByText('John Retained')).toBeInTheDocument();
      expect(screen.getByText('John Graduated')).toBeInTheDocument();
      expect(screen.getByText('John Transferred')).toBeInTheDocument();
      expect(screen.getByText('John Withdrawn')).toBeInTheDocument();
      expect(screen.getByText('John Blocked')).toBeInTheDocument();
      expect(screen.getByText('John Excluded')).toBeInTheDocument();
    });

    // Decisions rendered in badges
    expect(screen.getAllByText('PROMOTED')[0]).toBeInTheDocument();
    expect(screen.getAllByText('RETAINED')[0]).toBeInTheDocument();
    expect(screen.getAllByText('GRADUATED')[0]).toBeInTheDocument();
    expect(screen.getAllByText('TRANSFERRED')[0]).toBeInTheDocument();
    expect(screen.getAllByText('WITHDRAWN')[0]).toBeInTheDocument();
    expect(screen.getAllByText('PENDING').length).toBe(2);

    // Verify target placements are mapped correctly based on decision/status
    expect(screen.getByText('GRADUATED_OUT')).toBeInTheDocument();
    expect(screen.getByText('TRANSFERRED_OUT')).toBeInTheDocument();
    expect(screen.getByText('WITHDRAWN_OUT')).toBeInTheDocument();
    expect(screen.getByText('EXECUTION_BLOCKED')).toBeInTheDocument();
    expect(screen.getByText('EXCLUDED_STUDENT')).toBeInTheDocument();

    // Verify free-form warning text renders with natural sentence casing
    expect(screen.getByText("Section 'A' not found in target class. Fallback to section 'B'.")).toBeInTheDocument();
    expect(screen.getByText("Missing progression rule")).toBeInTheDocument();
    expect(screen.queryByText('FEE_DUE')).not.toBeInTheDocument();
  });

  it('renders and operates Matrix Rules pagination controls', async () => {
    vi.mocked(progressionApi.getRules).mockResolvedValue({
      items: [{ id: 'rule-1', source_class_id: 'class-nursery', target_class_id: 'class-lkg', is_terminal: false, description: 'Nursery to LKG' }],
      total: 15,
      page: 1,
      page_size: 10,
      total_pages: 2,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Nursery to LKG')).toBeInTheDocument();
    });

    const nextPageButton = screen.getByRole('button', { name: 'Next page' });
    expect(nextPageButton).toBeInTheDocument();

    fireEvent.click(nextPageButton);

    await waitFor(() => {
      expect(progressionApi.getRules).toHaveBeenCalledWith(expect.objectContaining({
        page: 2,
      }));
    });
  });

  it('renders and operates Decisions Ledger pagination controls', async () => {
    const mockPreviewResponse = {
      execution_plan_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      summary: {
        source_academic_year_id: 'ay-2025',
        target_academic_year_id: 'ay-2026',
        total_students_evaluated: 100,
        promoted_count: 80,
        graduated_count: 20,
        retained_count: 0,
        blocked_count: 0,
        excluded_count: 0,
        warning_count: 0,
      },
      items: [
        {
          student_id: 'stud-1',
          admission_number: 'ADM-001',
          student_name: 'John Doe',
          current_academic_year_id: 'ay-2025',
          current_class_id: 'class-nursery',
          current_class_name: 'Nursery',
          current_section_id: 'sec-a',
          current_section_name: 'A',
          decision: 'PROMOTED',
          target_class_name: 'LKG',
          target_section_name: 'A',
          allocation_status: 'ALLOCATED',
          reason: 'Meets promotional parameters',
          warnings: [],
        },
      ],
      total: 100,
      page: 1,
      page_size: 50,
      total_pages: 2,
    };
    vi.mocked(progressionApi.generatePreview).mockResolvedValue(mockPreviewResponse as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /Dry-Run & Rollover Console/i }));

    await waitFor(() => {
      expect(screen.getAllByRole('option', { name: '2025-2026 (ACTIVE)' }).length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText(/Source Academic Year/i), { target: { value: 'ay-2025' } });
    fireEvent.change(screen.getByLabelText(/Target Academic Year/i), { target: { value: 'ay-2026' } });
    fireEvent.click(screen.getByRole('button', { name: /Generate Dry-Run Preview/i }));

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const nextPageButton = screen.getByRole('button', { name: 'Next page' });
    expect(nextPageButton).toBeInTheDocument();

    fireEvent.click(nextPageButton);

    await waitFor(() => {
      expect(progressionApi.generatePreview).toHaveBeenCalledWith('ay-2025', expect.objectContaining({
        page: 2,
      }));
    });
  });

  it('updates Rules list request when Matrix filters change', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const sourceClassSelect = screen.getByLabelText('Source Class');
    await waitFor(() => {
      expect(sourceClassSelect).toHaveTextContent('Nursery');
    });

    fireEvent.change(screen.getByLabelText('Source Class'), { target: { value: 'class-nursery' } });

    await waitFor(() => {
      expect(progressionApi.getRules).toHaveBeenCalledWith(expect.objectContaining({
        source_class_id: 'class-nursery',
        page: 1,
      }));
    });

    fireEvent.change(screen.getByLabelText('Terminal Status'), { target: { value: 'true' } });

    await waitFor(() => {
      expect(progressionApi.getRules).toHaveBeenCalledWith(expect.objectContaining({
        source_class_id: 'class-nursery',
        is_terminal: true,
        page: 1,
      }));
    });
  });

  it('renders ErrorState when rules matrix query fails', async () => {
    vi.mocked(progressionApi.getRules).mockRejectedValue(new Error('Matrix Load Failure'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Academic Progression Configuration Error')).toBeInTheDocument();
      expect(screen.getByText('Matrix Load Failure')).toBeInTheDocument();
    });
  });

  it('invokes rules query refetch when ErrorState Retry is clicked', async () => {
    vi.mocked(progressionApi.getRules).mockRejectedValueOnce(new Error('Temporary Failure'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProgressionPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Temporary Failure')).toBeInTheDocument();
    });

    vi.mocked(progressionApi.getRules).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    } as any);

    const retryButton = screen.getByRole('button', { name: 'Retry Request' });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.queryByText('Temporary Failure')).not.toBeInTheDocument();
      expect(progressionApi.getRules).toHaveBeenCalledTimes(2);
    });
  });
});
