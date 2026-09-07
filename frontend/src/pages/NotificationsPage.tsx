import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { communicationApi, NotificationItem, UserPreferences, NotificationTemplate } from '@/api/communication';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { Card } from '@/components/ui/Card';
import {
  Bell,
  Send,
  Smartphone,
  Mail,
  MessageSquare,
  RefreshCw,
  Sliders,
  FileCode,
  Inbox,
  CheckCircle2,
  AlertTriangle,
  Server,
  ShieldCheck,
  CheckCheck,
  Sparkles,
} from 'lucide-react';
import { generateCommunicationDraft, CommunicationDraftResponse } from '@/api/aiCommunicationApi';

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { permissions, user } = useAuthStore();

  const isCommunicationAdmin =
    ['School Admin', 'Principal', 'Vice Principal', 'Super Admin'].some((r) =>
      user?.roles?.map((role: any) => (typeof role === 'string' ? role : role.name)).includes(r)
    ) ||
    permissions.includes('notification.manage') ||
    permissions.includes('notification.delivery.view');

  const [activeTab, setActiveTab] = useState<'inbox' | 'preferences' | 'logs' | 'templates' | 'providers'>('inbox');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);

  // AI Draft Assistant State
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [aiDraftForm, setAiDraftForm] = useState({
    category: 'ANNOUNCEMENT',
    target_audience: 'PARENTS',
    tone: 'FORMAL',
    key_details: '',
  });
  const [aiDraftResult, setAiDraftResult] = useState<CommunicationDraftResponse | null>(null);
  const [aiSelectedChannel, setAiSelectedChannel] = useState<'SMS' | 'EMAIL' | 'WHATSAPP' | 'IN_APP'>('EMAIL');

  const aiDraftMutation = useMutation({
    mutationFn: generateCommunicationDraft,
    onSuccess: (data) => {
      setAiDraftResult(data);
    },
  });

  // Send Form
  const [sendForm, setSendForm] = useState({
    title: '',
    message: '',
    recipient_name: 'All Staff & Students',
    recipient_contact: 'admin@school.com',
    channel: 'IN_APP',
  });
  const [sendError, setSendError] = useState<string | null>(null);

  // Template Form
  const [templateForm, setTemplateForm] = useState({
    template_key: '',
    name: '',
    category: 'ANNOUNCEMENT',
    title_template: '',
    body_template: '',
  });

  // ── Queries ──────────────
  const inboxQuery = useQuery({
    queryKey: ['user-inbox', page, pageSize],
    queryFn: () => communicationApi.fetchUserInbox(page, pageSize),
  });

  const preferencesQuery = useQuery({
    queryKey: ['user-preferences'],
    queryFn: communicationApi.fetchUserPreferences,
  });

  const logsQuery = useQuery({
    queryKey: ['notification-logs', page, pageSize, statusFilter, channelFilter],
    queryFn: () =>
      communicationApi.fetchDeliveryLogs({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
      }),
    enabled: isCommunicationAdmin,
  });

  const metricsQuery = useQuery({
    queryKey: ['delivery-metrics'],
    queryFn: communicationApi.fetchDeliveryMetrics,
    enabled: isCommunicationAdmin,
  });

  const templatesQuery = useQuery({
    queryKey: ['notification-templates'],
    queryFn: communicationApi.fetchTemplates,
    enabled: isCommunicationAdmin,
  });

  const providersQuery = useQuery({
    queryKey: ['provider-statuses'],
    queryFn: communicationApi.fetchProviderStatuses,
    enabled: isCommunicationAdmin,
  });

  // ── Mutations ─────────────
  const markReadMutation = useMutation({
    mutationFn: communicationApi.markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-inbox'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: communicationApi.markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-inbox'] });
    },
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: communicationApi.updateUserPreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: communicationApi.retryNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-logs'] });
      queryClient.invalidateQueries({ queryKey: ['delivery-metrics'] });
    },
  });

  const sendMutation = useMutation({
    mutationFn: communicationApi.sendAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-logs'] });
      queryClient.invalidateQueries({ queryKey: ['user-inbox'] });
      setIsSendModalOpen(false);
      setSendForm({
        title: '',
        message: '',
        recipient_name: 'All Staff & Students',
        recipient_contact: 'admin@school.com',
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

  const createTemplateMutation = useMutation({
    mutationFn: communicationApi.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] });
      setIsTemplateModalOpen(false);
      setTemplateForm({
        template_key: '',
        name: '',
        category: 'ANNOUNCEMENT',
        title_template: '',
        body_template: '',
      });
    },
  });

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
      case 'CANCELLED':
        return <Badge variant="neutral">{status}</Badge>;
      default:
        return <Badge variant="warning">{status}</Badge>;
    }
  };

  const logsColumns: Column<NotificationItem>[] = [
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
          <div className="font-medium text-xs text-ink dark:text-stone-200">{n.recipient_name}</div>
          <div className="text-[11px] text-muted dark:text-stone-400 font-mono">{n.recipient_contact}</div>
        </div>
      ),
    },
    {
      key: 'title',
      header: 'Notification Payload',
      render: (n) => (
        <div>
          <div className="font-semibold text-xs text-ink dark:text-stone-100">{n.title}</div>
          <div className="text-[11px] text-muted dark:text-stone-400 line-clamp-1">{n.body}</div>
          {n.error_message && (
            <div className="text-[10px] text-rose-600 dark:text-rose-400 mt-1">Err: {n.error_message}</div>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (n) => (
        <div className="flex items-center space-x-2">
          {getStatusBadge(n.status)}
          {n.retry_count !== undefined && (
            <span className="text-[10px] text-stone-500">
              ({n.retry_count}/{n.max_retries})
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (n) =>
        n.status === 'FAILED' ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => retryMutation.mutate(n.id)}
            isLoading={retryMutation.isPending}
          >
            <RefreshCw className="w-3 h-3 mr-1" /> Retry
          </Button>
        ) : null,
    },
  ];

  const prefs = preferencesQuery.data;

  return (
    <div className="p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink dark:text-stone-100 flex items-center gap-2">
            <Bell className="w-7 h-7 text-brand-600 dark:text-brand-400" />
            Communication & Notification Center
          </h1>
          <p className="text-sm text-muted dark:text-stone-400">
            Multi-channel messaging platform, user notification inbox, and provider administration.
          </p>
        </div>

        {isCommunicationAdmin && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setIsAiModalOpen(true)}
              className="flex items-center gap-2 border-purple-300 text-purple-700 hover:bg-purple-50 dark:border-purple-800 dark:text-purple-300 dark:hover:bg-purple-950"
            >
              <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" /> AI Draft Assistant
            </Button>
            <Button onClick={() => setIsSendModalOpen(true)} className="flex items-center gap-2">
              <Send className="w-4 h-4" /> Send Announcement
            </Button>
          </div>
        )}
      </div>

      {/* Admin KPI Summary Cards */}
      {isCommunicationAdmin && metricsQuery.data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Total Notifications</div>
            <div className="text-2xl font-bold text-ink dark:text-stone-100 mt-1">
              {metricsQuery.data.total_notifications}
            </div>
            <div className="text-[11px] text-stone-500 mt-1">Dispatched across channels</div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Sent & Delivered</div>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {metricsQuery.data.sent_count}
            </div>
            <div className="text-[11px] text-emerald-600 mt-1">100% Verified delivery</div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Failed Attempts</div>
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">
              {metricsQuery.data.failed_count}
            </div>
            <div className="text-[11px] text-rose-600 mt-1">
              Failure rate: {metricsQuery.data.failure_rate_percent}%
            </div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Channel Distribution</div>
            <div className="flex items-center space-x-2 mt-2 text-xs font-semibold">
              <span className="text-amber-500">IN:{metricsQuery.data.by_channel.IN_APP || 0}</span>
              <span className="text-purple-500">EM:{metricsQuery.data.by_channel.EMAIL || 0}</span>
              <span className="text-blue-500">SMS:{metricsQuery.data.by_channel.SMS || 0}</span>
              <span className="text-emerald-500">WA:{metricsQuery.data.by_channel.WHATSAPP || 0}</span>
            </div>
          </Card>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex border-b border-stone-200 dark:border-stone-800 space-x-4">
        <button
          onClick={() => setActiveTab('inbox')}
          className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
            activeTab === 'inbox'
              ? 'border-brand-600 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
          }`}
        >
          <Inbox className="w-4 h-4" /> My Notification Inbox
          {inboxQuery.data?.unread_count ? (
            <Badge variant="error" className="ml-1">
              {inboxQuery.data.unread_count}
            </Badge>
          ) : null}
        </button>

        <button
          onClick={() => setActiveTab('preferences')}
          className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
            activeTab === 'preferences'
              ? 'border-brand-600 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
          }`}
        >
          <Sliders className="w-4 h-4" /> Preferences
        </button>

        {isCommunicationAdmin && (
          <>
            <button
              onClick={() => setActiveTab('logs')}
              className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
                activeTab === 'logs'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
              }`}
            >
              <FileCode className="w-4 h-4" /> Delivery Logs & Retry
            </button>

            <button
              onClick={() => setActiveTab('templates')}
              className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
                activeTab === 'templates'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
              }`}
            >
              <FileCode className="w-4 h-4" /> Templates
            </button>

            <button
              onClick={() => setActiveTab('providers')}
              className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
                activeTab === 'providers'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
              }`}
            >
              <Server className="w-4 h-4" /> Provider Adapters
            </button>
          </>
        )}
      </div>

      {/* ── TAB 1: MY INBOX ────────────────────────────────────────────── */}
      {activeTab === 'inbox' && (
        <Card className="p-6 space-y-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
              <Inbox className="w-5 h-5 text-brand-500" /> Notifications Inbox
            </h3>
            {inboxQuery.data?.unread_count ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => markAllReadMutation.mutate()}
                isLoading={markAllReadMutation.isPending}
              >
                <CheckCheck className="w-4 h-4 mr-1" /> Mark All as Read
              </Button>
            ) : null}
          </div>

          {inboxQuery.isLoading ? (
            <div className="p-8 text-center text-muted">Loading inbox...</div>
          ) : inboxQuery.data?.items?.length === 0 ? (
            <div className="p-8 text-center text-muted">No notifications in your inbox.</div>
          ) : (
            <div className="space-y-3">
              {inboxQuery.data?.items?.map((item: NotificationItem) => (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border transition-all ${
                    item.is_read
                      ? 'bg-stone-50 dark:bg-stone-950 border-stone-200 dark:border-stone-800 opacity-80'
                      : 'bg-brand-50/40 dark:bg-brand-950/20 border-brand-200 dark:border-brand-800 font-medium'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="mt-1">{getChannelIcon(item.channel)}</div>
                      <div>
                        <div className="font-semibold text-sm text-ink dark:text-stone-100 flex items-center gap-2">
                          {item.title}
                          {!item.is_read && <Badge variant="error">UNREAD</Badge>}
                        </div>
                        <p className="text-xs text-stone-600 dark:text-stone-300 mt-1">{item.body}</p>
                        <div className="text-[10px] text-muted mt-2 font-mono">
                          {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                        </div>
                      </div>
                    </div>

                    {!item.is_read && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => markReadMutation.mutate(item.id)}
                        isLoading={markReadMutation.isPending}
                      >
                        Mark Read
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* ── TAB 2: COMMUNICATION PREFERENCES ──────────────────────────────────────── */}
      {activeTab === 'preferences' && prefs && (
        <Card className="p-6 space-y-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
          <div>
            <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
              <Sliders className="w-5 h-5 text-brand-500" /> Communication Preferences
            </h3>
            <p className="text-xs text-muted dark:text-stone-400 mt-1">
              Select which communication channels and notification categories you wish to receive.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Channel Controls */}
            <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-3">
              <h4 className="font-bold text-xs uppercase text-brand-600 dark:text-brand-400">
                Delivery Channels
              </h4>
              {[
                { key: 'enable_in_app', label: 'In-App Web Inbox' },
                { key: 'enable_email', label: 'Email Notifications' },
                { key: 'enable_sms', label: 'SMS Messages' },
                { key: 'enable_whatsapp', label: 'WhatsApp Messaging' },
              ].map((c) => (
                <label key={c.key} className="flex items-center justify-between cursor-pointer py-1">
                  <span className="text-sm font-medium text-ink dark:text-stone-200">{c.label}</span>
                  <input
                    type="checkbox"
                    checked={Boolean((prefs as any)[c.key])}
                    onChange={(e) =>
                      updatePreferencesMutation.mutate({ [c.key]: e.target.checked })
                    }
                    className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                  />
                </label>
              ))}
            </div>

            {/* Category Controls */}
            <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-3">
              <h4 className="font-bold text-xs uppercase text-brand-600 dark:text-brand-400">
                Notification Categories
              </h4>
              {[
                { key: 'enable_attendance', label: 'Student Absence & Attendance Alerts' },
                { key: 'enable_fees', label: 'Fee Dues & Payment Receipts' },
                { key: 'enable_exams', label: 'Exam Schedules & Report Cards' },
                { key: 'enable_events', label: 'School Events & Calendar' },
                { key: 'enable_hostel', label: 'Hostel Outpass & Attendance' },
                { key: 'enable_leave', label: 'Staff Leave Updates' },
                { key: 'enable_announcements', label: 'General Announcements' },
              ].map((c) => (
                <label key={c.key} className="flex items-center justify-between cursor-pointer py-1">
                  <span className="text-sm font-medium text-ink dark:text-stone-200">{c.label}</span>
                  <input
                    type="checkbox"
                    checked={Boolean((prefs as any)[c.key])}
                    onChange={(e) =>
                      updatePreferencesMutation.mutate({ [c.key]: e.target.checked })
                    }
                    className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                  />
                </label>
              ))}

              <div className="pt-2 border-t border-stone-200 dark:border-stone-800 flex items-center justify-between">
                <span className="text-sm font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4" /> Emergency Alerts
                </span>
                <Badge variant="error">MANDATORY</Badge>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* ── TAB 3: DELIVERY LOGS & RETRY QUEUE ──────────────────────────────────── */}
      {activeTab === 'logs' && isCommunicationAdmin && (
        <Card className="p-6 space-y-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h3 className="text-base font-bold text-ink dark:text-stone-100">Delivery History & Retry Audit</h3>
            <div className="flex items-center space-x-2">
              <select
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                className="px-3 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
              >
                <option value="">All Channels</option>
                <option value="IN_APP">In-App</option>
                <option value="EMAIL">Email</option>
                <option value="SMS">SMS</option>
                <option value="WHATSAPP">WhatsApp</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
              >
                <option value="">All Statuses</option>
                <option value="SENT">Sent</option>
                <option value="FAILED">Failed</option>
                <option value="PENDING">Pending</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          <Table
            data={logsQuery.data?.items || []}
            columns={logsColumns}
            isLoading={logsQuery.isLoading}
            emptyText="No delivery logs match your filter."
          />
        </Card>
      )}

      {/* ── TAB 4: NOTIFICATION TEMPLATES ──────────────────────────────────────── */}
      {activeTab === 'templates' && isCommunicationAdmin && (
        <Card className="p-6 space-y-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-ink dark:text-stone-100">Notification Templates</h3>
              <p className="text-xs text-muted dark:text-stone-400">
                School-configurable templates with variable placeholders (e.g. &#123;&#123;student_name&#125;&#125;).
              </p>
            </div>
            <Button size="sm" onClick={() => setIsTemplateModalOpen(true)}>
              + Add Custom Template
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templatesQuery.data?.map((t: NotificationTemplate) => (
              <div
                key={t.id}
                className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-2 bg-stone-50 dark:bg-stone-950"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-brand-600 dark:text-brand-400">
                    {t.template_key}
                  </span>
                  <Badge variant={t.is_custom ? 'info' : 'neutral'}>
                    {t.is_custom ? 'CUSTOM' : 'DEFAULT'}
                  </Badge>
                </div>
                <div className="font-semibold text-sm text-ink dark:text-stone-100">{t.name}</div>
                <div className="text-xs font-medium text-stone-700 dark:text-stone-300">
                  Subject: <span className="font-normal">{t.title_template}</span>
                </div>
                <div className="text-xs text-muted dark:text-stone-400 line-clamp-2">{t.body_template}</div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── TAB 5: PROVIDER ADAPTERS STATUS ────────────────────────────────────── */}
      {activeTab === 'providers' && isCommunicationAdmin && (
        <Card className="p-6 space-y-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
          <div>
            <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
              <Server className="w-5 h-5 text-brand-500" /> Channel Provider Adapters
            </h3>
            <p className="text-xs text-muted dark:text-stone-400 mt-1">
              Active channel driver state. Unconfigured production drivers fall back to Mock Development Mode safely.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {providersQuery.data?.map((p) => (
              <div key={p.channel} className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getChannelIcon(p.channel)}
                    <span className="font-bold text-sm text-ink dark:text-stone-100">{p.channel}</span>
                  </div>
                  <Badge variant={p.is_configured ? 'success' : 'warning'}>{p.status}</Badge>
                </div>
                <div className="text-xs text-stone-600 dark:text-stone-400">
                  Driver Adapter: <span className="font-mono font-semibold">{p.provider_name}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Modal: Send Announcement */}
      <Modal isOpen={isSendModalOpen} onClose={() => setIsSendModalOpen(false)} title="Dispatch Transactional Announcement">
        <form onSubmit={handleSendSubmit} className="space-y-4">
          {sendError && <Alert type="error">{sendError}</Alert>}

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Title</label>
            <Input
              value={sendForm.title}
              onChange={(e) => setSendForm({ ...sendForm, title: e.target.value })}
              placeholder="e.g. Parent Teacher Meeting Reminder"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Message Body</label>
            <textarea
              value={sendForm.message}
              onChange={(e) => setSendForm({ ...sendForm, message: e.target.value })}
              className="w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              rows={3}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Recipient Name</label>
              <Input
                value={sendForm.recipient_name}
                onChange={(e) => setSendForm({ ...sendForm, recipient_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Recipient Contact</label>
              <Input
                value={sendForm.recipient_contact}
                onChange={(e) => setSendForm({ ...sendForm, recipient_contact: e.target.value })}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Channel</label>
            <select
              value={sendForm.channel}
              onChange={(e) => setSendForm({ ...sendForm, channel: e.target.value })}
              className="w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
            >
              <option value="IN_APP">In-App Inbox</option>
              <option value="EMAIL">Email</option>
              <option value="SMS">SMS</option>
              <option value="WHATSAPP">WhatsApp</option>
            </select>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="outline" onClick={() => setIsSendModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={sendMutation.isPending}>
              Dispatch
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Create Template */}
      <Modal isOpen={isTemplateModalOpen} onClose={() => setIsTemplateModalOpen(false)} title="Create Custom Template">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createTemplateMutation.mutate(templateForm);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Template Key</label>
            <Input
              value={templateForm.template_key}
              onChange={(e) => setTemplateForm({ ...templateForm, template_key: e.target.value })}
              placeholder="e.g. custom_exam_alert"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Template Name</label>
            <Input
              value={templateForm.name}
              onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
              placeholder="e.g. Custom Exam Notification"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Category</label>
            <select
              value={templateForm.category}
              onChange={(e) => setTemplateForm({ ...templateForm, category: e.target.value })}
              className="w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
            >
              <option value="ANNOUNCEMENT">Announcement</option>
              <option value="ATTENDANCE">Attendance</option>
              <option value="FEES">Fees</option>
              <option value="EXAMS">Exams</option>
              <option value="EVENTS">Events</option>
              <option value="HOSTEL">Hostel</option>
              <option value="LEAVE">Staff Leave</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Subject Template</label>
            <Input
              value={templateForm.title_template}
              onChange={(e) => setTemplateForm({ ...templateForm, title_template: e.target.value })}
              placeholder="e.g. Alert for {student_name}"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Body Template</label>
            <textarea
              value={templateForm.body_template}
              onChange={(e) => setTemplateForm({ ...templateForm, body_template: e.target.value })}
              className="w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              rows={3}
              required
            />
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <Button variant="outline" onClick={() => setIsTemplateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createTemplateMutation.isPending}>
              Save Template
            </Button>
          </div>
        </form>
      </Modal>

      {/* AI Communication Draft Assistant Modal */}
      <Modal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        title="AI Multi-Channel Communication Draft Assistant"
      >
        <div className="space-y-4">
          <div className="p-3 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 rounded-lg text-xs text-purple-900 dark:text-purple-200 flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
            <div>
              <strong>Non-Custodial AI Generator</strong>: Automatically composes channel-optimized draft variants (SMS $\le 160$ chars, WhatsApp markdown, Email formal body). PII is automatically redacted.
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Category</label>
              <select
                value={aiDraftForm.category}
                onChange={(e) => setAiDraftForm({ ...aiDraftForm, category: e.target.value })}
                className="w-full px-3 py-1.5 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              >
                <option value="ANNOUNCEMENT">General Announcement</option>
                <option value="ACADEMIC_NOTICE">Academic Notice</option>
                <option value="EMERGENCY_ALERT">Emergency Alert</option>
                <option value="EVENT_INVITATION">Event Invitation</option>
                <option value="PARENT_UPDATE">Parent Update</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Audience</label>
              <select
                value={aiDraftForm.target_audience}
                onChange={(e) => setAiDraftForm({ ...aiDraftForm, target_audience: e.target.value })}
                className="w-full px-3 py-1.5 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              >
                <option value="PARENTS">Parents</option>
                <option value="STUDENTS">Students</option>
                <option value="TEACHERS">Teachers</option>
                <option value="ALL_STAFF">All Staff</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Tone</label>
              <select
                value={aiDraftForm.tone}
                onChange={(e) => setAiDraftForm({ ...aiDraftForm, tone: e.target.value })}
                className="w-full px-3 py-1.5 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              >
                <option value="FORMAL">Formal</option>
                <option value="URGENT">Urgent</option>
                <option value="FRIENDLY">Friendly</option>
                <option value="ENCOURAGING">Encouraging</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Notice Details / Topic Summary</label>
            <textarea
              value={aiDraftForm.key_details}
              onChange={(e) => setAiDraftForm({ ...aiDraftForm, key_details: e.target.value })}
              placeholder="e.g. Greenwood Academy will remain closed on Friday Oct 15th for Staff Training. Classes resume Monday."
              className="w-full px-3 py-2 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
              rows={3}
            />
          </div>

          <div className="flex justify-end">
            <Button
              onClick={() => aiDraftMutation.mutate(aiDraftForm)}
              isLoading={aiDraftMutation.isPending}
              disabled={!aiDraftForm.key_details.trim()}
              className="flex items-center gap-2 text-xs"
            >
              <Sparkles className="w-3.5 h-3.5" /> Generate AI Multi-Channel Draft
            </Button>
          </div>

          {/* Generated Result Preview */}
          {aiDraftResult && (
            <div className="mt-4 pt-4 border-t border-stone-200 dark:border-stone-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-ink dark:text-stone-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Generated Draft Variants
                </span>
                <Badge variant="neutral">Tokens Used: {aiDraftResult.token_count}</Badge>
              </div>

              {aiDraftResult.pii_redact_log && aiDraftResult.pii_redact_log.length > 0 && (
                <div className="text-[11px] text-amber-600 bg-amber-50 dark:bg-amber-950/40 p-2 rounded border border-amber-200 dark:border-amber-800">
                  🛡️ <strong>PII Masked</strong>: {aiDraftResult.pii_redact_log.join(', ')} automatically redacted before AI processing.
                </div>
              )}

              {/* Channel Tabs */}
              <div className="flex space-x-1 border-b border-stone-200 dark:border-stone-800">
                {(['SMS', 'EMAIL', 'WHATSAPP', 'IN_APP'] as const).map((ch) => (
                  <button
                    key={ch}
                    type="button"
                    onClick={() => setAiSelectedChannel(ch)}
                    className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                      aiSelectedChannel === ch
                        ? 'border-purple-600 text-purple-600 dark:border-purple-400 dark:text-purple-400'
                        : 'border-transparent text-stone-500 hover:text-stone-700 dark:text-stone-400'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>

              {/* Selected Channel Variant Display */}
              {aiDraftResult.channel_variants[aiSelectedChannel] ? (
                <div className="p-3 bg-stone-50 dark:bg-stone-900/60 rounded-md border border-stone-200 dark:border-stone-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-semibold text-ink dark:text-stone-200">
                    <span>Title: {aiDraftResult.channel_variants[aiSelectedChannel].title}</span>
                    {aiSelectedChannel === 'SMS' && (
                      <Badge variant={aiDraftResult.channel_variants.SMS.body.length <= 160 ? 'success' : 'warning'}>
                        {aiDraftResult.channel_variants.SMS.body.length}/160 chars
                      </Badge>
                    )}
                  </div>
                  <div className="p-2.5 bg-white dark:bg-stone-950 rounded border border-stone-200 dark:border-stone-800 font-mono text-[11px] whitespace-pre-wrap text-stone-800 dark:text-stone-300">
                    {aiDraftResult.channel_variants[aiSelectedChannel].body}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-muted">No variant generated for {aiSelectedChannel}</div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <Button variant="outline" onClick={() => setIsAiModalOpen(false)} size="sm">
                  Close
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    const selectedVar = aiDraftResult.channel_variants[aiSelectedChannel];
                    if (selectedVar) {
                      setSendForm({
                        ...sendForm,
                        title: selectedVar.title,
                        message: selectedVar.body,
                        channel: aiSelectedChannel,
                      });
                      setIsAiModalOpen(false);
                      setIsSendModalOpen(true);
                    }
                  }}
                  className="bg-purple-600 hover:bg-purple-700 text-white flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" /> Use Draft in Composer
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};
