import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AcademicsPage } from '@/pages/AcademicsPage';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { academicTermsApi } from '@/services/api/academicTermsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';

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
      ],
      total: 1,
      page: 1,
      page_size: 100,
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
      page_size: 100,
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
      ],
      total: 1,
      page: 1,
      page_size: 100,
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
      page_size: 100,
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
    
    // Default tab active is Academic Years
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

    // Switch to School Classes Tab
    const classesTab = screen.getByRole('button', { name: /School Classes/i });
    fireEvent.click(classesTab);

    await waitFor(() => {
      expect(screen.getByText('Class 10')).toBeInTheDocument();
    });
  });
});
