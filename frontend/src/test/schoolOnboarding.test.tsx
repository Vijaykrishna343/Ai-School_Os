import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SchoolOnboardingWizardModal } from '@/components/schools/SchoolOnboardingWizardModal';
import { schoolOnboardingApi, SchoolOnboardingResult } from '@/services/api/schoolOnboardingApi';

vi.mock('@/services/api/schoolOnboardingApi', () => ({
  schoolOnboardingApi: {
    onboardSchool: vi.fn(),
  },
}));

const mockProvisionResult: SchoolOnboardingResult = {
  school_id: 'sch-uuid-1234',
  name: 'Cambridge Global Academy',
  code: 'CGA01',
  status: 'ACTIVE',
  subscription_tier: 'STANDARD',
  admin_user_id: 'user-uuid-5678',
  admin_email: 'admin@cga.edu',
  admin_name: 'John Doe',
  academic_year_id: 'ay-uuid-9999',
  academic_year_name: '2026-2027',
  roles_provisioned_count: 12,
  classes_provisioned_count: 15,
  message: 'School tenant provisioned successfully.',
};

describe('SchoolOnboardingWizardModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Step 1 (School Identity) when opened', () => {
    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.getByText('School Tenant Onboarding & Provisioning Wizard')).toBeInTheDocument();
    expect(screen.getByText('School Details & Address')).toBeInTheDocument();
    expect(screen.getByLabelText('School Name')).toBeInTheDocument();
    expect(screen.getByLabelText('School Code')).toBeInTheDocument();
  });

  it('validates Step 1 required fields before allowing progression to Step 2', async () => {
    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Click Next without filling form
    fireEvent.click(screen.getByText('Next Step'));

    expect(await screen.findByText(/Please provide a valid school name/i)).toBeInTheDocument();

    // Fill valid Step 1 details
    fireEvent.change(screen.getByLabelText('School Name'), { target: { value: 'Cambridge Global Academy' } });
    fireEvent.change(screen.getByLabelText('School Code'), { target: { value: 'CGA01' } });
    fireEvent.change(screen.getByLabelText('Address Line 1'), { target: { value: '100 University Ave' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Bangalore' } });
    fireEvent.change(screen.getByLabelText('District'), { target: { value: 'Bangalore Urban' } });
    fireEvent.change(screen.getByLabelText('State'), { target: { value: 'Karnataka' } });
    fireEvent.change(screen.getByLabelText('Postal Code'), { target: { value: '560001' } });

    fireEvent.click(screen.getByText('Next Step'));

    // Should transition to Step 2
    expect(await screen.findByText('Initial School Administrator Account')).toBeInTheDocument();
  });

  it('validates Step 2 admin passwords match and are at least 8 characters', async () => {
    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill Step 1
    fireEvent.change(screen.getByLabelText('School Name'), { target: { value: 'Cambridge Global Academy' } });
    fireEvent.change(screen.getByLabelText('School Code'), { target: { value: 'CGA01' } });
    fireEvent.change(screen.getByLabelText('Address Line 1'), { target: { value: '100 University Ave' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Bangalore' } });
    fireEvent.change(screen.getByLabelText('District'), { target: { value: 'Bangalore Urban' } });
    fireEvent.change(screen.getByLabelText('State'), { target: { value: 'Karnataka' } });
    fireEvent.change(screen.getByLabelText('Postal Code'), { target: { value: '560001' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 2
    expect(await screen.findByText('Initial School Administrator Account')).toBeInTheDocument();

    // Fill short password
    fireEvent.change(screen.getByLabelText('Admin First Name'), { target: { value: 'John' } });
    fireEvent.change(screen.getByLabelText('Admin Last Name'), { target: { value: 'Doe' } });
    fireEvent.change(screen.getByLabelText('Admin Email'), { target: { value: 'admin@cga.edu' } });
    fireEvent.change(screen.getByLabelText('Admin Password'), { target: { value: 'short' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'short' } });
    fireEvent.click(screen.getByText('Next Step'));

    expect(await screen.findByText(/at least 8 characters long/i)).toBeInTheDocument();

    // Fill mismatched password
    fireEvent.change(screen.getByLabelText('Admin Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'DifferentPassword123!' } });
    fireEvent.click(screen.getByText('Next Step'));

    expect(await screen.findByText(/Password and Confirm Password do not match/i)).toBeInTheDocument();

    // Fill valid matching password
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Should transition to Step 3
    expect(await screen.findByText('Academic Calendar & Initial Class Templates')).toBeInTheDocument();
  });

  it('allows navigating Back and preserves entered data', async () => {
    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Step 1
    fireEvent.change(screen.getByLabelText('School Name'), { target: { value: 'Cambridge Global Academy' } });
    fireEvent.change(screen.getByLabelText('School Code'), { target: { value: 'CGA01' } });
    fireEvent.change(screen.getByLabelText('Address Line 1'), { target: { value: '100 University Ave' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Bangalore' } });
    fireEvent.change(screen.getByLabelText('District'), { target: { value: 'Bangalore Urban' } });
    fireEvent.change(screen.getByLabelText('State'), { target: { value: 'Karnataka' } });
    fireEvent.change(screen.getByLabelText('Postal Code'), { target: { value: '560001' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 2
    expect(await screen.findByText('Initial School Administrator Account')).toBeInTheDocument();

    // Click Back
    fireEvent.click(screen.getByText('Back'));

    // Back in Step 1, data should be preserved
    expect(screen.getByLabelText('School Name')).toHaveValue('Cambridge Global Academy');
    expect(screen.getByLabelText('School Code')).toHaveValue('CGA01');
  });

  it('completes all steps and successfully invokes schoolOnboardingApi', async () => {
    vi.mocked(schoolOnboardingApi.onboardSchool).mockResolvedValueOnce(mockProvisionResult);

    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Step 1
    fireEvent.change(screen.getByLabelText('School Name'), { target: { value: 'Cambridge Global Academy' } });
    fireEvent.change(screen.getByLabelText('School Code'), { target: { value: 'CGA01' } });
    fireEvent.change(screen.getByLabelText('Address Line 1'), { target: { value: '100 University Ave' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Bangalore' } });
    fireEvent.change(screen.getByLabelText('District'), { target: { value: 'Bangalore Urban' } });
    fireEvent.change(screen.getByLabelText('State'), { target: { value: 'Karnataka' } });
    fireEvent.change(screen.getByLabelText('Postal Code'), { target: { value: '560001' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 2
    expect(await screen.findByText('Initial School Administrator Account')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Admin First Name'), { target: { value: 'John' } });
    fireEvent.change(screen.getByLabelText('Admin Last Name'), { target: { value: 'Doe' } });
    fireEvent.change(screen.getByLabelText('Admin Email'), { target: { value: 'admin@cga.edu' } });
    fireEvent.change(screen.getByLabelText('Admin Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 3
    expect(await screen.findByText('Academic Calendar & Initial Class Templates')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Next Step'));

    // Step 4: Review & Provision
    expect(await screen.findByText('Review & Provision Tenant')).toBeInTheDocument();
    const provisionBtn = screen.getByRole('button', { name: /Provision School Tenant/i });
    expect(provisionBtn).toBeDisabled();

    // Check confirmation checkbox
    fireEvent.click(screen.getByLabelText('Confirm Provisioning'));
    expect(provisionBtn).toBeEnabled();

    // Submit provisioning
    fireEvent.click(provisionBtn);

    await waitFor(() => {
      expect(schoolOnboardingApi.onboardSchool).toHaveBeenCalledTimes(1);
    });

    // Check payload structure
    expect(schoolOnboardingApi.onboardSchool).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Cambridge Global Academy',
        code: 'CGA01',
        admin: expect.objectContaining({
          first_name: 'John',
          last_name: 'Doe',
          email: 'admin@cga.edu',
          password: 'AdminPassword123!',
        }),
        academic_year: expect.objectContaining({
          name: '2026-2027',
        }),
      })
    );

    // Verify Success screen rendered
    expect(await screen.findByText('Tenant Provisioned Successfully!')).toBeInTheDocument();
    expect(screen.getByText('Done & Close')).toBeInTheDocument();
    expect(mockOnSuccess).toHaveBeenCalledTimes(1);
  });

  it('displays error alert when API returns conflict or error', async () => {
    vi.mocked(schoolOnboardingApi.onboardSchool).mockRejectedValueOnce(
      new Error("School code 'CGA01' already exists.")
    );

    render(
      <SchoolOnboardingWizardModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Step 1
    fireEvent.change(screen.getByLabelText('School Name'), { target: { value: 'Cambridge Global Academy' } });
    fireEvent.change(screen.getByLabelText('School Code'), { target: { value: 'CGA01' } });
    fireEvent.change(screen.getByLabelText('Address Line 1'), { target: { value: '100 University Ave' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Bangalore' } });
    fireEvent.change(screen.getByLabelText('District'), { target: { value: 'Bangalore Urban' } });
    fireEvent.change(screen.getByLabelText('State'), { target: { value: 'Karnataka' } });
    fireEvent.change(screen.getByLabelText('Postal Code'), { target: { value: '560001' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 2
    expect(await screen.findByText('Initial School Administrator Account')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Admin First Name'), { target: { value: 'John' } });
    fireEvent.change(screen.getByLabelText('Admin Last Name'), { target: { value: 'Doe' } });
    fireEvent.change(screen.getByLabelText('Admin Email'), { target: { value: 'admin@cga.edu' } });
    fireEvent.change(screen.getByLabelText('Admin Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'AdminPassword123!' } });
    fireEvent.click(screen.getByText('Next Step'));

    // Step 3
    expect(await screen.findByText('Academic Calendar & Initial Class Templates')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Next Step'));

    // Step 4
    expect(await screen.findByText('Review & Provision Tenant')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Confirm Provisioning'));
    const provisionBtn = screen.getByRole('button', { name: /Provision School Tenant/i });
    fireEvent.click(provisionBtn);

    expect(await screen.findByText("School code 'CGA01' already exists.")).toBeInTheDocument();
  });
});
