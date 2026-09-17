import { apiClient } from './client';
import {
  PaginatedResponse,
  ReceptionAnalyticsResponse,
  ReceptionInquiry,
  ReceptionInquiryCreate,
  ReceptionInquiryUpdate,
  VisitorBadgeResponse,
  VisitorCheckOut,
  VisitorCreate,
  VisitorDetail,
  VisitorPreRegister,
  VisitorSummary,
} from '@/types/models';

export interface VisitorFilterParams {
  status?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface ReceptionInquiryFilterParams {
  status?: string;
  start_date?: string;
  end_date?: string;
  appointment_date?: string;
  visitor_id?: string;
  host_type?: string;
  host_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const receptionApi = {
  // Visitor Operations
  preRegisterVisitor: async (data: VisitorPreRegister): Promise<VisitorDetail> => {
    return await apiClient.post('/visitors/pre-register', data);
  },

  checkInVisitor: async (data: VisitorCreate): Promise<VisitorDetail> => {
    return await apiClient.post('/visitors/check-in', data);
  },

  quickCheckInVisitor: async (id: string, payload?: VisitorCheckOut): Promise<VisitorDetail> => {
    return await apiClient.post(`/visitors/${id}/quick-check-in`, payload || {});
  },

  checkOutVisitor: async (id: string, payload?: VisitorCheckOut): Promise<VisitorDetail> => {
    return await apiClient.post(`/visitors/${id}/check-out`, payload || {});
  },

  getVisitors: async (params?: VisitorFilterParams): Promise<PaginatedResponse<VisitorSummary>> => {
    return await apiClient.get('/visitors', { params });
  },

  getVisitor: async (id: string): Promise<VisitorDetail> => {
    return await apiClient.get(`/visitors/${id}`);
  },

  getVisitorBadge: async (id: string): Promise<VisitorBadgeResponse> => {
    return await apiClient.get(`/visitors/${id}/badge`);
  },

  // Reception Inquiry & Appointment Operations
  createInquiry: async (data: ReceptionInquiryCreate): Promise<ReceptionInquiry> => {
    return await apiClient.post('/reception/inquiries', data);
  },

  getInquiries: async (params?: ReceptionInquiryFilterParams): Promise<PaginatedResponse<ReceptionInquiry>> => {
    return await apiClient.get('/reception/inquiries', { params });
  },

  getInquiry: async (id: string): Promise<ReceptionInquiry> => {
    return await apiClient.get(`/reception/inquiries/${id}`);
  },

  updateInquiry: async (id: string, data: ReceptionInquiryUpdate): Promise<ReceptionInquiry> => {
    return await apiClient.patch(`/reception/inquiries/${id}`, data);
  },

  // Reception Analytics
  getAnalytics: async (params?: { start_date?: string; end_date?: string }): Promise<ReceptionAnalyticsResponse> => {
    return await apiClient.get('/reception/analytics', { params });
  },
};
