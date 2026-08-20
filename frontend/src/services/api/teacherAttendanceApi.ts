import { apiClient } from './client';

export interface TeacherAttendanceItem {
  id: string;
  school_id: string;
  teacher_id: string;
  teacher_name?: string;
  employee_id?: string;
  department?: string;
  attendance_date: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE' | 'HALF_DAY' | 'EXCUSED' | 'LEAVE';
  check_in_time?: string | null;
  check_out_time?: string | null;
  remarks?: string | null;
}

export interface TeacherAttendanceSummary {
  attendance_date: string;
  total_teachers: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  leave_count: number;
  half_day_count: number;
}

export interface BulkTeacherAttendancePayload {
  attendance_date: string;
  items: Array<{
    teacher_id: string;
    status: string;
    check_in_time?: string;
    check_out_time?: string;
    remarks?: string;
  }>;
}

export const teacherAttendanceApi = {
  list: async (date: string, status?: string): Promise<TeacherAttendanceItem[]> => {
    const params: Record<string, string> = { attendance_date: date };
    if (status) params.status = status;
    const res = await apiClient.get('/teachers/attendance', { params });
    return res.data.data;
  },

  getSummary: async (date: string): Promise<TeacherAttendanceSummary> => {
    const res = await apiClient.get('/teachers/attendance/summary', { params: { attendance_date: date } });
    return res.data.data;
  },

  bulkMark: async (payload: BulkTeacherAttendancePayload): Promise<TeacherAttendanceItem[]> => {
    const res = await apiClient.post('/teachers/attendance/bulk', payload);
    return res.data.data;
  },

  update: async (id: string, payload: Partial<TeacherAttendanceItem>): Promise<TeacherAttendanceItem> => {
    const res = await apiClient.put(`/teachers/attendance/${id}`, payload);
    return res.data.data;
  },

  checkIn: async (): Promise<TeacherAttendanceItem> => {
    const res = await apiClient.post('/teachers/attendance/check-in');
    return res.data.data;
  },

  checkOut: async (): Promise<TeacherAttendanceItem> => {
    const res = await apiClient.post('/teachers/attendance/check-out');
    return res.data.data;
  },
};
