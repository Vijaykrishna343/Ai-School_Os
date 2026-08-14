import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  width = 'md',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const widthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  }[width];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
      {/* Backdrop: dark ink overlay, no blur */}
      <div
        className="absolute inset-0 bg-stone-950/60 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dossier Panel: slides from right, plain vertical border, no shadow */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div
          className={`w-screen ${widthClasses} bg-paper dark:bg-stone-950 border-l border-divider dark:border-stone-800 flex flex-col`}
        >
          {/* Dossier Header: paper-dim, serif title, mono subtitle */}
          <div className="flex items-start justify-between px-5 py-4 border-b border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-900 shrink-0">
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-serif font-semibold text-brand-500 dark:text-stone-100 tracking-tight leading-tight">
                {title}
              </h2>
              {subtitle && (
                <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 mt-0.5 leading-none">
                  {subtitle}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="ml-4 p-1 text-ink-muted/60 hover:text-ink-muted dark:hover:text-stone-200 shrink-0 focus:outline-none focus-visible:ring-1 focus-visible:ring-brand-500"
              aria-label="Close dossier"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Dossier Body: scrollable content area */}
          <div className="flex-1 overflow-y-auto p-5">{children}</div>

          {/* Dossier Footer: dim tint, thin top rule */}
          {footer && (
            <div className="px-5 py-4 border-t border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-900/50 shrink-0">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
