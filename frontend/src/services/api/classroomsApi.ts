import { apiClient } from './client';
import {
  PaginatedResponse,
  Classroom,
  ClassroomCreate,
  ClassroomUpdate,
  RoomType,
} from '@/types/models';

export interface ClassroomFilters {
  room_type?: RoomType;
  search?: string;
  page?: number;
  page_size?: number;
}

export const classroomsApi = {
  getClassrooms: async (params?: ClassroomFilters): Promise<PaginatedResponse<Classroom>> => {
    return await apiClient.get('/classrooms', { params });
  },

  getClassroom: async (id: string): Promise<Classroom> => {
    return await apiClient.get(`/classrooms/${id}`);
  },

  createClassroom: async (data: ClassroomCreate): Promise<Classroom> => {
    return await apiClient.post('/classrooms', data);
  },

  updateClassroom: async (id: string, data: ClassroomUpdate): Promise<Classroom> => {
    return await apiClient.put(`/classrooms/${id}`, data);
  },

  deleteClassroom: async (id: string): Promise<void> => {
    await apiClient.delete(`/classrooms/${id}`);
  },
};
