import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teachersApi } from '@/services/api';
import { Teacher, TeacherCreate, TeacherUpdate } from '@/types/models';
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

export const TeachersPage: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('');

  const [isTeacherModalOpen, setIsTeacherModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState<Teacher | null>(null);
  const [viewingTeacher, setViewingTeacher] = useState<Teacher | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Teacher | null>(null);

  const [teacherForm, setTeacherForm] = useState<Partial<TeacherCreate>>({
    employee_id: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: 'MALE',
    date_of_birth: '',
    joining_date: '',
    qualification: '',
    specialization: '',
    experience_years: 0,
    phone: '',
    email: '',
    address_line1: '',
    city: '',
    district: '',
    state: '',
    postal_code: '110001',
  });

  const [formError, setFormError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string> | null>(null);

  // Queries
  const { data: teachersData, isLoading: isTeachersLoading } = useQuery({
    queryKey: ['teachers', page, pageSize, search, selectedStatusFilter],
    queryFn: () =>
      teachersApi.getTeachers({
        page,
        page_size: pageSize,
        search: search || undefined,
        status: selectedStatusFilter || undefined,
      }),
  });

  // Mutations
  const createTeacherMutation = useMutation({
    mutationFn: (data: TeacherCreate) => teachersApi.createTeacher(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      setIsTeacherModalOpen(false);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create teacher record.');
      if (err.errors) setValidationErrors(err.errors);
    },
  });

  const updateTeacherMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TeacherUpdate }) => teachersApi.updateTeacher(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      setIsTeacherModalOpen(false);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to update teacher record.');
      if (err.errors) setValidationErrors(err.errors);
    },
  });

  const deleteTeacherMutation = useMutation({
    mutationFn: (id: string) => teachersApi.deleteTeacher(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] });
      setDeleteTarget(null);
    },
  });

  const handleOpenCreateModal = () => {
    setFormError(null);
    setValidationErrors(null);
    setEditingTeacher(null);
    setTeacherForm({
      school_id: user?.school_id || '',
      employee_id: `EMP-${Math.floor(1000 + Math.random() * 9000)}`,
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: 'MALE',
      date_of_birth: '1990-01-01',
      joining_date: new Date().toISOString().split('T')[0],
      qualification: '',
      specialization: '',
      experience_years: 0,
      phone: '',
      email: '',
      address_line1: '',
      city: '',
      district: '',
      state: '',
      postal_code: '110001',
    });
    setIsTeacherModalOpen(true);
  };

  const handleOpenEditModal = (teacher: Teacher) => {
    setFormError(null);
    setValidationErrors(null);
    setEditingTeacher(teacher);
    setTeacherForm({
      first_name: teacher.first_name,
      middle_name: teacher.middle_name || '',
      last_name: teacher.last_name || '',
      gender: teacher.gender,
      qualification: teacher.qualification,
      specialization: teacher.specialization || '',
      experience_years: teacher.experience_years || 0,
      phone: teacher.phone,
      email: teacher.email,
      address_line1: teacher.address_line1,
      city: teacher.city,
      district: teacher.district,
      state: teacher.state,
      postal_code: teacher.postal_code,
    });
    setIsTeacherModalOpen(true);
  };

  const handleSubmitTeacher = () => {
    setFormError(null);
    setValidationErrors(null);

    if (editingTeacher) {
      updateTeacherMutation.mutate({
        id: editingTeacher.id,
        data: {
          first_name: teacherForm.first_name,
          middle_name: teacherForm.middle_name,
          last_name: teacherForm.last_name,
          qualification: teacherForm.qualification,
          specialization: teacherForm.specialization,
          experience_years: teacherForm.experience_years,
          phone: teacherForm.phone,
          email: teacherForm.email,
          address_line1: teacherForm.address_line1,
          city: teacherForm.city,
          district: teacherForm.district,
          state: teacherForm.state,
          postal_code: teacherForm.postal_code,
        },
      });
    } else {
      createTeacherMutation.mutate(teacherForm as TeacherCreate);
    }
  };

  const statusVariant = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'ON_LEAVE': return 'warning';
      case 'INACTIVE':
      case 'RESIGNED': return 'error';
      default: return 'default';
    }
  };

  const teacherColumns: Column<Teacher>[] = [
    {
      key: 'employee_id',
      header: 'Employee ID',
      className: 'min-w-[7rem]',
      render: (row) => (
        <span className="font-mono text-xs font-bold text-brand-500 dark:text-brand-350">{row.employee_id}</span>
      ),
    },
    {
      key: 'name',
      header: 'Teacher Name',
      className: 'min-w-[9rem]',
      render: (row) => (
        <div>
          <p className="font-semibold text-ink dark:text-stone-100">
            {row.first_name} {row.last_name}
          </p>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted/60 dark:text-stone-500">
            {row.gender}
          </p>
        </div>
      ),
    },
    {
      key: 'qualification',
      header: 'Qualification',
      className: 'min-w-[8rem]',
      render: (row) => (
        <div>
          <p className="font-medium text-ink dark:text-stone-200">{row.qualification}</p>
          {row.specialization && (
            <p className="text-[10px] font-mono uppercase tracking-wider text-ink-muted/60 dark:text-stone-500">
              {row.specialization}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'phone',
      header: 'Phone',
      className: 'min-w-[6.5rem]',
      render: (row) => <span className="font-mono text-xs text-ink dark:text-stone-300">{row.phone}</span>,
    },
    {
      key: 'joining_date',
      header: 'Joining Date',
      className: 'min-w-[6.5rem]',
      render: (row) => <span className="font-mono text-ink-muted dark:text-stone-400">{row.joining_date}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge variant={statusVariant(row.status) as any}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      className: 'min-w-[11rem]',
      render: (row) => (
        <div className="flex items-center gap-1.5">
          <Button variant="outline" size="sm" className="px-2 py-0.5 text-[10px] font-mono tracking-wide" onClick={() => setViewingTeacher(row)}>
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
            OFFICE OF THE REGISTRAR
          </p>
          <h1 className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100 mt-1 tracking-tight">
            Faculty Directory
          </h1>
          <p className="text-xs text-ink-muted dark:text-stone-400 mt-1">
            Directory of institutional teachers, professional qualifications, and employment logs.
          </p>
        </div>
        <Button onClick={handleOpenCreateModal} size="sm">
          + Add Teacher
        </Button>
      </div>

      <div className="p-4 border border-divider dark:border-stone-850 bg-paper flex flex-col md:flex-row items-center gap-4">
        <div className="flex-1 w-full">
          <Input
            placeholder="Search by teacher name, employee ID, or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto shrink-0">
          <select
            value={selectedStatusFilter}
            onChange={(e) => {
              setSelectedStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300 font-mono"
          >
            <option value="">ALL_STATUS</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="ON_LEAVE">ON_LEAVE</option>
            <option value="RESIGNED">RESIGNED</option>
          </select>
        </div>
      </div>

      <div className="space-y-4">
        <Table
          columns={teacherColumns}
          data={teachersData?.items || []}
          isLoading={isTeachersLoading}
          emptyText="No faculty records matching current registry filters."
        />
        {teachersData && (
          <Pagination
            page={teachersData.page}
            totalPages={teachersData.total_pages}
            totalItems={teachersData.total}
            pageSize={teachersData.page_size}
            onPageChange={(p) => setPage(p)}
          />
        )}
      </div>

      {/* Teacher Create/Edit Modal */}
      <Modal
        isOpen={isTeacherModalOpen}
        onClose={() => setIsTeacherModalOpen(false)}
        title={editingTeacher ? `Edit Teacher — ${editingTeacher.employee_id}` : 'Add New Teacher'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsTeacherModalOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitTeacher}
              isLoading={createTeacherMutation.isPending || updateTeacherMutation.isPending}
            >
              {editingTeacher ? 'Update Record' : 'Create Teacher'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {formError && <Alert type="error" title="Form Error">{formError}</Alert>}

          {!editingTeacher && (
            <Input
              label="Employee ID *"
              value={teacherForm.employee_id || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, employee_id: e.target.value })}
              error={validationErrors?.employee_id}
              required
            />
          )}

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name *"
              value={teacherForm.first_name || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, first_name: e.target.value })}
              error={validationErrors?.first_name}
              required
            />
            <Input
              label="Last Name"
              value={teacherForm.last_name || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, last_name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-ink-muted dark:text-stone-400 mb-1">
                Gender *
              </label>
              <select
                value={teacherForm.gender || 'MALE'}
                onChange={(e) => setTeacherForm({ ...teacherForm, gender: e.target.value as any })}
                className="w-full px-2.5 py-1.5 text-xs rounded-none border border-divider bg-paper-dim text-ink focus:border-brand-500 focus:bg-paper focus:outline-none dark:border-stone-700 dark:bg-stone-900 dark:text-stone-250"
              >
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            {!editingTeacher && (
              <Input
                type="date"
                label="Date of Birth *"
                value={teacherForm.date_of_birth || ''}
                onChange={(e) => setTeacherForm({ ...teacherForm, date_of_birth: e.target.value })}
                required
              />
            )}
          </div>

          {!editingTeacher && (
            <Input
              type="date"
              label="Joining Date *"
              value={teacherForm.joining_date || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, joining_date: e.target.value })}
              required
            />
          )}

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Qualification *"
              placeholder="e.g. M.Ed, B.Sc"
              value={teacherForm.qualification || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, qualification: e.target.value })}
              error={validationErrors?.qualification}
              required
            />
            <Input
              label="Specialization (Optional)"
              placeholder="e.g. Mathematics"
              value={teacherForm.specialization || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, specialization: e.target.value })}
            />
          </div>

          <Input
            type="number"
            label="Experience Years"
            value={teacherForm.experience_years || 0}
            onChange={(e) => setTeacherForm({ ...teacherForm, experience_years: parseInt(e.target.value, 10) || 0 })}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Phone *"
              value={teacherForm.phone || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })}
              error={validationErrors?.phone}
              required
            />
            <Input
              label="Email *"
              value={teacherForm.email || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })}
              error={validationErrors?.email}
              required
            />
          </div>

          <Input
            label="Address Line 1 *"
            value={teacherForm.address_line1 || ''}
            onChange={(e) => setTeacherForm({ ...teacherForm, address_line1: e.target.value })}
            required
          />

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="City *"
              value={teacherForm.city || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, city: e.target.value })}
              required
            />
            <Input
              label="District *"
              value={teacherForm.district || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, district: e.target.value })}
              required
            />
            <Input
              label="State *"
              value={teacherForm.state || ''}
              onChange={(e) => setTeacherForm({ ...teacherForm, state: e.target.value })}
              required
            />
          </div>
        </div>
      </Modal>

      {/* Teacher Detail Drawer */}
      <Drawer
        isOpen={!!viewingTeacher}
        onClose={() => setViewingTeacher(null)}
        title="FACULTY DOSSIER"
        subtitle={viewingTeacher ? `EMPLOYEE_ID: ${viewingTeacher.employee_id}` : ''}
        width="md"
      >
        {viewingTeacher && (
          <div className="space-y-6 text-ink dark:text-stone-300">
            {/* HEADER / FACULTY POSITION */}
            <div className="p-4 border border-divider dark:border-stone-800 bg-paper-dim dark:bg-stone-900/60 rounded-none flex items-center justify-between">
              <div>
                <p className="text-[9px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">FACULTY_POSITION</p>
                <p className="text-sm font-serif font-bold text-brand-500 dark:text-stone-100 mt-1">
                  {[viewingTeacher.first_name, viewingTeacher.middle_name, viewingTeacher.last_name].filter(Boolean).join(' ') || '—'}
                </p>
                <p className="text-[10px] font-mono text-ink-muted/80 mt-0.5">
                  {viewingTeacher.qualification}
                  {viewingTeacher.specialization && ` — ${viewingTeacher.specialization}`}
                </p>
              </div>
              <Badge variant={viewingTeacher.status === 'ACTIVE' ? 'success' : 'default'}>
                {viewingTeacher.status}
              </Badge>
            </div>

            {/* IDENTITY_RECORD */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                IDENTITY_RECORD
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">FULL_NAME:</span> <span className="font-medium">
                  {[viewingTeacher.first_name, viewingTeacher.middle_name, viewingTeacher.last_name].filter(Boolean).join(' ') || '—'}
                </span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">GENDER:</span> <span>{viewingTeacher.gender}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">DATE_OF_BIRTH:</span> <span className="font-mono">{viewingTeacher.date_of_birth}</span></div>
              </div>
            </div>

            {/* EMPLOYMENT_RECORD */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                EMPLOYMENT_RECORD
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">EMPLOYEE_ID:</span> <span className="font-mono">{viewingTeacher.employee_id}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">JOINING_DATE:</span> <span className="font-mono">{viewingTeacher.joining_date}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">EXPERIENCE_YEARS:</span> <span>{viewingTeacher.experience_years || 0} years</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">STATUS:</span> <span>{viewingTeacher.status}</span></div>
              </div>
            </div>

            {/* PROFESSIONAL_RECORD */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                PROFESSIONAL_RECORD
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">QUALIFICATION:</span> <span className="font-medium">{viewingTeacher.qualification}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">SPECIALIZATION:</span> <span className="font-medium">{viewingTeacher.specialization || '—'}</span></div>
              </div>
            </div>

            {/* CONTACT_REGISTER */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                CONTACT_REGISTER
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">PHONE:</span> <span className="font-mono">{viewingTeacher.phone}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">EMAIL:</span> <span className="font-mono">{viewingTeacher.email}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">EMERGENCY_CONTACT:</span> <span className="font-mono">{viewingTeacher.emergency_contact || '—'}</span></div>
              </div>
            </div>

            {/* ADDRESS_RECORD */}
            <div>
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500 border-b border-divider pb-1 mb-2.5">
                ADDRESS_RECORD
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-y-2 gap-x-4 text-xs">
                <div className="md:col-span-2"><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">ADDRESS_LINE1:</span> <span>{viewingTeacher.address_line1}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">CITY:</span> <span>{viewingTeacher.city}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">DISTRICT:</span> <span>{viewingTeacher.district}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">STATE:</span> <span>{viewingTeacher.state}</span></div>
                <div><span className="font-mono text-ink-muted text-[10px] mr-1 uppercase">POSTAL_CODE:</span> <span className="font-mono">{viewingTeacher.postal_code}</span></div>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteTeacherMutation.mutate(deleteTarget.id)}
        title={`Soft Delete Teacher`}
        message={`Are you sure you want to soft delete teacher "${deleteTarget?.first_name} ${deleteTarget?.last_name || ''}" (${deleteTarget?.employee_id})?`}
        isLoading={deleteTeacherMutation.isPending}
      />
    </div>
  );
};
