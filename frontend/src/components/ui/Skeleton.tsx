import React from 'react';
import { clsx } from 'clsx';

// Skeleton: slow-pulse flat fill matching the paper background
// No rounded-md — keeps consistent with design system shape policy
export const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={clsx(
      'animate-pulse bg-divider dark:bg-stone-800',
      className
    )}
    aria-hidden="true"
    {...props}
  />
);
