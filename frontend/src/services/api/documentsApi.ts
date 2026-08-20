import { apiClient as client } from './client';
import { ApiResponse } from '@/types/api';

export interface DocumentItem {
  id: string;
  school_id: string;
  owner_type: 'STUDENT' | 'STAFF';
  owner_id: string;
  document_type: string;
  title: string;
  original_filename: string;
  storage_key: string;
  mime_type: string;
  file_size: number;
  checksum: string;
  status: 'UPLOADED' | 'VERIFIED' | 'REJECTED';
  uploaded_by_id: string;
  uploaded_at: string;
  verified_by_id?: string | null;
  verified_at?: string | null;
  rejection_reason?: string | null;
  version: number;
  is_current: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  owner_name?: string | null;
  uploaded_by_name?: string | null;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DocumentSummaryResponse {
  total_documents: number;
  uploaded_count: number;
  verified_count: number;
  rejected_count: number;
  student_documents_count: number;
  staff_documents_count: number;
}

export const documentsApi = {
  uploadDocument: async (formData: FormData): Promise<DocumentItem> => {
    const response = await client.post<ApiResponse<DocumentItem>>('/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.data!;
  },

  listDocuments: async (params?: {
    page?: number;
    page_size?: number;
    owner_type?: string;
    owner_id?: string;
    document_type?: string;
    status?: string;
  }): Promise<DocumentListResponse> => {
    const response = await client.get<ApiResponse<DocumentListResponse>>('/v1/documents', { params });
    return response.data.data!;
  },

  getDocumentSummary: async (): Promise<DocumentSummaryResponse> => {
    const response = await client.get<ApiResponse<DocumentSummaryResponse>>('/v1/documents/summary');
    return response.data.data!;
  },

  getDocument: async (id: string): Promise<DocumentItem> => {
    const response = await client.get<ApiResponse<DocumentItem>>(`/v1/documents/${id}`);
    return response.data.data!;
  },

  downloadDocument: async (id: string, filename: string): Promise<void> => {
    const response = await client.get(`/v1/documents/${id}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  getPreviewUrl: (id: string): string => {
    const token = localStorage.getItem('access_token');
    return `/api/v1/documents/${id}/preview?token=${token}`;
  },

  updateDocument: async (id: string, payload: { title?: string; document_type?: string }): Promise<DocumentItem> => {
    const response = await client.put<ApiResponse<DocumentItem>>(`/v1/documents/${id}`, payload);
    return response.data.data!;
  },

  replaceDocument: async (id: string, formData: FormData): Promise<DocumentItem> => {
    const response = await client.post<ApiResponse<DocumentItem>>(`/v1/documents/${id}/replace`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.data!;
  },

  verifyDocument: async (id: string): Promise<DocumentItem> => {
    const response = await client.post<ApiResponse<DocumentItem>>(`/v1/documents/${id}/verify`);
    return response.data.data!;
  },

  rejectDocument: async (id: string, payload: { rejection_reason: string }): Promise<DocumentItem> => {
    const response = await client.post<ApiResponse<DocumentItem>>(`/v1/documents/${id}/reject`, payload);
    return response.data.data!;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await client.delete(`/v1/documents/${id}`);
  },
};
