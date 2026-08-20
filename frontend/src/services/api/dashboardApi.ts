import { apiClient } from './client';
import { DashboardSummary } from '@/types/models';

export const dashboardApi = {
  getAdminSummary: async (): Promise<DashboardSummary> => {
    return await apiClient.get('/dashboard/admin/summary');
  },
  getTeacherSummary: async (): Promise<any> => {
    return await apiClient.get('/dashboard/teacher/summary');
  },
};
