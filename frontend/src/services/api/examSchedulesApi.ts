import { apiClient } from './client';
import {
  PaginatedResponse,
  ExamSchedule,
  ExamScheduleCreate,
  ExamScheduleUpdate,
} from '@/types/models';

export interface ExamScheduleFilters {
  exam_id?: string;
  academic_year_id?: string;
  school_class_id?: string;
  section_id?: string;
  subject_id?: string;
  exam_date?: string;
  page?: number;
  page_size?: number;
}

export const examSchedulesApi = {
  getExamSchedules: async (params?: ExamScheduleFilters): Promise<PaginatedResponse<ExamSchedule>> => {
    return await apiClient.get('/exam-schedules', { params });
  },

  getExamSchedule: async (id: string): Promise<ExamSchedule> => {
    return await apiClient.get(`/exam-schedules/${id}`);
  },

  createExamSchedule: async (data: ExamScheduleCreate): Promise<ExamSchedule> => {
    return await apiClient.post('/exam-schedules', data);
  },

  updateExamSchedule: async (id: string, data: ExamScheduleUpdate): Promise<ExamSchedule> => {
    return await apiClient.put(`/exam-schedules/${id}`, data);
  },

  deleteExamSchedule: async (id: string): Promise<void> => {
    await apiClient.delete(`/exam-schedules/${id}`);
  },
};
