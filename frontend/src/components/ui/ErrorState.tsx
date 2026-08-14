import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState = ({
  title = 'Request Could Not Be Completed',
  message = 'The server returned an error while retrieving this register. Please try again.',
  onRetry,
}: ErrorStateProps) => (
  // Desaturated error panel — flat, muted, institutional
  <div className="flex flex-col items-center justify-center py-10 px-6 text-center border border-red-200/60 dark:border-red-900/40 bg-red-50/30 dark:bg-red-950/10">
    {/* Compact icon — no rounded bubble wrapper */}
    <AlertTriangle className="w-7 h-7 text-red-600/70 dark:text-red-500/70 mb-4" />

    {/* Institutional error label */}
    <h3 className="text-[10px] font-mono font-semibold uppercase tracking-widest text-red-800 dark:text-red-300 leading-none">
      {title}
    </h3>

    <p className="mt-2 text-xs text-red-700/80 dark:text-red-300/70 max-w-md leading-relaxed">
      {message}
    </p>

    {onRetry && (
      <Button
        onClick={onRetry}
        variant="outline"
        size="sm"
        className="mt-5 border-red-300 text-red-700 hover:bg-red-100/40 dark:border-red-800 dark:text-red-300"
        leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
      >
        Retry Request
      </Button>
    )}
  </div>
);
