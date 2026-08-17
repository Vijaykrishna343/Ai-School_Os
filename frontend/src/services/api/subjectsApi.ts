import { apiClient } from './client';
import {
  PaginatedResponse,
  Subject,
  SubjectCreate,
  SubjectUpdate,
} from '@/types/models';

export interface SubjectFilterParams {
  subject_code?: string;
  subject_name?: string;
  status?: string;
  is_optional?: boolean;
  page?: number;
  page_size?: number;
}

export const subjectsApi = {
  getSubjects: async (params?: SubjectFilterParams): Promise<PaginatedResponse<Subject>> => {
    return await apiClient.get('/subjects', { params });
  },

  getSubject: async (id: string): Promise<Subject> => {
    return await apiClient.get(`/subjects/${id}`);
  },

  createSubject: async (data: SubjectCreate): Promise<Subject> => {
    return await apiClient.post('/subjects', data);
  },

  updateSubject: async (id: string, data: SubjectUpdate): Promise<Subject> => {
    return await apiClient.put(`/subjects/${id}`, data);
  },

  deleteSubject: async (id: string): Promise<void> => {
    await apiClient.delete(`/subjects/${id}`);
  },
};
