import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AttendancePage } from '@/pages/AttendancePage';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { attendanceApi } from '@/services/api/attendanceApi';

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

vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: {
    getSectionsByClass: vi.fn(),
  },
}));

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn(),
    getStudent: vi.fn(),
    createStudent: vi.fn(),
    updateStudent: vi.fn(),
    deleteStudent: vi.fn(),
    getStudentEnrollmentHistory: vi.fn(),
  },
}));

vi.mock('@/services/api/attendanceApi', () => ({
  attendanceApi: {
    getAttendance: vi.fn(),
    getAttendanceById: vi.fn(),
    createAttendance: vi.fn(),
    createBulkAttendance: vi.fn(),
    updateAttendance: vi.fn(),
    deleteAttendance: vi.fn(),
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

describe('AttendancePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default permissions setup
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'registrar@school.com', school_id: 'school-1' } as any,
      permissions: ['attendance.view', 'attendance.create', 'attendance.update', 'attendance.delete'],
    });

    // Default mock resolves
    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [
        { id: 'ay-2026', school_id: 'school-1', name: '2026-2027', status: 'ACTIVE' },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [
        { id: 'class-nursery', school_id: 'school-1', name: 'Nursery', display_order: 1, status: 'ACTIVE' },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(sectionsApi.getSectionsByClass).mockResolvedValue({
      items: [
        { id: 'sec-nursery-a', school_class_id: 'class-nursery', name: 'A', capacity: 30, status: 'ACTIVE' },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [
        { id: 'stud-1', full_name: 'John Doe', admission_number: 'ADM-001', status: 'ACTIVE' },
        { id: 'stud-2', full_name: 'Jane Smith', admission_number: 'ADM-002', status: 'ACTIVE' },
      ],
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);

    vi.mocked(attendanceApi.getAttendance).mockResolvedValue({
      items: [
        {
          id: 'att-1',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          school_class_id: 'class-nursery',
          section_id: 'sec-nursery-a',
          student_id: 'stud-1',
          attendance_date: '2026-08-17',
          status: 'ABSENT',
          remarks: 'Medical leave request',
        },
      ],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    } as any);
  });

  const selectTestContext = async () => {
    const classSelect = screen.getByLabelText('Class');
    await waitFor(() => {
      expect(classSelect).toHaveTextContent('Nursery');
    });
    fireEvent.change(classSelect, { target: { value: 'class-nursery' } });

    const sectionSelect = screen.getByLabelText('Section');
    await waitFor(() => {
      expect(sectionSelect).toHaveTextContent('A');
    });
    fireEvent.change(sectionSelect, { target: { value: 'sec-nursery-a' } });
  };

  it('1. renders daily attendance page title', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Daily Attendance Registry')).toBeInTheDocument();
  });

  it('2. renders selectors layout fields', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Academic Year')).toBeInTheDocument();
      expect(screen.getByLabelText('Class')).toBeInTheDocument();
      expect(screen.getByLabelText('Section')).toBeInTheDocument();
      expect(screen.getByLabelText('Attendance Date')).toBeInTheDocument();
    });
  });

  it('3. class selection loads class-dependent sections and clearing class resets selection', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const classSelect = screen.getByLabelText('Class');
    await waitFor(() => {
      expect(classSelect).toHaveTextContent('Nursery');
    });

    fireEvent.change(classSelect, { target: { value: 'class-nursery' } });

    await waitFor(() => {
      expect(sectionsApi.getSectionsByClass).toHaveBeenCalledWith('class-nursery', expect.any(Object));
    });

    fireEvent.change(classSelect, { target: { value: '' } });
    expect(screen.getByLabelText('Section')).toBeDisabled();
  });

  it('4. displays student registry table when valid context is selected', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(studentsApi.getStudents).toHaveBeenCalledWith(
        expect.objectContaining({ section_id: 'sec-nursery-a', status: 'ACTIVE' })
      );
      expect(attendanceApi.getAttendance).toHaveBeenCalledWith(
        expect.objectContaining({ section_id: 'sec-nursery-a' })
      );
    });
  });

  it('5 & 6. merges existing attendance data correctly and defaults missing to PRESENT', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const johnRemarks = screen.getByDisplayValue('Medical leave request');
    expect(johnRemarks).toBeInTheDocument();

    const janeRow = screen.getByText('Jane Smith').closest('tr');
    const janeSelect = janeRow?.querySelector('select') as HTMLSelectElement;
    expect(janeSelect.value).toBe('PRESENT');
  });

  it('7 & 8. save button issues createBulkAttendance for new records', async () => {
    vi.mocked(attendanceApi.getAttendance).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: 'Save Registry Roll' });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(attendanceApi.createBulkAttendance).toHaveBeenCalledWith(
        expect.objectContaining({
          section_id: 'sec-nursery-a',
          records: expect.arrayContaining([
            expect.objectContaining({ student_id: 'stud-1', status: 'PRESENT' }),
            expect.objectContaining({ student_id: 'stud-2', status: 'PRESENT' }),
          ]),
        })
      );
    });
  });

  it('9 & 10. save button issues updateAttendance only for modified existing records', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const johnRow = screen.getByText('John Doe').closest('tr');
    const johnSelect = johnRow?.querySelector('select') as HTMLSelectElement;
    fireEvent.change(johnSelect, { target: { value: 'EXCUSED' } });

    const saveButton = screen.getByRole('button', { name: 'Save Registry Roll' });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(attendanceApi.updateAttendance).toHaveBeenCalledWith(
        'att-1',
        expect.objectContaining({ status: 'EXCUSED' })
      );
      expect(attendanceApi.createBulkAttendance).toHaveBeenCalledWith(
        expect.objectContaining({
          section_id: 'sec-nursery-a',
          records: [expect.objectContaining({ student_id: 'stud-2', status: 'PRESENT' })],
        })
      );
    });
  });

  it('11. create permission disables new record controls', async () => {
    useAuthStore.setState({
      permissions: ['attendance.view', 'attendance.update'],
    });

    vi.mocked(attendanceApi.getAttendance).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const johnRow = screen.getByText('John Doe').closest('tr');
    const johnSelect = johnRow?.querySelector('select') as HTMLSelectElement;
    expect(johnSelect).toBeDisabled();

    const saveButton = screen.getByRole('button', { name: 'Save Registry Roll' });
    expect(saveButton).toBeDisabled();
  });

  it('12. update permission disables existing record editing controls', async () => {
    useAuthStore.setState({
      permissions: ['attendance.view', 'attendance.create'],
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const johnRow = screen.getByText('John Doe').closest('tr');
    const johnSelect = johnRow?.querySelector('select') as HTMLSelectElement;
    expect(johnSelect).toBeDisabled();

    const janeRow = screen.getByText('Jane Smith').closest('tr');
    const janeSelect = janeRow?.querySelector('select') as HTMLSelectElement;
    expect(janeSelect).not.toBeDisabled();
  });

  it('13. renders ErrorState when query fails', async () => {
    vi.mocked(schoolClassesApi.getSchoolClasses).mockRejectedValue(new Error('Network Database Error'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Daily Attendance Registry Configuration Error')).toBeInTheDocument();
      expect(screen.getByText('Network Database Error')).toBeInTheDocument();
    });
  });

  it('14 & 15. save error shows mutation alert and handles 409 conflict duplicates', async () => {
    vi.mocked(attendanceApi.createBulkAttendance).mockRejectedValue({
      status: 409,
      message: '409 Conflict',
    });

    vi.mocked(attendanceApi.getAttendance).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: 'Save Registry Roll' });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Attendance records already exist/i)).toBeInTheDocument();
    });
  });

  it('16. renders empty roster view message when section has no active students', async () => {
    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AttendancePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('No active students enrolled in this section.')).toBeInTheDocument();
    });
  });
});
