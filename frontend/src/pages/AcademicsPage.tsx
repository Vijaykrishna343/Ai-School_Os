import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  academicYearsApi,
  academicTermsApi,
  schoolClassesApi,
  sectionsApi,
  subjectsApi,
} from '@/services/api';
import {
  AcademicYear,
  AcademicTerm,
  SchoolClass,
  Section,
  Subject,
  SubjectCreate,
  SubjectUpdate,
} from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';
import { Pagination } from '@/components/ui/Pagination';
import { ErrorState } from '@/components/ui/ErrorState';

type TabType = 'years' | 'terms' | 'classes' | 'sections' | 'subjects';

export const AcademicsPage: React.FC = () => {
  const { user, permissions } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>('years');

  // Modals & Confirmation States
  const [isYearModalOpen, setIsYearModalOpen] = useState(false);
  const [selectedYear, setSelectedYear] = useState<AcademicYear | null>(null);

  const [isTermModalOpen, setIsTermModalOpen] = useState(false);
  const [selectedTerm, setSelectedTerm] = useState<AcademicTerm | null>(null);

  const [isClassModalOpen, setIsClassModalOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState<SchoolClass | null>(null);

  const [isSectionModalOpen, setIsSectionModalOpen] = useState(false);
  const [selectedSection, setSelectedSection] = useState<Section | null>(null);

  const [isSubjectModalOpen, setIsSubjectModalOpen] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<{
    type: TabType;
    id: string;
    name: string;
  } | null>(null);

  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Form states
  const [yearForm, setYearForm] = useState({ name: '', start_date: '', end_date: '', status: 'UPCOMING' });
  const [termForm, setTermForm] = useState({ academic_year_id: '', name: '', code: '', start_date: '', end_date: '', is_active: true });
  const [classForm, setClassForm] = useState({ name: '', display_order: 1 });
  const [sectionForm, setSectionForm] = useState({ school_class_id: '', name: '', capacity: 40, room_number: '' });
  const [subjectForm, setSubjectForm] = useState<Partial<SubjectCreate>>({
    subject_code: '',
    subject_name: '',
    description: '',
    is_optional: false,
    status: 'ACTIVE',
  });

  const [formError, setFormError] = useState<string | null>(null);

  // Filters & Pagination states per tab
  const [selectedClassFilter, setSelectedClassFilter] = useState<string>('');
  const [selectedYearFilter, setSelectedYearFilter] = useState<string>('');

  const [subjectSearch, setSubjectSearch] = useState('');
  const [subjectStatusFilter, setSubjectStatusFilter] = useState('');
  const [subjectOptionalFilter, setSubjectOptionalFilter] = useState('');

  const [yearsPage, setYearsPage] = useState(1);
  const [termsPage, setTermsPage] = useState(1);
  const [classesPage, setClassesPage] = useState(1);
  const [sectionsPage, setSectionsPage] = useState(1);
  const [subjectsPage, setSubjectsPage] = useState(1);
  const pageSize = 10;

  // ---------------------------------------------------------
  // TanStack Queries
  // ---------------------------------------------------------
  const {
    data: yearsData,
    isLoading: isYearsLoading,
    isError: isYearsError,
    error: yearsError,
    refetch: refetchYears,
  } = useQuery({
    queryKey: ['academicYears', yearsPage],
    queryFn: () => academicYearsApi.getAcademicYears({ page: yearsPage, page_size: pageSize }),
    enabled: permissions.includes('academic_year.view'),
  });

  const {
    data: termsData,
    isLoading: isTermsLoading,
    isError: isTermsError,
    error: termsError,
    refetch: refetchTerms,
  } = useQuery({
    queryKey: ['academicTerms', selectedYearFilter, termsPage],
    queryFn: () => academicTermsApi.getAcademicTerms({
      academic_year_id: selectedYearFilter || undefined,
      page: termsPage,
      page_size: pageSize,
    }),
    enabled: permissions.includes('academic_term.view'),
  });

  const {
    data: classesData,
    isLoading: isClassesLoading,
    isError: isClassesError,
    error: classesError,
    refetch: refetchClasses,
  } = useQuery({
    queryKey: ['schoolClasses', classesPage],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: classesPage, page_size: pageSize }),
    enabled: permissions.includes('class.view'),
  });

  const fallbackClassId = classesData?.items?.[0]?.id || '';
  const activeClassId = selectedClassFilter || fallbackClassId;

  const {
    data: sectionsData,
    isLoading: isSectionsLoading,
    isError: isSectionsError,
    error: sectionsError,
    refetch: refetchSections,
  } = useQuery({
    queryKey: ['sections', activeClassId, sectionsPage],
    queryFn: () => {
      if (!activeClassId) {
        return Promise.resolve({ items: [], total: 0, page: 1, page_size: pageSize, total_pages: 0 });
      }
      return sectionsApi.getSectionsByClass(activeClassId, { page: sectionsPage, page_size: pageSize });
    },
    enabled: permissions.includes('section.view') && activeTab === 'sections' && !!activeClassId,
  });

  const {
    data: subjectsData,
    isLoading: isSubjectsLoading,
    isError: isSubjectsError,
    error: subjectsError,
    refetch: refetchSubjects,
  } = useQuery({
    queryKey: ['subjects', subjectSearch, subjectStatusFilter, subjectOptionalFilter, subjectsPage],
    queryFn: () => subjectsApi.getSubjects({
      subject_name: subjectSearch || undefined,
      status: subjectStatusFilter || undefined,
      is_optional: subjectOptionalFilter === 'true' ? true : subjectOptionalFilter === 'false' ? false : undefined,
      page: subjectsPage,
      page_size: pageSize,
    }),
    enabled: permissions.includes('subject.view') && activeTab === 'subjects',
  });

  // ---------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------
  const createYearMutation = useMutation({
    mutationFn: (data: any) => academicYearsApi.createAcademicYear({ ...data, school_id: user?.school_id || '' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicYears'] });
      setIsYearModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create academic year.'),
  });

  const updateYearMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => academicYearsApi.updateAcademicYear(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicYears'] });
      setIsYearModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update academic year.'),
  });

  const createTermMutation = useMutation({
    mutationFn: (data: any) => academicTermsApi.createAcademicTerm({ ...data, display_order: 1 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicTerms'] });
      setIsTermModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create academic term.'),
  });

  const updateTermMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => academicTermsApi.updateAcademicTerm(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicTerms'] });
      setIsTermModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update academic term.'),
  });

  const createClassMutation = useMutation({
    mutationFn: (data: any) => schoolClassesApi.createSchoolClass({ ...data, school_id: user?.school_id || '' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schoolClasses'] });
      setIsClassModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create school class.'),
  });

  const updateClassMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => schoolClassesApi.updateSchoolClass(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schoolClasses'] });
      setIsClassModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update school class.'),
  });

  const createSectionMutation = useMutation({
    mutationFn: (data: any) => sectionsApi.createSection(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections'] });
      setIsSectionModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create section.'),
  });

  const updateSectionMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => sectionsApi.updateSection(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections'] });
      setIsSectionModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update section.'),
  });

  const createSubjectMutation = useMutation({
    mutationFn: (data: SubjectCreate) => subjectsApi.createSubject({ ...data, school_id: user?.school_id || '' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setIsSubjectModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create subject.'),
  });

  const updateSubjectMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubjectUpdate }) => subjectsApi.updateSubject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setIsSubjectModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update subject.'),
  });

  const deleteMutation = useMutation({
    mutationFn: async (target: { type: TabType; id: string }) => {
      if (target.type === 'years') await academicYearsApi.deleteAcademicYear(target.id);
      if (target.type === 'terms') await academicTermsApi.deleteAcademicTerm(target.id);
      if (target.type === 'classes') await schoolClassesApi.deleteSchoolClass(target.id);
      if (target.type === 'sections') await sectionsApi.deleteSection(target.id);
      if (target.type === 'subjects') await subjectsApi.deleteSubject(target.id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicYears'] });
      queryClient.invalidateQueries({ queryKey: ['academicTerms'] });
      queryClient.invalidateQueries({ queryKey: ['schoolClasses'] });
      queryClient.invalidateQueries({ queryKey: ['sections'] });
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setDeleteTarget(null);
      setDeleteError(null);
    },
    onError: (err: any) => {
      setDeleteError(err.message || 'Deletion failed.');
      setDeleteTarget(null);
    },
  });

  // Modal handlers
  const handleOpenYearModal = (year?: AcademicYear) => {
    setFormError(null);
    if (year) {
      setSelectedYear(year);
      setYearForm({ name: year.name, start_date: year.start_date, end_date: year.end_date, status: year.status });
    } else {
      setSelectedYear(null);
      setYearForm({ name: '', start_date: '', end_date: '', status: 'UPCOMING' });
    }
    setIsYearModalOpen(true);
  };

  const handleOpenTermModal = (term?: AcademicTerm) => {
    setFormError(null);
    if (term) {
      setSelectedTerm(term);
      setTermForm({
        academic_year_id: term.academic_year_id,
        name: term.name,
        code: term.code,
        start_date: term.start_date,
        end_date: term.end_date,
        is_active: term.is_active,
      });
    } else {
      setSelectedTerm(null);
      setTermForm({
        academic_year_id: yearsData?.items?.[0]?.id || '',
        name: '',
        code: '',
        start_date: '',
        end_date: '',
        is_active: true,
      });
    }
    setIsTermModalOpen(true);
  };

  const handleOpenClassModal = (cls?: SchoolClass) => {
    setFormError(null);
    if (cls) {
      setSelectedClass(cls);
      setClassForm({ name: cls.name, display_order: cls.display_order });
    } else {
      setSelectedClass(null);
      setClassForm({ name: '', display_order: (classesData?.items?.length || 0) + 1 });
    }
    setIsClassModalOpen(true);
  };

  const handleOpenSectionModal = (sec?: Section) => {
    setFormError(null);
    if (sec) {
      setSelectedSection(sec);
      setSectionForm({
        school_class_id: sec.school_class_id,
        name: sec.name,
        capacity: sec.capacity,
        room_number: sec.room_number || '',
      });
    } else {
      setSelectedSection(null);
      setSectionForm({
        school_class_id: selectedClassFilter || classesData?.items?.[0]?.id || '',
        name: '',
        capacity: 40,
        room_number: '',
      });
    }
    setIsSectionModalOpen(true);
  };

  const handleOpenSubjectModal = (sub?: Subject) => {
    setFormError(null);
    if (sub) {
      setSelectedSubject(sub);
      setSubjectForm({
        subject_code: sub.subject_code,
        subject_name: sub.subject_name,
        description: sub.description || '',
        is_optional: sub.is_optional,
        status: sub.status,
      });
    } else {
      setSelectedSubject(null);
      setSubjectForm({
        subject_code: '',
        subject_name: '',
        description: '',
        is_optional: false,
        status: 'ACTIVE',
      });
    }
    setIsSubjectModalOpen(true);
  };

  // Table Columns
  const yearColumns: Column<AcademicYear>[] = [
    { key: 'name', header: 'Name', render: (row) => <span className="font-semibold">{row.name}</span> },
    { key: 'start_date', header: 'Start Date' },
    { key: 'end_date', header: 'End Date' },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.status === 'ACTIVE' ? 'success' : row.status === 'UPCOMING' ? 'warning' : 'default'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('academic_year.update') && (
            <Button variant="outline" size="sm" onClick={() => handleOpenYearModal(row)}>Edit</Button>
          )}
          {permissions.includes('academic_year.delete') && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'years', id: row.id, name: row.name })}>Delete</Button>
          )}
        </div>
      ),
    },
  ];

  const termColumns: Column<AcademicTerm>[] = [
    { key: 'name', header: 'Term Name', render: (row) => <span className="font-semibold">{row.name}</span> },
    { key: 'code', header: 'Code' },
    { key: 'start_date', header: 'Start Date' },
    { key: 'end_date', header: 'End Date' },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.is_active ? 'success' : 'default'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('academic_term.update') && (
            <Button variant="outline" size="sm" onClick={() => handleOpenTermModal(row)}>Edit</Button>
          )}
          {permissions.includes('academic_term.delete') && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'terms', id: row.id, name: row.name })}>Delete</Button>
          )}
        </div>
      ),
    },
  ];

  const classColumns: Column<SchoolClass>[] = [
    { key: 'display_order', header: 'Order', render: (row) => <span className="text-slate-500">{row.display_order}</span> },
    { key: 'name', header: 'Class Name', render: (row) => <span className="font-semibold text-slate-900 dark:text-white">{row.name}</span> },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.status === 'ACTIVE' ? 'success' : 'default'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('class.update') && (
            <Button variant="outline" size="sm" onClick={() => handleOpenClassModal(row)}>Edit</Button>
          )}
          {permissions.includes('class.delete') && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'classes', id: row.id, name: row.name })}>Delete</Button>
          )}
        </div>
      ),
    },
  ];

  const sectionColumns: Column<Section>[] = [
    { key: 'name', header: 'Section', render: (row) => <span className="font-semibold text-slate-900 dark:text-white">Section {row.name}</span> },
    { key: 'capacity', header: 'Capacity', render: (row) => <span>{row.capacity} students</span> },
    { key: 'room_number', header: 'Room', render: (row) => <span>{row.room_number || 'N/A'}</span> },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.status === 'ACTIVE' ? 'success' : 'default'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('section.update') && (
            <Button variant="outline" size="sm" onClick={() => handleOpenSectionModal(row)}>Edit</Button>
          )}
          {permissions.includes('section.delete') && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'sections', id: row.id, name: `Section ${row.name}` })}>Delete</Button>
          )}
        </div>
      ),
    },
  ];

  const subjectColumns: Column<Subject>[] = [
    { key: 'subject_code', header: 'Subject Code', render: (row) => <span className="font-mono text-xs font-bold text-brand-500">{row.subject_code}</span> },
    { key: 'subject_name', header: 'Subject Name', render: (row) => <span className="font-semibold">{row.subject_name}</span> },
    { key: 'description', header: 'Description', render: (row) => <span className="text-xs text-ink-muted">{row.description || '—'}</span> },
    {
      key: 'is_optional',
      header: 'Type',
      render: (row) => (
        <Badge variant={row.is_optional ? 'default' : 'info' as any}>
          {row.is_optional ? 'Optional' : 'Core'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.status === 'ACTIVE' ? 'success' : 'default'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('subject.update') && (
            <Button variant="outline" size="sm" onClick={() => handleOpenSubjectModal(row)}>Edit</Button>
          )}
          {permissions.includes('subject.delete') && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'subjects', id: row.id, name: row.subject_name })}>Delete</Button>
          )}
        </div>
      ),
    },
  ];

  let isTabError = false;
  let tabErrorMsg = '';
  let onRetryHandler = () => {};

  if (activeTab === 'years' && isYearsError) {
    isTabError = true;
    tabErrorMsg = (yearsError as any)?.message || 'Failed to retrieve academic years.';
    onRetryHandler = () => refetchYears();
  } else if (activeTab === 'terms' && isTermsError) {
    isTabError = true;
    tabErrorMsg = (termsError as any)?.message || 'Failed to retrieve academic terms.';
    onRetryHandler = () => refetchTerms();
  } else if (activeTab === 'classes' && isClassesError) {
    isTabError = true;
    tabErrorMsg = (classesError as any)?.message || 'Failed to retrieve school classes.';
    onRetryHandler = () => refetchClasses();
  } else if (activeTab === 'sections' && isSectionsError) {
    isTabError = true;
    tabErrorMsg = (sectionsError as any)?.message || 'Failed to retrieve sections.';
    onRetryHandler = () => refetchSections();
  } else if (activeTab === 'subjects' && isSubjectsError) {
    isTabError = true;
    tabErrorMsg = (subjectsError as any)?.message || 'Failed to retrieve subjects.';
    onRetryHandler = () => refetchSubjects();
  }

  if (isTabError) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorState
          title="Administrative Academics Error"
          message={tabErrorMsg}
          onRetry={onRetryHandler}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 select-none">
      {/* Page Header */}
      <div className="border-b border-divider dark:border-stone-850 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-stone-400">
            INSTITUTIONAL STRUCTURE
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-stone-100 mt-1">
            Academic Architecture
          </h1>
          <p className="text-xs text-slate-500 dark:text-stone-400 mt-1">
            Configure academic years, operational terms, school classes, and sections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'years' && permissions.includes('academic_year.create') && (
            <Button onClick={() => handleOpenYearModal()}>+ Add Academic Year</Button>
          )}
          {activeTab === 'terms' && permissions.includes('academic_term.create') && (
            <Button onClick={() => handleOpenTermModal()}>+ Add Academic Term</Button>
          )}
          {activeTab === 'classes' && permissions.includes('class.create') && (
            <Button onClick={() => handleOpenClassModal()}>+ Add School Class</Button>
          )}
          {activeTab === 'sections' && permissions.includes('section.create') && (
            <Button onClick={() => handleOpenSectionModal()}>+ Add Section</Button>
          )}
          {activeTab === 'subjects' && permissions.includes('subject.create') && (
            <Button onClick={() => handleOpenSubjectModal()}>+ Add Subject</Button>
          )}
        </div>
      </div>

      {deleteError && (
        <Alert type="error" title="Deletion Failure" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      {/* Architectural Flow Map Banner */}
      <div className="border border-divider dark:border-stone-800 bg-paper p-4 rounded-none">
        <p className="text-[9px] font-mono uppercase tracking-wider text-slate-400 mb-3">
          STRUCTURAL_HIERARCHY_MAP
        </p>
        <div className="grid grid-cols-5 gap-2 text-center text-[10px] sm:text-xs font-mono">
          <div className={`p-2 border transition-all ${activeTab === 'years' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-divider bg-paper-dim text-slate-500'}`}>
            ACADEMIC_YEAR
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'terms' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-divider bg-paper-dim text-slate-500'}`}>
            ➔ ACADEMIC_TERMS
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'classes' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-divider bg-paper-dim text-slate-500'}`}>
            ➔ SCHOOL_CLASSES
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'sections' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-divider bg-paper-dim text-slate-500'}`}>
            ➔ CLASS_SECTIONS
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'subjects' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-divider bg-paper-dim text-slate-500'}`}>
            ➔ SUBJECTS
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-divider dark:border-stone-800">
        <nav className="flex space-x-6">
          {[
            { id: 'years', label: 'Academic Years', count: yearsData?.total, visible: permissions.includes('academic_year.view') },
            { id: 'terms', label: 'Academic Terms', count: termsData?.total, visible: permissions.includes('academic_term.view') },
            { id: 'classes', label: 'School Classes', count: classesData?.total, visible: permissions.includes('class.view') },
            { id: 'sections', label: 'Sections', count: sectionsData?.total, visible: permissions.includes('section.view') },
            { id: 'subjects', label: 'Subjects', count: subjectsData?.total, visible: permissions.includes('subject.view') },
          ].filter(t => t.visible).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`py-2.5 px-1 text-xs font-mono uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-brand-500 text-brand-500 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-355'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="px-1.5 py-0.5 text-[9px] rounded-none border border-divider bg-paper-dim text-slate-500 dark:text-stone-400">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Contents */}
      {activeTab === 'years' && permissions.includes('academic_year.view') && (
        <div className="space-y-4">
          <Card className="p-4">
            <Table
              columns={yearColumns}
              data={yearsData?.items || []}
              isLoading={isYearsLoading}
              emptyText="No academic years defined yet."
            />
          </Card>
          {yearsData && yearsData.total_pages > 1 && (
            <Pagination
              page={yearsData.page}
              totalPages={yearsData.total_pages}
              totalItems={yearsData.total}
              pageSize={yearsData.page_size}
              onPageChange={(p) => setYearsPage(p)}
            />
          )}
        </div>
      )}

      {activeTab === 'terms' && permissions.includes('academic_term.view') && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 bg-paper dark:bg-stone-900 p-4 rounded-none border border-divider">
            <label className="text-xs font-mono uppercase text-slate-500">FILTER_BY_YEAR:</label>
            <select
              value={selectedYearFilter}
              onChange={(e) => {
                setSelectedYearFilter(e.target.value);
                setTermsPage(1);
              }}
              className="px-3 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-750 dark:bg-stone-950 font-mono"
            >
              <option value="">ALL_ACADEMIC_YEARS</option>
              {yearsData?.items?.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </div>
          <Card className="p-4">
            <Table
              columns={termColumns}
              data={termsData?.items || []}
              isLoading={isTermsLoading}
              emptyText="No academic terms found."
            />
          </Card>
          {termsData && termsData.total_pages > 1 && (
            <Pagination
              page={termsData.page}
              totalPages={termsData.total_pages}
              totalItems={termsData.total}
              pageSize={termsData.page_size}
              onPageChange={(p) => setTermsPage(p)}
            />
          )}
        </div>
      )}

      {activeTab === 'classes' && permissions.includes('class.view') && (
        <div className="space-y-4">
          <Card className="p-4">
            <Table
              columns={classColumns}
              data={classesData?.items || []}
              isLoading={isClassesLoading}
              emptyText="No school classes created yet."
            />
          </Card>
          {classesData && classesData.total_pages > 1 && (
            <Pagination
              page={classesData.page}
              totalPages={classesData.total_pages}
              totalItems={classesData.total}
              pageSize={classesData.page_size}
              onPageChange={(p) => setClassesPage(p)}
            />
          )}
        </div>
      )}

      {activeTab === 'sections' && permissions.includes('section.view') && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 bg-paper dark:bg-stone-900 p-4 rounded-none border border-divider">
            <label className="text-xs font-mono uppercase text-slate-500">SELECT_CLASS:</label>
            <select
              value={activeClassId}
              onChange={(e) => {
                setSelectedClassFilter(e.target.value);
                setSectionsPage(1);
              }}
              className="px-3 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-750 dark:bg-stone-950 font-mono"
            >
              <option value="">Select Class</option>
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <Card className="p-4">
            <Table
              columns={sectionColumns}
              data={sectionsData?.items || []}
              isLoading={isSectionsLoading}
              emptyText="No sections defined for this class."
            />
          </Card>
          {sectionsData && sectionsData.total_pages > 1 && (
            <Pagination
              page={sectionsData.page}
              totalPages={sectionsData.total_pages}
              totalItems={sectionsData.total}
              pageSize={sectionsData.page_size}
              onPageChange={(p) => setSectionsPage(p)}
            />
          )}
        </div>
      )}

      {activeTab === 'subjects' && permissions.includes('subject.view') && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row items-center gap-4 bg-paper dark:bg-stone-900 p-4 rounded-none border border-divider">
            <div className="flex-1 w-full">
              <Input
                placeholder="Search by subject code or name..."
                value={subjectSearch}
                onChange={(e) => {
                  setSubjectSearch(e.target.value);
                  setSubjectsPage(1);
                }}
              />
            </div>
            <div className="flex items-center gap-3 w-full md:w-auto shrink-0 font-mono text-xs">
              <select
                value={subjectStatusFilter}
                onChange={(e) => {
                  setSubjectStatusFilter(e.target.value);
                  setSubjectsPage(1);
                }}
                className="px-3 py-1.5 rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300"
              >
                <option value="">ALL_STATUS</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
              </select>

              <select
                value={subjectOptionalFilter}
                onChange={(e) => {
                  setSubjectOptionalFilter(e.target.value);
                  setSubjectsPage(1);
                }}
                className="px-3 py-1.5 rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300"
              >
                <option value="">ALL_TYPES</option>
                <option value="false">CORE</option>
                <option value="true">OPTIONAL</option>
              </select>
            </div>
          </div>
          <Card className="p-4">
            <Table
              columns={subjectColumns}
              data={subjectsData?.items || []}
              isLoading={isSubjectsLoading}
              emptyText="No subjects found matching filters."
            />
          </Card>
          {subjectsData && subjectsData.total_pages > 1 && (
            <Pagination
              page={subjectsData.page}
              totalPages={subjectsData.total_pages}
              totalItems={subjectsData.total}
              pageSize={subjectsData.page_size}
              onPageChange={(p) => setSubjectsPage(p)}
            />
          )}
        </div>
      )}

      {((activeTab === 'years' && !permissions.includes('academic_year.view')) ||
        (activeTab === 'terms' && !permissions.includes('academic_term.view')) ||
        (activeTab === 'classes' && !permissions.includes('class.view')) ||
        (activeTab === 'sections' && !permissions.includes('section.view')) ||
        (activeTab === 'subjects' && !permissions.includes('subject.view'))) && (
        <Card className="p-6 text-center">
          <p className="text-sm text-ink-muted">You do not have permission to view this academic docket.</p>
        </Card>
      )}

      {/* Modals */}

      {/* Academic Year Modal */}
      <Modal
        isOpen={isYearModalOpen}
        onClose={() => setIsYearModalOpen(false)}
        title={selectedYear ? 'Edit Academic Year' : 'Create Academic Year'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsYearModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedYear) {
                  updateYearMutation.mutate({ id: selectedYear.id, data: yearForm });
                } else {
                  createYearMutation.mutate(yearForm);
                }
              }}
              isLoading={createYearMutation.isPending || updateYearMutation.isPending}
            >
              Save Academic Year
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError && <Alert type="error" title="Validation Error">{formError}</Alert>}
          <Input
            label="Academic Year Name *"
            placeholder="e.g. 2026-2027"
            value={yearForm.name}
            onChange={(e) => setYearForm({ ...yearForm, name: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="date"
              label="Start Date *"
              value={yearForm.start_date}
              onChange={(e) => setYearForm({ ...yearForm, start_date: e.target.value })}
              required
            />
            <Input
              type="date"
              label="End Date *"
              value={yearForm.end_date}
              onChange={(e) => setYearForm({ ...yearForm, end_date: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-mono uppercase text-slate-700 dark:text-stone-300 mb-1">Status</label>
            <select
              value={yearForm.status}
              onChange={(e) => setYearForm({ ...yearForm, status: e.target.value as any })}
              className="w-full px-3 py-2 text-sm rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900"
            >
              <option value="UPCOMING">UPCOMING</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>
        </div>
      </Modal>

      {/* Academic Term Modal */}
      <Modal
        isOpen={isTermModalOpen}
        onClose={() => setIsTermModalOpen(false)}
        title={selectedTerm ? 'Edit Academic Term' : 'Create Academic Term'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsTermModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedTerm) {
                  updateTermMutation.mutate({ id: selectedTerm.id, data: termForm });
                } else {
                  createTermMutation.mutate(termForm);
                }
              }}
              isLoading={createTermMutation.isPending || updateTermMutation.isPending}
            >
              Save Academic Term
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError && <Alert type="error" title="Validation Error">{formError}</Alert>}
          <div>
            <label className="block text-xs font-mono uppercase text-slate-700 dark:text-stone-300 mb-1">Academic Year</label>
            <select
              value={termForm.academic_year_id}
              onChange={(e) => setTermForm({ ...termForm, academic_year_id: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900"
              disabled={!!selectedTerm}
            >
              {yearsData?.items?.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </div>
          <Input
            label="Term Name *"
            placeholder="e.g. Term 1 / Semester 1"
            value={termForm.name}
            onChange={(e) => setTermForm({ ...termForm, name: e.target.value })}
            required
          />
          <Input
            label="Term Code *"
            placeholder="e.g. TERM1"
            value={termForm.code}
            onChange={(e) => setTermForm({ ...termForm, code: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="date"
              label="Start Date *"
              value={termForm.start_date}
              onChange={(e) => setTermForm({ ...termForm, start_date: e.target.value })}
              required
            />
            <Input
              type="date"
              label="End Date *"
              value={termForm.end_date}
              onChange={(e) => setTermForm({ ...termForm, end_date: e.target.value })}
              required
            />
          </div>
        </div>
      </Modal>

      {/* School Class Modal */}
      <Modal
        isOpen={isClassModalOpen}
        onClose={() => setIsClassModalOpen(false)}
        title={selectedClass ? 'Edit School Class' : 'Create School Class'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsClassModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedClass) {
                  updateClassMutation.mutate({ id: selectedClass.id, data: classForm });
                } else {
                  createClassMutation.mutate(classForm);
                }
              }}
              isLoading={createClassMutation.isPending || updateClassMutation.isPending}
            >
              Save School Class
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError && <Alert type="error" title="Validation Error">{formError}</Alert>}
          <Input
            label="Class Name *"
            placeholder="e.g. Class 10"
            value={classForm.name}
            onChange={(e) => setClassForm({ ...classForm, name: e.target.value })}
            required
          />
          <Input
            type="number"
            label="Display Order *"
            value={classForm.display_order}
            onChange={(e) => setClassForm({ ...classForm, display_order: parseInt(e.target.value, 10) || 1 })}
            required
          />
        </div>
      </Modal>

      {/* Section Modal */}
      <Modal
        isOpen={isSectionModalOpen}
        onClose={() => setIsSectionModalOpen(false)}
        title={selectedSection ? 'Edit Section' : 'Create Section'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsSectionModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedSection) {
                  updateSectionMutation.mutate({ id: selectedSection.id, data: sectionForm });
                } else {
                  createSectionMutation.mutate(sectionForm);
                }
              }}
              isLoading={createSectionMutation.isPending || updateSectionMutation.isPending}
            >
              Save Section
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError && <Alert type="error" title="Validation Error">{formError}</Alert>}
          <div>
            <label className="block text-xs font-mono uppercase text-slate-700 dark:text-stone-300 mb-1">School Class</label>
            <select
              value={sectionForm.school_class_id}
              onChange={(e) => setSectionForm({ ...sectionForm, school_class_id: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900"
              disabled={!!selectedSection}
            >
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <Input
            label="Section Name *"
            placeholder="e.g. A"
            value={sectionForm.name}
            onChange={(e) => setSectionForm({ ...sectionForm, name: e.target.value })}
            required
          />
          <Input
            type="number"
            label="Capacity *"
            value={sectionForm.capacity}
            onChange={(e) => setSectionForm({ ...sectionForm, capacity: parseInt(e.target.value, 10) || 40 })}
            required
          />
          <Input
            label="Room Number (Optional)"
            placeholder="e.g. 201-B"
            value={sectionForm.room_number}
            onChange={(e) => setSectionForm({ ...sectionForm, room_number: e.target.value })}
          />
        </div>
      </Modal>

      {/* Subject Modal */}
      <Modal
        isOpen={isSubjectModalOpen}
        onClose={() => setIsSubjectModalOpen(false)}
        title={selectedSubject ? 'Edit Subject' : 'Create Subject'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsSubjectModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedSubject) {
                  updateSubjectMutation.mutate({ id: selectedSubject.id, data: subjectForm });
                } else {
                  createSubjectMutation.mutate(subjectForm as SubjectCreate);
                }
              }}
              isLoading={createSubjectMutation.isPending || updateSubjectMutation.isPending}
            >
              Save Subject
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError && <Alert type="error" title="Validation Error">{formError}</Alert>}
          <Input
            label="Subject Code *"
            placeholder="e.g. MAT101"
            value={subjectForm.subject_code || ''}
            onChange={(e) => setSubjectForm({ ...subjectForm, subject_code: e.target.value })}
            required
          />
          <Input
            label="Subject Name *"
            placeholder="e.g. Mathematics"
            value={subjectForm.subject_name || ''}
            onChange={(e) => setSubjectForm({ ...subjectForm, subject_name: e.target.value })}
            required
          />
          <Input
            label="Description"
            placeholder="Subject description..."
            value={subjectForm.description || ''}
            onChange={(e) => setSubjectForm({ ...subjectForm, description: e.target.value })}
          />
          <div className="flex items-center gap-2 py-2">
            <input
              type="checkbox"
              id="is_optional"
              checked={subjectForm.is_optional || false}
              onChange={(e) => setSubjectForm({ ...subjectForm, is_optional: e.target.checked })}
              className="rounded-none border-divider text-brand-500 bg-paper-dim focus:ring-brand-500 w-4 h-4"
            />
            <label htmlFor="is_optional" className="text-xs font-mono uppercase text-slate-700 dark:text-stone-300">
              Optional Subject
            </label>
          </div>
          <div>
            <label className="block text-xs font-mono uppercase text-slate-700 dark:text-stone-300 mb-1">Status</label>
            <select
              value={subjectForm.status}
              onChange={(e) => setSubjectForm({ ...subjectForm, status: e.target.value as any })}
              className="w-full px-3 py-2 text-sm rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>
        </div>
      </Modal>

      {/* Soft Delete Confirm Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
        title={`Soft Delete ${deleteTarget?.name}`}
        message={`Are you sure you want to soft delete "${deleteTarget?.name}"? This record will be marked as deleted in the database.`}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
