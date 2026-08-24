import { apiClient } from './client';
import { DashboardSummary } from '@/types/models';

export const dashboardApi = {
  getAdminSummary: async (): Promise<DashboardSummary> => {
    return await apiClient.get('/dashboard/admin/summary');
  },
  getTeacherSummary: async (): Promise<any> => {
    return await apiClient.get('/dashboard/teacher/summary');
  },
  getParentSummary: async (studentId?: string): Promise<any> => {
    const url = studentId ? `/dashboard/parent/summary?student_id=${studentId}` : '/dashboard/parent/summary';
    return await apiClient.get(url);
  },
  getStudentSummary: async (): Promise<any> => {
    return await apiClient.get('/dashboard/student/summary');
  },
};
