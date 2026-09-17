import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AdmissionsPage } from '@/pages/AdmissionsPage';
import { admissionsApi } from '@/services/api/admissionsApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { useAuthStore } from '@/store/useAuthStore';
import {
  AcademicYear,
  AdmissionApplication,
  AdmissionCycle,
  Applicant,
  SchoolClass,
  Section,
} from '@/types/models';

// Mock API modules
vi.mock('@/services/api/admissionsApi', () => ({
  admissionsApi: {
    listCycles: vi.fn(),
    getCycle: vi.fn(),
    createCycle: vi.fn(),
    updateCycle: vi.fn(),
    deleteCycle: vi.fn(),
    listApplicants: vi.fn(),
    getApplicant: vi.fn(),
    createApplicant: vi.fn(),
    updateApplicant: vi.fn(),
    deleteApplicant: vi.fn(),
    listApplications: vi.fn(),
    getApplication: vi.fn(),
    createApplication: vi.fn(),
    updateApplication: vi.fn(),
    deleteApplication: vi.fn(),
    submitApplication: vi.fn(),
    reviewApplication: vi.fn(),
    recordDecision: vi.fn(),
    withdrawApplication: vi.fn(),
    getApplicationHistory: vi.fn(),
    getApplicationDecisions: vi.fn(),
  },
}));

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn(),
  },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: {
    getSchoolClasses: vi.fn(),
  },
}));

vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: {
    getSectionsByClass: vi.fn(),
  },
}));

// Mock Data
const mockAcademicYears: AcademicYear[] = [
  {
    id: 'ay-1',
    school_id: 'sch-1',
    name: '2026-2027',
    start_date: '2026-06-01',
    end_date: '2027-04-30',
    status: 'ACTIVE',
  },
];

const mockClasses: SchoolClass[] = [
  {
    id: 'cls-1',
    school_id: 'sch-1',
    name: 'Grade 1',
    display_order: 1,
    status: 'ACTIVE',
  },
];

const mockSections: Section[] = [
  {
    id: 'sec-1',
    school_class_id: 'cls-1',
    name: 'Section A',
    capacity: 40,
    status: 'ACTIVE',
  },
];

