import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  homeworkApi,
  schoolClassesApi,
  subjectsApi,
  parentsApi,
  HomeworkItem,
  HomeworkSubmissionItem,
} from '@/services/api';
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
import { BookOpen, CheckCircle, Clock, FileText, Send, User } from 'lucide-react';

export const HomeworkPage: React.FC = () => {
  const { user, roles } = useAuthStore();
  const queryClient = useQueryClient();

  const userRole = roles[0]?.name || 'Teacher';
  const isStudent = userRole === 'Student';
  const isParent = userRole === 'Parent';
  const isTeacherOrAdmin = !isStudent && !isParent;

  // Pagination & Filter States
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [selectedClassFilter, setSelectedClassFilter] = useState('');
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('');

  // Student specific filter tab
  const [studentTab, setStudentTab] = useState<'all' | 'pending' | 'submitted' | 'graded'>('all');

  // Parent specific child selection
  const [selectedChildId, setSelectedChildId] = useState('');

  // Modals & Drawers
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingHomework, setEditingHomework] = useState<HomeworkItem | null>(null);
  const [viewingHomework, setViewingHomework] = useState<HomeworkItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<HomeworkItem | null>(null);

  // Submissions Drawer (Teacher view)
  const [selectedHomeworkForSubmissions, setSelectedHomeworkForSubmissions] = useState<HomeworkItem | null>(null);

  // Student Submission Modal
  const [submittingHomework, setSubmittingHomework] = useState<HomeworkItem | null>(null);
  const [responseText, setResponseText] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Grading Form State
  const [gradingSubmission, setGradingSubmission] = useState<HomeworkSubmissionItem | null>(null);
  const [gradeValue, setGradeValue] = useState('A');
  const [feedbackValue, setFeedbackValue] = useState('Good work!');

  // Form State for Homework Creation
  const [homeworkForm, setHomeworkForm] = useState({
    school_class_id: '',
    section_id: '',
    subject_id: '',
    title: '',
    description: '',
    due_date: new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0],
  });
  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const { data: classesData } = useQuery({
    queryKey: ['schoolClasses'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page_size: 100 }),
  });

  const { data: subjectsData } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => subjectsApi.getSubjects({ page_size: 100 }),
  });

  const { data: parentsData } = useQuery({
    queryKey: ['parentChildren'],
    queryFn: () => parentsApi.getParents({ page_size: 100 }),
    enabled: isParent,
  });

  const { data: summaryData } = useQuery({
    queryKey: ['homeworkSummary'],
    queryFn: () => homeworkApi.getSummary(),
    enabled: isTeacherOrAdmin,
  });

  const {
    data: homeworkData,
    isLoading: isHomeworkLoading,
    isError: isHomeworkError,
    error: homeworkError,
    refetch: refetchHomework,
  } = useQuery({
    queryKey: [
      'homework',
      page,
      pageSize,
      selectedClassFilter,
      selectedSubjectFilter,
      selectedStatusFilter,
      selectedChildId,
      userRole,
    ],
    queryFn: () =>
      homeworkApi.list({
        page,
        page_size: pageSize,
        school_class_id: selectedClassFilter || undefined,
        subject_id: selectedSubjectFilter || undefined,
        status: selectedStatusFilter || undefined,
        student_id: isParent && selectedChildId ? selectedChildId : undefined,
      }),
  });

  const { data: submissionsData, isLoading: isSubmissionsLoading } = useQuery({
    queryKey: ['homeworkSubmissions', selectedHomeworkForSubmissions?.id],
    queryFn: () =>
      selectedHomeworkForSubmissions
        ? homeworkApi.listSubmissions(selectedHomeworkForSubmissions.id)
        : Promise.resolve({ items: [], total: 0, page: 1, page_size: 20, total_pages: 1 }),
    enabled: !!selectedHomeworkForSubmissions,
  });

  // Mutations
  const createHomeworkMutation = useMutation({
    mutationFn: (payload: any) => homeworkApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      queryClient.invalidateQueries({ queryKey: ['homeworkSummary'] });
      setIsCreateModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create homework assignment.'),
  });

  const updateHomeworkMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => homeworkApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      queryClient.invalidateQueries({ queryKey: ['homeworkSummary'] });
      setIsCreateModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update homework.'),
  });

  const publishHomeworkMutation = useMutation({
    mutationFn: (id: string) => homeworkApi.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      queryClient.invalidateQueries({ queryKey: ['homeworkSummary'] });
    },
  });

  const closeHomeworkMutation = useMutation({
    mutationFn: (id: string) => homeworkApi.close(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      queryClient.invalidateQueries({ queryKey: ['homeworkSummary'] });
    },
  });

  const deleteHomeworkMutation = useMutation({
    mutationFn: (id: string) => homeworkApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      queryClient.invalidateQueries({ queryKey: ['homeworkSummary'] });
      setDeleteTarget(null);
    },
  });

  const submitWorkMutation = useMutation({
    mutationFn: ({ homeworkId, text }: { homeworkId: string; text: string }) =>
      homeworkApi.submitWork(homeworkId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      setSubmittingHomework(null);
      setSubmitError(null);
    },
    onError: (err: any) => setSubmitError(err.message || 'Failed to submit response.'),
  });

  const gradeSubmissionMutation = useMutation({
    mutationFn: ({ submissionId, grade, feedback }: { submissionId: string; grade: string; feedback?: string }) =>
      homeworkApi.gradeSubmission(submissionId, { grade, feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homeworkSubmissions'] });
      setGradingSubmission(null);
    },
  });

  const handleOpenCreateModal = () => {
    setFormError(null);
    setEditingHomework(null);
    setHomeworkForm({
      school_class_id: classesData?.items[0]?.id || '',
      section_id: '',
      subject_id: subjectsData?.items[0]?.id || '',
      title: '',
      description: '',
      due_date: new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0],
    });
    setIsCreateModalOpen(true);
  };

  const handleOpenEditModal = (hw: HomeworkItem) => {
    setFormError(null);
    setEditingHomework(hw);
    setHomeworkForm({
      school_class_id: hw.school_class_id,
      section_id: hw.section_id || '',
      subject_id: hw.subject_id,
      title: hw.title,
      description: hw.description,
      due_date: hw.due_date,
    });
    setIsCreateModalOpen(true);
  };

  const handleSubmitHomeworkForm = () => {
    setFormError(null);
    if (!homeworkForm.title.trim()) {
      setFormError('Title is required.');
      return;
    }
    if (!homeworkForm.description.trim()) {
      setFormError('Instructions/Description are required.');
      return;
    }

    if (editingHomework) {
      updateHomeworkMutation.mutate({
        id: editingHomework.id,
        payload: {
          title: homeworkForm.title,
          description: homeworkForm.description,
          due_date: homeworkForm.due_date,
        },
      });
    } else {
      createHomeworkMutation.mutate({
        school_class_id: homeworkForm.school_class_id,
        section_id: homeworkForm.section_id || undefined,
        subject_id: homeworkForm.subject_id,
        title: homeworkForm.title,
        description: homeworkForm.description,
        due_date: homeworkForm.due_date,
      });
    }
  };

  const statusVariant = (status: string) => {
    switch (status) {
      case 'PUBLISHED': return 'success';
      case 'DRAFT': return 'warning';
      case 'CLOSED': return 'default';
      default: return 'default';
    }
  };

  const submissionStatusVariant = (status: string) => {
    switch (status) {
      case 'GRADED': return 'success';
      case 'SUBMITTED':
      case 'RESUBMITTED': return 'info';
      case 'LATE': return 'warning';
      default: return 'default';
    }
  };

  const teacherColumns: Column<HomeworkItem>[] = [
    {
      key: 'title',
      header: 'Assignment Title',
      render: (row) => (
        <div>
          <div className="font-medium text-xs text-ink dark:text-stone-200">{row.title}</div>
          <div className="text-[10px] text-ink-muted font-mono">{row.subject_name || 'Subject'}</div>
        </div>
      ),
    },
    {
      key: 'class',
      header: 'Class / Sec',
      render: (row) => (
        <span className="text-xs font-mono">
          {row.school_class_name || 'Class'} {row.section_name ? `(${row.section_name})` : ''}
        </span>
      ),
    },
    {
      key: 'due_date',
      header: 'Due Date',
      render: (row) => <span className="font-mono text-xs text-amber-600 font-bold">{row.due_date}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <Badge variant={statusVariant(row.status)}>{row.status}</Badge>,
    },
    {
      key: 'submissions',
      header: 'Submissions',
      render: (row) => (
        <span className="font-mono text-xs font-bold text-brand-500">{row.submission_count || 0} Submitted</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      className: 'text-right min-w-[16rem]',
      render: (row) => (
        <div className="flex justify-end gap-1">
          <Button variant="outline" size="sm" onClick={() => setSelectedHomeworkForSubmissions(row)}>
            Review ({row.submission_count || 0})
          </Button>
          {row.status === 'DRAFT' && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => publishHomeworkMutation.mutate(row.id)}
              isLoading={publishHomeworkMutation.isPending}
            >
              Publish
            </Button>
          )}
          {row.status === 'PUBLISHED' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => closeHomeworkMutation.mutate(row.id)}
              isLoading={closeHomeworkMutation.isPending}
            >
              Close
            </Button>
          )}
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

  if (isHomeworkError) {
    return (
      <div className="p-6">
        <ErrorState
          title="Homework Module Error"
          message={(homeworkError as any)?.message || 'Failed to load homework assignments.'}
          onRetry={() => refetchHomework()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-paper dark:bg-stone-950 min-h-[85vh]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-divider pb-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-ink-muted">
            ACADEMIC_WORKSTATION // HOMEWORK_MODULE
          </p>
          <h1 className="text-2xl font-serif font-bold text-brand-500 mt-1">
            Homework & Assignments Portal
          </h1>
        </div>

        {isTeacherOrAdmin && (
          <Button variant="primary" size="sm" onClick={handleOpenCreateModal}>
            + Create Homework Assignment
          </Button>
        )}
      </div>

      {/* TEACHER/ADMIN VIEW */}
      {isTeacherOrAdmin && (
        <div className="space-y-6">
          {/* Summary Metric Bar */}
          {summaryData && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Card className="p-3 text-center border-brand-500/30">
                <p className="text-[10px] font-mono uppercase text-ink-muted">TOTAL</p>
                <p className="text-xl font-bold font-mono text-brand-500">{summaryData.total_homework}</p>
              </Card>
              <Card className="p-3 text-center border-amber-500/30">
                <p className="text-[10px] font-mono uppercase text-amber-600">DRAFT</p>
                <p className="text-xl font-bold font-mono text-amber-600">{summaryData.draft_count}</p>
              </Card>
              <Card className="p-3 text-center border-green-500/30">
                <p className="text-[10px] font-mono uppercase text-green-600">PUBLISHED</p>
                <p className="text-xl font-bold font-mono text-green-600">{summaryData.published_count}</p>
              </Card>
              <Card className="p-3 text-center border-sky-500/30">
                <p className="text-[10px] font-mono uppercase text-sky-600">DUE SOON</p>
                <p className="text-xl font-bold font-mono text-sky-600">{summaryData.due_soon_count}</p>
              </Card>
              <Card className="p-3 text-center border-stone-500/30">
                <p className="text-[10px] font-mono uppercase text-stone-500">CLOSED</p>
                <p className="text-xl font-bold font-mono text-stone-500">{summaryData.closed_count}</p>
              </Card>
            </div>
          )}

          {/* Filters & Table */}
          <Card className="p-4 space-y-4">
            <div className="flex flex-col md:flex-row gap-3">
              <select
                className="text-xs border border-divider rounded p-2 bg-paper dark:bg-stone-900"
                value={selectedClassFilter}
                onChange={(e) => { setSelectedClassFilter(e.target.value); setPage(1); }}
              >
                <option value="">All Target Classes</option>
                {classesData?.items.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>

              <select
                className="text-xs border border-divider rounded p-2 bg-paper dark:bg-stone-900"
                value={selectedSubjectFilter}
                onChange={(e) => { setSelectedSubjectFilter(e.target.value); setPage(1); }}
              >
                <option value="">All Subjects</option>
                {subjectsData?.items.map((s) => (
                  <option key={s.id} value={s.id}>{s.subject_name}</option>
                ))}
              </select>

              <select
                className="text-xs border border-divider rounded p-2 bg-paper dark:bg-stone-900"
                value={selectedStatusFilter}
                onChange={(e) => { setSelectedStatusFilter(e.target.value); setPage(1); }}
              >
                <option value="">All Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="PUBLISHED">Published</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <Table
              columns={teacherColumns}
              data={homeworkData?.items || []}
              rowKey={(row) => row.id}
              isLoading={isHomeworkLoading}
              emptyText="No homework assignments found."
            />

            {homeworkData && homeworkData.total_pages > 1 && (
              <Pagination page={page} totalPages={homeworkData.total_pages} onPageChange={(p) => setPage(p)} />
            )}
          </Card>
        </div>
      )}

      {/* STUDENT VIEW */}
      {isStudent && (
        <div className="space-y-4">
          <div className="flex border-b border-divider gap-4">
            <button
              onClick={() => setStudentTab('all')}
              className={`pb-2.5 text-xs font-mono font-bold border-b-2 uppercase ${
                studentTab === 'all' ? 'border-brand-500 text-brand-500' : 'border-transparent text-ink-muted'
              }`}
            >
              All Assignments
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {homeworkData?.items.map((hw) => (
              <Card key={hw.id} className="p-4 space-y-3 border-l-4 border-l-brand-500">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-mono uppercase bg-brand-50 text-brand-700 px-2 py-0.5 rounded font-bold">
                      {hw.subject_name || 'Subject'}
                    </span>
                    <h3 className="text-base font-bold text-ink dark:text-stone-100 mt-1">{hw.title}</h3>
                    <p className="text-xs text-ink-muted line-clamp-2 mt-0.5">{hw.description}</p>
                  </div>
                  <Badge variant={statusVariant(hw.status)}>{hw.status}</Badge>
                </div>

                <div className="flex items-center justify-between text-xs border-t border-divider pt-2 mt-2">
                  <div className="flex items-center gap-1 text-amber-600 font-mono font-bold">
                    <Clock className="w-3.5 h-3.5" /> Due: {hw.due_date}
                  </div>
                  <Button variant="primary" size="sm" onClick={() => setSubmittingHomework(hw)}>
                    <Send className="w-3 h-3 mr-1" /> View & Submit
                  </Button>
                </div>
              </Card>
            ))}

            {(!homeworkData?.items || homeworkData.items.length === 0) && (
              <Card className="p-8 text-center col-span-2 text-ink-muted">
                <BookOpen className="w-8 h-8 mx-auto mb-2 text-ink-muted/50" />
                <p className="text-sm font-bold">No Published Homework</p>
                <p className="text-xs">You have no pending assignments at this time.</p>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* PARENT VIEW */}
      {isParent && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-brand-500" />
              <label className="text-xs font-mono uppercase font-bold text-ink-muted">Select Child:</label>
              <select
                className="text-xs border border-divider px-3 py-1.5 rounded bg-paper dark:bg-stone-900"
                value={selectedChildId}
                onChange={(e) => setSelectedChildId(e.target.value)}
              >
                <option value="">All Linked Children</option>
              </select>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {homeworkData?.items.map((hw) => (
              <Card key={hw.id} className="p-4 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-brand-500 font-bold">
                      {hw.subject_name || 'Subject'}
                    </span>
                    <h3 className="text-base font-bold text-ink dark:text-stone-100">{hw.title}</h3>
                  </div>
                  <Badge variant={statusVariant(hw.status)}>{hw.status}</Badge>
                </div>

                <p className="text-xs text-ink-muted">{hw.description}</p>

                <div className="flex justify-between items-center text-xs font-mono text-ink-muted border-t border-divider pt-2">
                  <span>Teacher: {hw.teacher_name || 'Staff'}</span>
                  <span className="text-amber-600 font-bold">Due: {hw.due_date}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Modal: Create/Edit Homework */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title={editingHomework ? 'Edit Homework Assignment' : 'Create New Homework Assignment'}
      >
        <div className="space-y-4 py-2">
          {formError && <Alert type="error" title="Validation Failed">{formError}</Alert>}

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Assignment Title *</label>
            <Input
              value={homeworkForm.title}
              onChange={(e) => setHomeworkForm({ ...homeworkForm, title: e.target.value })}
              placeholder="e.g. Chapter 4 Algebra Practice Questions"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">Target Class *</label>
              <select
                className="w-full text-xs border border-divider p-2 rounded bg-paper"
                value={homeworkForm.school_class_id}
                onChange={(e) => setHomeworkForm({ ...homeworkForm, school_class_id: e.target.value })}
              >
                {classesData?.items.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-mono uppercase text-ink-muted">Subject *</label>
              <select
                className="w-full text-xs border border-divider p-2 rounded bg-paper"
                value={homeworkForm.subject_id}
                onChange={(e) => setHomeworkForm({ ...homeworkForm, subject_id: e.target.value })}
              >
                {subjectsData?.items.map((s) => (
                  <option key={s.id} value={s.id}>{s.subject_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Due Date *</label>
            <input
              type="date"
              className="w-full text-xs border border-divider p-2 rounded bg-paper"
              value={homeworkForm.due_date}
              onChange={(e) => setHomeworkForm({ ...homeworkForm, due_date: e.target.value })}
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Instructions / Description *</label>
            <textarea
              rows={4}
              className="w-full text-xs border border-divider p-2 rounded bg-paper"
              value={homeworkForm.description}
              onChange={(e) => setHomeworkForm({ ...homeworkForm, description: e.target.value })}
              placeholder="Enter detailed instructions for students..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
            <Button
              variant="primary"
              onClick={handleSubmitHomeworkForm}
              isLoading={createHomeworkMutation.isPending || updateHomeworkMutation.isPending}
            >
              {editingHomework ? 'Save Changes' : 'Create Assignment'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Drawer: Teacher Review Submissions */}
      <Drawer
        isOpen={!!selectedHomeworkForSubmissions}
        onClose={() => setSelectedHomeworkForSubmissions(null)}
        title={`Review Submissions — ${selectedHomeworkForSubmissions?.title || 'Assignment'}`}
      >
        <div className="space-y-4 text-xs">
          {submissionsData?.items.map((sub) => (
            <Card key={sub.id} className="p-3 space-y-2 border-l-2 border-l-brand-500">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-bold text-ink dark:text-stone-100">{sub.student_name || 'Student'}</p>
                  <p className="text-[10px] font-mono text-ink-muted">Adm: {sub.admission_number || 'N/A'}</p>
                </div>
                <Badge variant={submissionStatusVariant(sub.status)}>{sub.status}</Badge>
              </div>

              <div className="bg-paper-dim p-2.5 rounded border border-divider text-xs whitespace-pre-wrap font-sans">
                {sub.content_text}
              </div>

              {sub.grade && (
                <div className="p-2 bg-green-50/50 border border-green-200 rounded text-xs space-y-1">
                  <p className="font-bold text-green-900">Grade: {sub.grade}</p>
                  <p className="text-green-800">Feedback: {sub.feedback}</p>
                </div>
              )}

              <div className="flex justify-end pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setGradingSubmission(sub);
                    setGradeValue(sub.grade || 'A');
                    setFeedbackValue(sub.feedback || 'Good work!');
                  }}
                >
                  {sub.grade ? 'Re-Grade' : 'Grade Submission'}
                </Button>
              </div>
            </Card>
          ))}

          {(!submissionsData?.items || submissionsData.items.length === 0) && (
            <p className="text-center text-ink-muted py-8 font-mono">No submissions received yet.</p>
          )}
        </div>
      </Drawer>

      {/* Modal: Grade Submission */}
      <Modal
        isOpen={!!gradingSubmission}
        onClose={() => setGradingSubmission(null)}
        title={`Grade Work — ${gradingSubmission?.student_name || 'Student'}`}
      >
        <div className="space-y-4 py-2 text-xs">
          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Grade / Mark *</label>
            <Input
              value={gradeValue}
              onChange={(e) => setGradeValue(e.target.value)}
              placeholder="e.g. A, 95%, 10/10"
            />
          </div>

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Feedback / Remarks</label>
            <textarea
              rows={3}
              className="w-full text-xs border border-divider p-2 rounded bg-paper"
              value={feedbackValue}
              onChange={(e) => setFeedbackValue(e.target.value)}
              placeholder="Enter constructive feedback for the student..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setGradingSubmission(null)}>Cancel</Button>
            <Button
              variant="primary"
              onClick={() =>
                gradingSubmission &&
                gradeSubmissionMutation.mutate({
                  submissionId: gradingSubmission.id,
                  grade: gradeValue,
                  feedback: feedbackValue,
                })
              }
              isLoading={gradeSubmissionMutation.isPending}
            >
              Submit Grade & Feedback
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Student Submit Work */}
      <Modal
        isOpen={!!submittingHomework}
        onClose={() => setSubmittingHomework(null)}
        title={`Submit Homework — ${submittingHomework?.title || ''}`}
      >
        <div className="space-y-4 py-2 text-xs">
          {submitError && <Alert type="error" title="Submission Error">{submitError}</Alert>}

          {submittingHomework && (
            <div className="p-3 bg-brand-50/50 border border-brand-200 rounded text-xs space-y-1">
              <p className="font-bold text-brand-900">{submittingHomework.title}</p>
              <p className="text-brand-800">{submittingHomework.description}</p>
              <p className="text-[10px] font-mono text-amber-700 font-bold">Due Date: {submittingHomework.due_date}</p>
            </div>
          )}

          <div>
            <label className="text-[11px] font-mono uppercase text-ink-muted">Your Written Response *</label>
            <textarea
              rows={6}
              className="w-full text-xs border border-divider p-3 rounded bg-paper"
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              placeholder="Type your complete homework solution or response here..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-divider">
            <Button variant="outline" onClick={() => setSubmittingHomework(null)}>Cancel</Button>
            <Button
              variant="primary"
              onClick={() =>
                submittingHomework &&
                submitWorkMutation.mutate({
                  homeworkId: submittingHomework.id,
                  text: responseText,
                })
              }
              isLoading={submitWorkMutation.isPending}
            >
              Confirm & Submit Work
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteHomeworkMutation.mutate(deleteTarget.id)}
        title="Delete Homework Assignment"
        message={`Are you sure you want to delete assignment "${deleteTarget?.title}"? All student submissions for this assignment will also be permanently deleted.`}
        isLoading={deleteHomeworkMutation.isPending}
      />
    </div>
  );
};
