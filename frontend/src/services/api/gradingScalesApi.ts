import { apiClient } from './client';
import {
  PaginatedResponse,
  GradeScale,
  GradeScaleCreate,
  GradeScaleUpdate,
} from '@/types/models';

export interface GradeScaleFilters {
  is_default?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export const gradingScalesApi = {
  getGradeScales: async (params?: GradeScaleFilters): Promise<PaginatedResponse<GradeScale>> => {
    return await apiClient.get('/grading-scales', { params });
  },

  getGradeScale: async (id: string): Promise<GradeScale> => {
    return await apiClient.get(`/grading-scales/${id}`);
  },

  getDefaultGradeScale: async (): Promise<GradeScale> => {
    return await apiClient.get('/grading-scales/default');
  },

  createGradeScale: async (data: GradeScaleCreate): Promise<GradeScale> => {
    return await apiClient.post('/grading-scales', data);
  },

  updateGradeScale: async (id: string, data: GradeScaleUpdate): Promise<GradeScale> => {
    return await apiClient.put(`/grading-scales/${id}`, data);
  },

  deleteGradeScale: async (id: string): Promise<void> => {
    await apiClient.delete(`/grading-scales/${id}`);
  },

  matchGrade: async (percentage: number, gradeScaleId?: string): Promise<{ grade_code: string; grade_point: number; is_pass: boolean }> => {
    return await apiClient.post('/grading-scales/match-grade', { percentage, grade_scale_id: gradeScaleId });
  },
};
