import { apiClient } from './client';
import {
  AcademicTerm,
  AcademicTermCreate,
  AcademicTermUpdate,
  PaginatedResponse,
} from '@/types/models';

export const academicTermsApi = {
  getAcademicTerms: async (params?: {
    academic_year_id?: string;
    is_active?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<AcademicTerm>> => {
    return await apiClient.get('/academic-terms', { params });
  },

  getAcademicTerm: async (id: string): Promise<AcademicTerm> => {
    return await apiClient.get(`/academic-terms/${id}`);
  },

  createAcademicTerm: async (data: AcademicTermCreate): Promise<AcademicTerm> => {
    return await apiClient.post('/academic-terms', data);
  },

  updateAcademicTerm: async (id: string, data: AcademicTermUpdate): Promise<AcademicTerm> => {
    return await apiClient.put(`/academic-terms/${id}`, data);
  },

  deleteAcademicTerm: async (id: string): Promise<void> => {
    await apiClient.delete(`/academic-terms/${id}`);
  },
};
