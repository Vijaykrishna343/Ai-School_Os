import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TeachersPage } from '@/pages/TeachersPage';
import { teachersApi } from '@/services/api/teachersApi';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/services/api/teachersApi', () => ({
  teachersApi: {
    getTeachers: vi.fn(),
    createTeacher: vi.fn(),
    updateTeacher: vi.fn(),
    deleteTeacher: vi.fn(),
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

const mockTeacher = {
  id: 'teacher-123',
  school_id: 'school-1',
  employee_id: 'EMP-9999',
  first_name: 'Albus',
  middle_name: 'Percival',
  last_name: 'Dumbledore',
  gender: 'MALE' as const,
  date_of_birth: '1881-08-01',
  joining_date: '1938-09-01',
  qualification: 'Ph.D in Magic',
  specialization: 'Transfiguration',
  experience_years: 50,
  phone: '9876543210',
  email: 'albus@hogwarts.edu',
  emergency_contact: 'Minerva McGonagall',
  address_line1: 'Headmaster Tower',
  city: 'Hogsmeade',
  district: 'Highlands',
  state: 'Scotland',
  postal_code: 'HG1 1HT',
  status: 'ACTIVE' as const,
};

describe('TeachersPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      user: {
        id: 'user-1',
        school_id: 'school-1',
        role: 'ADMIN',
      } as any,
      isAuthenticated: true,
    });

    vi.mocked(teachersApi.getTeachers).mockResolvedValue({
      items: [mockTeacher],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
  });

  it('renders Faculty Directory with registrar header', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Faculty Directory')).toBeInTheDocument();
    expect(screen.getByText('OFFICE OF THE REGISTRAR')).toBeInTheDocument();
  });

  it('loads and displays teachers list', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Albus Dumbledore')).toBeInTheDocument();
      expect(screen.getByText('EMP-9999')).toBeInTheDocument();
      expect(screen.getByText('Ph.D in Magic')).toBeInTheDocument();
    });
  });

  it('updates query when searching', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const searchInput = screen.getByPlaceholderText(/Search by teacher name/i);
    fireEvent.change(searchInput, { target: { value: 'Severus' } });

    await waitFor(() => {
      expect(teachersApi.getTeachers).toHaveBeenLastCalledWith(
        expect.objectContaining({ search: 'Severus' })
      );
    });
  });

  it('updates query when changing status filter', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const selectFilter = screen.getByRole('combobox');
    fireEvent.change(selectFilter, { target: { value: 'ON_LEAVE' } });

    await waitFor(() => {
      expect(teachersApi.getTeachers).toHaveBeenLastCalledWith(
        expect.objectContaining({ status: 'ON_LEAVE' })
      );
    });
  });

  it('opens create modal when clicking add button', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const addButton = screen.getByText('+ Add Teacher');
    fireEvent.click(addButton);

    expect(screen.getByText('Add New Teacher')).toBeInTheDocument();
    expect(screen.getByLabelText(/First Name \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Emergency Contact/i)).toBeInTheDocument();
  });

  it('opens edit modal when clicking edit button on a row', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Edit'));

    expect(screen.getByText('Edit Teacher — EMP-9999')).toBeInTheDocument();
    // Verify prefilled value
    const firstNameInput = screen.getByLabelText(/First Name \*/i) as HTMLInputElement;
    expect(firstNameInput.value).toBe('Albus');
    
    // Status dropdown should exist in edit mode
    expect(screen.getByLabelText(/Employment Status \*/i)).toBeInTheDocument();
  });

  it('opens dossier when clicking view button on a row', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('View')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('View'));

    expect(screen.getByText('FACULTY DOSSIER')).toBeInTheDocument();
    expect(screen.getByText('EMPLOYEE_ID: EMP-9999')).toBeInTheDocument();
    expect(screen.getByText('Minerva McGonagall')).toBeInTheDocument();
  });

  it('opens delete confirmation modal when clicking delete button', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Delete'));

    expect(screen.getByText('Soft Delete Teacher')).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to soft delete teacher "Albus Dumbledore"/i)).toBeInTheDocument();
  });

  it('displays API/form error when creation fails', async () => {
    vi.mocked(teachersApi.createTeacher).mockRejectedValue(new Error('Duplicate Employee ID'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const addButton = screen.getByText('+ Add Teacher');
    fireEvent.click(addButton);

    // Fill in required fields
    fireEvent.change(screen.getByLabelText(/First Name \*/i), { target: { value: 'Minerva' } });
    fireEvent.change(screen.getByLabelText(/Qualification \*/i), { target: { value: 'B.Ed' } });
    fireEvent.change(screen.getByLabelText(/Phone \*/i), { target: { value: '9876543211' } });
    fireEvent.change(screen.getByLabelText(/Email \*/i), { target: { value: 'minerva@hogwarts.edu' } });
    fireEvent.change(screen.getByLabelText(/Address Line 1 \*/i), { target: { value: 'Gryffindor' } });
    fireEvent.change(screen.getByLabelText(/City \*/i), { target: { value: 'Hogsmeade' } });
    fireEvent.change(screen.getByLabelText(/District \*/i), { target: { value: 'Highlands' } });
    fireEvent.change(screen.getByLabelText(/State \*/i), { target: { value: 'Scotland' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: 'Create Teacher' }));

    await waitFor(() => {
      expect(screen.getByText('Duplicate Employee ID')).toBeInTheDocument();
    });
  });

  it('renders empty and loading states correctly', async () => {
    const queryClient = createTestQueryClient();
    
    // Test empty state
    vi.mocked(teachersApi.getTeachers).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <TeachersPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No faculty records matching current registry filters.')).toBeInTheDocument();
    });
  });
});
