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
    queryKey: ['teachers', page, pageSize, search],
    queryFn: () => teachersApi.getTeachers({ page, page_size: pageSize, search: search || undefined }),
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
      case 'RESIGNED':
      case 'TERMINATED': return 'error';
      default: return 'default';
    }
  };

  const columns: Column<Teacher>[] = [
    {
      key: 'employee_id',
      header: 'Employee ID',
      render: (row) => <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">{row.employee_id}</span>,
    },
    {
      key: 'name',
      header: 'Teacher Name',
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">
            {row.first_name} {row.last_name}
          </p>
          <p className="text-xs text-slate-400">{row.gender}</p>
        </div>
      ),
    },
    {
      key: 'qualification',
      header: 'Qualification',
      render: (row) => <span className="text-sm text-slate-600 dark:text-slate-300">{row.qualification}</span>,
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (row) => <span className="font-mono text-xs text-slate-600 dark:text-slate-300">{row.phone}</span>,
    },
    {
      key: 'joining_date',
      header: 'Joining Date',
      render: (row) => <span className="text-xs text-slate-500">{row.joining_date}</span>,
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
      render: (row) => (
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setViewingTeacher(row)}>
            View
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleOpenEditModal(row)}>
            Edit
          </Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8]">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            OFFICE OF THE REGISTRAR
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Faculty Directory
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Directory of institutional teachers, professional qualifications, and employment logs.
          </p>
        </div>
        <Button onClick={handleOpenCreateModal}>+ Add Teacher</Button>
      </div>

      <div className="p-4 border border-slate-200 dark:border-slate-800 bg-white rounded-none">
        <Input
          placeholder="Search by teacher name, employee ID, or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 space-y-4 rounded-none">
        <Table
          columns={columns}
          data={teachersData?.items || []}
          isLoading={isTeachersLoading}
          emptyText="No teachers found matching the search criteria."
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
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsTeacherModalOpen(false)}>
              Cancel
            </Button>
            <Button
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
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Gender *
              </label>
              <select
                value={teacherForm.gender || 'MALE'}
                onChange={(e) => setTeacherForm({ ...teacherForm, gender: e.target.value as any })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
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
        title={viewingTeacher ? `${viewingTeacher.first_name} ${viewingTeacher.last_name || ''}` : ''}
        subtitle={viewingTeacher ? `Employee ID: ${viewingTeacher.employee_id}` : ''}
        width="md"
      >
        {viewingTeacher && (
          <div className="space-y-6 text-slate-800 dark:text-slate-350">
            <div className="p-4 bg-[#fcf9f8] rounded-none border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">FACULTY_POSITION</p>
                <p className="text-base font-bold font-serif text-slate-900 dark:text-white mt-1">
                  {viewingTeacher.qualification}
                </p>
                {viewingTeacher.specialization && (
                  <p className="text-[10px] text-slate-500 font-mono mt-0.5">SPECIALIZATION: {viewingTeacher.specialization}</p>
                )}
              </div>
              <Badge variant={viewingTeacher.status === 'ACTIVE' ? 'success' : 'default'}>
                {viewingTeacher.status}
              </Badge>
            </div>

            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 border-b border-slate-200 pb-1.5 mb-2">IDENTITY_RECORD</h3>
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div><span className="text-slate-400">GENDER:</span> {viewingTeacher.gender}</div>
                <div><span className="text-slate-400">DATE_OF_BIRTH:</span> {viewingTeacher.date_of_birth}</div>
                <div><span className="text-slate-400">JOINING_DATE:</span> {viewingTeacher.joining_date}</div>
                <div><span className="text-slate-400">EXPERIENCE_RECORD:</span> {viewingTeacher.experience_years || 0} years</div>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 border-b border-slate-200 pb-1.5 mb-2">CONTACT_RECORD</h3>
              <div className="grid grid-cols-1 gap-2 text-xs font-mono">
                <div><span className="text-slate-400">PHONE_CONTACT:</span> {viewingTeacher.phone}</div>
                <div><span className="text-slate-400">EMAIL_ADDRESS:</span> {viewingTeacher.email}</div>
                <div><span className="text-slate-400">RESIDENCE_ADDRESS:</span> {viewingTeacher.address_line1}, {viewingTeacher.city}, {viewingTeacher.state} — {viewingTeacher.postal_code}</div>
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
