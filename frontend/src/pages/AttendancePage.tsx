import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { attendanceApi } from '@/services/api/attendanceApi';
import { AttendanceStatus, Attendance } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { ErrorState } from '@/components/ui/ErrorState';

export const AttendancePage: React.FC = () => {
  const { permissions } = useAuthStore();
  const queryClient = useQueryClient();

  const [selectedYearId, setSelectedYearId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState('');
  const [selectedDate, setSelectedDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });

  const [localRegistry, setLocalRegistry] = useState<
    Record<
      string,
      {
        status: AttendanceStatus;
        remarks: string;
        attendance_id: string | null;
      }
    >
  >({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Queries
  const {
    data: yearsData,
    isLoading: isYearsLoading,
    isError: isYearsError,
    error: yearsError,
    refetch: refetchYears,
  } = useQuery({
    queryKey: ['academicYearsList'],
    queryFn: () => academicYearsApi.getAcademicYears({ page: 1, page_size: 100 }),
    enabled: permissions.includes('attendance.view'),
  });

  const {
    data: classesData,
    isLoading: isClassesLoading,
    isError: isClassesError,
    error: classesError,
    refetch: refetchClasses,
  } = useQuery({
    queryKey: ['schoolClassesList'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: 1, page_size: 100 }),
    enabled: permissions.includes('attendance.view'),
  });

  const {
    data: sectionsData,
    isLoading: isSectionsLoading,
    isError: isSectionsError,
    error: sectionsError,
    refetch: refetchSections,
  } = useQuery({
    queryKey: ['sectionsByClass', selectedClassId],
    queryFn: () => sectionsApi.getSectionsByClass(selectedClassId, { page: 1, page_size: 100 }),
    enabled: permissions.includes('attendance.view') && !!selectedClassId,
  });

  const {
    data: studentsData,
    isLoading: isStudentsLoading,
    isError: isStudentsError,
    error: studentsError,
    refetch: refetchStudents,
  } = useQuery({
    queryKey: ['studentsListForAttendance', selectedSectionId],
    queryFn: () =>
      studentsApi.getStudents({
        section_id: selectedSectionId,
        status: 'ACTIVE',
        page_size: 100,
      }),
    enabled: permissions.includes('attendance.view') && !!selectedSectionId,
  });

  const {
    data: attendanceData,
    isLoading: isAttendanceLoading,
    isError: isAttendanceError,
    error: attendanceError,
    refetch: refetchAttendance,
  } = useQuery({
    queryKey: ['attendanceListForRegister', selectedSectionId, selectedDate],
    queryFn: () =>
      attendanceApi.getAttendance({
        section_id: selectedSectionId,
        attendance_date: selectedDate,
        page_size: 100,
      }),
    enabled: permissions.includes('attendance.view') && !!selectedSectionId && !!selectedDate,
  });

  // Pre-select current academic year when loaded
  useEffect(() => {
    if (yearsData?.items && yearsData.items.length > 0 && !selectedYearId) {
      const activeYear = yearsData.items.find((y) => y.status === 'ACTIVE');
      if (activeYear) {
        setSelectedYearId(activeYear.id);
      } else {
        setSelectedYearId(yearsData.items[0].id);
      }
    }
  }, [yearsData, selectedYearId]);

  // Synchronize database records with local registry state
  useEffect(() => {
    if (!studentsData?.items) {
      setLocalRegistry({});
      return;
    }

    const registry: Record<
      string,
      {
        status: AttendanceStatus;
        remarks: string;
        attendance_id: string | null;
      }
    > = {};
    const attendanceMap = new Map<string, Attendance>();

    if (attendanceData?.items) {
      attendanceData.items.forEach((record) => {
        attendanceMap.set(record.student_id, record);
      });
    }

    studentsData.items.forEach((student) => {
      const existing = attendanceMap.get(student.id);
      if (existing) {
        registry[student.id] = {
          status: existing.status,
          remarks: existing.remarks || '',
          attendance_id: existing.id,
        };
      } else {
        registry[student.id] = {
          status: 'PRESENT',
          remarks: '',
          attendance_id: null,
        };
      }
    });

    setLocalRegistry(registry);
  }, [studentsData, attendanceData]);

  // Reset section select when class changes
  const handleClassChange = (classId: string) => {
    setSelectedClassId(classId);
    setSelectedSectionId('');
  };

  const handleStatusChange = (studentId: string, status: AttendanceStatus) => {
    setLocalRegistry((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        status,
      },
    }));
  };

  const handleRemarksChange = (studentId: string, remarks: string) => {
    setLocalRegistry((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        remarks,
      },
    }));
  };

  const handleSaveAttendance = async () => {
    if (!selectedSectionId || !selectedDate || !studentsData?.items) return;
    setSaveError(null);
    setSaveSuccess(null);
    setIsSaving(true);

    try {
      const newRecordsPayload: any[] = [];
      const updatePromises: Promise<any>[] = [];

      studentsData.items.forEach((student) => {
        const local = localRegistry[student.id];
        if (!local) return;

        if (local.attendance_id === null) {
          newRecordsPayload.push({
            student_id: student.id,
            status: local.status,
            remarks: local.remarks || undefined,
          });
        } else {
          const existing = attendanceData?.items?.find((r) => r.student_id === student.id);
          if (existing) {
            const hasChanged =
              local.status !== existing.status || local.remarks !== (existing.remarks || '');
            if (hasChanged) {
              updatePromises.push(
                attendanceApi.updateAttendance(local.attendance_id, {
                  status: local.status,
                  remarks: local.remarks || null,
                })
              );
            }
          }
        }
      });

      // Submit new records via POST /bulk
      if (newRecordsPayload.length > 0) {
        await attendanceApi.createBulkAttendance({
          section_id: selectedSectionId,
          attendance_date: selectedDate,
          records: newRecordsPayload,
        });
      }

      // Execute updates via PUT /attendance/{id} in parallel
      if (updatePromises.length > 0) {
        await Promise.all(updatePromises);
      }

      setSaveSuccess('Attendance register saved successfully.');
      await queryClient.invalidateQueries({
        queryKey: ['attendanceListForRegister', selectedSectionId, selectedDate],
      });
    } catch (err: any) {
      console.error(err);
      if (err.status === 409 || err.message?.includes('already exists') || err.message?.includes('409')) {
        setSaveError('Attendance records already exist for one or more students on this date. Please reload or check logs.');
      } else if (err.status === 403 || err.message?.includes('403')) {
        setSaveError('You do not have authorization to modify these attendance records.');
      } else {
        setSaveError(err.message || 'Failed to save attendance registry.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleRetryAll = () => {
    if (isYearsError) refetchYears();
    if (isClassesError) refetchClasses();
    if (isSectionsError) refetchSections();
    if (isStudentsError) refetchStudents();
    if (isAttendanceError) refetchAttendance();
  };

  // RBAC Gating
  const hasViewPermission = permissions.includes('attendance.view');
  const hasCreatePermission = permissions.includes('attendance.create');
  const hasUpdatePermission = permissions.includes('attendance.update');

  if (!hasViewPermission) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorState
          title="Access Denied"
          message="You do not have permission to view daily attendance registers."
        />
      </div>
    );
  }

  const isQueryError =
    isYearsError || isClassesError || isSectionsError || isStudentsError || isAttendanceError;

  if (isQueryError) {
    const errorMsg =
      (yearsError as any)?.message ||
      (classesError as any)?.message ||
      (sectionsError as any)?.message ||
      (studentsError as any)?.message ||
      (attendanceError as any)?.message ||
      'Failed to load daily attendance registry dependencies.';

    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorState
          title="Daily Attendance Registry Configuration Error"
          message={errorMsg}
          onRetry={handleRetryAll}
        />
      </div>
    );
  }

  // Registry columns
  const columns: Column<any>[] = [
    {
      key: 'admission_number',
      header: 'Admission No',
      className: 'w-36 font-mono text-xs font-bold text-brand-500 dark:text-brand-350',
      render: (row) => row.admission_number,
    },
    {
      key: 'full_name',
      header: 'Student Name',
      className: 'font-semibold text-ink dark:text-stone-100',
      render: (row) => row.full_name,
    },
    {
      key: 'status',
      header: 'Attendance Status',
      className: 'w-48',
      render: (row) => {
        const local = localRegistry[row.id];
        if (!local) return null;

        const isNewRecord = local.attendance_id === null;
        const canEdit = isNewRecord ? hasCreatePermission : hasUpdatePermission;

        return (
          <select
            value={local.status}
            onChange={(e) => handleStatusChange(row.id, e.target.value as AttendanceStatus)}
            disabled={!canEdit}
            className="w-full px-2 py-1 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
          >
            <option value="PRESENT">PRESENT</option>
            <option value="ABSENT">ABSENT</option>
            <option value="LATE">LATE</option>
            <option value="HALF_DAY">HALF_DAY</option>
            <option value="EXCUSED">EXCUSED</option>
          </select>
        );
      },
    },
    {
      key: 'remarks',
      header: 'Remarks',
      render: (row) => {
        const local = localRegistry[row.id];
        if (!local) return null;

        const isNewRecord = local.attendance_id === null;
        const canEdit = isNewRecord ? hasCreatePermission : hasUpdatePermission;

        return (
          <Input
            value={local.remarks}
            placeholder="e.g. Medical leave, late entry"
            onChange={(e) => handleRemarksChange(row.id, e.target.value)}
            disabled={!canEdit}
            className="text-xs py-0.5"
          />
        );
      },
    },
  ];

  // Submission gating
  const hasNew = Object.values(localRegistry).some((r) => r.attendance_id === null);
  const hasChangedExisting = Object.keys(localRegistry).some((studentId) => {
    const local = localRegistry[studentId];
    if (local.attendance_id === null) return false;
    const existing = attendanceData?.items?.find((r) => r.student_id === studentId);
    return (
      existing &&
      (local.status !== existing.status || local.remarks !== (existing.remarks || ''))
    );
  });

  const isSaveDisabled =
    isSaving ||
    !selectedSectionId ||
    (hasNew && !hasCreatePermission) ||
    (hasChangedExisting && !hasUpdatePermission) ||
    (!hasNew && !hasChangedExisting);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh]">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            DAILY ATTENDANCE SERVICE
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Daily Attendance Registry
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Mark daily section rolls, add attendance remarks, and modify historical logs.
          </p>
        </div>
      </div>

      {/* Selectors Area */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-4 gap-3 w-full">
          <div>
            <label
              htmlFor="year-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Academic Year
            </label>
            <select
              id="year-select"
              value={selectedYearId}
              onChange={(e) => setSelectedYearId(e.target.value)}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
            >
              <option value="">Select Year</option>
              {yearsData?.items?.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.name} ({y.status})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="class-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Class
            </label>
            <select
              id="class-select"
              value={selectedClassId}
              onChange={(e) => handleClassChange(e.target.value)}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
            >
              <option value="">Select Class</option>
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="section-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Section
            </label>
            <select
              id="section-select"
              value={selectedSectionId}
              onChange={(e) => setSelectedSectionId(e.target.value)}
              disabled={!selectedClassId}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white disabled:opacity-40"
            >
              <option value="">Select Section</option>
              {sectionsData?.items?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="date-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Attendance Date
            </label>
            <input
              type="date"
              id="date-select"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full px-2 py-1 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white min-h-[30px]"
            />
          </div>
        </div>
      </div>

      {/* Messages */}
      {saveError && (
        <Alert type="error" title="Submission Error">
          {saveError}
        </Alert>
      )}
      {saveSuccess && <Alert type="success">{saveSuccess}</Alert>}

      {/* Roster & Table Grid */}
      {!selectedClassId || !selectedSectionId ? (
        <div className="p-8 border border-slate-200 dark:border-slate-800 bg-white text-center">
          <p className="text-xs text-slate-500 font-mono">
            SELECT CLASS AND SECTION TO MOUNT DAILY REGISTRAR ROSTER.
          </p>
        </div>
      ) : (
        <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
              DAILY_STUDENT_REGISTER
            </p>
            <div className="flex items-center gap-3">
              {attendanceData && attendanceData.total > 0 ? (
                <Badge variant="success">LOGGED</Badge>
              ) : (
                <Badge variant="default">UNMARKED</Badge>
              )}
              <Button onClick={handleSaveAttendance} disabled={isSaveDisabled}>
                {isSaving ? 'Saving...' : 'Save Registry Roll'}
              </Button>
            </div>
          </div>

          <Table
            columns={columns}
            data={studentsData?.items || []}
            isLoading={isStudentsLoading || isAttendanceLoading}
            emptyText="No active students enrolled in this section."
          />
        </div>
      )}
    </div>
  );
};
