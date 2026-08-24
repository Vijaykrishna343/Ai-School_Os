import { apiClient } from './client';

export interface JobStatusResponse {
  id: string;
  school_id: string;
  created_by_user_id: string;
  job_type: 'BATCH_REPORT_CARD_GEN' | 'BULK_NOTIFICATION_DISPATCH' | 'BULK_STUDENT_IMPORT';
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress_percentage: number;
  processed_items: number;
  total_items: number;
  payload: Record<string, any>;
  result?: Record<string, any> | null;
  error_message?: string | null;
  idempotency_key?: string | null;
  retry_count: number;
  max_retries: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export const jobsApi = {
  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const res = await apiClient.get<{ success: boolean; data: JobStatusResponse }>(`/jobs/${jobId}`);
    const body = res as any;
    return body?.data || body;
  },

  retryJob: async (jobId: string): Promise<JobStatusResponse> => {
    const res = await apiClient.post<{ success: boolean; data: JobStatusResponse }>(`/jobs/${jobId}/retry`);
    const body = res as any;
    return body?.data || body;
  },

  cancelJob: async (jobId: string): Promise<JobStatusResponse> => {
    const res = await apiClient.post<{ success: boolean; data: JobStatusResponse }>(`/jobs/${jobId}/cancel`);
    const body = res as any;
    return body?.data || body;
  },
};
