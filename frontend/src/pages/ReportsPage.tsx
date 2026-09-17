import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  TrendingUp,
  Users,
  CalendarCheck,
  CreditCard,
  UserPlus,
  GraduationCap,
  Building2,
  Download,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Bus,
  BookOpen,
  Package,
  Bell,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { academicTermsApi } from '@/services/api/academicTermsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { reportsApi, ReportFilterParams } from '@/services/api/reportsApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';

type TabType = 'overview' | 'students' | 'attendance' | 'finance' | 'admissions' | 'academic' | 'operations';

export const ReportsPage: React.FC = () => {
  const { permissions } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Filter state
  const [academicYearId, setAcademicYearId] = useState<string>('');
  const [academicTermId, setAcademicTermId] = useState<string>('');
  const [classId, setClassId] = useState<string>('');
  const [sectionId, setSectionId] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Common metadata queries
  const { data: years = [] } = useQuery({
    queryKey: ['academicYears'],
    queryFn: async () => {
      try {
        const res = await academicYearsApi.getAcademicYears({ page_size: 100 });
        return (res as any)?.items || (Array.isArray(res) ? res : []);
      } catch {
        return [];
      }
    },
  });

  const { data: terms = [] } = useQuery({
    queryKey: ['academicTerms', academicYearId],
    queryFn: async () => {
      try {
        const res = await academicTermsApi.getAcademicTerms({ academic_year_id: academicYearId || undefined, page_size: 100 });
        return (res as any)?.items || (Array.isArray(res) ? res : []);
      } catch {
        return [];
      }
    },
  });

  const { data: classes = [] } = useQuery({
    queryKey: ['schoolClasses'],
    queryFn: async () => {
      try {
        const res = await schoolClassesApi.getSchoolClasses({ page_size: 100 });
        return (res as any)?.items || (Array.isArray(res) ? res : []);
      } catch {
        return [];
      }
    },
  });

  const { data: sections = [] } = useQuery({
    queryKey: ['sections', classId],
    queryFn: async () => {
      if (!classId) return [];
      try {
        const res = await sectionsApi.getSectionsByClass(classId, { page_size: 100 });
        return (res as any)?.items || (Array.isArray(res) ? res : []);
      } catch {
        return [];
      }
    },
    enabled: !!classId,
  });

  const currentFilters: ReportFilterParams = {
    academic_year_id: academicYearId || undefined,
    academic_term_id: academicTermId || undefined,
    class_id: classId || undefined,
    section_id: sectionId || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    page,
    page_size: 20,
  };

  // Domain Queries
  const {
    data: executiveSummary,
    isLoading: isExecLoading,
    error: execError,
    refetch: refetchExec,
  } = useQuery({
    queryKey: ['reports', 'executiveSummary', currentFilters],
    queryFn: () => reportsApi.getExecutiveSummary(currentFilters),
    enabled: activeTab === 'overview',
  });

  const {
    data: studentReport,
    isLoading: isStudentsLoading,
    error: studentError,
    refetch: refetchStudents,
  } = useQuery({
    queryKey: ['reports', 'students', currentFilters],
    queryFn: () => reportsApi.getStudentReport(currentFilters),
    enabled: activeTab === 'students',
  });

  const {
    data: attendanceReport,
    isLoading: isAttendanceLoading,
    error: attendanceError,
    refetch: refetchAttendance,
  } = useQuery({
    queryKey: ['reports', 'attendance', currentFilters],
    queryFn: () => reportsApi.getAttendanceReport(currentFilters),
    enabled: activeTab === 'attendance',
  });

  const {
    data: financeReport,
    isLoading: isFinanceLoading,
    error: financeError,
    refetch: refetchFinance,
  } = useQuery({
    queryKey: ['reports', 'finance', currentFilters],
    queryFn: () => reportsApi.getFinanceReport(currentFilters),
    enabled: activeTab === 'finance',
  });

  const {
    data: admissionsReport,
    isLoading: isAdmissionsLoading,
    error: admissionsError,
    refetch: refetchAdmissions,
  } = useQuery({
    queryKey: ['reports', 'admissions'],
    queryFn: reportsApi.getAdmissionsReport,
    enabled: activeTab === 'admissions',
  });

  const {
    data: academicReport,
    isLoading: isAcademicLoading,
    error: academicError,
    refetch: refetchAcademic,
  } = useQuery({
    queryKey: ['reports', 'academic', currentFilters],
    queryFn: () => reportsApi.getAcademicReport(currentFilters),
    enabled: activeTab === 'academic',
  });

  const {
    data: operationsReport,
    isLoading: isOperationsLoading,
    error: operationsError,
    refetch: refetchOperations,
  } = useQuery({
    queryKey: ['reports', 'operations'],
    queryFn: reportsApi.getOperationsReport,
    enabled: activeTab === 'operations',
  });

  const handleClearFilters = () => {
    setAcademicYearId('');
    setAcademicTermId('');
    setClassId('');
    setSectionId('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  const handleExportCsv = async (category: string) => {
    try {
      setIsExporting(true);
      const blob = await reportsApi.exportCsv(category, currentFilters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${category}_report_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const canExport = permissions.includes('reports.export') || permissions.includes('reports.*') || permissions.includes('*');

  return (
    <div className="space-y-6 pb-12">
      {/* ── HEADER & ACTIONS ───────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <BarChart3 className="w-6 h-6" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">Executive Reports & BI Analytics</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Centralized role-aware operational intelligence, academic performance, and financial ledger truth.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canExport && (
            <Button
              variant="outline"
              disabled={isExporting}
              onClick={() => handleExportCsv(activeTab === 'overview' ? 'executive' : activeTab)}
              className="flex items-center gap-2 text-slate-700 border-slate-300 hover:bg-slate-50"
            >
              <Download className="w-4 h-4 text-slate-600" />
              {isExporting ? 'Exporting...' : 'Export CSV'}
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => {
              if (activeTab === 'overview') refetchExec();
              if (activeTab === 'students') refetchStudents();
              if (activeTab === 'attendance') refetchAttendance();
              if (activeTab === 'finance') refetchFinance();
              if (activeTab === 'admissions') refetchAdmissions();
              if (activeTab === 'academic') refetchAcademic();
              if (activeTab === 'operations') refetchOperations();
            }}
            className="flex items-center gap-2 text-slate-700 border-slate-300 hover:bg-slate-50"
          >
            <RefreshCw className="w-4 h-4 text-slate-600" />
            Refresh
          </Button>
        </div>
      </div>

      {/* ── FILTER TOOLBAR ──────────────────────────────────────────────── */}
      <Card className="p-4 bg-slate-50/70 border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Filter className="w-3.5 h-3.5" />
          Report Filters
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Academic Year</label>
            <select
              value={academicYearId}
              onChange={(e) => {
                setAcademicYearId(e.target.value);
                setAcademicTermId('');
              }}
              className="w-full text-xs h-9 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">All Academic Years</option>
              {years.map((y: any) => (
                <option key={y.id} value={y.id}>
                  {y.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Academic Term</label>
            <select
              value={academicTermId}
              onChange={(e) => setAcademicTermId(e.target.value)}
              className="w-full text-xs h-9 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">All Terms</option>
              {terms.map((t: any) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Class</label>
            <select
              value={classId}
              onChange={(e) => {
                setClassId(e.target.value);
                setSectionId('');
              }}
              className="w-full text-xs h-9 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">All Classes</option>
              {classes.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Section</label>
            <select
              value={sectionId}
              onChange={(e) => setSectionId(e.target.value)}
              className="w-full text-xs h-9 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">All Sections</option>
              {sections.map((s: any) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">From Date</label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="h-9 text-xs"
            />
          </div>

          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-600 mb-1">To Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="h-9 text-xs"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearFilters}
              className="h-9 text-xs text-slate-600 hover:bg-white"
            >
              Reset
            </Button>
          </div>
        </div>
      </Card>

      {/* ── WORKSTATION NAVIGATION TABS ─────────────────────────────────── */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-2 overflow-x-auto" aria-label="Tabs">
          {[
            { id: 'overview', name: 'Executive Overview', icon: TrendingUp },
            { id: 'students', name: 'Student & Enrollment', icon: Users },
            { id: 'attendance', name: 'Attendance & Absenteeism', icon: CalendarCheck },
            { id: 'finance', name: 'Finance & Ledger', icon: CreditCard },
            { id: 'admissions', name: 'Admissions Funnel', icon: UserPlus },
            { id: 'academic', name: 'Academic Performance', icon: GraduationCap },
            { id: 'operations', name: 'Operations Health', icon: Building2 },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                data-testid={`tab-${tab.id}`}
                onClick={() => {
                  setActiveTab(tab.id as TabType);
                  setPage(1);
                }}
                className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                  isActive
                    ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50 rounded-t-lg'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ── TAB CONTENT ─────────────────────────────────────────────────── */}

      {/* 1. EXECUTIVE OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {isExecLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : execError ? (
            <Alert type="error">Failed to load executive summary metrics.</Alert>
          ) : executiveSummary ? (
            <>
              {/* KPI Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {executiveSummary.kpi_cards.map((kpi) => (
                  <Card key={kpi.id} className="p-5 border-slate-200 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        {kpi.title}
                      </span>
                      {kpi.status === 'success' && <Badge variant="success">Good</Badge>}
                      {kpi.status === 'warning' && <Badge variant="warning">Attention</Badge>}
                      {kpi.status === 'danger' && <Badge variant="error">Critical</Badge>}
                      {kpi.status === 'info' && <Badge variant="info">Active</Badge>}
                    </div>
                    <div className="text-2xl font-extrabold text-slate-900 mt-2">{kpi.value}</div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
                      {kpi.trend_direction === 'up' && <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />}
                      {kpi.trend_direction === 'down' && <ArrowDownRight className="w-3.5 h-3.5 text-rose-600" />}
                      <span>{kpi.subtext}</span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Cross-Domain Overview Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Financial Health Card */}
                <Card className="p-6 border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                      <CreditCard className="w-4 h-4 text-emerald-600" />
                      Financial Health & Collections
                    </h3>
                    <Badge variant="default">{executiveSummary.fee_collection_rate_pct}% Collected</Badge>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm py-1 border-b border-slate-100">
                      <span className="text-slate-500">Total Fees Assigned</span>
                      <span className="font-semibold text-slate-900">
                        ${executiveSummary.total_fees_assigned.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm py-1 border-b border-slate-100">
                      <span className="text-slate-500">Total Fees Collected</span>
                      <span className="font-semibold text-emerald-600">
                        ${executiveSummary.total_fees_collected.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm py-1 border-b border-slate-100">
                      <span className="text-slate-500">Outstanding Balance</span>
                      <span className="font-semibold text-rose-600">
                        ${executiveSummary.total_fees_outstanding.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 mt-4">
                      <div
                        className="bg-emerald-500 h-2.5 rounded-full"
                        style={{ width: `${Math.min(100, executiveSummary.fee_collection_rate_pct)}%` }}
                      />
                    </div>
                  </div>
                </Card>

                {/* Academic & Attendance Snapshot */}
                <Card className="p-6 border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                      <GraduationCap className="w-4 h-4 text-indigo-600" />
                      Academic & Attendance Status
                    </h3>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-slate-600">Overall Attendance Rate</span>
                        <span className="font-semibold text-slate-900">{executiveSummary.overall_attendance_pct}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, executiveSummary.overall_attendance_pct)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-slate-600">Report Cards Published</span>
                        <span className="font-semibold text-slate-900">{executiveSummary.published_report_cards_pct}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div
                          className="bg-teal-500 h-2 rounded-full"
                          style={{ width: `${Math.min(100, executiveSummary.published_report_cards_pct)}%` }}
                        />
                      </div>
                    </div>
                    <div className="pt-2 text-xs text-slate-400">
                      Evaluated across {executiveSummary.active_classes} classes and {executiveSummary.active_teachers} teaching staff.
                    </div>
                  </div>
                </Card>

                {/* Operations Health Summary */}
                <Card className="p-6 border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-amber-600" />
                      Operations Overview
                    </h3>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500">Fleet Vehicles</div>
                      <div className="text-lg font-bold text-slate-800">
                        {executiveSummary.operations_highlights.active_vehicles || 0}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500">Active Book Loans</div>
                      <div className="text-lg font-bold text-slate-800">
                        {executiveSummary.operations_highlights.active_library_loans || 0}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500">Low Stock Alerts</div>
                      <div className="text-lg font-bold text-amber-600">
                        {executiveSummary.operations_highlights.low_stock_alerts || 0}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <div className="text-xs text-slate-500">Inquiries Logged</div>
                      <div className="text-lg font-bold text-slate-800">
                        {executiveSummary.admissions_inquiries || 0}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* 2. STUDENT & ENROLLMENT REPORT */}
      {activeTab === 'students' && (
        <div className="space-y-6">
          {isStudentsLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : studentError ? (
            <Alert type="error">Failed to load student enrollment report.</Alert>
          ) : studentReport ? (
            <>
              {/* Demographics & Totals Header */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Active Students</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{studentReport.total_active_students}</div>
                  <div className="text-xs text-slate-400 mt-1">Currently enrolled</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Inactive / Transferred</div>
                  <div className="text-2xl font-bold text-slate-500 mt-1">{studentReport.total_inactive_students}</div>
                  <div className="text-xs text-slate-400 mt-1">Archived or graduated</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Gender Distribution</div>
                  <div className="flex items-center gap-3 mt-2 text-sm">
                    <span className="text-blue-600 font-semibold">M: {studentReport.gender_distribution.MALE || 0}</span>
                    <span className="text-pink-600 font-semibold">F: {studentReport.gender_distribution.FEMALE || 0}</span>
                    <span className="text-slate-600 font-semibold">O: {studentReport.gender_distribution.OTHER || 0}</span>
                  </div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Total Registry</div>
                  <div className="text-2xl font-bold text-indigo-600 mt-1">{studentReport.total_students}</div>
                  <div className="text-xs text-slate-400 mt-1">Lifetime registrations</div>
                </Card>
              </div>

              {/* Class & Section Table */}
              <Card className="p-6 border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-slate-900">Enrollment by Class & Section</h3>
                  <Badge variant="default">{studentReport.total_items} Classes / Sections</Badge>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50/50">
                        <th className="py-3 px-4 font-semibold text-slate-700">Class</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Section</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Total Enrolled</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Male</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Female</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Capacity</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Occupancy</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {studentReport.by_class_section.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-400">
                            No class enrollment records found matching active filters.
                          </td>
                        </tr>
                      ) : (
                        studentReport.by_class_section.map((item, idx) => (
                          <tr key={`${item.class_id}-${item.section_id || idx}`} className="hover:bg-slate-50">
                            <td className="py-3 px-4 font-medium text-slate-900">{item.class_name}</td>
                            <td className="py-3 px-4 text-slate-600">{item.section_name || '—'}</td>
                            <td className="py-3 px-4 font-semibold text-indigo-600">{item.student_count}</td>
                            <td className="py-3 px-4 text-slate-600">{item.male_count}</td>
                            <td className="py-3 px-4 text-slate-600">{item.female_count}</td>
                            <td className="py-3 px-4 text-slate-500">{item.capacity || '—'}</td>
                            <td className="py-3 px-4">
                              {item.occupancy_pct !== undefined && item.occupancy_pct !== null ? (
                                <Badge variant={item.occupancy_pct > 90 ? 'warning' : 'success'}>
                                  {item.occupancy_pct}%
                                </Badge>
                              ) : (
                                '—'
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 3. ATTENDANCE REPORT */}
      {activeTab === 'attendance' && (
        <div className="space-y-6">
          {isAttendanceLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : attendanceError ? (
            <Alert type="error">Failed to load attendance report.</Alert>
          ) : attendanceReport ? (
            <>
              {/* Attendance KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Average Attendance</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{attendanceReport.overall_attendance_pct}%</div>
                  <div className="text-xs text-slate-400 mt-1">Evaluated records</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Present Days Logged</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">{attendanceReport.total_present}</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Absences Logged</div>
                  <div className="text-2xl font-bold text-rose-600 mt-1">{attendanceReport.total_absent}</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Late Arrivals</div>
                  <div className="text-2xl font-bold text-amber-600 mt-1">{attendanceReport.total_late}</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Chronic Absenteeism</div>
                  <div className="text-2xl font-bold text-rose-700 mt-1">{attendanceReport.chronic_absentee_count}</div>
                  <div className="text-xs text-slate-400 mt-1">&lt; 75% attendance</div>
                </Card>
              </div>

              {/* Class Attendance Breakdown Table */}
              <Card className="p-6 border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-slate-900">Class & Section Attendance Breakdown</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50/50">
                        <th className="py-3 px-4 font-semibold text-slate-700">Class</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Section</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Total Evaluated</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Present</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Absent</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Late</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {attendanceReport.by_class_section.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-400">
                            No attendance records logged for the selected filter period.
                          </td>
                        </tr>
                      ) : (
                        attendanceReport.by_class_section.map((item, idx) => (
                          <tr key={`${item.class_id}-${item.section_id || idx}`} className="hover:bg-slate-50">
                            <td className="py-3 px-4 font-medium text-slate-900">{item.class_name}</td>
                            <td className="py-3 px-4 text-slate-600">{item.section_name || '—'}</td>
                            <td className="py-3 px-4 text-slate-600">{item.total_students}</td>
                            <td className="py-3 px-4 font-semibold text-emerald-600">{item.present_count}</td>
                            <td className="py-3 px-4 text-rose-600">{item.absent_count}</td>
                            <td className="py-3 px-4 text-amber-600">{item.late_count}</td>
                            <td className="py-3 px-4">
                              <Badge variant={item.attendance_pct >= 85 ? 'success' : item.attendance_pct >= 75 ? 'warning' : 'error'}>
                                {item.attendance_pct}%
                              </Badge>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>

              {/* Chronic Absentee List */}
              {attendanceReport.chronic_absentees.length > 0 && (
                <Card className="p-6 border-rose-200 bg-rose-50/20 shadow-sm">
                  <div className="flex items-center gap-2 mb-4 text-rose-700 font-semibold">
                    <AlertCircle className="w-5 h-5" />
                    Students with Chronic Low Attendance (&lt; 75%)
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-rose-200 bg-rose-50">
                          <th className="py-2.5 px-4 font-semibold text-rose-900">Admission #</th>
                          <th className="py-2.5 px-4 font-semibold text-rose-900">Student Name</th>
                          <th className="py-2.5 px-4 font-semibold text-rose-900">Class & Section</th>
                          <th className="py-2.5 px-4 font-semibold text-rose-900">Present / Total</th>
                          <th className="py-2.5 px-4 font-semibold text-rose-900">Attendance %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-rose-100">
                        {attendanceReport.chronic_absentees.map((s) => (
                          <tr key={s.student_id}>
                            <td className="py-2.5 px-4 font-mono text-xs text-slate-700">{s.admission_number}</td>
                            <td className="py-2.5 px-4 font-medium text-slate-900">{s.student_name}</td>
                            <td className="py-2.5 px-4 text-slate-600">{s.class_name} ({s.section_name})</td>
                            <td className="py-2.5 px-4 text-slate-600">{s.present_days} / {s.total_days} days</td>
                            <td className="py-2.5 px-4">
                              <Badge variant="error">{s.attendance_pct}%</Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          ) : null}
        </div>
      )}

      {/* 4. FINANCE & LEDGER REPORT */}
      {activeTab === 'finance' && (
        <div className="space-y-6">
          {isFinanceLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : financeError ? (
            <Alert type="error">Failed to load finance reporting data.</Alert>
          ) : financeReport ? (
            <>
              {/* Financial Metrics Summary */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Total Fees Assigned</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">
                    ${financeReport.total_fees_assigned.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Authoritative ledger total</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Total Fees Collected</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">
                    ${financeReport.total_fees_collected.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{financeReport.collection_rate_pct}% collection rate</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Outstanding Balance</div>
                  <div className="text-2xl font-bold text-rose-600 mt-1">
                    ${financeReport.total_fees_outstanding.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Pending payments</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Hostel Contribution</div>
                  <div className="text-2xl font-bold text-indigo-600 mt-1">
                    ${financeReport.hostel_fees_collected.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Hostel fee structures</div>
                </Card>
              </div>

              {/* Payment Methods & Aging Buckets */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6 border-slate-200">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Payment Methods Breakdown</h3>
                  <div className="space-y-3">
                    {financeReport.payment_methods_breakdown.length === 0 ? (
                      <div className="text-sm text-slate-400 py-4 text-center">No payment transactions recorded.</div>
                    ) : (
                      financeReport.payment_methods_breakdown.map((pm) => (
                        <div key={pm.method} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div>
                            <div className="font-semibold text-slate-800">{pm.method}</div>
                            <div className="text-xs text-slate-500">{pm.transaction_count} transactions</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-slate-900">
                              ${pm.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </div>
                            <div className="text-xs text-emerald-600 font-medium">{pm.percentage_of_total}%</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </Card>

                <Card className="p-6 border-slate-200">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Overdue Aging Buckets</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-lg">
                      <div className="text-xs font-medium text-emerald-800">0 – 30 Days</div>
                      <div className="text-xl font-bold text-emerald-900 mt-1">
                        ${financeReport.aging_buckets.bucket_0_30_days.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-4 bg-amber-50/50 border border-amber-100 rounded-lg">
                      <div className="text-xs font-medium text-amber-800">31 – 60 Days</div>
                      <div className="text-xl font-bold text-amber-900 mt-1">
                        ${financeReport.aging_buckets.bucket_31_60_days.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-4 bg-orange-50/50 border border-orange-100 rounded-lg">
                      <div className="text-xs font-medium text-orange-800">61 – 90 Days</div>
                      <div className="text-xl font-bold text-orange-900 mt-1">
                        ${financeReport.aging_buckets.bucket_61_90_days.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="p-4 bg-rose-50/50 border border-rose-100 rounded-lg">
                      <div className="text-xs font-medium text-rose-800">90+ Days</div>
                      <div className="text-xl font-bold text-rose-900 mt-1">
                        ${financeReport.aging_buckets.bucket_90_plus_days.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Recent Collections Table */}
              <Card className="p-6 border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-slate-900">Recent Collections Ledger</h3>
                  <Badge variant="default">{financeReport.total_collections_count} Collections</Badge>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50/50">
                        <th className="py-3 px-4 font-semibold text-slate-700">Receipt #</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Student</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Admission #</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Fee Type</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Method</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {financeReport.recent_collections.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-slate-400">
                            No collection transactions found.
                          </td>
                        </tr>
                      ) : (
                        financeReport.recent_collections.map((item) => (
                          <tr key={item.payment_id} className="hover:bg-slate-50">
                            <td className="py-3 px-4 font-mono text-xs text-indigo-600 font-semibold">{item.payment_reference}</td>
                            <td className="py-3 px-4 font-medium text-slate-900">{item.student_name}</td>
                            <td className="py-3 px-4 text-slate-500">{item.admission_number}</td>
                            <td className="py-3 px-4 text-slate-600">{item.fee_type}</td>
                            <td className="py-3 px-4">
                              <Badge variant="default">{item.payment_method}</Badge>
                            </td>
                            <td className="py-3 px-4 font-bold text-emerald-600">
                              ${item.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 5. ADMISSIONS REPORT */}
      {activeTab === 'admissions' && (
        <div className="space-y-6">
          {isAdmissionsLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : admissionsError ? (
            <Alert type="error">Failed to load admissions reporting data.</Alert>
          ) : admissionsReport ? (
            <>
              {/* Funnel KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Inquiries</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{admissionsReport.total_inquiries}</div>
                  <div className="text-xs text-slate-400 mt-1">Reception / web inquiries</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Applications</div>
                  <div className="text-2xl font-bold text-indigo-600 mt-1">{admissionsReport.total_applications}</div>
                  <div className="text-xs text-slate-400 mt-1">{admissionsReport.inquiry_to_app_conversion_pct}% conversion</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Under Review</div>
                  <div className="text-2xl font-bold text-amber-600 mt-1">{admissionsReport.total_under_review}</div>
                  <div className="text-xs text-slate-400 mt-1">Pending action</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Admitted</div>
                  <div className="text-2xl font-bold text-teal-600 mt-1">{admissionsReport.total_admitted}</div>
                  <div className="text-xs text-slate-400 mt-1">Offers extended</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Enrolled</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">{admissionsReport.total_enrolled}</div>
                  <div className="text-xs text-slate-400 mt-1">{admissionsReport.app_to_enroll_conversion_pct}% conversion</div>
                </Card>
              </div>

              {/* Pipeline Stages Breakdown */}
              <Card className="p-6 border-slate-200 shadow-sm">
                <h3 className="text-base font-semibold text-slate-900 mb-4">Admissions Pipeline Stage Breakdown</h3>
                <div className="space-y-4">
                  {admissionsReport.stages_breakdown.map((st) => (
                    <div key={st.stage}>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="font-medium text-slate-700">{st.stage_label}</span>
                        <span className="text-slate-500">
                          {st.count} applicants ({st.percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5">
                        <div
                          className="bg-indigo-600 h-2.5 rounded-full transition-all"
                          style={{ width: `${Math.min(100, st.percentage)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 6. ACADEMIC REPORT */}
      {activeTab === 'academic' && (
        <div className="space-y-6">
          {isAcademicLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : academicError ? (
            <Alert type="error">Failed to load academic performance report.</Alert>
          ) : academicReport ? (
            <>
              {/* Academic Overview KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Total Report Cards</div>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{academicReport.total_report_cards}</div>
                  <div className="text-xs text-slate-400 mt-1">Generated cards</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Publication Rate</div>
                  <div className="text-2xl font-bold text-teal-600 mt-1">{academicReport.overall_publication_pct}%</div>
                  <div className="text-xs text-slate-400 mt-1">{academicReport.total_published} cards published</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Average Score</div>
                  <div className="text-2xl font-bold text-indigo-600 mt-1">{academicReport.overall_average_score_pct}%</div>
                  <div className="text-xs text-slate-400 mt-1">Across all evaluated exams</div>
                </Card>
                <Card className="p-5 border-slate-200">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Overall Pass Rate</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">{academicReport.overall_pass_rate_pct}%</div>
                  <div className="text-xs text-slate-400 mt-1">Passing grades</div>
                </Card>
              </div>

              {/* Class Performance Table */}
              <Card className="p-6 border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-slate-900">Class Performance & Results Publication</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50/50">
                        <th className="py-3 px-4 font-semibold text-slate-700">Class</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Section</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Cards</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Published</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Avg Score</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Avg GPA</th>
                        <th className="py-3 px-4 font-semibold text-slate-700">Pass Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {academicReport.by_class_section.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-400">
                            No report card records generated for active term/year filters.
                          </td>
                        </tr>
                      ) : (
                        academicReport.by_class_section.map((item, idx) => (
                          <tr key={`${item.class_id}-${item.section_id || idx}`} className="hover:bg-slate-50">
                            <td className="py-3 px-4 font-medium text-slate-900">{item.class_name}</td>
                            <td className="py-3 px-4 text-slate-600">{item.section_name || '—'}</td>
                            <td className="py-3 px-4 text-slate-600">{item.total_report_cards}</td>
                            <td className="py-3 px-4">
                              <Badge variant={item.published_count === item.total_report_cards ? 'success' : 'warning'}>
                                {item.published_count} / {item.total_report_cards}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 font-semibold text-slate-800">{item.average_score_pct}%</td>
                            <td className="py-3 px-4 text-slate-600">{item.average_gpa !== undefined && item.average_gpa !== null ? item.average_gpa : '—'}</td>
                            <td className="py-3 px-4">
                              <Badge variant={item.pass_rate_pct >= 80 ? 'success' : item.pass_rate_pct >= 50 ? 'warning' : 'error'}>
                                {item.pass_rate_pct}%
                              </Badge>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 7. OPERATIONS REPORT */}
      {activeTab === 'operations' && (
        <div className="space-y-6">
          {isOperationsLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : operationsError ? (
            <Alert type="error">Failed to load operations report.</Alert>
          ) : operationsReport ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Transport */}
              <Card className="p-6 border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                  <Bus className="w-5 h-5 text-indigo-600" />
                  Transport Operations
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Fleet Vehicles</span>
                    <span className="font-semibold text-slate-900">{operationsReport.transport.total_vehicles}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Active Bus Routes</span>
                    <span className="font-semibold text-slate-900">{operationsReport.transport.total_routes}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Students Transported</span>
                    <span className="font-semibold text-indigo-600">{operationsReport.transport.total_assigned_students}</span>
                  </div>
                </div>
              </Card>

              {/* Library */}
              <Card className="p-6 border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                  <BookOpen className="w-5 h-5 text-emerald-600" />
                  Library & Resource Circulation
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Book Copies</span>
                    <span className="font-semibold text-slate-900">{operationsReport.library.total_books}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Active Loans</span>
                    <span className="font-semibold text-emerald-600">{operationsReport.library.active_loans_count}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Overdue Returns</span>
                    <span className="font-semibold text-rose-600">{operationsReport.library.overdue_loans_count}</span>
                  </div>
                </div>
              </Card>

              {/* Inventory */}
              <Card className="p-6 border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                  <Package className="w-5 h-5 text-amber-600" />
                  Inventory & Stock Health
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Cataloged Items</span>
                    <span className="font-semibold text-slate-900">{operationsReport.inventory.total_items}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Low Stock Alerts</span>
                    <span className="font-semibold text-amber-600">{operationsReport.inventory.low_stock_items_count}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Out of Stock Items</span>
                    <span className="font-semibold text-rose-600">{operationsReport.inventory.out_of_stock_items_count}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Asset Valuation</span>
                    <span className="font-semibold text-slate-900">
                      ${operationsReport.inventory.total_inventory_valuation.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </Card>

              {/* Hostel */}
              <Card className="p-6 border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                  <Building2 className="w-5 h-5 text-teal-600" />
                  Hostel Occupancy
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Rooms</span>
                    <span className="font-semibold text-slate-900">{operationsReport.hostel.total_rooms}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Bed Capacity</span>
                    <span className="font-semibold text-slate-900">{operationsReport.hostel.total_bed_capacity}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Occupancy Rate</span>
                    <span className="font-semibold text-teal-600">{operationsReport.hostel.occupancy_rate_pct}%</span>
                  </div>
                </div>
              </Card>

              {/* Notifications */}
              <Card className="p-6 border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                  <Bell className="w-5 h-5 text-blue-600" />
                  Communication Delivery
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Total Sent</span>
                    <span className="font-semibold text-slate-900">{operationsReport.notifications.total_notifications_sent}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Delivered Successfully</span>
                    <span className="font-semibold text-emerald-600">{operationsReport.notifications.delivered_count}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Delivery Success Rate</span>
                    <span className="font-semibold text-blue-600">{operationsReport.notifications.delivery_success_rate_pct}%</span>
                  </div>
                </div>
              </Card>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
