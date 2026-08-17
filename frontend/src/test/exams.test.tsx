import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ExamsPage } from '@/pages/ExamsPage';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { academicTermsApi } from '@/services/api/academicTermsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { subjectsApi } from '@/services/api/subjectsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { examsApi } from '@/services/api/examsApi';
import { examSchedulesApi } from '@/services/api/examSchedulesApi';
import { studentExamResultsApi } from '@/services/api/studentExamResultsApi';
import { reportCardsApi } from '@/services/api/reportCardsApi';

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: { getAcademicYears: vi.fn() },
}));

vi.mock('@/services/api/academicTermsApi', () => ({
  academicTermsApi: { getAcademicTerms: vi.fn() },
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

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: { getStudents: vi.fn() },
}));

vi.mock('@/services/api/examsApi', () => ({
  examsApi: {
    getExams: vi.fn(),
    getExam: vi.fn(),
    createExam: vi.fn(),
    updateExam: vi.fn(),
    deleteExam: vi.fn(),
  },
}));

vi.mock('@/services/api/examSchedulesApi', () => ({
  examSchedulesApi: {
    getExamSchedules: vi.fn(),
    getExamSchedule: vi.fn(),
    createExamSchedule: vi.fn(),
    createSchedule: vi.fn(),
    updateExamSchedule: vi.fn(),
    deleteExamSchedule: vi.fn(),
  },
}));

vi.mock('@/services/api/studentExamResultsApi', () => ({
  studentExamResultsApi: {
    getStudentExamResults: vi.fn(),
    getStudentExamResult: vi.fn(),
    createStudentExamResult: vi.fn(),
    updateStudentExamResult: vi.fn(),
    deleteStudentExamResult: vi.fn(),
  },
}));

