import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '@/pages/DashboardPage';
import { dashboardApi } from '@/services/api/dashboardApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/dashboardApi', () => ({
  dashboardApi: {
    getAdminSummary: vi.fn(),
    getTeacherSummary: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('DashboardPage Component', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: {
        id: 'user-123',
        school_id: 'school-456',
        email: 'admin@school.com',
        first_name: 'Principal',
        last_name: 'User',
        is_active: true,
      },
      permissions: ['school.view', 'student.view'],
      isAuthenticated: true,
      isLoading: false,
    });
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(dashboardApi.getAdminSummary).mockReturnValue(new Promise(() => {}));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.queryByText(/Administrative Command Center/i)).not.toBeInTheDocument();
  });

  it('renders admin dashboard with real metrics when api success', async () => {
    const mockSummary = {
      active_students: 150,
      active_teachers: 15,
      active_parents: 120,
      active_classes: 10,
      active_sections: 20,
    };
    vi.mocked(dashboardApi.getAdminSummary).mockResolvedValue(mockSummary as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Administrative Command Center/i)).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument(); // students
      expect(screen.getByText('15')).toBeInTheDocument(); // faculty
      expect(screen.getByText('120')).toBeInTheDocument(); // parents
    });
  });

  it('renders teacher workstation dashboard when user lacks school.view', async () => {
    useAuthStore.setState({
      user: {
        id: 'teacher-123',
        school_id: 'school-456',
        email: 'smoke.teacher@school.com',
        first_name: 'Smoke',
        last_name: 'Teacher',
        is_active: true,
      },
      permissions: ['attendance.view', 'student.view'],
      isAuthenticated: true,
      isLoading: false,
    });

    const mockTeacherSummary = {
      user_id: 'teacher-123',
      user_name: 'Smoke Teacher',
      assigned_students_count: 42,
      active_classes_count: 2,
      active_sections_count: 4,
    };
    vi.mocked(dashboardApi.getTeacherSummary).mockResolvedValue(mockTeacherSummary as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Teacher Workstation/i)).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument(); // assigned students
    });
  });

  it('renders error state on API failure', async () => {
    vi.mocked(dashboardApi.getAdminSummary).mockRejectedValue(
      new Error('Network error loading dashboard')
    );

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Administrative Command Center Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error loading dashboard/i)).toBeInTheDocument();
    });
  });
});
