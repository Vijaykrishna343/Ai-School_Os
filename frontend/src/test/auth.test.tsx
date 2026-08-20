import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { useAuthStore } from '@/store/useAuthStore';
import { authService } from '@/services/api/authService';

vi.mock('@/services/api/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    getUserRoles: vi.fn(),
  },
}));

describe('Frontend Authentication & Login Experience', () => {
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

  it('renders login page with school code, email and password inputs', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'AI School OS' })).toBeInTheDocument();
    expect(screen.getByLabelText('School Code')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /SIGN IN TO PORTAL/i })).toBeInTheDocument();
  });

  it('validates empty inputs and displays client error messages', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /SIGN IN TO PORTAL/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/School code is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Email address is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });
  });

  it('handles successful backend authentication flow with school_code and updates auth store', async () => {
    const mockTokenRes = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'Bearer',
      expires_in: 1800,
    };

    const mockUser = {
      id: 'user-123',
      school_id: 'school-456',
      email: 'admin@school.com',
      first_name: 'Admin',
      last_name: 'User',
      is_active: true,
    };

    vi.mocked(authService.login).mockResolvedValue(mockTokenRes);
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser as any);
    vi.mocked(authService.getUserRoles).mockResolvedValue([
      {
        id: 'role-1',
        name: 'Administrator',
        code: 'admin',
        permissions: [{ id: 'p-1', name: 'student.view', module: 'student' }],
      },
    ]);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('School Code'), {
      target: { value: 'VGS001' },
    });
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'admin@school.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'SecurePass123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /SIGN IN TO PORTAL/i }));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        school_code: 'VGS001',
        email: 'admin@school.com',
        password: 'SecurePass123!',
      });
      const storeState = useAuthStore.getState();
      expect(storeState.isAuthenticated).toBe(true);
      expect(storeState.user?.email).toBe('admin@school.com');
      expect(storeState.permissions).toContain('student.view');
    });
  });

  it('handles backend login failure and displays error message', async () => {
    vi.mocked(authService.login).mockRejectedValue({
      message: 'Invalid credentials provided.',
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('School Code'), {
      target: { value: 'VGS001' },
    });
    fireEvent.change(screen.getByLabelText('Email Address'), {
      target: { value: 'admin@school.com' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'WrongPassword' },
    });

    fireEvent.click(screen.getByRole('button', { name: /SIGN IN TO PORTAL/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials provided/i)).toBeInTheDocument();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });
});