vi.mock('@/services/api/reportCardsApi', () => ({
  reportCardsApi: {
    getReportCards: vi.fn(),
    getReportCard: vi.fn(),
    generateReportCards: vi.fn(),
    updateRemarks: vi.fn(),
    finalizeReportCard: vi.fn(),
    publishReportCard: vi.fn(),
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

describe('ExamsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'registrar@school.com', school_id: 'school-1' } as any,
      permissions: ['exam.view', 'exam.create', 'exam.update', 'exam.delete', 'marks.view', 'marks.create', 'marks.update', 'report_card.view', 'report_card.generate', 'report_card.finalize', 'report_card.publish'],
    });

    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [{ id: 'ay-2026', school_id: 'school-1', name: '2026-2027', status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(academicTermsApi.getAcademicTerms).mockResolvedValue({
      items: [{ id: 'term-1', academic_year_id: 'ay-2026', name: 'Term 1' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [{ id: 'class-nursery', school_id: 'school-1', name: 'Nursery', display_order: 1, status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(sectionsApi.getSectionsByClass).mockResolvedValue({
      items: [{ id: 'sec-nursery-a', school_class_id: 'class-nursery', name: 'A', capacity: 30, status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(subjectsApi.getSubjects).mockResolvedValue({
      items: [{ id: 'sub-english', subject_code: 'ENG', subject_name: 'English', is_optional: false, status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [
        { id: 'stud-1', first_name: 'John', last_name: 'Doe', admission_number: 'ADM-001', status: 'ACTIVE' },
        { id: 'stud-2', first_name: 'Jane', last_name: 'Smith', admission_number: 'ADM-002', status: 'ACTIVE' },
      ],
      total: 2, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(examsApi.getExams).mockResolvedValue({
      items: [
        {
          id: 'exam-mid',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          name: 'Mid Term Exams',
          assessment_type: 'MID_TERM',
          attempt_type: 'REGULAR',
          start_date: '2026-10-01',
          end_date: '2026-10-10',
          status: 'SCHEDULED',
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(examSchedulesApi.getExamSchedules).mockResolvedValue({
      items: [
        {
          id: 'sched-1',
          exam_id: 'exam-mid',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          school_class_id: 'class-nursery',
          section_id: 'sec-nursery-a',
          subject_id: 'sub-english',
          exam_date: '2026-10-02',
          start_time: '10:00:00',
          end_time: '12:00:00',
          maximum_marks: 100,
          passing_marks: 33,
          subject: { id: 'sub-english', subject_name: 'English' },
          school_class: { id: 'class-nursery', name: 'Nursery' },
          section: { id: 'sec-nursery-a', name: 'A' },
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(studentExamResultsApi.getStudentExamResults).mockResolvedValue({
      items: [
        {
          id: 'res-1',
          exam_schedule_id: 'sched-1',
          student_id: 'stud-1',
          marks_obtained: 85.00,
          remarks: 'Good performance',
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(reportCardsApi.getReportCards).mockResolvedValue({
      items: [
        {
          id: 'rc-1',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          academic_term_id: 'term-1',
          student_id: 'stud-1',
          school_class_id: 'class-nursery',
          section_id: 'sec-nursery-a',
          grade_scale_id: 'gs-1',
          evaluation_config_id: 'ec-1',
          status: 'DRAFT',
          total_max_marks: 100,
          total_obtained_marks: 85,
          percentage: 85,
          overall_grade: 'A',
          overall_grade_point: 8,
          gpa: 8,
          is_passed: true,
          total_working_days: 100,
          present_days: 95,
          attendance_percentage: 95,
          teacher_remarks: 'Excellent student',
          principal_remarks: 'Keep it up',
          student: { first_name: 'John', last_name: 'Doe' },
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);
  });

  const selectTestContext = async () => {
    const classSelect = screen.getByLabelText('Class');
    await waitFor(() => expect(classSelect).toHaveTextContent('Nursery'));
    fireEvent.change(classSelect, { target: { value: 'class-nursery' } });

    const sectionSelect = screen.getByLabelText('Section');
    await waitFor(() => expect(sectionSelect).toHaveTextContent('A'));
    fireEvent.change(sectionSelect, { target: { value: 'sec-nursery-a' } });
  };

  it('1. renders exams page with tabs and selectors', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Examinations & Reports')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Assessment Schedules' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Marks Entry Workspace' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Report Cards' })).toBeInTheDocument();
  });

  it('2. opens add exam modal and triggers creation', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Mid Term Exams')).toBeInTheDocument();
    });

    const addBtn = screen.getByRole('button', { name: 'Add Exam Cycle' });
    fireEvent.click(addBtn);

    expect(screen.getByText('NEW EXAM CYCLE')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Exam Name *'), { target: { value: 'Final Exam 2026' } });
    fireEvent.change(screen.getByLabelText('Start Date *'), { target: { value: '2026-11-01' } });
    fireEvent.change(screen.getByLabelText('End Date *'), { target: { value: '2026-11-15' } });

    const saveBtn = screen.getByRole('button', { name: 'Save Exam Cycle' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(examsApi.createExam).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Final Exam 2026',
          start_date: '2026-11-01',
          end_date: '2026-11-15',
        })
      );
    });
  });

  it('3. manages schedules rendering and deletion', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Mid Term Exams')).toBeInTheDocument();
    });

    const schedBtn = screen.getByRole('button', { name: 'Schedules' });
    fireEvent.click(schedBtn);

    await waitFor(() => {
      expect(screen.getByText('SCHEDULES: Mid Term Exams')).toBeInTheDocument();
      expect(screen.getByText('English')).toBeInTheDocument();
    });

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(examSchedulesApi.deleteExamSchedule).toHaveBeenCalledWith('sched-1');
    });
  });

  it('4. loads marks entry ledger, merges data, and handles input validation limits', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Marks tab
    fireEvent.click(screen.getByRole('button', { name: 'Marks Entry Workspace' }));

    // Select selectors
    const examSelect = screen.getByLabelText('Exam Cycle');
    await waitFor(() => expect(examSelect).toHaveTextContent('Mid Term Exams'));
    fireEvent.change(examSelect, { target: { value: 'exam-mid' } });

    await selectTestContext();

    const subjectSelect = screen.getByLabelText('Subject');
    await waitFor(() => expect(subjectSelect).toHaveTextContent('English'));
    fireEvent.change(subjectSelect, { target: { value: 'sub-english' } });

    // Roster is loaded
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    // John Doe has marks 85.00
    expect(screen.getByDisplayValue('85')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Good performance')).toBeInTheDocument();

    // Jane Smith has no result (defaults to blank)
    const janeRow = screen.getByText('Jane Smith').closest('tr');
    const janeInput = janeRow?.querySelector('input[type="number"]') as HTMLInputElement;
    expect(janeInput.value).toBe('');

    // Input validation: test typing invalid marks > 100
    fireEvent.change(janeInput, { target: { value: '150' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Marks' }));

    await waitFor(() => {
      expect(screen.getByText(/Marks must be between 0 and maximum marks/i)).toBeInTheDocument();
    });
  });

  it('5. triggers bulk marks update correctly', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Marks Entry Workspace' }));

    const examSelect = screen.getByLabelText('Exam Cycle');
    await waitFor(() => expect(examSelect).toHaveTextContent('Mid Term Exams'));
    fireEvent.change(examSelect, { target: { value: 'exam-mid' } });

    await selectTestContext();

    const subjectSelect = screen.getByLabelText('Subject');
    await waitFor(() => expect(subjectSelect).toHaveTextContent('English'));
    fireEvent.change(subjectSelect, { target: { value: 'sub-english' } });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const janeRow = screen.getByText('Jane Smith').closest('tr');
    const janeInput = janeRow?.querySelector('input[type="number"]') as HTMLInputElement;
    fireEvent.change(janeInput, { target: { value: '92' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: 'Save Marks' }));

    await waitFor(() => {
      // Create new mark for Jane Smith (stud-2)
      expect(studentExamResultsApi.createStudentExamResult).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: 'stud-2',
          marks_obtained: 92,
        })
      );
    });
  });

  it('6. report cards tab manages generation, remarks drawer, and publish triggers', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ExamsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Switch to Report Cards tab
    fireEvent.click(screen.getByRole('button', { name: 'Report Cards' }));

    await selectTestContext();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('85/100')).toBeInTheDocument();
    });

    // Bulk generate cards
    const genBtn = screen.getByRole('button', { name: 'Bulk Generate / Recalculate Cards' });
    fireEvent.click(genBtn);

    await waitFor(() => {
      expect(reportCardsApi.generateReportCards).toHaveBeenCalled();
    });

    // Remarks modal editing
    const remarksBtn = screen.getByRole('button', { name: 'Remarks' });
    fireEvent.click(remarksBtn);

    expect(screen.getByText('REPORT CARD REMARKS')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('Input student performance evaluation remarks...'), {
      target: { value: 'Outstanding effort' },
    });

    const saveRemarksBtn = screen.getByRole('button', { name: 'Save Remarks' });
    fireEvent.click(saveRemarksBtn);

    await waitFor(() => {
      expect(reportCardsApi.updateRemarks).toHaveBeenCalledWith(
        'rc-1',
        expect.objectContaining({ teacher_remarks: 'Outstanding effort' })
      );
    });

    // Finalize report card
    const finalizeBtn = screen.getByRole('button', { name: 'Finalize' });
    fireEvent.click(finalizeBtn);

    await waitFor(() => {
      expect(reportCardsApi.finalizeReportCard).toHaveBeenCalledWith('rc-1');
    });
  });
});
