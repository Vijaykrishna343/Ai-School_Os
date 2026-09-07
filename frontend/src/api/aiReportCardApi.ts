import { apiClient } from '@/services/api/client';

export interface GenerateReportCardRemarksRequest {
  report_card_id: string;
  tone?: 'ENCOURAGING' | 'CONSTRUCTIVE' | 'FORMAL' | 'CELEBRATORY';
  detail_level?: 'BRIEF' | 'STANDARD' | 'DETAILED';
}

export interface ApplyReportCardRemarksRequest {
  report_card_id: string;
  teacher_remarks: string;
  principal_remarks: string;
}

export interface ReportCardRemarksResponse {
  id: string;
  report_card_id: string;
  student_id: string;
  tone: string;
  detail_level: string;
  teacher_remarks_draft: string;
  principal_remarks_draft: string;
  action_items: string[];
  strength_subjects: string[];
  focus_subjects: string[];
  token_count: number;
  status: string;
  assessed_at: string;
}

export const aiReportCardApi = {
  generateRemarks: async (req: GenerateReportCardRemarksRequest): Promise<ReportCardRemarksResponse> => {
    const res = await apiClient.post<ReportCardRemarksResponse>('/api/v1/ai/report-card/remarks/generate', req);
    return res.data;
  },

  applyRemarks: async (req: ApplyReportCardRemarksRequest) => {
    const res = await apiClient.post('/api/v1/ai/report-card/remarks/apply', req);
    return res.data;
  },

  getRemarks: async (reportCardId: string): Promise<ReportCardRemarksResponse> => {
    const res = await apiClient.get<ReportCardRemarksResponse>(`/api/v1/ai/report-card/remarks/${reportCardId}`);
    return res.data;
  },
};
