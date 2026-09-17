import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  communicationApi,
  NotificationItem,
  NotificationDetail,
  UserPreferences,
  NotificationTemplate,
  NotificationAnalytics,
} from '@/api/communication';
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
  BarChart3,
  Eye,
  Search,
  Calendar,
  Filter,
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

  const [activeTab, setActiveTab] = useState<'inbox' | 'preferences' | 'logs' | 'analytics' | 'templates' | 'providers'>('inbox');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');

  // Notification Detail Inspection State
  const [selectedNotificationId, setSelectedNotificationId] = useState<string | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

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
    queryKey: ['notification-logs', page, pageSize, statusFilter, channelFilter, eventTypeFilter, startDateFilter, endDateFilter, searchFilter],
    queryFn: () =>
      communicationApi.fetchDeliveryLogs({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
        event_type: eventTypeFilter || undefined,
        start_date: startDateFilter ? `${startDateFilter}T00:00:00Z` : undefined,
        end_date: endDateFilter ? `${endDateFilter}T23:59:59Z` : undefined,
        search: searchFilter || undefined,
      }),
    enabled: isCommunicationAdmin,
  });

  const analyticsQuery = useQuery({
    queryKey: ['notification-analytics', startDateFilter, endDateFilter],
    queryFn: () =>
      communicationApi.fetchNotificationAnalytics({
        start_date: startDateFilter ? `${startDateFilter}T00:00:00Z` : undefined,
        end_date: endDateFilter ? `${endDateFilter}T23:59:59Z` : undefined,
      }),
    enabled: isCommunicationAdmin,
  });

  const detailQuery = useQuery({
    queryKey: ['notification-detail', selectedNotificationId],
    queryFn: () => communicationApi.fetchNotificationDetail(selectedNotificationId!),
    enabled: !!selectedNotificationId && isDetailModalOpen,
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
      queryClient.invalidateQueries({ queryKey: ['notification-analytics'] });
      queryClient.invalidateQueries({ queryKey: ['notification-detail'] });
    },
  });

  const sendMutation = useMutation({
    mutationFn: communicationApi.sendAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-logs'] });
      queryClient.invalidateQueries({ queryKey: ['notification-analytics'] });
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

  const openNotificationDetail = (id: string) => {
    setSelectedNotificationId(id);
    setIsDetailModalOpen(true);
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
      key: 'template_key',
      header: 'Event / Type',
      render: (n) => (
        <Badge variant="neutral" className="font-mono text-[10px]">
          {n.template_key}
        </Badge>
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
        <div className="cursor-pointer" onClick={() => openNotificationDetail(n.id)}>
          <div className="font-semibold text-xs text-ink dark:text-stone-100 hover:text-brand-600 transition-colors">
            {n.title}
          </div>
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
      render: (n) => (
        <div className="flex items-center space-x-1.5">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => openNotificationDetail(n.id)}
            title="Inspect Details"
          >
            <Eye className="w-3.5 h-3.5 text-stone-600 dark:text-stone-400" />
          </Button>
          {n.status === 'FAILED' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => retryMutation.mutate(n.id)}
              isLoading={retryMutation.isPending}
              title="Retry Delivery"
            >
              <RefreshCw className="w-3 h-3 mr-1" /> Retry
            </Button>
          )}
        </div>
      ),
    },
  ];

  const prefs = preferencesQuery.data;
  const analytics = analyticsQuery.data;

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
            Multi-channel messaging platform, operational delivery monitoring, and tenant administration.
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
      {isCommunicationAdmin && analytics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Total Notifications</div>
            <div className="text-2xl font-bold text-ink dark:text-stone-100 mt-1">
              {analytics.total_notifications}
            </div>
            <div className="text-[11px] text-stone-500 mt-1">
              Success Rate: <span className="font-semibold text-emerald-600">{analytics.success_rate_percent}%</span>
            </div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Sent & Delivered</div>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {analytics.sent_count + analytics.delivered_count}
            </div>
            <div className="text-[11px] text-emerald-600 mt-1">Verified outbound dispatches</div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Failed Attempts</div>
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">
              {analytics.failed_count}
            </div>
            <div className="text-[11px] text-rose-600 mt-1">
              Failure rate: {analytics.failure_rate_percent}%
            </div>
          </Card>

          <Card className="p-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="text-xs text-muted dark:text-stone-400 font-medium">Channel Distribution</div>
            <div className="flex items-center space-x-2 mt-2 text-xs font-semibold">
              <span className="text-amber-500">IN:{analytics.by_channel.IN_APP || 0}</span>
              <span className="text-purple-500">EM:{analytics.by_channel.EMAIL || 0}</span>
              <span className="text-blue-500">SMS:{analytics.by_channel.SMS || 0}</span>
              <span className="text-emerald-500">WA:{analytics.by_channel.WHATSAPP || 0}</span>
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
              <FileCode className="w-4 h-4" /> Delivery Logs & History
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`pb-2 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 ${
                activeTab === 'analytics'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-muted hover:text-ink dark:text-stone-400'
              }`}
            >
              <BarChart3 className="w-4 h-4" /> Analytics & Reports
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
          <div className="flex flex-col gap-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <FileCode className="w-5 h-5 text-brand-500" /> Delivery History & Audit Trail
              </h3>
              <div className="text-xs text-muted">
                Total Records: <span className="font-semibold text-ink dark:text-stone-200">{logsQuery.data?.total ?? 0}</span>
              </div>
            </div>

            {/* Filter Toolbar */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2.5 pt-2 border-t border-stone-200 dark:border-stone-800">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-stone-400" />
                <input
                  type="text"
                  placeholder="Search recipient/title..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
                />
              </div>

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
                <option value="DELIVERED">Delivered</option>
                <option value="FAILED">Failed</option>
                <option value="PENDING">Pending</option>
                <option value="CANCELLED">Cancelled</option>
              </select>

              <select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                className="px-3 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
              >
                <option value="">All Event Types</option>
                <option value="visitor_checkin">Visitor Check-in</option>
                <option value="visitor_checkout">Visitor Check-out</option>
                <option value="fee_payment_received">Fee Payment Receipt</option>
                <option value="student_absence">Student Absence</option>
                <option value="homework_published">Homework Published</option>
                <option value="general_announcement">General Announcement</option>
                <option value="emergency_alert">Emergency Alert</option>
              </select>

              <div className="flex items-center space-x-1">
                <input
                  type="date"
                  value={startDateFilter}
                  onChange={(e) => setStartDateFilter(e.target.value)}
                  className="w-1/2 px-2 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
                  title="From Date"
                />
                <span className="text-muted text-xs">-</span>
                <input
                  type="date"
                  value={endDateFilter}
                  onChange={(e) => setEndDateFilter(e.target.value)}
                  className="w-1/2 px-2 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
                  title="To Date"
                />
              </div>
            </div>
          </div>

          <Table
            data={logsQuery.data?.items || []}
            columns={logsColumns}
            isLoading={logsQuery.isLoading}
            emptyText="No delivery logs match your active filters."
          />
        </Card>
      )}

      {/* ── TAB 3B: ANALYTICS & REPORTS ────────────────────────────────────────── */}
      {activeTab === 'analytics' && isCommunicationAdmin && (
        <div className="space-y-6">
          <Card className="p-6 space-y-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-brand-500" /> Communication Performance & Volume Analytics
                </h3>
                <p className="text-xs text-muted dark:text-stone-400 mt-1">
                  Database-aggregated operational metrics, channel mix, delivery success rates, and volume distribution.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="date"
                  value={startDateFilter}
                  onChange={(e) => setStartDateFilter(e.target.value)}
                  className="px-2.5 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
                />
                <span className="text-muted text-xs">to</span>
                <input
                  type="date"
                  value={endDateFilter}
                  onChange={(e) => setEndDateFilter(e.target.value)}
                  className="px-2.5 py-1.5 border border-stone-300 dark:border-stone-700 rounded-md text-xs bg-white dark:bg-stone-900"
                />
                {(startDateFilter || endDateFilter) && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setStartDateFilter('');
                      setEndDateFilter('');
                    }}
                  >
                    Reset
                  </Button>
                )}
              </div>
            </div>

            {analyticsQuery.isLoading ? (
              <div className="p-8 text-center text-muted">Calculating analytics...</div>
            ) : analytics ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Event Breakdown */}
                <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-3 bg-stone-50/50 dark:bg-stone-950/50">
                  <h4 className="font-bold text-xs uppercase text-brand-600 dark:text-brand-400">
                    Volume by Trigger Event
                  </h4>
                  {Object.keys(analytics.by_event).length === 0 ? (
                    <div className="text-xs text-muted">No events recorded in this period.</div>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(analytics.by_event).map(([evt, count]) => {
                        const pct = analytics.total_notifications > 0
                          ? Math.round((count / analytics.total_notifications) * 100)
                          : 0;
                        return (
                          <div key={evt} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-mono font-medium text-ink dark:text-stone-200">{evt}</span>
                              <span className="text-stone-500">{count} ({pct}%)</span>
                            </div>
                            <div className="w-full bg-stone-200 dark:bg-stone-800 h-2 rounded-full overflow-hidden">
                              <div className="bg-brand-500 h-full rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Channel Breakdown */}
                <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-3 bg-stone-50/50 dark:bg-stone-950/50">
                  <h4 className="font-bold text-xs uppercase text-brand-600 dark:text-brand-400">
                    Volume by Channel
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(analytics.by_channel).map(([ch, count]) => {
                      const pct = analytics.total_notifications > 0
                        ? Math.round((count / analytics.total_notifications) * 100)
                        : 0;
                      return (
                        <div key={ch} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-medium text-ink dark:text-stone-200 flex items-center gap-1.5">
                              {getChannelIcon(ch)} {ch}
                            </span>
                            <span className="text-stone-500">{count} ({pct}%)</span>
                          </div>
                          <div className="w-full bg-stone-200 dark:bg-stone-800 h-2 rounded-full overflow-hidden">
                            <div className="bg-blue-500 h-full rounded-full" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Daily Volume Timeline */}
                <div className="md:col-span-2 p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-3 bg-stone-50/50 dark:bg-stone-950/50">
                  <h4 className="font-bold text-xs uppercase text-brand-600 dark:text-brand-400">
                    Daily Notification Volume
                  </h4>
                  {analytics.daily_volume.length === 0 ? (
                    <div className="text-xs text-muted">No daily volume data available.</div>
                  ) : (
                    <div className="space-y-2">
                      <div className="grid grid-cols-4 text-xs font-semibold text-muted border-b border-stone-200 dark:border-stone-800 pb-1">
                        <span>Date</span>
                        <span>Total Volume</span>
                        <span className="text-emerald-600">Sent / Delivered</span>
                        <span className="text-rose-600">Failed</span>
                      </div>
                      {analytics.daily_volume.map((dv) => (
                        <div key={dv.date} className="grid grid-cols-4 text-xs font-mono py-1 border-b border-stone-100 dark:border-stone-900">
                          <span className="text-ink dark:text-stone-200">{dv.date}</span>
                          <span className="font-semibold">{dv.count}</span>
                          <span className="text-emerald-600 font-semibold">{dv.sent}</span>
                          <span className="text-rose-600 font-semibold">{dv.failed}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </Card>
        </div>
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

      {/* ── TAB 5: PROVIDER ADAPTERS & TENANT CONFIGURATION ──────────────────── */}
      {activeTab === 'providers' && isCommunicationAdmin && (
        <div className="space-y-6">
          <Card className="p-6 space-y-4 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div>
              <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <Server className="w-5 h-5 text-brand-500" /> Channel Provider Statuses
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

          {/* Tenant Provider Credentials & Settings Form */}
          <Card className="p-6 space-y-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
            <div className="flex items-center justify-between border-b border-stone-200 dark:border-stone-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" /> School Gateway Provider Configuration
                </h3>
                <p className="text-xs text-muted dark:text-stone-400 mt-1">
                  Configure gateway credentials and DLT metadata. Secrets are encrypted at rest and never rendered back in plaintext.
                </p>
              </div>
            </div>

            <ProviderConfigForm />
          </Card>
        </div>
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

      {/* Modal: Notification Detail Inspection */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedNotificationId(null);
        }}
        title="Notification Audit & Delivery Details"
      >
        {detailQuery.isLoading ? (
          <div className="p-8 text-center text-muted text-xs">Loading notification details...</div>
        ) : detailQuery.data ? (
          <div className="space-y-4 text-xs">
            {/* Header / Summary Status */}
            <div className="p-3 bg-stone-50 dark:bg-stone-900 rounded-lg border border-stone-200 dark:border-stone-800 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getChannelIcon(detailQuery.data.channel)}
                <span className="font-bold text-sm text-ink dark:text-stone-100">{detailQuery.data.channel}</span>
                <Badge variant="neutral" className="font-mono text-[10px]">
                  {detailQuery.data.template_key}
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusBadge(detailQuery.data.status)}
                {detailQuery.data.retry_count !== undefined && (
                  <span className="text-[10px] text-stone-500 font-mono">
                    ({detailQuery.data.retry_count}/{detailQuery.data.max_retries} Retries)
                  </span>
                )}
              </div>
            </div>

            {/* Recipient Details */}
            <div className="grid grid-cols-2 gap-3 p-3 border border-stone-200 dark:border-stone-800 rounded-lg">
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Recipient Name</span>
                <span className="font-medium text-ink dark:text-stone-200">{detailQuery.data.recipient_name}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Contact / Target</span>
                <span className="font-mono text-ink dark:text-stone-200">{detailQuery.data.recipient_contact}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Recipient Type</span>
                <span className="font-medium text-ink dark:text-stone-200">{detailQuery.data.recipient_type || 'N/A'}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Recipient UUID</span>
                <span className="font-mono text-[10px] text-stone-500">{detailQuery.data.recipient_id || 'None'}</span>
              </div>
            </div>

            {/* Payload */}
            <div className="space-y-1.5 p-3 border border-stone-200 dark:border-stone-800 rounded-lg">
              <span className="text-muted block text-[10px] uppercase font-semibold">Message Title</span>
              <div className="font-semibold text-ink dark:text-stone-100">{detailQuery.data.title}</div>
              <span className="text-muted block text-[10px] uppercase font-semibold pt-1">Message Body</span>
              <div className="p-2.5 bg-stone-50 dark:bg-stone-950 rounded border border-stone-200 dark:border-stone-800 font-mono text-[11px] whitespace-pre-wrap text-stone-800 dark:text-stone-300">
                {detailQuery.data.body}
              </div>
            </div>

            {/* Provider & Dispatch Info */}
            <div className="grid grid-cols-2 gap-3 p-3 border border-stone-200 dark:border-stone-800 rounded-lg">
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Provider</span>
                <span className="font-mono text-ink dark:text-stone-200">{detailQuery.data.provider_name || 'MOCK / Default'}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Provider Message ID</span>
                <span className="font-mono text-[11px] text-ink dark:text-stone-200">{detailQuery.data.provider_message_id || 'None'}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Created At</span>
                <span className="font-mono text-[11px]">{detailQuery.data.created_at ? new Date(detailQuery.data.created_at).toLocaleString() : 'N/A'}</span>
              </div>
              <div>
                <span className="text-muted block text-[10px] uppercase font-semibold">Sent At</span>
                <span className="font-mono text-[11px] text-emerald-600">{detailQuery.data.sent_at ? new Date(detailQuery.data.sent_at).toLocaleString() : 'Not Sent'}</span>
              </div>
            </div>

            {/* Error Message if Failed */}
            {detailQuery.data.error_message && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg text-rose-700 dark:text-rose-300">
                <span className="font-bold block text-[10px] uppercase">Error Log:</span>
                <span className="font-mono text-[11px]">{detailQuery.data.error_message}</span>
              </div>
            )}

            {/* Action Footer */}
            <div className="flex justify-between items-center pt-2">
              {detailQuery.data.idempotency_key && (
                <span className="text-[10px] text-muted font-mono truncate max-w-[200px]" title={detailQuery.data.idempotency_key}>
                  Key: {detailQuery.data.idempotency_key}
                </span>
              )}
              <div className="flex space-x-2 ml-auto">
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsDetailModalOpen(false);
                    setSelectedNotificationId(null);
                  }}
                  size="sm"
                >
                  Close
                </Button>
                {detailQuery.data.status === 'FAILED' && (
                  <Button
                    size="sm"
                    onClick={() => {
                      if (selectedNotificationId) {
                        retryMutation.mutate(selectedNotificationId);
                      }
                    }}
                    isLoading={retryMutation.isPending}
                    className="flex items-center gap-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Retry Dispatch
                  </Button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-muted text-xs">Notification record not found.</div>
        )}
      </Modal>
    </div>
  );
};

const ProviderConfigForm: React.FC = () => {
  const queryClient = useQueryClient();
  const configQuery = useQuery({
    queryKey: ['school-comm-config'],
    queryFn: communicationApi.fetchSchoolCommunicationConfig,
  });

  const [form, setForm] = useState({
    sms_provider: 'NONE',
    whatsapp_provider: 'NONE',
    sms_enabled: false,
    whatsapp_enabled: false,
    sms_api_key: '',
    sms_sender_id: '',
    sms_entity_id: '',
    whatsapp_access_token: '',
    whatsapp_phone_number_id: '',
    whatsapp_business_account_id: '',
  });

  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  React.useEffect(() => {
    if (configQuery.data) {
      setForm((prev) => ({
        ...prev,
        sms_provider: configQuery.data.sms_provider,
        whatsapp_provider: configQuery.data.whatsapp_provider,
        sms_enabled: configQuery.data.sms_enabled,
        whatsapp_enabled: configQuery.data.whatsapp_enabled,
        sms_sender_id: configQuery.data.sms_sender_id || '',
        sms_entity_id: configQuery.data.sms_entity_id || '',
        whatsapp_phone_number_id: configQuery.data.whatsapp_phone_number_id || '',
        whatsapp_business_account_id: configQuery.data.whatsapp_business_account_id || '',
        sms_api_key: '',
        whatsapp_access_token: '',
      }));
    }
  }, [configQuery.data]);

  const updateMutation = useMutation({
    mutationFn: communicationApi.updateSchoolCommunicationConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-comm-config'] });
      queryClient.invalidateQueries({ queryKey: ['provider-statuses'] });
      setSuccessMsg('Provider configuration updated and credentials encrypted successfully.');
      setTimeout(() => setSuccessMsg(null), 4000);
    },
  });

  if (configQuery.isLoading) return <div className="text-xs text-muted">Loading provider configuration...</div>;

  const cfg = configQuery.data;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {
      sms_provider: form.sms_provider,
      whatsapp_provider: form.whatsapp_provider,
      sms_enabled: form.sms_enabled,
      whatsapp_enabled: form.whatsapp_enabled,
      sms_sender_id: form.sms_sender_id,
      sms_entity_id: form.sms_entity_id,
      whatsapp_phone_number_id: form.whatsapp_phone_number_id,
      whatsapp_business_account_id: form.whatsapp_business_account_id,
    };
    if (form.sms_api_key.trim()) payload.sms_api_key = form.sms_api_key.trim();
    if (form.whatsapp_access_token.trim()) payload.whatsapp_access_token = form.whatsapp_access_token.trim();
    updateMutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {successMsg && <Alert type="success">{successMsg}</Alert>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SMS Provider Settings */}
        <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-4 bg-stone-50/50 dark:bg-stone-950/50">
          <div className="flex items-center justify-between border-b border-stone-200 dark:border-stone-800 pb-2">
            <span className="font-bold text-xs uppercase text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
              <Smartphone className="w-4 h-4" /> SMS Provider Configuration
            </span>
            <Badge variant={cfg?.sms_configured ? 'success' : 'neutral'}>
              {cfg?.sms_configured ? 'CONFIGURED' : 'NOT CONFIGURED'}
            </Badge>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">SMS Gateway</label>
            <select
              value={form.sms_provider}
              onChange={(e) => setForm({ ...form, sms_provider: e.target.value as any })}
              className="w-full px-3 py-2 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
            >
              <option value="NONE">Disabled / None</option>
              <option value="FAST2SMS">Fast2SMS (India)</option>
              <option value="TWILIO">Twilio SMS</option>
              <option value="MOCK">Mock Provider (Dev)</option>
            </select>
          </div>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.sms_enabled}
              onChange={(e) => setForm({ ...form, sms_enabled: e.target.checked })}
              className="w-4 h-4 rounded text-blue-600"
            />
            <span className="text-xs font-medium text-ink dark:text-stone-200">Enable SMS Dispatch</span>
          </label>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">
              SMS API Key / Token
              {cfg?.sms_api_key_masked && (
                <span className="ml-2 font-mono text-[10px] text-emerald-600 dark:text-emerald-400">
                  (Current: {cfg.sms_api_key_masked})
                </span>
              )}
            </label>
            <Input
              type="password"
              value={form.sms_api_key}
              onChange={(e) => setForm({ ...form, sms_api_key: e.target.value })}
              placeholder={cfg?.sms_configured ? 'Leave blank to keep current key' : 'Enter API Key'}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Sender / Header ID</label>
              <Input
                value={form.sms_sender_id}
                onChange={(e) => setForm({ ...form, sms_sender_id: e.target.value })}
                placeholder="e.g. SCHLOB"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">DLT Entity ID (India)</label>
              <Input
                value={form.sms_entity_id}
                onChange={(e) => setForm({ ...form, sms_entity_id: e.target.value })}
                placeholder="e.g. 170115..."
              />
            </div>
          </div>
        </div>

        {/* WhatsApp Provider Settings */}
        <div className="p-4 border border-stone-200 dark:border-stone-800 rounded-lg space-y-4 bg-stone-50/50 dark:bg-stone-950/50">
          <div className="flex items-center justify-between border-b border-stone-200 dark:border-stone-800 pb-2">
            <span className="font-bold text-xs uppercase text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
              <MessageSquare className="w-4 h-4" /> WhatsApp Gateway Configuration
            </span>
            <Badge variant={cfg?.whatsapp_configured ? 'success' : 'neutral'}>
              {cfg?.whatsapp_configured ? 'CONFIGURED' : 'NOT CONFIGURED'}
            </Badge>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">WhatsApp Gateway</label>
            <select
              value={form.whatsapp_provider}
              onChange={(e) => setForm({ ...form, whatsapp_provider: e.target.value as any })}
              className="w-full px-3 py-2 border rounded-md text-xs bg-white dark:bg-stone-900 border-stone-300 dark:border-stone-700"
            >
              <option value="NONE">Disabled / None</option>
              <option value="META_WHATSAPP_CLOUD">Meta WhatsApp Cloud API</option>
              <option value="TWILIO_WHATSAPP">Twilio WhatsApp</option>
              <option value="MOCK">Mock Provider (Dev)</option>
            </select>
          </div>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.whatsapp_enabled}
              onChange={(e) => setForm({ ...form, whatsapp_enabled: e.target.checked })}
              className="w-4 h-4 rounded text-emerald-600"
            />
            <span className="text-xs font-medium text-ink dark:text-stone-200">Enable WhatsApp Dispatch</span>
          </label>

          <div>
            <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">
              WhatsApp Access Token
              {cfg?.whatsapp_access_token_masked && (
                <span className="ml-2 font-mono text-[10px] text-emerald-600 dark:text-emerald-400">
                  (Current: {cfg.whatsapp_access_token_masked})
                </span>
              )}
            </label>
            <Input
              type="password"
              value={form.whatsapp_access_token}
              onChange={(e) => setForm({ ...form, whatsapp_access_token: e.target.value })}
              placeholder={cfg?.whatsapp_configured ? 'Leave blank to keep current token' : 'Enter Access Token'}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Phone Number ID</label>
              <Input
                value={form.whatsapp_phone_number_id}
                onChange={(e) => setForm({ ...form, whatsapp_phone_number_id: e.target.value })}
                placeholder="e.g. 1045..."
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink dark:text-stone-300 mb-1">Business Account ID</label>
              <Input
                value={form.whatsapp_business_account_id}
                onChange={(e) => setForm({ ...form, whatsapp_business_account_id: e.target.value })}
                placeholder="e.g. 2049..."
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <Button type="submit" isLoading={updateMutation.isPending} className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" /> Save Provider Configuration
        </Button>
      </div>
    </form>
  );
};

