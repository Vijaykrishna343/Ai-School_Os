import React from 'react';
import { clsx } from 'clsx';

// Card reinterpreted as an Institutional Panel
// Flat surface, 1px warm border, no shadow, rounded-none
// Use Card for content grouping that genuinely needs a container boundary.
// Prefer ledger/section/rule patterns for page-level layout.

export const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div
    className={clsx(
      'border border-divider bg-paper dark:border-stone-800 dark:bg-stone-950',
      className
    )}
  >
    {children}
  </div>
);

// CardHeader: paper-dim tint + thin divider rule
export const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div
    className={clsx(
      'px-4 py-3 bg-paper-dim border-b border-divider dark:bg-stone-900/60 dark:border-stone-800',
      className
    )}
  >
    {children}
  </div>
);

// CardTitle: serif display for section classification headings
export const CardTitle = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h3 className={clsx('text-sm font-serif font-semibold text-brand-500 dark:text-stone-100 tracking-tight', className)}>
    {children}
  </h3>
);

// CardContent: standard p-4 body area
export const CardContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx('p-4', className)}>{children}</div>
);

// CardFooter: dim-paper footer + thin top rule, right-aligned for action buttons
export const CardFooter = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div
    className={clsx(
      'px-4 py-3 bg-paper-dim border-t border-divider dark:bg-stone-900/40 dark:border-stone-800',
      className
    )}
  >
    {children}
  </div>
);
