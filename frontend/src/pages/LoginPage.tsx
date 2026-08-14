import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, Lock, Mail, ShieldAlert } from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';

export const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, authError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const from = (location.state as any)?.from?.pathname || '/app/dashboard';

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!password) {
      errors.password = 'Password is required.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch {
      // Error is caught and stored in authError state
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#fcf9f8] sm:p-6 lg:p-8 select-none">
      <div className="w-full max-w-sm space-y-8 bg-white dark:bg-slate-900 p-8 sm:p-10 rounded-sm border border-slate-200 dark:border-slate-800">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-sm bg-brand-500 text-white mb-2">
            <Building2 className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold font-serif tracking-tight text-brand-500 dark:text-slate-100">
            AI School OS
          </h2>
          <p className="text-xs font-mono uppercase tracking-wider text-slate-400">
            ENTERPRISE_SYSTEM_LOGIN
          </p>
        </div>

        {/* Global Error Banner */}
        {authError && (
          <Alert type="error" title="Authentication Error">
            {authError}
          </Alert>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <Input
            label="Email Address"
            type="email"
            placeholder="admin@school.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={fieldErrors.email}
            leftIcon={<Mail className="w-4 h-4" />}
            autoComplete="email"
            autoFocus
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fieldErrors.password}
            leftIcon={<Lock className="w-4 h-4" />}
            autoComplete="current-password"
            required
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full py-2.5 mt-2 font-semibold text-xs tracking-wider"
          >
            SIGN IN TO PORTAL
          </Button>
        </form>

        {/* Footer Notice */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-center font-mono">
          <p className="text-[10px] text-slate-400 flex items-center justify-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" />
            SECURITY_SYSTEM_ACTIVE_RBAC
          </p>
        </div>
      </div>
    </div>
  );
};
