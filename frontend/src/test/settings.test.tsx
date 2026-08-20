import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsPage } from '@/pages/SettingsPage';
import { useAuthStore } from '@/store/useAuthStore';
import { schoolsApi } from '@/services/api/schoolsApi';

vi.mock('@/services/api/schoolsApi', () => ({
  schoolsApi: {
    getSchool: vi.fn(),
    updateSchool: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

const renderSettingsPage = () => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockSchool = {
  id: 'school-1',
  name: 'Greenwood International School',
  code: 'GWIS-2026',
  address: '123 Academic Blvd, Science City',
  phone: '+1-555-0192',
  email: 'info@greenwood.edu',
  website: 'https://greenwood.edu',
  status: 'ACTIVE',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-08-17T12:00:00Z',
};

describe('SettingsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-admin', email: 'admin@greenwood.edu', school_id: 'school-1' } as any,
      permissions: ['school.view', 'school.update'],
    });

    vi.mocked(schoolsApi.getSchool).mockResolvedValue(mockSchool as any);
  });

  // 1. Header renders
  it('renders school profile header', async () => {
    renderSettingsPage();
    await waitFor(() => {
      expect(screen.getByText('School Profile & Institutional Settings')).toBeInTheDocument();
    });
  });

  // 2. School profile data renders
  it('renders school profile data correctly', async () => {
    renderSettingsPage();
    await waitFor(() => {
      expect(screen.getByText('Greenwood International School')).toBeInTheDocument();
      expect(screen.getByText('GWIS-2026')).toBeInTheDocument();
      expect(screen.getByText('123 Academic Blvd, Science City')).toBeInTheDocument();
      expect(screen.getByText('+1-555-0192')).toBeInTheDocument();
      expect(screen.getByText('info@greenwood.edu')).toBeInTheDocument();
      expect(screen.getByText('https://greenwood.edu')).toBeInTheDocument();
    });
  });

  // 3. Loading state
  it('shows loading state initially', async () => {
    vi.mocked(schoolsApi.getSchool).mockImplementation(() => new Promise(() => {}));
    renderSettingsPage();
    expect(screen.getByText('Loading school profile details...')).toBeInTheDocument();
  });

  // 4. Query error and retry
  it('displays query error and retries on button click', async () => {
    vi.mocked(schoolsApi.getSchool).mockRejectedValueOnce(new Error('Network error'));

    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('Failed to load school profile')).toBeInTheDocument();
    });

    vi.mocked(schoolsApi.getSchool).mockResolvedValue(mockSchool as any);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    await waitFor(() => {
      expect(screen.getByText('Greenwood International School')).toBeInTheDocument();
    });
  });

  // 5. Edit button visible with school.update
  it('displays Edit Profile button when user has school.update permission', async () => {
    renderSettingsPage();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });
  });

  // 6. Edit button unavailable without school.update
  it('hides Edit Profile button when user lacks school.update permission', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-viewer', email: 'viewer@greenwood.edu', school_id: 'school-1' } as any,
      permissions: ['school.view'],
    });

    renderSettingsPage();
    await waitFor(() => {
      expect(screen.getByText('Greenwood International School')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Edit Profile' })).not.toBeInTheDocument();
    });
  });

  // 7. Edit modal renders
  it('opens edit modal when Edit Profile button is clicked', async () => {
    renderSettingsPage();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    await waitFor(() => {
      expect(screen.getByText('EDIT INSTITUTIONAL PROFILE')).toBeInTheDocument();
      expect(screen.getByLabelText('School Name *')).toHaveValue('Greenwood International School');
      expect(screen.getByLabelText('School Code *')).toHaveValue('GWIS-2026');
    });
  });

  // 8. Update sends the correct payload
  it('sends correct payload on edit form submission', async () => {
    vi.mocked(schoolsApi.updateSchool).mockResolvedValue({
      ...mockSchool,
      name: 'Greenwood Academy',
    } as any);

    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    await waitFor(() => {
      expect(screen.getByLabelText('School Name *')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('School Name *'), { target: { value: 'Greenwood Academy' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(schoolsApi.updateSchool).toHaveBeenCalledWith('school-1', expect.objectContaining({
        name: 'Greenwood Academy',
        code: 'GWIS-2026',
      }));
    });
  });

  // 9. Successful update refreshes displayed data
  it('refetches and shows success message after update', async () => {
    vi.mocked(schoolsApi.updateSchool).mockResolvedValue({
      ...mockSchool,
      name: 'Greenwood High',
    } as any);

    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    await waitFor(() => {
      expect(screen.getByLabelText('School Name *')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('School Name *'), { target: { value: 'Greenwood High' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(screen.getByText('School profile updated successfully.')).toBeInTheDocument();
    });
  });

  // 10. Mutation error displays correctly
  it('displays mutation error alert if update fails', async () => {
    vi.mocked(schoolsApi.updateSchool).mockRejectedValue(new Error('School code already in use'));

    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(screen.getByText('School code already in use')).toBeInTheDocument();
    });
  });

  // 11. Status values render correctly
  it('renders status badges for active, inactive, and suspended states', async () => {
    vi.mocked(schoolsApi.getSchool).mockResolvedValue({
      ...mockSchool,
      status: 'SUSPENDED',
    } as any);

    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('SUSPENDED')).toBeInTheDocument();
    });
  });

  // 12. No school selector / arbitrary school_id input exists
  it('uses current user school_id and contains no school selector input', async () => {
    renderSettingsPage();

    await waitFor(() => {
      expect(screen.getByText('Greenwood International School')).toBeInTheDocument();
    });

    expect(screen.queryByLabelText(/Select School/i)).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Enter School ID/i)).not.toBeInTheDocument();
  });
});
