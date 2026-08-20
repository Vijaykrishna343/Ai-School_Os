import { apiClient } from './client';
import {
  Role,
  RoleCreate,
  RoleUpdate,
} from '@/types/models';

export interface RoleFilters {
  school_id?: string;
  name?: string;
  is_system?: boolean;
  page?: number;
  page_size?: number;
}

export const rolesApi = {
  getRoles: async (params?: RoleFilters): Promise<Role[]> => {
    return await apiClient.get('/roles', { params });
  },

  getRole: async (id: string): Promise<Role> => {
    return await apiClient.get(`/roles/${id}`);
  },

  createRole: async (data: RoleCreate): Promise<Role> => {
    return await apiClient.post('/roles', data);
  },

  updateRole: async (id: string, data: RoleUpdate): Promise<Role> => {
    return await apiClient.put(`/roles/${id}`, data);
  },

  deleteRole: async (id: string): Promise<void> => {
    await apiClient.delete(`/roles/${id}`);
  },
};
