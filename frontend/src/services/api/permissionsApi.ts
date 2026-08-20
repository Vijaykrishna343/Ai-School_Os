import { apiClient } from './client';
import {
  Permission,
  PermissionFilter,
} from '@/types/models';

export const permissionsApi = {
  getPermissions: async (params?: PermissionFilter): Promise<Permission[]> => {
    return await apiClient.get('/permissions', { params });
  },

  getPermission: async (id: string): Promise<Permission> => {
    return await apiClient.get(`/permissions/${id}`);
  },
};
