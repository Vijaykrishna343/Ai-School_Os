import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  studentsApi,
  schoolClassesApi,
  sectionsApi,
  studentCertificatesApi,
  StudentCertificateItem,
} from '@/services/api';
import {
  Student,
  StudentCreate,
  StudentUpdate,
} from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Modal } from '@/components/ui/Modal';
import { Drawer } from '@/components/ui/Drawer';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';
import { Printer } from 'lucide-react';

export const StudentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'registry' | 'certificates'>('registry');

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

  // Certificate Modal states
  const [isIssueTcModalOpen, setIsIssueTcModalOpen] = useState(false);
  const [isIssueBonafideModalOpen, setIsIssueBonafideModalOpen] = useState(false);
  const [certificateTargetStudent, setCertificateTargetStudent] = useState<Student | null>(null);
  const [tcReason, setTcReason] = useState('Completed Academic Term');
  const [tcConduct, setTcConduct] = useState('Good');
  const [bonafidePurpose, setBonafidePurpose] = useState('Educational / Verification Purpose');
  const [bonafideConduct, setBonafideConduct] = useState('Good');
  const [certFormError, setCertFormError] = useState<string | null>(null);

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

  // Data Queries
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

  const { data: sectionsData } = useQuery({
    queryKey: ['sections', selectedClassFilter],
    queryFn: () => sectionsApi.getSectionsByClass(selectedClassFilter),
    enabled: !!selectedClassFilter,
  });

  const { data: certificatesData, isLoading: isCertificatesLoading } = useQuery({
    queryKey: ['studentCertificates', page],
    queryFn: () => studentCertificatesApi.list(undefined, undefined, page),
    enabled: activeTab === 'certificates',
  });

  // Mutations
  const createStudentMutation = useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.createStudent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setIsStudentModalOpen(false);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to register student.');
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

  const issueTcMutation = useMutation({
    mutationFn: ({ studentId, reason, conduct }: { studentId: string; reason: string; conduct: string }) =>
      studentCertificatesApi.issueTC(studentId, { reason_for_leaving: reason, conduct, update_student_status: true }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['studentCertificates'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setIsIssueTcModalOpen(false);
      window.open(studentCertificatesApi.getPrintViewUrl(data.id), '_blank');
    },
    onError: (err: any) => setCertFormError(err.message || 'Failed to issue Transfer Certificate.'),
  });

  const issueBonafideMutation = useMutation({
    mutationFn: ({ studentId, purpose, conduct }: { studentId: string; purpose: string; conduct: string }) =>
      studentCertificatesApi.issueBonafide(studentId, { purpose, conduct }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['studentCertificates'] });
      setIsIssueBonafideModalOpen(false);
      window.open(studentCertificatesApi.getPrintViewUrl(data.id), '_blank');
    },
    onError: (err: any) => setCertFormError(err.message || 'Failed to issue Bonafide Certificate.'),
  });

  const handleOpenCreateModal = () => {
    setFormError(null);
    setValidationErrors(null);
    setEditingStudent(null);
    setStudentForm({
      school_id: user?.school_id || '',
      admission_number: `ADM-${Math.floor(100000 + Math.random() * 900000)}`,
      roll_number: '1',
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: 'MALE',
      date_of_birth: '2010-01-01',
      admission_date: new Date().toISOString().split('T')[0],
      phone: '',
      email: '',
      school_class_id: classesData?.items[0]?.id || '',
      section_id: '',
      parent_id: '',
      academic_year_id: '',
      address_line1: '',
      city: '',
      district: '',
      state: '',
      postal_code: '110001',
    });
    setIsStudentModalOpen(true);
  };

  const handleOpenIssueTc = (student: Student) => {
    setCertFormError(null);
    setCertificateTargetStudent(student);
    setTcReason('Parent Transfer / Course Completed');
    setTcConduct('Good');
    setIsIssueTcModalOpen(true);
  };

  const handleOpenIssueBonafide = (student: Student) => {
    setCertFormError(null);
    setCertificateTargetStudent(student);
    setBonafidePurpose('Educational / Passport Verification Purpose');
    setBonafideConduct('Good');
    setIsIssueBonafideModalOpen(true);
  };

  const studentColumns: Column<Student>[] = [
    {
      key: 'admission_number',
      header: 'Adm No',
      render: (row) => <span className="font-mono text-xs font-bold text-brand-500">{row.admission_number}</span>,
    },
    {
      key: 'name',
      header: 'Student Name',
      render: (row) => (
        <div>
          <div className="font-medium text-xs text-ink dark:text-stone-200">
            {row.first_name} {row.last_name}
          </div>
          <div className="text-[10px] text-ink-muted font-mono">{row.email || 'No email registered'}</div>
        </div>
      ),
    },
    {
      key: 'class',
      header: 'Class / Sec',
      render: (row) => (
        <span className="text-xs font-mono">
          {row.school_class?.name || 'Class'} ({row.section?.name || 'Sec'})
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.status === 'ACTIVE' ? 'success' : row.status === 'TRANSFERRED' ? 'warning' : 'default'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions & Certificates',
      className: 'text-right min-w-[16rem]',
      render: (row) => (
        <div className="flex justify-end gap-1">
          <Button variant="outline" size="sm" onClick={() => setViewingStudent(row)}>
            View
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleOpenIssueBonafide(row)}>
            + Bonafide
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleOpenIssueTc(row)}>
            + TC
          </Button>
        </div>
      ),
    },
  ];

  const certificateColumns: Column<StudentCertificateItem>[] = [
    {
      key: 'certificate_number',
      header: 'Cert No',
      render: (row) => <span className="font-mono text-xs font-bold text-brand-500">{row.certificate_number}</span>,
    },
    {
      key: 'student_name',
      header: 'Student',
      render: (row) => (
        <div>
          <div className="font-medium text-xs">{row.student_name}</div>
          <div className="text-[10px] text-ink-muted font-mono">Adm: {row.admission_number || 'N/A'}</div>
        </div>
      ),
    },
    {
      key: 'certificate_type',
      header: 'Type',
      render: (row) => <Badge variant={row.certificate_type === 'TC' ? 'warning' : 'info'}>{row.certificate_type}</Badge>,
    },
    {
      key: 'issued_date',
      header: 'Issued Date',
      render: (row) => <span className="font-mono text-xs">{row.issued_date}</span>,
    },
    {
      key: 'actions',
      header: 'Print Action',
      className: 'text-right',
      render: (row) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open(studentCertificatesApi.getPrintViewUrl(row.id), '_blank')}
        >
          <Printer className="w-3 h-3 mr-1 text-brand-500" />
          Print A4 PDF
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh]">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-divider pb-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted">
            STUDENT_ACADEMIC_OPERATIONS // REGISTRY_AND_CERTIFICATES
          </p>
          <h1 className="text-2xl font-serif font-bold text-brand-500 mt-1">
            Student Dossier & Certificates Workstation
          </h1>
        </div>

        {activeTab === 'registry' && (
          <Button variant="primary" size="sm" onClick={handleOpenCreateModal}>
            + Register New Student
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-divider gap-4">
        <button
          onClick={() => setActiveTab('registry')}
          className={`pb-2.5 text-xs font-mono font-bold border-b-2 uppercase transition-colors ${
            activeTab === 'registry' ? 'border-brand-500 text-brand-500' : 'border-transparent text-ink-muted'
          }`}
        >
          Student Registry
        </button>
        <button
          onClick={() => setActiveTab('certificates')}
          className={`pb-2.5 text-xs font-mono font-bold border-b-2 uppercase transition-colors ${
            activeTab === 'certificates' ? 'border-brand-500 text-brand-500' : 'border-transparent text-ink-muted'
          }`}
        >
          Issued Certificates Registry
        </button>
      </div>

      {/* TAB 1: REGISTRY */}
      {activeTab === 'registry' && (
        <Card className="p-4 space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between">
            <div className="w-full md:w-72">
              <Input
                placeholder="Search student by name or Adm No..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="flex gap-2">
              <select
                className="text-xs border border-divider rounded p-2 bg-paper"
                value={selectedClassFilter}
                onChange={(e) => {
                  setSelectedClassFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Classes</option>
                {classesData?.items.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Table
            columns={studentColumns}
            data={studentsData?.items || []}
            rowKey={(row) => row.id}
            isLoading={isStudentsLoading}
            emptyText="No students found in registry."
          />

          {studentsData && studentsData.total_pages > 1 && (
            <Pagination
              page={page}
              totalPages={studentsData.total_pages}
              onPageChange={(p) => setPage(p)}
            />
          )}
        </Card>
      )}

      {/* TAB 2: CERTIFICATES HISTORY */}
      {activeTab === 'certificates' && (
        <Card className="p-4 space-y-4">
          <div className="border-b border-divider pb-3">
            <h2 className="text-sm font-bold font-mono text-brand-500 uppercase">OFFICIAL_CERTIFICATE_ISSUANCE_HISTORY</h2>
            <p className="text-xs text-ink-muted font-sans">Tenant history log of Transfer Certificates (TC) and Bonafide Certificates issued.</p>
          </div>

          <Table
            columns={certificateColumns}
            data={certificatesData?.items || []}
            rowKey={(row) => row.id}
            isLoading={isCertificatesLoading}
            emptyText="No certificates issued yet."
          />

          {certificatesData && certificatesData.total_pages > 1 && (
            <Pagination
              page={page}
              totalPages={certificatesData.total_pages}
              onPageChange={(p) => setPage(p)}
            />
          )}
        </Card>
      )}

      {/* Modal: Issue Transfer Certificate (TC) */}
      <Modal
        isOpen={isIssueTcModalOpen}
        onClose={() => setIsIssueTcModalOpen(false)}
        title={`Issue Transfer Certificate (TC)`}
      >
        <div className="space-y-4 py-2">
          {certFormError && <Alert type="error" title="Issuance Error">{certFormError}</Alert>}

          {certificateTargetStudent && (
            <div className="p-3 bg-amber-50/50 border border-amber-200 rounded text-xs space-y-1">
              <p className="font-bold text-amber-900">Student: {certificateTargetStudent.first_name} {certificateTargetStudent.last_name}</p>
              <p className="text-amber-800 font-mono">Admission No: {certificateTargetStudent.admission_number} | Class: {certificateTargetStudent.school_class?.name || 'Class'}</p>
            </div>
          )}

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Reason for Leaving *</label>
            <Input
              value={tcReason}
              onChange={(e) => setTcReason(e.target.value)}
              placeholder="e.g. Parent Transfer / Course Completed"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Conduct & Behavior *</label>
            <Input
              value={tcConduct}
              onChange={(e) => setTcConduct(e.target.value)}
              placeholder="e.g. Good / Exemplary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setIsIssueTcModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() =>
                certificateTargetStudent &&
                issueTcMutation.mutate({
                  studentId: certificateTargetStudent.id,
                  reason: tcReason,
                  conduct: tcConduct,
                })
              }
              isLoading={issueTcMutation.isPending}
            >
              Generate TC & Print A4 PDF
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Issue Bonafide Certificate */}
      <Modal
        isOpen={isIssueBonafideModalOpen}
        onClose={() => setIsIssueBonafideModalOpen(false)}
        title={`Issue Bonafide Certificate`}
      >
        <div className="space-y-4 py-2">
          {certFormError && <Alert type="error" title="Issuance Error">{certFormError}</Alert>}

          {certificateTargetStudent && (
            <div className="p-3 bg-blue-50/50 border border-blue-200 rounded text-xs space-y-1">
              <p className="font-bold text-blue-900">Student: {certificateTargetStudent.first_name} {certificateTargetStudent.last_name}</p>
              <p className="text-blue-800 font-mono">Admission No: {certificateTargetStudent.admission_number} | Class: {certificateTargetStudent.school_class?.name || 'Class'}</p>
            </div>
          )}

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Certificate Purpose *</label>
            <Input
              value={bonafidePurpose}
              onChange={(e) => setBonafidePurpose(e.target.value)}
              placeholder="e.g. Passport Application / Bank Account / Scholarship"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Conduct & Behavior *</label>
            <Input
              value={bonafideConduct}
              onChange={(e) => setBonafideConduct(e.target.value)}
              placeholder="e.g. Good / Exemplary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setIsIssueBonafideModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() =>
                certificateTargetStudent &&
                issueBonafideMutation.mutate({
                  studentId: certificateTargetStudent.id,
                  purpose: bonafidePurpose,
                  conduct: bonafideConduct,
                })
              }
              isLoading={issueBonafideMutation.isPending}
            >
              Generate Bonafide & Print A4 PDF
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Create Student */}
      <Modal
        isOpen={isStudentModalOpen}
        onClose={() => setIsStudentModalOpen(false)}
        title="Register New Student"
      >
        <div className="space-y-4 py-2">
          {formError && <Alert type="error" title="Validation Failed">{formError}</Alert>}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">First Name *</label>
              <Input
                value={studentForm.first_name}
                onChange={(e) => setStudentForm({ ...studentForm, first_name: e.target.value })}
                error={validationErrors?.first_name}
              />
            </div>
            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">Last Name *</label>
              <Input
                value={studentForm.last_name}
                onChange={(e) => setStudentForm({ ...studentForm, last_name: e.target.value })}
                error={validationErrors?.last_name}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">Admission No *</label>
              <Input
                value={studentForm.admission_number}
                onChange={(e) => setStudentForm({ ...studentForm, admission_number: e.target.value })}
                error={validationErrors?.admission_number}
              />
            </div>
            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">Roll Number *</label>
              <Input
                value={studentForm.roll_number}
                onChange={(e) => setStudentForm({ ...studentForm, roll_number: e.target.value })}
                error={validationErrors?.roll_number}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setIsStudentModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => createStudentMutation.mutate(studentForm as StudentCreate)}
              isLoading={createStudentMutation.isPending}
            >
              Register Student
            </Button>
          </div>
        </div>
      </Modal>

      {/* Drawer: Student View */}
      <Drawer
        isOpen={!!viewingStudent}
        onClose={() => setViewingStudent(null)}
        title="Student Profile Dossier"
      >
        {viewingStudent && (
          <div className="space-y-4 text-xs">
            <div className="border-b border-divider pb-3">
              <h2 className="text-lg font-bold text-brand-500 font-serif">
                {viewingStudent.first_name} {viewingStudent.last_name}
              </h2>
              <p className="font-mono text-ink-muted">Admission No: {viewingStudent.admission_number}</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><span className="font-mono text-ink-muted">GENDER:</span> {viewingStudent.gender}</div>
              <div><span className="font-mono text-ink-muted">STATUS:</span> {viewingStudent.status}</div>
              <div><span className="font-mono text-ink-muted">DOB:</span> {viewingStudent.date_of_birth}</div>
              <div><span className="font-mono text-ink-muted">ADMISSION DATE:</span> {viewingStudent.admission_date}</div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteStudentMutation.mutate(deleteTarget.id)}
        title="Soft Delete Student"
        message={`Are you sure you want to soft delete student "${deleteTarget?.admission_number}"?`}
        isLoading={deleteStudentMutation.isPending}
      />
    </div>
  );
};
