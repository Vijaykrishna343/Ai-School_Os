import { apiClient } from './client';
import {
  PaginatedResponse,
  Section,
  SectionCreate,
  SectionUpdate,
} from '@/types/models';

export const sectionsApi = {
  getSectionsByClass: async (
    classId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<Section>> => {
    return await apiClient.get(`/sections/class/${classId}`, { params });
  },

  getSection: async (id: string): Promise<Section> => {
    return await apiClient.get(`/sections/${id}`);
  },

  createSection: async (data: SectionCreate): Promise<Section> => {
    return await apiClient.post('/sections', data);
  },

  updateSection: async (id: string, data: SectionUpdate): Promise<Section> => {
    return await apiClient.put(`/sections/${id}`, data);
  },

  deleteSection: async (id: string): Promise<void> => {
    await apiClient.delete(`/sections/${id}`);
  },
};
