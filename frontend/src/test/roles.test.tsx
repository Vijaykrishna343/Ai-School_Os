import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RolesPage } from '@/pages/RolesPage';
import { useAuthStore } from '@/store/useAuthStore';
import { rolesApi } from '@/services/api/rolesApi';
import { permissionsApi } from '@/services/api/permissionsApi';
import { rolePermissionsApi } from '@/services/api/rolePermissionsApi';

vi.mock('@/services/api/rolesApi', () => ({
  rolesApi: {
    getRoles: vi.fn(),
    getRole: vi.fn(),
    createRole: vi.fn(),
    updateRole: vi.fn(),
    deleteRole: vi.fn(),
  },
}));

vi.mock('@/services/api/permissionsApi', () => ({
  permissionsApi: {
    getPermissions: vi.fn(),
    getPermission: vi.fn(),
  },
}));

vi.mock('@/services/api/rolePermissionsApi', () => ({
  rolePermissionsApi: {
    getRolePermissions: vi.fn(),
    assignPermission: vi.fn(),
    removePermission: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

const renderRolesPage = () => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RolesPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockRolesList = [
  {
    id: 'role-sys-1',
    school_id: null,
    name: 'School Admin',
    description: 'System Administrator',
    is_system: true,
    created_at: '2026-08-17T10:00:00Z',
    updated_at: '2026-08-17T10:00:00Z',
  },
  {
    id: 'role-cust-1',
    school_id: 'school-1',
    name: 'Exam Coordinator',
    description: 'Manages exams and report cards',
    is_system: false,
    created_at: '2026-08-17T10:00:00Z',
    updated_at: '2026-08-17T10:00:00Z',
  },
];

const mockPermissionsList = [
  {
    id: 'perm-1',
    name: 'student.create',
    description: 'Create student',
    module: 'student',
    action: 'create',
    created_at: '',
    updated_at: '',
  },
  {
    id: 'perm-2',
    name: 'exam.create',
    description: 'Create exam',
    module: 'exam',
    action: 'create',
    created_at: '',
    updated_at: '',
  },
];

describe('RolesPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'usr-admin', email: 'admin@school.com', school_id: 'school-1' } as any,
      permissions: ['role.view', 'role.create', 'role.update', 'role.delete', 'role_permission.assign', 'role_permission.remove'],
    });

    vi.mocked(rolesApi.getRoles).mockResolvedValue(mockRolesList as any);
    vi.mocked(permissionsApi.getPermissions).mockResolvedValue(mockPermissionsList as any);
    vi.mocked(rolePermissionsApi.getRolePermissions).mockResolvedValue([mockPermissionsList[0]] as any);
  });

  it('renders Roles page header and list of roles', async () => {
    renderRolesPage();
    await waitFor(() => {
      expect(screen.getByText('Role & Access Control Configuration')).toBeInTheDocument();
      expect(screen.getByText('School Admin')).toBeInTheDocument();
      expect(screen.getByText('Exam Coordinator')).toBeInTheDocument();
    });
  });

  it('shows SYSTEM badge for system roles and CUSTOM badge for custom roles', async () => {
    renderRolesPage();
    await waitFor(() => {
      expect(screen.getByText('SYSTEM')).toBeInTheDocument();
      expect(screen.getByText('CUSTOM')).toBeInTheDocument();
    });
  });

  it('opens Create Custom Role modal and submits role payload', async () => {
    vi.mocked(rolesApi.createRole).mockResolvedValue({
      id: 'role-cust-2',
      school_id: 'school-1',
      name: 'Lab Assistant',
      description: 'Manages laboratory schedule',
      is_system: false,
      created_at: '',
      updated_at: '',
    } as any);

    renderRolesPage();

    await waitFor(() => {
      expect(screen.getByText('+ Create Custom Role')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ Create Custom Role'));

    await waitFor(() => {
      expect(screen.getByText('CREATE CUSTOM ROLE')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Role Name *'), { target: { value: 'Lab Assistant' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create Role' }));

    await waitFor(() => {
      expect(rolesApi.createRole).toHaveBeenCalledWith({
        school_id: 'school-1',
        name: 'Lab Assistant',
        description: null,
      });
    });
  });

  it('opens Permission Matrix drawer for custom role and displays grouped permissions', async () => {
    renderRolesPage();

    await waitFor(() => {
      expect(screen.getByText('Exam Coordinator')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByText('Permissions')[0]);

    await waitFor(() => {
      expect(screen.getByText(/MODULE: student/i)).toBeInTheDocument();
      expect(screen.getByText(/student.create/i)).toBeInTheDocument();
    });
  });

  it('shows read-only message when viewing system role permission matrix', async () => {
    renderRolesPage();

    await waitFor(() => {
      expect(screen.getByText('View Matrix')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('View Matrix'));

    await waitFor(() => {
      expect(screen.getByText(/System roles are platform built-ins/i)).toBeInTheDocument();
    });
  });
});
