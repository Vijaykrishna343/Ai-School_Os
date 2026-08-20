import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authService } from '@/services/api/authService';
import { apiClient } from '@/services/api/client';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Permission Hydration Contract & Multi-Role Logic', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      roles: [],
      permissions: [],
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      authError: null,
    });
    vi.clearAllMocks();
  });

  it('1. hydrates permissions correctly from backend roles and permissions endpoints', async () => {
    // 1. GET /users/u1/roles
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/users/u1/roles') {
        return Promise.resolve([{ user_id: 'u1', role_id: 'r1' }]);
      }
      if (url === '/permissions') {
        return Promise.resolve([
          { id: 'p1', name: 'student.view', module: 'student' },
          { id: 'p2', name: 'student.create', module: 'student' },
        ]);
      }
      if (url === '/roles/r1/permissions') {
        return Promise.resolve([
          { role_id: 'r1', permission_id: 'p1' },
          { role_id: 'r1', permission_id: 'p2' },
        ]);
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const userRoles = await authService.getUserRoles('u1');
    expect(userRoles).toHaveLength(1);
    expect(userRoles[0].permissions).toHaveLength(2);
    expect(userRoles[0].permissions?.map((p) => p.name)).toEqual(['student.view', 'student.create']);
  });

  it('2. produces the union of permissions across multiple assigned roles', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/users/u2/roles') {
        return Promise.resolve([
          { user_id: 'u2', role_id: 'roleA' },
          { user_id: 'u2', role_id: 'roleB' },
        ]);
      }
      if (url === '/permissions') {
        return Promise.resolve([
          { id: 'pA', name: 'student.view', module: 'student' },
          { id: 'pB', name: 'teacher.view', module: 'teacher' },
        ]);
      }
      if (url === '/roles/roleA/permissions') {
        return Promise.resolve([{ role_id: 'roleA', permission_id: 'pA' }]);
      }
      if (url === '/roles/roleB/permissions') {
        return Promise.resolve([{ role_id: 'roleB', permission_id: 'pB' }]);
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const roles = await authService.getUserRoles('u2');
    const permissionsSet = new Set<string>();
    roles.forEach((r) => {
      if (r.permissions) {
        r.permissions.forEach((p) => permissionsSet.add(p.name));
      }
    });

    const permissions = Array.from(permissionsSet);
    expect(permissions).toContain('student.view');
    expect(permissions).toContain('teacher.view');
    expect(permissions).toHaveLength(2);
  });

  it('3. deduplicates duplicate permissions across multiple roles', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/users/u3/roles') {
        return Promise.resolve([
          { user_id: 'u3', role_id: 'role1' },
          { user_id: 'u3', role_id: 'role2' },
        ]);
      }
      if (url === '/permissions') {
        return Promise.resolve([
          { id: 'p1', name: 'academic_year.view', module: 'academic' },
        ]);
      }
      if (url === '/roles/role1/permissions') {
        return Promise.resolve([{ role_id: 'role1', permission_id: 'p1' }]);
      }
      if (url === '/roles/role2/permissions') {
        return Promise.resolve([{ role_id: 'role2', permission_id: 'p1' }]);
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const roles = await authService.getUserRoles('u3');
    const permissionsSet = new Set<string>();
    roles.forEach((r) => {
      if (r.permissions) {
        r.permissions.forEach((p) => permissionsSet.add(p.name));
      }
    });

    expect(Array.from(permissionsSet)).toEqual(['academic_year.view']);
  });

  it('4. user with no roles gets zero permissions', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/users/u4/roles') {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const roles = await authService.getUserRoles('u4');
    expect(roles).toEqual([]);
  });

  it('5. permission hydration failure safely defaults to empty permissions (zero access granted)', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/users/u5/roles') {
        return Promise.reject(new Error('500 Internal Server Error'));
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const roles = await authService.getUserRoles('u5');
    expect(roles).toEqual([]);
  });
});
