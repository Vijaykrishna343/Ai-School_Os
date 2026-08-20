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

  const [schoolCode, setSchoolCode] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{
    schoolCode?: string;
    email?: string;
    password?: string;
  }>({});

  const from = (location.state as any)?.from?.pathname || '/app/dashboard';

  const validate = () => {
    const errors: { schoolCode?: string; email?: string; password?: string } = {};

    if (!schoolCode.trim()) {
      errors.schoolCode = 'School code is required.';
    }
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
      await login({
        school_code: schoolCode.trim().toUpperCase(),
        email: email.trim(),
        password,
      });
      navigate(from, { replace: true });
    } catch {
      // Error is caught and stored in authError state
    }
  };

  return (
    <div className="min-h-screen w-full bg-paper dark:bg-stone-950 flex flex-col md:flex-row select-none">
      {/* Left Column: Scholarly / Editorial identity branding */}
      <div className="w-full md:w-1/2 flex flex-col justify-between p-8 md:p-16 bg-paper-dim dark:bg-stone-900/60 border-b md:border-b-0 md:border-r border-divider dark:border-stone-800 shrink-0">
        {/* Top Brand Block */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 bg-brand-500 text-white shrink-0">
              <Building2 className="w-4 h-4" />
            </div>
            <span className="font-mono text-xs uppercase tracking-widest text-ink-muted/80 dark:text-stone-400">
              Academic OS
            </span>
          </div>

          <div className="space-y-3 pt-6 md:pt-12">
            <h1 className="text-4xl md:text-5xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-tight">
              AI School OS
            </h1>
            <p className="font-serif italic text-sm md:text-base text-ink-muted dark:text-stone-400 max-w-sm">
              Unified administration, academic progression registry, and multi-tenant operational control core.
            </p>
          </div>
        </div>

        {/* Bottom Institutional Metadata (docket style) */}
        <div className="mt-12 md:mt-0 pt-8 border-t border-divider/60 dark:border-stone-800 space-y-4">
          <div className="grid grid-cols-2 gap-x-8 gap-y-4 max-w-md">
            <div>
              <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/50">SYSTEM DESIGNATION</span>
              <span className="text-[11px] font-mono font-medium text-ink dark:text-stone-300">REGISTRAR_PORTAL_01</span>
            </div>
            <div>
              <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/50">SECURITY PROTOCOL</span>
              <span className="text-[11px] font-mono font-medium text-ink dark:text-stone-300">RBAC_ACTIVE</span>
            </div>
            <div>
              <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/50">TENANT ISOLATION</span>
              <span className="text-[11px] font-mono font-medium text-ink dark:text-stone-300">ISOLATED_SANDBOX</span>
            </div>
            <div>
              <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/50">VERSION CONTROL</span>
              <span className="text-[11px] font-mono font-medium text-ink dark:text-stone-300">v1.0.0_STABLE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Portal Gateway Form */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-8 md:p-16">
        <div className="w-full max-w-sm space-y-6">
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">GATEWAY ACCESS</span>
            <h2 className="text-xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight">
              Enter Credentials
            </h2>
          </div>

          {/* Global Error Banner */}
          {authError && (
            <Alert type="error" title="Authentication Failed">
              {authError}
            </Alert>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              label="School Code"
              type="text"
              placeholder="e.g. VGS001"
              value={schoolCode}
              onChange={(e) => setSchoolCode(e.target.value)}
              error={fieldErrors.schoolCode}
              leftIcon={<Building2 className="w-3.5 h-3.5 text-ink-muted/70" />}
              autoComplete="organization"
              autoFocus
              required
            />

            <Input
              label="Email Address"
              type="email"
              placeholder="registrar@school.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={fieldErrors.email}
              leftIcon={<Mail className="w-3.5 h-3.5 text-ink-muted/70" />}
              autoComplete="email"
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={fieldErrors.password}
              leftIcon={<Lock className="w-3.5 h-3.5 text-ink-muted/70" />}
              autoComplete="current-password"
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              className="w-full mt-2 py-2.5 font-mono text-[10px] font-bold uppercase tracking-widest"
            >
              Sign In To Portal
            </Button>
          </form>

          {/* Footer Notice */}
          <div className="pt-4 border-t border-divider/60 dark:border-stone-800 flex justify-between items-center text-[10px] font-mono text-ink-muted/60 dark:text-stone-600">
            <span className="flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-brand-500/50" />
              AUTHORIZED ACCESS ONLY
            </span>
            <span>ID: VIJAYKRISHNA343</span>
          </div>
        </div>
      </div>
    </div>
  );
};
