import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Building2 } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['adminDashboardSummary'],
    queryFn: dashboardApi.getAdminSummary,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh]">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
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
          title="Administrative Command Center Error"
          message={(error as any)?.message || 'Failed to fetch institutional summary data.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh] select-none">
      {/* Title Header */}
      <div className="border-b border-divider dark:border-stone-850 pb-5">
        <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
          SYSTEM_COMMAND_CENTER // OPERATIONAL_DOCKET
        </p>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex items-center justify-center w-7 h-7 bg-brand-500 text-white shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-brand-500 dark:text-stone-100 tracking-tight leading-none">
            Administrative Command Center
          </h1>
        </div>
        <p className="text-xs text-ink-muted dark:text-stone-400 mt-2 font-sans">
          Institutional registry active under user identifier <span className="font-mono text-ink dark:text-stone-300 font-semibold">{user?.email}</span>.
        </p>
      </div>

      {/* Operational State Indicators (Current Academic Context Bar) */}
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

      {/* Registry Metrics Ledger (1px Outline Grid) */}
      <div className="border border-divider dark:border-stone-800 bg-paper divide-y md:divide-y-0 md:divide-x divide-divider dark:divide-stone-800 md:flex">
        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_STUDENTS</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_students ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ACTIVE_ENROLLMENTS</span>
          </div>
        </div>

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_FACULTY</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_teachers ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ACTIVE_EMPLOYEES</span>
          </div>
        </div>

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">REGISTRY_GUARDIANS</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_parents ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">ASSOCIATED_FAMILIES</span>
          </div>
        </div>

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">CLASSES_ACTIVE</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_classes ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">DEPARTMENTS</span>
          </div>
        </div>

        <div className="flex-1 p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[9px] font-mono uppercase tracking-widest text-ink-muted/70 dark:text-stone-500">SECTIONS_ACTIVE</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100">
              {summary?.active_sections ?? 0}
            </span>
            <span className="text-[9px] font-mono text-ink-muted/40 uppercase">CLASS_UNITS</span>
          </div>
        </div>
      </div>

      {/* Main Command Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Area: Attention Logs & Attendance Registry */}
        <div className="lg:col-span-2 space-y-6">
          {/* Attention Log Panel */}
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

          {/* Daily Attendance Ledger Panel */}
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

        {/* Right Area: Navigation Docket Links */}
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
