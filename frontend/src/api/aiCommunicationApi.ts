import { apiClient } from '@/services/api/client';

export interface ChannelVariant {
  title: string;
  body: string;
}

export interface GenerateCommunicationDraftRequest {
  category: string;
  target_audience: string;
  tone: string;
  key_details: string;
  requested_channels?: string[];
}

export interface CommunicationDraftResponse {
  id: string;
  school_id: string;
  created_by_user_id?: string;
  category: string;
  target_audience: string;
  tone: string;
  prompt_summary: string;
  channel_variants: Record<string, ChannelVariant>;
  pii_redact_log: string[];
  token_count: number;
  status: string;
  assessed_at: string;
  created_at: string;
}

export interface CommunicationDraftListResponse {
  total: number;
  drafts: CommunicationDraftResponse[];
}

export const generateCommunicationDraft = async (
  payload: GenerateCommunicationDraftRequest
): Promise<CommunicationDraftResponse> => {
  const response = await apiClient.post<CommunicationDraftResponse>('/api/v1/ai/communication/draft', payload);
  return response.data;
};

export const getCommunicationDrafts = async (
  category?: string,
  limit = 20,
  offset = 0
): Promise<CommunicationDraftListResponse> => {
  const response = await apiClient.get<CommunicationDraftListResponse>('/api/v1/ai/communication/drafts', {
    params: { category, limit, offset },
  });
  return response.data;
};

export const getCommunicationDraftById = async (
  draftId: string
): Promise<CommunicationDraftResponse> => {
  const response = await apiClient.get<CommunicationDraftResponse>(`/api/v1/ai/communication/draft/${draftId}`);
  return response.data;
};
