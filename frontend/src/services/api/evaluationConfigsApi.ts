import { apiClient } from './client';
import {
  PaginatedResponse,
  EvaluationConfig,
  EvaluationConfigCreate,
} from '@/types/models';

export interface EvaluationConfigFilters {
  academic_year_id?: string;
  page?: number;
  page_size?: number;
}

export const evaluationConfigsApi = {
  getEvaluationConfigs: async (params?: EvaluationConfigFilters): Promise<PaginatedResponse<EvaluationConfig>> => {
    return await apiClient.get('/evaluation-configs', { params });
  },

  getEvaluationConfig: async (id: string): Promise<EvaluationConfig> => {
    return await apiClient.get(`/evaluation-configs/${id}`);
  },

  createEvaluationConfig: async (data: EvaluationConfigCreate): Promise<EvaluationConfig> => {
    return await apiClient.post('/evaluation-configs', data);
  },
};
