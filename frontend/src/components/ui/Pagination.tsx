import React from 'react';
import { Button } from './Button';

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

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 py-3 border-t border-slate-200 dark:border-slate-800 ${className}`}>
      <div className="text-xs text-slate-500 dark:text-slate-400">
        {totalItems !== undefined ? (
          <>
            Showing <span className="font-semibold text-slate-700 dark:text-slate-200">{startItem}</span> to{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">{endItem}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">{totalItems}</span> results
          </>
        ) : (
          <>
            Page <span className="font-semibold text-slate-700 dark:text-slate-200">{page}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">{totalPages}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <span className="text-xs font-medium px-2 text-slate-600 dark:text-slate-400">
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
};
