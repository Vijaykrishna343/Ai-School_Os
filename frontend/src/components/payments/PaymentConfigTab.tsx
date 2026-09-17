import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentsApi, PaymentConfigUpdatePayload } from '@/services/api/paymentsApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

interface PaymentConfigTabProps {
  canEdit: boolean;
}

export const PaymentConfigTab: React.FC<PaymentConfigTabProps> = ({ canEdit }) => {
  const queryClient = useQueryClient();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form states (write-only secrets)
  const [razorpayKeyId, setRazorpayKeyId] = useState('');
  const [razorpayKeySecret, setRazorpayKeySecret] = useState('');
  const [razorpayWebhookSecret, setRazorpayWebhookSecret] = useState('');

  const [stripePublishableKey, setStripePublishableKey] = useState('');
  const [stripeSecretKey, setStripeSecretKey] = useState('');
  const [stripeWebhookSecret, setStripeWebhookSecret] = useState('');

  const { data: config, isLoading, isError, refetch } = useQuery({
    queryKey: ['paymentConfig'],
    queryFn: async () => {
      const res = await paymentsApi.getConfig();
      if (res) {
        setRazorpayKeyId(res.razorpay_key_id || '');
        setStripePublishableKey(res.stripe_publishable_key || '');
      }
      return res;
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: PaymentConfigUpdatePayload) => paymentsApi.updateConfig(payload),
    onSuccess: (updated) => {
      setSuccessMessage('Payment gateway provider settings updated successfully.');
      setErrorMessage(null);
      setRazorpayKeySecret('');
      setRazorpayWebhookSecret('');
      setStripeSecretKey('');
      setStripeWebhookSecret('');
      queryClient.setQueryData(['paymentConfig'], updated);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || 'Failed to update payment gateway credentials.');
      setSuccessMessage(null);
    },
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;

    const payload: PaymentConfigUpdatePayload = {};
    if (razorpayKeyId !== (config?.razorpay_key_id || '')) {
      payload.razorpay_key_id = razorpayKeyId;
    }
    if (razorpayKeySecret.trim()) {
      payload.razorpay_key_secret = razorpayKeySecret.trim();
    }
    if (razorpayWebhookSecret.trim()) {
      payload.razorpay_webhook_secret = razorpayWebhookSecret.trim();
    }

    if (stripePublishableKey !== (config?.stripe_publishable_key || '')) {
      payload.stripe_publishable_key = stripePublishableKey;
    }
    if (stripeSecretKey.trim()) {
      payload.stripe_secret_key = stripeSecretKey.trim();
    }
    if (stripeWebhookSecret.trim()) {
      payload.stripe_webhook_secret = stripeWebhookSecret.trim();
    }

    updateMutation.mutate(payload);
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center bg-white border border-slate-200">
        <p className="text-xs font-mono text-slate-400">Loading payment gateway provider configuration...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
          <div>
            <h2 className="text-lg font-bold font-serif text-slate-800">
              Live Payment Gateway & Webhook Settings
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Configure production payment adapters and cryptographic webhook secrets. Secrets are encrypted at rest with write-only masking.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400 uppercase">Provider Status:</span>
            {config?.razorpay_enabled ? (
              <Badge variant="success">Razorpay Active</Badge>
            ) : (
              <Badge variant="default">Razorpay Inactive</Badge>
            )}
            {config?.stripe_enabled ? (
              <Badge variant="success">Stripe Active</Badge>
            ) : (
              <Badge variant="default">Stripe Inactive</Badge>
            )}
          </div>
        </div>

        {successMessage && <Alert type="success">{successMessage}</Alert>}
        {errorMessage && <Alert type="error" title="Configuration Error">{errorMessage}</Alert>}

        <form onSubmit={handleSave} className="space-y-8">
          {/* Razorpay Section */}
          <div className="border border-slate-200 rounded p-5 bg-slate-50/50 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-slate-800">Razorpay Gateway</span>
                {config?.razorpay_enabled ? (
                  <Badge variant="success">CONFIGURED</Badge>
                ) : (
                  <Badge variant="warning">NOT CONFIGURED</Badge>
                )}
              </div>
              <span className="text-[11px] font-mono text-slate-400">HMAC-SHA256 Signed</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Razorpay Key ID
                </label>
                <Input
                  value={razorpayKeyId}
                  onChange={(e) => setRazorpayKeyId(e.target.value)}
                  placeholder="rzp_live_..."
                  disabled={!canEdit}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Razorpay Key Secret (Write-Only)
                </label>
                <Input
                  type="password"
                  value={razorpayKeySecret}
                  onChange={(e) => setRazorpayKeySecret(e.target.value)}
                  placeholder={config?.razorpay_key_secret_masked || 'Enter new secret to update'}
                  disabled={!canEdit}
                />
                {config?.razorpay_key_secret_masked && (
                  <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                    Current masked: {config.razorpay_key_secret_masked}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Razorpay Webhook Secret (Write-Only)
                </label>
                <Input
                  type="password"
                  value={razorpayWebhookSecret}
                  onChange={(e) => setRazorpayWebhookSecret(e.target.value)}
                  placeholder={config?.razorpay_webhook_secret_masked || 'Enter webhook signing secret'}
                  disabled={!canEdit}
                />
                {config?.razorpay_webhook_secret_masked && (
                  <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                    Current masked: {config.razorpay_webhook_secret_masked}
                  </span>
                )}
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Webhook Endpoint URL
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    readOnly
                    value={config?.razorpay_webhook_url || '/api/v1/payments/webhooks/razorpay'}
                    className="bg-slate-100 font-mono text-xs text-slate-600"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      navigator.clipboard?.writeText(
                        `${window.location.origin}${config?.razorpay_webhook_url || '/api/v1/payments/webhooks/razorpay'}`
                      );
                    }}
                  >
                    Copy
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Stripe Section */}
          <div className="border border-slate-200 rounded p-5 bg-slate-50/50 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-slate-800">Stripe Gateway</span>
                {config?.stripe_enabled ? (
                  <Badge variant="success">CONFIGURED</Badge>
                ) : (
                  <Badge variant="warning">NOT CONFIGURED</Badge>
                )}
              </div>
              <span className="text-[11px] font-mono text-slate-400">Timestamped HMAC-SHA256</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Stripe Publishable Key
                </label>
                <Input
                  value={stripePublishableKey}
                  onChange={(e) => setStripePublishableKey(e.target.value)}
                  placeholder="pk_live_..."
                  disabled={!canEdit}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Stripe Secret Key (Write-Only)
                </label>
                <Input
                  type="password"
                  value={stripeSecretKey}
                  onChange={(e) => setStripeSecretKey(e.target.value)}
                  placeholder={config?.stripe_secret_key_masked || 'Enter new secret key to update'}
                  disabled={!canEdit}
                />
                {config?.stripe_secret_key_masked && (
                  <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                    Current masked: {config.stripe_secret_key_masked}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Stripe Webhook Signing Secret (Write-Only)
                </label>
                <Input
                  type="password"
                  value={stripeWebhookSecret}
                  onChange={(e) => setStripeWebhookSecret(e.target.value)}
                  placeholder={config?.stripe_webhook_secret_masked || 'whsec_...'}
                  disabled={!canEdit}
                />
                {config?.stripe_webhook_secret_masked && (
                  <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                    Current masked: {config.stripe_webhook_secret_masked}
                  </span>
                )}
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Webhook Endpoint URL
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    readOnly
                    value={config?.stripe_webhook_url || '/api/v1/payments/webhooks/stripe'}
                    className="bg-slate-100 font-mono text-xs text-slate-600"
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      navigator.clipboard?.writeText(
                        `${window.location.origin}${config?.stripe_webhook_url || '/api/v1/payments/webhooks/stripe'}`
                      );
                    }}
                  >
                    Copy
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {canEdit && (
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <Button
                type="submit"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? 'Saving Settings...' : 'Save Payment Configuration'}
              </Button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
