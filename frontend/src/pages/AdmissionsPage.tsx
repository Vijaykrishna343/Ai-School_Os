import React, { useEffect, useState } from 'react';
import {
  Users,
  UserPlus,
  Calendar,
  Layers,
  Search,
  Plus,
  Edit2,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  FileText,
  Send,
  Eye,
  ArrowRight,
  Filter,
  RefreshCw,
  Award,
  Ban,
  HelpCircle,
  CalendarDays,
  UserCheck,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { admissionsApi } from '@/services/api/admissionsApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import {
  AcademicYear,
  AdmissionApplication,
  AdmissionApplicationCreate,
  AdmissionApplicationStatus,
  AdmissionCycle,
  AdmissionCycleCreate,
  AdmissionCycleStatus,
  AdmissionCycleUpdate,
  AdmissionDecision,
  AdmissionDecisionCreate,
  AdmissionDecisionType,
  Applicant,
  ApplicantCreate,
  ApplicantStatus,
  ApplicantUpdate,
  ApplicationStatusHistory,
  SchoolClass,
  Section,
} from '@/types/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';

export const AdmissionsPage: React.FC = () => {
  const { user, permissions, roles } = useAuthStore();
  const isSuperAdmin =
    user?.is_super_admin ||
    roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');

  const hasPermission = (perm: string) => isSuperAdmin || permissions.includes(perm);

  const canCreate = hasPermission('admissions.create');
  const canUpdate = hasPermission('admissions.update');
  const canDelete = hasPermission('admissions.delete');
  const canReview = hasPermission('admissions.review');
  const canManage = hasPermission('admissions.manage');

  // Active Navigation Tab
  const [activeTab, setActiveTab] = useState<
    'dashboard' | 'cycles' | 'applicants' | 'applications'
  >('dashboard');

  // Global Notification / Alert
  const [pageAlert, setPageAlert] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Reference Data
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [schoolClasses, setSchoolClasses] = useState<SchoolClass[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [cyclesList, setCyclesList] = useState<AdmissionCycle[]>([]);
  const [applicantsList, setApplicantsList] = useState<Applicant[]>([]);

  // ---------------------------------------------------------------------------
  // 1. Dashboard State
  // ---------------------------------------------------------------------------
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardMetrics, setDashboardMetrics] = useState<{
    totalCycles: number;
    activeCycles: number;
    totalApplicants: number;
    totalApplications: number;
    draftCount: number;
    submittedCount: number;
    underReviewCount: number;
    acceptedCount: number;
    waitlistedCount: number;
    rejectedCount: number;
    withdrawnCount: number;
  }>({
    totalCycles: 0,
    activeCycles: 0,
    totalApplicants: 0,
    totalApplications: 0,
    draftCount: 0,
    submittedCount: 0,
    underReviewCount: 0,
    acceptedCount: 0,
    waitlistedCount: 0,
    rejectedCount: 0,
    withdrawnCount: 0,
  });

  // ---------------------------------------------------------------------------
  // 2. Admission Cycles State
  // ---------------------------------------------------------------------------
  const [cycles, setCycles] = useState<AdmissionCycle[]>([]);
  const [cycleSearch, setCycleSearch] = useState('');
  const [cycleStatusFilter, setCycleStatusFilter] = useState('');
  const [cyclePage, setCyclePage] = useState(1);
  const [cycleTotalPages, setCycleTotalPages] = useState(1);
  const [loadingCycles, setLoadingCycles] = useState(false);
  const [cycleError, setCycleError] = useState<string | null>(null);

  const [showCycleModal, setShowCycleModal] = useState(false);
  const [editingCycle, setEditingCycle] = useState<AdmissionCycle | null>(null);
  const [cycleFormData, setCycleFormData] = useState<AdmissionCycleCreate>({
    academic_year_id: '',
    name: '',
    code: '',
    start_date: '',
    end_date: '',
    description: '',
    status: 'DRAFT',
    is_active: true,
  });
  const [cycleSaving, setCycleSaving] = useState(false);
  const [deleteCycleTarget, setDeleteCycleTarget] = useState<AdmissionCycle | null>(null);

  // ---------------------------------------------------------------------------
  // 3. Applicants / Prospects State
  // ---------------------------------------------------------------------------
  const [applicants, setApplicants] = useState<Applicant[]>([]);
  const [applicantSearch, setApplicantSearch] = useState('');
  const [applicantStatusFilter, setApplicantStatusFilter] = useState('');
  const [applicantCycleFilter, setApplicantCycleFilter] = useState('');
  const [applicantPage, setApplicantPage] = useState(1);
  const [applicantTotalPages, setApplicantTotalPages] = useState(1);
  const [loadingApplicants, setLoadingApplicants] = useState(false);
  const [applicantError, setApplicantError] = useState<string | null>(null);

  const [showApplicantModal, setShowApplicantModal] = useState(false);
  const [editingApplicant, setEditingApplicant] = useState<Applicant | null>(null);
  const [applicantFormData, setApplicantFormData] = useState<ApplicantCreate>({
    first_name: '',
    middle_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'MALE',
    email: '',
    phone: '',
    address: '',
    parent_name: '',
    parent_phone: '',
    parent_email: '',
    source: 'WALK_IN',
    admission_cycle_id: '',
    notes: '',
  });
  const [applicantSaving, setApplicantSaving] = useState(false);
  const [deleteApplicantTarget, setDeleteApplicantTarget] = useState<Applicant | null>(null);

  // ---------------------------------------------------------------------------
  // 4. Applications Pipeline State
  // ---------------------------------------------------------------------------
  const [applications, setApplications] = useState<AdmissionApplication[]>([]);
  const [appSearch, setAppSearch] = useState('');
  const [appStatusFilter, setAppStatusFilter] = useState('');
  const [appCycleFilter, setAppCycleFilter] = useState('');
  const [appClassFilter, setAppClassFilter] = useState('');
  const [appPage, setAppPage] = useState(1);
  const [appTotalPages, setAppTotalPages] = useState(1);
  const [loadingApplications, setLoadingApplications] = useState(false);
  const [applicationError, setApplicationError] = useState<string | null>(null);

  // Application Creation
  const [showAppModal, setShowAppModal] = useState(false);
  const [appFormData, setAppFormData] = useState<AdmissionApplicationCreate>({
    applicant_id: '',
    admission_cycle_id: '',
    academic_year_id: '',
    target_class_id: '',
    target_section_id: '',
    remarks: '',
  });
  const [appSaving, setAppSaving] = useState(false);

  // Lifecycle Action Modals
  const [submitTarget, setSubmitTarget] = useState<AdmissionApplication | null>(null);
  const [submitRemarks, setSubmitRemarks] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);

  const [reviewTarget, setReviewTarget] = useState<AdmissionApplication | null>(null);
  const [reviewRemarks, setReviewRemarks] = useState('');
  const [reviewingAction, setReviewingAction] = useState(false);

  const [decisionTarget, setDecisionTarget] = useState<AdmissionApplication | null>(null);
  const [decisionType, setDecisionType] = useState<AdmissionDecisionType>('ACCEPTED');
  const [decisionComments, setDecisionComments] = useState('');
  const [decisionConditions, setDecisionConditions] = useState('');
  const [decidingAction, setDecidingAction] = useState(false);

  const [withdrawTarget, setWithdrawTarget] = useState<AdmissionApplication | null>(null);
  const [withdrawReason, setWithdrawReason] = useState('');
  const [withdrawRemarks, setWithdrawRemarks] = useState('');
  const [withdrawingAction, setWithdrawingAction] = useState(false);

  // Detail Dossier View
  const [dossierApp, setDossierApp] = useState<AdmissionApplication | null>(null);
  const [dossierHistory, setDossierHistory] = useState<ApplicationStatusHistory[]>([]);
  const [dossierDecisions, setDossierDecisions] = useState<AdmissionDecision[]>([]);
  const [loadingDossier, setLoadingDossier] = useState(false);

  // Load Reference Data
  const loadReferenceData = async () => {
    try {
      const [ayRes, clsRes, cycRes, appRes] = await Promise.all([
        academicYearsApi.getAcademicYears({ page_size: 100 }),
        schoolClassesApi.getSchoolClasses({ page_size: 100 }),
        admissionsApi.listCycles({ page_size: 100 }),
        admissionsApi.listApplicants({ page_size: 100 }),
      ]);
      setAcademicYears(ayRes.items || []);
      setSchoolClasses(clsRes.items || []);
      setCyclesList(cycRes.items || []);
      setApplicantsList(appRes.items || []);
      if (clsRes.items && clsRes.items.length > 0) {
        try {
          const secRes = await sectionsApi.getSectionsByClass(clsRes.items[0].id);
          setSections(secRes.items || []);
        } catch (e) {
          // fallback
        }
      }
    } catch (err: any) {
      console.error('Failed to load admissions reference data:', err);
    }
  };

  // Load Dashboard Summary
  const loadDashboard = async () => {
    setLoadingDashboard(true);
    try {
      const [cyclesRes, applicantsRes, appsRes] = await Promise.all([
        admissionsApi.listCycles({ page_size: 100 }),
        admissionsApi.listApplicants({ page_size: 100 }),
        admissionsApi.listApplications({ page_size: 100 }),
      ]);

      const cycleItems = cyclesRes.items || [];
      const appItems = appsRes.items || [];

      setDashboardMetrics({
        totalCycles: cyclesRes.total || 0,
        activeCycles: cycleItems.filter((c) => c.status === 'ACTIVE').length,
        totalApplicants: applicantsRes.total || 0,
        totalApplications: appsRes.total || 0,
        draftCount: appItems.filter((a) => a.status === 'DRAFT').length,
        submittedCount: appItems.filter((a) => a.status === 'SUBMITTED').length,
        underReviewCount: appItems.filter((a) => a.status === 'UNDER_REVIEW').length,
        acceptedCount: appItems.filter((a) => a.status === 'ACCEPTED').length,
        waitlistedCount: appItems.filter((a) => a.status === 'WAITLISTED').length,
        rejectedCount: appItems.filter((a) => a.status === 'REJECTED').length,
        withdrawnCount: appItems.filter((a) => a.status === 'WITHDRAWN').length,
      });
    } catch (err: any) {
      console.error('Failed to load admissions dashboard metrics:', err);
    } finally {
      setLoadingDashboard(false);
    }
  };

  // Load Cycles
  const fetchCycles = async () => {
    setLoadingCycles(true);
    setCycleError(null);
    try {
      const res = await admissionsApi.listCycles({
        search: cycleSearch || undefined,
        status: (cycleStatusFilter as AdmissionCycleStatus) || undefined,
        page: cyclePage,
        page_size: 10,
      });
      setCycles(res.items || []);
      setCycleTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setCycleError(err.response?.data?.detail || 'Failed to load admission cycles.');
    } finally {
      setLoadingCycles(false);
    }
  };

  // Load Applicants
  const fetchApplicants = async () => {
    setLoadingApplicants(true);
    setApplicantError(null);
    try {
      const res = await admissionsApi.listApplicants({
        search: applicantSearch || undefined,
        status: (applicantStatusFilter as ApplicantStatus) || undefined,
        admission_cycle_id: applicantCycleFilter || undefined,
        page: applicantPage,
        page_size: 10,
      });
      setApplicants(res.items || []);
      setApplicantTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setApplicantError(err.response?.data?.detail || 'Failed to load applicants.');
    } finally {
      setLoadingApplicants(false);
    }
  };

  // Load Applications
  const fetchApplications = async () => {
    setLoadingApplications(true);
    setApplicationError(null);
    try {
      const res = await admissionsApi.listApplications({
        search: appSearch || undefined,
        status: (appStatusFilter as AdmissionApplicationStatus) || undefined,
        admission_cycle_id: appCycleFilter || undefined,
        target_class_id: appClassFilter || undefined,
        page: appPage,
        page_size: 10,
      });
      setApplications(res.items || []);
      setAppTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setApplicationError(err.response?.data?.detail || 'Failed to load applications.');
    } finally {
      setLoadingApplications(false);
    }
  };

  useEffect(() => {
    loadReferenceData();
  }, []);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboard();
    } else if (activeTab === 'cycles') {
      fetchCycles();
    } else if (activeTab === 'applicants') {
      fetchApplicants();
    } else if (activeTab === 'applications') {
      fetchApplications();
    }
  }, [
    activeTab,
    cyclePage,
    cycleSearch,
    cycleStatusFilter,
    applicantPage,
    applicantSearch,
    applicantStatusFilter,
    applicantCycleFilter,
    appPage,
    appSearch,
    appStatusFilter,
    appCycleFilter,
    appClassFilter,
  ]);

  // Handle Cycle Create/Update
  const handleSaveCycle = async (e: React.FormEvent) => {
    e.preventDefault();
    setCycleSaving(true);
    try {
      if (editingCycle) {
        await admissionsApi.updateCycle(editingCycle.id, {
          name: cycleFormData.name,
          code: cycleFormData.code,
          start_date: cycleFormData.start_date,
          end_date: cycleFormData.end_date,
          description: cycleFormData.description || null,
          status: cycleFormData.status,
          is_active: cycleFormData.is_active,
        });
        setPageAlert({ type: 'success', message: 'Admission cycle updated successfully.' });
      } else {
        await admissionsApi.createCycle(cycleFormData);
        setPageAlert({ type: 'success', message: 'Admission cycle created successfully.' });
      }
      setShowCycleModal(false);
      setEditingCycle(null);
      fetchCycles();
      loadReferenceData();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to save admission cycle.',
      });
    } finally {
      setCycleSaving(false);
    }
  };

  // Handle Cycle Delete
  const handleDeleteCycle = async () => {
    if (!deleteCycleTarget) return;
    try {
      await admissionsApi.deleteCycle(deleteCycleTarget.id);
      setPageAlert({ type: 'success', message: 'Admission cycle deactivated successfully.' });
      setDeleteCycleTarget(null);
      fetchCycles();
      loadReferenceData();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to delete admission cycle.',
      });
    }
  };

  // Handle Applicant Create/Update
  const handleSaveApplicant = async (e: React.FormEvent) => {
    e.preventDefault();
    setApplicantSaving(true);
    try {
      if (editingApplicant) {
        await admissionsApi.updateApplicant(editingApplicant.id, {
          first_name: applicantFormData.first_name,
          middle_name: applicantFormData.middle_name || null,
          last_name: applicantFormData.last_name,
          date_of_birth: applicantFormData.date_of_birth,
          gender: applicantFormData.gender,
          email: applicantFormData.email || null,
          phone: applicantFormData.phone || null,
          address: applicantFormData.address || null,
          parent_name: applicantFormData.parent_name || null,
          parent_phone: applicantFormData.parent_phone || null,
          parent_email: applicantFormData.parent_email || null,
          source: applicantFormData.source || null,
          status: applicantFormData.status,
          admission_cycle_id: applicantFormData.admission_cycle_id || null,
          notes: applicantFormData.notes || null,
        });
        setPageAlert({ type: 'success', message: 'Applicant updated successfully.' });
      } else {
        await admissionsApi.createApplicant({
          ...applicantFormData,
          admission_cycle_id: applicantFormData.admission_cycle_id || null,
          email: applicantFormData.email || null,
          phone: applicantFormData.phone || null,
          address: applicantFormData.address || null,
          parent_name: applicantFormData.parent_name || null,
          parent_phone: applicantFormData.parent_phone || null,
          parent_email: applicantFormData.parent_email || null,
          notes: applicantFormData.notes || null,
        });
        setPageAlert({ type: 'success', message: 'Applicant registered successfully.' });
      }
      setShowApplicantModal(false);
      setEditingApplicant(null);
      fetchApplicants();
      loadReferenceData();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to save applicant.',
      });
    } finally {
      setApplicantSaving(false);
    }
  };

  // Handle Applicant Delete
  const handleDeleteApplicant = async () => {
    if (!deleteApplicantTarget) return;
    try {
      await admissionsApi.deleteApplicant(deleteApplicantTarget.id);
      setPageAlert({ type: 'success', message: 'Applicant deleted successfully.' });
      setDeleteApplicantTarget(null);
      fetchApplicants();
      loadReferenceData();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to delete applicant.',
      });
    }
  };

  // Handle Application Create
  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    setAppSaving(true);
    try {
      await admissionsApi.createApplication({
        ...appFormData,
        target_section_id: appFormData.target_section_id || null,
        remarks: appFormData.remarks || null,
      });
      setPageAlert({
        type: 'success',
        message: 'Admission application created in DRAFT status.',
      });
      setShowAppModal(false);
      setAppFormData({
        applicant_id: '',
        admission_cycle_id: '',
        academic_year_id: '',
        target_class_id: '',
        target_section_id: '',
        remarks: '',
      });
      fetchApplications();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to create application.',
      });
    } finally {
      setAppSaving(false);
    }
  };

  // Handle Lifecycle Workflows
  const handleSubmitApplication = async () => {
    if (!submitTarget) return;
    setSubmittingAction(true);
    try {
      await admissionsApi.submitApplication(submitTarget.id, {
        remarks: submitRemarks || undefined,
      });
      setPageAlert({ type: 'success', message: 'Application submitted successfully.' });
      setSubmitTarget(null);
      setSubmitRemarks('');
      fetchApplications();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to submit application.',
      });
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleReviewApplication = async () => {
    if (!reviewTarget) return;
    setReviewingAction(true);
    try {
      await admissionsApi.reviewApplication(reviewTarget.id, {
        remarks: reviewRemarks || undefined,
      });
      setPageAlert({ type: 'success', message: 'Application moved into review.' });
      setReviewTarget(null);
      setReviewRemarks('');
      fetchApplications();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to start review.',
      });
    } finally {
      setReviewingAction(false);
    }
  };

  const handleRecordDecision = async () => {
    if (!decisionTarget) return;
    setDecidingAction(true);
    try {
      await admissionsApi.recordDecision(decisionTarget.id, {
        decision_type: decisionType,
        comments: decisionComments || undefined,
        conditions: decisionConditions || undefined,
      });
      setPageAlert({
        type: 'success',
        message: `Decision (${decisionType}) recorded successfully.`,
      });
      setDecisionTarget(null);
      setDecisionComments('');
      setDecisionConditions('');
      fetchApplications();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to record decision.',
      });
    } finally {
      setDecidingAction(false);
    }
  };

  const handleWithdrawApplication = async () => {
    if (!withdrawTarget || !withdrawReason) return;
    setWithdrawingAction(true);
    try {
      await admissionsApi.withdrawApplication(withdrawTarget.id, {
        reason: withdrawReason,
        remarks: withdrawRemarks || undefined,
      });
      setPageAlert({ type: 'success', message: 'Application withdrawn successfully.' });
      setWithdrawTarget(null);
      setWithdrawReason('');
      setWithdrawRemarks('');
      fetchApplications();
    } catch (err: any) {
      setPageAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to withdraw application.',
      });
    } finally {
      setWithdrawingAction(false);
    }
  };

  // Load Application Dossier Details
  const handleOpenDossier = async (app: AdmissionApplication) => {
    setDossierApp(app);
    setLoadingDossier(true);
    try {
      const [histRes, decsRes] = await Promise.all([
        admissionsApi.getApplicationHistory(app.id),
        admissionsApi.getApplicationDecisions(app.id),
      ]);
      setDossierHistory(histRes.items || []);
      setDossierDecisions(decsRes.items || []);
    } catch (err: any) {
      console.error('Failed to load dossier history/decisions:', err);
    } finally {
      setLoadingDossier(false);
    }
  };

  // Helper Badge Color
  const getStatusBadge = (status: AdmissionApplicationStatus | ApplicantStatus | AdmissionCycleStatus) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="neutral">DRAFT</Badge>;
      case 'ACTIVE':
        return <Badge variant="success">ACTIVE</Badge>;
      case 'CLOSED':
      case 'ARCHIVED':
        return <Badge variant="neutral">{status}</Badge>;
      case 'PROSPECT':
        return <Badge variant="info">PROSPECT</Badge>;
      case 'APPLIED':
      case 'SUBMITTED':
        return <Badge variant="warning">SUBMITTED</Badge>;
      case 'UNDER_REVIEW':
        return <Badge variant="info">UNDER REVIEW</Badge>;
      case 'ACCEPTED':
      case 'ENROLLED':
        return <Badge variant="success">{status}</Badge>;
      case 'WAITLISTED':
        return <Badge variant="warning">WAITLISTED</Badge>;
      case 'REJECTED':
        return <Badge variant="error">REJECTED</Badge>;
      case 'WITHDRAWN':
        return <Badge variant="neutral">WITHDRAWN</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  // Resolve Names
  const getApplicantName = (applicantId: string) => {
    const a = applicantsList.find((x) => x.id === applicantId);
    if (!a) return applicantId.slice(0, 8);
    return `${a.first_name} ${a.last_name} (${a.applicant_number})`;
  };

  const getCycleName = (cycleId: string) => {
    const c = cyclesList.find((x) => x.id === cycleId);
    return c ? `${c.name} (${c.code})` : cycleId.slice(0, 8);
  };

  const getClassName = (classId: string) => {
    const cls = schoolClasses.find((x) => x.id === classId);
    return cls ? cls.name : classId.slice(0, 8);
  };

  const getYearName = (ayId: string) => {
    const ay = academicYears.find((x) => x.id === ayId);
    return ay ? ay.name : ayId.slice(0, 8);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-divider dark:border-stone-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <UserPlus className="w-6 h-6 text-brand-500" />
            <h1 className="text-2xl font-serif font-bold text-ink dark:text-stone-100">
              Admissions Management
            </h1>
          </div>
          <p className="text-sm text-ink-muted dark:text-stone-400 mt-1">
            Enterprise Admissions Pipeline · Prospects, Applications, Reviews & Decisions
          </p>
        </div>

        {/* Action Header Button */}
        {activeTab === 'cycles' && canCreate && (
          <Button
            onClick={() => {
              setEditingCycle(null);
              setCycleFormData({
                academic_year_id: academicYears[0]?.id || '',
                name: '',
                code: '',
                start_date: '',
                end_date: '',
                description: '',
                status: 'DRAFT',
                is_active: true,
              });
              setShowCycleModal(true);
            }}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Cycle</span>
          </Button>
        )}

        {activeTab === 'applicants' && canCreate && (
          <Button
            onClick={() => {
              setEditingApplicant(null);
              setApplicantFormData({
                first_name: '',
                middle_name: '',
                last_name: '',
                date_of_birth: '',
                gender: 'MALE',
                email: '',
                phone: '',
                address: '',
                parent_name: '',
                parent_phone: '',
                parent_email: '',
                source: 'WALK_IN',
                admission_cycle_id: cyclesList[0]?.id || '',
                notes: '',
              });
              setShowApplicantModal(true);
            }}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Register Applicant</span>
          </Button>
        )}

        {activeTab === 'applications' && canCreate && (
          <Button
            onClick={() => {
              setAppFormData({
                applicant_id: applicantsList[0]?.id || '',
                admission_cycle_id: cyclesList[0]?.id || '',
                academic_year_id: academicYears[0]?.id || '',
                target_class_id: schoolClasses[0]?.id || '',
                target_section_id: '',
                remarks: '',
              });
              setShowAppModal(true);
            }}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Application</span>
          </Button>
        )}
      </div>

      {/* Global Alert Notification */}
      {pageAlert && (
        <Alert
          type={pageAlert.type === 'success' ? 'success' : 'error'}
          onClose={() => setPageAlert(null)}
        >
          {pageAlert.message}
        </Alert>
      )}

      {/* Workstation Tab Bar */}
      <div className="flex border-b border-divider dark:border-stone-800 space-x-1 overflow-x-auto">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'dashboard'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Pipeline Dashboard</span>
        </button>

        <button
          onClick={() => setActiveTab('cycles')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'cycles'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200'
          }`}
        >
          <CalendarDays className="w-4 h-4" />
          <span>Admission Cycles</span>
        </button>

        <button
          onClick={() => setActiveTab('applicants')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'applicants'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Applicants Directory</span>
        </button>

        <button
          onClick={() => setActiveTab('applications')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'applications'
              ? 'border-brand-500 text-brand-600 dark:text-brand-400'
              : 'border-transparent text-ink-muted hover:text-ink dark:text-stone-400 dark:hover:text-stone-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Application Pipeline</span>
        </button>
      </div>

      {/* ===================================================================== */}
      {/* 1. PIPELINE DASHBOARD TAB                                             */}
      {/* ===================================================================== */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {loadingDashboard ? (
            <LoadingState message="Loading admissions pipeline metrics..." />
          ) : (
            <>
              {/* Metric Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-mono uppercase tracking-wider text-ink-muted">
                      Active Intake Cycles
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-ink dark:text-stone-100">
                      {dashboardMetrics.activeCycles}{' '}
                      <span className="text-xs font-normal text-ink-muted">
                        / {dashboardMetrics.totalCycles} Total
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-mono uppercase tracking-wider text-ink-muted">
                      Registered Prospects
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-ink dark:text-stone-100">
                      {dashboardMetrics.totalApplicants}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-mono uppercase tracking-wider text-ink-muted">
                      Total Applications
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-ink dark:text-stone-100">
                      {dashboardMetrics.totalApplications}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-mono uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                      Accepted Offers
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                      {dashboardMetrics.acceptedCount}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Status Breakdown Grid */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">
                    Applications Pipeline Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-3 text-center">
                    <div className="p-3 bg-stone-50 dark:bg-stone-900 rounded-md border border-divider dark:border-stone-800">
                      <p className="text-xs font-mono text-ink-muted uppercase">Draft</p>
                      <p className="text-xl font-bold text-ink dark:text-stone-100 mt-1">
                        {dashboardMetrics.draftCount}
                      </p>
                    </div>

                    <div className="p-3 bg-amber-50/50 dark:bg-amber-950/20 rounded-md border border-amber-200/50 dark:border-amber-900/30">
                      <p className="text-xs font-mono text-amber-600 dark:text-amber-400 uppercase">
                        Submitted
                      </p>
                      <p className="text-xl font-bold text-amber-700 dark:text-amber-300 mt-1">
                        {dashboardMetrics.submittedCount}
                      </p>
                    </div>

                    <div className="p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-md border border-blue-200/50 dark:border-blue-900/30">
                      <p className="text-xs font-mono text-blue-600 dark:text-blue-400 uppercase">
                        Under Review
                      </p>
                      <p className="text-xl font-bold text-blue-700 dark:text-blue-300 mt-1">
                        {dashboardMetrics.underReviewCount}
                      </p>
                    </div>

                    <div className="p-3 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-md border border-emerald-200/50 dark:border-emerald-900/30">
                      <p className="text-xs font-mono text-emerald-600 dark:text-emerald-400 uppercase">
                        Accepted
                      </p>
                      <p className="text-xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">
                        {dashboardMetrics.acceptedCount}
                      </p>
                    </div>

                    <div className="p-3 bg-purple-50/50 dark:bg-purple-950/20 rounded-md border border-purple-200/50 dark:border-purple-900/30">
                      <p className="text-xs font-mono text-purple-600 dark:text-purple-400 uppercase">
                        Waitlisted
                      </p>
                      <p className="text-xl font-bold text-purple-700 dark:text-purple-300 mt-1">
                        {dashboardMetrics.waitlistedCount}
                      </p>
                    </div>

                    <div className="p-3 bg-rose-50/50 dark:bg-rose-950/20 rounded-md border border-rose-200/50 dark:border-rose-900/30">
                      <p className="text-xs font-mono text-rose-600 dark:text-rose-400 uppercase">
                        Rejected
                      </p>
                      <p className="text-xl font-bold text-rose-700 dark:text-rose-300 mt-1">
                        {dashboardMetrics.rejectedCount}
                      </p>
                    </div>

                    <div className="p-3 bg-stone-100/50 dark:bg-stone-800/50 rounded-md border border-divider dark:border-stone-700">
                      <p className="text-xs font-mono text-stone-500 uppercase">Withdrawn</p>
                      <p className="text-xl font-bold text-stone-600 dark:text-stone-300 mt-1">
                        {dashboardMetrics.withdrawnCount}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 2. ADMISSION CYCLES TAB                                               */}
      {/* ===================================================================== */}
      {activeTab === 'cycles' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-ink-muted" />
              <Input
                placeholder="Search cycles by name or code..."
                value={cycleSearch}
                onChange={(e) => {
                  setCycleSearch(e.target.value);
                  setCyclePage(1);
                }}
                className="pl-9"
              />
            </div>
            <select
              value={cycleStatusFilter}
              onChange={(e) => {
                setCycleStatusFilter(e.target.value);
                setCyclePage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="CLOSED">CLOSED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>

          {cycleError ? (
            <ErrorState message={cycleError} onRetry={fetchCycles} />
          ) : loadingCycles ? (
            <LoadingState message="Loading admission cycles..." />
          ) : cycles.length === 0 ? (
            <EmptyState
              title="No admission cycles found"
              description="Create an admission cycle to start receiving applicant registrations."
            />
          ) : (
            <div className="border border-divider dark:border-stone-800 rounded-lg overflow-hidden bg-paper dark:bg-stone-900">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-paper-dim dark:bg-stone-950/50 text-xs font-mono uppercase text-ink-muted border-b border-divider dark:border-stone-800">
                    <tr>
                      <th className="px-4 py-3">Cycle Name / Code</th>
                      <th className="px-4 py-3">Academic Year</th>
                      <th className="px-4 py-3">Intake Period</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-divider dark:divide-stone-800">
                    {cycles.map((c) => (
                      <tr key={c.id} className="hover:bg-stone-50/50 dark:hover:bg-stone-800/30">
                        <td className="px-4 py-3">
                          <div className="font-medium text-ink dark:text-stone-100">{c.name}</div>
                          <div className="text-xs font-mono text-ink-muted">{c.code}</div>
                        </td>
                        <td className="px-4 py-3">{getYearName(c.academic_year_id)}</td>
                        <td className="px-4 py-3 font-mono text-xs">
                          {c.start_date} → {c.end_date}
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(c.status)}</td>
                        <td className="px-4 py-3 text-right space-x-2">
                          {canUpdate && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setEditingCycle(c);
                                setCycleFormData({
                                  academic_year_id: c.academic_year_id,
                                  name: c.name,
                                  code: c.code,
                                  start_date: c.start_date,
                                  end_date: c.end_date,
                                  description: c.description || '',
                                  status: c.status,
                                  is_active: c.is_active,
                                });
                                setShowCycleModal(true);
                              }}
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-rose-600 hover:text-rose-700"
                              onClick={() => setDeleteCycleTarget(c)}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-3 border-t border-divider dark:border-stone-800 flex justify-end">
                <Pagination
                  page={cyclePage}
                  totalPages={cycleTotalPages}
                  onPageChange={setCyclePage}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 3. APPLICANTS DIRECTORY TAB                                           */}
      {/* ===================================================================== */}
      {activeTab === 'applicants' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-ink-muted" />
              <Input
                placeholder="Search by name, applicant #..."
                value={applicantSearch}
                onChange={(e) => {
                  setApplicantSearch(e.target.value);
                  setApplicantPage(1);
                }}
                className="pl-9"
              />
            </div>
            <select
              value={applicantStatusFilter}
              onChange={(e) => {
                setApplicantStatusFilter(e.target.value);
                setApplicantPage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Applicant Statuses</option>
              <option value="PROSPECT">PROSPECT</option>
              <option value="APPLIED">APPLIED</option>
              <option value="ENROLLED">ENROLLED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="WITHDRAWN">WITHDRAWN</option>
            </select>
            <select
              value={applicantCycleFilter}
              onChange={(e) => {
                setApplicantCycleFilter(e.target.value);
                setApplicantPage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Cycles</option>
              {cyclesList.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {applicantError ? (
            <ErrorState message={applicantError} onRetry={fetchApplicants} />
          ) : loadingApplicants ? (
            <LoadingState message="Loading applicants directory..." />
          ) : applicants.length === 0 ? (
            <EmptyState
              title="No applicants registered"
              description="Register new prospects or applicants to manage admissions intake."
            />
          ) : (
            <div className="border border-divider dark:border-stone-800 rounded-lg overflow-hidden bg-paper dark:bg-stone-900">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-paper-dim dark:bg-stone-950/50 text-xs font-mono uppercase text-ink-muted border-b border-divider dark:border-stone-800">
                    <tr>
                      <th className="px-4 py-3">Applicant #</th>
                      <th className="px-4 py-3">Full Name / Gender</th>
                      <th className="px-4 py-3">Date of Birth</th>
                      <th className="px-4 py-3">Parent / Guardian</th>
                      <th className="px-4 py-3">Contact</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-divider dark:divide-stone-800">
                    {applicants.map((a) => (
                      <tr key={a.id} className="hover:bg-stone-50/50 dark:hover:bg-stone-800/30">
                        <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600 dark:text-brand-400">
                          {a.applicant_number}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-ink dark:text-stone-100">
                            {a.first_name} {a.middle_name ? `${a.middle_name} ` : ''}
                            {a.last_name}
                          </div>
                          <div className="text-xs text-ink-muted">{a.gender}</div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">{a.date_of_birth}</td>
                        <td className="px-4 py-3">
                          <div>{a.parent_name || '—'}</div>
                          {a.parent_phone && (
                            <div className="text-xs text-ink-muted font-mono">{a.parent_phone}</div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {a.email && <div>{a.email}</div>}
                          {a.phone && <div className="font-mono text-ink-muted">{a.phone}</div>}
                          {!a.email && !a.phone && <span className="text-ink-muted">—</span>}
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(a.status)}</td>
                        <td className="px-4 py-3 text-right space-x-2">
                          {canUpdate && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setEditingApplicant(a);
                                setApplicantFormData({
                                  first_name: a.first_name,
                                  middle_name: a.middle_name || '',
                                  last_name: a.last_name,
                                  date_of_birth: a.date_of_birth,
                                  gender: a.gender,
                                  email: a.email || '',
                                  phone: a.phone || '',
                                  address: a.address || '',
                                  parent_name: a.parent_name || '',
                                  parent_phone: a.parent_phone || '',
                                  parent_email: a.parent_email || '',
                                  source: a.source || 'WALK_IN',
                                  admission_cycle_id: a.admission_cycle_id || '',
                                  notes: a.notes || '',
                                });
                                setShowApplicantModal(true);
                              }}
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-rose-600 hover:text-rose-700"
                              onClick={() => setDeleteApplicantTarget(a)}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-3 border-t border-divider dark:border-stone-800 flex justify-end">
                <Pagination
                  page={applicantPage}
                  totalPages={applicantTotalPages}
                  onPageChange={setApplicantPage}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 4. APPLICATIONS PIPELINE TAB                                          */}
      {/* ===================================================================== */}
      {activeTab === 'applications' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-ink-muted" />
              <Input
                placeholder="Search application #..."
                value={appSearch}
                onChange={(e) => {
                  setAppSearch(e.target.value);
                  setAppPage(1);
                }}
                className="pl-9"
              />
            </div>
            <select
              value={appStatusFilter}
              onChange={(e) => {
                setAppStatusFilter(e.target.value);
                setAppPage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Pipeline Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="SUBMITTED">SUBMITTED</option>
              <option value="UNDER_REVIEW">UNDER REVIEW</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="WAITLISTED">WAITLISTED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="WITHDRAWN">WITHDRAWN</option>
            </select>
            <select
              value={appCycleFilter}
              onChange={(e) => {
                setAppCycleFilter(e.target.value);
                setAppPage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Admission Cycles</option>
              {cyclesList.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <select
              value={appClassFilter}
              onChange={(e) => {
                setAppClassFilter(e.target.value);
                setAppPage(1);
              }}
              className="px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">All Classes</option>
              {schoolClasses.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>
          </div>

          {applicationError ? (
            <ErrorState message={applicationError} onRetry={fetchApplications} />
          ) : loadingApplications ? (
            <LoadingState message="Loading applications pipeline..." />
          ) : applications.length === 0 ? (
            <EmptyState
              title="No admission applications found"
              description="Create an application to initiate the review and decision lifecycle."
            />
          ) : (
            <div className="border border-divider dark:border-stone-800 rounded-lg overflow-hidden bg-paper dark:bg-stone-900">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-paper-dim dark:bg-stone-950/50 text-xs font-mono uppercase text-ink-muted border-b border-divider dark:border-stone-800">
                    <tr>
                      <th className="px-4 py-3">App Number</th>
                      <th className="px-4 py-3">Applicant</th>
                      <th className="px-4 py-3">Cycle / Class</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Pipeline Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-divider dark:divide-stone-800">
                    {applications.map((app) => (
                      <tr
                        key={app.id}
                        className="hover:bg-stone-50/50 dark:hover:bg-stone-800/30 transition-colors"
                      >
                        <td className="px-4 py-3 font-mono font-semibold text-xs text-brand-600 dark:text-brand-400">
                          {app.application_number}
                        </td>
                        <td className="px-4 py-3 font-medium text-ink dark:text-stone-100">
                          {getApplicantName(app.applicant_id)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-xs">{getCycleName(app.admission_cycle_id)}</div>
                          <div className="text-xs text-ink-muted font-medium">
                            {getClassName(app.target_class_id)}
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">{app.application_date}</td>
                        <td className="px-4 py-3">{getStatusBadge(app.status)}</td>
                        <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                          {/* Dossier Detail Button */}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleOpenDossier(app)}
                            title="View Dossier & History"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </Button>

                          {/* DRAFT -> SUBMIT */}
                          {app.status === 'DRAFT' && canUpdate && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSubmitTarget(app);
                                setSubmitRemarks('');
                              }}
                              className="text-amber-600 border-amber-300 dark:border-amber-800 hover:bg-amber-50 dark:hover:bg-amber-950/30"
                            >
                              <Send className="w-3 h-3 mr-1" />
                              Submit
                            </Button>
                          )}

                          {/* SUBMITTED -> REVIEW */}
                          {app.status === 'SUBMITTED' && canReview && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setReviewTarget(app);
                                setReviewRemarks('');
                              }}
                              className="text-blue-600 border-blue-300 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-950/30"
                            >
                              <ArrowRight className="w-3 h-3 mr-1" />
                              Review
                            </Button>
                          )}

                          {/* UNDER_REVIEW -> DECISION */}
                          {app.status === 'UNDER_REVIEW' && canManage && (
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => {
                                setDecisionTarget(app);
                                setDecisionType('ACCEPTED');
                                setDecisionComments('');
                                setDecisionConditions('');
                              }}
                            >
                              <Award className="w-3 h-3 mr-1" />
                              Decision
                            </Button>
                          )}

                          {/* WITHDRAW (if not finalized/withdrawn) */}
                          {app.status !== 'WITHDRAWN' && canUpdate && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-stone-500 hover:text-stone-700 dark:hover:text-stone-300"
                              onClick={() => {
                                setWithdrawTarget(app);
                                setWithdrawReason('');
                                setWithdrawRemarks('');
                              }}
                              title="Withdraw Application"
                            >
                              <Ban className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-3 border-t border-divider dark:border-stone-800 flex justify-end">
                <Pagination
                  page={appPage}
                  totalPages={appTotalPages}
                  onPageChange={setAppPage}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: CREATE / EDIT CYCLE                                            */}
      {/* ===================================================================== */}
      <Modal
        isOpen={showCycleModal}
        onClose={() => setShowCycleModal(false)}
        title={editingCycle ? 'Edit Admission Cycle' : 'Create Admission Cycle'}
      >
        <form onSubmit={handleSaveCycle} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Academic Year *
            </label>
            <select
              required
              disabled={!!editingCycle}
              value={cycleFormData.academic_year_id}
              onChange={(e) =>
                setCycleFormData({ ...cycleFormData, academic_year_id: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">Select Academic Year</option>
              {academicYears.map((ay) => (
                <option key={ay.id} value={ay.id}>
                  {ay.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Cycle Name *
              </label>
              <Input
                required
                value={cycleFormData.name}
                onChange={(e) => setCycleFormData({ ...cycleFormData, name: e.target.value })}
                placeholder="e.g. AY 2026-27 General Intake"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Cycle Code *
              </label>
              <Input
                required
                value={cycleFormData.code}
                onChange={(e) => setCycleFormData({ ...cycleFormData, code: e.target.value })}
                placeholder="e.g. CYC-2026-GEN"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Start Date *
              </label>
              <Input
                type="date"
                required
                value={cycleFormData.start_date}
                onChange={(e) => setCycleFormData({ ...cycleFormData, start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                End Date *
              </label>
              <Input
                type="date"
                required
                value={cycleFormData.end_date}
                onChange={(e) => setCycleFormData({ ...cycleFormData, end_date: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Status</label>
            <select
              value={cycleFormData.status}
              onChange={(e) =>
                setCycleFormData({
                  ...cycleFormData,
                  status: e.target.value as AdmissionCycleStatus,
                })
              }
              className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="DRAFT">DRAFT</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="CLOSED">CLOSED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Description
            </label>
            <Input
              value={cycleFormData.description || ''}
              onChange={(e) => setCycleFormData({ ...cycleFormData, description: e.target.value })}
              placeholder="Optional description / instructions"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button type="button" variant="ghost" onClick={() => setShowCycleModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={cycleSaving}>
              {cycleSaving ? 'Saving...' : editingCycle ? 'Update Cycle' : 'Create Cycle'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: CREATE / EDIT APPLICANT                                        */}
      {/* ===================================================================== */}
      <Modal
        isOpen={showApplicantModal}
        onClose={() => setShowApplicantModal(false)}
        title={editingApplicant ? 'Edit Applicant / Prospect' : 'Register Applicant / Prospect'}
      >
        <form onSubmit={handleSaveApplicant} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                First Name *
              </label>
              <Input
                required
                value={applicantFormData.first_name}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, first_name: e.target.value })
                }
                placeholder="First name"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Middle Name
              </label>
              <Input
                value={applicantFormData.middle_name || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, middle_name: e.target.value })
                }
                placeholder="Middle name"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Last Name *
              </label>
              <Input
                required
                value={applicantFormData.last_name}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, last_name: e.target.value })
                }
                placeholder="Last name"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Date of Birth *
              </label>
              <Input
                type="date"
                required
                value={applicantFormData.date_of_birth}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, date_of_birth: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Gender *
              </label>
              <select
                required
                value={applicantFormData.gender}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, gender: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Email</label>
              <Input
                type="email"
                value={applicantFormData.email || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, email: e.target.value })
                }
                placeholder="applicant@example.com"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Phone</label>
              <Input
                value={applicantFormData.phone || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, phone: e.target.value })
                }
                placeholder="+91-9876543210"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Parent / Guardian Name
              </label>
              <Input
                value={applicantFormData.parent_name || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, parent_name: e.target.value })
                }
                placeholder="Parent full name"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Parent Phone
              </label>
              <Input
                value={applicantFormData.parent_phone || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, parent_phone: e.target.value })
                }
                placeholder="Parent phone"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Parent Email
              </label>
              <Input
                type="email"
                value={applicantFormData.parent_email || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, parent_email: e.target.value })
                }
                placeholder="Parent email"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Admission Cycle
              </label>
              <select
                value={applicantFormData.admission_cycle_id || ''}
                onChange={(e) =>
                  setApplicantFormData({
                    ...applicantFormData,
                    admission_cycle_id: e.target.value,
                  })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="">No cycle linked</option>
                {cyclesList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Lead Source
              </label>
              <Input
                value={applicantFormData.source || ''}
                onChange={(e) =>
                  setApplicantFormData({ ...applicantFormData, source: e.target.value })
                }
                placeholder="e.g. WALK_IN, WEBSITE, REFERRAL"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Notes</label>
            <Input
              value={applicantFormData.notes || ''}
              onChange={(e) =>
                setApplicantFormData({ ...applicantFormData, notes: e.target.value })
              }
              placeholder="Internal counselor notes"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button type="button" variant="ghost" onClick={() => setShowApplicantModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={applicantSaving}>
              {applicantSaving ? 'Saving...' : editingApplicant ? 'Update' : 'Register Applicant'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: CREATE APPLICATION                                             */}
      {/* ===================================================================== */}
      <Modal
        isOpen={showAppModal}
        onClose={() => setShowAppModal(false)}
        title="Create Admission Application (Draft)"
      >
        <form onSubmit={handleCreateApplication} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Applicant *
            </label>
            <select
              required
              value={appFormData.applicant_id}
              onChange={(e) => setAppFormData({ ...appFormData, applicant_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
            >
              <option value="">Select Applicant</option>
              {applicantsList.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.first_name} {a.last_name} ({a.applicant_number})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Admission Cycle *
              </label>
              <select
                required
                value={appFormData.admission_cycle_id}
                onChange={(e) =>
                  setAppFormData({ ...appFormData, admission_cycle_id: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="">Select Cycle</option>
                {cyclesList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Academic Year *
              </label>
              <select
                required
                value={appFormData.academic_year_id}
                onChange={(e) =>
                  setAppFormData({ ...appFormData, academic_year_id: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="">Select Academic Year</option>
                {academicYears.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Target Class / Grade *
              </label>
              <select
                required
                value={appFormData.target_class_id}
                onChange={(e) =>
                  setAppFormData({ ...appFormData, target_class_id: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="">Select Target Class</option>
                {schoolClasses.map((cls) => (
                  <option key={cls.id} value={cls.id}>
                    {cls.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
                Target Section (Optional)
              </label>
              <select
                value={appFormData.target_section_id || ''}
                onChange={(e) =>
                  setAppFormData({ ...appFormData, target_section_id: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm"
              >
                <option value="">No section preference</option>
                {sections.map((sec) => (
                  <option key={sec.id} value={sec.id}>
                    {sec.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Remarks</label>
            <Input
              value={appFormData.remarks || ''}
              onChange={(e) => setAppFormData({ ...appFormData, remarks: e.target.value })}
              placeholder="Initial application notes"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button type="button" variant="ghost" onClick={() => setShowAppModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={appSaving}>
              {appSaving ? 'Creating...' : 'Create Application'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: SUBMIT APPLICATION                                             */}
      {/* ===================================================================== */}
      <Modal
        isOpen={!!submitTarget}
        onClose={() => setSubmitTarget(null)}
        title="Submit Admission Application"
      >
        <div className="space-y-4">
          <p className="text-sm text-ink-muted">
            Are you sure you want to submit application{' '}
            <strong className="text-ink dark:text-stone-100 font-mono">
              {submitTarget?.application_number}
            </strong>
            ? This will transition the application from <strong>DRAFT</strong> to{' '}
            <strong>SUBMITTED</strong>.
          </p>
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Submission Remarks (Optional)
            </label>
            <Input
              value={submitRemarks}
              onChange={(e) => setSubmitRemarks(e.target.value)}
              placeholder="e.g. All documents verified"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button variant="ghost" onClick={() => setSubmitTarget(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmitApplication} disabled={submittingAction}>
              {submittingAction ? 'Submitting...' : 'Submit Application'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: REVIEW APPLICATION                                             */}
      {/* ===================================================================== */}
      <Modal
        isOpen={!!reviewTarget}
        onClose={() => setReviewTarget(null)}
        title="Move Application Into Review"
      >
        <div className="space-y-4">
          <p className="text-sm text-ink-muted">
            Start officer evaluation for application{' '}
            <strong className="text-ink dark:text-stone-100 font-mono">
              {reviewTarget?.application_number}
            </strong>
            . Status will change to <strong>UNDER_REVIEW</strong>.
          </p>
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Reviewer Notes (Optional)
            </label>
            <Input
              value={reviewRemarks}
              onChange={(e) => setReviewRemarks(e.target.value)}
              placeholder="e.g. Initiating document scrutiny"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button variant="ghost" onClick={() => setReviewTarget(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleReviewApplication} disabled={reviewingAction}>
              {reviewingAction ? 'Processing...' : 'Start Review'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: RECORD ADMISSION DECISION                                      */}
      {/* ===================================================================== */}
      <Modal
        isOpen={!!decisionTarget}
        onClose={() => setDecisionTarget(null)}
        title="Record Admission Decision"
      >
        <div className="space-y-4">
          <p className="text-sm text-ink-muted">
            Record final decision for application{' '}
            <strong className="text-ink dark:text-stone-100 font-mono">
              {decisionTarget?.application_number}
            </strong>
            .
          </p>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Decision Outcome *
            </label>
            <select
              value={decisionType}
              onChange={(e) => setDecisionType(e.target.value as AdmissionDecisionType)}
              className="w-full px-3 py-2 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-sm font-semibold"
            >
              <option value="ACCEPTED">ACCEPTED — Offer Admission</option>
              <option value="WAITLISTED">WAITLISTED — Place on Waiting List</option>
              <option value="REJECTED">REJECTED — Deny Admission</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Decision Comments
            </label>
            <Input
              value={decisionComments}
              onChange={(e) => setDecisionComments(e.target.value)}
              placeholder="Reasoning or evaluation feedback"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Offer Conditions (Optional)
            </label>
            <Input
              value={decisionConditions}
              onChange={(e) => setDecisionConditions(e.target.value)}
              placeholder="e.g. Submit transfer certificate within 14 days"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button variant="ghost" onClick={() => setDecisionTarget(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleRecordDecision} disabled={decidingAction}>
              {decidingAction ? 'Recording...' : 'Commit Decision'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: WITHDRAW APPLICATION                                           */}
      {/* ===================================================================== */}
      <Modal
        isOpen={!!withdrawTarget}
        onClose={() => setWithdrawTarget(null)}
        title="Withdraw Application"
      >
        <div className="space-y-4">
          <p className="text-sm text-ink-muted">
            Are you sure you want to withdraw application{' '}
            <strong className="text-ink dark:text-stone-100 font-mono">
              {withdrawTarget?.application_number}
            </strong>
            ? This action cannot be reversed.
          </p>
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">
              Withdrawal Reason *
            </label>
            <Input
              required
              value={withdrawReason}
              onChange={(e) => setWithdrawReason(e.target.value)}
              placeholder="e.g. Parent relocated / Joined another school"
            />
          </div>
          <div>
            <label className="block text-xs font-mono uppercase text-ink-muted mb-1">Remarks</label>
            <Input
              value={withdrawRemarks}
              onChange={(e) => setWithdrawRemarks(e.target.value)}
              placeholder="Additional notes"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-divider dark:border-stone-800">
            <Button variant="ghost" onClick={() => setWithdrawTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              className="bg-rose-600 hover:bg-rose-700"
              onClick={handleWithdrawApplication}
              disabled={withdrawingAction || !withdrawReason}
            >
              {withdrawingAction ? 'Processing...' : 'Confirm Withdrawal'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ===================================================================== */}
      {/* MODAL: APPLICATION DETAIL DOSSIER                                     */}
      {/* ===================================================================== */}
      <Modal
        isOpen={!!dossierApp}
        onClose={() => setDossierApp(null)}
        title={`Application Dossier · ${dossierApp?.application_number || ''}`}
      >
        {dossierApp && (
          <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-1">
            {/* Overview Card */}
            <div className="p-4 bg-stone-50 dark:bg-stone-900 rounded-lg border border-divider dark:border-stone-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase text-ink-muted">Current Status</span>
                {getStatusBadge(dossierApp.status)}
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs pt-2">
                <div>
                  <span className="text-ink-muted">Applicant: </span>
                  <span className="font-semibold text-ink dark:text-stone-100">
                    {getApplicantName(dossierApp.applicant_id)}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted">Intake Cycle: </span>
                  <span className="font-semibold text-ink dark:text-stone-100">
                    {getCycleName(dossierApp.admission_cycle_id)}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted">Academic Year: </span>
                  <span className="font-semibold text-ink dark:text-stone-100">
                    {getYearName(dossierApp.academic_year_id)}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted">Target Class: </span>
                  <span className="font-semibold text-ink dark:text-stone-100">
                    {getClassName(dossierApp.target_class_id)}
                  </span>
                </div>
              </div>
            </div>

            {/* Decision Records */}
            <div>
              <h4 className="text-xs font-mono uppercase text-ink-muted mb-2 font-semibold">
                Admission Decisions
              </h4>
              {dossierDecisions.length === 0 ? (
                <p className="text-xs text-ink-muted italic">No decision recorded yet.</p>
              ) : (
                <div className="space-y-2">
                  {dossierDecisions.map((dec) => (
                    <div
                      key={dec.id}
                      className="p-3 border rounded-md border-divider dark:border-stone-800 bg-paper dark:bg-stone-900 text-xs space-y-1"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-bold">{getStatusBadge(dec.decision_type)}</span>
                        <span className="font-mono text-ink-muted">
                          {new Date(dec.decided_at).toLocaleString()}
                        </span>
                      </div>
                      {dec.comments && <p className="text-ink dark:text-stone-200">{dec.comments}</p>}
                      {dec.conditions && (
                        <p className="text-amber-600 dark:text-amber-400 font-mono">
                          Conditions: {dec.conditions}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Status History Timeline */}
            <div>
              <h4 className="text-xs font-mono uppercase text-ink-muted mb-2 font-semibold">
                Audit Timeline (Status History)
              </h4>
              {loadingDossier ? (
                <LoadingState message="Loading timeline..." />
              ) : dossierHistory.length === 0 ? (
                <p className="text-xs text-ink-muted italic">No history available.</p>
              ) : (
                <div className="space-y-3 relative pl-4 border-l-2 border-divider dark:border-stone-800">
                  {dossierHistory.map((hist) => (
                    <div key={hist.id} className="relative text-xs">
                      <div className="absolute -left-[21px] top-0.5 w-2.5 h-2.5 rounded-full bg-brand-500 ring-4 ring-paper dark:ring-stone-900" />
                      <div className="flex items-center gap-2 font-medium">
                        <span>{hist.old_status ? `${hist.old_status} → ` : 'Created in '}</span>
                        <strong className="text-ink dark:text-stone-100">{hist.new_status}</strong>
                        <span className="text-ink-muted font-mono text-[10px] ml-auto">
                          {new Date(hist.changed_at).toLocaleString()}
                        </span>
                      </div>
                      {hist.reason && (
                        <p className="text-ink-muted mt-0.5">Reason: {hist.reason}</p>
                      )}
                      {hist.remarks && (
                        <p className="text-ink-muted italic mt-0.5">Remarks: {hist.remarks}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t border-divider dark:border-stone-800">
              <Button variant="ghost" onClick={() => setDossierApp(null)}>
                Close Dossier
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Confirm Delete Cycle Dialog */}
      <ConfirmDialog
        isOpen={!!deleteCycleTarget}
        title="Deactivate Admission Cycle"
        message={`Are you sure you want to deactivate cycle '${deleteCycleTarget?.name}'?`}
        confirmText="Deactivate"
        onConfirm={handleDeleteCycle}
        onClose={() => setDeleteCycleTarget(null)}
      />

      {/* Confirm Delete Applicant Dialog */}
      <ConfirmDialog
        isOpen={!!deleteApplicantTarget}
        title="Delete Applicant"
        message={`Are you sure you want to delete applicant '${deleteApplicantTarget?.first_name} ${deleteApplicantTarget?.last_name}'?`}
        confirmText="Delete"
        onConfirm={handleDeleteApplicant}
        onClose={() => setDeleteApplicantTarget(null)}
      />
    </div>
  );
};
