import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StudentsPage } from '@/pages/StudentsPage';
import { studentsApi } from '@/services/api/studentsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { parentsApi } from '@/services/api/parentsApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn(),
    getStudent: vi.fn(),
    createStudent: vi.fn(),
    updateStudent: vi.fn(),
    deleteStudent: vi.fn(),
    getStudentEnrollmentHistory: vi.fn(),
    getTransferCertificates: vi.fn(),
    issueTransferCertificate: vi.fn(),
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

const mockStudent = {
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
};

const mockEnrollmentHistory = {
  student_id: 'student-1',
  enrollments: [
    {
      id: 'history-1',
      student_id: 'student-1',
      academic_year_id: 'ay-1',
      school_class_id: 'class-1',
      section_id: 'sec-1',
      roll_number: '12',
      status: 'ACTIVE',
      promotion_decision: 'PROMOTED',
      remarks: 'Promoted to Class 2',
      created_at: '2026-04-01T00:00:00Z',
      academic_year: { id: 'ay-1', name: '2025-2026' },
      school_class: { id: 'class-1', name: 'Class 1' },
      section: { id: 'sec-1', name: 'A' },
    },
  ],
  total: 1,
};

const mockTcList = {
  student_id: 'student-1',
  certificates: [
    {
      id: 'tc-1',
      school_id: 'school-123',
      student_id: 'student-1',
      tc_number: 'TC-2026-001',
      issue_date: '2026-08-15',
      reason: 'Relocation',
      remarks: 'Good conduct',
      status: 'ISSUED',
      created_at: '2026-08-15T10:00:00Z',
    },
  ],
  total: 1,
};

describe('StudentsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'registrar@school.edu', school_id: 'school-123' } as any,
      permissions: ['student.view', 'student.create', 'student.update', 'student.delete', 'student.tc.view', 'student.tc.create'],
    });

    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [mockStudent as any],
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
      items: [mockStudent.parent as any],
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

    vi.mocked(studentsApi.getStudentEnrollmentHistory).mockResolvedValue(mockEnrollmentHistory as any);
    vi.mocked(studentsApi.getTransferCertificates).mockResolvedValue(mockTcList as any);
  });

  const renderPage = () => {
    const queryClient = createTestQueryClient();
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <StudentsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  // 1. Existing student directory renders
  it('renders student list table with correct details', async () => {
    renderPage();
    expect(screen.getByText('Student Registry')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Harry Potter')).toBeInTheDocument();
      expect(screen.getByText('ADM-1001')).toBeInTheDocument();
      expect(screen.getByText('Gryffindor Class (A)')).toBeInTheDocument();
    });
  });

  // 2. View button opens profile dossier drawer
  it('opens profile dossier drawer when View button is clicked', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'View' })).toBeInTheDocument();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByRole('button', { name: 'View' }));

    await waitFor(() => {
      expect(screen.getByText('Student Profile Dossier')).toBeInTheDocument();
      expect(screen.getByText('Admission No: ADM-1001')).toBeInTheDocument();
    });
  });

  // 3. Certificates history tab switching
  it('switches to certificates registry tab when tab clicked', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Issued Certificates Registry' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Issued Certificates Registry' }));

    await waitFor(() => {
      expect(screen.getByText('OFFICIAL_CERTIFICATE_ISSUANCE_HISTORY')).toBeInTheDocument();
    });
  });

  // 4. Issue TC button visibility
  it('shows + TC button in student actions column', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '+ TC' })).toBeInTheDocument();
    });
  });

  // 5. TC Modal rendering and submission
  it('opens TC modal, fills form, and triggers TC issuance mutation', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '+ TC' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '+ TC' }));

    await waitFor(() => {
      expect(screen.getByText('Issue Transfer Certificate (TC)')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('e.g. Parent Transfer / Course Completed'), { target: { value: 'Parent Relocation' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate TC & Print A4 PDF' }));
  });

  // 6. Registration modal trigger
  it('opens register new student modal when top action button is clicked', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '+ Register New Student' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '+ Register New Student' }));

    await waitFor(() => {
      expect(screen.getByText('Register New Student')).toBeInTheDocument();
      expect(screen.getByText('First Name *')).toBeInTheDocument();
    });
  });
});
