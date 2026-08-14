import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge = ({ children, variant = 'default', size = 'sm', className }: BadgeProps) => {
  const base = 'inline-flex items-center font-mono font-medium rounded-sm border';

  const variants = {
    default: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300',
    success: 'border-emerald-200 bg-emerald-50/40 text-emerald-800 dark:border-emerald-800/40 dark:bg-emerald-950/20 dark:text-emerald-400',
    warning: 'border-amber-200 bg-amber-50/40 text-amber-800 dark:border-amber-800/40 dark:bg-amber-950/20 dark:text-amber-400',
    error: 'border-red-200 bg-red-50/40 text-red-800 dark:border-red-800/40 dark:bg-red-950/20 dark:text-red-400',
    info: 'border-sky-200 bg-sky-50/40 text-sky-800 dark:border-sky-800/40 dark:bg-sky-950/20 dark:text-sky-400',
    neutral: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px] uppercase tracking-wider',
    md: 'px-2.5 py-1 text-xs uppercase tracking-wider',
  };

  return <span className={clsx(base, variants[variant], sizes[size], className)}>{children}</span>;
};
