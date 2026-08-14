import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StudentsPage } from '@/pages/StudentsPage';
import { studentsApi } from '@/services/api/studentsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { parentsApi } from '@/services/api/parentsApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn(),
    createStudent: vi.fn(),
    updateStudent: vi.fn(),
    deleteStudent: vi.fn(),
    getStudentEnrollmentHistory: vi.fn(),
  },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: {
    getSchoolClasses: vi.fn(),
  },
}));

vi.mock('@/services/api/parentsApi', () => ({
  parentsApi: {
    getParents: vi.fn(),
  },
}));

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn(),
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

describe('StudentsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [
        {
          id: 'student-1',
          school_id: 'school-123',
          academic_year_id: 'ay-1',
          school_class_id: 'class-1',
          section_id: 'sec-1',
          parent_id: 'parent-1',
          admission_number: 'ADM-1001',
          roll_number: '12',
          first_name: 'Harry',
          last_name: 'Potter',
          gender: 'MALE',
          date_of_birth: '2012-07-31',
          admission_date: '2026-04-01',
          address_line1: '4 Privet Drive',
          city: 'Little Whinging',
          district: 'Surrey',
          state: 'England',
          postal_code: 'GU21',
          status: 'ACTIVE',
          school_class: { id: 'class-1', name: 'Gryffindor Class', school_id: 'school-123', display_order: 1, status: 'ACTIVE' },
          section: { id: 'sec-1', school_class_id: 'class-1', name: 'A', capacity: 40, status: 'ACTIVE' },
          parent: {
            id: 'parent-1',
            school_id: 'school-123',
            father_name: 'James Potter',
            relationship: 'FATHER',
            primary_phone: '1234567890',
            address_line1: '123 St',
            city: 'London',
            district: 'Dist',
            state: 'State',
            postal_code: '1234',
            is_active: true,
          },
        } as any,
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [{ id: 'class-1', school_id: 'school-123', name: 'Gryffindor Class', display_order: 1, status: 'ACTIVE' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });

    vi.mocked(parentsApi.getParents).mockResolvedValue({
      items: [
        {
          id: 'parent-1',
          school_id: 'school-123',
          father_name: 'James Potter',
          relationship: 'FATHER',
          primary_phone: '1234567890',
          address_line1: '123 St',
          city: 'London',
          district: 'Dist',
          state: 'State',
          postal_code: '1234',
          is_active: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });

    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [{ id: 'ay-1', school_id: 'school-123', name: '2026-2027', start_date: '2026-04-01', end_date: '2027-03-31', status: 'ACTIVE' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
  });

  it('renders student list table with correct details', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <StudentsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Student Registry')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Harry Potter')).toBeInTheDocument();
      expect(screen.getByText('ADM-1001')).toBeInTheDocument();
      expect(screen.getByText('#12')).toBeInTheDocument();
      expect(screen.getByText('Gryffindor Class - Section A')).toBeInTheDocument();
      expect(screen.getByText('James Potter')).toBeInTheDocument();
    });
  });
});
