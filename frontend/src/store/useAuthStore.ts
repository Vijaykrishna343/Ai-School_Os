import { create } from 'zustand';
import { User, UserLoginPayload, UserRole } from '@/types/auth';
import { authService } from '@/services/api/authService';
import { ApiError } from '@/types/api';

interface AuthState {
  user: User | null;
  roles: UserRole[];
  permissions: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;

  login: (credentials: UserLoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  initializeAuth: () => Promise<void>;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  roles: [],
  permissions: [],
  isAuthenticated: false,
  isLoading: true,
  authError: null,

  login: async (credentials: UserLoginPayload) => {
    set({ isLoading: true, authError: null });
    try {
      await authService.login(credentials);

      // Fetch user profile and roles (authenticated via HttpOnly cookie)
      const user = await authService.getCurrentUser();
      const roles = await authService.getUserRoles(user.id);

      // Collect permissions set from assigned roles
      const permissionsSet = new Set<string>();
      roles.forEach((r) => {
        if (r.permissions) {
          r.permissions.forEach((p) => permissionsSet.add(p.name));
        }
      });

      set({
        user,
        roles,
        permissions: Array.from(permissionsSet),
        isAuthenticated: true,
        isLoading: false,
        authError: null,
      });
    } catch (err: any) {
      const apiErr = err as ApiError;
      set({
        authError: apiErr.message || 'Login failed. Please check your credentials.',
        isLoading: false,
        isAuthenticated: false,
      });
      throw err;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout().catch(() => {
        // Ignore network or token revocation errors on logout
      });
    } finally {
      set({
        user: null,
        roles: [],
        permissions: [],
        isAuthenticated: false,
        isLoading: false,
        authError: null,
      });
    }
  },

  initializeAuth: async () => {
    set({ isLoading: true });
    try {
      const user = await authService.getCurrentUser();
      const roles = await authService.getUserRoles(user.id);

      const permissionsSet = new Set<string>();
      roles.forEach((r) => {
        if (r.permissions) {
          r.permissions.forEach((p) => permissionsSet.add(p.name));
        }
      });

      set({
        user,
        roles,
        permissions: Array.from(permissionsSet),
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({
        user: null,
        roles: [],
        permissions: [],
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  clearAuth: () => {
    set({
      user: null,
      roles: [],
      permissions: [],
      isAuthenticated: false,
      isLoading: false,
      authError: null,
    });
  },
}));

// Listen for global 401 unauthorized events dispatched by apiClient
if (typeof window !== 'undefined') {
  window.addEventListener('auth:unauthorized', () => {
    useAuthStore.getState().clearAuth();
  });
}
