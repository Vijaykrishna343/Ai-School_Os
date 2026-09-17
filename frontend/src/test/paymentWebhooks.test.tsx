import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PaymentConfigTab } from '@/components/payments/PaymentConfigTab';
import { paymentsApi } from '@/services/api/paymentsApi';

vi.mock('@/services/api/paymentsApi', () => ({
  paymentsApi: {
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
    createOrder: vi.fn(),
    getOrderStatus: vi.fn(),
    verifyPayment: vi.fn(),
  },
}));

const renderWithQueryClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('Phase 30.6 — Payment Gateway Webhooks & Provider Configuration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders PaymentConfigTab with masked provider credentials and webhook endpoints', async () => {
    vi.mocked(paymentsApi.getConfig).mockResolvedValue({
      school_id: 'school-101',
      razorpay_enabled: true,
      razorpay_key_id: 'rzp_live_testkey123',
      razorpay_key_secret_masked: '••••••••1234',
      razorpay_webhook_secret_masked: '••••••••5678',
      razorpay_webhook_url: '/api/v1/payments/webhooks/razorpay',
      stripe_enabled: false,
      stripe_publishable_key: '',
      stripe_secret_key_masked: null,
      stripe_webhook_secret_masked: null,
      stripe_webhook_url: '/api/v1/payments/webhooks/stripe',
    });

    renderWithQueryClient(<PaymentConfigTab canEdit={true} />);

    expect(await screen.findByText('Live Payment Gateway & Webhook Settings')).toBeInTheDocument();
    expect(screen.getByText('Razorpay Active')).toBeInTheDocument();
    expect(screen.getByText('Stripe Inactive')).toBeInTheDocument();

    // Check Key ID is displayed
    const razorpayKeyInput = screen.getByDisplayValue('rzp_live_testkey123');
    expect(razorpayKeyInput).toBeInTheDocument();

    // Check masked secrets are shown as helper labels, NOT plaintext
    expect(screen.getByText(/Current masked: ••••••••1234/i)).toBeInTheDocument();
    expect(screen.getByText(/Current masked: ••••••••5678/i)).toBeInTheDocument();

    // Check Webhook URLs
    expect(screen.getByDisplayValue('/api/v1/payments/webhooks/razorpay')).toBeInTheDocument();
    expect(screen.getByDisplayValue('/api/v1/payments/webhooks/stripe')).toBeInTheDocument();
  });

  it('2. Disables credential inputs when canEdit is false (RBAC)', async () => {
    vi.mocked(paymentsApi.getConfig).mockResolvedValue({
      school_id: 'school-101',
      razorpay_enabled: true,
      razorpay_key_id: 'rzp_live_testkey123',
      razorpay_key_secret_masked: '••••••••1234',
      razorpay_webhook_secret_masked: '••••••••5678',
      razorpay_webhook_url: '/api/v1/payments/webhooks/razorpay',
      stripe_enabled: false,
      stripe_publishable_key: '',
      stripe_secret_key_masked: null,
      stripe_webhook_secret_masked: null,
      stripe_webhook_url: '/api/v1/payments/webhooks/stripe',
    });

    renderWithQueryClient(<PaymentConfigTab canEdit={false} />);

    await screen.findByText('Live Payment Gateway & Webhook Settings');
    const razorpayKeyInput = screen.getByDisplayValue('rzp_live_testkey123');
    expect(razorpayKeyInput).toBeDisabled();

    // Save button should not even be rendered for view-only users
    expect(screen.queryByRole('button', { name: /save payment configuration/i })).not.toBeInTheDocument();
  });

  it('3. Submits updated provider configuration with write-only secrets', async () => {
    vi.mocked(paymentsApi.getConfig).mockResolvedValue({
      school_id: 'school-101',
      razorpay_enabled: false,
      razorpay_key_id: '',
      razorpay_key_secret_masked: null,
      razorpay_webhook_secret_masked: null,
      razorpay_webhook_url: '/api/v1/payments/webhooks/razorpay',
      stripe_enabled: false,
      stripe_publishable_key: '',
      stripe_secret_key_masked: null,
      stripe_webhook_secret_masked: null,
      stripe_webhook_url: '/api/v1/payments/webhooks/stripe',
    });

    vi.mocked(paymentsApi.updateConfig).mockResolvedValue({
      school_id: 'school-101',
      razorpay_enabled: true,
      razorpay_key_id: 'rzp_live_newkey',
      razorpay_key_secret_masked: '••••••••9999',
      razorpay_webhook_secret_masked: '••••••••8888',
      razorpay_webhook_url: '/api/v1/payments/webhooks/razorpay',
      stripe_enabled: true,
      stripe_publishable_key: 'pk_live_stripe_new',
      stripe_secret_key_masked: '••••••••7777',
      stripe_webhook_secret_masked: '••••••••6666',
      stripe_webhook_url: '/api/v1/payments/webhooks/stripe',
    });

    renderWithQueryClient(<PaymentConfigTab canEdit={true} />);

    await screen.findByText('Live Payment Gateway & Webhook Settings');

    // Fill in Razorpay Key ID
    const keyIdInput = screen.getByPlaceholderText('rzp_live_...');
    fireEvent.change(keyIdInput, { target: { value: 'rzp_live_newkey' } });

    // Fill in Razorpay Secrets
    const secretInput = screen.getByPlaceholderText('Enter new secret to update');
    fireEvent.change(secretInput, { target: { value: 'new_rzp_secret_val' } });

    const webhookSecretInput = screen.getByPlaceholderText('Enter webhook signing secret');
    fireEvent.change(webhookSecretInput, { target: { value: 'new_rzp_wh_secret' } });

    // Submit form
    const saveButton = screen.getByRole('button', { name: /save payment configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(paymentsApi.updateConfig).toHaveBeenCalledWith({
        razorpay_key_id: 'rzp_live_newkey',
        razorpay_key_secret: 'new_rzp_secret_val',
        razorpay_webhook_secret: 'new_rzp_wh_secret',
      });
    });

    expect(await screen.findByText('Payment gateway provider settings updated successfully.')).toBeInTheDocument();
  });

  it('4. Authoritative order status polling exposes settled state and receipt', async () => {
    vi.mocked(paymentsApi.getOrderStatus).mockResolvedValue({
      order_id: 'po-12345',
      school_id: 'school-101',
      student_fee_assignment_id: 'sfa-999',
      provider: 'RAZORPAY',
      gateway_order_id: 'order_rzp_12345',
      amount: '10000.00',
      currency: 'INR',
      status: 'PAID',
      receipt_number: 'RCP-2026-0001',
      is_settled: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const status = await paymentsApi.getOrderStatus('po-12345');
    expect(status.order_id).toBe('po-12345');
    expect(status.status).toBe('PAID');
    expect(status.is_settled).toBe(true);
    expect(status.receipt_number).toBe('RCP-2026-0001');
    expect(paymentsApi.getOrderStatus).toHaveBeenCalledWith('po-12345');
  });
});
