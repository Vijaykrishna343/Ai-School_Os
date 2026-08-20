import { apiClient } from './client';
import {
  PaginatedResponse,
  User,
  UserCreate,
  UserUpdate,
} from '@/types/models';

export interface UserFilters {
  school_id?: string;
  email?: string;
  username?: string;
  first_name?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export const usersApi = {
  getUsers: async (params?: UserFilters): Promise<PaginatedResponse<User>> => {
    return await apiClient.get('/users', { params });
  },

  getUser: async (id: string): Promise<User> => {
    return await apiClient.get(`/users/${id}`);
  },

  createUser: async (data: UserCreate): Promise<User> => {
    return await apiClient.post('/users', data);
  },

  updateUser: async (id: string, data: UserUpdate): Promise<User> => {
    return await apiClient.put(`/users/${id}`, data);
  },

  deleteUser: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`);
  },

  updateUserStatus: async (id: string, status: string, suspension_reason?: string): Promise<User> => {
    return await apiClient.put(`/users/${id}/status`, { status, suspension_reason });
  },
};

