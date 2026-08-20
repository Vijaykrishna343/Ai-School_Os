import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditLogsApi, AuditLogItem } from '@/services/api/phase9Api';
import { Table, Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Shield } from 'lucide-react';

export const AuditLogPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [userEmail, setUserEmail] = useState('');
  const [action, setAction] = useState('');
  const [module, setModule] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, pageSize, userEmail, action, module],
    queryFn: () =>
      auditLogsApi.list({
        page,
        page_size: pageSize,
        user_email: userEmail || undefined,
        action: action || undefined,
        module: module || undefined,
      }),
  });

  const columns: Column<AuditLogItem>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp',
      render: (log) => (
        <span className="text-xs text-ink-muted dark:text-stone-400 font-mono">
          {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
        </span>
      ),
    },
    {
      key: 'user_email',
      header: 'User & Role',
      render: (log) => (
        <div>
          <div className="font-medium text-sm text-ink dark:text-stone-100">{log.user_email}</div>
          <div className="text-xs text-brand-600 dark:text-brand-400 font-mono">{log.role_name || 'System'}</div>
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Action / Event',
      render: (log) => (
        <div>
          <Badge variant={log.status_code < 400 ? 'success' : 'error'}>
            {log.action}
          </Badge>
          <span className="ml-2 text-xs text-ink-muted dark:text-stone-400 font-mono">
            {log.status_code}
          </span>
        </div>
      ),
    },
    {
      key: 'module',
      header: 'Module',
      render: (log) => (
        <span className="text-xs font-semibold uppercase tracking-wider text-stone-600 dark:text-stone-300">
          {log.module}
        </span>
      ),
    },
    {
      key: 'entity_type',
      header: 'Entity Details',
      render: (log) => (
        <div className="text-xs text-ink-muted dark:text-stone-400">
          {log.entity_type && <span className="font-mono text-ink dark:text-stone-200">{log.entity_type}: </span>}
          {log.entity_id && <span className="font-mono text-stone-500">{log.entity_id}</span>}
          {log.details && <div className="truncate max-w-xs">{log.details}</div>}
        </div>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP Address',
      render: (log) => (
        <span className="text-xs font-mono text-stone-400">
          {log.ip_address || '127.0.0.1'}
        </span>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-ink dark:text-stone-100 tracking-tight flex items-center space-x-2">
            <Shield className="w-6 h-6 text-brand-500" />
            <span>Administrative Audit Log</span>
          </h1>
          <p className="text-sm text-ink-muted dark:text-stone-400 mt-1">
            System audit trail for tracking administrative changes, logins, and operational events.
          </p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-white dark:bg-stone-900 p-4 rounded-xl border border-stone-200 dark:border-stone-800">
        <Input
          placeholder="Filter by user email..."
          value={userEmail}
          onChange={(e) => setUserEmail(e.target.value)}
        />
        <Input
          placeholder="Filter by action (e.g. CREATE, DELETE)..."
          value={action}
          onChange={(e) => setAction(e.target.value)}
        />
        <Input
          placeholder="Filter by module..."
          value={module}
          onChange={(e) => setModule(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl overflow-hidden shadow-sm">
        <Table
          columns={columns}
          data={data?.items || []}
          isLoading={isLoading}
          rowKey={(item) => item.id}
        />
      </div>
    </div>
  );
};
