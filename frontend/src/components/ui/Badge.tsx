import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge = ({ children, variant = 'default', size = 'sm', className }: BadgeProps) => {
  // Base: rectangular status chip — status metadata, not decorative pill
  // rounded-sm = 2px per Tailwind config lock; never rounded-full or rounded-lg
  const base = 'inline-flex items-center font-mono font-semibold border rounded-sm leading-none';

  const variants = {
    // Neutral / default — general reference metadata
    default:
      'border-divider bg-paper-dim text-ink-muted ' +
      'dark:border-stone-700 dark:bg-stone-900 dark:text-stone-400',
    // Success — active, enrolled, promoted, complete
    success:
      'border-emerald-200/80 bg-emerald-50/50 text-emerald-800 ' +
      'dark:border-emerald-800/40 dark:bg-emerald-950/20 dark:text-emerald-400',
    // Warning — pending, retained, under review
    warning:
      'border-amber-200/80 bg-amber-50/50 text-amber-800 ' +
      'dark:border-amber-800/40 dark:bg-amber-950/20 dark:text-amber-400',
    // Error — blocked, failed, inactive, deleted
    error:
      'border-red-200/80 bg-red-50/50 text-red-800 ' +
      'dark:border-red-800/40 dark:bg-red-950/20 dark:text-red-400',
    // Info — upcoming, future, informational
    info:
      'border-sky-200/80 bg-sky-50/50 text-sky-800 ' +
      'dark:border-sky-800/40 dark:bg-sky-950/20 dark:text-sky-400',
    // Neutral alias — same as default, for explicit semantics
    neutral:
      'border-divider bg-paper-dim text-ink-muted ' +
      'dark:border-stone-700 dark:bg-stone-900 dark:text-stone-400',
  };

  const sizes = {
    sm: 'px-1.5 py-0.5 text-[9px] uppercase tracking-widest',
    md: 'px-2 py-0.5 text-[10px] uppercase tracking-wider',
  };

  return <span className={clsx(base, variants[variant], sizes[size], className)}>{children}</span>;
};
