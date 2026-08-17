import { apiClient } from './client';
import {
  PaginatedResponse,
  Exam,
  ExamCreate,
  ExamUpdate,
  AssessmentType,
  AttemptType,
  ExamStatus,
} from '@/types/models';

export interface ExamFilters {
  academic_year_id?: string;
  assessment_type?: AssessmentType;
  attempt_type?: AttemptType;
  status?: ExamStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export const examsApi = {
  getExams: async (params?: ExamFilters): Promise<PaginatedResponse<Exam>> => {
    return await apiClient.get('/exams', { params });
  },

  getExam: async (id: string): Promise<Exam> => {
    return await apiClient.get(`/exams/${id}`);
  },

  createExam: async (data: ExamCreate): Promise<Exam> => {
    return await apiClient.post('/exams', data);
  },

  updateExam: async (id: string, data: ExamUpdate): Promise<Exam> => {
    return await apiClient.put(`/exams/${id}`, data);
  },

  deleteExam: async (id: string): Promise<void> => {
    await apiClient.delete(`/exams/${id}`);
  },
};
