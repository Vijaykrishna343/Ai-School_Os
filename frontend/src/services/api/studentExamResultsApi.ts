import { apiClient } from './client';
import {
  PaginatedResponse,
  StudentExamResult,
  StudentExamResultCreate,
  StudentExamResultUpdate,
} from '@/types/models';

export interface StudentExamResultFilters {
  exam_schedule_id?: string;
  student_id?: string;
  page?: number;
  page_size?: number;
}

export const studentExamResultsApi = {
  getStudentExamResults: async (params?: StudentExamResultFilters): Promise<PaginatedResponse<StudentExamResult>> => {
    return await apiClient.get('/student-exam-results', { params });
  },

  getStudentExamResult: async (id: string): Promise<StudentExamResult> => {
    return await apiClient.get(`/student-exam-results/${id}`);
  },

  createStudentExamResult: async (data: StudentExamResultCreate): Promise<StudentExamResult> => {
    return await apiClient.post('/student-exam-results', data);
  },

  updateStudentExamResult: async (id: string, data: StudentExamResultUpdate): Promise<StudentExamResult> => {
    return await apiClient.put(`/student-exam-results/${id}`, data);
  },

  deleteStudentExamResult: async (id: string): Promise<void> => {
    await apiClient.delete(`/student-exam-results/${id}`);
  },
};
