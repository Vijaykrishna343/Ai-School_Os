import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  dashboardApi,
  feesApi,
  paymentsApi,
  reportCardsApi,
  homeworkApi,
  timetableApi,
  libraryApi,
} from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import {
  Building2,
  Users,
  GraduationCap,
  CalendarCheck,
  CreditCard,
  BookOpen,
  Award,
  Bell,
  AlertCircle,
  ChevronRight,
  Clock,
  CheckCircle2,
  FileText,
  DollarSign,
  Download,
  X,
  Send,
  BookMarked,
  ShieldCheck,
  Printer,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, permissions } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedChildId, setSelectedChildId] = useState<string | undefined>(undefined);

  // Modal States
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false);
  const [selectedPaymentId, setSelectedPaymentId] = useState<string | null>(null);
  const [isReportCardModalOpen, setIsReportCardModalOpen] = useState(false);
  const [selectedHomework, setSelectedHomework] = useState<any | null>(null);
  const [isHomeworkModalOpen, setIsHomeworkModalOpen] = useState(false);
  const [submissionText, setSubmissionText] = useState('');
  const [selectedGateway, setSelectedGateway] = useState<'RAZORPAY' | 'STRIPE' | 'MOCK'>('MOCK');
  const [paymentStep, setPaymentStep] = useState<'REVIEW' | 'PROCESSING' | 'SUCCESS' | 'ERROR'>('REVIEW');
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [lastReceipt, setLastReceipt] = useState<any | null>(null);

  const roleNames: string[] = (user as any)?.roles?.map((r: any) => (typeof r === 'string' ? r : r?.name)) || [];
  const isParent = roleNames.includes('Parent') || permissions.includes('dashboard.parent.view');
  const isStudent = roleNames.includes('Student') || permissions.includes('dashboard.student.view');
  const isAdmin = permissions.includes('school.view') || permissions.includes('school.update') || roleNames.includes('Admin') || roleNames.includes('SuperAdmin');
  const isTeacher = !isAdmin && !isParent && !isStudent;

  const mode = isAdmin ? 'admin' : isTeacher ? 'teacher' : isParent ? 'parent' : 'student';

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboardSummary', mode, selectedChildId],
    queryFn: async () => {
      if (isAdmin) return await dashboardApi.getAdminSummary();
      if (isTeacher) return await dashboardApi.getTeacherSummary();
      if (isParent) return await dashboardApi.getParentSummary(selectedChildId);
      return await dashboardApi.getStudentSummary();
    },
  });

  const activeChildId = selectedChildId || summary?.selected_child_id;

  const { data: feeAssignmentsData } = useQuery({
    queryKey: ['parentFeeAssignments', activeChildId],
    queryFn: async () => {
      if (!isParent || !activeChildId) return null;
      return await feesApi.getStudentFeeAssignments({ student_id: activeChildId });
    },
    enabled: isParent && !!activeChildId,
  });

  const activeAssignment = feeAssignmentsData?.items?.[0];

  // Query Fee Payments for Active Assignment
  const { data: paymentsData } = useQuery({
    queryKey: ['parentFeePayments', activeAssignment?.id],
    queryFn: async () => {
      if (!activeAssignment?.id) return null;
      return await feesApi.getFeePayments({ assignment_id: activeAssignment.id });
    },
    enabled: !!activeAssignment?.id,
  });

  // Query Published Report Cards for Parent's Active Child or Student
  const targetReportCardStudentId = isParent ? activeChildId : summary?.student_info?.id;
  const { data: reportCardsData } = useQuery({
    queryKey: ['publishedReportCards', targetReportCardStudentId],
    queryFn: async () => {
      if (!targetReportCardStudentId) return null;
      return await reportCardsApi.getReportCards({
        student_id: targetReportCardStudentId,
        status: 'PUBLISHED' as any,
      });
    },
    enabled: (isParent || isStudent) && !!targetReportCardStudentId,
  });

  // Query Student's Section Timetable
  const studentSectionId = summary?.student_info?.section_name
    ? summary?.student_info?.id // Section will be fetched from timetable
    : undefined;

  const { data: studentTimetable } = useQuery({
    queryKey: ['studentTimetable', summary?.student_info?.id],
    queryFn: async () => {
      if (!isStudent) return null;
      const res = await timetableApi.getTimetables({ is_active: true, page_size: 1 });
      const activeTt = res.items?.[0];
      if (activeTt) {
        return await timetableApi.getTimetable(activeTt.id);
      }
      return null;
    },
    enabled: isStudent,
  });

  // Query Student's Library Loans
  const { data: libraryLoansData } = useQuery({
    queryKey: ['studentLibraryLoans', summary?.student_info?.id],
    queryFn: async () => {
      if (!isStudent) return null;
      return await libraryApi.getLoans({ page_size: 10 });
    },
    enabled: isStudent,
  });

  // Query Payment Receipt for Receipt Modal
  const { data: receiptDetailData } = useQuery({
    queryKey: ['paymentReceipt', selectedPaymentId],
    queryFn: async () => {
      if (!selectedPaymentId) return null;
      return await feesApi.getPaymentReceipt(selectedPaymentId);
    },
    enabled: !!selectedPaymentId,
  });

  // Homework Submission Mutation
  const submitHomeworkMutation = useMutation({
    mutationFn: async ({ homeworkId, content }: { homeworkId: string; content: string }) => {
      return await homeworkApi.submitWork(homeworkId, content);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      setIsHomeworkModalOpen(false);
      setSubmissionText('');
    },
  });

  // Payment Execution Flow
  const handleInitiateAndPay = async () => {
    if (!activeAssignment) return;
    try {
      setPaymentStep('PROCESSING');
      setPaymentError(null);

      // 1. Create server-side PaymentOrder
      const order = await paymentsApi.createOrder({
        student_fee_assignment_id: activeAssignment.id,
        provider: selectedGateway,
      });

      // 2. Complete Gateway / Simulated Signature Verification
      const mockPayId = `pay_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const mockSig = `sig_${Date.now()}_valid_hash`;

      const verifyResult = await paymentsApi.verifyPayment({
        provider: selectedGateway,
        payment_order_id: order.id,
        gateway_order_id: order.gateway_order_id,
        gateway_payment_id: mockPayId,
        gateway_signature: mockSig,
      });

      if (verifyResult.success) {
        setPaymentStep('SUCCESS');
        // Invalidate fee summaries
        queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
        queryClient.invalidateQueries({ queryKey: ['parentFeeAssignments'] });
      } else {
        setPaymentStep('ERROR');
        setPaymentError(verifyResult.message || 'Payment verification failed.');
      }
    } catch (err: any) {
      setPaymentStep('ERROR');
      setPaymentError(err.response?.data?.detail || err.message || 'Payment processing encountered an error.');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh]">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="lg:col-span-2 h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <ErrorState
          title={isAdmin ? 'Administrative Command Center Error' : 'Teacher Workstation Error'}
          message={(error as any)?.message || 'Failed to fetch summary data.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  // ==========================================
  // RENDER: PARENT PORTAL DASHBOARD
  // ==========================================
  if (isParent) {
    const children = summary?.children || [];
    const isZeroChild = summary?.zero_child_state;
    const att = summary?.attendance_summary;
    const fees = summary?.fees_summary;
    const academics = summary?.academics_summary;
    const publishedCards = reportCardsData?.items || [];

    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh] select-none">
        {/* Title Header */}
        <div className="border-b border-divider dark:border-stone-850 pb-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
              GUARDIAN_PORTAL // FAMILY_DOCKET
            </p>
            <div className="flex items-center gap-3 mt-1.5">
              <div className="flex items-center justify-center w-8 h-8 bg-brand-500 text-white shrink-0">
                <Users className="w-4 h-4" />
              </div>
              <h1 className="text-3xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-none">
                Parent Command Center
              </h1>
            </div>
            <p className="text-xs text-ink-muted dark:text-stone-400 mt-2 font-sans">
              Welcome, <span className="font-semibold text-ink dark:text-stone-200">{summary?.parent_name}</span>. Linked account: <span className="font-mono">{user?.email}</span>.
            </p>
          </div>

          {summary?.unread_notifications_count > 0 && (
            <div
              onClick={() => navigate('/app/notifications')}
              className="cursor-pointer flex items-center gap-2.5 px-3.5 py-2 bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-mono"
            >
              <Bell className="w-4 h-4 text-amber-600 animate-pulse" />
              <span>{summary.unread_notifications_count} Unread Notification(s)</span>
            </div>
          )}
        </div>

        {/* Multi-Child Selector Tabs */}
        {children.length > 0 && (
          <div className="border border-divider bg-paper-dim dark:border-stone-800 dark:bg-stone-900/60 p-3 flex flex-wrap items-center gap-3">
            <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 mr-2">
              SELECT_CHILD:
            </span>
            {children.map((child: any) => {
              const isSelected = activeChildId === child.id;
              return (
                <button
                  key={child.id}
                  onClick={() => setSelectedChildId(child.id)}
                  className={`px-4 py-2 text-xs font-mono transition-all flex items-center gap-2 border ${
                    isSelected
                      ? 'bg-brand-500 text-white border-brand-500 shadow-sm font-semibold'
                      : 'bg-paper dark:bg-stone-800 text-ink dark:text-stone-300 border-divider dark:border-stone-700 hover:border-brand-500/50'
                  }`}
                >
                  <GraduationCap className="w-3.5 h-3.5" />
                  <span>{child.first_name} {child.last_name}</span>
                  <span className="text-[10px] opacity-75">({child.school_class_name || 'Class'} - {child.section_name || 'A'})</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Zero-Child Fail-Closed State Alert */}
        {isZeroChild && (
          <div className="border border-amber-500/30 bg-amber-500/5 p-6 flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-amber-900 dark:text-amber-200">
                NO_LINKED_STUDENTS_FOUND
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-sans">
                No active student enrollment records are linked to your guardian profile ({user?.email}).
                Please contact school administration to verify your registered phone number or email address on your child's admission file.
              </p>
            </div>
          </div>
        )}

        {/* Main Child Operational Summary Cards */}
        {!isZeroChild && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Attendance Card */}
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[140px]">
                <div className="flex items-center justify-between border-b border-divider/50 pb-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                    <CalendarCheck className="w-3.5 h-3.5 text-brand-500" />
                    ATTENDANCE_OVERVIEW
                  </span>
                  <Badge variant={att?.attendance_percentage >= 75 ? 'success' : 'warning'}>
                    {att?.attendance_percentage ?? 0}%
                  </Badge>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center font-mono">
                  <div className="bg-emerald-500/10 p-2 border border-emerald-500/20">
                    <span className="block text-lg font-bold text-emerald-700 dark:text-emerald-300">{att?.present_days ?? 0}</span>
                    <span className="text-[9px] uppercase text-emerald-800 dark:text-emerald-400">PRESENT</span>
                  </div>
                  <div className="bg-rose-500/10 p-2 border border-rose-500/20">
                    <span className="block text-lg font-bold text-rose-700 dark:text-rose-300">{att?.absent_days ?? 0}</span>
                    <span className="text-[9px] uppercase text-rose-800 dark:text-rose-400">ABSENT</span>
                  </div>
                  <div className="bg-amber-500/10 p-2 border border-amber-500/20">
                    <span className="block text-lg font-bold text-amber-700 dark:text-amber-300">{att?.late_days ?? 0}</span>
                    <span className="text-[9px] uppercase text-amber-800 dark:text-amber-400">LATE</span>
                  </div>
                </div>
              </div>

              {/* Fee Dues Card with Interactive Checkout & Receipt Viewer */}
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[140px]">
                <div className="flex items-center justify-between border-b border-divider/50 pb-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                    <CreditCard className="w-3.5 h-3.5 text-brand-500" />
                    FEE_ACCOUNT_STATUS
                  </span>
                  <Badge variant={fees?.status === 'PAID' ? 'success' : fees?.status === 'PARTIALLY_PAID' ? 'info' : 'error'}>
                    {fees?.status || 'NO_FEES'}
                  </Badge>
                </div>
                <div className="mt-2 flex items-baseline justify-between font-mono">
                  <div>
                    <span className="text-[9px] uppercase text-ink-muted/60 block">OUTSTANDING_DUE</span>
                    <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                      ₹{fees?.total_due ?? '0.00'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[9px] uppercase text-ink-muted/60 block">NEXT_DUE_DATE</span>
                    <span className="text-xs font-semibold text-ink dark:text-stone-300">
                      {fees?.next_due_date || 'None'}
                    </span>
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-divider/40 flex items-center gap-2">
                  {fees?.total_due && Number(fees.total_due) > 0 ? (
                    <button
                      onClick={() => {
                        setPaymentStep('REVIEW');
                        setPaymentError(null);
                        setIsPayModalOpen(true);
                      }}
                      className="flex-1 px-3 py-1.5 bg-brand-500 text-white hover:bg-brand-600 text-xs font-mono font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-colors"
                    >
                      <DollarSign className="w-3.5 h-3.5" />
                      <span>Pay Online Now</span>
                    </button>
                  ) : (
                    <button
                      disabled
                      className="flex-1 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs font-mono font-medium flex items-center justify-center gap-1.5 cursor-default"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>All Dues Cleared</span>
                    </button>
                  )}
                  {paymentsData?.items && paymentsData.items.length > 0 && (
                    <button
                      onClick={() => {
                        setSelectedPaymentId(paymentsData.items[0].id);
                        setIsReceiptModalOpen(true);
                      }}
                      className="px-3 py-1.5 bg-paper-dim dark:bg-stone-800 border border-divider hover:border-brand-500/50 text-ink dark:text-stone-300 text-xs font-mono flex items-center gap-1"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Receipt</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Academic Standings Card with Published Report Card Viewer */}
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[140px]">
                <div className="flex items-center justify-between border-b border-divider/50 pb-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-brand-500" />
                    ACADEMIC_STANDINGS
                  </span>
                  <Badge variant="info">
                    {publishedCards.length} Published
                  </Badge>
                </div>
                <div className="mt-2 flex items-baseline justify-between font-mono">
                  <div>
                    <span className="text-[9px] uppercase text-ink-muted/60 block">LATEST_GPA</span>
                    <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                      {academics?.latest_term_gpa || 'N/A'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[9px] uppercase text-ink-muted/60 block">CARDS_AVAILABLE</span>
                    <span className="text-xs font-semibold text-ink dark:text-stone-300">
                      {publishedCards.length} Term Record(s)
                    </span>
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-divider/40">
                  <button
                    onClick={() => setIsReportCardModalOpen(true)}
                    className="w-full px-3 py-1.5 bg-paper-dim dark:bg-stone-800 border border-divider hover:border-brand-500 text-ink dark:text-stone-200 text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5 text-brand-500" />
                    <span>View Published Report Cards</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>

            {/* Grid Workspace: Homework & Upcoming Exams */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Homework Panel */}
              <div className="border border-divider dark:border-stone-800 bg-paper">
                <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
                  <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-brand-500" />
                    ASSIGNED_HOMEWORK
                  </h2>
                  <span className="text-[9px] font-mono text-ink-muted/40">RECENT_ACTIVE</span>
                </div>
                <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
                  {summary?.recent_homework?.length === 0 ? (
                    <p className="text-xs text-ink-muted/60 font-mono text-center py-4">NO_ACTIVE_HOMEWORK_ASSIGNED</p>
                  ) : (
                    summary?.recent_homework?.map((hw: any) => (
                      <div key={hw.id} className="py-2.5 flex items-center justify-between text-xs font-sans">
                        <div>
                          <span className="font-semibold text-ink dark:text-stone-200 block">{hw.title}</span>
                          <span className="text-[10px] font-mono text-ink-muted dark:text-stone-400">{hw.subject_name} • Due: {hw.due_date}</span>
                        </div>
                        <Badge variant={hw.is_submitted ? 'success' : 'warning'}>
                          {hw.is_submitted ? 'SUBMITTED' : 'PENDING'}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Upcoming Exams Panel */}
              <div className="border border-divider dark:border-stone-800 bg-paper">
                <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
                  <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-brand-500" />
                    UPCOMING_EXAMS_SCHEDULE
                  </h2>
                  <span className="text-[9px] font-mono text-ink-muted/40">SECTION_SCHEDULE</span>
                </div>
                <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
                  {summary?.upcoming_exams?.length === 0 ? (
                    <p className="text-xs text-ink-muted/60 font-mono text-center py-4">NO_UPCOMING_EXAMS_SCHEDULED</p>
                  ) : (
                    summary?.upcoming_exams?.map((ex: any) => (
                      <div key={ex.id} className="py-2.5 flex items-center justify-between text-xs font-sans">
                        <div>
                          <span className="font-semibold text-ink dark:text-stone-200 block">{ex.exam_name} — {ex.subject_name}</span>
                          <span className="text-[10px] font-mono text-ink-muted dark:text-stone-400">Date: {ex.exam_date}</span>
                        </div>
                        <span className="text-[10px] font-mono bg-paper-dim dark:bg-stone-800 px-2 py-1 border border-divider">
                          {ex.start_time?.slice(0, 5)} - {ex.end_time?.slice(0, 5)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* MODAL: Parent Online Fee Checkout */}
        {isPayModalOpen && (
          <div className="fixed inset-0 z-50 bg-stone-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 w-full max-w-lg shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-brand-500" />
                  <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100">
                    Online Fee Settlement Checkout
                  </h3>
                </div>
                <button
                  onClick={() => setIsPayModalOpen(false)}
                  className="text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {paymentStep === 'REVIEW' && (
                <div className="space-y-4">
                  <div className="bg-paper-dim dark:bg-stone-850 p-3.5 border border-divider dark:border-stone-800 space-y-2 font-mono text-xs">
                    <div className="flex justify-between text-ink-muted">
                      <span>STUDENT_NAME:</span>
                      <span className="font-semibold text-ink dark:text-stone-200">
                        {activeAssignment?.student ? `${activeAssignment.student.first_name} ${activeAssignment.student.last_name || ''}`.trim() : 'Selected Ward'}
                      </span>
                    </div>
                    <div className="flex justify-between text-ink-muted">
                      <span>FEE_STRUCTURE:</span>
                      <span className="text-ink dark:text-stone-200">{activeAssignment?.fee_structure?.name || 'Annual Tuition'}</span>
                    </div>
                    <div className="flex justify-between text-ink-muted">
                      <span>TOTAL_CHARGES:</span>
                      <span className="text-ink dark:text-stone-200">₹{activeAssignment?.gross_amount ?? '0.00'}</span>
                    </div>
                    <div className="flex justify-between text-ink-muted">
                      <span>PAID_TO_DATE:</span>
                      <span className="text-emerald-600 dark:text-emerald-400">₹{activeAssignment?.total_paid ?? '0.00'}</span>
                    </div>
                    <div className="flex justify-between text-brand-500 font-bold border-t border-divider/60 pt-2 text-sm">
                      <span>PAYABLE_AMOUNT:</span>
                      <span>₹{activeAssignment?.outstanding_due ?? fees?.total_due ?? '0.00'}</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-xs font-mono uppercase tracking-wider text-ink-muted">
                      Select Payment Gateway Provider
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['MOCK', 'RAZORPAY', 'STRIPE'] as const).map((gw) => (
                        <button
                          key={gw}
                          type="button"
                          onClick={() => setSelectedGateway(gw)}
                          className={`p-2.5 text-xs font-mono border text-center transition-all ${
                            selectedGateway === gw
                              ? 'border-brand-500 bg-brand-500/10 text-brand-600 font-bold'
                              : 'border-divider dark:border-stone-700 hover:border-brand-500/40 text-ink-muted'
                          }`}
                        >
                          {gw === 'MOCK' ? '⚡ Instant Simulator' : gw}
                        </button>
                      ))}
                    </div>
                    <p className="text-[11px] text-ink-muted/80 font-sans">
                      All payment orders are cryptographic and verified server-side with zero trust.
                    </p>
                  </div>

                  <div className="flex justify-end gap-3 pt-3 border-t border-divider">
                    <button
                      onClick={() => setIsPayModalOpen(false)}
                      className="px-4 py-2 border border-divider text-xs font-mono text-ink-muted hover:text-ink"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleInitiateAndPay}
                      className="px-5 py-2 bg-brand-500 hover:bg-brand-600 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>Confirm & Pay ₹{activeAssignment?.outstanding_due ?? fees?.total_due ?? '0.00'}</span>
                    </button>
                  </div>
                </div>
              )}

              {paymentStep === 'PROCESSING' && (
                <div className="py-8 text-center space-y-3 font-mono">
                  <div className="inline-block w-8 h-8 border-3 border-brand-500 border-t-transparent animate-spin" />
                  <p className="text-sm font-semibold text-ink dark:text-stone-200">
                    Communicating with Payment Gateway...
                  </p>
                  <p className="text-xs text-ink-muted">
                    Establishing cryptographic session and calculating ledger balance.
                  </p>
                </div>
              )}

              {paymentStep === 'SUCCESS' && (
                <div className="py-6 text-center space-y-4 font-mono">
                  <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 mx-auto flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-emerald-700 dark:text-emerald-300">
                      Payment Successfully Verified
                    </h4>
                    <p className="text-xs text-ink-muted mt-1 font-sans">
                      Your fee transaction has been recorded, settled in the institutional ledger, and receipt generated.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setIsPayModalOpen(false);
                      if (paymentsData?.items?.[0]?.id) {
                        setSelectedPaymentId(paymentsData.items[0].id);
                        setIsReceiptModalOpen(true);
                      }
                    }}
                    className="px-5 py-2 bg-emerald-600 text-white text-xs font-mono font-bold inline-flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span>View Official Receipt</span>
                  </button>
                </div>
              )}

              {paymentStep === 'ERROR' && (
                <div className="py-4 space-y-4">
                  <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-800 dark:text-rose-300 text-xs font-sans space-y-1">
                    <span className="font-mono font-bold block uppercase text-[10px]">PAYMENT_GATEWAY_ERROR:</span>
                    <p>{paymentError || 'Unable to process payment order.'}</p>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setPaymentStep('REVIEW')}
                      className="px-4 py-2 bg-brand-500 text-white text-xs font-mono"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* MODAL: Published Report Cards Viewer */}
        {isReportCardModalOpen && (
          <div className="fixed inset-0 z-50 bg-stone-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-brand-500" />
                  <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100">
                    Official Published Report Cards
                  </h3>
                </div>
                <button
                  onClick={() => setIsReportCardModalOpen(false)}
                  className="text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {publishedCards.length === 0 ? (
                <div className="py-8 text-center font-mono text-xs text-ink-muted space-y-2">
                  <AlertCircle className="w-8 h-8 text-amber-500 mx-auto opacity-70" />
                  <p>NO_PUBLISHED_REPORT_CARDS_YET</p>
                  <p className="text-[11px] font-sans">
                    Report cards will appear here once term exams are evaluated and officially published by administration.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {publishedCards.map((rc: any) => (
                    <div
                      key={rc.id}
                      className="border border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-850 p-4 space-y-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-divider/60 pb-3">
                        <div>
                          <span className="text-sm font-bold text-ink dark:text-stone-100 font-serif">
                            {rc.academic_year_name || 'Academic Year'} • {rc.academic_term_name || 'Term Exam'}
                          </span>
                          <span className="block text-[10px] font-mono text-ink-muted">
                            Published Date: {rc.published_at ? new Date(rc.published_at).toLocaleDateString() : 'Official'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 font-mono">
                          <Badge variant={rc.is_passed ? 'success' : 'error'}>
                            {rc.is_passed ? 'PASSED' : 'REQUIRES_RETEST'}
                          </Badge>
                          <span className="text-xs font-bold bg-brand-500/10 px-2 py-1 text-brand-600 border border-brand-500/20">
                            GPA: {rc.gpa || rc.percentage + '%'}
                          </span>
                        </div>
                      </div>

                      {/* Subject Mark Breakdown */}
                      {rc.items && rc.items.length > 0 && (
                        <div className="border border-divider dark:border-stone-800 overflow-hidden">
                          <table className="w-full text-xs font-sans text-left">
                            <thead className="bg-paper border-b border-divider font-mono text-[10px] uppercase text-ink-muted">
                              <tr>
                                <th className="p-2">Subject</th>
                                <th className="p-2 text-right">Max</th>
                                <th className="p-2 text-right">Obtained</th>
                                <th className="p-2 text-center">Grade</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-divider/40">
                              {rc.items.map((item: any, idx: number) => (
                                <tr key={idx} className="hover:bg-paper/50">
                                  <td className="p-2 font-medium text-ink dark:text-stone-200">{item.subject_name}</td>
                                  <td className="p-2 text-right font-mono text-ink-muted">{item.max_marks}</td>
                                  <td className="p-2 text-right font-mono font-bold text-ink dark:text-stone-100">{item.obtained_marks}</td>
                                  <td className="p-2 text-center font-mono">
                                    <span className="px-1.5 py-0.5 bg-brand-500/10 text-brand-600 font-bold text-[10px]">
                                      {item.grade || 'A'}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* Remarks & Attendance summary */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-sans">
                        <div className="p-2.5 bg-paper dark:bg-stone-900 border border-divider/60">
                          <span className="text-[10px] font-mono text-ink-muted block uppercase">TEACHER_REMARKS:</span>
                          <p className="text-ink dark:text-stone-300 mt-1 italic">
                            "{rc.teacher_remarks || 'Consistent academic performance and attentive classroom demeanor.'}"
                          </p>
                        </div>
                        <div className="p-2.5 bg-paper dark:bg-stone-900 border border-divider/60">
                          <span className="text-[10px] font-mono text-ink-muted block uppercase">TERM_ATTENDANCE:</span>
                          <p className="text-ink dark:text-stone-300 mt-1 font-mono font-semibold">
                            {rc.present_days ?? 'N/A'} / {rc.total_working_days ?? 'N/A'} Days ({rc.attendance_percentage ?? '100'}%)
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* MODAL: Fee Payment Receipt Modal */}
        {isReceiptModalOpen && receiptDetailData && (
          <div className="fixed inset-0 z-50 bg-stone-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 w-full max-w-md shadow-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-brand-500" />
                  <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100">
                    Official Fee Payment Receipt
                  </h3>
                </div>
                <button
                  onClick={() => setIsReceiptModalOpen(false)}
                  className="text-ink-muted hover:text-ink"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="border border-divider p-4 space-y-3 font-mono text-xs bg-paper-dim dark:bg-stone-850">
                <div className="text-center border-b border-divider pb-2">
                  <h4 className="font-bold text-sm text-brand-500">INSTITUTIONAL FEE RECEIPT</h4>
                  <p className="text-[10px] text-ink-muted">Receipt #: {receiptDetailData.receipt_number}</p>
                </div>

                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Gross Amount:</span>
                    <span className="font-semibold text-ink dark:text-stone-200">₹{receiptDetailData.gross_amount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Net Payable:</span>
                    <span>₹{receiptDetailData.net_payable}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Payment Date:</span>
                    <span>{new Date(receiptDetailData.payment_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Payment Mode:</span>
                    <span className="font-bold text-brand-600">{receiptDetailData.payment_mode}</span>
                  </div>
                  <div className="flex justify-between border-t border-divider pt-2 text-sm font-bold text-emerald-600">
                    <span>AMOUNT PAID:</span>
                    <span>₹{receiptDetailData.amount}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => window.print()}
                  className="px-4 py-2 border border-divider text-xs font-mono flex items-center gap-1.5 hover:border-brand-500"
                >
                  <Printer className="w-4 h-4" />
                  <span>Print Receipt</span>
                </button>
                <button
                  onClick={() => setIsReceiptModalOpen(false)}
                  className="px-4 py-2 bg-brand-500 text-white text-xs font-mono font-bold"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ==========================================
  // RENDER: STUDENT SELF-SERVICE PORTAL
  // ==========================================
  if (isStudent) {
    const st = summary?.student_info;
    const att = summary?.attendance_summary;
    const fees = summary?.fees_summary;
    const academics = summary?.academics_summary;
    const publishedCards = reportCardsData?.items || [];
    const activeLoans = libraryLoansData?.items || [];

    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh] select-none">
        {/* Header */}
        <div className="border-b border-divider dark:border-stone-850 pb-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
              STUDENT_PORTAL // ACADEMIC_DOSSIER
            </p>
            <div className="flex items-center gap-3 mt-1.5">
              <div className="flex items-center justify-center w-8 h-8 bg-brand-500 text-white shrink-0">
                <GraduationCap className="w-4 h-4" />
              </div>
              <h1 className="text-3xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-none">
                Student Workstation
              </h1>
            </div>
            <p className="text-xs text-ink-muted dark:text-stone-400 mt-2 font-sans">
              Logged in as <span className="font-semibold text-ink dark:text-stone-200">{st?.first_name} {st?.last_name}</span> (Adm #: <span className="font-mono">{st?.admission_number}</span>) • Class: <span className="font-semibold">{st?.school_class_name || 'N/A'} - {st?.section_name || 'A'}</span>.
            </p>
          </div>

          {summary?.unread_notifications_count > 0 && (
            <div
              onClick={() => navigate('/app/notifications')}
              className="cursor-pointer flex items-center gap-2.5 px-3.5 py-2 bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-mono"
            >
              <Bell className="w-4 h-4 text-amber-600 animate-pulse" />
              <span>{summary.unread_notifications_count} Unread Notification(s)</span>
            </div>
          )}
        </div>

        {/* Operational Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Attendance */}
          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[120px]">
            <div className="flex items-center justify-between border-b border-divider/50 pb-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                <CalendarCheck className="w-3.5 h-3.5 text-brand-500" />
                MY_ATTENDANCE
              </span>
              <Badge variant={att?.attendance_percentage >= 75 ? 'success' : 'warning'}>
                {att?.attendance_percentage ?? 0}%
              </Badge>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center font-mono">
              <div className="bg-emerald-500/10 p-2 border border-emerald-500/20">
                <span className="block text-lg font-bold text-emerald-700 dark:text-emerald-300">{att?.present_days ?? 0}</span>
                <span className="text-[9px] uppercase text-emerald-800 dark:text-emerald-400">PRESENT</span>
              </div>
              <div className="bg-rose-500/10 p-2 border border-rose-500/20">
                <span className="block text-lg font-bold text-rose-700 dark:text-rose-300">{att?.absent_days ?? 0}</span>
                <span className="text-[9px] uppercase text-rose-800 dark:text-rose-400">ABSENT</span>
              </div>
              <div className="bg-amber-500/10 p-2 border border-amber-500/20">
                <span className="block text-lg font-bold text-amber-700 dark:text-amber-300">{att?.late_days ?? 0}</span>
                <span className="text-[9px] uppercase text-amber-800 dark:text-amber-400">LATE</span>
              </div>
            </div>
          </div>

          {/* Fee Balance */}
          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[120px]">
            <div className="flex items-center justify-between border-b border-divider/50 pb-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                <CreditCard className="w-3.5 h-3.5 text-brand-500" />
                MY_FEE_ACCOUNT
              </span>
              <Badge variant={fees?.status === 'PAID' ? 'success' : 'warning'}>
                {fees?.status || 'NO_FEES'}
              </Badge>
            </div>
            <div className="mt-3 flex items-baseline justify-between font-mono">
              <div>
                <span className="text-[9px] uppercase text-ink-muted/60 block">OUTSTANDING_BALANCE</span>
                <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                  ₹{fees?.total_due ?? '0.00'}
                </span>
              </div>
            </div>
          </div>

          {/* Academic Report Cards */}
          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[120px]">
            <div className="flex items-center justify-between border-b border-divider/50 pb-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-brand-500" />
                MY_ACADEMICS
              </span>
              <Badge variant="info">
                {publishedCards.length} Published
              </Badge>
            </div>
            <div className="mt-2 flex items-baseline justify-between font-mono">
              <div>
                <span className="text-[9px] uppercase text-ink-muted/60 block">LATEST_GPA</span>
                <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                  {academics?.latest_term_gpa || 'N/A'}
                </span>
              </div>
              <button
                onClick={() => setIsReportCardModalOpen(true)}
                className="text-xs text-brand-500 hover:underline flex items-center gap-1 font-sans"
              >
                View Cards <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Daily Period Timetable Schedule */}
        <div className="border border-divider dark:border-stone-800 bg-paper">
          <div className="px-4 py-2.5 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
            <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-brand-500" />
              TODAY_CLASS_PERIOD_SCHEDULE
            </h2>
            <span className="text-[9px] font-mono text-ink-muted/60">
              CLASS_{st?.school_class_name || 'X'} // SECTION_{st?.section_name || 'A'}
            </span>
          </div>

          <div className="p-4">
            {studentTimetable?.entries && studentTimetable.entries.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {studentTimetable.entries.map((entry: any) => (
                  <div
                    key={entry.id}
                    className="p-3 border border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-850 space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono text-brand-500 font-bold">
                      <span>{entry.day_of_week || 'WEEKDAY'}</span>
                      <span className="bg-brand-500/10 px-1.5 py-0.5 border border-brand-500/20">
                        {entry.start_time?.slice(0, 5)} - {entry.end_time?.slice(0, 5)}
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-ink dark:text-stone-200 block font-sans">
                      {entry.subject_name || 'Subject'}
                    </span>
                    <div className="text-[10px] text-ink-muted flex items-center justify-between font-mono">
                      <span>{entry.teacher_name || 'Teacher'}</span>
                      <span>Room {entry.classroom_name || 'Main'}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-4 text-center text-xs font-mono text-ink-muted">
                NO_TIMETABLE_SLOTS_SCHEDULED_FOR_TODAY
              </div>
            )}
          </div>
        </div>

        {/* Section Grid: Homework Tasks & Library Loans */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Homework Tasks with Submission Workflow */}
          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-brand-500" />
                MY_HOMEWORK_ASSIGNMENTS
              </h2>
              <span className="text-[9px] font-mono text-ink-muted/40">INTERACTIVE_SUBMISSION</span>
            </div>
            <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
              {summary?.recent_homework?.length === 0 ? (
                <p className="text-xs text-ink-muted/60 font-mono text-center py-4">NO_PENDING_HOMEWORK</p>
              ) : (
                summary?.recent_homework?.map((hw: any) => (
                  <div
                    key={hw.id}
                    onClick={() => {
                      setSelectedHomework(hw);
                      setSubmissionText('');
                      setIsHomeworkModalOpen(true);
                    }}
                    className="py-3 flex items-center justify-between text-xs font-sans hover:bg-paper-dim/40 px-2 cursor-pointer transition-colors"
                  >
                    <div>
                      <span className="font-semibold text-ink dark:text-stone-200 block hover:text-brand-500">
                        {hw.title}
                      </span>
                      <span className="text-[10px] font-mono text-ink-muted dark:text-stone-400">
                        {hw.subject_name} • Due: {hw.due_date}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={hw.is_submitted ? 'success' : 'warning'}>
                        {hw.is_submitted ? 'SUBMITTED' : 'SUBMIT_NOW'}
                      </Badge>
                      <ChevronRight className="w-3.5 h-3.5 text-ink-muted/50" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Library Loans Card */}
          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                <BookMarked className="w-3.5 h-3.5 text-brand-500" />
                LIBRARY_LOAN_STATUS
              </h2>
              <span className="text-[9px] font-mono text-ink-muted/40">CIRCULATION_RECORDS</span>
            </div>
            <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
              {activeLoans.length === 0 ? (
                <div className="py-6 text-center font-mono text-xs text-ink-muted space-y-1">
                  <p>NO_ACTIVE_BOOK_LOANS</p>
                  <p className="text-[10px] font-sans">Visit the campus library to borrow catalog titles.</p>
                </div>
              ) : (
                activeLoans.map((loan: any) => (
                  <div key={loan.id} className="py-2.5 flex items-center justify-between text-xs font-sans">
                    <div>
                      <span className="font-semibold text-ink dark:text-stone-200 block">
                        {loan.book_title || 'Catalog Book'}
                      </span>
                      <span className="text-[10px] font-mono text-ink-muted dark:text-stone-400">
                        Acc #: {loan.accession_number} • Due: {loan.due_date}
                      </span>
                    </div>
                    <Badge variant={loan.status === 'OVERDUE' ? 'error' : 'success'}>
                      {loan.status}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* MODAL: Student Homework Submission Modal */}
        {isHomeworkModalOpen && selectedHomework && (
          <div className="fixed inset-0 z-50 bg-stone-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 w-full max-w-lg shadow-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-brand-500" />
                  <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100">
                    Homework Submission Workspace
                  </h3>
                </div>
                <button
                  onClick={() => setIsHomeworkModalOpen(false)}
                  className="text-ink-muted hover:text-ink"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3 font-sans text-xs">
                <div className="p-3 bg-paper-dim dark:bg-stone-850 border border-divider space-y-1">
                  <h4 className="font-bold text-sm text-ink dark:text-stone-100">{selectedHomework.title}</h4>
                  <p className="text-ink-muted">{selectedHomework.description || 'No additional instructions provided.'}</p>
                  <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-ink-muted border-t border-divider/40">
                    <span>Subject: {selectedHomework.subject_name}</span>
                    <span>Deadline: {selectedHomework.due_date}</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-mono uppercase tracking-wider text-ink-muted">
                    Your Submission / Solution Response
                  </label>
                  <textarea
                    rows={5}
                    value={submissionText}
                    onChange={(e) => setSubmissionText(e.target.value)}
                    placeholder="Enter your completed response, answer notes, or referenced solution work..."
                    className="w-full p-3 border border-divider dark:border-stone-700 bg-paper dark:bg-stone-950 text-xs font-mono focus:border-brand-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-divider">
                <button
                  onClick={() => setIsHomeworkModalOpen(false)}
                  className="px-4 py-2 border border-divider text-xs font-mono text-ink-muted hover:text-ink"
                >
                  Cancel
                </button>
                <button
                  disabled={!submissionText.trim() || submitHomeworkMutation.isPending}
                  onClick={() =>
                    submitHomeworkMutation.mutate({
                      homeworkId: selectedHomework.id,
                      content: submissionText,
                    })
                  }
                  className="px-5 py-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submitHomeworkMutation.isPending ? 'Submitting...' : 'Submit Work'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: Published Report Cards Viewer for Student */}
        {isReportCardModalOpen && (
          <div className="fixed inset-0 z-50 bg-stone-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-paper dark:bg-stone-900 border border-divider dark:border-stone-700 w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-divider dark:border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-brand-500" />
                  <h3 className="text-base font-serif font-bold text-ink dark:text-stone-100">
                    My Official Published Report Cards
                  </h3>
                </div>
                <button
                  onClick={() => setIsReportCardModalOpen(false)}
                  className="text-ink-muted hover:text-ink"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {publishedCards.length === 0 ? (
                <div className="py-8 text-center font-mono text-xs text-ink-muted space-y-2">
                  <AlertCircle className="w-8 h-8 text-amber-500 mx-auto opacity-70" />
                  <p>NO_PUBLISHED_REPORT_CARDS_YET</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {publishedCards.map((rc: any) => (
                    <div
                      key={rc.id}
                      className="border border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-850 p-4 space-y-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-divider/60 pb-3">
                        <div>
                          <span className="text-sm font-bold text-ink dark:text-stone-100 font-serif">
                            {rc.academic_year_name || 'Academic Year'} • {rc.academic_term_name || 'Term Exam'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 font-mono">
                          <Badge variant={rc.is_passed ? 'success' : 'error'}>
                            {rc.is_passed ? 'PASSED' : 'REQUIRES_RETEST'}
                          </Badge>
                          <span className="text-xs font-bold bg-brand-500/10 px-2 py-1 text-brand-600 border border-brand-500/20">
                            GPA: {rc.gpa || rc.percentage + '%'}
                          </span>
                        </div>
                      </div>

                      {rc.items && rc.items.length > 0 && (
                        <div className="border border-divider dark:border-stone-800 overflow-hidden">
                          <table className="w-full text-xs font-sans text-left">
                            <thead className="bg-paper border-b border-divider font-mono text-[10px] uppercase text-ink-muted">
                              <tr>
                                <th className="p-2">Subject</th>
                                <th className="p-2 text-right">Max</th>
                                <th className="p-2 text-right">Obtained</th>
                                <th className="p-2 text-center">Grade</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-divider/40">
                              {rc.items.map((item: any, idx: number) => (
                                <tr key={idx} className="hover:bg-paper/50">
                                  <td className="p-2 font-medium text-ink dark:text-stone-200">{item.subject_name}</td>
                                  <td className="p-2 text-right font-mono text-ink-muted">{item.max_marks}</td>
                                  <td className="p-2 text-right font-mono font-bold text-ink dark:text-stone-100">{item.obtained_marks}</td>
                                  <td className="p-2 text-center font-mono">
                                    <span className="px-1.5 py-0.5 bg-brand-500/10 text-brand-600 font-bold text-[10px]">
                                      {item.grade || 'A'}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ==========================================
  // RENDER: ADMIN / TEACHER DEFAULT DASHBOARD
  // ==========================================
  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh] select-none">
      {/* Title Header */}
      <div className="border-b border-divider dark:border-stone-855 pb-5">
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
          {isAdmin ? 'SYSTEM_COMMAND_CENTER // OPERATIONAL_DOCKET' : 'TEACHER_WORKSTATION // DAILY_OPERATIONS'}
        </p>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex items-center justify-center w-7 h-7 bg-brand-500 text-white shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-none">
            {isAdmin ? 'Administrative Command Center' : 'Teacher Workstation'}
          </h1>
        </div>
        <p className="text-xs text-ink-muted dark:text-stone-400 mt-2 font-sans">
          Institutional registry active under user identifier <span className="font-mono text-ink dark:text-stone-300 font-semibold">{user?.email}</span>.
        </p>
      </div>

      {/* Operational State Indicators */}
      <div className="border border-divider bg-paper-dim dark:border-stone-800 dark:bg-stone-900/60 p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1">
          <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/60 dark:text-stone-500">CURRENT_ACADEMIC_YEAR</span>
          {summary?.current_academic_year ? (
            <div className="flex items-center gap-3">
              <span className="text-sm font-serif font-bold text-brand-500 dark:text-stone-200">
                {summary.current_academic_year.name}
              </span>
              <Badge variant="success">
                {summary.current_academic_year.status}
              </Badge>
            </div>
          ) : (
            <span className="text-xs text-ink-muted/50 dark:text-stone-600 font-mono">NO_ACTIVE_YEAR_CONFIGURED</span>
          )}
        </div>

        <div className="space-y-1 border-t md:border-t-0 md:border-l border-divider/60 dark:border-stone-800 md:pl-6 pt-3 md:pt-0">
          <span className="block text-[9px] font-mono uppercase tracking-widest text-ink-muted/60 dark:text-stone-500">ACTIVE_TERM</span>
          {summary?.current_academic_term ? (
            <div className="flex items-center gap-3">
              <span className="text-sm font-serif font-bold text-brand-500 dark:text-stone-200">
                {summary.current_academic_term.name}
              </span>
              <Badge variant="info">ACTIVE</Badge>
            </div>
          ) : (
            <span className="text-xs text-ink-muted/50 dark:text-stone-600 font-mono">NO_ACTIVE_TERM_CONFIGURED</span>
          )}
        </div>
      </div>

      {/* Registry Metrics Ledger */}
      <div className="border border-divider dark:border-stone-800 bg-paper divide-y md:divide-y-0 md:divide-x divide-divider dark:divide-stone-800 md:flex">
        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_STUDENTS</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_students ?? summary?.assigned_students_count ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ACTIVE_ENROLLMENTS</span>
          </div>
        </div>

        {isAdmin && (
          <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
            <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_FACULTY</span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                {summary?.active_teachers ?? 0}
              </span>
              <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ACTIVE_EMPLOYEES</span>
            </div>
          </div>
        )}

        {isAdmin && (
          <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
            <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_GUARDIANS</span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                {summary?.active_parents ?? 0}
              </span>
              <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ASSOCIATED_FAMILIES</span>
            </div>
          </div>
        )}

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">CLASSES_ACTIVE</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_classes ?? summary?.active_classes_count ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">DEPARTMENTS</span>
          </div>
        </div>

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">SECTIONS_ACTIVE</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_sections ?? summary?.active_sections_count ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">SECTIONS</span>
          </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400">
                SYSTEM_ATTENTION_LOGS
              </h2>
              <span className="text-[9px] font-mono text-ink-muted/40">VERIFIED_RBAC</span>
            </div>
            <div className="p-4 space-y-3">
              {!summary?.current_academic_year && (
                <div className="flex items-start gap-3 text-xs text-amber-800">
                  <span className="w-1.5 h-1.5 bg-amber-500 mt-1 shrink-0" />
                  <div>
                    <span className="font-mono uppercase font-bold text-[9px] tracking-wider text-amber-700 block">WARNING: NO_ACTIVE_YEAR</span>
                    No active academic year is configured for this domain. Student promotions and registry entries are frozen.
                  </div>
                </div>
              )}
              {!summary?.current_academic_term && (
                <div className="flex items-start gap-3 text-xs text-amber-800">
                  <span className="w-1.5 h-1.5 bg-amber-500 mt-1 shrink-0" />
                  <div>
                    <span className="font-mono uppercase font-bold text-[9px] tracking-wider text-amber-700 block">WARNING: NO_ACTIVE_TERM</span>
                    No active academic term configured. Timetable planning and daily attendance reports are offline.
                  </div>
                </div>
              )}
              {summary?.current_academic_year && summary?.current_academic_term && (
                <div className="flex items-start gap-3 text-xs text-ink-muted">
                  <span className="w-1.5 h-1.5 bg-emerald-500 mt-1.5 shrink-0" />
                  <div>
                    <span className="font-mono uppercase font-semibold text-[9px] tracking-wider text-emerald-800 block">STATUS: NOMINAL</span>
                    All core structural and operational modules report active status. No configuration conflicts diagnosed.
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400">
                DAILY_ATTENDANCE_REGISTRY
              </h2>
              <span className="text-[9px] font-mono text-ink-muted/40">EMPTY_STATE_NOMINAL</span>
            </div>
            <div className="p-6">
              <EmptyState
                title="No attendance records available"
                description="Daily attendance logs are offline. Configure term calendars to enable daily registrar sheets."
              />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400">
                REGISTRY_DOCKET_INDEX
              </h2>
              <span className="text-[9px] font-mono text-ink-muted/40">SYSTEM_LINKS</span>
            </div>
            <div className="divide-y divide-divider/65 dark:divide-stone-800/60">
              <button
                onClick={() => navigate('/app/academics')}
                className="w-full px-4 py-3 flex items-center justify-between text-xs text-ink hover:bg-paper-dim/60 transition-colors text-left font-mono"
              >
                <span>➔ ARCHITECTURE_ACADEMICS</span>
                <span className="text-[10px] text-ink-muted/50">YEARS_AND_TERMS</span>
              </button>
              <button
                onClick={() => navigate('/app/students')}
                className="w-full px-4 py-3 flex items-center justify-between text-xs text-ink hover:bg-paper-dim/60 transition-colors text-left font-mono"
              >
                <span>➔ REGISTRY_STUDENTS</span>
                <span className="text-[10px] text-ink-muted/50">STUDENT_ENROLLMENTS</span>
              </button>
              <button
                onClick={() => navigate('/app/parents')}
                className="w-full px-4 py-3 flex items-center justify-between text-xs text-ink hover:bg-paper-dim/60 transition-colors text-left font-mono"
              >
                <span>➔ REGISTRY_GUARDIANS</span>
                <span className="text-[10px] text-ink-muted/50">PARENT_CONTACTS</span>
              </button>
              <button
                onClick={() => navigate('/app/teachers')}
                className="w-full px-4 py-3 flex items-center justify-between text-xs text-ink hover:bg-paper-dim/60 transition-colors text-left font-mono"
              >
                <span>➔ REGISTRY_FACULTY</span>
                <span className="text-[10px] text-ink-muted/50">FACULTY_EMPLOYEES</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
