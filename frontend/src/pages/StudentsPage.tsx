import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  studentsApi,
  schoolClassesApi,
  sectionsApi,
  parentsApi,
  academicYearsApi,
} from '@/services/api';
import {
  Student,
  StudentCreate,
  StudentUpdate,
} from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Modal } from '@/components/ui/Modal';
import { Drawer } from '@/components/ui/Drawer';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';
import { Building2 } from 'lucide-react';

export const StudentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Query & Filter states
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [selectedClassFilter, setSelectedClassFilter] = useState('');
  const [selectedSectionFilter, setSelectedSectionFilter] = useState('');

  // Modals & Detail Drawer
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [viewingStudent, setViewingStudent] = useState<Student | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Student | null>(null);

  // Form State
  const [studentForm, setStudentForm] = useState<Partial<StudentCreate>>({
    admission_number: '',
    roll_number: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: 'MALE',
    date_of_birth: '',
    admission_date: '',
    phone: '',
    email: '',
    school_class_id: '',
    section_id: '',
    parent_id: '',
    academic_year_id: '',
    address_line1: '',
    city: '',
    district: '',
    state: '',
    postal_code: '110001',
  });

  const [formError, setFormError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string> | null>(null);

  // ---------------------------------------------------------
  // Data Queries
  // ---------------------------------------------------------
  const { data: studentsData, isLoading: isStudentsLoading } = useQuery({
    queryKey: ['students', page, pageSize, search, selectedClassFilter, selectedSectionFilter],
    queryFn: () =>
      studentsApi.getStudents({
        page,
        page_size: pageSize,
        search: search || undefined,
        school_class_id: selectedClassFilter || undefined,
        section_id: selectedSectionFilter || undefined,
      }),
  });

  const { data: classesData } = useQuery({
    queryKey: ['schoolClasses'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page_size: 100 }),
  });

  const emptySection = { items: [] as import('@/types/models').Section[], total: 0, page: 1, page_size: 100, total_pages: 0 };

  const { data: filterSectionsData } = useQuery({
    queryKey: ['sections', selectedClassFilter],
    queryFn: () =>
      selectedClassFilter
        ? sectionsApi.getSectionsByClass(selectedClassFilter, { page_size: 100 })
        : Promise.resolve(emptySection),
    enabled: !!selectedClassFilter,
  });

  const { data: formSectionsData } = useQuery({
    queryKey: ['sections', studentForm.school_class_id],
    queryFn: () =>
      studentForm.school_class_id
        ? sectionsApi.getSectionsByClass(studentForm.school_class_id, { page_size: 100 })
        : Promise.resolve(emptySection),
    enabled: !!studentForm.school_class_id,
  });

  const { data: parentsData } = useQuery({
    queryKey: ['parents'],
    queryFn: () => parentsApi.getParents({ page_size: 100 }),
  });

  const { data: yearsData } = useQuery({
    queryKey: ['academicYears'],
    queryFn: () => academicYearsApi.getAcademicYears({ page_size: 100 }),
  });

  const { data: enrollmentHistoryData, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['studentEnrollmentHistory', viewingStudent?.id],
    queryFn: () => (viewingStudent ? studentsApi.getStudentEnrollmentHistory(viewingStudent.id) : Promise.resolve([])),
    enabled: !!viewingStudent,
  });

  // ---------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------
  const createStudentMutation = useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.createStudent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setIsStudentModalOpen(false);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create student record.');
      if (err.errors) setValidationErrors(err.errors);
    },
  });

  const updateStudentMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: StudentUpdate }) => studentsApi.updateStudent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setIsStudentModalOpen(false);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to update student record.');
      if (err.errors) setValidationErrors(err.errors);
    },
  });

  const deleteStudentMutation = useMutation({
    mutationFn: (id: string) => studentsApi.deleteStudent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setDeleteTarget(null);
    },
  });

  // Handlers
  const handleOpenCreateModal = () => {
    setFormError(null);
    setValidationErrors(null);
    setEditingStudent(null);
    setStudentForm({
      school_id: user?.school_id || '',
      academic_year_id: yearsData?.items[0]?.id || '',
      school_class_id: classesData?.items[0]?.id || '',
      section_id: '',
      parent_id: parentsData?.items[0]?.id || '',
      admission_number: `ADM-${Math.floor(1000 + Math.random() * 9000)}`,
      roll_number: '1',
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: 'MALE',
      date_of_birth: '2012-01-01',
      admission_date: new Date().toISOString().split('T')[0],
      phone: '',
      email: '',
      address_line1: '123 Main St',
      city: 'Delhi',
      district: 'Central',
      state: 'Delhi',
      postal_code: '110001',
    });
    setIsStudentModalOpen(true);
  };

  const handleOpenEditModal = (student: Student) => {
    setFormError(null);
    setValidationErrors(null);
    setEditingStudent(student);
    setStudentForm({
      first_name: student.first_name,
      middle_name: student.middle_name || '',
      last_name: student.last_name || '',
      gender: student.gender,
      phone: student.phone || '',
      email: student.email || '',
      school_class_id: student.school_class_id,
      section_id: student.section_id,
      address_line1: student.address_line1,
      city: student.city,
      district: student.district,
      state: student.state,
      postal_code: student.postal_code,
    });
    setIsStudentModalOpen(true);
  };

  const handleSubmitStudent = () => {
    setFormError(null);
    setValidationErrors(null);

    if (editingStudent) {
      updateStudentMutation.mutate({
        id: editingStudent.id,
        data: {
          first_name: studentForm.first_name,
          middle_name: studentForm.middle_name,
          last_name: studentForm.last_name,
          gender: studentForm.gender,
          phone: studentForm.phone,
          email: studentForm.email,
          school_class_id: studentForm.school_class_id,
          section_id: studentForm.section_id,
          address_line1: studentForm.address_line1,
          city: studentForm.city,
          district: studentForm.district,
          state: studentForm.state,
          postal_code: studentForm.postal_code,
        },
      });
    } else {
      createStudentMutation.mutate(studentForm as StudentCreate);
    }
  };

  // Columns
  const studentColumns: Column<Student>[] = [
    {
      key: 'admission_number',
      header: 'Adm No',
      render: (row) => <span className="font-mono text-xs font-bold text-brand-500 dark:text-brand-350">{row.admission_number}</span>,
    },
    {
      key: 'name',
      header: 'Student Name',
      render: (row) => (
        <div>
          <p className="font-semibold text-ink dark:text-stone-100">
            {row.first_name} {row.last_name}
          </p>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/60 dark:text-stone-500">{row.gender}</p>
        </div>
      ),
    },
    {
      key: 'class',
      header: 'Class & Section',
      render: (row) => (
        <span className="font-medium text-ink dark:text-stone-200">
          {row.school_class?.name || 'Class'} - Section {row.section?.name || 'A'}
        </span>
      ),
    },
    {
      key: 'roll_number',
      header: 'Roll No',
      render: (row) => <span className="text-ink-muted dark:text-stone-400 font-mono">#{row.roll_number}</span>,
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
      key: 'parent',
      header: 'Parent/Guardian',
      render: (row) => (
        <span className="text-xs text-ink-muted dark:text-stone-300">
          {row.parent ? row.parent.father_name || row.parent.mother_name || row.parent.guardian_name : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-1.5">
          <Button variant="outline" size="sm" className="px-2 py-0.5 text-[10px] font-mono tracking-wide" onClick={() => setViewingStudent(row)}>
            View
          </Button>
          <Button variant="outline" size="sm" className="px-2 py-0.5 text-[10px] font-mono tracking-wide" onClick={() => handleOpenEditModal(row)}>
            Edit
          </Button>
          <Button variant="danger" size="sm" className="px-2 py-0.5 text-[10px] font-mono tracking-wide" onClick={() => setDeleteTarget(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 select-none">
      {/* Editorial Header */}
      <div className="border-b border-divider dark:border-stone-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
            OFFICE OF THE REGISTRAR // RECORDS INDEX
          </p>
          <h1 className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100 mt-1 tracking-tight">
            Student Registry
          </h1>
          <p className="text-xs text-ink-muted dark:text-stone-400 mt-1">
            Institutional database of student records, academic placements, and history ledgers.
          </p>
        </div>
        <Button onClick={handleOpenCreateModal} size="sm">
          + Enroll New Student
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 border border-divider dark:border-stone-850 bg-paper flex flex-col md:flex-row items-center gap-4">
        <div className="flex-1 w-full">
          <Input
            placeholder="Search registry by name or admission number..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto shrink-0">
          <select
            value={selectedClassFilter}
            onChange={(e) => {
              setSelectedClassFilter(e.target.value);
              setSelectedSectionFilter('');
              setPage(1);
            }}
            className="px-3 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 font-mono"
          >
            <option value="">ALL_CLASSES</option>
            {classesData?.items?.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <select
            value={selectedSectionFilter}
            onChange={(e) => {
              setSelectedSectionFilter(e.target.value);
              setPage(1);
            }}
            disabled={!selectedClassFilter}
            className="px-3 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 disabled:opacity-40 font-mono"
          >
            <option value="">ALL_SECTIONS</option>
            {filterSectionsData?.items?.map((s: import('@/types/models').Section) => (
              <option key={s.id} value={s.id}>Section {s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table & Pagination Grid */}
      <div className="space-y-4">
        <Table
          columns={studentColumns}
          data={studentsData?.items || []}
          isLoading={isStudentsLoading}
          emptyText="No students matching criteria in current school scope."
        />
        {studentsData && (
          <Pagination
            page={studentsData.page}
            totalPages={studentsData.total_pages}
            totalItems={studentsData.total}
            pageSize={studentsData.page_size}
            onPageChange={(p) => setPage(p)}
          />
        )}
      </div>

      {/* Student Form Modal (Create & Edit) */}
      <Modal
        isOpen={isStudentModalOpen}
        onClose={() => setIsStudentModalOpen(false)}
        title={editingStudent ? `Edit Student Record — ${editingStudent.admission_number}` : 'Enroll New Student'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsStudentModalOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitStudent}
              isLoading={createStudentMutation.isPending || updateStudentMutation.isPending}
            >
              {editingStudent ? 'Update Dossier' : 'Submit Admission'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {formError && <Alert type="error" title="Form Error">{formError}</Alert>}

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name"
              value={studentForm.first_name || ''}
              onChange={(e) => setStudentForm({ ...studentForm, first_name: e.target.value })}
              error={validationErrors?.first_name}
              required
            />
            <Input
              label="Last Name"
              value={studentForm.last_name || ''}
              onChange={(e) => setStudentForm({ ...studentForm, last_name: e.target.value })}
              error={validationErrors?.last_name}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400 mb-1">
                Gender *
              </label>
              <select
                value={studentForm.gender || 'MALE'}
                onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value as any })}
                className="w-full px-2.5 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-250"
              >
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            {!editingStudent && (
              <Input
                label="Admission Number"
                value={studentForm.admission_number || ''}
                onChange={(e) => setStudentForm({ ...studentForm, admission_number: e.target.value })}
                error={validationErrors?.admission_number}
                required
              />
            )}
          </div>

          {!editingStudent && (
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="date"
                label="Date of Birth"
                value={studentForm.date_of_birth || ''}
                onChange={(e) => setStudentForm({ ...studentForm, date_of_birth: e.target.value })}
                required
              />
              <Input
                type="date"
                label="Admission Date"
                value={studentForm.admission_date || ''}
                onChange={(e) => setStudentForm({ ...studentForm, admission_date: e.target.value })}
                required
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400 mb-1">
                School Class *
              </label>
              <select
                value={studentForm.school_class_id || ''}
                onChange={(e) => setStudentForm({ ...studentForm, school_class_id: e.target.value, section_id: '' })}
                className="w-full px-2.5 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-250"
              >
                <option value="">Select Class</option>
                {classesData?.items?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400 mb-1">
                Section *
              </label>
              <select
                value={studentForm.section_id || ''}
                onChange={(e) => setStudentForm({ ...studentForm, section_id: e.target.value })}
                disabled={!studentForm.school_class_id}
                className="w-full px-2.5 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-250 disabled:opacity-40"
              >
                <option value="">Select Section</option>
                {formSectionsData?.items?.map((s: import('@/types/models').Section) => (
                  <option key={s.id} value={s.id}>Section {s.name}</option>
                ))}
              </select>
            </div>
          </div>

          {!editingStudent && (
            <div>
              <label className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400 mb-1">
                Link Parent/Guardian *
              </label>
              <select
                value={studentForm.parent_id || ''}
                onChange={(e) => setStudentForm({ ...studentForm, parent_id: e.target.value })}
                className="w-full px-2.5 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-250"
              >
                <option value="">Select Parent</option>
                {parentsData?.items?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.father_name || p.mother_name || p.guardian_name} ({p.primary_phone})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Phone (Optional)"
              value={studentForm.phone || ''}
              onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })}
            />
            <Input
              label="Email (Optional)"
              value={studentForm.email || ''}
              onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
            />
          </div>

          <Input
            label="Address Line 1 *"
            value={studentForm.address_line1 || ''}
            onChange={(e) => setStudentForm({ ...studentForm, address_line1: e.target.value })}
            required
          />

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="City *"
              value={studentForm.city || ''}
              onChange={(e) => setStudentForm({ ...studentForm, city: e.target.value })}
              required
            />
            <Input
              label="District *"
              value={studentForm.district || ''}
              onChange={(e) => setStudentForm({ ...studentForm, district: e.target.value })}
              required
            />
            <Input
              label="State *"
              value={studentForm.state || ''}
              onChange={(e) => setStudentForm({ ...studentForm, state: e.target.value })}
              required
            />
          </div>
        </div>
      </Modal>

      {/* Student Dossier (Detail Drawer) */}
      <Drawer
        isOpen={!!viewingStudent}
        onClose={() => setViewingStudent(null)}
        title="STUDENT DOSSIER"
        subtitle={viewingStudent ? `ADM_NO: ${viewingStudent.admission_number}` : ''}
        width="lg"
      >
        {viewingStudent && (
          <div className="space-y-6 text-ink dark:text-stone-300">
            {/* Academic Placement Dossier Card */}
            <div className="p-4 border border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-900/60 rounded-none flex items-center justify-between">
              <div>
                <p className="text-[9px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">ACADEMIC_PLACEMENT</p>
                <p className="text-sm font-serif font-bold text-brand-500 dark:text-stone-100 mt-1">
                  {viewingStudent.school_class?.name || 'Class'} // Section {viewingStudent.section?.name || 'A'}
                </p>
                <p className="text-[10px] font-mono text-ink-muted/80 mt-0.5">ROLL_NO: #{viewingStudent.roll_number}</p>
              </div>
              <Badge variant={viewingStudent.status === 'ACTIVE' ? 'success' : 'default'}>{viewingStudent.status}</Badge>
            </div>

            {/* Identity Dossier Section */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                IDENTITY_RECORD
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">FULL_NAME:</span> <span className="font-medium">{viewingStudent.first_name} {viewingStudent.last_name || ''}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">GENDER:</span> <span>{viewingStudent.gender}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">DATE_OF_BIRTH:</span> <span className="font-mono">{viewingStudent.date_of_birth}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">ADMISSION_DATE:</span> <span className="font-mono">{viewingStudent.admission_date}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">PHONE_CONTACT:</span> <span className="font-mono">{viewingStudent.phone || '—'}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">EMAIL_ADDRESS:</span> <span className="font-mono">{viewingStudent.email || '—'}</span></div>
                <div className="md:col-span-2"><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">RESIDENCE:</span> <span>{viewingStudent.address_line1}, {viewingStudent.city}, {viewingStudent.state}</span></div>
              </div>
            </div>

            {/* Guardian Dossier Section */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                GUARDIAN_LINKAGE
              </h3>
              {viewingStudent.parent ? (
                <div className="p-3 border border-divider/60 dark:border-stone-800 bg-paper-dim/40 rounded-none text-xs space-y-1">
                  <p><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">FATHER_NAME:</span> <span className="font-medium">{viewingStudent.parent.father_name}</span></p>
                  {viewingStudent.parent.mother_name && (
                    <p><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">MOTHER_NAME:</span> <span className="font-medium">{viewingStudent.parent.mother_name}</span></p>
                  )}
                  <p><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">PRIMARY_PHONE:</span> <span className="font-mono">{viewingStudent.parent.primary_phone}</span></p>
                  <p><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">RELATIONSHIP:</span> <span>{viewingStudent.parent.relationship}</span></p>
                </div>
              ) : (
                <p className="text-xs text-ink-muted/50 dark:text-stone-600 font-mono">NO_GUARDIAN_RECORD_LINKED</p>
              )}
            </div>

            {/* Enrollment History longitudinal ledger */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-3">
                LONGITUDINAL_ACADEMIC_LEDGER
              </h3>
              {isHistoryLoading ? (
                <p className="text-xs text-ink-muted/60 font-mono">Retrieving registry history...</p>
              ) : enrollmentHistoryData && enrollmentHistoryData.length > 0 ? (
                <div className="space-y-4 relative pl-3 border-l border-brand-500/35 dark:border-stone-850 font-mono text-xs">
                  {enrollmentHistoryData.map((item) => (
                    <div key={item.id} className="relative">
                      {/* Square timeline anchor */}
                      <div className="absolute -left-[16px] top-1 w-1.5 h-1.5 rounded-none bg-brand-500" />
                      <p className="font-semibold text-brand-500 dark:text-stone-250 text-xs">
                        {item.school_class?.name || 'Class'} (Section {item.section?.name || 'A'})
                      </p>
                      <p className="text-[10px] text-ink-muted mt-0.5">
                        STATUS: {item.enrollment_status} | ROLL_NUM: {item.roll_number}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-ink-muted/50 dark:text-stone-600 font-mono">NO_PREVIOUS_LEDGER_ENTRIES_FOUND</p>
              )}
            </div>
          </div>
        )}
      </Drawer>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteStudentMutation.mutate(deleteTarget.id)}
        title="Soft Delete Student dossier"
        message={`Are you sure you want to soft delete student registry dossier "${deleteTarget?.admission_number}"? This record will be archived.`}
        isLoading={deleteStudentMutation.isPending}
      />
    </div>
  );
};
