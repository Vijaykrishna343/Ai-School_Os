import React from 'react';
import { clsx } from 'clsx';

export const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx('rounded-sm border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900', className)}>
    {children}
  </div>
);

export const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx('px-4 py-3 border-b border-slate-100 dark:border-slate-800/60', className)}>
    {children}
  </div>
);

export const CardTitle = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h3 className={clsx('text-sm font-bold font-serif text-brand-500 dark:text-slate-100', className)}>
    {children}
  </h3>
);

export const CardContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx('p-4', className)}>{children}</div>
);

export const CardFooter = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={clsx('px-4 py-3 bg-slate-50/50 border-t border-slate-100 rounded-b-sm dark:bg-slate-900/50 dark:border-slate-800/60', className)}>
    {children}
  </div>
);

