import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teachersApi, teacherAttendanceApi, TeacherAttendanceItem } from '@/services/api';
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
import { ErrorState } from '@/components/ui/ErrorState';
import { Calendar, Clock } from 'lucide-react';

export const TeachersPage: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'directory' | 'attendance'>('directory');
  const [attendanceDate, setAttendanceDate] = useState<string>(new Date().toISOString().split('T')[0]);

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
    emergency_contact: '',
    address_line1: '',
    city: '',
    district: '',
    state: '',
    postal_code: '110001',
    status: 'ACTIVE',
  });

  const [formError, setFormError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string> | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Directory Queries
  const {
    data: teachersData,
    isLoading: isTeachersLoading,
    isError: isTeachersError,
    error: teachersError,
    refetch: refetchTeachers,
  } = useQuery({
    queryKey: ['teachers', page, pageSize, search, selectedStatusFilter],
    queryFn: () =>
      teachersApi.getTeachers({
        page,
        page_size: pageSize,
        search: search || undefined,
        status: selectedStatusFilter || undefined,
      }),
  });

  // Attendance Queries
  const {
    data: attendanceList,
    isLoading: isAttendanceLoading,
    refetch: refetchAttendance,
  } = useQuery({
    queryKey: ['teacherAttendance', attendanceDate],
    queryFn: () => teacherAttendanceApi.list(attendanceDate),
    enabled: activeTab === 'attendance',
  });

  const { data: attendanceSummary } = useQuery({
    queryKey: ['teacherAttendanceSummary', attendanceDate],
    queryFn: () => teacherAttendanceApi.getSummary(attendanceDate),
    enabled: activeTab === 'attendance',
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
      setDeleteError(null);
    },
    onError: (err: any) => {
      setDeleteError(err.message || 'Failed to delete teacher record.');
      setDeleteTarget(null);
    },
  });

  const updateAttendanceMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      teacherAttendanceApi.update(id, { status: status as any }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacherAttendance'] });
      queryClient.invalidateQueries({ queryKey: ['teacherAttendanceSummary'] });
    },
  });

  const checkInMutation = useMutation({
    mutationFn: () => teacherAttendanceApi.checkIn(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacherAttendance'] });
      queryClient.invalidateQueries({ queryKey: ['teacherAttendanceSummary'] });
    },
  });

  const checkOutMutation = useMutation({
    mutationFn: () => teacherAttendanceApi.checkOut(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacherAttendance'] });
      queryClient.invalidateQueries({ queryKey: ['teacherAttendanceSummary'] });
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
      emergency_contact: '',
      address_line1: '',
      city: '',
      district: '',
      state: '',
      postal_code: '110001',
      status: 'ACTIVE',
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
      emergency_contact: teacher.emergency_contact || '',
      address_line1: teacher.address_line1,
      city: teacher.city,
      district: teacher.district,
      state: teacher.state,
      postal_code: teacher.postal_code,
      status: teacher.status,
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
          gender: teacherForm.gender,
          qualification: teacherForm.qualification,
          specialization: teacherForm.specialization,
          experience_years: teacherForm.experience_years,
          phone: teacherForm.phone,
          email: teacherForm.email,
          emergency_contact: teacherForm.emergency_contact,
          address_line1: teacherForm.address_line1,
          city: teacherForm.city,
          district: teacherForm.district,
          state: teacherForm.state,
          postal_code: teacherForm.postal_code,
          status: teacherForm.status,
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

  const attendanceVariant = (status: string) => {
    switch (status) {
      case 'PRESENT': return 'success';
      case 'LATE': return 'warning';
      case 'ABSENT': return 'error';
      case 'LEAVE': return 'info';
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
      render: (row) => (
        <div>
          <div className="font-medium text-xs text-ink dark:text-stone-200">
            {row.first_name} {row.last_name}
          </div>
          <div className="text-[10px] text-ink-muted dark:text-stone-400 font-mono">{row.email}</div>
        </div>
      ),
    },
    {
      key: 'qualification',
      header: 'Qualification',
      render: (row) => <span className="text-xs">{row.qualification}</span>,
    },
    {
      key: 'phone',
      header: 'Phone Number',
      render: (row) => <span className="font-mono text-xs text-ink-muted">{row.phone}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <Badge variant={statusVariant(row.status)}>{row.status}</Badge>,
    },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right min-w-[10rem]',
      render: (row) => (
        <div className="flex justify-end gap-1.5">
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

  const attendanceColumns: Column<TeacherAttendanceItem>[] = [
    {
      key: 'employee_id',
      header: 'Employee ID',
      render: (row) => <span className="font-mono text-xs font-bold text-brand-500">{row.employee_id || 'STAFF'}</span>,
    },
    {
      key: 'teacher_name',
      header: 'Staff Member',
      render: (row) => (
        <div>
          <div className="font-medium text-xs text-ink dark:text-stone-200">{row.teacher_name}</div>
          <div className="text-[10px] text-ink-muted font-mono">{row.department || 'Academic Staff'}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Attendance Status',
      render: (row) => <Badge variant={attendanceVariant(row.status)}>{row.status}</Badge>,
    },
    {
      key: 'check_in',
      header: 'Check In',
      render: (row) => <span className="font-mono text-xs">{row.check_in_time || '—'}</span>,
    },
    {
      key: 'check_out',
      header: 'Check Out',
      render: (row) => <span className="font-mono text-xs">{row.check_out_time || '—'}</span>,
    },
    {
      key: 'actions',
      header: 'Quick Action',
      className: 'text-right min-w-[14rem]',
      render: (row) => (
        <div className="flex justify-end gap-1">
          <Button
            variant={row.status === 'PRESENT' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => updateAttendanceMutation.mutate({ id: row.id, status: 'PRESENT' })}
          >
            Present
          </Button>
          <Button
            variant={row.status === 'ABSENT' ? 'danger' : 'outline'}
            size="sm"
            onClick={() => updateAttendanceMutation.mutate({ id: row.id, status: 'ABSENT' })}
          >
            Absent
          </Button>
          <Button
            variant={row.status === 'LATE' ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => updateAttendanceMutation.mutate({ id: row.id, status: 'LATE' })}
          >
            Late
          </Button>
          <Button
            variant={row.status === 'LEAVE' ? 'ghost' : 'outline'}
            size="sm"
            onClick={() => updateAttendanceMutation.mutate({ id: row.id, status: 'LEAVE' })}
          >
            Leave
          </Button>
        </div>
      ),
    },
  ];

  if (isTeachersError) {
    return (
      <div className="p-6">
        <ErrorState
          title="Staff Directory Error"
          message={(teachersError as any)?.message || 'Failed to load teacher directory.'}
          onRetry={() => refetchTeachers()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh]">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-divider pb-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted dark:text-stone-500">
            STAFF_MANAGEMENT // DIRECTORY_AND_ATTENDANCE
          </p>
          <h1 className="text-2xl font-serif font-bold text-brand-500 dark:text-stone-100 mt-1">
            Teacher & Staff Workstation
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => checkInMutation.mutate()}
            isLoading={checkInMutation.isPending}
          >
            <Clock className="w-3.5 h-3.5 mr-1 text-green-600" />
            Check In
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => checkOutMutation.mutate()}
            isLoading={checkOutMutation.isPending}
          >
            <Clock className="w-3.5 h-3.5 mr-1 text-amber-600" />
            Check Out
          </Button>

          {activeTab === 'directory' && (
            <Button variant="primary" size="sm" onClick={handleOpenCreateModal}>
              + Register New Staff
            </Button>
          )}
        </div>
      </div>

      {deleteError && (
        <Alert type="error" title="Delete Operation Failed">
          {deleteError}
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-divider gap-4">
        <button
          onClick={() => setActiveTab('directory')}
          className={`pb-2.5 text-xs font-mono font-bold border-b-2 uppercase transition-colors ${
            activeTab === 'directory'
              ? 'border-brand-500 text-brand-500 dark:text-stone-100'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          Staff Directory
        </button>
        <button
          onClick={() => setActiveTab('attendance')}
          className={`pb-2.5 text-xs font-mono font-bold border-b-2 uppercase transition-colors ${
            activeTab === 'attendance'
              ? 'border-brand-500 text-brand-500 dark:text-stone-100'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          Staff Attendance Workstation
        </button>
      </div>

      {/* TAB 1: STAFF DIRECTORY */}
      {activeTab === 'directory' && (
        <Card className="p-4 space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between">
            <div className="w-full md:w-72">
              <Input
                placeholder="Search teacher by name or ID..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="flex gap-2">
              <select
                className="text-xs border border-divider rounded p-2 bg-paper dark:bg-stone-900"
                value={selectedStatusFilter}
                onChange={(e) => {
                  setSelectedStatusFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="ON_LEAVE">On Leave</option>
                <option value="INACTIVE">Inactive</option>
                <option value="RESIGNED">Resigned</option>
              </select>
            </div>
          </div>

          <Table
            columns={teacherColumns}
            data={teachersData?.items || []}
            rowKey={(row) => row.id}
            isLoading={isTeachersLoading}
            emptyText="No teachers found in registry."
          />

          {teachersData && teachersData.total_pages > 1 && (
            <Pagination
              page={page}
              totalPages={teachersData.total_pages}
              onPageChange={(p) => setPage(p)}
            />
          )}
        </Card>
      )}

      {/* TAB 2: STAFF ATTENDANCE WORKSTATION */}
      {activeTab === 'attendance' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-paper-dim dark:bg-stone-900/60 p-4 border border-divider">
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-brand-500" />
              <label className="text-xs font-mono uppercase font-bold text-ink-muted">Select Date:</label>
              <input
                type="date"
                className="text-xs font-mono border border-divider px-3 py-1.5 rounded bg-paper dark:bg-stone-950"
                value={attendanceDate}
                onChange={(e) => setAttendanceDate(e.target.value)}
              />
            </div>

            <Button variant="outline" size="sm" onClick={() => refetchAttendance()}>
              Refresh Roster
            </Button>
          </div>

          {/* Attendance Metric Summary Bar */}
          {attendanceSummary && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Card className="p-3 text-center border-brand-500/30">
                <p className="text-[10px] font-mono uppercase text-ink-muted">TOTAL STAFF</p>
                <p className="text-xl font-bold font-mono text-brand-500">{attendanceSummary.total_teachers}</p>
              </Card>
              <Card className="p-3 text-center border-green-500/30">
                <p className="text-[10px] font-mono uppercase text-green-600">PRESENT</p>
                <p className="text-xl font-bold font-mono text-green-600">{attendanceSummary.present_count}</p>
              </Card>
              <Card className="p-3 text-center border-red-500/30">
                <p className="text-[10px] font-mono uppercase text-red-600">ABSENT</p>
                <p className="text-xl font-bold font-mono text-red-600">{attendanceSummary.absent_count}</p>
              </Card>
              <Card className="p-3 text-center border-amber-500/30">
                <p className="text-[10px] font-mono uppercase text-amber-600">LATE</p>
                <p className="text-xl font-bold font-mono text-amber-600">{attendanceSummary.late_count}</p>
              </Card>
              <Card className="p-3 text-center border-blue-500/30">
                <p className="text-[10px] font-mono uppercase text-blue-600">LEAVE</p>
                <p className="text-xl font-bold font-mono text-blue-600">{attendanceSummary.leave_count}</p>
              </Card>
            </div>
          )}

          <Card className="p-4">
            <Table
              columns={attendanceColumns}
              data={attendanceList || []}
              rowKey={(row) => row.id}
              isLoading={isAttendanceLoading}
              emptyText="No attendance records available for selected date."
            />
          </Card>
        </div>
      )}

      {/* Modal: Create/Edit Teacher */}
      <Modal
        isOpen={isTeacherModalOpen}
        onClose={() => setIsTeacherModalOpen(false)}
        title={editingTeacher ? 'Edit Teacher Record' : 'Register New Staff Member'}
      >
        <div className="space-y-4 py-2">
          {formError && <Alert type="error" title="Validation Failed">{formError}</Alert>}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="first_name" className="text-[11px] font-mono uppercase text-ink-muted">First Name *</label>
              <Input
                id="first_name"
                value={teacherForm.first_name}
                onChange={(e) => setTeacherForm({ ...teacherForm, first_name: e.target.value })}
                error={validationErrors?.first_name}
              />
            </div>
            <div>
              <label htmlFor="last_name" className="text-[11px] font-mono uppercase text-ink-muted">Last Name *</label>
              <Input
                id="last_name"
                value={teacherForm.last_name}
                onChange={(e) => setTeacherForm({ ...teacherForm, last_name: e.target.value })}
                error={validationErrors?.last_name}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="email" className="text-[11px] font-mono uppercase text-ink-muted">Email Address *</label>
              <Input
                id="email"
                type="email"
                value={teacherForm.email}
                onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })}
                error={validationErrors?.email}
              />
            </div>
            <div>
              <label htmlFor="phone" className="text-[11px] font-mono uppercase text-ink-muted">Phone Number *</label>
              <Input
                id="phone"
                value={teacherForm.phone}
                onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })}
                error={validationErrors?.phone}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="qualification" className="text-[11px] font-mono uppercase text-ink-muted">Qualification *</label>
              <Input
                id="qualification"
                value={teacherForm.qualification}
                onChange={(e) => setTeacherForm({ ...teacherForm, qualification: e.target.value })}
                error={validationErrors?.qualification}
              />
            </div>
            <div>
              <label htmlFor="specialization" className="text-[11px] font-mono uppercase text-ink-muted">Specialization</label>
              <Input
                id="specialization"
                value={teacherForm.specialization}
                onChange={(e) => setTeacherForm({ ...teacherForm, specialization: e.target.value })}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setIsTeacherModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmitTeacher}
              isLoading={createTeacherMutation.isPending || updateTeacherMutation.isPending}
            >
              {editingTeacher ? 'Save Changes' : 'Create Teacher'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Drawer: Viewing Teacher Details */}
      <Drawer
        isOpen={!!viewingTeacher}
        onClose={() => setViewingTeacher(null)}
        title="Teacher Comprehensive Profile"
      >
        {viewingTeacher && (
          <div className="space-y-6 text-xs">
            <div className="border-b border-divider pb-3">
              <h2 className="text-lg font-bold text-brand-500 font-serif">
                {viewingTeacher.first_name} {viewingTeacher.last_name}
              </h2>
              <p className="font-mono text-ink-muted">{viewingTeacher.email}</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><span className="font-mono text-ink-muted">EMPLOYEE ID:</span> {viewingTeacher.employee_id}</div>
              <div><span className="font-mono text-ink-muted">QUALIFICATION:</span> {viewingTeacher.qualification}</div>
              <div><span className="font-mono text-ink-muted">STATUS:</span> {viewingTeacher.status}</div>
              <div><span className="font-mono text-ink-muted">PHONE:</span> {viewingTeacher.phone}</div>
            </div>
          </div>
        )}
      </Drawer>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteTeacherMutation.mutate(deleteTarget.id)}
        title="Soft Delete Teacher"
        message={`Are you sure you want to soft delete teacher "${deleteTarget?.first_name} ${deleteTarget?.last_name || ''}" (${deleteTarget?.employee_id})?`}
        isLoading={deleteTeacherMutation.isPending}
      />
    </div>
  );
};