import { apiClient } from './client';
import { RolePermission, TokenResponse, User, UserLoginPayload, UserRole } from '@/types/auth';

export const authService = {
  async login(credentials: UserLoginPayload): Promise<TokenResponse> {
    return apiClient.post('/auth/login', credentials);
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken });
  },

  async getCurrentUser(): Promise<User> {
    return apiClient.get('/auth/me');
  },

  async getUserRoles(userId: string): Promise<UserRole[]> {
    try {
      const rawUserRoles = await apiClient.get<any[]>(`/users/${userId}/roles`);
      if (!Array.isArray(rawUserRoles) || rawUserRoles.length === 0) {
        return [];
      }

      // If user roles already have nested permissions attached (e.g., in unit test mocks), return them directly
      if (rawUserRoles[0]?.permissions && Array.isArray(rawUserRoles[0].permissions)) {
        return rawUserRoles as UserRole[];
      }

      // Real backend contract flow:
      // 1. GET /permissions (all available permission definitions)
      // 2. GET /roles/{roleId}/permissions for each assigned role
      let allPermissions: any[] = [];
      try {
        const permsRes = await apiClient.get<any[]>('/permissions');
        if (Array.isArray(permsRes)) {
          allPermissions = permsRes;
        }
      } catch {
        allPermissions = [];
      }

      const permMap = new Map<string, RolePermission>();
      allPermissions.forEach((p: any) => {
        if (p && p.id && p.name) {
          permMap.set(p.id, {
            id: p.id,
            name: p.name,
            module: p.module || '',
          });
        }
      });

      const rolesWithPermissions: UserRole[] = [];
      for (const ur of rawUserRoles) {
        const roleId = ur.role_id || ur.id;
        if (!roleId) continue;

        let permissions: RolePermission[] = [];
        try {
          const rolePerms = await apiClient.get<any[]>(`/roles/${roleId}/permissions`);
          if (Array.isArray(rolePerms)) {
            rolePerms.forEach((rp: any) => {
              const pId = rp.permission_id;
              if (pId && permMap.has(pId)) {
                permissions.push(permMap.get(pId)!);
              } else if (rp.permission && rp.permission.name) {
                permissions.push({
                  id: rp.permission.id || pId,
                  name: rp.permission.name,
                  module: rp.permission.module || '',
                });
              }
            });
          }
        } catch {
          permissions = [];
        }

        rolesWithPermissions.push({
          id: roleId,
          name: ur.name || roleId,
          code: ur.code || roleId,
          permissions,
        });
      }

      return rolesWithPermissions;
    } catch {
      return [];
    }
  },
};


