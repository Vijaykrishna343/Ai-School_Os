import React, { useEffect } from 'react';
import { clsx } from 'clsx';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal = ({ isOpen, onClose, title, children, footer, size = 'md' }: ModalProps) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    // Backdrop: dark ink overlay, no blur — flat institutional overlay
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-stone-950/70"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Administrative Decision Sheet: flat paper surface, no shadow, thin border */}
      <div
        className={clsx(
          'w-full bg-paper dark:bg-stone-950 border border-divider dark:border-stone-700 overflow-hidden',
          'shadow-[0_2px_8px_rgba(0,0,0,0.10)]',
          sizes[size]
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header: paper-dim tint, serif title, flat close button */}
        {title && (
          <div className="flex items-center justify-between px-5 py-3 border-b border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-900">
            <h3
              id="modal-title"
              className="text-sm font-serif font-semibold text-brand-500 dark:text-stone-100 tracking-tight"
            >
              {title}
            </h3>
            <button
              onClick={onClose}
              className="p-1 text-ink-muted/60 hover:text-ink-muted dark:hover:text-stone-200 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-brand-500"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Body: standard padding */}
        <div className="p-5">{children}</div>

        {/* Footer: dim-paper strip, right-aligned actions, thin top rule */}
        {footer && (
          <div className="px-5 py-3 bg-paper-dim dark:bg-stone-900/60 border-t border-divider dark:border-stone-800 flex justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
