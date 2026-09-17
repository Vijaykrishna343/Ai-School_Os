import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MobileNav } from '@/layouts/MobileNav';
import { useAuthStore } from '@/store/useAuthStore';

describe('MobileNav Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders System Administration and Operations items when permissions exist', () => {
    useAuthStore.setState({
      permissions: ['user.view', 'role.view', 'school.view', 'progression_matrix.view', 'hostel.view'],
    });

    render(
      <MemoryRouter>
        <MobileNav isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Roles & Access')).toBeInTheDocument();
    expect(screen.getByText('School Profile')).toBeInTheDocument();
    expect(screen.getByText('Progression')).toBeInTheDocument();
    expect(screen.getByText('Hostel Management')).toBeInTheDocument();
  });

  it('hides System Administration and Operations items when permissions are absent', () => {
    useAuthStore.setState({
      permissions: [],
    });

    render(
      <MemoryRouter>
        <MobileNav isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
    expect(screen.queryByText('Roles & Access')).not.toBeInTheDocument();
    expect(screen.queryByText('School Profile')).not.toBeInTheDocument();
    expect(screen.queryByText('Progression')).not.toBeInTheDocument();
    expect(screen.queryByText('Hostel Management')).not.toBeInTheDocument();
  });
});
