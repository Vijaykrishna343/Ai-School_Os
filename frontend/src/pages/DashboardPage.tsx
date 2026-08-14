import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';

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
      <div className="space-y-6 p-6">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-none" />
          ))}
        </div>
        <Skeleton className="h-32 rounded-none" />
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
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh]">
      {/* Header System */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
          OPERATIONAL COMMAND PANEL
        </p>
        <h1 className="text-3xl font-bold font-serif text-brand-500 dark:text-white mt-1">
          Administrative Command Center
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 font-sans">
          Institutional scope active for school domain under user record <span className="font-mono text-slate-700 dark:text-slate-300 font-semibold">{user?.email}</span>.
        </p>
      </div>

      {/* Control Room Metric Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <p className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">REGISTRY_STUDENTS</p>
          <p className="text-2xl font-extrabold font-serif text-brand-500 dark:text-white mt-2">
            {summary?.active_students ?? 0}
          </p>
          <div className="h-1 bg-brand-500/10 mt-3 w-full">
            <div className="h-1 bg-brand-500 w-3/4" />
          </div>
        </div>

        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <p className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">REGISTRY_FACULTY</p>
          <p className="text-2xl font-extrabold font-serif text-brand-500 dark:text-white mt-2">
            {summary?.active_teachers ?? 0}
          </p>
          <div className="h-1 bg-emerald-500/10 mt-3 w-full">
            <div className="h-1 bg-emerald-600 w-1/2" />
          </div>
        </div>

        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <p className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">REGISTRY_GUARDIANS</p>
          <p className="text-2xl font-extrabold font-serif text-brand-500 dark:text-white mt-2">
            {summary?.active_parents ?? 0}
          </p>
          <div className="h-1 bg-indigo-500/10 mt-3 w-full">
            <div className="h-1 bg-indigo-600 w-2/3" />
          </div>
        </div>

        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <p className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">CLASSES_ACTIVE</p>
          <p className="text-2xl font-extrabold font-serif text-brand-500 dark:text-white mt-2">
            {summary?.active_classes ?? 0}
          </p>
          <div className="h-1 bg-amber-500/10 mt-3 w-full">
            <div className="h-1 bg-amber-600 w-1/3" />
          </div>
        </div>

        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <p className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">SECTIONS_ACTIVE</p>
          <p className="text-2xl font-extrabold font-serif text-brand-500 dark:text-white mt-2">
            {summary?.active_sections ?? 0}
          </p>
          <div className="h-1 bg-purple-500/10 mt-3 w-full">
            <div className="h-1 bg-purple-600 w-1/2" />
          </div>
        </div>
      </div>

      {/* Operational State Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <Card className="lg:col-span-2 p-5 rounded-none border border-slate-200 dark:border-slate-800">
          <h2 className="text-xs font-mono uppercase tracking-wider text-slate-500 border-b border-slate-100 dark:border-slate-800 pb-2">
            CURRENT_ACADEMIC_OPERATIONAL_STATE
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            <div className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-850">
              <span className="text-[10px] font-mono text-slate-400">ACADEMIC_YEAR</span>
              {summary?.current_academic_year ? (
                <div className="mt-1">
                  <div className="flex items-center justify-between">
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {summary.current_academic_year.name}
                    </p>
                    <Badge variant="success">
                      {summary.current_academic_year.status}
                    </Badge>
                  </div>
                  {summary.current_academic_year.start_date && (
                    <p className="text-[10px] text-slate-500 font-mono mt-1">
                      {summary.current_academic_year.start_date} // {summary.current_academic_year.end_date}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-400 mt-1">NO_ACTIVE_YEAR_CONFIGURED</p>
              )}
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-850">
              <span className="text-[10px] font-mono text-slate-400">ACTIVE_TERM</span>
              {summary?.current_academic_term ? (
                <div className="mt-1">
                  <div className="flex items-center justify-between">
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {summary.current_academic_term.name}
                    </p>
                    <Badge variant="info">ACTIVE</Badge>
                  </div>
                  {summary.current_academic_term.term_structure && (
                    <p className="text-[10px] text-slate-500 font-mono mt-1">
                      STRUCTURE_CODE: {summary.current_academic_term.term_structure}
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-400 mt-1">NO_ACTIVE_TERM_CONFIGURED</p>
              )}
            </div>
          </div>
        </Card>

        {/* Quick Navigation Commands */}
        <Card className="p-5 rounded-none border border-slate-200 dark:border-slate-800">
          <h2 className="text-xs font-mono uppercase tracking-wider text-slate-500 border-b border-slate-100 dark:border-slate-800 pb-2">
            INSTITUTIONAL_REGISTRY_LINKS
          </h2>
          <div className="flex flex-col gap-2 mt-4">
            <Button
              variant="outline"
              className="justify-start text-xs font-mono rounded-none border border-slate-200"
              onClick={() => navigate('/app/academics')}
            >
              ➔ ARCHITECTURE_ACADEMICS
            </Button>
            <Button
              variant="outline"
              className="justify-start text-xs font-mono rounded-none border border-slate-200"
              onClick={() => navigate('/app/students')}
            >
              ➔ REGISTRY_STUDENTS
            </Button>
            <Button
              variant="outline"
              className="justify-start text-xs font-mono rounded-none border border-slate-200"
              onClick={() => navigate('/app/parents')}
            >
              ➔ REGISTRY_GUARDIANS
            </Button>
            <Button
              variant="outline"
              className="justify-start text-xs font-mono rounded-none border border-slate-200"
              onClick={() => navigate('/app/teachers')}
            >
              ➔ REGISTRY_FACULTY
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
