import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { subjectsApi } from '@/services/api/subjectsApi';
import { teachersApi } from '@/services/api/teachersApi';
import { timetableApi } from '@/services/api/timetableApi';
import { periodSlotsApi } from '@/services/api/periodSlotsApi';
import { classroomsApi } from '@/services/api/classroomsApi';
import { substitutionsApi } from '@/services/api/substitutionsApi';
import {
  DayOfWeek,
  PeriodType,
  RoomType,
  TimetableEntryCreate,
  TimetableEntryDetail,
  TimetableDetail,
  PeriodSlot,
  PeriodSlotCreate,
  PeriodSlotUpdate,
  Classroom,
  ClassroomCreate,
  ClassroomUpdate,
  TeacherSubstitutionCreate,
  TeacherSubstitutionDetail,
} from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

const ALL_DAYS: DayOfWeek[] = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'];

export const TimetablePage: React.FC = () => {
  const { permissions } = useAuthStore();
  const hasPerm = (p: string) => permissions.includes(p);

  const [activeTab, setActiveTab] = useState<'builder' | 'slots' | 'rooms' | 'substitutions'>('builder');

  // Shared filter state
  const [selectedYearId, setSelectedYearId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState('');

  // Alerts
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const clearMessages = () => { setErrorMessage(null); setSuccessMessage(null); };

  // ===== Common queries =====
  const { data: yearsData } = useQuery({
    queryKey: ['ttYears'],
    queryFn: () => academicYearsApi.getAcademicYears({ page: 1, page_size: 100 }),
    enabled: hasPerm('timetable.view'),
  });

  const { data: classesData } = useQuery({
    queryKey: ['ttClasses'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: 1, page_size: 100 }),
    enabled: hasPerm('timetable.view'),
  });

  const { data: sectionsData } = useQuery({
    queryKey: ['ttSections', selectedClassId],
    queryFn: () => sectionsApi.getSectionsByClass(selectedClassId, { page: 1, page_size: 100 }),
    enabled: !!selectedClassId,
  });

  const { data: subjectsData } = useQuery({
    queryKey: ['ttSubjects'],
    queryFn: () => subjectsApi.getSubjects({ page_size: 200 }),
    enabled: hasPerm('timetable.view'),
  });

  const { data: teachersData } = useQuery({
    queryKey: ['ttTeachers'],
    queryFn: () => teachersApi.getTeachers({ page_size: 200 }),
    enabled: hasPerm('timetable.view'),
  });

  // Default year
  useEffect(() => {
    if (yearsData?.items?.length && !selectedYearId) {
      const active = yearsData.items.find((y) => y.status === 'ACTIVE');
      setSelectedYearId(active ? active.id : yearsData.items[0].id);
    }
  }, [yearsData, selectedYearId]);

  // ===== Tab 1: Timetable Builder =====
  const { data: timetableDetail, refetch: refetchTimetable, isError: isTtError, error: ttError } = useQuery({
    queryKey: ['ttSectionTimetable', selectedSectionId, selectedYearId],
    queryFn: () => timetableApi.getSectionTimetable(selectedSectionId, { academic_year_id: selectedYearId }),
    enabled: !!selectedSectionId && !!selectedYearId && activeTab === 'builder',
    retry: false,
  });

  const { data: periodSlotsForGrid } = useQuery({
    queryKey: ['ttPeriodSlotsGrid'],
    queryFn: () => periodSlotsApi.getPeriodSlots({ page_size: 100 }),
    enabled: hasPerm('timetable.view') && activeTab === 'builder',
  });

  const { data: classroomsForEntry } = useQuery({
    queryKey: ['ttClassroomsEntry'],
    queryFn: () => classroomsApi.getClassrooms({ page_size: 100 }),
    enabled: hasPerm('timetable.view'),
  });

  // Entry creation modal
  const [isEntryModalOpen, setIsEntryModalOpen] = useState(false);
  const [entryForm, setEntryForm] = useState<TimetableEntryCreate>({
    day_of_week: 'MONDAY',
    period_slot_id: '',
    subject_id: '',
    teacher_id: '',
    classroom_id: null,
  });

  // Create new timetable
  const handleCreateTimetable = async () => {
    if (!selectedYearId || !selectedClassId || !selectedSectionId) return;
    clearMessages();
    try {
      await timetableApi.createTimetable({
        school_id: '', // backend ignores this and uses current_user.school_id
        academic_year_id: selectedYearId,
        school_class_id: selectedClassId,
        section_id: selectedSectionId,
      });
      setSuccessMessage('Timetable created successfully.');
      refetchTimetable();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create timetable.');
    }
  };

  const handlePublish = async () => {
    if (!timetableDetail) return;
    clearMessages();
    try {
      await timetableApi.publishTimetable(timetableDetail.id);
      setSuccessMessage('Timetable published successfully.');
      refetchTimetable();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to publish timetable.');
    }
  };

  const handleArchive = async () => {
    if (!timetableDetail) return;
    clearMessages();
    try {
      await timetableApi.archiveTimetable(timetableDetail.id);
      setSuccessMessage('Timetable archived.');
      refetchTimetable();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to archive timetable.');
    }
  };

  const openEntryModal = (day: DayOfWeek, slotId: string) => {
    setEntryForm({ day_of_week: day, period_slot_id: slotId, subject_id: '', teacher_id: '', classroom_id: null });
    setIsEntryModalOpen(true);
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!timetableDetail) return;
    clearMessages();
    try {
      await timetableApi.addEntry(timetableDetail.id, entryForm);
      setSuccessMessage('Timetable entry added.');
      setIsEntryModalOpen(false);
      refetchTimetable();
    } catch (err: any) {
      setErrorMessage(err.message || 'Conflict: teacher or classroom may already be booked for this slot.');
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    if (!window.confirm('Remove this timetable entry?')) return;
    clearMessages();
    try {
      await timetableApi.deleteEntry(entryId);
      refetchTimetable();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to remove entry.');
    }
  };

  // Build grid lookup
  const gridMap = useMemo(() => {
    const map: Record<string, TimetableEntryDetail> = {};
    if (timetableDetail?.entries) {
      timetableDetail.entries.forEach((e) => {
        map[`${e.day_of_week}::${e.period_slot_id}`] = e;
      });
    }
    return map;
  }, [timetableDetail]);

  const sortedSlots = useMemo(() => {
    return [...(periodSlotsForGrid?.items || [])].sort((a, b) => a.display_order - b.display_order);
  }, [periodSlotsForGrid]);

  // ===== Tab 2: Period Slots =====
  const { data: periodSlotsData, refetch: refetchSlots, isError: isSlotsError, error: slotsError } = useQuery({
    queryKey: ['ttPeriodSlotsList'],
    queryFn: () => periodSlotsApi.getPeriodSlots({ page_size: 100 }),
    enabled: hasPerm('timetable.view') && activeTab === 'slots',
  });

  const [isSlotModalOpen, setIsSlotModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<PeriodSlot | null>(null);
  const [slotForm, setSlotForm] = useState<Partial<PeriodSlotCreate>>({
    name: '', period_type: 'REGULAR', start_time: '08:30', end_time: '09:15', display_order: 1,
  });

  const openSlotModal = (slot: PeriodSlot | null = null) => {
    if (slot) {
      setEditingSlot(slot);
      setSlotForm({
        name: slot.name,
        period_type: slot.period_type,
        start_time: slot.start_time,
        end_time: slot.end_time,
        display_order: slot.display_order,
      });
    } else {
      setEditingSlot(null);
      setSlotForm({ name: '', period_type: 'REGULAR', start_time: '08:30', end_time: '09:15', display_order: (periodSlotsData?.items?.length || 0) + 1 });
    }
    setIsSlotModalOpen(true);
  };

  const handleSaveSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    try {
      if (editingSlot) {
        const updatePayload: PeriodSlotUpdate = {
          name: slotForm.name, period_type: slotForm.period_type, start_time: slotForm.start_time, end_time: slotForm.end_time, display_order: slotForm.display_order,
        };
        await periodSlotsApi.updatePeriodSlot(editingSlot.id, updatePayload);
        setSuccessMessage('Period slot updated.');
      } else {
        await periodSlotsApi.createPeriodSlot({
          school_id: '',
          name: slotForm.name || '',
          period_type: slotForm.period_type,
          start_time: slotForm.start_time || '08:30',
          end_time: slotForm.end_time || '09:15',
          display_order: slotForm.display_order || 1,
        });
        setSuccessMessage('Period slot created.');
      }
      setIsSlotModalOpen(false);
      refetchSlots();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save period slot.');
    }
  };

  const handleDeleteSlot = async (id: string) => {
    if (!window.confirm('Delete this period slot?')) return;
    clearMessages();
    try {
      await periodSlotsApi.deletePeriodSlot(id);
      refetchSlots();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete period slot.');
    }
  };

  // ===== Tab 3: Classrooms =====
  const { data: classroomsData, refetch: refetchRooms, isError: isRoomsError, error: roomsError } = useQuery({
    queryKey: ['ttClassroomsList'],
    queryFn: () => classroomsApi.getClassrooms({ page_size: 100 }),
    enabled: hasPerm('timetable.view') && activeTab === 'rooms',
  });

  const [isRoomModalOpen, setIsRoomModalOpen] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Classroom | null>(null);
  const [roomForm, setRoomForm] = useState<Partial<ClassroomCreate>>({
    room_number: '', building_name: '', capacity: 40, room_type: 'CLASSROOM',
  });

  const openRoomModal = (room: Classroom | null = null) => {
    if (room) {
      setEditingRoom(room);
      setRoomForm({ room_number: room.room_number, building_name: room.building_name || '', capacity: room.capacity, room_type: room.room_type });
    } else {
      setEditingRoom(null);
      setRoomForm({ room_number: '', building_name: '', capacity: 40, room_type: 'CLASSROOM' });
    }
    setIsRoomModalOpen(true);
  };

  const handleSaveRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    try {
      if (editingRoom) {
        const updatePayload: ClassroomUpdate = {
          room_number: roomForm.room_number, building_name: roomForm.building_name, capacity: roomForm.capacity, room_type: roomForm.room_type,
        };
        await classroomsApi.updateClassroom(editingRoom.id, updatePayload);
        setSuccessMessage('Classroom updated.');
      } else {
        await classroomsApi.createClassroom({
          school_id: '',
          room_number: roomForm.room_number || '',
          building_name: roomForm.building_name || null,
          capacity: roomForm.capacity || 40,
          room_type: roomForm.room_type || 'CLASSROOM',
        });
        setSuccessMessage('Classroom created.');
      }
      setIsRoomModalOpen(false);
      refetchRooms();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save classroom.');
    }
  };

  const handleDeleteRoom = async (id: string) => {
    if (!window.confirm('Delete this classroom?')) return;
    clearMessages();
    try {
      await classroomsApi.deleteClassroom(id);
      refetchRooms();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete classroom.');
    }
  };

  // ===== Tab 4: Teacher Substitutions =====
  const [subDateFilter, setSubDateFilter] = useState('');

  const { data: subsData, refetch: refetchSubs, isError: isSubsError, error: subsError } = useQuery({
    queryKey: ['ttSubsList', subDateFilter],
    queryFn: () => substitutionsApi.getSubstitutions({
      substitution_date: subDateFilter || undefined,
      page_size: 100,
    }),
    enabled: hasPerm('substitution.view') && activeTab === 'substitutions',
  });

  const [isSubModalOpen, setIsSubModalOpen] = useState(false);
  const [subForm, setSubForm] = useState<Partial<TeacherSubstitutionCreate>>({
    timetable_entry_id: '', substitution_date: new Date().toISOString().split('T')[0], substitute_teacher_id: '', remarks: '',
  });

  const handleSaveSub = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    try {
      await substitutionsApi.createSubstitution({
        school_id: '',
        timetable_entry_id: subForm.timetable_entry_id || '',
        substitution_date: subForm.substitution_date || '',
        substitute_teacher_id: subForm.substitute_teacher_id || '',
        remarks: subForm.remarks || null,
      });
      setSuccessMessage('Substitution recorded successfully.');
      setIsSubModalOpen(false);
      refetchSubs();
    } catch (err: any) {
      setErrorMessage(err.message || 'Conflict: substitute teacher may already be booked.');
    }
  };

  const handleDeleteSub = async (id: string) => {
    if (!window.confirm('Delete this substitution record?')) return;
    clearMessages();
    try {
      await substitutionsApi.deleteSubstitution(id);
      refetchSubs();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete substitution.');
    }
  };

  // Status badge helper
  const statusBadge = (s: string) => {
    if (s === 'PUBLISHED') return <Badge variant="success">PUBLISHED</Badge>;
    if (s === 'ARCHIVED') return <Badge variant="default">ARCHIVED</Badge>;
    return <Badge variant="warning">DRAFT</Badge>;
  };

  const periodTypeBadge = (t: PeriodType) => {
    if (t === 'BREAK') return <Badge variant="warning">BREAK</Badge>;
    if (t === 'LUNCH') return <Badge variant="warning">LUNCH</Badge>;
    if (t === 'ASSEMBLY') return <Badge variant="default">ASSEMBLY</Badge>;
    return <Badge variant="success">REGULAR</Badge>;
  };

  // ===================================================================
  // RENDER
  // ===================================================================
  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
          SCHEDULING & OPERATIONS
        </p>
        <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
          Timetable & Scheduling Workspace
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure period slots, manage classrooms, build section timetables, and arrange teacher substitutions.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
        {[
          { key: 'builder' as const, label: 'Timetable Builder' },
          { key: 'slots' as const, label: 'Period Slots' },
          { key: 'rooms' as const, label: 'Classrooms' },
          { key: 'substitutions' as const, label: 'Teacher Substitutions' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => { setActiveTab(key); clearMessages(); }}
            className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider whitespace-nowrap ${
              activeTab === key
                ? 'border-brand-500 text-brand-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Alerts */}
      {errorMessage && <Alert type="error" title="Scheduling Error">{errorMessage}</Alert>}
      {successMessage && <Alert type="success">{successMessage}</Alert>}

      {/* ============================================================= */}
      {/* TAB 1 — TIMETABLE BUILDER */}
      {/* ============================================================= */}
      {activeTab === 'builder' && (
        <div className="space-y-4">
          {/* Context selectors */}
          <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label htmlFor="tt-year" className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Academic Year</label>
                <select id="tt-year" value={selectedYearId} onChange={(e) => { setSelectedYearId(e.target.value); setSelectedSectionId(''); }}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white">
                  <option value="">Select Year</option>
                  {yearsData?.items?.map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="tt-class" className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Class</label>
                <select id="tt-class" value={selectedClassId} onChange={(e) => { setSelectedClassId(e.target.value); setSelectedSectionId(''); }}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white">
                  <option value="">Select Class</option>
                  {classesData?.items?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="tt-section" className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Section</label>
                <select id="tt-section" value={selectedSectionId} onChange={(e) => setSelectedSectionId(e.target.value)}
                  disabled={!selectedClassId}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white disabled:opacity-40">
                  <option value="">Select Section</option>
                  {sectionsData?.items?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Timetable Grid */}
          {selectedSectionId && (
            <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <div className="flex items-center gap-3">
                  <p className="text-xs font-mono uppercase tracking-wider text-slate-500">SECTION_TIMETABLE_MATRIX</p>
                  {timetableDetail && statusBadge(timetableDetail.status)}
                </div>
                <div className="flex items-center gap-2">
                  {!timetableDetail && !isTtError && hasPerm('timetable.create') && (
                    <Button onClick={handleCreateTimetable}>Create Timetable</Button>
                  )}
                  {timetableDetail?.status === 'DRAFT' && hasPerm('timetable.publish') && (
                    <Button onClick={handlePublish}>Publish</Button>
                  )}
                  {timetableDetail?.status === 'PUBLISHED' && hasPerm('timetable.archive') && (
                    <Button variant="secondary" onClick={handleArchive}>Archive</Button>
                  )}
                </div>
              </div>

              {isTtError && (
                <div className="text-center py-8">
                  <p className="text-xs text-slate-500 mb-2">No timetable found for this section.</p>
                  {hasPerm('timetable.create') && (
                    <Button onClick={handleCreateTimetable}>Create Timetable</Button>
                  )}
                </div>
              )}

              {timetableDetail && sortedSlots.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left min-w-[700px] border border-slate-200">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="px-2 py-2 text-[10px] font-mono uppercase text-slate-500 border-r border-slate-200 w-24">Day</th>
                        {sortedSlots.map((slot) => (
                          <th key={slot.id} className="px-2 py-2 text-[10px] font-mono uppercase text-slate-500 border-r border-slate-200 text-center min-w-[120px]">
                            <div>{slot.name}</div>
                            <div className="text-[9px] text-slate-400 font-normal">{slot.start_time?.substring(0, 5)}–{slot.end_time?.substring(0, 5)}</div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {ALL_DAYS.map((day) => (
                        <tr key={day} className="border-b border-slate-100 hover:bg-slate-50/50">
                          <td className="px-2 py-2 text-[10px] font-mono font-bold uppercase text-slate-600 border-r border-slate-200">{day.substring(0, 3)}</td>
                          {sortedSlots.map((slot) => {
                            const entry = gridMap[`${day}::${slot.id}`];
                            return (
                              <td key={slot.id} className="px-1 py-1 border-r border-slate-100 text-center align-top min-w-[120px]">
                                {entry ? (
                                  <div className="bg-brand-500/5 border border-brand-500/20 rounded-sm p-1.5 text-[10px] leading-tight space-y-0.5 group relative">
                                    <div className="font-bold text-brand-500">{entry.subject.subject_code}</div>
                                    <div className="text-slate-600">{entry.teacher.first_name} {entry.teacher.last_name?.charAt(0)}.</div>
                                    {entry.classroom && <div className="text-slate-400">{entry.classroom.room_number}</div>}
                                    {hasPerm('timetable.delete') && timetableDetail.status === 'DRAFT' && (
                                      <button
                                        onClick={() => handleDeleteEntry(entry.id)}
                                        className="absolute top-0 right-0 text-red-400 hover:text-red-600 text-[9px] px-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Remove entry"
                                      >✕</button>
                                    )}
                                  </div>
                                ) : (
                                  timetableDetail.status === 'DRAFT' && hasPerm('timetable.create') ? (
                                    <button
                                      onClick={() => openEntryModal(day, slot.id)}
                                      className="w-full h-full min-h-[40px] text-[9px] text-slate-300 hover:text-brand-500 hover:bg-brand-500/5 transition-colors rounded-sm border border-dashed border-slate-200 hover:border-brand-500/30"
                                    >+ Add</button>
                                  ) : (
                                    <div className="min-h-[40px] flex items-center justify-center text-[9px] text-slate-200">—</div>
                                  )
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {timetableDetail && sortedSlots.length === 0 && (
                <p className="text-xs text-slate-500 text-center py-4">No period slots configured. Add period slots in the Period Slots tab first.</p>
              )}
            </div>
          )}

          {!selectedSectionId && (
            <p className="text-xs text-slate-500 text-center py-8">Select an Academic Year, Class, and Section to load or create a timetable.</p>
          )}
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 2 — PERIOD SLOTS */}
      {/* ============================================================= */}
      {activeTab === 'slots' && (
        <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">PERIOD_SLOT_CONFIGURATION</p>
            {hasPerm('timetable.create') && (
              <Button onClick={() => openSlotModal(null)}>Add Period Slot</Button>
            )}
          </div>

          {isSlotsError && (
            <Alert type="error" title="Failed to load period slots">
              {(slotsError as any)?.message || 'An error occurred.'}
              <Button variant="secondary" onClick={() => refetchSlots()} className="ml-2">Retry</Button>
            </Alert>
          )}

          <Table
            columns={[
              { key: 'name', header: 'Slot Name', className: 'font-semibold text-xs', render: (r) => r.name },
              { key: 'type', header: 'Type', render: (r) => periodTypeBadge(r.period_type) },
              { key: 'start', header: 'Start Time', render: (r) => <span className="text-xs font-mono">{r.start_time?.substring(0, 5)}</span> },
              { key: 'end', header: 'End Time', render: (r) => <span className="text-xs font-mono">{r.end_time?.substring(0, 5)}</span> },
              { key: 'order', header: 'Order', render: (r) => <span className="text-xs font-mono">{r.display_order}</span> },
              {
                key: 'actions', header: 'Actions',
                render: (r) => (
                  <div className="flex items-center gap-2">
                    {hasPerm('timetable.update') && <Button variant="secondary" onClick={() => openSlotModal(r)}>Edit</Button>}
                    {hasPerm('timetable.delete') && <Button variant="secondary" onClick={() => handleDeleteSlot(r.id)}>Delete</Button>}
                  </div>
                ),
              },
            ]}
            data={[...(periodSlotsData?.items || [])].sort((a, b) => a.display_order - b.display_order)}
            emptyText="No period slots configured for this school."
          />
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 3 — CLASSROOMS */}
      {/* ============================================================= */}
      {activeTab === 'rooms' && (
        <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">CLASSROOM_REGISTRY</p>
            {hasPerm('timetable.create') && (
              <Button onClick={() => openRoomModal(null)}>Add Classroom</Button>
            )}
          </div>

          {isRoomsError && (
            <Alert type="error" title="Failed to load classrooms">
              {(roomsError as any)?.message || 'An error occurred.'}
              <Button variant="secondary" onClick={() => refetchRooms()} className="ml-2">Retry</Button>
            </Alert>
          )}

          <Table
            columns={[
              { key: 'room_number', header: 'Room Number', className: 'font-semibold text-xs font-mono', render: (r) => r.room_number },
              { key: 'building', header: 'Building', render: (r) => <span className="text-xs">{r.building_name || '—'}</span> },
              { key: 'type', header: 'Room Type', render: (r) => <Badge variant="default">{r.room_type}</Badge> },
              { key: 'capacity', header: 'Capacity', render: (r) => <span className="text-xs font-mono">{r.capacity}</span> },
              {
                key: 'actions', header: 'Actions',
                render: (r) => (
                  <div className="flex items-center gap-2">
                    {hasPerm('timetable.update') && <Button variant="secondary" onClick={() => openRoomModal(r)}>Edit</Button>}
                    {hasPerm('timetable.delete') && <Button variant="secondary" onClick={() => handleDeleteRoom(r.id)}>Delete</Button>}
                  </div>
                ),
              },
            ]}
            data={classroomsData?.items || []}
            emptyText="No classrooms registered for this school."
          />
        </div>
      )}

      {/* ============================================================= */}
      {/* TAB 4 — TEACHER SUBSTITUTIONS */}
      {/* ============================================================= */}
      {activeTab === 'substitutions' && (
        <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">TEACHER_SUBSTITUTION_LOG</p>
            <div className="flex items-center gap-3">
              <Input type="date" value={subDateFilter} onChange={(e) => setSubDateFilter(e.target.value)} className="text-xs" />
              {hasPerm('substitution.create') && (
                <Button onClick={() => { setSubForm({ timetable_entry_id: '', substitution_date: subDateFilter || new Date().toISOString().split('T')[0], substitute_teacher_id: '', remarks: '' }); setIsSubModalOpen(true); }}>
                  Record Substitution
                </Button>
              )}
            </div>
          </div>

          {isSubsError && (
            <Alert type="error" title="Failed to load substitutions">
              {(subsError as any)?.message || 'An error occurred.'}
              <Button variant="secondary" onClick={() => refetchSubs()} className="ml-2">Retry</Button>
            </Alert>
          )}

          <Table
            columns={[
              { key: 'date', header: 'Date', render: (r: TeacherSubstitutionDetail) => <span className="text-xs font-mono">{r.substitution_date}</span> },
              { key: 'original', header: 'Original Teacher', render: (r: TeacherSubstitutionDetail) => <span className="text-xs">{r.original_teacher.first_name} {r.original_teacher.last_name}</span> },
              { key: 'substitute', header: 'Substitute Teacher', className: 'font-semibold text-xs', render: (r: TeacherSubstitutionDetail) => <span>{r.substitute_teacher.first_name} {r.substitute_teacher.last_name}</span> },
              { key: 'slot', header: 'Period / Slot', render: (r: TeacherSubstitutionDetail) => <span className="text-xs font-mono">{r.timetable_entry?.period_slot?.name} ({r.timetable_entry?.day_of_week?.substring(0, 3)})</span> },
              { key: 'subject', header: 'Subject', render: (r: TeacherSubstitutionDetail) => <span className="text-xs">{r.timetable_entry?.subject?.subject_code}</span> },
              { key: 'remarks', header: 'Remarks', render: (r: TeacherSubstitutionDetail) => <span className="text-xs text-slate-500">{r.remarks || '—'}</span> },
              {
                key: 'actions', header: 'Actions',
                render: (r: TeacherSubstitutionDetail) => (
                  <div className="flex items-center gap-2">
                    {hasPerm('substitution.delete') && <Button variant="secondary" onClick={() => handleDeleteSub(r.id)}>Delete</Button>}
                  </div>
                ),
              },
            ]}
            data={subsData?.items || []}
            emptyText="No substitution records found."
          />
        </div>
      )}

      {/* ============================================================= */}
      {/* MODALS */}
      {/* ============================================================= */}

      {/* Entry Creation Modal */}
      <Modal isOpen={isEntryModalOpen} onClose={() => setIsEntryModalOpen(false)} title="ADD TIMETABLE ENTRY">
        <form onSubmit={handleSaveEntry} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Day of Week</label>
            <select value={entryForm.day_of_week} onChange={(e) => setEntryForm({ ...entryForm, day_of_week: e.target.value as DayOfWeek })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              {ALL_DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Period Slot *</label>
            <select value={entryForm.period_slot_id} onChange={(e) => setEntryForm({ ...entryForm, period_slot_id: e.target.value })} required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="">Select Period Slot</option>
              {sortedSlots.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.start_time?.substring(0, 5)}–{s.end_time?.substring(0, 5)})</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Subject *</label>
            <select value={entryForm.subject_id} onChange={(e) => setEntryForm({ ...entryForm, subject_id: e.target.value })} required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="">Select Subject</option>
              {subjectsData?.items?.map((s) => <option key={s.id} value={s.id}>{s.subject_name} ({s.subject_code})</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Teacher *</label>
            <select value={entryForm.teacher_id} onChange={(e) => setEntryForm({ ...entryForm, teacher_id: e.target.value })} required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="">Select Teacher</option>
              {teachersData?.items?.map((t) => <option key={t.id} value={t.id}>{t.first_name} {t.last_name || ''} ({t.employee_id})</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Classroom (Optional)</label>
            <select value={entryForm.classroom_id || ''} onChange={(e) => setEntryForm({ ...entryForm, classroom_id: e.target.value || null })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="">No Classroom</option>
              {classroomsForEntry?.items?.map((c) => <option key={c.id} value={c.id}>{c.room_number} ({c.room_type})</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsEntryModalOpen(false)}>Cancel</Button>
            <Button type="submit">Add Entry</Button>
          </div>
        </form>
      </Modal>

      {/* Period Slot Modal */}
      <Modal isOpen={isSlotModalOpen} onClose={() => setIsSlotModalOpen(false)} title={editingSlot ? 'EDIT PERIOD SLOT' : 'CREATE PERIOD SLOT'}>
        <form onSubmit={handleSaveSlot} className="space-y-4 text-xs">
          <Input label="Slot Name *" value={slotForm.name || ''} onChange={(e) => setSlotForm({ ...slotForm, name: e.target.value })} required />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Type</label>
            <select value={slotForm.period_type} onChange={(e) => setSlotForm({ ...slotForm, period_type: e.target.value as PeriodType })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="REGULAR">Regular</option>
              <option value="BREAK">Break</option>
              <option value="LUNCH">Lunch</option>
              <option value="ASSEMBLY">Assembly</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input type="time" label="Start Time *" value={slotForm.start_time || ''} onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })} required />
            <Input type="time" label="End Time *" value={slotForm.end_time || ''} onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })} required />
          </div>
          <Input type="number" label="Display Order *" value={slotForm.display_order || ''} onChange={(e) => setSlotForm({ ...slotForm, display_order: Number(e.target.value) })} required />
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsSlotModalOpen(false)}>Cancel</Button>
            <Button type="submit">Save</Button>
          </div>
        </form>
      </Modal>

      {/* Classroom Modal */}
      <Modal isOpen={isRoomModalOpen} onClose={() => setIsRoomModalOpen(false)} title={editingRoom ? 'EDIT CLASSROOM' : 'ADD CLASSROOM'}>
        <form onSubmit={handleSaveRoom} className="space-y-4 text-xs">
          <Input label="Room Number *" value={roomForm.room_number || ''} onChange={(e) => setRoomForm({ ...roomForm, room_number: e.target.value })} required />
          <Input label="Building Name" value={roomForm.building_name || ''} onChange={(e) => setRoomForm({ ...roomForm, building_name: e.target.value })} />
          <Input type="number" label="Capacity" value={roomForm.capacity || ''} onChange={(e) => setRoomForm({ ...roomForm, capacity: Number(e.target.value) })} />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Room Type</label>
            <select value={roomForm.room_type} onChange={(e) => setRoomForm({ ...roomForm, room_type: e.target.value as RoomType })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="CLASSROOM">Classroom</option>
              <option value="LABORATORY">Laboratory</option>
              <option value="AUDITORIUM">Auditorium</option>
              <option value="SPORTS_GROUND">Sports Ground</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsRoomModalOpen(false)}>Cancel</Button>
            <Button type="submit">Save</Button>
          </div>
        </form>
      </Modal>

      {/* Substitution Modal */}
      <Modal isOpen={isSubModalOpen} onClose={() => setIsSubModalOpen(false)} title="RECORD TEACHER SUBSTITUTION">
        <form onSubmit={handleSaveSub} className="space-y-4 text-xs">
          <Input type="date" label="Substitution Date *" value={subForm.substitution_date || ''} onChange={(e) => setSubForm({ ...subForm, substitution_date: e.target.value })} required />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Timetable Entry ID *</label>
            <Input value={subForm.timetable_entry_id || ''} onChange={(e) => setSubForm({ ...subForm, timetable_entry_id: e.target.value })} required placeholder="Paste entry UUID" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Substitute Teacher *</label>
            <select value={subForm.substitute_teacher_id || ''} onChange={(e) => setSubForm({ ...subForm, substitute_teacher_id: e.target.value })} required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white">
              <option value="">Select Teacher</option>
              {teachersData?.items?.map((t) => <option key={t.id} value={t.id}>{t.first_name} {t.last_name || ''} ({t.employee_id})</option>)}
            </select>
          </div>
          <Input label="Remarks" value={subForm.remarks || ''} onChange={(e) => setSubForm({ ...subForm, remarks: e.target.value })} />
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsSubModalOpen(false)}>Cancel</Button>
            <Button type="submit">Record Substitution</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
