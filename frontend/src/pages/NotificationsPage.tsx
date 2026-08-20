import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi, NotificationItem } from '@/services/api/phase9Api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { Bell, Send, Smartphone, Mail, MessageSquare } from 'lucide-react';

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [isSendModalOpen, setIsSendModalOpen] = useState(false);

  const [sendForm, setSendForm] = useState({
    title: '',
    message: '',
    recipient_name: 'All Parents & Teachers',
    recipient_contact: '9999999999',
    channel: 'IN_APP',
  });
  const [sendError, setSendError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', page, pageSize, statusFilter, channelFilter],
    queryFn: () =>
      notificationsApi.list({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
      }),
  });

  const sendMutation = useMutation({
    mutationFn: notificationsApi.sendAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setIsSendModalOpen(false);
      setSendForm({
        title: '',
        message: '',
        recipient_name: 'All Parents & Teachers',
        recipient_contact: '9999999999',
        channel: 'IN_APP',
      });
    },
    onError: (err: any) => {
      setSendError(err.message || 'Failed to send notification');
    },
  });

  const handleSendSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSendError(null);
    sendMutation.mutate(sendForm);
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'SMS':
        return <Smartphone className="w-4 h-4 text-blue-500" />;
      case 'WHATSAPP':
        return <MessageSquare className="w-4 h-4 text-emerald-500" />;
      case 'EMAIL':
        return <Mail className="w-4 h-4 text-purple-500" />;
      default:
        return <Bell className="w-4 h-4 text-amber-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SENT':
      case 'DELIVERED':
        return <Badge variant="success">{status}</Badge>;
      case 'FAILED':
        return <Badge variant="error">{status}</Badge>;
      default:
        return <Badge variant="warning">{status}</Badge>;
    }
  };

  const columns: Column<NotificationItem>[] = [
    {
      key: 'channel',
      header: 'Channel',
      render: (n) => (
        <div className="flex items-center space-x-2">
          {getChannelIcon(n.channel)}
          <span className="font-medium text-xs text-ink dark:text-stone-200">{n.channel}</span>
        </div>
      ),
    },
    {
      key: 'recipient_name',
      header: 'Recipient',
      render: (n) => (
        <div>
          <div className="font-semibold text-sm text-ink dark:text-stone-100">{n.recipient_name}</div>
          <div className="text-xs text-ink-muted dark:text-stone-400 font-mono">{n.recipient_contact}</div>
        </div>
      ),
    },
    {
      key: 'title',
      header: 'Title & Message',
      render: (n) => (
        <div className="max-w-md">
          <div className="font-medium text-sm text-ink dark:text-stone-200">{n.title}</div>
          <div className="text-xs text-ink-muted dark:text-stone-400 truncate">{n.body}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (n) => getStatusBadge(n.status),
    },
    {
      key: 'created_at',
      header: 'Sent At',
      render: (n) => (
        <span className="text-xs text-ink-muted dark:text-stone-400 font-mono">
          {n.created_at ? new Date(n.created_at).toLocaleString() : 'Pending'}
        </span>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-ink dark:text-stone-100 tracking-tight">
            School Communication & Notifications
          </h1>
          <p className="text-sm text-ink-muted dark:text-stone-400 mt-1">
            Dispatch announcements and view delivery logs across IN_APP, SMS, WhatsApp, and EMAIL.
          </p>
        </div>
        <Button onClick={() => setIsSendModalOpen(true)}>
          <Send className="w-4 h-4 mr-2" />
          Send Announcement
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex space-x-3 bg-white dark:bg-stone-900 p-3 rounded-xl border border-stone-200 dark:border-stone-800">
        <select
          value={channelFilter}
          onChange={(e) => setChannelFilter(e.target.value)}
          className="text-sm border border-stone-300 dark:border-stone-700 rounded-lg px-3 py-1.5 bg-white dark:bg-stone-800 text-ink dark:text-stone-200"
        >
          <option value="">All Channels</option>
          <option value="IN_APP">In-App</option>
          <option value="SMS">SMS</option>
          <option value="WHATSAPP">WhatsApp</option>
          <option value="EMAIL">Email</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-sm border border-stone-300 dark:border-stone-700 rounded-lg px-3 py-1.5 bg-white dark:bg-stone-800 text-ink dark:text-stone-200"
        >
          <option value="">All Statuses</option>
          <option value="SENT">Sent</option>
          <option value="DELIVERED">Delivered</option>
          <option value="FAILED">Failed</option>
          <option value="PENDING">Pending</option>
        </select>
      </div>

      {/* Notifications Table */}
      <div className="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl overflow-hidden shadow-sm">
        <Table
          columns={columns}
          data={data?.items || []}
          isLoading={isLoading}
          rowKey={(item) => item.id}
        />
      </div>

      {/* Send Announcement Modal */}
      <Modal
        isOpen={isSendModalOpen}
        onClose={() => setIsSendModalOpen(false)}
        title="Broadcast School Announcement"
      >
        <form onSubmit={handleSendSubmit} className="space-y-4">
          {sendError && <Alert type="error">{sendError}</Alert>}
          <Input
            label="Announcement Title"
            required
            value={sendForm.title}
            onChange={(e) => setSendForm({ ...sendForm, title: e.target.value })}
            placeholder="e.g. Sports Day Schedule Update"
          />
          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">
              Message Content
            </label>
            <textarea
              required
              rows={3}
              value={sendForm.message}
              onChange={(e) => setSendForm({ ...sendForm, message: e.target.value })}
              placeholder="Enter announcement details..."
              className="w-full text-sm border border-stone-300 dark:border-stone-700 rounded-lg p-2.5 bg-white dark:bg-stone-800 text-ink dark:text-stone-200"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">
                Channel
              </label>
              <select
                value={sendForm.channel}
                onChange={(e) => setSendForm({ ...sendForm, channel: e.target.value })}
                className="w-full text-sm border border-stone-300 dark:border-stone-700 rounded-lg p-2 bg-white dark:bg-stone-800 text-ink dark:text-stone-200"
              >
                <option value="IN_APP">IN_APP</option>
                <option value="SMS">SMS (Mock)</option>
                <option value="WHATSAPP">WHATSAPP (Mock)</option>
                <option value="EMAIL">EMAIL (Mock)</option>
              </select>
            </div>
            <Input
              label="Recipient Group / Name"
              required
              value={sendForm.recipient_name}
              onChange={(e) => setSendForm({ ...sendForm, recipient_name: e.target.value })}
            />
          </div>
          <Input
            label="Target Contact / Phone Number"
            required
            value={sendForm.recipient_contact}
            onChange={(e) => setSendForm({ ...sendForm, recipient_contact: e.target.value })}
          />

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsSendModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={sendMutation.isPending}>
              Dispatch Notification
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
