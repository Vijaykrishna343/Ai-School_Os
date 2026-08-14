import { apiClient } from './client';
import {
  PaginatedResponse,
  Teacher,
  TeacherCreate,
  TeacherUpdate,
} from '@/types/models';

export interface TeacherFilterParams {
  search?: string;
  status?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export const teachersApi = {
  getTeachers: async (params?: TeacherFilterParams): Promise<PaginatedResponse<Teacher>> => {
    return await apiClient.get('/teachers', { params });
  },

  getTeacher: async (id: string): Promise<Teacher> => {
    return await apiClient.get(`/teachers/${id}`);
  },

  createTeacher: async (data: TeacherCreate): Promise<Teacher> => {
    return await apiClient.post('/teachers', data);
  },

  updateTeacher: async (id: string, data: TeacherUpdate): Promise<Teacher> => {
    return await apiClient.put(`/teachers/${id}`, data);
  },

  deleteTeacher: async (id: string): Promise<void> => {
    await apiClient.delete(`/teachers/${id}`);
  },
};
