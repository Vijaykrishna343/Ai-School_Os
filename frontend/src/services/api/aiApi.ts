import { apiClient } from './client';
import type {
  AssistantChatRequest,
  AssistantChatResponse,
  AssistantToolDefinition,
  AIUsageStats,
  AIProviderConfig,
  AIProviderConfigUpdate,
  AIUsageLimitUpdate,
  AIAuditLogQueryResponse,
} from '../../api/ai';

export const aiApi = {
  chat: async (payload: AssistantChatRequest): Promise<AssistantChatResponse> => {
    const res = await apiClient.post<AssistantChatResponse>('/ai/assistant/chat', payload);
    return res.data;
  },

  listTools: async (): Promise<AssistantToolDefinition[]> => {
    const res = await apiClient.get<AssistantToolDefinition[]>('/ai/assistant/tools');
    return res.data;
  },

  getUsageStats: async (): Promise<AIUsageStats> => {
    const res = await apiClient.get<AIUsageStats>('/ai/usage/stats');
    return res.data;
  },

  getProviderConfig: async (): Promise<AIProviderConfig> => {
    const res = await apiClient.get<AIProviderConfig>('/ai/admin/provider-config');
    return res.data;
  },

  updateProviderConfig: async (payload: AIProviderConfigUpdate): Promise<AIProviderConfig> => {
    const res = await apiClient.put<AIProviderConfig>('/ai/admin/provider-config', payload);
    return res.data;
  },

  updateUsageLimit: async (payload: AIUsageLimitUpdate): Promise<AIUsageStats> => {
    const res = await apiClient.put<AIUsageStats>('/ai/admin/usage-limit', payload);
    return res.data;
  },

  getAuditLogs: async (params?: {
    capability?: string;
    status?: string;
    provider_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<AIAuditLogQueryResponse> => {
    const res = await apiClient.get<AIAuditLogQueryResponse>('/ai/admin/audit-logs', { params });
    return res.data;
  },
};
