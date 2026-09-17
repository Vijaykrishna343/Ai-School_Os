import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TeacherCockpitPage } from '@/pages/TeacherCockpitPage';
import { teacherCockpitApi, TeacherCockpitResponse } from '@/services/api/teacherCockpitApi';

vi.mock('@/services/api/teacherCockpitApi', () => ({
  teacherCockpitApi: {
    getCockpitData: vi.fn(),
    getCockpitSummary: vi.fn(),
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

const mockCockpitData: TeacherCockpitResponse = {
  today_date: '2026-09-16',
  day_of_week: 'Wednesday',
  current_academic_year: '2026-2027',
  teacher: {
    teacher_id: 'teacher-123',
    user_id: 'user-123',
    full_name: 'Dr. Alan Turing',
    email: 'alan.turing@school.edu',
    employee_id: 'T-1001',
    qualification: 'Ph.D. Mathematics',
    specialization: 'Applied Calculus',
    school_id: 'school-123',
    school_name: 'Newton Science Academy',
    is_assigned_teacher: true,
  },
  summary: {
    total_classes_today: 4,
    completed_classes_today: 1,
    remaining_classes_today: 3,
    unmarked_attendance_count: 1,
    pending_homework_reviews_count: 5,
    active_homework_count: 2,
    upcoming_exams_count: 1,
    urgent_alerts_count: 1,
  },
  current_and_next: {
    current_class: {
      timetable_entry_id: 'entry-1',
      period_slot_id: 'slot-2',
      slot_number: 2,
      period_name: 'Period 2',
      start_time: '09:30',
      end_time: '10:30',
      period_type: 'REGULAR',
      class_id: 'class-10',
      class_name: 'Grade 10',
      section_id: 'sec-a',
      section_name: 'A',
      subject_id: 'subj-math',
      subject_name: 'Advanced Calculus',
      room_number: '204',
      building_name: 'Science Block',
      status: 'IN_PROGRESS',
      is_substitution: true,
      original_teacher_name: 'Ada Lovelace',
      substitution_remarks: 'Covering medical leave',
      attendance_marked: false,
    },
    next_class: {
      timetable_entry_id: 'entry-2',
      period_slot_id: 'slot-3',
      slot_number: 3,
      period_name: 'Period 3',
      start_time: '10:45',
      end_time: '11:45',
      period_type: 'REGULAR',
      class_id: 'class-11',
      class_name: 'Grade 11',
      section_id: 'sec-b',
      section_name: 'B',
      subject_id: 'subj-cs',
      subject_name: 'Discrete Mathematics',
      room_number: '102',
      status: 'UPCOMING',
      is_substitution: false,
      attendance_marked: false,
    },
  },
  today_schedule: [
    {
      timetable_entry_id: 'entry-0',
      period_slot_id: 'slot-1',
      slot_number: 1,
      period_name: 'Period 1',
      start_time: '08:30',
      end_time: '09:25',
      period_type: 'REGULAR',
      class_id: 'class-9',
      class_name: 'Grade 9',
      section_id: 'sec-a',
      section_name: 'A',
      subject_name: 'Algebra Foundations',
      room_number: '101',
      status: 'COMPLETED',
      is_substitution: false,
      attendance_marked: true,
      attendance_stats: { present: 28, absent: 2, late: 0 },
    },
    {
      timetable_entry_id: 'entry-1',
      period_slot_id: 'slot-2',
      slot_number: 2,
      period_name: 'Period 2',
      start_time: '09:30',
      end_time: '10:30',
      period_type: 'REGULAR',
      class_id: 'class-10',
      class_name: 'Grade 10',
      section_id: 'sec-a',
      section_name: 'A',
      subject_name: 'Advanced Calculus',
      room_number: '204',
      status: 'IN_PROGRESS',
      is_substitution: true,
      original_teacher_name: 'Ada Lovelace',
      attendance_marked: false,
    },
  ],
  attendance_roster: [
    {
      school_class_id: 'class-10',
      class_name: 'Grade 10',
      section_id: 'sec-a',
      section_name: 'A',
      total_students: 30,
      marked_count: 0,
      present_count: 0,
      absent_count: 0,
      late_count: 0,
      half_day_count: 0,
      attendance_pct: 0,
      is_marked: false,
      is_class_teacher: true,
    },
  ],
  homework_overview: [
    {
      homework_id: 'hw-1',
      title: 'Vector Calculus Problem Set 3',
      description: 'Solve exercises 1-15',
      subject_name: 'Advanced Calculus',
      class_name: 'Grade 10',
      section_name: 'A',
      assigned_date: '2026-09-15',
      due_date: '2026-09-18',
      status: 'PUBLISHED',
      total_submissions: 25,
      graded_submissions: 20,
      pending_review_count: 5,
    },
  ],
  upcoming_exams: [
    {
      exam_id: 'exam-1',
      exam_name: 'Mid-Term Exam',
      exam_schedule_id: 'sched-1',
      subject_name: 'Advanced Calculus',
      class_name: 'Grade 10',
      section_name: 'A',
      exam_date: '2026-09-22',
      start_time: '09:00',
      end_time: '11:00',
      max_marks: 100,
      passing_marks: 40,
      results_entered_count: 0,
      total_students_count: 30,
      grading_status: 'NOT_STARTED',
    },
  ],
  alerts: [
    {
      id: 'alert-1',
      level: 'WARNING',
      title: 'Unmarked Attendance',
      message: 'Attendance for Grade 10-A has not been submitted yet.',
      action_label: 'Mark Attendance',
      action_url: '/app/attendance?class_id=class-10&section_id=sec-a',
    },
  ],
  quick_actions: {
    can_mark_attendance: true,
    can_create_homework: true,
    can_enter_marks: true,
    can_request_substitution: true,
    can_view_analytics: true,
  },
};

describe('TeacherCockpitPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    const queryClient = createTestQueryClient();
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeacherCockpitPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders loading indicator while fetching cockpit data', () => {
    vi.mocked(teacherCockpitApi.getCockpitData).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText(/Loading Teacher Classroom Command Cockpit/i)).toBeInTheDocument();
  });

  it('renders error state when API request fails', async () => {
    vi.mocked(teacherCockpitApi.getCockpitData).mockRejectedValue(new Error('Network error'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Failed to load classroom cockpit/i)).toBeInTheDocument();
    });
  });

  it('renders teacher profile header, KPIs, and operational spotlight', async () => {
    vi.mocked(teacherCockpitApi.getCockpitData).mockResolvedValue(mockCockpitData);
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Dr. Alan Turing')).toBeInTheDocument();
      expect(screen.getByText(/Active Faculty/i)).toBeInTheDocument();
      expect(screen.getByText(/Newton Science Academy/i)).toBeInTheDocument();
      expect(screen.getByText(/ID: T-1001/i)).toBeInTheDocument();
    });

    // KPI Summary
    expect(screen.getByText('Classes Today')).toBeInTheDocument();
    expect(screen.getByText('Unmarked Att.')).toBeInTheDocument();
    expect(screen.getByText('HW Pending')).toBeInTheDocument();

    // Spotlight Current & Next Class
    expect(screen.getByText(/Class In Session/i)).toBeInTheDocument();
    expect(screen.getByText(/Next Upcoming Class/i)).toBeInTheDocument();
    expect(screen.getByText('Discrete Mathematics')).toBeInTheDocument();

    // Schedule Timeline
    expect(screen.getByText("Today's Class Schedule")).toBeInTheDocument();
    expect(screen.getByText('Algebra Foundations')).toBeInTheDocument();
    expect(screen.getByText(/Cover: Ada Lovelace/i)).toBeInTheDocument();

    // Homework & Exams
    expect(screen.getByText('Vector Calculus Problem Set 3')).toBeInTheDocument();
    expect(screen.getByText(/5 Pending Review/i)).toBeInTheDocument();
    expect(screen.getByText(/Mid-Term Exam/i)).toBeInTheDocument();

    // Operational Alert
    expect(screen.getByText('Unmarked Attendance')).toBeInTheDocument();
  });

  it('renders observation mode notice when teacher is unassigned', async () => {
    const unassignedData: TeacherCockpitResponse = {
      ...mockCockpitData,
      teacher: {
        ...mockCockpitData.teacher,
        is_assigned_teacher: false,
      },
      today_schedule: [],
      attendance_roster: [],
      homework_overview: [],
      upcoming_exams: [],
      current_and_next: { current_class: null, next_class: null },
    };

    vi.mocked(teacherCockpitApi.getCockpitData).mockResolvedValue(unassignedData);
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Staff \/ Admin View/i)).toBeInTheDocument();
      expect(screen.getByText(/Administrator Observation Mode/i)).toBeInTheDocument();
    });
  });
});
