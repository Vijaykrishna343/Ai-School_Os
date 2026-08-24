import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '@/services/api';
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
  UserCheck,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, permissions } = useAuthStore();
  const navigate = useNavigate();
  const [selectedChildId, setSelectedChildId] = useState<string | undefined>(undefined);

  const roleNames: string[] = (user as any)?.roles?.map((r: any) => r.name) || [];
  const isParent = roleNames.includes('Parent');
  const isStudent = roleNames.includes('Student');
  const isAdmin = permissions.includes('school.view') || permissions.includes('school.update');
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
          title={isAdmin ? "Administrative Command Center Error" : "Teacher Workstation Error"}
          message={(error as any)?.message || 'Failed to fetch summary data.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  // Render Parent Portal Dashboard
  if (isParent) {
    const children = summary?.children || [];
    const isZeroChild = summary?.zero_child_state;
    const att = summary?.attendance_summary;
    const fees = summary?.fees_summary;
    const academics = summary?.academics_summary;

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
              const isSelected = (selectedChildId || summary?.selected_child_id) === child.id;
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
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
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

              {/* Fee Dues Card */}
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
                <div className="flex items-center justify-between border-b border-divider/50 pb-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                    <CreditCard className="w-3.5 h-3.5 text-brand-500" />
                    FEE_ACCOUNT_STATUS
                  </span>
                  <Badge variant={fees?.status === 'PAID' ? 'success' : fees?.status === 'PARTIALLY_PAID' ? 'info' : 'error'}>
                    {fees?.status || 'NO_FEES'}
                  </Badge>
                </div>
                <div className="mt-3 flex items-baseline justify-between font-mono">
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
              </div>

              {/* Academic Performance Card */}
              <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
                <div className="flex items-center justify-between border-b border-divider/50 pb-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-brand-500" />
                    ACADEMIC_STANDINGS
                  </span>
                  <Badge variant="info">
                    {academics?.published_report_cards_count ?? 0} Report Card(s)
                  </Badge>
                </div>
                <div className="mt-3 flex items-baseline justify-between font-mono">
                  <div>
                    <span className="text-[9px] uppercase text-ink-muted/60 block">LATEST_GPA</span>
                    <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                      {academics?.latest_term_gpa || 'N/A'}
                    </span>
                  </div>
                  <button
                    onClick={() => navigate('/app/exams')}
                    className="text-xs text-brand-500 hover:underline flex items-center gap-1 font-sans"
                  >
                    View Cards <ChevronRight className="w-3 h-3" />
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
      </div>
    );
  }

  // Render Student Self Portal Dashboard
  if (isStudent) {
    const st = summary?.student_info;
    const att = summary?.attendance_summary;
    const fees = summary?.fees_summary;
    const academics = summary?.academics_summary;

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
          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
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

          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
            <div className="flex items-center justify-between border-b border-divider/50 pb-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                <CreditCard className="w-3.5 h-3.5 text-brand-500" />
                MY_FEE_DUES
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

          <div className="border border-divider dark:border-stone-800 bg-paper p-4 flex flex-col justify-between min-h-[110px]">
            <div className="flex items-center justify-between border-b border-divider/50 pb-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-brand-500" />
                REPORT_CARDS
              </span>
              <Badge variant="info">
                {academics?.published_report_cards_count ?? 0} Published
              </Badge>
            </div>
            <div className="mt-3 flex items-baseline justify-between font-mono">
              <div>
                <span className="text-[9px] uppercase text-ink-muted/60 block">LATEST_GPA</span>
                <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
                  {academics?.latest_term_gpa || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-brand-500" />
                MY_HOMEWORK_TASKS
              </h2>
            </div>
            <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
              {summary?.recent_homework?.length === 0 ? (
                <p className="text-xs text-ink-muted/60 font-mono text-center py-4">NO_PENDING_HOMEWORK</p>
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

          <div className="border border-divider dark:border-stone-800 bg-paper">
            <div className="px-4 py-2 border-b border-divider bg-paper-dim dark:bg-stone-900 flex justify-between items-center">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-400 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-brand-500" />
                MY_UPCOMING_EXAMS
              </h2>
            </div>
            <div className="p-4 divide-y divide-divider/50 dark:divide-stone-800">
              {summary?.upcoming_exams?.length === 0 ? (
                <p className="text-xs text-ink-muted/60 font-mono text-center py-4">NO_UPCOMING_EXAMS</p>
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
      </div>
    );
  }

  // Render Admin / Teacher Default Dashboard View
  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh] select-none">
      {/* Title Header */}
      <div className="border-b border-divider dark:border-stone-855 pb-5">
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
          {isAdmin ? "SYSTEM_COMMAND_CENTER // OPERATIONAL_DOCKET" : "TEACHER_WORKSTATION // DAILY_OPERATIONS"}
        </p>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex items-center justify-center w-7 h-7 bg-brand-500 text-white shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-none">
            {isAdmin ? "Administrative Command Center" : "Teacher Workstation"}
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
