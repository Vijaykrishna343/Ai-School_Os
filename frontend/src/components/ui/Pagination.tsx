import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationProps {
  page: number;
  totalPages: number;
  totalItems?: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  className = '',
}) => {
  if (totalPages <= 1) return null;

  const startItem = (page - 1) * (pageSize || 10) + 1;
  const endItem = Math.min(page * (pageSize || 10), totalItems || page * (pageSize || 10));

  const navBtn = (
    label: string,
    icon: React.ReactNode,
    disabled: boolean,
    onClick: () => void
  ) => (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={
        'inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium border border-divider ' +
        'text-ink-muted transition-colors ' +
        'hover:bg-paper-dim hover:text-ink hover:border-ink-muted/30 ' +
        'dark:border-stone-700 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-200 ' +
        'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-ink-muted ' +
        'focus:outline-none focus-visible:ring-1 focus-visible:ring-brand-500'
      }
    >
      {icon}
    </button>
  );

  return (
    <div
      className={`flex flex-col sm:flex-row items-center justify-between gap-3 py-2.5 border-t border-divider dark:border-stone-800 ${className}`}
    >
      {/* Registry record count */}
      <p className="text-[10px] font-mono text-ink-muted dark:text-stone-500 leading-none">
        {totalItems !== undefined ? (
          <>
            Records{' '}
            <span className="text-ink dark:text-stone-300">{startItem}</span>
            {' '}–{' '}
            <span className="text-ink dark:text-stone-300">{endItem}</span>
            {' '}of{' '}
            <span className="text-ink dark:text-stone-300">{totalItems}</span>
          </>
        ) : (
          <>
            Page{' '}
            <span className="text-ink dark:text-stone-300">{page}</span>
            {' '}of{' '}
            <span className="text-ink dark:text-stone-300">{totalPages}</span>
          </>
        )}
      </p>

      {/* Registry navigation controls */}
      <div className="flex items-center gap-0">
        {navBtn('Previous page', <ChevronLeft className="w-3.5 h-3.5" />, page <= 1, () => onPageChange(page - 1))}

        {/* Current page indicator: solid brand-dim block */}
        <div className="inline-flex items-center px-3 py-1.5 border-y border-divider bg-paper-dim dark:border-stone-700 dark:bg-stone-900">
          <span className="text-[11px] font-mono font-semibold text-brand-500 dark:text-stone-200 leading-none">
            {page}
          </span>
        </div>

        {navBtn('Next page', <ChevronRight className="w-3.5 h-3.5" />, page >= totalPages, () => onPageChange(page + 1))}
      </div>
    </div>
  );
};
