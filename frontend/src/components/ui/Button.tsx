import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled,
      leftIcon,
      rightIcon,
      type = 'button',
      ...props
    },
    ref
  ) => {
    // Base: flat rectangular operational control, no rounding beyond 2px
    const baseStyles =
      'inline-flex items-center justify-center font-medium rounded-sm transition-colors ' +
      'focus:outline-none focus-visible:ring-1 focus-visible:ring-offset-1 ' +
      'disabled:opacity-40 disabled:cursor-not-allowed select-none';

    const variants = {
      // Primary: solid institutional blue — the primary command action
      primary:
        'bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-700 ' +
        'focus-visible:ring-brand-500 dark:bg-brand-500 dark:hover:bg-brand-600',
      // Secondary: dim-paper surface + border — for paired actions
      secondary:
        'bg-paper-dim text-ink border border-divider hover:bg-divider/60 active:bg-divider ' +
        'focus-visible:ring-ink-muted dark:bg-stone-800 dark:text-stone-200 dark:border-stone-700 dark:hover:bg-stone-700',
      // Outline: minimal — transparent with a visible border
      outline:
        'bg-transparent text-ink-muted border border-divider hover:bg-paper-dim hover:text-ink active:bg-divider/60 ' +
        'focus-visible:ring-ink-muted dark:border-stone-700 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-200',
      // Ghost: no border, for tertiary actions and nav controls
      ghost:
        'bg-transparent text-ink-muted hover:bg-paper-dim hover:text-ink active:bg-divider/60 ' +
        'focus-visible:ring-ink-muted dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-200',
      // Danger: desaturated red — destructive administrative action
      danger:
        'bg-red-700 text-white hover:bg-red-800 active:bg-red-900 ' +
        'focus-visible:ring-red-600 dark:bg-red-700 dark:hover:bg-red-800',
    };

    const sizes = {
      sm: 'px-2.5 py-1 text-[11px] tracking-wide gap-1.5',
      md: 'px-3 py-1.5 text-xs tracking-wide gap-2',
      lg: 'px-4 py-2 text-sm tracking-wide gap-2',
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={clsx(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        {!isLoading && leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
