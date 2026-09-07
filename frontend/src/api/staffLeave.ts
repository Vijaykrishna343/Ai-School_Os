import { apiClient } from '@/services/api/client';

export interface StaffLeaveType {
  id: string;
  school_id: string;
  code: string;
  name: string;
  description?: string;
  max_days_per_year: number;
  requires_attachment: boolean;
  is_paid: boolean;
  is_active: boolean;
}

export interface StaffLeaveBalance {
  id: string;
  school_id: string;
  teacher_id: string;
  academic_year_id: string;
  leave_type_id: string;
  leave_type_code: string;
  leave_type_name: string;
  allocated_days: number;
  used_days: number;
  pending_days: number;
  remaining_days: number;
}

export interface StaffLeaveApprovalHistory {
  id: string;
  action_by_user_id: string;
  action_by_name?: string;
  action: string;
  from_status?: string;
  to_status: string;
  remarks?: string;
  created_at: string;
}

export interface StaffLeaveRequest {
  id: string;
  school_id: string;
  teacher_id: string;
  teacher_name?: string;
  employee_id?: string;
  academic_year_id: string;
  academic_year_name?: string;
  leave_type_id: string;
  leave_type_code?: string;
  leave_type_name?: string;
  start_date: string;
  end_date: string;
  requested_days: number;
  half_day_type: string;
  reason: string;
  attachment_url?: string;
  status: string;
  requested_by_user_id?: string;
  requested_by_name?: string;
  approved_by_user_id?: string;
  approved_by_name?: string;
  rejected_by_user_id?: string;
  rejected_by_name?: string;
  cancelled_by_user_id?: string;
  approval_remarks?: string;
  rejection_reason?: string;
  approved_at?: string;
  rejected_at?: string;
  cancelled_at?: string;
  created_at: string;
  updated_at: string;
  approval_history: StaffLeaveApprovalHistory[];
}

export interface StaffLeaveSummaryReport {
  academic_year_id: string;
  total_requests: number;
  pending_requests: number;
  approved_today: number;
  currently_on_leave: number;
  by_leave_type: Record<string, number>;
  by_status: Record<string, number>;
}

export const staffLeaveApi = {
  getLeaveTypes: async (): Promise<StaffLeaveType[]> => {
    const res = await apiClient.get('/api/v1/staff-leave/types');
    return res.data.data;
  },

  createLeaveType: async (data: Partial<StaffLeaveType>): Promise<StaffLeaveType> => {
    const res = await apiClient.post('/api/v1/staff-leave/types', data);
    return res.data.data;
  },

  updateLeaveType: async (typeId: string, data: Partial<StaffLeaveType>): Promise<StaffLeaveType> => {
    const res = await apiClient.put(`/api/v1/staff-leave/types/${typeId}`, data);
    return res.data.data;
  },

  getMyBalances: async (academicYearId: string): Promise<StaffLeaveBalance[]> => {
    const res = await apiClient.get('/api/v1/staff-leave/balance', { params: { academic_year_id: academicYearId } });
    return res.data.data;
  },

  getTeacherBalances: async (teacherId: string, academicYearId: string): Promise<StaffLeaveBalance[]> => {
    const res = await apiClient.get(`/api/v1/staff-leave/balance/${teacherId}`, { params: { academic_year_id: academicYearId } });
    return res.data.data;
  },

  allocateBalance: async (data: { teacher_id: string; academic_year_id: string; leave_type_id: string; allocated_days: number }): Promise<StaffLeaveBalance> => {
    const res = await apiClient.post('/api/v1/staff-leave/balances/allocate', data);
    return res.data.data;
  },

  getLeaveRequests: async (params?: {
    teacher_id?: string;
    status?: string;
    leave_type_id?: string;
    start_date?: string;
    end_date?: string;
    academic_year_id?: string;
  }): Promise<StaffLeaveRequest[]> => {
    const res = await apiClient.get('/api/v1/staff-leave', { params });
    return res.data.data;
  },

  getLeaveRequestById: async (id: string): Promise<StaffLeaveRequest> => {
    const res = await apiClient.get(`/api/v1/staff-leave/${id}`);
    return res.data.data;
  },

  createLeaveRequest: async (data: {
    academic_year_id: string;
    leave_type_id: string;
    start_date: string;
    end_date: string;
    half_day_type?: string;
    reason: string;
    attachment_url?: string;
  }): Promise<StaffLeaveRequest> => {
    const res = await apiClient.post('/api/v1/staff-leave', data);
    return res.data.data;
  },

  approveLeaveRequest: async (id: string, remarks?: string): Promise<StaffLeaveRequest> => {
    const res = await apiClient.post(`/api/v1/staff-leave/${id}/approve`, { remarks });
    return res.data.data;
  },

  rejectLeaveRequest: async (id: string, rejection_reason: string): Promise<StaffLeaveRequest> => {
    const res = await apiClient.post(`/api/v1/staff-leave/${id}/reject`, { rejection_reason });
    return res.data.data;
  },

  cancelLeaveRequest: async (id: string, remarks?: string): Promise<StaffLeaveRequest> => {
    const res = await apiClient.post(`/api/v1/staff-leave/${id}/cancel`, { remarks });
    return res.data.data;
  },

  getSummaryReport: async (academicYearId: string): Promise<StaffLeaveSummaryReport> => {
    const res = await apiClient.get('/api/v1/staff-leave/reports/summary', { params: { academic_year_id: academicYearId } });
    return res.data.data;
  },
};
