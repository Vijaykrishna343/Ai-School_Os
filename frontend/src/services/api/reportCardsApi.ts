import { apiClient } from './client';
import {
  PaginatedResponse,
  ReportCard,
  ReportCardGenerateRequest,
  ReportCardRemarksUpdate,
  ReportCardStatus,
} from '@/types/models';

export interface ReportCardFilters {
  academic_year_id?: string;
  academic_term_id?: string;
  school_class_id?: string;
  section_id?: string;
  student_id?: string;
  status?: ReportCardStatus;
  page?: number;
  page_size?: number;
}

export const reportCardsApi = {
  getReportCards: async (params?: ReportCardFilters): Promise<PaginatedResponse<ReportCard>> => {
    return await apiClient.get('/report-cards', { params });
  },

  getReportCard: async (id: string): Promise<ReportCard> => {
    return await apiClient.get(`/report-cards/${id}`);
  },

  generateReportCards: async (data: ReportCardGenerateRequest): Promise<ReportCard[]> => {
    return await apiClient.post('/report-cards/generate', data);
  },

  updateRemarks: async (id: string, data: ReportCardRemarksUpdate): Promise<ReportCard> => {
    return await apiClient.put(`/report-cards/${id}/remarks`, data);
  },

  finalizeReportCard: async (id: string): Promise<ReportCard> => {
    return await apiClient.put(`/report-cards/${id}/finalize`);
  },

  publishReportCard: async (id: string): Promise<ReportCard> => {
    return await apiClient.put(`/report-cards/${id}/publish`);
  },
};
