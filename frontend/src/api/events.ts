import { apiClient } from '@/services/api/client';

export interface SchoolEvent {
  id: string;
  academic_year_id?: string;
  title: string;
  description?: string;
  event_type: string;
  start_datetime: string;
  end_datetime: string;
  all_day: boolean;
  venue?: string;
  audience_scope: string;
  status: string;
}

export const eventsApi = {
  getEvents: async (params?: {
    start_date?: string;
    end_date?: string;
    event_type?: string;
    status?: string;
    audience_scope?: string;
  }): Promise<SchoolEvent[]> => {
    const res = await apiClient.get('/api/v1/events', { params });
    return res.data.data;
  },

  getEventById: async (eventId: string): Promise<SchoolEvent> => {
    const res = await apiClient.get(`/api/v1/events/${eventId}`);
    return res.data.data;
  },

  createEvent: async (data: Partial<SchoolEvent>): Promise<any> => {
    const res = await apiClient.post('/api/v1/events', data);
    return res.data;
  },

  updateEvent: async (eventId: string, data: Partial<SchoolEvent>): Promise<any> => {
    const res = await apiClient.put(`/api/v1/events/${eventId}`, data);
    return res.data;
  },

  publishEvent: async (eventId: string): Promise<any> => {
    const res = await apiClient.put(`/api/v1/events/${eventId}/publish`);
    return res.data;
  },

  cancelEvent: async (eventId: string): Promise<any> => {
    const res = await apiClient.put(`/api/v1/events/${eventId}/cancel`);
    return res.data;
  },

  deleteEvent: async (eventId: string): Promise<any> => {
    const res = await apiClient.delete(`/api/v1/events/${eventId}`);
    return res.data;
  },
};
