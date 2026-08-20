import { apiClient } from './client';
import { Permission } from '@/types/models';

export const rolePermissionsApi = {
  getRolePermissions: async (roleId: string): Promise<Permission[]> => {
    return await apiClient.get(`/roles/${roleId}/permissions`);
  },

  assignPermission: async (roleId: string, permissionId: string): Promise<any> => {
    return await apiClient.post(`/roles/${roleId}/permissions/${permissionId}`);
  },

  assignRolePermission: async (roleId: string, permissionId: string): Promise<any> => {
    return await apiClient.post(`/roles/${roleId}/permissions/${permissionId}`);
  },

  removePermission: async (roleId: string, permissionId: string): Promise<void> => {
    await apiClient.delete(`/roles/${roleId}/permissions/${permissionId}`);
  },

  removeRolePermission: async (roleId: string, permissionId: string): Promise<void> => {
    await apiClient.delete(`/roles/${roleId}/permissions/${permissionId}`);
  },
};

