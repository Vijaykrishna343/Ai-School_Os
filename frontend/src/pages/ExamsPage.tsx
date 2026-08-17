import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { academicTermsApi } from '@/services/api/academicTermsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { subjectsApi } from '@/services/api/subjectsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { examsApi } from '@/services/api/examsApi';
import { examSchedulesApi } from '@/services/api/examSchedulesApi';
import { studentExamResultsApi } from '@/services/api/studentExamResultsApi';
import { reportCardsApi } from '@/services/api/reportCardsApi';
import { gradingScalesApi } from '@/services/api/gradingScalesApi';
import { evaluationConfigsApi } from '@/services/api/evaluationConfigsApi';
import {
  Exam,
  ExamCreate,
  ExamSchedule,
  ExamScheduleCreate,
  StudentExamResult,
  ReportCard,
  AssessmentType,
  AttemptType,
  ExamStatus,
} from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { ErrorState } from '@/components/ui/ErrorState';
import { Modal } from '@/components/ui/Modal';
import { Drawer } from '@/components/ui/Drawer';

export const ExamsPage: React.FC = () => {
  const { permissions, user } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'exams' | 'marks' | 'report-cards'>('exams');

  // Shared state selectors
  const [selectedYearId, setSelectedYearId] = useState('');
  const [selectedTermId, setSelectedTermId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState('');

  // ------------------------------------------------------------------
  // Tab 1: Exams & Schedules State
  // ------------------------------------------------------------------
  const [isExamModalOpen, setIsExamModalOpen] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [examForm, setExamForm] = useState<Partial<ExamCreate>>({
    name: '',
    assessment_type: 'OTHER',
    attempt_type: 'REGULAR',
    start_date: '',
    end_date: '',
    status: 'DRAFT',
  });

  const [selectedExamForSchedules, setSelectedExamForSchedules] = useState<Exam | null>(null);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [scheduleForm, setScheduleForm] = useState<Partial<ExamScheduleCreate>>({
    school_class_id: '',
    section_id: '',
    subject_id: '',
    exam_date: '',
    start_time: '',
    end_time: '',
    maximum_marks: 100,
    passing_marks: 33,
  });

  // ------------------------------------------------------------------
  // Tab 2: Marks Entry State
  // ------------------------------------------------------------------
  const [selectedExamId, setSelectedExamId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [localMarks, setLocalMarks] = useState<
    Record<string, { marks_obtained: string; remarks: string; result_id: string | null }>
  >({});
  const [isSavingMarks, setIsSavingMarks] = useState(false);
  const [marksError, setMarksError] = useState<string | null>(null);
  const [marksSuccess, setMarksSuccess] = useState<string | null>(null);

  // ------------------------------------------------------------------
  // Tab 3: Report Cards State
  // ------------------------------------------------------------------
  const [isRemarksDrawerOpen, setIsRemarksDrawerOpen] = useState(false);
  const [selectedCardForRemarks, setSelectedCardForRemarks] = useState<ReportCard | null>(null);
  const [remarksForm, setRemarksForm] = useState({
    teacher_remarks: '',
    principal_remarks: '',
  });
  const [reportCardMessage, setReportCardMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [isGeneratingCards, setIsGeneratingCards] = useState(false);

  // ------------------------------------------------------------------
  // Queries
  // ------------------------------------------------------------------
  const { data: yearsData } = useQuery({
    queryKey: ['academicYearsExams'],
    queryFn: () => academicYearsApi.getAcademicYears({ page: 1, page_size: 100 }),
    enabled: permissions.includes('exam.view') || permissions.includes('report_card.view'),
  });

  const { data: termsData } = useQuery({
    queryKey: ['academicTermsExams', selectedYearId],
    queryFn: () => academicTermsApi.getAcademicTerms({ page: 1, page_size: 100 }),
    enabled: !!selectedYearId,
  });

  const { data: classesData } = useQuery({
    queryKey: ['schoolClassesExams'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: 1, page_size: 100 }),
    enabled: permissions.includes('exam.view') || permissions.includes('report_card.view'),
  });

  const { data: sectionsData } = useQuery({
    queryKey: ['sectionsExams', selectedClassId],
    queryFn: () => sectionsApi.getSectionsByClass(selectedClassId, { page: 1, page_size: 100 }),
    enabled: !!selectedClassId,
  });

  const { data: subjectsData } = useQuery({
    queryKey: ['subjectsExams'],
    queryFn: () => subjectsApi.getSubjects({ page: 1, page_size: 100 }),
    enabled: activeTab === 'marks',
  });

  // Exams list
  const { data: examsData, refetch: refetchExams } = useQuery({
    queryKey: ['examsList', selectedYearId],
    queryFn: () =>
      examsApi.getExams({
        academic_year_id: selectedYearId || undefined,
        page_size: 100,
      }),
    enabled: permissions.includes('exam.view') && !!selectedYearId,
  });

  // Selected Exam Schedules
  const { data: schedulesData, refetch: refetchSchedules } = useQuery({
    queryKey: ['examSchedulesList', selectedExamForSchedules?.id],
    queryFn: () =>
      examSchedulesApi.getExamSchedules({
        exam_id: selectedExamForSchedules?.id,
        page_size: 100,
      }),
    enabled: permissions.includes('exam.view') && !!selectedExamForSchedules?.id,
  });

  // Tab 2: Marks entry - active schedule query
  const { data: activeScheduleData } = useQuery({
    queryKey: ['activeExamSchedule', selectedExamId, selectedSectionId, selectedSubjectId],
    queryFn: () =>
      examSchedulesApi.getExamSchedules({
        exam_id: selectedExamId || undefined,
        section_id: selectedSectionId || undefined,
        subject_id: selectedSubjectId || undefined,
        page_size: 100,
      }),
    enabled: !!selectedExamId && !!selectedSectionId && !!selectedSubjectId,
  });

  const activeSchedule = activeScheduleData?.items?.[0] || null;

  // Tab 2: Students Query
  const { data: studentsData } = useQuery({
    queryKey: ['marksStudentsList', selectedSectionId],
    queryFn: () =>
      studentsApi.getStudents({
        section_id: selectedSectionId,
        status: 'ACTIVE',
        page_size: 100,
      }),
    enabled: !!selectedSectionId && !!activeSchedule,
  });

  // Tab 2: Marks Query
  const { data: marksData } = useQuery({
    queryKey: ['marksList', activeSchedule?.id],
    queryFn: () =>
      studentExamResultsApi.getStudentExamResults({
        exam_schedule_id: activeSchedule?.id,
        page_size: 100,
      }),
    enabled: !!activeSchedule?.id,
  });

  // Tab 3: Report Cards Query
  const { data: reportCardsData, refetch: refetchReportCards } = useQuery({
    queryKey: ['reportCardsList', selectedYearId, selectedTermId, selectedSectionId],
    queryFn: () =>
      reportCardsApi.getReportCards({
        academic_year_id: selectedYearId || undefined,
        academic_term_id: selectedTermId || undefined,
        section_id: selectedSectionId || undefined,
        page_size: 100,
      }),
    enabled: permissions.includes('report_card.view') && !!selectedYearId && !!selectedSectionId,
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

  // Tab 2: Merge marks query with local entry map
  useEffect(() => {
    if (!studentsData?.items) {
      setLocalMarks({});
      return;
    }

    const marksMap: Record<
      string,
      { marks_obtained: string; remarks: string; result_id: string | null }
    > = {};
    const resultsMap = new Map<string, StudentExamResult>();

    if (marksData?.items) {
      marksData.items.forEach((item) => {
        resultsMap.set(item.student_id, item);
      });
    }

    studentsData.items.forEach((student) => {
      const existing = resultsMap.get(student.id);
      if (existing) {
        marksMap[student.id] = {
          marks_obtained: String(existing.marks_obtained),
          remarks: existing.remarks || '',
          result_id: existing.id,
        };
      } else {
        marksMap[student.id] = {
          marks_obtained: '',
          remarks: '',
          result_id: null,
        };
      }
    });

    setLocalMarks(marksMap);
  }, [studentsData, marksData]);

  // ------------------------------------------------------------------
  // Mutations
  // ------------------------------------------------------------------
  const createExamMutation = useMutation({
    mutationFn: (data: ExamCreate) => examsApi.createExam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examsList'] });
      setIsExamModalOpen(false);
    },
  });

  const updateExamMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ExamCreate> }) =>
      examsApi.updateExam(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examsList'] });
      setIsExamModalOpen(false);
    },
  });

  const deleteExamMutation = useMutation({
    mutationFn: (id: string) => examsApi.deleteExam(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examsList'] });
    },
  });

  const createScheduleMutation = useMutation({
    mutationFn: (data: ExamScheduleCreate) => examSchedulesApi.createExamSchedule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examSchedulesList'] });
      setIsScheduleModalOpen(false);
    },
  });

  const deleteScheduleMutation = useMutation({
    mutationFn: (id: string) => examSchedulesApi.deleteExamSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examSchedulesList'] });
    },
  });

  // ------------------------------------------------------------------
  // Handlers
  // ------------------------------------------------------------------
  const handleOpenExamModal = (exam: Exam | null = null) => {
    if (exam) {
      setEditingExam(exam);
      setExamForm({
        name: exam.name,
        assessment_type: exam.assessment_type,
        attempt_type: exam.attempt_type,
        start_date: exam.start_date,
        end_date: exam.end_date,
        status: exam.status,
      });
    } else {
      setEditingExam(null);
      setExamForm({
        name: '',
        assessment_type: 'OTHER',
        attempt_type: 'REGULAR',
        start_date: '',
        end_date: '',
        status: 'DRAFT',
      });
    }
    setIsExamModalOpen(true);
  };

  const handleSaveExam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedYearId) return;

    const payload: ExamCreate = {
      academic_year_id: selectedYearId,
      school_id: user?.school_id || '',
      name: examForm.name || '',
      assessment_type: examForm.assessment_type || 'OTHER',
      attempt_type: examForm.attempt_type || 'REGULAR',
      start_date: examForm.start_date || '',
      end_date: examForm.end_date || '',
      status: examForm.status || 'DRAFT',
    };

    if (editingExam) {
      updateExamMutation.mutate({ id: editingExam.id, data: payload });
    } else {
      createExamMutation.mutate(payload);
    }
  };

  const handleOpenScheduleModal = () => {
    setScheduleForm({
      school_class_id: '',
      section_id: '',
      subject_id: '',
      exam_date: '',
      start_time: '',
      end_time: '',
      maximum_marks: 100,
      passing_marks: 33,
    });
    setIsScheduleModalOpen(true);
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExamForSchedules || !selectedYearId) return;

    // Append seconds to times to comply with backend Time format
    const formatTime = (t: string) => (t.length === 5 ? `${t}:00` : t);

    const payload: ExamScheduleCreate = {
      exam_id: selectedExamForSchedules.id,
      school_id: user?.school_id || '',
      academic_year_id: selectedYearId,
      school_class_id: scheduleForm.school_class_id || '',
      section_id: scheduleForm.section_id || '',
      subject_id: scheduleForm.subject_id || '',
      exam_date: scheduleForm.exam_date || '',
      start_time: formatTime(scheduleForm.start_time || ''),
      end_time: formatTime(scheduleForm.end_time || ''),
      maximum_marks: Number(scheduleForm.maximum_marks),
      passing_marks: Number(scheduleForm.passing_marks),
    };

    try {
      await examSchedulesApi.createExamSchedule(payload);
      queryClient.invalidateQueries({ queryKey: ['examSchedulesList'] });
      setIsScheduleModalOpen(false);
    } catch (err: any) {
      alert(err.message || 'Failed to create schedule.');
    }
  };

  // Tab 2: Marks entry handlers
  const handleMarkChange = (studentId: string, value: string) => {
    setLocalMarks((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        marks_obtained: value,
      },
    }));
  };

  const handleRemarkChange = (studentId: string, value: string) => {
    setLocalMarks((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        remarks: value,
      },
    }));
  };

  const handleSaveMarks = async () => {
    if (!activeSchedule || !studentsData?.items) return;
    setMarksError(null);
    setMarksSuccess(null);
    setIsSavingMarks(true);

    try {
      const promises: Promise<any>[] = [];
      let hasValidationError = false;

      studentsData.items.forEach((student) => {
        const local = localMarks[student.id];
        if (!local || local.marks_obtained === '') return;

        const score = Number(local.marks_obtained);
        if (score < 0 || score > Number(activeSchedule.maximum_marks)) {
          hasValidationError = true;
          return;
        }

        if (local.result_id === null) {
          promises.push(
            studentExamResultsApi.createStudentExamResult({
              exam_schedule_id: activeSchedule.id,
              student_id: student.id,
              marks_obtained: score,
              remarks: local.remarks || undefined,
            })
          );
        } else {
          // Compare with database record to avoid redundant PUTs
          const dbItem = marksData?.items?.find((r) => r.student_id === student.id);
          if (dbItem) {
            const hasChanged =
              score !== Number(dbItem.marks_obtained) || local.remarks !== (dbItem.remarks || '');
            if (hasChanged) {
              promises.push(
                studentExamResultsApi.updateStudentExamResult(local.result_id, {
                  marks_obtained: score,
                  remarks: local.remarks || null,
                })
              );
            }
          }
        }
      });

      if (hasValidationError) {
        throw new Error(`Marks must be between 0 and maximum marks (${activeSchedule.maximum_marks}).`);
      }

      if (promises.length > 0) {
        await Promise.all(promises);
      }

      setMarksSuccess('Marks updated successfully.');
      queryClient.invalidateQueries({ queryKey: ['marksList', activeSchedule.id] });
    } catch (err: any) {
      setMarksError(err.message || 'Failed to save marks.');
    } finally {
      setIsSavingMarks(false);
    }
  };

  // Tab 3: Report Cards Handlers
  const handleBulkGenerateCards = async () => {
    if (!selectedYearId || !selectedSectionId) return;
    setReportCardMessage(null);
    setIsGeneratingCards(true);

    try {
      await reportCardsApi.generateReportCards({
        school_id: user?.school_id || '',
        academic_year_id: selectedYearId,
        academic_term_id: selectedTermId || undefined,
        section_id: selectedSectionId || undefined,
      });
      setReportCardMessage({
        type: 'success',
        text: 'Report cards generated/recalculated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['reportCardsList'] });
    } catch (err: any) {
      setReportCardMessage({
        type: 'error',
        text: err.message || 'Failed to generate report cards.',
      });
    } finally {
      setIsGeneratingCards(false);
    }
  };

  const handleOpenRemarksDrawer = (card: ReportCard) => {
    setSelectedCardForRemarks(card);
    setRemarksForm({
      teacher_remarks: card.teacher_remarks || '',
      principal_remarks: card.principal_remarks || '',
    });
    setIsRemarksDrawerOpen(true);
  };

  const handleSaveRemarks = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCardForRemarks) return;

    try {
      await reportCardsApi.updateRemarks(selectedCardForRemarks.id, remarksForm);
      queryClient.invalidateQueries({ queryKey: ['reportCardsList'] });
      setIsRemarksDrawerOpen(false);
    } catch (err: any) {
      alert(err.message || 'Failed to save remarks.');
    }
  };

  const handleFinalizeCard = async (id: string) => {
    try {
      await reportCardsApi.finalizeReportCard(id);
      queryClient.invalidateQueries({ queryKey: ['reportCardsList'] });
    } catch (err: any) {
      alert(err.message || 'Failed to finalize report card.');
    }
  };

  const handlePublishCard = async (id: string) => {
    try {
      await reportCardsApi.publishReportCard(id);
      queryClient.invalidateQueries({ queryKey: ['reportCardsList'] });
    } catch (err: any) {
      alert(err.message || 'Failed to publish report card.');
    }
  };

  const handleClassChangeForSchedules = (classId: string) => {
    setScheduleForm((prev) => ({
      ...prev,
      school_class_id: classId,
      section_id: '',
    }));
  };

  // RBAC Gating checks
  const canManageExams = permissions.includes('exam.create') || permissions.includes('exam.update');
  const canManageMarks = permissions.includes('marks.create') || permissions.includes('marks.update');
  const canManageReports =
    permissions.includes('report_card.generate') ||
    permissions.includes('report_card.finalize') ||
    permissions.includes('report_card.publish');

  // Exam statuses badges
  const getStatusBadge = (status: ExamStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="success">COMPLETED</Badge>;
      case 'ONGOING':
        return <Badge variant="warning">ONGOING</Badge>;
      case 'SCHEDULED':
        return <Badge variant="default">SCHEDULED</Badge>;
      case 'CANCELLED':
        return <Badge variant="error">CANCELLED</Badge>;
      default:
        return <Badge variant="default">DRAFT</Badge>;
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            ASSESSMENT & RECORD SERVICES
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Examinations & Reports
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage school exam cycles, schedule subjects, input student scores, and finalize term report cards.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('exams')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'exams'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Assessment Schedules
        </button>
        <button
          onClick={() => setActiveTab('marks')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'marks'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Marks Entry Workspace
        </button>
        <button
          onClick={() => setActiveTab('report-cards')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'report-cards'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Report Cards
        </button>
      </div>

      {/* Shared Year Select */}
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

          {activeTab === 'report-cards' && (
            <div>
              <label
                htmlFor="term-select"
                className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
              >
                Academic Term (Optional)
              </label>
              <select
                id="term-select"
                value={selectedTermId}
                onChange={(e) => setSelectedTermId(e.target.value)}
                disabled={!selectedYearId}
                className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white disabled:opacity-40"
              >
                <option value="">Full Year</option>
                {termsData?.items
                  ?.filter((t) => t.academic_year_id === selectedYearId)
                  ?.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
              </select>
            </div>
          )}

          {activeTab !== 'exams' && (
            <>
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
                  onChange={(e) => {
                    setSelectedClassId(e.target.value);
                    setSelectedSectionId('');
                  }}
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
            </>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------
          TAB 1: Exams & Schedules Layout
          ------------------------------------------------------------------ */}
      {activeTab === 'exams' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Exams List */}
          <div className="lg:col-span-2 space-y-4 border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
                ACTIVE_EXAM_CYCLES
              </p>
              {canManageExams && (
                <Button onClick={() => handleOpenExamModal(null)}>Add Exam Cycle</Button>
              )}
            </div>

            <Table
              columns={[
                {
                  key: 'name',
                  header: 'Exam Name',
                  className: 'font-semibold',
                  render: (row) => row.name,
                },
                {
                  key: 'assessment_type',
                  header: 'Type',
                  render: (row) => (
                    <span className="text-[10px] font-mono">{row.assessment_type}</span>
                  ),
                },
                {
                  key: 'dates',
                  header: 'Duration',
                  render: (row) => (
                    <span className="text-xs font-mono">
                      {row.start_date} to {row.end_date}
                    </span>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (row) => getStatusBadge(row.status),
                },
                {
                  key: 'actions',
                  header: 'Actions',
                  render: (row) => (
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => setSelectedExamForSchedules(row)}
                      >
                        Schedules
                      </Button>
                      {canManageExams && (
                        <>
                          <Button variant="secondary" onClick={() => handleOpenExamModal(row)}>
                            Edit
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={() => deleteExamMutation.mutate(row.id)}
                          >
                            Delete
                          </Button>
                        </>
                      )}
                    </div>
                  ),
                },
              ]}
              data={examsData?.items || []}
              emptyText="No exams created for the selected academic year."
            />
          </div>

          {/* Schedules list for selected exam */}
          <div className="space-y-4 border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
                SCHEDULES: {selectedExamForSchedules?.name || 'SELECT EXAM'}
              </p>
              {selectedExamForSchedules && canManageExams && (
                <Button onClick={handleOpenScheduleModal}>Schedule Subject</Button>
              )}
            </div>

            {!selectedExamForSchedules ? (
              <div className="p-8 text-center">
                <p className="text-xs font-mono text-slate-400">
                  SELECT AN EXAM CYCLE TO MANAGE SUBJECT SCHEDULES.
                </p>
              </div>
            ) : (
              <Table
                columns={[
                  {
                    key: 'subject',
                    header: 'Subject / Class',
                    render: (row) => (
                      <div>
                        <p className="font-semibold text-xs">{row.subject?.subject_name || 'Subject'}</p>
                        <p className="text-[9px] font-mono text-slate-400">
                          {row.school_class?.name} - {row.section?.name}
                        </p>
                      </div>
                    ),
                  },
                  {
                    key: 'schedule',
                    header: 'Date & Time',
                    render: (row) => (
                      <div>
                        <p className="text-xs font-mono">{row.exam_date}</p>
                        <p className="text-[9px] font-mono text-slate-400">
                          {row.start_time.substring(0, 5)} - {row.end_time.substring(0, 5)}
                        </p>
                      </div>
                    ),
                  },
                  {
                    key: 'marks',
                    header: 'Marks',
                    render: (row) => (
                      <span className="text-xs font-mono">
                        {row.passing_marks}/{row.maximum_marks}
                      </span>
                    ),
                  },
                  {
                    key: 'actions',
                    header: '',
                    render: (row) =>
                      canManageExams ? (
                        <Button
                          variant="secondary"
                          onClick={() => deleteScheduleMutation.mutate(row.id)}
                        >
                          Cancel
                        </Button>
                      ) : null,
                  },
                ]}
                data={schedulesData?.items || []}
                emptyText="No subjects scheduled for this exam."
              />
            )}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------
          TAB 2: Marks Entry Workspace Layout
          ------------------------------------------------------------------ */}
      {activeTab === 'marks' && (
        <div className="space-y-6">
          {/* Select Roster Filters */}
          <div className="flex flex-col md:flex-row items-center gap-4 bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full">
              <div>
                <label
                  htmlFor="exam-select"
                  className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
                >
                  Exam Cycle
                </label>
                <select
                  id="exam-select"
                  value={selectedExamId}
                  onChange={(e) => setSelectedExamId(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
                >
                  <option value="">Select Exam</option>
                  {examsData?.items?.map((exam) => (
                    <option key={exam.id} value={exam.id}>
                      {exam.name} ({exam.status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="subject-select"
                  className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
                >
                  Subject
                </label>
                <select
                  id="subject-select"
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
                >
                  <option value="">Select Subject</option>
                  {subjectsData?.items?.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.subject_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Validation Alerts */}
          {marksError && (
            <Alert type="error" title="Input Error">
              {marksError}
            </Alert>
          )}
          {marksSuccess && <Alert type="success">{marksSuccess}</Alert>}

          {/* Students Marks Grid */}
          {!selectedExamId || !selectedClassId || !selectedSectionId || !selectedSubjectId ? (
            <div className="p-8 border border-slate-200 dark:border-slate-800 bg-white text-center">
              <p className="text-xs text-slate-500 font-mono">
                SELECT EXAM, CLASS, SECTION, AND SUBJECT TO LOAD MARKS ENTRY LEDGER.
              </p>
            </div>
          ) : !activeSchedule ? (
            <div className="p-8 border border-slate-200 dark:border-slate-800 bg-white text-center">
              <p className="text-xs text-red-500 font-mono">
                NO EXAM SCHEDULE FOUND FOR THE SELECTED CONTEXT. PLEASE CONFIGURE EXAM SCHEDULE FIRST.
              </p>
            </div>
          ) : (
            <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-2">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
                    MARKS_ENTRY_GRID
                  </p>
                  <p className="text-[10px] font-mono text-slate-400 mt-1">
                    MAXIMUM MARKS: {activeSchedule.maximum_marks} | PASSING MARKS:{' '}
                    {activeSchedule.passing_marks}
                  </p>
                </div>
                <Button onClick={handleSaveMarks} disabled={isSavingMarks || !canManageMarks}>
                  {isSavingMarks ? 'Saving...' : 'Save Marks'}
                </Button>
              </div>

              <Table
                columns={[
                  {
                    key: 'admission_number',
                    header: 'Admission No',
                    className: 'w-36 font-mono text-xs font-bold text-brand-500 dark:text-brand-350',
                    render: (row) => row.admission_number,
                  },
                  {
                    key: 'full_name',
                    header: 'Student Name',
                    className: 'font-semibold',
                    render: (row) => `${row.first_name} ${row.last_name || ''}`.trim(),
                  },
                  {
                    key: 'marks',
                    header: 'Marks Obtained',
                    className: 'w-48',
                    render: (row) => {
                      const local = localMarks[row.id];
                      return (
                        <Input
                          type="number"
                          value={local?.marks_obtained || ''}
                          onChange={(e) => handleMarkChange(row.id, e.target.value)}
                          placeholder="e.g. 85"
                          disabled={!canManageMarks}
                          className="text-xs py-0.5"
                        />
                      );
                    },
                  },
                  {
                    key: 'remarks',
                    header: 'Remarks',
                    render: (row) => {
                      const local = localMarks[row.id];
                      return (
                        <Input
                          value={local?.remarks || ''}
                          onChange={(e) => handleRemarkChange(row.id, e.target.value)}
                          placeholder="e.g. Absent, late entry"
                          disabled={!canManageMarks}
                          className="text-xs py-0.5"
                        />
                      );
                    },
                  },
                ]}
                data={studentsData?.items || []}
                emptyText="No active students found in this section."
              />
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------
          TAB 3: Report Cards Layout
          ------------------------------------------------------------------ */}
      {activeTab === 'report-cards' && (
        <div className="space-y-6">
          {/* Action Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
              REPORT_CARDS_SERVICE
            </p>
            {selectedSectionId && (
              <Button
                onClick={handleBulkGenerateCards}
                disabled={isGeneratingCards || !canManageReports}
              >
                {isGeneratingCards ? 'Generating...' : 'Bulk Generate / Recalculate Cards'}
              </Button>
            )}
          </div>

          {reportCardMessage && (
            <Alert type={reportCardMessage.type} title="Card Service">
              {reportCardMessage.text}
            </Alert>
          )}

          {/* Cards Grid list */}
          {!selectedYearId || !selectedClassId || !selectedSectionId ? (
            <div className="p-8 border border-slate-200 dark:border-slate-800 bg-white text-center">
              <p className="text-xs text-slate-500 font-mono">
                SELECT YEAR, CLASS, AND SECTION TO MOUNT REPORT CARDS.
              </p>
            </div>
          ) : (
            <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none space-y-4">
              <Table
                columns={[
                  {
                    key: 'student',
                    header: 'Student',
                    className: 'font-semibold',
                    render: (row) => row.student ? `${row.student.first_name} ${row.student.last_name || ''}`.trim() : 'Student',
                  },
                  {
                    key: 'marks',
                    header: 'Total Marks',
                    render: (row) => (
                      <span className="text-xs font-mono">
                        {row.total_obtained_marks}/{row.total_max_marks}
                      </span>
                    ),
                  },
                  {
                    key: 'percentage',
                    header: 'Percentage',
                    render: (row) => (
                      <span className="text-xs font-mono">{row.percentage}%</span>
                    ),
                  },
                  {
                    key: 'gpa',
                    header: 'Grade / GPA',
                    render: (row) => (
                      <span className="text-xs font-mono">
                        {row.overall_grade} {row.gpa !== null ? `(GPA: ${row.gpa})` : ''}
                      </span>
                    ),
                  },
                  {
                    key: 'result',
                    header: 'Pass/Fail',
                    render: (row) => (
                      <Badge variant={row.is_passed ? 'success' : 'error'}>
                        {row.is_passed ? 'PASSED' : 'FAILED'}
                      </Badge>
                    ),
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    render: (row) => (
                      <Badge
                        variant={
                          row.status === 'PUBLISHED'
                            ? 'success'
                            : row.status === 'FINALIZED'
                            ? 'warning'
                            : 'default'
                        }
                      >
                        {row.status}
                      </Badge>
                    ),
                  },
                  {
                    key: 'actions',
                    header: 'Actions',
                    render: (row) => (
                      <div className="flex items-center gap-2">
                        <Button variant="secondary" onClick={() => handleOpenRemarksDrawer(row)}>
                          Remarks
                        </Button>
                        {row.status === 'DRAFT' && permissions.includes('report_card.finalize') && (
                          <Button variant="secondary" onClick={() => handleFinalizeCard(row.id)}>
                            Finalize
                          </Button>
                        )}
                        {row.status === 'FINALIZED' && permissions.includes('report_card.publish') && (
                          <Button variant="secondary" onClick={() => handlePublishCard(row.id)}>
                            Publish
                          </Button>
                        )}
                      </div>
                    ),
                  },
                ]}
                data={reportCardsData?.items || []}
                emptyText="No report cards generated. Click the button above to generate cards for this section."
              />
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------
          Exam Cycle Form Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isExamModalOpen}
        onClose={() => setIsExamModalOpen(false)}
        title={editingExam ? 'EDIT EXAM CYCLE' : 'NEW EXAM CYCLE'}
      >
        <form onSubmit={handleSaveExam} className="space-y-4">
          <Input
            label="Exam Name *"
            value={examForm.name || ''}
            onChange={(e) => setExamForm({ ...examForm, name: e.target.value })}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Assessment Type *
              </label>
              <select
                value={examForm.assessment_type}
                onChange={(e) =>
                  setExamForm({ ...examForm, assessment_type: e.target.value as AssessmentType })
                }
                className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
              >
                <option value="FORMATIVE_ASSESSMENT">Formative Assessment</option>
                <option value="SUMMATIVE_ASSESSMENT">Summative Assessment</option>
                <option value="UNIT_TEST">Unit Test</option>
                <option value="PERIODIC_TEST">Periodic Test</option>
                <option value="QUARTERLY">Quarterly</option>
                <option value="HALF_YEARLY">Half Yearly</option>
                <option value="TERM">Term</option>
                <option value="FINAL">Final</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Attempt Type *</label>
              <select
                value={examForm.attempt_type}
                onChange={(e) =>
                  setExamForm({ ...examForm, attempt_type: e.target.value as AttemptType })
                }
                className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
              >
                <option value="REGULAR">Regular</option>
                <option value="RETEST">Retest</option>
                <option value="MAKEUP">Makeup</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              type="date"
              label="Start Date *"
              value={examForm.start_date || ''}
              onChange={(e) => setExamForm({ ...examForm, start_date: e.target.value })}
              required
            />
            <Input
              type="date"
              label="End Date *"
              value={examForm.end_date || ''}
              onChange={(e) => setExamForm({ ...examForm, end_date: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Status *</label>
            <select
              value={examForm.status}
              onChange={(e) => setExamForm({ ...examForm, status: e.target.value as ExamStatus })}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
            >
              <option value="DRAFT">Draft</option>
              <option value="SCHEDULED">Scheduled</option>
              <option value="ONGOING">Ongoing</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsExamModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Exam Cycle</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Exam Schedule Form Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        title="SCHEDULE EXAM SUBJECT"
      >
        <form onSubmit={handleCreateSchedule} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Class *</label>
              <select
                value={scheduleForm.school_class_id}
                onChange={(e) => handleClassChangeForSchedules(e.target.value)}
                required
                className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
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
              <label className="block text-xs font-medium text-slate-700 mb-1">Section *</label>
              <select
                value={scheduleForm.section_id}
                onChange={(e) => setScheduleForm({ ...scheduleForm, section_id: e.target.value })}
                disabled={!scheduleForm.school_class_id}
                required
                className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white disabled:opacity-40"
              >
                <option value="">Select Section</option>
                {sectionsData?.items?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Subject *</label>
            <select
              value={scheduleForm.subject_id}
              onChange={(e) => setScheduleForm({ ...scheduleForm, subject_id: e.target.value })}
              required
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
            >
              <option value="">Select Subject</option>
              {subjectsData?.items?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.subject_name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <Input
              type="date"
              label="Date *"
              value={scheduleForm.exam_date || ''}
              onChange={(e) => setScheduleForm({ ...scheduleForm, exam_date: e.target.value })}
              required
            />
            <Input
              type="time"
              label="Start Time *"
              value={scheduleForm.start_time || ''}
              onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })}
              required
            />
            <Input
              type="time"
              label="End Time *"
              value={scheduleForm.end_time || ''}
              onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              type="number"
              label="Max Marks *"
              value={scheduleForm.maximum_marks || 100}
              onChange={(e) => setScheduleForm({ ...scheduleForm, maximum_marks: Number(e.target.value) })}
              required
            />
            <Input
              type="number"
              label="Passing Marks *"
              value={scheduleForm.passing_marks || 33}
              onChange={(e) => setScheduleForm({ ...scheduleForm, passing_marks: Number(e.target.value) })}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsScheduleModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Schedule Subject</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Report Card Remarks Drawer
          ------------------------------------------------------------------ */}
      <Drawer
        isOpen={isRemarksDrawerOpen}
        onClose={() => setIsRemarksDrawerOpen(false)}
        title="REPORT CARD REMARKS"
        subtitle={selectedCardForRemarks?.student ? `${selectedCardForRemarks.student.first_name} ${selectedCardForRemarks.student.last_name || ''}`.trim() : ''}
      >
        <form onSubmit={handleSaveRemarks} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Teacher Remarks</label>
            <textarea
              value={remarksForm.teacher_remarks}
              onChange={(e) => setRemarksForm({ ...remarksForm, teacher_remarks: e.target.value })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
              rows={4}
              placeholder="Input student performance evaluation remarks..."
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Principal Remarks</label>
            <textarea
              value={remarksForm.principal_remarks}
              onChange={(e) => setRemarksForm({ ...remarksForm, principal_remarks: e.target.value })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
              rows={4}
              placeholder="Input administrative remarks..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsRemarksDrawerOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Remarks</Button>
          </div>
        </form>
      </Drawer>
    </div>
  );
};
