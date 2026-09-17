import { apiClient } from './client';
import {
  AdmissionApplication,
  AdmissionApplicationCreate,
  AdmissionApplicationStatus,
  AdmissionApplicationUpdate,
  AdmissionCycle,
  AdmissionCycleCreate,
  AdmissionCycleStatus,
  AdmissionCycleUpdate,
  AdmissionDecision,
  AdmissionDecisionCreate,
  Applicant,
  ApplicantCreate,
  ApplicantStatus,
  ApplicantUpdate,
  ApplicationReviewRequest,
  ApplicationStatusHistory,
  ApplicationSubmitRequest,
  ApplicationWithdrawRequest,
  PaginatedResponse,
} from '@/types/models';

export interface AdmissionCycleFilterParams {
  academic_year_id?: string;
  status?: AdmissionCycleStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ApplicantFilterParams {
  admission_cycle_id?: string;
  status?: ApplicantStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AdmissionApplicationFilterParams {
  applicant_id?: string;
  admission_cycle_id?: string;
  academic_year_id?: string;
  target_class_id?: string;
  status?: AdmissionApplicationStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export const admissionsApi = {
  // ---------------------------------------------------------------------------
  // 1. Admission Cycles
  // ---------------------------------------------------------------------------
  listCycles: async (
    params?: AdmissionCycleFilterParams
  ): Promise<PaginatedResponse<AdmissionCycle>> => {
    const response = await apiClient.get<PaginatedResponse<AdmissionCycle>>(
      '/admissions/cycles',
      { params }
    );
    return response.data;
  },

  getCycle: async (cycleId: string): Promise<AdmissionCycle> => {
    const response = await apiClient.get<AdmissionCycle>(
      `/admissions/cycles/${cycleId}`
    );
    return response.data;
  },

  createCycle: async (data: AdmissionCycleCreate): Promise<AdmissionCycle> => {
    const response = await apiClient.post<AdmissionCycle>(
      '/admissions/cycles',
      data
    );
    return response.data;
  },

  updateCycle: async (
    cycleId: string,
    data: AdmissionCycleUpdate
  ): Promise<AdmissionCycle> => {
    const response = await apiClient.put<AdmissionCycle>(
      `/admissions/cycles/${cycleId}`,
      data
    );
    return response.data;
  },

  deleteCycle: async (cycleId: string): Promise<void> => {
    await apiClient.delete(`/admissions/cycles/${cycleId}`);
  },

  // ---------------------------------------------------------------------------
  // 2. Applicants / Prospects
  // ---------------------------------------------------------------------------
  listApplicants: async (
    params?: ApplicantFilterParams
  ): Promise<PaginatedResponse<Applicant>> => {
    const response = await apiClient.get<PaginatedResponse<Applicant>>(
      '/admissions/applicants',
      { params }
    );
    return response.data;
  },

  getApplicant: async (applicantId: string): Promise<Applicant> => {
    const response = await apiClient.get<Applicant>(
      `/admissions/applicants/${applicantId}`
    );
    return response.data;
  },

  createApplicant: async (data: ApplicantCreate): Promise<Applicant> => {
    const response = await apiClient.post<Applicant>(
      '/admissions/applicants',
      data
    );
    return response.data;
  },

  updateApplicant: async (
    applicantId: string,
    data: ApplicantUpdate
  ): Promise<Applicant> => {
    const response = await apiClient.put<Applicant>(
      `/admissions/applicants/${applicantId}`,
      data
    );
    return response.data;
  },

  deleteApplicant: async (applicantId: string): Promise<void> => {
    await apiClient.delete(`/admissions/applicants/${applicantId}`);
  },

  // ---------------------------------------------------------------------------
  // 3. Applications & Lifecycle
  // ---------------------------------------------------------------------------
  listApplications: async (
    params?: AdmissionApplicationFilterParams
  ): Promise<PaginatedResponse<AdmissionApplication>> => {
    const response = await apiClient.get<PaginatedResponse<AdmissionApplication>>(
      '/admissions/applications',
      { params }
    );
    return response.data;
  },

  getApplication: async (
    applicationId: string
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.get<AdmissionApplication>(
      `/admissions/applications/${applicationId}`
    );
    return response.data;
  },

  createApplication: async (
    data: AdmissionApplicationCreate
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.post<AdmissionApplication>(
      '/admissions/applications',
      data
    );
    return response.data;
  },

  updateApplication: async (
    applicationId: string,
    data: AdmissionApplicationUpdate
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.put<AdmissionApplication>(
      `/admissions/applications/${applicationId}`,
      data
    );
    return response.data;
  },

  deleteApplication: async (applicationId: string): Promise<void> => {
    await apiClient.delete(`/admissions/applications/${applicationId}`);
  },

  submitApplication: async (
    applicationId: string,
    data?: ApplicationSubmitRequest
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.post<AdmissionApplication>(
      `/admissions/applications/${applicationId}/submit`,
      data || {}
    );
    return response.data;
  },

  reviewApplication: async (
    applicationId: string,
    data?: ApplicationReviewRequest
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.post<AdmissionApplication>(
      `/admissions/applications/${applicationId}/review`,
      data || {}
    );
    return response.data;
  },

  recordDecision: async (
    applicationId: string,
    data: AdmissionDecisionCreate
  ): Promise<AdmissionDecision> => {
    const response = await apiClient.post<AdmissionDecision>(
      `/admissions/applications/${applicationId}/decision`,
      data
    );
    return response.data;
  },

  withdrawApplication: async (
    applicationId: string,
    data: ApplicationWithdrawRequest
  ): Promise<AdmissionApplication> => {
    const response = await apiClient.post<AdmissionApplication>(
      `/admissions/applications/${applicationId}/withdraw`,
      data
    );
    return response.data;
  },

  getApplicationHistory: async (
    applicationId: string
  ): Promise<{ items: ApplicationStatusHistory[]; total: number }> => {
    const response = await apiClient.get<{
      items: ApplicationStatusHistory[];
      total: number;
    }>(`/admissions/applications/${applicationId}/history`);
    return response.data;
  },

  getApplicationDecisions: async (
    applicationId: string
  ): Promise<{ items: AdmissionDecision[]; total: number }> => {
    const response = await apiClient.get<{
      items: AdmissionDecision[];
      total: number;
    }>(`/admissions/applications/${applicationId}/decisions`);
    return response.data;
  },
};
