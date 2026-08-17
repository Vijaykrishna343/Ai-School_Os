import { apiClient } from './client';
import {
  PaginatedResponse,
  Attendance,
  AttendanceCreate,
  AttendanceBulkCreate,
  AttendanceUpdate,
  AttendanceStatus,
} from '@/types/models';

export interface AttendanceFilters {
  section_id?: string;
  school_class_id?: string;
  student_id?: string;
  attendance_date?: string; // YYYY-MM-DD
  status?: AttendanceStatus;
  page?: number;
  page_size?: number;
}

export const attendanceApi = {
  getAttendance: async (params?: AttendanceFilters): Promise<PaginatedResponse<Attendance>> => {
    return await apiClient.get('/attendance', { params });
  },

  getAttendanceById: async (id: string): Promise<Attendance> => {
    return await apiClient.get(`/attendance/${id}`);
  },

  createAttendance: async (data: AttendanceCreate): Promise<Attendance> => {
    return await apiClient.post('/attendance', data);
  },

  createBulkAttendance: async (
    data: AttendanceBulkCreate
  ): Promise<{ items: Attendance[]; count: number }> => {
    return await apiClient.post('/attendance/bulk', data);
  },

  updateAttendance: async (id: string, data: AttendanceUpdate): Promise<Attendance> => {
    return await apiClient.put(`/attendance/${id}`, data);
  },

  deleteAttendance: async (id: string): Promise<void> => {
    await apiClient.delete(`/attendance/${id}`);
  },
};
