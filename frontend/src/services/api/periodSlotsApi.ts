import { apiClient } from './client';
import {
  PaginatedResponse,
  PeriodSlot,
  PeriodSlotCreate,
  PeriodSlotUpdate,
  PeriodType,
} from '@/types/models';

export interface PeriodSlotFilters {
  period_type?: PeriodType;
  search?: string;
  page?: number;
  page_size?: number;
}

export const periodSlotsApi = {
  getPeriodSlots: async (params?: PeriodSlotFilters): Promise<PaginatedResponse<PeriodSlot>> => {
    return await apiClient.get('/period-slots', { params });
  },

  getPeriodSlot: async (id: string): Promise<PeriodSlot> => {
    return await apiClient.get(`/period-slots/${id}`);
  },

  createPeriodSlot: async (data: PeriodSlotCreate): Promise<PeriodSlot> => {
    return await apiClient.post('/period-slots', data);
  },

  updatePeriodSlot: async (id: string, data: PeriodSlotUpdate): Promise<PeriodSlot> => {
    return await apiClient.put(`/period-slots/${id}`, data);
  },

  deletePeriodSlot: async (id: string): Promise<void> => {
    await apiClient.delete(`/period-slots/${id}`);
  },
};
