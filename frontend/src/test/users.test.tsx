import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UsersPage } from '@/pages/UsersPage';
import { useAuthStore } from '@/store/useAuthStore';
import { usersApi } from '@/services/api/usersApi';
import { rolesApi } from '@/services/api/rolesApi';
import { userRolesApi } from '@/services/api/userRolesApi';

vi.mock('@/services/api/usersApi', () => ({
  usersApi: {
    getUsers: vi.fn(),
    getUser: vi.fn(),
    createUser: vi.fn(),
    updateUser: vi.fn(),
    deleteUser: vi.fn(),
  },
}));

vi.mock('@/services/api/rolesApi', () => ({
  rolesApi: {
    getRoles: vi.fn(),
    getRole: vi.fn(),
    createRole: vi.fn(),
    updateRole: vi.fn(),
    deleteRole: vi.fn(),
  },
}));

vi.mock('@/services/api/userRolesApi', () => ({
  userRolesApi: {
    getUserRoles: vi.fn(),
    assignRole: vi.fn(),
    removeRole: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

const renderUsersPage = () => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockUsersResponse = {
  items: [
    {
      id: 'usr-1',
      school_id: 'school-1',
      email: 'john@school.com',
      username: 'john_doe',
      first_name: 'John',
      last_name: 'Doe',
      phone: '+1234567890',
      is_active: true,
      is_verified: true,
      last_login: null,
      created_at: '2026-08-17T10:00:00Z',
      updated_at: '2026-08-17T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockRolesResponse = [
  {
    id: 'role-1',
    school_id: 'school-1',
    name: 'School Admin',
    description: 'Administrator role',
    is_system: true,
    created_at: '2026-08-17T10:00:00Z',
    updated_at: '2026-08-17T10:00:00Z',
  },
];

describe('UsersPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'usr-admin', email: 'admin@school.com', school_id: 'school-1' } as any,
      permissions: ['user.view', 'user.create', 'user.update', 'user.delete', 'user_role.assign', 'user_role.remove'],
    });

    vi.mocked(usersApi.getUsers).mockResolvedValue(mockUsersResponse as any);
    vi.mocked(rolesApi.getRoles).mockResolvedValue(mockRolesResponse as any);
    vi.mocked(userRolesApi.getUserRoles).mockResolvedValue(mockRolesResponse as any);
  });

  it('renders User Management header and user table', async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText('User Management & Staff Accounts')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@school.com')).toBeInTheDocument();
    });
  });

  it('opens Create User modal and submits user data', async () => {
    vi.mocked(usersApi.createUser).mockResolvedValue({
      id: 'usr-2',
      school_id: 'school-1',
      email: 'jane@school.com',
      username: 'jane_smith',
      first_name: 'Jane',
      last_name: 'Smith',
      phone: null,
      is_active: true,
      is_verified: false,
      last_login: null,
      created_at: '',
      updated_at: '',
    } as any);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByText('+ Create User')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ Create User'));

    await waitFor(() => {
      expect(screen.getByText('CREATE USER ACCOUNT')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'jane@school.com' } });
    fireEvent.change(screen.getByLabelText('Password *'), { target: { value: 'Secret123!' } });
    fireEvent.change(screen.getByLabelText('First Name *'), { target: { value: 'Jane' } });

    fireEvent.click(screen.getByRole('button', { name: 'Create User' }));

    await waitFor(() => {
      expect(usersApi.createUser).toHaveBeenCalledWith({
        school_id: 'school-1',
        email: 'jane@school.com',
        username: null,
        password: 'Secret123!',
        first_name: 'Jane',
        last_name: null,
        phone: null,
      });
    });
  });

  it('opens Edit User modal and submits updates', async () => {
    vi.mocked(usersApi.updateUser).mockResolvedValue({
      ...mockUsersResponse.items[0],
      first_name: 'Johnny',
    } as any);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Edit'));

    await waitFor(() => {
      expect(screen.getByText('EDIT USER ACCOUNT')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('First Name *'), { target: { value: 'Johnny' } });

    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(usersApi.updateUser).toHaveBeenCalledWith('usr-1', expect.objectContaining({
        first_name: 'Johnny',
      }));
    });
  });

  it('opens Roles modal and assigns a role', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByText('Roles')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Roles'));

    await waitFor(() => {
      expect(screen.getByText('School Admin')).toBeInTheDocument();
    });
  });

  it('hides create button when user lacks user.create permission', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'usr-viewer', email: 'viewer@school.com', school_id: 'school-1' } as any,
      permissions: ['user.view'],
    });

    renderUsersPage();

    await waitFor(() => {
      expect(screen.queryByText('+ Create User')).not.toBeInTheDocument();
    });
  });
});
