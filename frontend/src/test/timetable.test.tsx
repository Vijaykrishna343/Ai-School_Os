import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TimetablePage } from '@/pages/TimetablePage';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { subjectsApi } from '@/services/api/subjectsApi';
import { teachersApi } from '@/services/api/teachersApi';
import { timetableApi } from '@/services/api/timetableApi';
import { periodSlotsApi } from '@/services/api/periodSlotsApi';
import { classroomsApi } from '@/services/api/classroomsApi';
import { substitutionsApi } from '@/services/api/substitutionsApi';

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: { getAcademicYears: vi.fn() },
}));
vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: { getSchoolClasses: vi.fn() },
}));
vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: { getSectionsByClass: vi.fn() },
}));
vi.mock('@/services/api/subjectsApi', () => ({
  subjectsApi: { getSubjects: vi.fn() },
}));
vi.mock('@/services/api/teachersApi', () => ({
  teachersApi: { getTeachers: vi.fn() },
}));
vi.mock('@/services/api/timetableApi', () => ({
  timetableApi: {
    getTimetables: vi.fn(),
    getTimetable: vi.fn(),
    createTimetable: vi.fn(),
    getSectionTimetable: vi.fn(),
    getTeacherSchedule: vi.fn(),
    publishTimetable: vi.fn(),
    archiveTimetable: vi.fn(),
    addEntry: vi.fn(),
    listEntries: vi.fn(),
    updateEntry: vi.fn(),
    deleteEntry: vi.fn(),
  },
}));
vi.mock('@/services/api/periodSlotsApi', () => ({
  periodSlotsApi: {
    getPeriodSlots: vi.fn(),
    getPeriodSlot: vi.fn(),
    createPeriodSlot: vi.fn(),
    updatePeriodSlot: vi.fn(),
    deletePeriodSlot: vi.fn(),
  },
}));
vi.mock('@/services/api/classroomsApi', () => ({
  classroomsApi: {
    getClassrooms: vi.fn(),
    getClassroom: vi.fn(),
    createClassroom: vi.fn(),
    updateClassroom: vi.fn(),
    deleteClassroom: vi.fn(),
  },
}));
vi.mock('@/services/api/substitutionsApi', () => ({
  substitutionsApi: {
    getSubstitutions: vi.fn(),
    getSubstitution: vi.fn(),
    createSubstitution: vi.fn(),
    updateSubstitution: vi.fn(),
    deleteSubstitution: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

const renderTimetablePage = () => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TimetablePage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock data
const mockYears = {
  items: [{ id: 'ay-2026', school_id: 'school-1', name: '2026-2027', status: 'ACTIVE' }],
  total: 1, page: 1, page_size: 100, total_pages: 1,
};

const mockClasses = {
  items: [{ id: 'class-5', school_id: 'school-1', name: 'Class 5', display_order: 5, status: 'ACTIVE' }],
  total: 1, page: 1, page_size: 100, total_pages: 1,
};

const mockSections = {
  items: [{ id: 'sec-5a', school_class_id: 'class-5', name: 'A', capacity: 30, status: 'ACTIVE' }],
  total: 1, page: 1, page_size: 100, total_pages: 1,
};

const mockPeriodSlots = {
  items: [
    { id: 'ps-1', school_id: 'school-1', name: 'Period 1', period_type: 'REGULAR', start_time: '08:30:00', end_time: '09:15:00', display_order: 1, created_at: '', updated_at: '' },
    { id: 'ps-2', school_id: 'school-1', name: 'Lunch', period_type: 'LUNCH', start_time: '12:00:00', end_time: '12:30:00', display_order: 2, created_at: '', updated_at: '' },
  ],
  total: 2, page: 1, page_size: 100, total_pages: 1,
};

const mockClassrooms = {
  items: [
    { id: 'cr-101', school_id: 'school-1', room_number: '101', building_name: 'Main', capacity: 40, room_type: 'CLASSROOM', created_at: '', updated_at: '' },
    { id: 'cr-lab1', school_id: 'school-1', room_number: 'Lab-1', building_name: 'Science Block', capacity: 30, room_type: 'LABORATORY', created_at: '', updated_at: '' },
  ],
  total: 2, page: 1, page_size: 100, total_pages: 1,
};

const mockSubjects = {
  items: [{ id: 'sub-math', subject_name: 'Mathematics', subject_code: 'MATH' }],
  total: 1, page: 1, page_size: 200, total_pages: 1,
};

const mockTeachers = {
  items: [{ id: 'tch-1', first_name: 'Alice', last_name: 'Johnson', employee_id: 'EMP-001' }],
  total: 1, page: 1, page_size: 200, total_pages: 1,
};

const mockTimetableDetail = {
  id: 'tt-1',
  school_id: 'school-1',
  academic_year_id: 'ay-2026',
  school_class_id: 'class-5',
  section_id: 'sec-5a',
  academic_term_id: null,
  status: 'DRAFT',
  is_active: true,
  created_at: '',
  updated_at: '',
  entries: [
    {
      id: 'entry-1',
      timetable_id: 'tt-1',
      day_of_week: 'MONDAY',
      period_slot_id: 'ps-1',
      subject_id: 'sub-math',
      teacher_id: 'tch-1',
      classroom_id: 'cr-101',
      created_at: '',
      updated_at: '',
      period_slot: { id: 'ps-1', name: 'Period 1', period_type: 'REGULAR', start_time: '08:30:00', end_time: '09:15:00', display_order: 1 },
      subject: { id: 'sub-math', subject_name: 'Mathematics', subject_code: 'MATH' },
      teacher: { id: 'tch-1', first_name: 'Alice', last_name: 'Johnson', employee_id: 'EMP-001' },
      classroom: { id: 'cr-101', room_number: '101', building_name: 'Main', capacity: 40, room_type: 'CLASSROOM' },
    },
  ],
};

const mockSubstitutions = {
  items: [
    {
      id: 'sub-rec-1',
      school_id: 'school-1',
      timetable_entry_id: 'entry-1',
      substitution_date: '2026-08-18',
      original_teacher_id: 'tch-1',
      substitute_teacher_id: 'tch-2',
      remarks: 'Sick leave',
      created_at: '',
      updated_at: '',
      original_teacher: { id: 'tch-1', first_name: 'Alice', last_name: 'Johnson', employee_id: 'EMP-001' },
      substitute_teacher: { id: 'tch-2', first_name: 'Bob', last_name: 'Williams', employee_id: 'EMP-002' },
      timetable_entry: mockTimetableDetail.entries[0],
    },
  ],
  total: 1, page: 1, page_size: 100, total_pages: 1,
};

describe('TimetablePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'admin@school.com', school_id: 'school-1' } as any,
      permissions: [
        'timetable.view', 'timetable.create', 'timetable.update', 'timetable.delete',
        'timetable.publish', 'timetable.archive',
        'substitution.view', 'substitution.create', 'substitution.delete',
      ],
    });

    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue(mockYears as any);
    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue(mockClasses as any);
    vi.mocked(sectionsApi.getSectionsByClass).mockResolvedValue(mockSections as any);
    vi.mocked(subjectsApi.getSubjects).mockResolvedValue(mockSubjects as any);
    vi.mocked(teachersApi.getTeachers).mockResolvedValue(mockTeachers as any);
    vi.mocked(periodSlotsApi.getPeriodSlots).mockResolvedValue(mockPeriodSlots as any);
    vi.mocked(classroomsApi.getClassrooms).mockResolvedValue(mockClassrooms as any);
    vi.mocked(timetableApi.getSectionTimetable).mockResolvedValue(mockTimetableDetail as any);
    vi.mocked(substitutionsApi.getSubstitutions).mockResolvedValue(mockSubstitutions as any);
  });

  // -----------------------------------------------------------
  // 1. RENDER & HEADER
  // -----------------------------------------------------------
  it('renders the timetable workspace header', async () => {
    renderTimetablePage();
    await waitFor(() => {
      expect(screen.getByText('Timetable & Scheduling Workspace')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 2. TAB NAVIGATION
  // -----------------------------------------------------------
  it('renders all four tabs', async () => {
    renderTimetablePage();
    await waitFor(() => {
      expect(screen.getByText('Timetable Builder')).toBeInTheDocument();
      expect(screen.getByText('Period Slots')).toBeInTheDocument();
      expect(screen.getByText('Classrooms')).toBeInTheDocument();
      expect(screen.getByText('Teacher Substitutions')).toBeInTheDocument();
    });
  });

  it('switches tabs on click', async () => {
    renderTimetablePage();
    await waitFor(() => {
      expect(screen.getByText('Timetable Builder')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Period Slots'));
    await waitFor(() => {
      expect(screen.getByText('PERIOD_SLOT_CONFIGURATION')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Classrooms'));
    await waitFor(() => {
      expect(screen.getByText('CLASSROOM_REGISTRY')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Teacher Substitutions'));
    await waitFor(() => {
      expect(screen.getByText('TEACHER_SUBSTITUTION_LOG')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 3. TIMETABLE BUILDER — CONTEXT SELECTORS
  // -----------------------------------------------------------
  it('renders academic year, class, section selectors in builder tab', async () => {
    renderTimetablePage();
    await waitFor(() => {
      expect(screen.getByLabelText('Academic Year')).toBeInTheDocument();
      expect(screen.getByLabelText('Class')).toBeInTheDocument();
      expect(screen.getByLabelText('Section')).toBeInTheDocument();
    });
  });

  it('auto-selects the active academic year', async () => {
    renderTimetablePage();
    await waitFor(() => {
      const yearSelect = screen.getByLabelText('Academic Year') as HTMLSelectElement;
      expect(yearSelect.value).toBe('ay-2026');
    });
  });

  // -----------------------------------------------------------
  // 4. TIMETABLE BUILDER — GRID
  // -----------------------------------------------------------
  it('renders timetable grid with entries after selecting section', async () => {
    renderTimetablePage();

    // Wait for years to load and auto-select
    await waitFor(() => {
      const yearSelect = screen.getByLabelText('Academic Year') as HTMLSelectElement;
      expect(yearSelect.value).toBe('ay-2026');
    });

    // Select class
    fireEvent.change(screen.getByLabelText('Class'), { target: { value: 'class-5' } });

    // Wait for sections to load, then select section
    await waitFor(() => {
      expect(sectionsApi.getSectionsByClass).toHaveBeenCalledWith('class-5', { page: 1, page_size: 100 });
    });

    await waitFor(() => {
      const sectionSelect = screen.getByLabelText('Section') as HTMLSelectElement;
      expect(sectionSelect.disabled).toBe(false);
    });

    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'sec-5a' } });

    await waitFor(() => {
      expect(screen.getByText('MATH')).toBeInTheDocument();
    });
  });

  it('shows DRAFT status badge for draft timetable', async () => {
    renderTimetablePage();

    await waitFor(() => {
      expect((screen.getByLabelText('Academic Year') as HTMLSelectElement).value).toBe('ay-2026');
    });

    fireEvent.change(screen.getByLabelText('Class'), { target: { value: 'class-5' } });

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'sec-5a' } });

    await waitFor(() => {
      expect(screen.getByText('DRAFT')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 5. TIMETABLE BUILDER — LIFECYCLE
  // -----------------------------------------------------------
  it('shows Publish button for DRAFT timetable', async () => {
    renderTimetablePage();

    await waitFor(() => {
      expect((screen.getByLabelText('Academic Year') as HTMLSelectElement).value).toBe('ay-2026');
    });

    fireEvent.change(screen.getByLabelText('Class'), { target: { value: 'class-5' } });

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'sec-5a' } });

    await waitFor(() => {
      expect(screen.getByText('Publish')).toBeInTheDocument();
    });
  });

  it('calls publishTimetable when Publish is clicked', async () => {
    vi.mocked(timetableApi.publishTimetable).mockResolvedValue({
      ...mockTimetableDetail,
      status: 'PUBLISHED',
    } as any);

    renderTimetablePage();

    await waitFor(() => {
      expect((screen.getByLabelText('Academic Year') as HTMLSelectElement).value).toBe('ay-2026');
    });

    fireEvent.change(screen.getByLabelText('Class'), { target: { value: 'class-5' } });

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Section'), { target: { value: 'sec-5a' } });

    await waitFor(() => {
      expect(screen.getByText('Publish')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Publish'));
    await waitFor(() => {
      expect(timetableApi.publishTimetable).toHaveBeenCalledWith('tt-1');
    });
  });


  // -----------------------------------------------------------
  // 6. PERIOD SLOTS TAB
  // -----------------------------------------------------------
  it('renders period slots table', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Period Slots'));

    await waitFor(() => {
      expect(screen.getByText('Period 1')).toBeInTheDocument();
      expect(screen.getByText('Lunch')).toBeInTheDocument();
    });
  });

  it('shows Add Period Slot button', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Period Slots'));

    await waitFor(() => {
      expect(screen.getByText('Add Period Slot')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 7. CLASSROOMS TAB
  // -----------------------------------------------------------
  it('renders classrooms table', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Classrooms'));

    await waitFor(() => {
      expect(screen.getByText('101')).toBeInTheDocument();
      expect(screen.getByText('Lab-1')).toBeInTheDocument();
    });
  });

  it('shows Add Classroom button', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Classrooms'));

    await waitFor(() => {
      expect(screen.getByText('Add Classroom')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 8. SUBSTITUTIONS TAB
  // -----------------------------------------------------------
  it('renders substitutions table with data', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Teacher Substitutions'));

    await waitFor(() => {
      expect(screen.getByText('2026-08-18')).toBeInTheDocument();
      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      expect(screen.getByText('Bob Williams')).toBeInTheDocument();
    });
  });

  it('shows Record Substitution button', async () => {
    renderTimetablePage();
    fireEvent.click(screen.getByText('Teacher Substitutions'));

    await waitFor(() => {
      expect(screen.getByText('Record Substitution')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 9. RBAC — VIEW-ONLY PERMISSIONS
  // -----------------------------------------------------------
  it('hides write-action buttons when user lacks create/update/delete permissions', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'viewer@school.com', school_id: 'school-1' } as any,
      permissions: ['timetable.view', 'substitution.view'],
    });

    renderTimetablePage();

    // Period Slots tab
    fireEvent.click(screen.getByText('Period Slots'));
    await waitFor(() => {
      expect(screen.queryByText('Add Period Slot')).not.toBeInTheDocument();
    });

    // Classrooms tab
    fireEvent.click(screen.getByText('Classrooms'));
    await waitFor(() => {
      expect(screen.queryByText('Add Classroom')).not.toBeInTheDocument();
    });

    // Substitutions tab
    fireEvent.click(screen.getByText('Teacher Substitutions'));
    await waitFor(() => {
      expect(screen.queryByText('Record Substitution')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------
  // 10. ERROR STATE — PERIOD SLOTS
  // -----------------------------------------------------------
  it('shows error state when period slots fail to load', async () => {
    vi.mocked(periodSlotsApi.getPeriodSlots).mockRejectedValue({ message: 'Network error' });

    renderTimetablePage();
    fireEvent.click(screen.getByText('Period Slots'));

    await waitFor(() => {
      expect(screen.getByText('Failed to load period slots')).toBeInTheDocument();
    });
  });
});
