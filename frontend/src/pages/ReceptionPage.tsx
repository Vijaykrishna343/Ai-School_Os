import React, { useEffect, useState } from 'react';
import {
  UserCheck,
  Building2,
  Search,
  Plus,
  LogOut,
  Eye,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
  Calendar,
  Phone,
  Mail,
  Shield,
  FileText,
  HelpCircle,
  RefreshCw,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { receptionApi } from '@/services/api/receptionApi';
import {
  HostType,
  IdProofType,
  ReceptionInquiry,
  ReceptionInquiryStatus,
  VisitorDetail,
  VisitorStatus,
  VisitorSummary,
} from '@/types/models';

export const ReceptionPage: React.FC = () => {
  const { user, permissions, roles } = useAuthStore();
  const isSuperAdmin =
    user?.is_super_admin ||
    roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');

  const hasPermission = (perm: string) => isSuperAdmin || permissions.includes(perm);

  const canViewVisitors = hasPermission('visitors.view');
  const canCheckInVisitors = hasPermission('visitors.checkin');
  const canCheckOutVisitors = hasPermission('visitors.checkout');

  const canViewInquiries = hasPermission('reception.view');
  const canCreateInquiry = hasPermission('reception.create');
  const canUpdateInquiry = hasPermission('reception.update');

  // State
  const [activeTab, setActiveTab] = useState<'overview' | 'visitors' | 'inquiries'>('overview');

  // Stats / Overview
  const [activeVisitorsCount, setActiveVisitorsCount] = useState<number>(0);
  const [todayCheckedOutCount, setTodayCheckedOutCount] = useState<number>(0);
  const [pendingInquiriesCount, setPendingInquiriesCount] = useState<number>(0);
  const [inProgressInquiriesCount, setInProgressInquiriesCount] = useState<number>(0);
  const [todayAppointmentsCount, setTodayAppointmentsCount] = useState<number>(0);

  // Visitors list
  const [visitors, setVisitors] = useState<VisitorSummary[]>([]);
  const [visitorStatusFilter, setVisitorStatusFilter] = useState<string>('CHECKED_IN');
  const [visitorSearch, setVisitorSearch] = useState<string>('');
  const [visitorPage, setVisitorPage] = useState<number>(1);
  const [visitorTotalPages, setVisitorTotalPages] = useState<number>(1);
  const [loadingVisitors, setLoadingVisitors] = useState<boolean>(false);

  // Visitor Details & Check-In / Check-Out Modals
  const [selectedVisitor, setSelectedVisitor] = useState<VisitorDetail | null>(null);
  const [showVisitorDetailModal, setShowVisitorDetailModal] = useState<boolean>(false);
  const [showCheckInModal, setShowCheckInModal] = useState<boolean>(false);
  const [checkoutTarget, setCheckoutTarget] = useState<VisitorSummary | null>(null);
  const [checkoutRemarks, setCheckoutRemarks] = useState<string>('');
  const [checkInSuccessGatePass, setCheckInSuccessGatePass] = useState<string | null>(null);

  // Check-In Form
  const [checkInForm, setCheckInForm] = useState({
    visitor_name: '',
    phone: '',
    email: '',
    id_proof_type: '' as IdProofType | '',
    id_proof_number: '',
    purpose: '',
    host_type: '' as HostType | '',
    host_id: '',
    remarks: '',
  });

  // Inquiries list
  const [inquiries, setInquiries] = useState<ReceptionInquiry[]>([]);
  const [inquiryStatusFilter, setInquiryStatusFilter] = useState<string>('');
  const [inquirySearch, setInquirySearch] = useState<string>('');
  const [inquiryPage, setInquiryPage] = useState<number>(1);
  const [inquiryTotalPages, setInquiryTotalPages] = useState<number>(1);
  const [loadingInquiries, setLoadingInquiries] = useState<boolean>(false);

  // Inquiry Modals
  const [showCreateInquiryModal, setShowCreateInquiryModal] = useState<boolean>(false);
  const [selectedInquiry, setSelectedInquiry] = useState<ReceptionInquiry | null>(null);
  const [showInquiryDetailModal, setShowInquiryDetailModal] = useState<boolean>(false);

  // Create Inquiry Form
  const [inquiryForm, setInquiryForm] = useState({
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    subject: '',
    details: '',
    host_type: '' as HostType | '',
    host_id: '',
    appointment_time: '',
    notes: '',
  });

  // Inquiry Update Status State
  const [updateInquiryStatus, setUpdateInquiryStatus] = useState<ReceptionInquiryStatus | ''>('');
  const [updateInquiryNotes, setUpdateInquiryNotes] = useState<string>('');

  // General Notification & Error State
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const todayStr = new Date().toISOString().split('T')[0];

  // Load Dashboard Counts
  const loadOverviewCounts = async () => {
    try {
      if (canViewVisitors) {
        const activeRes = await receptionApi.getVisitors({ status: 'CHECKED_IN', page_size: 1 });
        setActiveVisitorsCount(activeRes.total);

        const checkedOutRes = await receptionApi.getVisitors({
          status: 'CHECKED_OUT',
          start_date: todayStr,
          end_date: todayStr,
          page_size: 1,
        });
        setTodayCheckedOutCount(checkedOutRes.total);
      }

      if (canViewInquiries) {
        const pendingRes = await receptionApi.getInquiries({ status: 'PENDING', page_size: 1 });
        setPendingInquiriesCount(pendingRes.total);

        const inProgressRes = await receptionApi.getInquiries({ status: 'IN_PROGRESS', page_size: 1 });
        setInProgressInquiriesCount(inProgressRes.total);

        const apptRes = await receptionApi.getInquiries({ appointment_date: todayStr, page_size: 1 });
        setTodayAppointmentsCount(apptRes.total);
      }
    } catch (err: any) {
      // Ignore count fetch failures gracefully
    }
  };

  // Load Visitors
  const loadVisitors = async () => {
    if (!canViewVisitors) return;
    setLoadingVisitors(true);
    setErrorMessage(null);
    try {
      const res = await receptionApi.getVisitors({
        status: visitorStatusFilter || undefined,
        search: visitorSearch.trim() || undefined,
        page: visitorPage,
        page_size: 10,
      });
      setVisitors(res.items);
      setVisitorTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load visitors list');
    } finally {
      setLoadingVisitors(false);
    }
  };

  // Load Inquiries
  const loadInquiries = async () => {
    if (!canViewInquiries) return;
    setLoadingInquiries(true);
    setErrorMessage(null);
    try {
      const res = await receptionApi.getInquiries({
        status: inquiryStatusFilter || undefined,
        search: inquirySearch.trim() || undefined,
        page: inquiryPage,
        page_size: 10,
      });
      setInquiries(res.items);
      setInquiryTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load reception inquiries');
    } finally {
      setLoadingInquiries(false);
    }
  };

  useEffect(() => {
    loadOverviewCounts();
  }, []);

  useEffect(() => {
    if (activeTab === 'visitors' || activeTab === 'overview') {
      loadVisitors();
    }
    if (activeTab === 'inquiries' || activeTab === 'overview') {
      loadInquiries();
    }
  }, [activeTab, visitorStatusFilter, visitorSearch, visitorPage, inquiryStatusFilter, inquirySearch, inquiryPage]);

  // Handle Check-In Submit
  const handleCheckInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkInForm.visitor_name.trim() || !checkInForm.phone.trim() || !checkInForm.purpose.trim()) {
      setErrorMessage('Visitor Name, Phone Number, and Purpose are required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const payload = {
        visitor_name: checkInForm.visitor_name.trim(),
        phone: checkInForm.phone.trim(),
        email: checkInForm.email.trim() || undefined,
        id_proof_type: checkInForm.id_proof_type || undefined,
        id_proof_number: checkInForm.id_proof_number.trim() || undefined,
        purpose: checkInForm.purpose.trim(),
        host_type: checkInForm.host_type || undefined,
        host_id: checkInForm.host_id.trim() || undefined,
        remarks: checkInForm.remarks.trim() || undefined,
      };

      const newVisitor = await receptionApi.checkInVisitor(payload);
      setCheckInSuccessGatePass(newVisitor.pass_number || 'GENERATED');
      setSuccessMessage(`Visitor ${newVisitor.visitor_name} checked in successfully! Gate Pass: ${newVisitor.pass_number}`);
      setShowCheckInModal(false);
      setCheckInForm({
        visitor_name: '',
        phone: '',
        email: '',
        id_proof_type: '',
        id_proof_number: '',
        purpose: '',
        host_type: '',
        host_id: '',
        remarks: '',
      });
      loadVisitors();
      loadOverviewCounts();
    } catch (err: any) {
      setErrorMessage(err.message || 'Check-in failed. Please verify visitor identity details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Check-Out Submit
  const handleCheckOutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkoutTarget) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await receptionApi.checkOutVisitor(checkoutTarget.id, {
        remarks: checkoutRemarks.trim() || undefined,
      });
      setSuccessMessage(`Visitor ${checkoutTarget.visitor_name} checked out successfully.`);
      setCheckoutTarget(null);
      setCheckoutRemarks('');
      loadVisitors();
      loadOverviewCounts();
    } catch (err: any) {
      setErrorMessage(err.message || 'Check-out failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // View Visitor Details
  const handleViewVisitorDetail = async (id: string) => {
    setErrorMessage(null);
    try {
      const details = await receptionApi.getVisitor(id);
      setSelectedVisitor(details);
      setShowVisitorDetailModal(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to fetch visitor details.');
    }
  };

  // Handle Create Inquiry Submit
  const handleCreateInquirySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inquiryForm.contact_name.trim() || !inquiryForm.contact_phone.trim() || !inquiryForm.subject.trim()) {
      setErrorMessage('Contact Name, Phone, and Subject are required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const payload = {
        contact_name: inquiryForm.contact_name.trim(),
        contact_phone: inquiryForm.contact_phone.trim(),
        contact_email: inquiryForm.contact_email.trim() || undefined,
        subject: inquiryForm.subject.trim(),
        details: inquiryForm.details.trim() || undefined,
        host_type: inquiryForm.host_type || undefined,
        host_id: inquiryForm.host_id.trim() || undefined,
        appointment_time: inquiryForm.appointment_time ? new Date(inquiryForm.appointment_time).toISOString() : undefined,
        notes: inquiryForm.notes.trim() || undefined,
      };

      const newInquiry = await receptionApi.createInquiry(payload);
      setSuccessMessage(`Reception inquiry "${newInquiry.subject}" created successfully (Status: PENDING).`);
      setShowCreateInquiryModal(false);
      setInquiryForm({
        contact_name: '',
        contact_phone: '',
        contact_email: '',
        subject: '',
        details: '',
        host_type: '',
        host_id: '',
        appointment_time: '',
        notes: '',
      });
      loadInquiries();
      loadOverviewCounts();
    } catch (err: any) {
      setErrorMessage(err.message || 'Inquiry creation failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Inquiry Detail / Update Modal
  const handleOpenInquiryDetail = (inquiry: ReceptionInquiry) => {
    setSelectedInquiry(inquiry);
    setUpdateInquiryStatus(inquiry.status);
    setUpdateInquiryNotes(inquiry.notes || '');
    setShowInquiryDetailModal(true);
  };

  // Handle Update Inquiry Submit
  const handleUpdateInquirySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInquiry) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const payload: any = {};
      if (updateInquiryStatus && updateInquiryStatus !== selectedInquiry.status) {
        payload.status = updateInquiryStatus;
      }
      if (updateInquiryNotes !== (selectedInquiry.notes || '')) {
        payload.notes = updateInquiryNotes.trim();
      }

      if (Object.keys(payload).length === 0) {
        setShowInquiryDetailModal(false);
        return;
      }

      const updated = await receptionApi.updateInquiry(selectedInquiry.id, payload);
      setSuccessMessage(`Inquiry "${updated.subject}" status updated to ${updated.status}.`);
      setShowInquiryDetailModal(false);
      loadInquiries();
      loadOverviewCounts();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update inquiry status.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render Status Badge
  const renderVisitorStatusBadge = (status: VisitorStatus) => {
    switch (status) {
      case 'CHECKED_IN':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle className="w-3 h-3" /> Checked In
          </span>
        );
      case 'CHECKED_OUT':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300">
            <LogOut className="w-3 h-3" /> Checked Out
          </span>
        );
      case 'EXPECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
            <Clock className="w-3 h-3" /> Expected
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
            <XCircle className="w-3 h-3" /> Cancelled
          </span>
        );
      default:
        return <span className="text-xs text-ink-muted">{status}</span>;
    }
  };

  const renderInquiryStatusBadge = (status: ReceptionInquiryStatus) => {
    switch (status) {
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
            <Clock className="w-3 h-3" /> Pending
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
            <RefreshCw className="w-3 h-3 animate-spin" /> In Progress
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle className="w-3 h-3" /> Resolved
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
            <XCircle className="w-3 h-3" /> Cancelled
          </span>
        );
      default:
        return <span className="text-xs text-ink-muted">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-divider dark:border-stone-800 pb-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-brand-500" /> Reception Workstation
          </h1>
          <p className="text-xs text-ink-muted dark:text-stone-400 mt-1">
            Front-office operational desk for visitor check-in/out, security passes, and reception inquiries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {canCheckInVisitors && (
            <button
              onClick={() => {
                setErrorMessage(null);
                setShowCheckInModal(true);
              }}
              className="px-3.5 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 transition flex items-center gap-1.5 shadow-sm"
            >
              <UserCheck className="w-4 h-4" /> Check-In Visitor
            </button>
          )}

          {canCreateInquiry && (
            <button
              onClick={() => {
                setErrorMessage(null);
                setShowCreateInquiryModal(true);
              }}
              className="px-3.5 py-2 text-xs font-semibold rounded-md bg-stone-800 text-white hover:bg-stone-900 dark:bg-stone-700 dark:hover:bg-stone-600 transition flex items-center gap-1.5 shadow-sm"
            >
              <Plus className="w-4 h-4" /> Log Inquiry
            </button>
          )}
        </div>
      </div>

      {/* Global Alerts */}
      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/50 dark:border-rose-900 dark:text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-700">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/50 dark:border-emerald-900 dark:text-emerald-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-500 hover:text-emerald-700">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center border-b border-divider dark:border-stone-800 text-xs font-medium space-x-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 transition-colors border-b-2 font-semibold ${
            activeTab === 'overview'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400'
          }`}
        >
          Daily Overview
        </button>
        {canViewVisitors && (
          <button
            onClick={() => setActiveTab('visitors')}
            className={`pb-3 transition-colors border-b-2 font-semibold ${
              activeTab === 'visitors'
                ? 'border-brand-500 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400'
            }`}
          >
            Campus Visitors
          </button>
        )}
        {canViewInquiries && (
          <button
            onClick={() => setActiveTab('inquiries')}
            className={`pb-3 transition-colors border-b-2 font-semibold ${
              activeTab === 'inquiries'
                ? 'border-brand-500 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400'
            }`}
          >
            Inquiries & Appointments
          </button>
        )}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-muted dark:text-stone-400">Active Visitors</span>
                <span className="p-2 rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
                  <UserCheck className="w-4 h-4" />
                </span>
              </div>
              <p className="text-2xl font-bold text-ink dark:text-stone-100 mt-2">{activeVisitorsCount}</p>
              <p className="text-[10px] text-ink-muted dark:text-stone-500 mt-1">Currently inside campus</p>
            </div>

            <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-muted dark:text-stone-400">Checked Out Today</span>
                <span className="p-2 rounded-lg bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-400">
                  <LogOut className="w-4 h-4" />
                </span>
              </div>
              <p className="text-2xl font-bold text-ink dark:text-stone-100 mt-2">{todayCheckedOutCount}</p>
              <p className="text-[10px] text-ink-muted dark:text-stone-500 mt-1">Departed campus today</p>
            </div>

            <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-muted dark:text-stone-400">Pending Inquiries</span>
                <span className="p-2 rounded-lg bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
                  <Clock className="w-4 h-4" />
                </span>
              </div>
              <p className="text-2xl font-bold text-ink dark:text-stone-100 mt-2">{pendingInquiriesCount}</p>
              <p className="text-[10px] text-ink-muted dark:text-stone-500 mt-1">Awaiting action</p>
            </div>

            <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-muted dark:text-stone-400">In-Progress</span>
                <span className="p-2 rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
                  <RefreshCw className="w-4 h-4" />
                </span>
              </div>
              <p className="text-2xl font-bold text-ink dark:text-stone-100 mt-2">{inProgressInquiriesCount}</p>
              <p className="text-[10px] text-ink-muted dark:text-stone-500 mt-1">Active resolution</p>
            </div>

            <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-muted dark:text-stone-400">Today's Appointments</span>
                <span className="p-2 rounded-lg bg-purple-50 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400">
                  <Calendar className="w-4 h-4" />
                </span>
              </div>
              <p className="text-2xl font-bold text-ink dark:text-stone-100 mt-2">{todayAppointmentsCount}</p>
              <p className="text-[10px] text-ink-muted dark:text-stone-500 mt-1">Scheduled for today</p>
            </div>
          </div>

          {/* Quick Active Visitors Snapshot */}
          <div className="p-5 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-ink dark:text-stone-100 flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-600" /> Active Campus Visitors Snapshot
              </h2>
              {canViewVisitors && (
                <button
                  onClick={() => setActiveTab('visitors')}
                  className="text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
                >
                  View All Visitors →
                </button>
              )}
            </div>

            {loadingVisitors ? (
              <div className="p-6 text-center text-xs text-ink-muted">Loading active visitors...</div>
            ) : visitors.length === 0 ? (
              <div className="p-6 text-center text-xs text-ink-muted">No visitors currently checked in.</div>
            ) : (
              <div className="divide-y divide-divider dark:divide-stone-800">
                {visitors.slice(0, 5).map((v) => (
                  <div key={v.id} className="py-3 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-ink dark:text-stone-200 flex items-center gap-2">
                        <span>{v.visitor_name}</span>
                        <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300">
                          {v.pass_number || 'NO-PASS'}
                        </span>
                      </div>
                      <div className="text-ink-muted dark:text-stone-400 text-[11px] mt-0.5">
                        Purpose: {v.purpose} • Phone: {v.phone}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-ink-muted text-[11px]">
                        In: {v.check_in_time ? new Date(v.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                      </span>
                      {canCheckOutVisitors && v.status === 'CHECKED_IN' && (
                        <button
                          onClick={() => setCheckoutTarget(v)}
                          className="px-2.5 py-1 text-xs font-medium rounded bg-rose-50 text-rose-700 hover:bg-rose-100 dark:bg-rose-950/60 dark:text-rose-300 dark:hover:bg-rose-900 transition"
                        >
                          Check Out
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Visitors */}
      {activeTab === 'visitors' && (
        <div className="space-y-4">
          {/* Filter Toolbar */}
          <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <input
                  type="text"
                  placeholder="Search name, phone, pass #..."
                  value={visitorSearch}
                  onChange={(e) => setVisitorSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <select
                value={visitorStatusFilter}
                onChange={(e) => setVisitorStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">All Statuses</option>
                <option value="CHECKED_IN">Checked In</option>
                <option value="CHECKED_OUT">Checked Out</option>
                <option value="EXPECTED">Expected</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            <div className="text-xs text-ink-muted">
              Showing page {visitorPage} of {visitorTotalPages}
            </div>
          </div>

          {/* Table */}
          <div className="rounded-xl border border-divider dark:border-stone-800 overflow-hidden bg-paper dark:bg-stone-900 shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-paper-dim dark:bg-stone-800/60 border-b border-divider dark:border-stone-800 text-ink-muted dark:text-stone-400 font-medium">
                    <th className="p-3">Gate Pass</th>
                    <th className="p-3">Visitor Name</th>
                    <th className="p-3">Phone</th>
                    <th className="p-3">Purpose</th>
                    <th className="p-3">Host Type</th>
                    <th className="p-3">Check-In Time</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-divider dark:divide-stone-800 text-ink dark:text-stone-200">
                  {loadingVisitors ? (
                    <tr>
                      <td colSpan={8} className="p-6 text-center text-ink-muted">
                        Loading visitors data...
                      </td>
                    </tr>
                  ) : visitors.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-6 text-center text-ink-muted">
                        No visitor records found.
                      </td>
                    </tr>
                  ) : (
                    visitors.map((v) => (
                      <tr key={v.id} className="hover:bg-paper-dim/50 dark:hover:bg-stone-800/40 transition">
                        <td className="p-3 font-mono font-semibold text-brand-600 dark:text-brand-400">
                          {v.pass_number || 'N/A'}
                        </td>
                        <td className="p-3 font-medium">{v.visitor_name}</td>
                        <td className="p-3">{v.phone}</td>
                        <td className="p-3 truncate max-w-xs">{v.purpose}</td>
                        <td className="p-3">
                          {v.host_type ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300">
                              {v.host_type}
                            </span>
                          ) : (
                            <span className="text-ink-muted">-</span>
                          )}
                        </td>
                        <td className="p-3">
                          {v.check_in_time ? new Date(v.check_in_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '-'}
                        </td>
                        <td className="p-3">{renderVisitorStatusBadge(v.status)}</td>
                        <td className="p-3 text-right space-x-2">
                          <button
                            onClick={() => handleViewVisitorDetail(v.id)}
                            className="p-1.5 rounded text-stone-600 hover:bg-stone-100 dark:text-stone-400 dark:hover:bg-stone-800"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {canCheckOutVisitors && v.status === 'CHECKED_IN' && (
                            <button
                              onClick={() => setCheckoutTarget(v)}
                              className="px-2 py-1 text-[11px] font-semibold rounded bg-rose-50 text-rose-700 hover:bg-rose-100 dark:bg-rose-950/60 dark:text-rose-300"
                            >
                              Check Out
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-3 border-t border-divider dark:border-stone-800 flex items-center justify-between text-xs">
              <button
                disabled={visitorPage <= 1}
                onClick={() => setVisitorPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 rounded border border-divider dark:border-stone-700 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-ink-muted">Page {visitorPage} of {visitorTotalPages}</span>
              <button
                disabled={visitorPage >= visitorTotalPages}
                onClick={() => setVisitorPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-divider dark:border-stone-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Inquiries & Appointments */}
      {activeTab === 'inquiries' && (
        <div className="space-y-4">
          {/* Filter Toolbar */}
          <div className="p-4 rounded-xl bg-paper dark:bg-stone-900 border border-divider dark:border-stone-800 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <input
                  type="text"
                  placeholder="Search contact, phone, subject..."
                  value={inquirySearch}
                  onChange={(e) => setInquirySearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <select
                value={inquiryStatusFilter}
                onChange={(e) => setInquiryStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            <div className="text-xs text-ink-muted">
              Page {inquiryPage} of {inquiryTotalPages}
            </div>
          </div>

          {/* Table */}
          <div className="rounded-xl border border-divider dark:border-stone-800 overflow-hidden bg-paper dark:bg-stone-900 shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-paper-dim dark:bg-stone-800/60 border-b border-divider dark:border-stone-800 text-ink-muted dark:text-stone-400 font-medium">
                    <th className="p-3">Contact Name</th>
                    <th className="p-3">Phone</th>
                    <th className="p-3">Subject</th>
                    <th className="p-3">Host Type</th>
                    <th className="p-3">Appointment Time</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-divider dark:divide-stone-800 text-ink dark:text-stone-200">
                  {loadingInquiries ? (
                    <tr>
                      <td colSpan={7} className="p-6 text-center text-ink-muted">
                        Loading reception inquiries...
                      </td>
                    </tr>
                  ) : inquiries.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-6 text-center text-ink-muted">
                        No reception inquiry records found.
                      </td>
                    </tr>
                  ) : (
                    inquiries.map((inq) => (
                      <tr key={inq.id} className="hover:bg-paper-dim/50 dark:hover:bg-stone-800/40 transition">
                        <td className="p-3 font-medium">{inq.contact_name}</td>
                        <td className="p-3">{inq.contact_phone}</td>
                        <td className="p-3 truncate max-w-xs font-semibold">{inq.subject}</td>
                        <td className="p-3">
                          {inq.host_type ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300">
                              {inq.host_type}
                            </span>
                          ) : (
                            <span className="text-ink-muted">-</span>
                          )}
                        </td>
                        <td className="p-3">
                          {inq.appointment_time ? new Date(inq.appointment_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '-'}
                        </td>
                        <td className="p-3">{renderInquiryStatusBadge(inq.status)}</td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleOpenInquiryDetail(inq)}
                            className="px-2.5 py-1 text-[11px] font-semibold rounded bg-stone-100 text-stone-700 hover:bg-stone-200 dark:bg-stone-800 dark:text-stone-300"
                          >
                            {canUpdateInquiry && inq.status !== 'RESOLVED' && inq.status !== 'CANCELLED' ? 'Manage' : 'View'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="p-3 border-t border-divider dark:border-stone-800 flex items-center justify-between text-xs">
              <button
                disabled={inquiryPage <= 1}
                onClick={() => setInquiryPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 rounded border border-divider dark:border-stone-700 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-ink-muted">Page {inquiryPage} of {inquiryTotalPages}</span>
              <button
                disabled={inquiryPage >= inquiryTotalPages}
                onClick={() => setInquiryPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-divider dark:border-stone-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: CHECK-IN VISITOR */}
      {/* ========================================================================= */}
      {showCheckInModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/60 p-4">
          <div className="bg-paper dark:bg-stone-900 rounded-xl border border-divider dark:border-stone-800 max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
              <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-brand-500" /> Campus Visitor Check-In
              </h3>
              <button onClick={() => setShowCheckInModal(false)} className="text-ink-muted hover:text-ink">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCheckInSubmit} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">
                    Visitor Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={checkInForm.visitor_name}
                    onChange={(e) => setCheckInForm({ ...checkInForm, visitor_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                    placeholder="Full Name"
                  />
                </div>

                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">
                    Phone Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={checkInForm.phone}
                    onChange={(e) => setCheckInForm({ ...checkInForm, phone: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                    placeholder="+91 98765 43210"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Purpose of Visit <span className="text-rose-500">*</span></label>
                <input
                  type="text"
                  required
                  value={checkInForm.purpose}
                  onChange={(e) => setCheckInForm({ ...checkInForm, purpose: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="e.g. Parent-Teacher Meeting, Fee Payment, Vendor Delivery"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">ID Proof Type</label>
                  <select
                    value={checkInForm.id_proof_type}
                    onChange={(e) => setCheckInForm({ ...checkInForm, id_proof_type: e.target.value as IdProofType })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  >
                    <option value="">None Selected</option>
                    <option value="AADHAAR">Aadhaar Card</option>
                    <option value="DRIVING_LICENSE">Driving License</option>
                    <option value="PASSPORT">Passport</option>
                    <option value="VOTER_ID">Voter ID</option>
                    <option value="OTHER">Other Govt ID</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">ID Proof Number</label>
                  <input
                    type="text"
                    value={checkInForm.id_proof_number}
                    onChange={(e) => setCheckInForm({ ...checkInForm, id_proof_number: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                    placeholder="Document Identifier"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Host Entity Type</label>
                  <select
                    value={checkInForm.host_type}
                    onChange={(e) => setCheckInForm({ ...checkInForm, host_type: e.target.value as HostType })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  >
                    <option value="">No Host Specified</option>
                    <option value="TEACHER">Teacher / Faculty</option>
                    <option value="STAFF">Staff / Admin</option>
                    <option value="STUDENT">Student</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Host Entity ID</label>
                  <input
                    type="text"
                    value={checkInForm.host_id}
                    onChange={(e) => setCheckInForm({ ...checkInForm, host_id: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100 font-mono text-[11px]"
                    placeholder="Host UUID (Optional)"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={checkInForm.email}
                  onChange={(e) => setCheckInForm({ ...checkInForm, email: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="visitor@example.com"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-divider dark:border-stone-800">
                <button
                  type="button"
                  onClick={() => setShowCheckInModal(false)}
                  className="px-3.5 py-1.5 rounded text-stone-600 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded bg-brand-500 text-white font-semibold hover:bg-brand-600 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Checking In...' : 'Confirm & Issue Gate Pass'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: CHECK-OUT CONFIRMATION */}
      {/* ========================================================================= */}
      {checkoutTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/60 p-4">
          <div className="bg-paper dark:bg-stone-900 rounded-xl border border-divider dark:border-stone-800 max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
              <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <LogOut className="w-5 h-5 text-rose-500" /> Confirm Visitor Departure
              </h3>
              <button onClick={() => setCheckoutTarget(null)} className="text-ink-muted hover:text-ink">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs space-y-2 bg-paper-dim dark:bg-stone-800/50 p-3 rounded-lg border border-divider dark:border-stone-800">
              <div>
                <span className="text-ink-muted">Visitor: </span>
                <span className="font-semibold">{checkoutTarget.visitor_name}</span>
              </div>
              <div>
                <span className="text-ink-muted">Pass Number: </span>
                <span className="font-mono font-semibold text-brand-600">{checkoutTarget.pass_number || 'N/A'}</span>
              </div>
              <div>
                <span className="text-ink-muted">Purpose: </span>
                <span>{checkoutTarget.purpose}</span>
              </div>
            </div>

            <form onSubmit={handleCheckOutSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Departure Remarks (Optional)</label>
                <input
                  type="text"
                  value={checkoutRemarks}
                  onChange={(e) => setCheckoutRemarks(e.target.value)}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="e.g. Returned pass badge, departed main gate"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-divider dark:border-stone-800">
                <button
                  type="button"
                  onClick={() => setCheckoutTarget(null)}
                  className="px-3.5 py-1.5 rounded text-stone-600 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded bg-rose-600 text-white font-semibold hover:bg-rose-700 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Processing...' : 'Complete Check-Out'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: VISITOR DETAIL DRAWER */}
      {/* ========================================================================= */}
      {showVisitorDetailModal && selectedVisitor && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-stone-950/60 p-4">
          <div className="bg-paper dark:bg-stone-900 h-full max-w-md w-full p-6 shadow-xl border-l border-divider dark:border-stone-800 overflow-y-auto space-y-5">
            <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
              <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <Shield className="w-5 h-5 text-brand-500" /> Visitor Identity Dossier
              </h3>
              <button onClick={() => setShowVisitorDetailModal(false)} className="text-ink-muted hover:text-ink">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-paper-dim dark:bg-stone-800/60 border border-divider dark:border-stone-800 space-y-2">
                <div className="text-lg font-bold text-ink dark:text-stone-100">{selectedVisitor.visitor_name}</div>
                <div className="flex items-center gap-2 text-brand-600 font-mono font-semibold">
                  Gate Pass: {selectedVisitor.pass_number || 'N/A'}
                </div>
                <div>{renderVisitorStatusBadge(selectedVisitor.status)}</div>
              </div>

              <div className="space-y-3 divide-y divide-divider dark:divide-stone-800">
                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Phone Number</div>
                  <div className="font-medium flex items-center gap-1.5"><Phone className="w-3.5 h-3.5" /> {selectedVisitor.phone}</div>
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Email</div>
                  <div className="font-medium flex items-center gap-1.5"><Mail className="w-3.5 h-3.5" /> {selectedVisitor.email || 'Not provided'}</div>
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Purpose of Visit</div>
                  <div className="font-semibold text-ink dark:text-stone-200">{selectedVisitor.purpose}</div>
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Identity Proof (Authorized View)</div>
                  <div className="font-mono text-stone-700 dark:text-stone-300">
                    Type: {selectedVisitor.id_proof_type || 'None'} • Number: {selectedVisitor.id_proof_number || 'Masked / Not recorded'}
                  </div>
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Host Entity Linkage</div>
                  <div>
                    Host Type: {selectedVisitor.host_type || 'General Reception'}
                  </div>
                  {selectedVisitor.host_id && (
                    <div className="font-mono text-[10px] text-ink-muted">ID: {selectedVisitor.host_id}</div>
                  )}
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Check-In Timestamp</div>
                  <div>{selectedVisitor.check_in_time ? new Date(selectedVisitor.check_in_time).toLocaleString() : 'Pending'}</div>
                </div>

                <div className="pt-2 space-y-1">
                  <div className="text-ink-muted">Check-Out Timestamp</div>
                  <div>{selectedVisitor.check_out_time ? new Date(selectedVisitor.check_out_time).toLocaleString() : 'Not checked out'}</div>
                </div>

                {selectedVisitor.remarks && (
                  <div className="pt-2 space-y-1">
                    <div className="text-ink-muted">Reception Remarks</div>
                    <div className="italic text-stone-600 dark:text-stone-400">{selectedVisitor.remarks}</div>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-divider dark:border-stone-800">
              <button
                onClick={() => setShowVisitorDetailModal(false)}
                className="w-full py-2 rounded bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 font-semibold hover:bg-stone-200"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 4: CREATE RECEPTION INQUIRY */}
      {/* ========================================================================= */}
      {showCreateInquiryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/60 p-4">
          <div className="bg-paper dark:bg-stone-900 rounded-xl border border-divider dark:border-stone-800 max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
              <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <FileText className="w-5 h-5 text-brand-500" /> Log Reception Inquiry / Appointment
              </h3>
              <button onClick={() => setShowCreateInquiryModal(false)} className="text-ink-muted hover:text-ink">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateInquirySubmit} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">
                    Contact Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={inquiryForm.contact_name}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, contact_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                    placeholder="Full Name"
                  />
                </div>

                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">
                    Phone Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={inquiryForm.contact_phone}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, contact_phone: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                    placeholder="+91 98765 43210"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">
                  Inquiry Subject <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={inquiryForm.subject}
                  onChange={(e) => setInquiryForm({ ...inquiryForm, subject: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="e.g. Admission Inquiry Grade 5, Fee Structure Clarification"
                />
              </div>

              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Details & Remarks</label>
                <textarea
                  rows={2}
                  value={inquiryForm.details}
                  onChange={(e) => setInquiryForm({ ...inquiryForm, details: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="Additional context or caller details..."
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Target Host Type</label>
                  <select
                    value={inquiryForm.host_type}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, host_type: e.target.value as HostType })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  >
                    <option value="">None Specified</option>
                    <option value="TEACHER">Teacher</option>
                    <option value="STAFF">Staff</option>
                    <option value="STUDENT">Student</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Appointment Time</label>
                  <input
                    type="datetime-local"
                    value={inquiryForm.appointment_time}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, appointment_time: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-divider dark:border-stone-800">
                <button
                  type="button"
                  onClick={() => setShowCreateInquiryModal(false)}
                  className="px-3.5 py-1.5 rounded text-stone-600 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded bg-brand-500 text-white font-semibold hover:bg-brand-600 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Log Inquiry (PENDING)'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 5: INQUIRY STATUS MANAGEMENT & DETAILS */}
      {/* ========================================================================= */}
      {showInquiryDetailModal && selectedInquiry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/60 p-4">
          <div className="bg-paper dark:bg-stone-900 rounded-xl border border-divider dark:border-stone-800 max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
              <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100 flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-brand-500" /> Inquiry Status & Resolution
              </h3>
              <button onClick={() => setShowInquiryDetailModal(false)} className="text-ink-muted hover:text-ink">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs space-y-3 p-3 rounded-lg bg-paper-dim dark:bg-stone-800/50 border border-divider dark:border-stone-800">
              <div>
                <span className="text-ink-muted">Subject: </span>
                <span className="font-bold text-ink dark:text-stone-100">{selectedInquiry.subject}</span>
              </div>
              <div>
                <span className="text-ink-muted">Contact: </span>
                <span>{selectedInquiry.contact_name} ({selectedInquiry.contact_phone})</span>
              </div>
              {selectedInquiry.details && (
                <div>
                  <span className="text-ink-muted">Details: </span>
                  <span>{selectedInquiry.details}</span>
                </div>
              )}
              <div>
                <span className="text-ink-muted">Current Status: </span>
                {renderInquiryStatusBadge(selectedInquiry.status)}
              </div>
            </div>

            <form onSubmit={handleUpdateInquirySubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">State Machine Status Transition</label>
                {selectedInquiry.status === 'RESOLVED' || selectedInquiry.status === 'CANCELLED' ? (
                  <div className="p-2.5 rounded bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300 text-xs italic">
                    This inquiry is in a terminal state ({selectedInquiry.status}). No further state transitions allowed.
                  </div>
                ) : (
                  <select
                    value={updateInquiryStatus}
                    onChange={(e) => setUpdateInquiryStatus(e.target.value as ReceptionInquiryStatus)}
                    disabled={!canUpdateInquiry}
                    className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  >
                    {selectedInquiry.status === 'PENDING' && <option value="PENDING">PENDING (Keep Active)</option>}
                    <option value="IN_PROGRESS">IN_PROGRESS (Mark Under Review)</option>
                    <option value="RESOLVED">RESOLVED (Complete Inquiry)</option>
                    <option value="CANCELLED">CANCELLED (Cancel Inquiry)</option>
                  </select>
                )}
              </div>

              <div>
                <label className="block font-medium text-ink-muted dark:text-stone-300 mb-1">Resolution Notes</label>
                <textarea
                  rows={3}
                  value={updateInquiryNotes}
                  onChange={(e) => setUpdateInquiryNotes(e.target.value)}
                  disabled={!canUpdateInquiry}
                  className="w-full px-3 py-1.5 rounded border border-divider dark:border-stone-700 bg-paper-dim dark:bg-stone-800 text-ink dark:text-stone-100"
                  placeholder="Record resolution steps or receptionist notes..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-divider dark:border-stone-800">
                <button
                  type="button"
                  onClick={() => setShowInquiryDetailModal(false)}
                  className="px-3.5 py-1.5 rounded text-stone-600 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                >
                  Close
                </button>
                {canUpdateInquiry && selectedInquiry.status !== 'RESOLVED' && selectedInquiry.status !== 'CANCELLED' && (
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-1.5 rounded bg-brand-500 text-white font-semibold hover:bg-brand-600 transition disabled:opacity-50"
                  >
                    {isSubmitting ? 'Updating...' : 'Save Updates'}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
