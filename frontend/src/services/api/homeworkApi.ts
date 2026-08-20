import { apiClient } from './client';

export interface HomeworkItem {
  id: string;
  school_id: string;
  teacher_id: string;
  school_class_id: string;
  section_id?: string | null;
  subject_id: string;
  title: string;
  description: string;
  assigned_date: string;
  due_date: string;
  status: 'DRAFT' | 'PUBLISHED' | 'CLOSED';
  published_at?: string | null;
  created_at: string;
  updated_at: string;

  teacher_name?: string;
  school_class_name?: string;
  section_name?: string;
  subject_name?: string;
  submission_count?: number;
}

export interface HomeworkSummary {
  total_homework: number;
  draft_count: number;
  published_count: number;
  due_soon_count: number;
  closed_count: number;
}

export interface HomeworkListResponse {
  items: HomeworkItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HomeworkCreatePayload {
  teacher_id?: string;
  school_class_id: string;
  section_id?: string;
  subject_id: string;
  title: string;
  description: string;
  assigned_date?: string;
  due_date: string;
}

export interface HomeworkUpdatePayload {
  title?: string;
  description?: string;
  due_date?: string;
  status?: 'DRAFT' | 'PUBLISHED' | 'CLOSED';
}

export interface HomeworkSubmissionItem {
  id: string;
  school_id: string;
  homework_id: string;
  student_id: string;
  submitted_at: string;
  status: 'SUBMITTED' | 'RESUBMITTED' | 'REVIEWED' | 'GRADED' | 'LATE';
  content_text: string;
  grade?: string | null;
  feedback?: string | null;
  reviewed_at?: string | null;
  reviewed_by_id?: string | null;
  created_at: string;
  updated_at: string;

  student_name?: string;
  admission_number?: string;
  homework_title?: string;
  subject_name?: string;
}

export interface HomeworkSubmissionListResponse {
  items: HomeworkSubmissionItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const homeworkApi = {
  create: async (payload: HomeworkCreatePayload): Promise<HomeworkItem> => {
    const res = await apiClient.post('/homework', payload);
    return res.data.data;
  },

  list: async (params?: {
    page?: number;
    page_size?: number;
    school_class_id?: string;
    section_id?: string;
    subject_id?: string;
    status?: string;
    teacher_id?: string;
    student_id?: string;
  }): Promise<HomeworkListResponse> => {
    const res = await apiClient.get('/homework', { params });
    return res.data.data;
  },

  getSummary: async (teacherId?: string): Promise<HomeworkSummary> => {
    const params = teacherId ? { teacher_id: teacherId } : {};
    const res = await apiClient.get('/homework/summary', { params });
    return res.data.data;
  },

  getById: async (id: string): Promise<HomeworkItem> => {
    const res = await apiClient.get(`/homework/${id}`);
    return res.data.data;
  },

  update: async (id: string, payload: HomeworkUpdatePayload): Promise<HomeworkItem> => {
    const res = await apiClient.put(`/homework/${id}`, payload);
    return res.data.data;
  },

  publish: async (id: string): Promise<HomeworkItem> => {
    const res = await apiClient.post(`/homework/${id}/publish`);
    return res.data.data;
  },

  close: async (id: string): Promise<HomeworkItem> => {
    const res = await apiClient.post(`/homework/${id}/close`);
    return res.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/homework/${id}`);
  },

  submitWork: async (homeworkId: string, contentText: string): Promise<HomeworkSubmissionItem> => {
    const res = await apiClient.post(`/homework/${homeworkId}/submit`, { content_text: contentText });
    return res.data.data;
  },

  listSubmissions: async (homeworkId: string, page = 1): Promise<HomeworkSubmissionListResponse> => {
    const res = await apiClient.get(`/homework/${homeworkId}/submissions`, { params: { page } });
    return res.data.data;
  },

  gradeSubmission: async (
    submissionId: string,
    payload: { grade: string; feedback?: string }
  ): Promise<HomeworkSubmissionItem> => {
    const res = await apiClient.post(`/homework/submissions/${submissionId}/grade`, payload);
    return res.data.data;
  },
};
