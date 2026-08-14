import React from 'react';
import { clsx } from 'clsx';

export const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={clsx('animate-pulse rounded-md bg-slate-200 dark:bg-slate-800', className)}
    {...props}
  />
);
