import React from 'react';
import { clsx } from 'clsx';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export interface AlertProps {
  type?: 'info' | 'warning' | 'error' | 'success';
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

export const Alert = ({ type = 'info', title, children, onClose, className }: AlertProps) => {
  const icons = {
    info:    <Info className="w-4 h-4 shrink-0 mt-px" />,
    warning: <AlertTriangle className="w-4 h-4 shrink-0 mt-px" />,
    error:   <AlertCircle className="w-4 h-4 shrink-0 mt-px" />,
    success: <CheckCircle2 className="w-4 h-4 shrink-0 mt-px" />,
  };

  // Desaturated institutional palette — no vivid backgrounds
  const styles = {
    info:
      'bg-sky-50/50 border-sky-200/80 text-sky-900 ' +
      'dark:bg-sky-950/30 dark:border-sky-800/50 dark:text-sky-200',
    warning:
      'bg-amber-50/50 border-amber-200/80 text-amber-900 ' +
      'dark:bg-amber-950/30 dark:border-amber-800/50 dark:text-amber-200',
    error:
      'bg-red-50/50 border-red-200/80 text-red-900 ' +
      'dark:bg-red-950/30 dark:border-red-800/50 dark:text-red-200',
    success:
      'bg-emerald-50/50 border-emerald-200/80 text-emerald-900 ' +
      'dark:bg-emerald-950/30 dark:border-emerald-800/50 dark:text-emerald-200',
  };

  const iconColors = {
    info:    'text-sky-600 dark:text-sky-400',
    warning: 'text-amber-600 dark:text-amber-400',
    error:   'text-red-600 dark:text-red-400',
    success: 'text-emerald-600 dark:text-emerald-400',
  };

  return (
    <div
      className={clsx('flex gap-3 px-4 py-3 border text-xs', styles[type], className)}
      role="alert"
    >
      <span className={iconColors[type]}>{icons[type]}</span>
      <div className="flex-1 space-y-0.5 min-w-0">
        {title && (
          <h4 className="text-[11px] font-semibold font-mono uppercase tracking-wider leading-none">
            {title}
          </h4>
        )}
        <div className="leading-relaxed text-inherit">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-current opacity-50 hover:opacity-80 shrink-0 focus:outline-none focus-visible:ring-1"
          aria-label="Dismiss"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
