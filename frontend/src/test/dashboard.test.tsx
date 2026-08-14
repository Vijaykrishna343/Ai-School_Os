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

    // Welcome text or banner skeletal loading should appear
    expect(screen.queryByText(/Administrative Command Center/i)).not.toBeInTheDocument();
  });

  it('renders dashboard with real metrics when api success', async () => {
    const mockSummary = {
      active_students: 150,
      active_teachers: 15,
      active_parents: 120,
      active_classes: 10,
      active_sections: 20,
      current_academic_year: {
        id: 'ay-1',
        name: '2026-2027',
        status: 'ACTIVE',
        start_date: '2026-04-01',
        end_date: '2027-03-31',
      },
      current_academic_term: {
        id: 'term-1',
        name: 'Term 1',
        term_structure: 'TERM1',
      },
    };

    vi.mocked(dashboardApi.getAdminSummary).mockResolvedValue(mockSummary);

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
      expect(screen.getByText('15')).toBeInTheDocument();  // teachers
      expect(screen.getByText('120')).toBeInTheDocument(); // parents
      expect(screen.getByText('10')).toBeInTheDocument();  // classes
      expect(screen.getByText('20')).toBeInTheDocument();  // sections
      expect(screen.getByText('2026-2027')).toBeInTheDocument();
      expect(screen.getByText('Term 1')).toBeInTheDocument();
    });
  });

  it('renders error state on API failure', async () => {
    vi.mocked(dashboardApi.getAdminSummary).mockRejectedValue(new Error('Network error loading dashboard'));

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
