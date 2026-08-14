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

const TableHead = ({ columns }: { columns: Column<unknown>[] }) => (
  <thead>
    <tr className="bg-paper-dim dark:bg-stone-900/80 border-b border-divider dark:border-stone-800">
      {columns.map((col) => (
        <th
          key={col.key}
          scope="col"
          className={`px-3 py-2 text-left text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-500 whitespace-nowrap ${col.headerClassName || ''}`}
        >
          {col.header}
        </th>
      ))}
    </tr>
  </thead>
);

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
      <div className={`w-full overflow-x-auto border border-divider dark:border-stone-800 ${className}`}>
        <table className="w-full text-left min-w-full">
          <TableHead columns={columns as Column<unknown>[]} />
          <tbody className="bg-paper dark:bg-stone-950">
            {Array.from({ length: 6 }).map((_, idx) => (
              <tr key={idx} className="border-b border-divider/60 dark:border-stone-800/60">
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2">
                    <Skeleton className="h-3 w-full max-w-[140px]" />
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
      <div className={`border border-divider dark:border-stone-800 bg-paper dark:bg-stone-950 ${className}`}>
        <EmptyState title={emptyText} description="No records match the current registry filters." icon={emptyIcon} />
      </div>
    );
  }

  return (
    <div className={`w-full overflow-x-auto border border-divider dark:border-stone-800 ${className}`}>
      <table className="w-full text-left min-w-full">
        <TableHead columns={columns as Column<unknown>[]} />
        <tbody className="bg-paper dark:bg-stone-950 divide-y divide-divider/60 dark:divide-stone-800/60">
          {data.map((row, idx) => {
            const key = rowKey ? rowKey(row, idx) : ((row as any).id || idx.toString());
            return (
              <tr
                key={key}
                onClick={() => onRowClick?.(row)}
                className={`transition-colors hover:bg-paper-dim/70 dark:hover:bg-stone-900/60 ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-3 py-2 text-xs text-ink dark:text-stone-300 whitespace-nowrap ${col.className || ''}`}
                  >
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
