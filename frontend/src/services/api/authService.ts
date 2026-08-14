import { apiClient } from './client';
import { TokenResponse, User, UserLoginPayload, UserRole } from '@/types/auth';

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
      return await apiClient.get(`/users/${userId}/roles`);
    } catch {
      return [];
    }
  },
};
