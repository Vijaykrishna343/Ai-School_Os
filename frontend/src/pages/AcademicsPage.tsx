import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  academicYearsApi,
  academicTermsApi,
  schoolClassesApi,
  sectionsApi,
} from '@/services/api';
import {
  AcademicYear,
  AcademicTerm,
  SchoolClass,
  Section,
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

type TabType = 'years' | 'terms' | 'classes' | 'sections';

export const AcademicsPage: React.FC = () => {
  const { user } = useAuthStore();
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

  const [deleteTarget, setDeleteTarget] = useState<{
    type: TabType;
    id: string;
    name: string;
  } | null>(null);

  // Form states
  const [yearForm, setYearForm] = useState({ name: '', start_date: '', end_date: '', status: 'UPCOMING' });
  const [termForm, setTermForm] = useState({ academic_year_id: '', name: '', code: '', start_date: '', end_date: '', is_active: true });
  const [classForm, setClassForm] = useState({ name: '', display_order: 1 });
  const [sectionForm, setSectionForm] = useState({ school_class_id: '', name: '', capacity: 40, room_number: '' });

  const [formError, setFormError] = useState<string | null>(null);

  // Filters
  const [selectedClassFilter, setSelectedClassFilter] = useState<string>('');
  const [selectedYearFilter, setSelectedYearFilter] = useState<string>('');

  // ---------------------------------------------------------
  // TanStack Queries
  // ---------------------------------------------------------
  const { data: yearsData, isLoading: isYearsLoading } = useQuery({
    queryKey: ['academicYears'],
    queryFn: () => academicYearsApi.getAcademicYears({ page_size: 100 }),
  });

  const { data: termsData, isLoading: isTermsLoading } = useQuery({
    queryKey: ['academicTerms', selectedYearFilter],
    queryFn: () => academicTermsApi.getAcademicTerms({ academic_year_id: selectedYearFilter || undefined, page_size: 100 }),
  });

  const { data: classesData, isLoading: isClassesLoading } = useQuery({
    queryKey: ['schoolClasses'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page_size: 100 }),
  });

  const { data: sectionsData, isLoading: isSectionsLoading } = useQuery({
    queryKey: ['sections', selectedClassFilter],
    queryFn: () => {
      if (!selectedClassFilter && classesData?.items?.length) {
        return sectionsApi.getSectionsByClass(classesData.items[0].id, { page_size: 100 });
      }
      if (selectedClassFilter) {
        return sectionsApi.getSectionsByClass(selectedClassFilter, { page_size: 100 });
      }
      return Promise.resolve({ items: [], total: 0, page: 1, page_size: 100, total_pages: 0 });
    },
    enabled: activeTab === 'sections',
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
    mutationFn: (data: any) => academicTermsApi.createAcademicTerm(data),
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

  const deleteMutation = useMutation({
    mutationFn: async (target: { type: TabType; id: string }) => {
      if (target.type === 'years') await academicYearsApi.deleteAcademicYear(target.id);
      if (target.type === 'terms') await academicTermsApi.deleteAcademicTerm(target.id);
      if (target.type === 'classes') await schoolClassesApi.deleteSchoolClass(target.id);
      if (target.type === 'sections') await sectionsApi.deleteSection(target.id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academicYears'] });
      queryClient.invalidateQueries({ queryKey: ['academicTerms'] });
      queryClient.invalidateQueries({ queryKey: ['schoolClasses'] });
      queryClient.invalidateQueries({ queryKey: ['sections'] });
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
        academic_year_id: yearsData?.items[0]?.id || '',
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
        school_class_id: selectedClassFilter || classesData?.items[0]?.id || '',
        name: '',
        capacity: 40,
        room_number: '',
      });
    }
    setIsSectionModalOpen(true);
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
          <Button variant="outline" size="sm" onClick={() => handleOpenYearModal(row)}>Edit</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'years', id: row.id, name: row.name })}>Delete</Button>
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
          <Button variant="outline" size="sm" onClick={() => handleOpenTermModal(row)}>Edit</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'terms', id: row.id, name: row.name })}>Delete</Button>
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
          <Button variant="outline" size="sm" onClick={() => handleOpenClassModal(row)}>Edit</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'classes', id: row.id, name: row.name })}>Delete</Button>
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
          <Button variant="outline" size="sm" onClick={() => handleOpenSectionModal(row)}>Edit</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget({ type: 'sections', id: row.id, name: `Section ${row.name}` })}>Delete</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8]">
      {/* Page Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            INSTITUTIONAL STRUCTURE
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Academic Architecture
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure academic years, operational terms, school classes, and sections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'years' && (
            <Button onClick={() => handleOpenYearModal()}>+ Add Academic Year</Button>
          )}
          {activeTab === 'terms' && (
            <Button onClick={() => handleOpenTermModal()}>+ Add Academic Term</Button>
          )}
          {activeTab === 'classes' && (
            <Button onClick={() => handleOpenClassModal()}>+ Add School Class</Button>
          )}
          {activeTab === 'sections' && (
            <Button onClick={() => handleOpenSectionModal()}>+ Add Section</Button>
          )}
        </div>
      </div>

      {/* Architectural Flow Map Banner */}
      <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
        <p className="text-[9px] font-mono uppercase tracking-wider text-slate-400 mb-3">
          STRUCTURAL_HIERARCHY_MAP
        </p>
        <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono">
          <div className={`p-2 border transition-all ${activeTab === 'years' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-slate-100 bg-slate-50 text-slate-500'}`}>
            ACADEMIC_YEAR
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'terms' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-slate-100 bg-slate-50 text-slate-500'}`}>
            ➔ ACADEMIC_TERMS
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'classes' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-slate-100 bg-slate-50 text-slate-500'}`}>
            ➔ SCHOOL_CLASSES
          </div>
          <div className={`p-2 border transition-all ${activeTab === 'sections' ? 'border-brand-500 bg-brand-50/10 text-brand-500 font-bold' : 'border-slate-100 bg-slate-50 text-slate-500'}`}>
            ➔ CLASS_SECTIONS
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <nav className="flex space-x-6">
          {[
            { id: 'years', label: 'Academic Years', count: yearsData?.total },
            { id: 'terms', label: 'Academic Terms', count: termsData?.total },
            { id: 'classes', label: 'School Classes', count: classesData?.total },
            { id: 'sections', label: 'Sections' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`py-2.5 px-1 text-xs font-mono uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-brand-500 text-brand-500 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="px-1.5 py-0.5 text-[9px] rounded-none border border-slate-200 bg-slate-50 text-slate-500">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Contents */}
      {activeTab === 'years' && (
        <Card className="p-4">
          <Table
            columns={yearColumns}
            data={yearsData?.items || []}
            isLoading={isYearsLoading}
            emptyText="No academic years defined yet."
          />
        </Card>
      )}

      {activeTab === 'terms' && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 bg-white dark:bg-slate-900 p-4 rounded-none border border-slate-200 dark:border-slate-800">
            <label className="text-xs font-mono uppercase text-slate-500">FILTER_BY_YEAR:</label>
            <select
              value={selectedYearFilter}
              onChange={(e) => setSelectedYearFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-sm border border-slate-350 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono"
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
        </div>
      )}

      {activeTab === 'classes' && (
        <Card className="p-4">
          <Table
            columns={classColumns}
            data={classesData?.items || []}
            isLoading={isClassesLoading}
            emptyText="No school classes created yet."
          />
        </Card>
      )}

      {activeTab === 'sections' && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 bg-white dark:bg-slate-900 p-4 rounded-none border border-slate-200 dark:border-slate-800">
            <label className="text-xs font-mono uppercase text-slate-500">SELECT_CLASS:</label>
            <select
              value={selectedClassFilter || classesData?.items[0]?.id || ''}
              onChange={(e) => setSelectedClassFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-sm border border-slate-350 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono"
            >
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
        </div>
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
            label="Academic Year Name"
            placeholder="e.g. 2026-2027"
            value={yearForm.name}
            onChange={(e) => setYearForm({ ...yearForm, name: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="date"
              label="Start Date"
              value={yearForm.start_date}
              onChange={(e) => setYearForm({ ...yearForm, start_date: e.target.value })}
              required
            />
            <Input
              type="date"
              label="End Date"
              value={yearForm.end_date}
              onChange={(e) => setYearForm({ ...yearForm, end_date: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Status</label>
            <select
              value={yearForm.status}
              onChange={(e) => setYearForm({ ...yearForm, status: e.target.value as any })}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
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
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Academic Year</label>
            <select
              value={termForm.academic_year_id}
              onChange={(e) => setTermForm({ ...termForm, academic_year_id: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
              disabled={!!selectedTerm}
            >
              {yearsData?.items?.map((y) => (
                <option key={y.id} value={y.id}>{y.name}</option>
              ))}
            </select>
          </div>
          <Input
            label="Term Name"
            placeholder="e.g. Term 1 / Semester 1"
            value={termForm.name}
            onChange={(e) => setTermForm({ ...termForm, name: e.target.value })}
            required
          />
          <Input
            label="Term Code"
            placeholder="e.g. TERM1"
            value={termForm.code}
            onChange={(e) => setTermForm({ ...termForm, code: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="date"
              label="Start Date"
              value={termForm.start_date}
              onChange={(e) => setTermForm({ ...termForm, start_date: e.target.value })}
              required
            />
            <Input
              type="date"
              label="End Date"
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
            label="Class Name"
            placeholder="e.g. Class 10"
            value={classForm.name}
            onChange={(e) => setClassForm({ ...classForm, name: e.target.value })}
            required
          />
          <Input
            type="number"
            label="Display Order"
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
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">School Class</label>
            <select
              value={sectionForm.school_class_id}
              onChange={(e) => setSectionForm({ ...sectionForm, school_class_id: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
              disabled={!!selectedSection}
            >
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <Input
            label="Section Name"
            placeholder="e.g. A"
            value={sectionForm.name}
            onChange={(e) => setSectionForm({ ...sectionForm, name: e.target.value })}
            required
          />
          <Input
            type="number"
            label="Capacity"
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
