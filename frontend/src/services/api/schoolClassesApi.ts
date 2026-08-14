import { apiClient } from './client';
import {
  PaginatedResponse,
  SchoolClass,
  SchoolClassCreate,
  SchoolClassUpdate,
} from '@/types/models';

export const schoolClassesApi = {
  getSchoolClasses: async (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<SchoolClass>> => {
    return await apiClient.get('/school-classes', { params });
  },

  getSchoolClass: async (id: string): Promise<SchoolClass> => {
    return await apiClient.get(`/school-classes/${id}`);
  },

  createSchoolClass: async (data: SchoolClassCreate): Promise<SchoolClass> => {
    return await apiClient.post('/school-classes', data);
  },

  updateSchoolClass: async (id: string, data: SchoolClassUpdate): Promise<SchoolClass> => {
    return await apiClient.put(`/school-classes/${id}`, data);
  },

  deleteSchoolClass: async (id: string): Promise<void> => {
    await apiClient.delete(`/school-classes/${id}`);
  },
};
