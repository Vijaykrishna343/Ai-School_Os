import React from 'react';
import { FolderOpen } from 'lucide-react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = ({
  icon = <FolderOpen className="w-8 h-8 text-ink-muted/40 dark:text-stone-600" />,
  title,
  description,
  action,
}: EmptyStateProps) => (
  // Flat institutional empty register — no bubble icon wrapper, no dashed card
  <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
    {/* Desaturated icon — purposefully restrained */}
    <div className="mb-4 text-ink-muted/40 dark:text-stone-600">{icon}</div>

    {/* Registry label: monospace caps as a register heading */}
    <h3 className="text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-500 leading-none">
      {title}
    </h3>

    {description && (
      <p className="mt-2 text-xs text-ink-muted/70 dark:text-stone-500 max-w-xs leading-relaxed">
        {description}
      </p>
    )}

    {action && <div className="mt-5">{action}</div>}
  </div>
);
