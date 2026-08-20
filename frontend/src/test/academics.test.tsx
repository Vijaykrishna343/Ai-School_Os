import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AcademicsPage } from '@/pages/AcademicsPage';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { academicTermsApi } from '@/services/api/academicTermsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { subjectsApi } from '@/services/api/subjectsApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn(),
    createAcademicYear: vi.fn(),
    updateAcademicYear: vi.fn(),
    deleteAcademicYear: vi.fn(),
  },
}));

vi.mock('@/services/api/academicTermsApi', () => ({
  academicTermsApi: {
    getAcademicTerms: vi.fn(),
    createAcademicTerm: vi.fn(),
    updateAcademicTerm: vi.fn(),
    deleteAcademicTerm: vi.fn(),
  },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: {
    getSchoolClasses: vi.fn(),
    createSchoolClass: vi.fn(),
    updateSchoolClass: vi.fn(),
    deleteSchoolClass: vi.fn(),
  },
}));

vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: {
    getSectionsByClass: vi.fn(),
    createSection: vi.fn(),
    updateSection: vi.fn(),
    deleteSection: vi.fn(),
  },
}));

vi.mock('@/services/api/subjectsApi', () => ({
  subjectsApi: {
    getSubjects: vi.fn(),
    getSubject: vi.fn(),
    createSubject: vi.fn(),
    updateSubject: vi.fn(),
    deleteSubject: vi.fn(),
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

describe('AcademicsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      user: { id: 'admin-1', school_id: 'school-123', email: 'admin@school.com', first_name: 'Admin', is_active: true },
      permissions: [
        'academic_year.view',
        'academic_year.create',
        'academic_year.update',
        'academic_year.delete',
        'academic_term.view',
        'academic_term.create',
        'academic_term.update',
        'academic_term.delete',
        'class.view',
        'class.create',
        'class.update',
        'class.delete',
        'section.view',
        'section.create',
        'section.update',
        'section.delete',
        'subject.view',
        'subject.create',
        'subject.update',
        'subject.delete',
      ],
    });

    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [
        {
          id: 'ay-1',
          school_id: 'school-123',
          name: '2026-2027',
          start_date: '2026-04-01',
          end_date: '2027-03-31',
          status: 'ACTIVE',
        },
        {
          id: 'ay-2',
          school_id: 'school-123',
          name: '2027-2028',
          start_date: '2027-04-01',
          end_date: '2028-03-31',
          status: 'UPCOMING',
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    vi.mocked(academicTermsApi.getAcademicTerms).mockResolvedValue({
      items: [
        {
          id: 'term-1',
          school_id: 'school-123',
          academic_year_id: 'ay-1',
          name: 'Term 1',
          code: 'TERM1',
          start_date: '2026-04-01',
          end_date: '2026-09-30',
          display_order: 1,
          is_active: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [
        {
          id: 'class-1',
          school_id: 'school-123',
          name: 'Class 10',
          display_order: 10,
          status: 'ACTIVE',
        },
        {
          id: 'class-2',
          school_id: 'school-123',
          name: 'Class 11',
          display_order: 11,
          status: 'ACTIVE',
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    vi.mocked(sectionsApi.getSectionsByClass).mockResolvedValue({
      items: [
        {
          id: 'sec-1',
          school_class_id: 'class-1',
          name: 'A',
          capacity: 40,
          room_number: '101',
          status: 'ACTIVE',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    vi.mocked(subjectsApi.getSubjects).mockResolvedValue({
      items: [
        {
          id: 'sub-1',
          school_id: 'school-123',
          subject_code: 'MAT101',
          subject_name: 'Mathematics',
          description: 'Algebra and Calculus',
          is_optional: false,
          status: 'ACTIVE',
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
  });

  it('renders academics layout with tabs and loads academic years by default', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Academic Architecture')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('2026-2027')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('can switch tabs to school classes and displays the class details', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const classesTab = screen.getByRole('button', { name: /School Classes/i });
    fireEvent.click(classesTab);

    await waitFor(() => {
      expect(screen.getByText('Class 10')).toBeInTheDocument();
    });
  });

  it('can switch to Academic Terms tab and filters work', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const termsTab = screen.getByRole('button', { name: /Academic Terms/i });
    fireEvent.click(termsTab);

    await waitFor(() => {
      expect(screen.getByText('Term 1')).toBeInTheDocument();
    });

    const yearFilterSelect = screen.getByRole('combobox');
    fireEvent.change(yearFilterSelect, { target: { value: 'ay-1' } });

    await waitFor(() => {
      expect(academicTermsApi.getAcademicTerms).toHaveBeenCalledWith(expect.objectContaining({
        academic_year_id: 'ay-1',
      }));
    });
  });

  it('can switch to Sections tab and Class selector works', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const sectionsTab = screen.getByRole('button', { name: /Sections/i });
    fireEvent.click(sectionsTab);

    await waitFor(() => {
      expect(screen.getByText('Section A')).toBeInTheDocument();
    });

    const classSelect = screen.getByRole('combobox');
    fireEvent.change(classSelect, { target: { value: 'class-1' } });

    await waitFor(() => {
      expect(sectionsApi.getSectionsByClass).toHaveBeenCalledWith('class-1', expect.anything());
    });
  });

  it('renders Subjects tab, displays subjects list, and enables filtering', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const subjectsTab = screen.getByRole('button', { name: /Subjects/i });
    fireEvent.click(subjectsTab);

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
      expect(screen.getByText('MAT101')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search by subject code or name...');
    fireEvent.change(searchInput, { target: { value: 'Science' } });

    await waitFor(() => {
      expect(subjectsApi.getSubjects).toHaveBeenCalledWith(expect.objectContaining({
        subject_name: 'Science',
      }));
    });
  });

  it('opens and closes the subject create modal successfully', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const subjectsTab = screen.getByRole('button', { name: /Subjects/i });
    fireEvent.click(subjectsTab);

    await waitFor(() => {
      expect(screen.getByText('+ Add Subject')).toBeInTheDocument();
    });

    const addBtn = screen.getByText('+ Add Subject');
    fireEvent.click(addBtn);

    expect(screen.getByRole('heading', { name: 'Create Subject' })).toBeInTheDocument();

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Create Subject' })).not.toBeInTheDocument();
    });
  });

  it('opens subject edit modal with prefilled data', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const subjectsTab = screen.getByRole('button', { name: /Subjects/i });
    fireEvent.click(subjectsTab);

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
    });

    const editBtn = screen.getByRole('button', { name: 'Edit' });
    fireEvent.click(editBtn);

    expect(screen.getByRole('heading', { name: 'Edit Subject' })).toBeInTheDocument();
    expect(screen.getByLabelText('Subject Code *')).toHaveValue('MAT101');
    expect(screen.getByLabelText('Subject Name *')).toHaveValue('Mathematics');
  });

  it('opens subject delete confirmation dialog', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const subjectsTab = screen.getByRole('button', { name: /Subjects/i });
    fireEvent.click(subjectsTab);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    });

    const deleteBtn = screen.getByRole('button', { name: 'Delete' });
    fireEvent.click(deleteBtn);

    expect(screen.getByRole('heading', { name: 'Soft Delete Mathematics' })).toBeInTheDocument();
  });

  it('respects permission gating and hides mutation actions if unauthorized', async () => {
    // Restrict permissions
    useAuthStore.setState({
      user: { id: 'admin-1', school_id: 'school-123', email: 'admin@school.com', first_name: 'Admin', is_active: true },
      permissions: ['academic_year.view'],
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('2026-2027')).toBeInTheDocument();
    });

    // Verify Add button is hidden
    expect(screen.queryByText('+ Add Academic Year')).not.toBeInTheDocument();

    // Verify Edit and Delete row buttons are hidden
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
  });

  it('renders page-level ErrorState when a list query fails', async () => {
    vi.mocked(academicYearsApi.getAcademicYears).mockRejectedValue(new Error('API Failure'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Administrative Academics Error')).toBeInTheDocument();
      expect(screen.getByText('API Failure')).toBeInTheDocument();
    });
  });

  it('renders EmptyState when list data is empty', async () => {
    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No academic years defined yet.')).toBeInTheDocument();
    });
  });

  it('allows single-click class selection in Create Section modal after rapid tab switching (DEF-10-1)', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AcademicsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch rapidly between tabs
    const yearsTab = screen.getByText('Academic Years');
    const classesTab = screen.getByText('School Classes');
    const sectionsTab = screen.getByText('Sections');

    fireEvent.click(classesTab);
    fireEvent.click(sectionsTab);
    fireEvent.click(yearsTab);
    fireEvent.click(sectionsTab);

    // Open Create Section Modal
    await waitFor(() => {
      expect(screen.getByText('+ Add Section')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('+ Add Section'));

    // Verify modal is open and select dropdown is populated
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Create Section' })).toBeInTheDocument();
    });

    const selects = screen.getAllByRole('combobox');
    const select = selects[selects.length - 1];
    expect(select).toBeInTheDocument();
    expect(select).not.toBeDisabled();

    // Single click / change selection to Grade 6
    fireEvent.change(select, { target: { value: 'class-2' } });

    expect((select as HTMLSelectElement).value).toBe('class-2');
  });
});
