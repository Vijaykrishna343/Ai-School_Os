import { apiClient } from './client';
import {
  ClassProgressionRule,
  ClassProgressionRuleCreate,
  ClassProgressionRuleUpdate,
  ProgressionPreviewResponse,
  ProgressionExecutionData,
  PaginatedResponse,
} from '@/types/models';

export const progressionApi = {
  getRules: async (params?: {
    source_class_id?: string;
    target_class_id?: string;
    is_terminal?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<ClassProgressionRule>> => {
    return await apiClient.get('/progression-matrix', { params });
  },

  createRule: async (data: ClassProgressionRuleCreate): Promise<ClassProgressionRule> => {
    return await apiClient.post('/progression-matrix', data);
  },

  updateRule: async (id: string, data: ClassProgressionRuleUpdate): Promise<ClassProgressionRule> => {
    return await apiClient.put(`/progression-matrix/${id}`, data);
  },

  deleteRule: async (id: string): Promise<void> => {
    await apiClient.delete(`/progression-matrix/${id}`);
  },

  generatePreview: async (
    academicYearId: string,
    data: { target_academic_year_id: string; page?: number; page_size?: number }
  ): Promise<ProgressionPreviewResponse> => {
    return await apiClient.post(`/academic-years/${academicYearId}/progression-preview`, data);
  },

  executeRollover: async (
    academicYearId: string,
    data: { target_academic_year_id: string; execution_plan_hash: string; confirm_warnings: boolean },
    idempotencyKey: string
  ): Promise<ProgressionExecutionData> => {
    return await apiClient.post(`/academic-years/${academicYearId}/progression-execute`, data, {
      headers: {
        'Idempotency-Key': idempotencyKey,
      },
    });
  },
};
