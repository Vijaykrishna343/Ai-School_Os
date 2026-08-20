import { apiClient } from './client';
import {
  PaginatedResponse,
  Student,
  StudentCreate,
  StudentEnrollmentHistoryResponse,
  StudentUpdate,
  TransferCertificate,
  TransferCertificateCreate,
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

  getStudentEnrollmentHistory: async (id: string): Promise<{ student_id: string; enrollments: StudentEnrollmentHistoryResponse[]; total: number }> => {
    return await apiClient.get(`/students/${id}/enrollments`);
  },

  getTransferCertificates: async (studentId: string): Promise<{ student_id: string; certificates: TransferCertificate[]; total: number }> => {
    return await apiClient.get(`/students/${studentId}/transfer-certificates`);
  },

  issueTransferCertificate: async (studentId: string, data: TransferCertificateCreate): Promise<TransferCertificate> => {
    return await apiClient.post(`/students/${studentId}/transfer-certificate`, data);
  },
};
