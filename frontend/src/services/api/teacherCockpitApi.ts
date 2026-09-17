import { apiClient } from './client';

export interface TeacherProfileHeader {
  teacher_id?: string | null;
  user_id: string;
  full_name: string;
  email: string;
  employee_id?: string | null;
  qualification?: string | null;
  specialization?: string | null;
  school_id: string;
  school_name: string;
  is_assigned_teacher: boolean;
  avatar_url?: string | null;
}

export interface CockpitMetricsSummary {
  total_classes_today: number;
  completed_classes_today: number;
  remaining_classes_today: number;
  unmarked_attendance_count: number;
  pending_homework_reviews_count: number;
  active_homework_count: number;
  upcoming_exams_count: number;
  urgent_alerts_count: number;
}

export interface CockpitScheduleEntry {
  timetable_entry_id?: string | null;
  period_slot_id: string;
  slot_number: number;
  period_name: string;
  start_time: string;
  end_time: string;
  period_type: string;
  class_id?: string | null;
  class_name: string;
  section_id?: string | null;
  section_name?: string | null;
  subject_id?: string | null;
  subject_name: string;
  classroom_id?: string | null;
  room_number?: string | null;
  building_name?: string | null;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'UPCOMING';
  is_substitution: boolean;
  original_teacher_name?: string | null;
  substitution_remarks?: string | null;
  attendance_marked: boolean;
  attendance_stats?: {
    present: number;
    absent: number;
    late: number;
  } | null;
}

export interface CurrentAndNextClass {
  current_class?: CockpitScheduleEntry | null;
  next_class?: CockpitScheduleEntry | null;
}

export interface CockpitAttendanceSection {
  school_class_id: string;
  class_name: string;
  section_id: string;
  section_name: string;
  total_students: number;
  marked_count: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  half_day_count: number;
  attendance_pct: number;
  is_marked: boolean;
  is_class_teacher: boolean;
}

export interface CockpitHomeworkItem {
  homework_id: string;
  title: string;
  description?: string | null;
  subject_name: string;
  class_name: string;
  section_name?: string | null;
  assigned_date: string;
  due_date: string;
  status: string;
  total_submissions: number;
  graded_submissions: number;
  pending_review_count: number;
}

export interface CockpitExamItem {
  exam_id: string;
  exam_name: string;
  exam_schedule_id: string;
  subject_name: string;
  class_name: string;
  section_name?: string | null;
  exam_date: string;
  start_time: string;
  end_time: string;
  max_marks: number;
  passing_marks: number;
  results_entered_count: number;
  total_students_count: number;
  grading_status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
}

export interface CockpitAlertItem {
  id: string;
  level: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  message: string;
  action_label?: string | null;
  action_url?: string | null;
}

export interface CockpitQuickActions {
  can_mark_attendance: boolean;
  can_create_homework: boolean;
  can_enter_marks: boolean;
  can_request_substitution: boolean;
  can_view_analytics: boolean;
}

export interface TeacherCockpitResponse {
  today_date: string;
  day_of_week: string;
  current_academic_year?: string | null;
  teacher: TeacherProfileHeader;
  summary: CockpitMetricsSummary;
  current_and_next: CurrentAndNextClass;
  today_schedule: CockpitScheduleEntry[];
  attendance_roster: CockpitAttendanceSection[];
  homework_overview: CockpitHomeworkItem[];
  upcoming_exams: CockpitExamItem[];
  alerts: CockpitAlertItem[];
  quick_actions: CockpitQuickActions;
}

export interface TeacherCockpitSummaryResponse {
  today_date: string;
  day_of_week: string;
  teacher: TeacherProfileHeader;
  summary: CockpitMetricsSummary;
  current_and_next: CurrentAndNextClass;
  alerts: CockpitAlertItem[];
}

export const teacherCockpitApi = {
  /**
   * Get consolidated operational data for teacher classroom cockpit.
   */
  async getCockpitData(targetDate?: string): Promise<TeacherCockpitResponse> {
    const params = targetDate ? { target_date: targetDate } : undefined;
    const response = await apiClient.get<{ message: string; data: TeacherCockpitResponse }>('/teacher-cockpit', { params });
    return response.data.data;
  },

  /**
   * Get lightweight summary KPIs and active alerts for quick refresh/polling.
   */
  async getCockpitSummary(targetDate?: string): Promise<TeacherCockpitSummaryResponse> {
    const params = targetDate ? { target_date: targetDate } : undefined;
    const response = await apiClient.get<{ message: string; data: TeacherCockpitSummaryResponse }>('/teacher-cockpit/summary', { params });
    return response.data.data;
  },
};
