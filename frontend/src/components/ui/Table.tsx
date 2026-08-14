import React from 'react';
import { Skeleton } from './Skeleton';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  key: string;
  header: React.ReactNode;
  render?: (row: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyText?: string;
  emptyIcon?: React.ReactNode;
  rowKey?: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function Table<T>({
  columns,
  data,
  isLoading = false,
  emptyText = 'No records found',
  emptyIcon,
  rowKey,
  onRowClick,
  className = '',
}: TableProps<T>) {
  if (isLoading) {
    return (
      <div className="w-full overflow-x-auto rounded-none border border-slate-200 dark:border-slate-800">
        <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
          <thead className="bg-[#fcf9f8] text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:bg-slate-900/50 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={`px-3 py-2 ${col.headerClassName || ''}`}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {Array.from({ length: 5 }).map((_, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2">
                    <Skeleton className="h-3 w-full max-w-[100px]" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-none border border-slate-200 p-6 dark:border-slate-800 bg-white">
        <EmptyState title={emptyText} description="There is no data to display right now." icon={emptyIcon} />
      </div>
    );
  }

  return (
    <div className={`w-full overflow-x-auto rounded-none border border-slate-200 dark:border-slate-800 ${className}`}>
      <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
        <thead className="bg-[#fcf9f8] text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:bg-slate-900/50 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={`px-3 py-2 ${col.headerClassName || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-150 bg-white dark:divide-slate-800 dark:bg-slate-950">
          {data.map((row, idx) => {
            const key = rowKey ? rowKey(row, idx) : ((row as any).id || idx.toString());
            return (
              <tr
                key={key}
                onClick={() => onRowClick?.(row)}
                className={`transition-colors hover:bg-slate-50/60 dark:hover:bg-slate-900/50 ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`px-3 py-2 whitespace-nowrap ${col.className || ''}`}>
                    {col.render ? col.render(row, idx) : (row as any)[col.key] ?? '—'}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
