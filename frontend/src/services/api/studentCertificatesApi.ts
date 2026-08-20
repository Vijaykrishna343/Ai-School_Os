import { apiClient } from './client';

export interface StudentCertificateItem {
  id: string;
  school_id: string;
  student_id: string;
  student_name?: string;
  admission_number?: string;
  roll_number?: string;
  school_class_name?: string;
  section_name?: string;
  parent_name?: string;
  certificate_type: 'TC' | 'BONAFIDE';
  certificate_number: string;
  issued_date: string;
  purpose?: string | null;
  reason_for_leaving?: string | null;
  conduct?: string | null;
  issued_by_name?: string | null;
}

export interface StudentCertificateListResponse {
  items: StudentCertificateItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const studentCertificatesApi = {
  issueTC: async (studentId: string, payload: { reason_for_leaving: string; conduct?: string; update_student_status?: boolean }): Promise<StudentCertificateItem> => {
    const res = await apiClient.post(`/students/${studentId}/certificates/tc`, payload);
    return res.data.data;
  },

  issueBonafide: async (studentId: string, payload: { purpose: string; conduct?: string }): Promise<StudentCertificateItem> => {
    const res = await apiClient.post(`/students/${studentId}/certificates/bonafide`, payload);
    return res.data.data;
  },

  list: async (type?: string, studentId?: string, page = 1): Promise<StudentCertificateListResponse> => {
    const params: Record<string, any> = { page };
    if (type) params.type = type;
    if (studentId) params.student_id = studentId;
    const res = await apiClient.get('/certificates', { params });
    return res.data.data;
  },

  getPrintViewUrl: (certificateId: string): string => {
    return `/api/v1/certificates/${certificateId}/print`;
  },
};
