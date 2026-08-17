import { apiClient } from './client';
import {
  PaginatedResponse,
  TeacherSubstitutionCreate,
  TeacherSubstitutionUpdate,
  TeacherSubstitutionDetail,
} from '@/types/models';

export interface SubstitutionFilters {
  timetable_entry_id?: string;
  original_teacher_id?: string;
  substitute_teacher_id?: string;
  substitution_date?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export const substitutionsApi = {
  getSubstitutions: async (
    params?: SubstitutionFilters
  ): Promise<PaginatedResponse<TeacherSubstitutionDetail>> => {
    return await apiClient.get('/teacher-substitutions', { params });
  },

  getSubstitution: async (id: string): Promise<TeacherSubstitutionDetail> => {
    return await apiClient.get(`/teacher-substitutions/${id}`);
  },

  createSubstitution: async (data: TeacherSubstitutionCreate): Promise<TeacherSubstitutionDetail> => {
    return await apiClient.post('/teacher-substitutions', data);
  },

  updateSubstitution: async (
    id: string,
    data: TeacherSubstitutionUpdate
  ): Promise<TeacherSubstitutionDetail> => {
    return await apiClient.put(`/teacher-substitutions/${id}`, data);
  },

  deleteSubstitution: async (id: string): Promise<void> => {
    await apiClient.delete(`/teacher-substitutions/${id}`);
  },
};
