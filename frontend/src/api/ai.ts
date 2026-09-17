export interface AssistantChatRequest {
  message: string;
  context?: Record<string, unknown>;
}

export interface AssistantChatResponse {
  reply: string;
  tool_invoked?: string | null;
  tool_args?: Record<string, unknown> | null;
  tokens_used: number;
  latency_ms: number;
  redacted_fields: string[];
}

export interface AssistantToolDefinition {
  name: string;
  description: string;
  required_permission: string;
  parameters: Record<string, unknown>;
}

export interface AIUsageStats {
  school_id: string;
  monthly_token_quota: number;
  used_tokens_current_month: number;
  quota_remaining: number;
  quota_reset_date: string;
  is_enabled: boolean;
}

export interface AIProviderConfig {
  id: string;
  school_id: string | null;
  provider_type: string;
  model_name: string | null;
  is_enabled: boolean;
  allow_external_ai: boolean;
  api_key_configured?: boolean;
  masked_api_key?: string | null;
  api_base_url?: string | null;
  notes: string | null;
  updated_at: string;
}

export interface AIProviderConfigUpdate {
  provider_type: string;
  model_name?: string | null;
  is_enabled: boolean;
  allow_external_ai: boolean;
  api_key?: string | null;
  api_base_url?: string | null;
  notes?: string | null;
}

export interface AIUsageLimitUpdate {
  monthly_token_quota: number;
  is_enabled: boolean;
}

export interface AIAuditLogItem {
  id: string;
  school_id: string;
  user_id: string;
  user_full_name: string;
  capability: string;
  provider_type: string;
  model_name: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface AIAuditLogQueryResponse {
  total_count: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost_usd: number;
  items: AIAuditLogItem[];
}
