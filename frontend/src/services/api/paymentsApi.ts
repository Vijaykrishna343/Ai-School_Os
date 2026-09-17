import { apiClient } from './client';

export type PaymentProviderType = 'RAZORPAY' | 'STRIPE' | 'MOCK';
export type PaymentOrderStatusType = 'CREATED' | 'ATTEMPTED' | 'PAID' | 'FAILED' | 'EXPIRED' | 'CANCELLED';

export interface CreatePaymentOrderPayload {
  student_fee_assignment_id: string;
  provider?: PaymentProviderType;
}

export interface PaymentOrder {
  id: string;
  school_id: string;
  student_fee_assignment_id: string;
  provider: PaymentProviderType;
  gateway_order_id: string;
  amount: number | string;
  currency: string;
  status: PaymentOrderStatusType;
  expires_at?: string | null;
  extra_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentOrderStatus {
  order_id: string;
  school_id: string;
  student_fee_assignment_id: string;
  provider: PaymentProviderType;
  gateway_order_id: string;
  amount: number | string;
  currency: string;
  status: PaymentOrderStatusType;
  receipt_number?: string | null;
  is_settled: boolean;
  created_at: string;
  updated_at: string;
}

export interface VerifyPaymentPayload {
  provider: PaymentProviderType;
  payment_order_id: string;
  gateway_order_id: string;
  gateway_payment_id: string;
  gateway_signature: string;
  amount?: number | string;
  currency?: string;
}

export interface VerifyPaymentResult {
  success: boolean;
  message: string;
  order_id: string;
  status: PaymentOrderStatusType;
  gateway_transaction_id?: string | null;
  amount: number | string;
  currency: string;
}

export interface PaymentConfigResponse {
  school_id?: string | null;
  razorpay_enabled: boolean;
  razorpay_key_id: string;
  razorpay_key_secret_masked?: string | null;
  razorpay_webhook_secret_masked?: string | null;
  razorpay_webhook_url: string;
  stripe_enabled: boolean;
  stripe_publishable_key: string;
  stripe_secret_key_masked?: string | null;
  stripe_webhook_secret_masked?: string | null;
  stripe_webhook_url: string;
}

export interface PaymentConfigUpdatePayload {
  razorpay_key_id?: string;
  razorpay_key_secret?: string;
  razorpay_webhook_secret?: string;
  stripe_publishable_key?: string;
  stripe_secret_key?: string;
  stripe_webhook_secret?: string;
}

export const paymentsApi = {
  createOrder: async (payload: CreatePaymentOrderPayload): Promise<PaymentOrder> => {
    return await apiClient.post('/payments/orders', payload);
  },

  getOrderStatus: async (orderId: string): Promise<PaymentOrderStatus> => {
    return await apiClient.get(`/payments/orders/${orderId}`);
  },

  verifyPayment: async (payload: VerifyPaymentPayload): Promise<VerifyPaymentResult> => {
    return await apiClient.post('/payments/verify', payload);
  },

  getConfig: async (): Promise<PaymentConfigResponse> => {
    return await apiClient.get('/payments/config');
  },

  updateConfig: async (payload: PaymentConfigUpdatePayload): Promise<PaymentConfigResponse> => {
    return await apiClient.put('/payments/config', payload);
  },
};
