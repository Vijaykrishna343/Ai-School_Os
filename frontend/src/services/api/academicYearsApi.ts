import { apiClient } from './client';
import {
  AcademicYear,
  AcademicYearCreate,
  AcademicYearUpdate,
  PaginatedResponse,
} from '@/types/models';

export const academicYearsApi = {
  getCurrentAcademicYear: async (): Promise<PaginatedResponse<AcademicYear>> => {
    return await apiClient.get('/academic-years/current');
  },

  getAcademicYears: async (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<AcademicYear>> => {
    try {
      return await apiClient.get('/academic-years', { params });
    } catch (err: any) {
      if (err?.status === 403 || err?.response?.status === 403) {
        return await apiClient.get('/academic-years/current');
      }
      throw err;
    }
  },

  getAcademicYear: async (id: string): Promise<AcademicYear> => {
    return await apiClient.get(`/academic-years/${id}`);
  },

  createAcademicYear: async (data: AcademicYearCreate): Promise<AcademicYear> => {
    return await apiClient.post('/academic-years', data);
  },

  updateAcademicYear: async (id: string, data: AcademicYearUpdate): Promise<AcademicYear> => {
    return await apiClient.put(`/academic-years/${id}`, data);
  },

  deleteAcademicYear: async (id: string): Promise<void> => {
    await apiClient.delete(`/academic-years/${id}`);
  },
};
