import React, { InputHTMLAttributes, forwardRef, useState } from 'react';
import { clsx } from 'clsx';
import { Eye, EyeOff } from 'lucide-react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, type = 'text', className, id, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
    const isPassword = type === 'password';
    const actualType = isPassword ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-ink-muted/60">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={actualType}
            className={clsx(
              // Base: institutional form field — cream fill, compact height, thin border
              'block w-full border text-xs transition-colors focus:outline-none',
              'placeholder:text-ink-muted/50 dark:placeholder:text-stone-600',
              leftIcon ? 'pl-8' : 'pl-2.5',
              isPassword || rightIcon ? 'pr-8' : 'pr-2.5',
              'py-1.5',
              // Disabled: visually dimmed, no interaction
              'disabled:bg-paper-dim disabled:text-ink-muted disabled:cursor-not-allowed',
              'dark:disabled:bg-stone-900 dark:disabled:text-stone-600',
              // Error state: red border, error text
              error
                ? 'border-red-400 bg-red-50/30 text-red-900 focus:border-red-500 focus:ring-0 ' +
                  'dark:border-red-700 dark:bg-red-950/20 dark:text-red-200'
                // Default state:
                // Resting:  cream fill (#f4f1ef = paper-dim) with warm divider border
                // Focused:  white fill + stronger brand border
                : 'border-divider bg-paper-dim text-ink ' +
                  'focus:border-brand-500 focus:bg-paper focus:ring-0 ' +
                  'dark:border-stone-700 dark:bg-stone-900 dark:text-stone-100 ' +
                  'dark:focus:border-brand-400 dark:focus:bg-stone-950',
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-ink-muted/60 hover:text-ink-muted dark:hover:text-stone-300"
              tabIndex={-1}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          )}
          {!isPassword && rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none text-ink-muted/60">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="text-[10px] font-mono text-red-700 dark:text-red-400 leading-none mt-0.5">{error}</p>
        )}
        {!error && helperText && (
          <p className="text-[10px] text-ink-muted dark:text-stone-500 leading-none mt-0.5">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
