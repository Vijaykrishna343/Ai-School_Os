import { apiClient } from './client';
import { School, SchoolUpdate } from '@/types/models';

export const schoolsApi = {
  getAll: async (params?: { page?: number; page_size?: number }): Promise<{ items: School[]; total: number }> => {

    const res = await apiClient.get('/schools', { params });
    return res.data || res;
  },

  getSchool: async (id: string): Promise<School> => {
    const res = await apiClient.get(`/schools/${id}`);
    return res.data || res;
  },

  createSchool: async (data: Partial<School>): Promise<School> => {
    const res = await apiClient.post('/schools', data);
    return res.data || res;
  },

  updateSchool: async (id: string, data: Partial<School>): Promise<School> => {
    const res = await apiClient.put(`/schools/${id}`, data);
    return res.data || res;
  },

  updateStatus: async (id: string, status: string, suspension_reason?: string): Promise<School> => {
    const res = await apiClient.put(`/schools/${id}/status`, { status, suspension_reason });
    return res.data || res;
  },

  updateSubscription: async (id: string, subscriptionData: Record<string, unknown>): Promise<School> => {
    const res = await apiClient.put(`/schools/${id}/subscription`, subscriptionData);
    return res.data || res;
  },
};

