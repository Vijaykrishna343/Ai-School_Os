import { apiClient } from './client';

export interface ImportResult {
  entity_type: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  inserted_rows: number;
  skipped_rows: number;
  errors: Array<{
    row_number: number;
    field: string | null;
    message: string;
  }>;
}

export interface ImportSchema {
  entity_type: string;
  required_columns: string[];
  optional_columns: string[];
  description: string;
}

export const importApi = {
  /**
   * Bulk import data from a CSV/XLSX file.
   */
  async importData(entityType: string, file: File): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<{ success: boolean; data: ImportResult }>(
      `/import/${entityType}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    // Handle API envelope
    const body = response as any;
    return body?.data || body;
  },

  /**
   * Get the CSV schema for a given entity type.
   */
  async getSchema(entityType: string): Promise<ImportSchema> {
    const response = await apiClient.get<ImportSchema>(`/import/schema/${entityType}`);
    return response as any;
  },
};

export const exportApi = {
  /**
   * Download a CSV export by opening a direct URL with auth token.
   */
  downloadCsv(endpoint: string, params?: Record<string, string>): void {
    const token = localStorage.getItem('access_token');
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : '';
    const url = `${baseUrl}/export/${endpoint}${queryString}`;

    // Create a temporary anchor element to trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = `${endpoint}_export.csv`;
    // Add auth header via fetch instead of anchor for security
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const objectUrl = URL.createObjectURL(blob);
        a.href = objectUrl;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objectUrl);
      })
      .catch(() => {
        // Fallback: open in new tab
        window.open(url, '_blank');
      });
  },
};

export interface NotificationItem {
  id: string;
  recipient_name: string;
  recipient_contact: string;
  channel: string;
  template_key: string;
  title: string;
  body: string;
  status: string;
  sent_at: string | null;
  created_at: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
}

export const notificationsApi = {
  async list(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    channel?: string;
  }): Promise<NotificationListResponse> {
    const response = await apiClient.get('/notifications', { params });
    const body = response as any;
    return body?.data || body;
  },

  async sendAnnouncement(payload: {
    title: string;
    message: string;
    recipient_name: string;
    recipient_contact: string;
    channel: string;
  }): Promise<{ id: string; status: string; title: string; channel: string }> {
    const response = await apiClient.post('/notifications/send', payload);
    const body = response as any;
    return body?.data || body;
  },

  async listTemplates(): Promise<Record<string, { title: string; body: string }>> {
    const response = await apiClient.get('/notifications/templates');
    const body = response as any;
    return body?.data || body;
  },
};

export interface AuditLogItem {
  id: string;
  timestamp: string | null;
  user_email: string;
  role_name: string | null;
  action: string;
  module: string;
  entity_type: string | null;
  entity_id: string | null;
  status_code: number;
  ip_address: string | null;
  details: string | null;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
}

export const auditLogsApi = {
  async list(params?: {
    page?: number;
    page_size?: number;
    user_email?: string;
    action?: string;
    module?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<AuditLogListResponse> {
    const response = await apiClient.get('/audit-logs', { params });
    const body = response as any;
    return body?.data || body;
  },
};
