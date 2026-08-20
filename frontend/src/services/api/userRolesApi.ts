import { apiClient } from './client';
import { Role } from '@/types/models';

export const userRolesApi = {
  getUserRoles: async (userId: string): Promise<Role[]> => {
    return await apiClient.get(`/users/${userId}/roles`);
  },

  assignRole: async (userId: string, roleId: string): Promise<any> => {
    return await apiClient.post(`/users/${userId}/roles/${roleId}`);
  },

  assignUserRole: async (userId: string, roleId: string): Promise<any> => {
    return await apiClient.post(`/users/${userId}/roles/${roleId}`);
  },

  removeRole: async (userId: string, roleId: string): Promise<void> => {
    await apiClient.delete(`/users/${userId}/roles/${roleId}`);
  },

  removeUserRole: async (userId: string, roleId: string): Promise<void> => {
    await apiClient.delete(`/users/${userId}/roles/${roleId}`);
  },
};

