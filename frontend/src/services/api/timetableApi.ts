import { apiClient } from './client';
import {
  PaginatedResponse,
  Timetable,
  TimetableCreate,
  TimetableDetail,
  TimetableEntryCreate,
  TimetableEntryDetail,
  TimetableStatus,
  TeacherScheduleEntry,
} from '@/types/models';

export interface TimetableFilters {
  academic_year_id?: string;
  school_class_id?: string;
  section_id?: string;
  academic_term_id?: string;
  status?: TimetableStatus;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export const timetableApi = {
  // Timetable containers
  getTimetables: async (params?: TimetableFilters): Promise<PaginatedResponse<Timetable>> => {
    return await apiClient.get('/timetables', { params });
  },

  getTimetable: async (id: string): Promise<TimetableDetail> => {
    return await apiClient.get(`/timetables/${id}`);
  },

  createTimetable: async (data: TimetableCreate): Promise<TimetableDetail> => {
    return await apiClient.post('/timetables', data);
  },

  getSectionTimetable: async (
    sectionId: string,
    params?: { academic_year_id?: string; academic_term_id?: string }
  ): Promise<TimetableDetail> => {
    return await apiClient.get(`/timetables/section/${sectionId}`, { params });
  },

  getTeacherSchedule: async (
    teacherId: string,
    params?: { academic_year_id?: string }
  ): Promise<TeacherScheduleEntry[]> => {
    return await apiClient.get(`/timetables/teacher/${teacherId}`, { params });
  },

  publishTimetable: async (id: string): Promise<TimetableDetail> => {
    return await apiClient.post(`/timetables/${id}/publish`);
  },

  archiveTimetable: async (id: string): Promise<TimetableDetail> => {
    return await apiClient.post(`/timetables/${id}/archive`);
  },

  // Timetable entries (nested under timetable)
  addEntry: async (timetableId: string, data: TimetableEntryCreate): Promise<TimetableEntryDetail> => {
    return await apiClient.post(`/timetables/${timetableId}/entries`, data);
  },

  listEntries: async (timetableId: string): Promise<TimetableEntryDetail[]> => {
    return await apiClient.get(`/timetables/${timetableId}/entries`);
  },

  // Standalone entry operations (via /timetable-entries)
  updateEntry: async (entryId: string, data: Partial<TimetableEntryCreate>): Promise<TimetableEntryDetail> => {
    return await apiClient.put(`/timetable-entries/${entryId}`, data);
  },

  deleteEntry: async (entryId: string): Promise<void> => {
    await apiClient.delete(`/timetable-entries/${entryId}`);
  },
};
