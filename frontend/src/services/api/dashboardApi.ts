import { apiClient } from './client';
import { DashboardSummary } from '@/types/models';

export const dashboardApi = {
  getAdminSummary: async (): Promise<DashboardSummary> => {
    return await apiClient.get('/dashboard/admin/summary');
  },
};