const mockCycles: AdmissionCycle[] = [
  {
    id: 'cyc-1',
    school_id: 'sch-1',
    academic_year_id: 'ay-1',
    name: 'AY 2026-27 General Intake',
    code: 'CYC-2026-GEN',
    start_date: '2026-01-01',
    end_date: '2026-05-31',
    status: 'ACTIVE',
    description: 'General admissions',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

const mockApplicants: Applicant[] = [
  {
    id: 'app-1',
    school_id: 'sch-1',
    admission_cycle_id: 'cyc-1',
    applicant_number: 'APP-2026-0001',
    first_name: 'Rohan',
    last_name: 'Sharma',
    date_of_birth: '2020-03-15',
    gender: 'MALE',
    email: 'rohan.sharma@example.com',
    phone: '+91-9876543210',
    parent_name: 'Rajesh Sharma',
    parent_phone: '+91-9876543210',
    source: 'WALK_IN',
    status: 'PROSPECT',
    notes: 'Interested in Grade 1',
    created_at: '2026-01-10T00:00:00Z',
    updated_at: '2026-01-10T00:00:00Z',
  },
];

const mockApplications: AdmissionApplication[] = [
  {
    id: 'appl-1',
    school_id: 'sch-1',
    applicant_id: 'app-1',
    admission_cycle_id: 'cyc-1',
    academic_year_id: 'ay-1',
    target_class_id: 'cls-1',
    target_section_id: 'sec-1',
    application_number: 'ADM-2026-0001',
    application_date: '2026-01-15',
    status: 'DRAFT',
    remarks: 'Online registration draft',
    created_at: '2026-01-15T00:00:00Z',
    updated_at: '2026-01-15T00:00:00Z',
  },
];

describe('AdmissionsPage Workstation UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default reference data mocks
    (academicYearsApi.getAcademicYears as any).mockResolvedValue({ items: mockAcademicYears, total: 1 });
    (schoolClassesApi.getSchoolClasses as any).mockResolvedValue({ items: mockClasses, total: 1 });
    (sectionsApi.getSectionsByClass as any).mockResolvedValue({ items: mockSections, total: 1 });

    (admissionsApi.listCycles as any).mockResolvedValue({
      items: mockCycles,
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (admissionsApi.listApplicants as any).mockResolvedValue({
      items: mockApplicants,
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (admissionsApi.listApplications as any).mockResolvedValue({
      items: mockApplications,
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    (admissionsApi.getApplicationHistory as any).mockResolvedValue({
      items: [
        {
          id: 'hist-1',
          school_id: 'sch-1',
          application_id: 'appl-1',
          old_status: null,
          new_status: 'DRAFT',
          changed_at: '2026-01-15T10:00:00Z',
          remarks: 'Draft created',
        },
      ],
      total: 1,
    });

    (admissionsApi.getApplicationDecisions as any).mockResolvedValue({
      items: [],
      total: 0,
    });

    // Default Auth: Super Admin
    useAuthStore.setState({
      user: {
        id: 'admin-id',
        email: 'admin@school.com',
        first_name: 'Super',
        last_name: 'Admin',
        is_super_admin: true,
        school_id: 'sch-1',
      } as any,
      permissions: [
        'admissions.view',
        'admissions.create',
        'admissions.update',
        'admissions.delete',
        'admissions.review',
        'admissions.manage',
      ],
      roles: [{ id: 'r-1', name: 'Super Admin', code: 'SUPER_ADMIN' }],
      isAuthenticated: true,
    });
  });

  it('1. Renders Admissions Management Workstation and default Dashboard metrics', async () => {
    render(<AdmissionsPage />);

    expect(screen.getByText('Admissions Management')).toBeInTheDocument();
    expect(screen.getByText('Pipeline Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Admission Cycles')).toBeInTheDocument();
    expect(screen.getByText('Applicants Directory')).toBeInTheDocument();
    expect(screen.getByText('Application Pipeline')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Active Intake Cycles')).toBeInTheDocument();
      expect(screen.getByText('Registered Prospects')).toBeInTheDocument();
      expect(screen.getByText('Total Applications')).toBeInTheDocument();
      expect(screen.getByText('Applications Pipeline Breakdown')).toBeInTheDocument();
    });
  });

  it('2. Navigates to Admission Cycles tab and renders cycles table', async () => {
    render(<AdmissionsPage />);

    const cyclesTab = screen.getByRole('button', { name: /Admission Cycles/i });
    fireEvent.click(cyclesTab);

    await waitFor(() => {
      expect(screen.getByText('AY 2026-27 General Intake')).toBeInTheDocument();
      expect(screen.getByText('CYC-2026-GEN')).toBeInTheDocument();
    });
  });

  it('3. Opens Create Cycle modal and submits cycle form', async () => {
    (admissionsApi.createCycle as any).mockResolvedValue({
      id: 'cyc-2',
      name: 'AY 2027 Nursery Intake',
      code: 'CYC-2027-NUR',
      status: 'DRAFT',
    });

    render(<AdmissionsPage />);

    // Switch to cycles tab
    fireEvent.click(screen.getByRole('button', { name: /Admission Cycles/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Create Cycle/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Create Cycle/i }));

    expect(screen.getByText('Create Admission Cycle')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/e.g. AY 2026-27 General Intake/i), {
      target: { value: 'AY 2027 Nursery Intake' },
    });
    fireEvent.change(screen.getByPlaceholderText(/e.g. CYC-2026-GEN/i), {
      target: { value: 'CYC-2027-NUR' },
    });

    const dateInputs = screen.getAllByDisplayValue('');
    const startDateInput = dateInputs.find((input) => input.getAttribute('type') === 'date');
    if (startDateInput) {
      fireEvent.change(startDateInput, { target: { value: '2026-06-01' } });
    }
    const remainingDateInputs = screen.getAllByDisplayValue('');
    const endDateInput = remainingDateInputs.find((input) => input.getAttribute('type') === 'date');
    if (endDateInput) {
      fireEvent.change(endDateInput, { target: { value: '2027-04-30' } });
    }

    const submitBtns = screen.getAllByRole('button', { name: /Create Cycle/i });
    const submitBtn = submitBtns.find((b) => b.getAttribute('type') === 'submit') || submitBtns[submitBtns.length - 1];
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(admissionsApi.createCycle).toHaveBeenCalled();
    });
  });

  it('4. Navigates to Applicants Directory and displays applicant list', async () => {
    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Applicants Directory/i }));

    await waitFor(() => {
      expect(screen.getByText('APP-2026-0001')).toBeInTheDocument();
      expect(screen.getByText(/Rohan Sharma/i)).toBeInTheDocument();
      expect(screen.getByText('Rajesh Sharma')).toBeInTheDocument();
    });
  });

  it('5. Navigates to Application Pipeline and submits a draft application', async () => {
    (admissionsApi.submitApplication as any).mockResolvedValue({
      ...mockApplications[0],
      status: 'SUBMITTED',
      submitted_at: '2026-01-16T00:00:00Z',
    });

    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByText('ADM-2026-0001')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Submit/i }));

    expect(screen.getByText('Submit Admission Application')).toBeInTheDocument();

    const confirmSubmitBtn = screen.getByRole('button', { name: /^Submit Application$/i });
    fireEvent.click(confirmSubmitBtn);

    await waitFor(() => {
      expect(admissionsApi.submitApplication).toHaveBeenCalledWith('appl-1', { remarks: undefined });
    });
  });

  it('6. Starts review on submitted application and records decision', async () => {
    const submittedApp: AdmissionApplication = {
      ...mockApplications[0],
      status: 'SUBMITTED',
    };
    (admissionsApi.listApplications as any).mockResolvedValue({
      items: [submittedApp],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (admissionsApi.reviewApplication as any).mockResolvedValue({
      ...submittedApp,
      status: 'UNDER_REVIEW',
    });

    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Review/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Review/i }));

    expect(screen.getByText('Move Application Into Review')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^Start Review$/i }));

    await waitFor(() => {
      expect(admissionsApi.reviewApplication).toHaveBeenCalledWith('appl-1', { remarks: undefined });
    });
  });

  it('7. Opens Application Dossier and displays history timeline', async () => {
    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByTitle('View Dossier & History')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle('View Dossier & History'));

    await waitFor(() => {
      expect(screen.getByText(/Application Dossier · ADM-2026-0001/i)).toBeInTheDocument();
      expect(screen.getByText('Audit Timeline (Status History)')).toBeInTheDocument();
      expect(screen.getByText('Remarks: Draft created')).toBeInTheDocument();
    });
  });

  it('8. Hides creation and management action buttons for read-only viewer user', async () => {
    useAuthStore.setState({
      user: {
        id: 'viewer-id',
        email: 'viewer@school.com',
        first_name: 'Victor',
        last_name: 'Viewer',
        is_super_admin: false,
        school_id: 'sch-1',
      } as any,
      permissions: ['admissions.view'],
      roles: [{ id: 'r-2', name: 'Admissions Viewer', code: 'ADMISSIONS_VIEWER' }],
      isAuthenticated: true,
    });

    render(<AdmissionsPage />);

    // Dashboard renders
    expect(screen.getByText('Admissions Management')).toBeInTheDocument();

    // Switch to cycles tab
    fireEvent.click(screen.getByRole('button', { name: /Admission Cycles/i }));

    await waitFor(() => {
      expect(screen.getByText('AY 2026-27 General Intake')).toBeInTheDocument();
    });

    // Create Cycle button should NOT exist
    expect(screen.queryByRole('button', { name: /Create Cycle/i })).not.toBeInTheDocument();

    // Switch to application pipeline
    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByText('ADM-2026-0001')).toBeInTheDocument();
    });

    // Action buttons like Submit, Review, Decision, Withdraw should NOT exist for viewer
    expect(screen.queryByRole('button', { name: /^Submit$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^New Application$/i })).not.toBeInTheDocument();
  });

  it('9. Records admission decision on under-review application', async () => {
    const underReviewApp: AdmissionApplication = {
      ...mockApplications[0],
      status: 'UNDER_REVIEW',
    };
    (admissionsApi.listApplications as any).mockResolvedValue({
      items: [underReviewApp],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (admissionsApi.recordDecision as any).mockResolvedValue({
      id: 'dec-1',
      application_id: 'appl-1',
      decision_type: 'ACCEPTED',
      decided_at: '2026-01-20T00:00:00Z',
    });

    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Decision/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Decision/i }));

    expect(screen.getByText('Record Admission Decision')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/Reasoning or evaluation feedback/i), {
      target: { value: 'Candidate meets all admission criteria' },
    });

    const commitBtn = screen.getByRole('button', { name: /Commit Decision/i });
    fireEvent.click(commitBtn);

    await waitFor(() => {
      expect(admissionsApi.recordDecision).toHaveBeenCalledWith('appl-1', {
        decision_type: 'ACCEPTED',
        comments: 'Candidate meets all admission criteria',
        conditions: undefined,
      });
    });
  });

  it('10. Withdraws an active application with reason', async () => {
    (admissionsApi.withdrawApplication as any).mockResolvedValue({
      ...mockApplications[0],
      status: 'WITHDRAWN',
    });

    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Application Pipeline/i }));

    await waitFor(() => {
      expect(screen.getByTitle('Withdraw Application')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle('Withdraw Application'));

    expect(screen.getByText('Withdraw Application')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/Parent relocated/i), {
      target: { value: 'Parent relocated to another state' },
    });

    const confirmWithdrawBtn = screen.getByRole('button', { name: /Confirm Withdrawal/i });
    fireEvent.click(confirmWithdrawBtn);

    await waitFor(() => {
      expect(admissionsApi.withdrawApplication).toHaveBeenCalledWith('appl-1', {
        reason: 'Parent relocated to another state',
        remarks: undefined,
      });
    });
  });

  it('11. Handles error state and empty state across workstation tabs', async () => {
    (admissionsApi.listCycles as any).mockRejectedValue({
      response: { data: { detail: 'Network connectivity error' } },
    });

    render(<AdmissionsPage />);

    fireEvent.click(screen.getByRole('button', { name: /Admission Cycles/i }));

    await waitFor(() => {
      expect(screen.getByText('Network connectivity error')).toBeInTheDocument();
    });

    // Empty State on Applicants
    (admissionsApi.listApplicants as any).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    });

    fireEvent.click(screen.getByRole('button', { name: /Applicants Directory/i }));

    await waitFor(() => {
      expect(screen.getByText('No applicants registered')).toBeInTheDocument();
    });
  });
});

