import { apiClient } from './client';
import {
  PaginatedResponse,
  Parent,
  ParentCreate,
  ParentUpdate,
} from '@/types/models';

export const parentsApi = {
  getParents: async (params?: { page?: number; page_size?: number; search?: string }): Promise<PaginatedResponse<Parent>> => {
    return await apiClient.get('/parents', { params });
  },

  getParent: async (id: string): Promise<Parent> => {
    return await apiClient.get(`/parents/${id}`);
  },

  createParent: async (data: ParentCreate): Promise<Parent> => {
    return await apiClient.post('/parents', data);
  },

  updateParent: async (id: string, data: ParentUpdate): Promise<Parent> => {
    return await apiClient.put(`/parents/${id}`, data);
  },

  deleteParent: async (id: string): Promise<void> => {
    await apiClient.delete(`/parents/${id}`);
  },
};
