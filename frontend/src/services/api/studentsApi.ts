import { apiClient } from './client';
import {
  PaginatedResponse,
  Student,
  StudentCreate,
  StudentEnrollmentHistory,
  StudentUpdate,
} from '@/types/models';

export interface StudentFilterParams {
  school_class_id?: string;
  section_id?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const studentsApi = {
  getStudents: async (params?: StudentFilterParams): Promise<PaginatedResponse<Student>> => {
    return await apiClient.get('/students', { params });
  },

  getStudent: async (id: string): Promise<Student> => {
    return await apiClient.get(`/students/${id}`);
  },

  createStudent: async (data: StudentCreate): Promise<Student> => {
    return await apiClient.post('/students', data);
  },

  updateStudent: async (id: string, data: StudentUpdate): Promise<Student> => {
    return await apiClient.put(`/students/${id}`, data);
  },

  deleteStudent: async (id: string): Promise<void> => {
    await apiClient.delete(`/students/${id}`);
  },

  getStudentEnrollmentHistory: async (id: string): Promise<StudentEnrollmentHistory[]> => {
    return await apiClient.get(`/students/${id}/enrollment-history`);
  },
};
