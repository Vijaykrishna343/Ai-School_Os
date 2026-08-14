import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { progressionApi } from '@/services/api/progressionApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import {
  AcademicYear,
  ClassProgressionRule,
  ClassProgressionRuleCreate,
  StudentProgressionPreviewItem,
} from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';

type TabType = 'matrix' | 'rollover';

export const ProgressionPage: React.FC = () => {
  const { permissions } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<TabType>('matrix');

  // Matrix Rule form and creation states
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<ClassProgressionRule | null>(null);
  const [ruleForm, setRuleForm] = useState<Partial<ClassProgressionRuleCreate>>({
    source_class_id: '',
    target_class_id: '',
    is_terminal: false,
    description: '',
  });
  const [ruleError, setRuleError] = useState<string | null>(null);

  // Rollover dry run states
  const [sourceYearId, setSourceYearId] = useState('');
  const [targetYearId, setTargetYearId] = useState('');
  const [previewPage, setPreviewPage] = useState(1);
  const [previewPageSize] = useState(50);
  
  // Dry run preview response cache
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // Execution verification state
  const [isExecuteConfirmOpen, setIsExecuteConfirmOpen] = useState(false);
  const [confirmWarningsCheck, setConfirmWarningsCheck] = useState(false);
  const [confirmHashCheck, setConfirmHashCheck] = useState('');
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // ---------------------------------------------------------
  // Data Queries
  // ---------------------------------------------------------
  const { data: yearsData } = useQuery({
    queryKey: ['academicYearsList'],
    queryFn: () => academicYearsApi.getAcademicYears({ page: 1, page_size: 100 }),
  });

  const { data: classesData } = useQuery({
    queryKey: ['schoolClassesList'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: 1, page_size: 100 }),
  });

  const { data: rulesData, isLoading: isRulesLoading } = useQuery({
    queryKey: ['progressionRules'],
    queryFn: () => progressionApi.getRules({ page: 1, page_size: 100 }),
  });

  // Rule mutations
  const createRuleMutation = useMutation({
    mutationFn: progressionApi.createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progressionRules'] });
      setIsRuleModalOpen(false);
      resetRuleForm();
    },
    onError: (err: any) => {
      setRuleError(err.message || 'Failed to create progression rule.');
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => progressionApi.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progressionRules'] });
      setIsRuleModalOpen(false);
      resetRuleForm();
    },
    onError: (err: any) => {
      setRuleError(err.message || 'Failed to update progression rule.');
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: progressionApi.deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progressionRules'] });
    },
    onError: (err: any) => {
      alert(err.message || 'Failed to delete progression rule.');
    },
  });

  // ---------------------------------------------------------
  // Helper methods
  // ---------------------------------------------------------
  const resetRuleForm = () => {
    setRuleForm({
      source_class_id: '',
      target_class_id: '',
      is_terminal: false,
      description: '',
    });
    setEditingRule(null);
    setRuleError(null);
  };

  const handleOpenCreateModal = () => {
    resetRuleForm();
    setIsRuleModalOpen(true);
  };

  const handleOpenEditModal = (rule: ClassProgressionRule) => {
    resetRuleForm();
    setEditingRule(rule);
    setRuleForm({
      source_class_id: rule.source_class_id,
      target_class_id: rule.target_class_id || '',
      is_terminal: rule.is_terminal,
      description: rule.description || '',
    });
    setIsRuleModalOpen(true);
  };

  const handleSubmitRule = () => {
    if (!ruleForm.source_class_id) {
      setRuleError('Source class is required.');
      return;
    }
    if (!ruleForm.is_terminal && !ruleForm.target_class_id) {
      setRuleError('Target class is required for non-terminal progression.');
      return;
    }
    if (ruleForm.is_terminal && ruleForm.target_class_id) {
      setRuleForm({ ...ruleForm, target_class_id: null });
    }

    if (editingRule) {
      updateRuleMutation.mutate({
        id: editingRule.id,
        data: {
          target_class_id: ruleForm.is_terminal ? null : ruleForm.target_class_id,
          is_terminal: ruleForm.is_terminal,
          description: ruleForm.description,
        },
      });
    } else {
      createRuleMutation.mutate(ruleForm as ClassProgressionRuleCreate);
    }
  };

  // Preview Dry Run trigger
  const handleTriggerPreview = async () => {
    if (!sourceYearId || !targetYearId) {
      setPreviewError('Source and target academic years are required.');
      return;
    }
    if (sourceYearId === targetYearId) {
      setPreviewError('Source and target academic years cannot be the same.');
      return;
    }

    setIsPreviewLoading(true);
    setPreviewError(null);
    setPreviewData(null);
    setExecutionResult(null);
    setExecutionError(null);

    try {
      const res = await progressionApi.generatePreview(sourceYearId, {
        target_academic_year_id: targetYearId,
        page: previewPage,
        page_size: previewPageSize,
      });
      setPreviewData(res);
    } catch (err: any) {
      setPreviewError(err.message || 'Failed to calculate academic progression preview.');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Rollover execution confirmation trigger
  const handleOpenExecutionConfirm = () => {
    if (!previewData) return;
    setConfirmWarningsCheck(false);
    setConfirmHashCheck('');
    setExecutionError(null);
    setIsExecuteConfirmOpen(true);
  };

  const handleExecuteRollover = async () => {
    if (!previewData) return;
    
    // Hash match enforcement
    if (confirmHashCheck !== previewData.execution_plan_hash) {
      setExecutionError('Hash validation failed. The entered hash does not match the active plan.');
      return;
    }

    setIsExecuting(true);
    setExecutionError(null);

    // Generate unique idempotency key
    const idempotencyKey = `rollover-${sourceYearId}-${targetYearId}-${Date.now()}`;

    try {
      const res = await progressionApi.executeRollover(
        sourceYearId,
        {
          target_academic_year_id: targetYearId,
          execution_plan_hash: previewData.execution_plan_hash,
          confirm_warnings: confirmWarningsCheck,
        },
        idempotencyKey
      );
      setExecutionResult(res);
      setIsExecuteConfirmOpen(false);
      setPreviewData(null); // Clear preview state upon successful rollover
    } catch (err: any) {
      // Catch STALE plan changes or conflicts
      if (err.status === 409) {
        setExecutionError('Stale plan hash encountered. The underlying registry records have changed. Generate a new preview.');
      } else {
        setExecutionError(err.message || 'An unexpected error occurred during rollover execution.');
      }
    } finally {
      setIsExecuting(false);
    }
  };

  // ---------------------------------------------------------
  // Column definitions
  // ---------------------------------------------------------
  const ruleColumns: Column<ClassProgressionRule>[] = [
    {
      key: 'source_class',
      header: 'Source Class',
      render: (row) => {
        const cls = classesData?.items?.find((c) => c.id === row.source_class_id);
        return <span className="font-semibold text-slate-800">{cls?.name || row.source_class_id}</span>;
      },
    },
    {
      key: 'direction',
      header: '➔',
      render: () => <span className="text-slate-400 font-mono">➔</span>,
      className: 'text-center w-12',
    },
    {
      key: 'target_class',
      header: 'Target Class / Destination',
      render: (row) => {
        if (row.is_terminal) {
          return <Badge variant="neutral">GRADUATED (Terminal)</Badge>;
        }
        const cls = classesData?.items?.find((c) => c.id === row.target_class_id);
        return <span className="text-slate-800">{cls?.name || row.target_class_id}</span>;
      },
    },
    {
      key: 'description',
      header: 'Description',
      render: (row) => <span className="text-slate-500 font-mono text-xs">{row.description || '—'}</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {permissions.includes('progression_matrix.manage') && (
            <>
              <Button variant="outline" size="sm" onClick={() => handleOpenEditModal(row)}>
                Edit
              </Button>
              <Button variant="danger" size="sm" onClick={() => {
                if (confirm('Delete this progression mapping?')) {
                  deleteRuleMutation.mutate(row.id);
                }
              }}>
                Delete
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const previewItemColumns: Column<StudentProgressionPreviewItem>[] = [
    {
      key: 'admission_number',
      header: 'Adm No',
      render: (row) => <span className="font-mono font-bold text-slate-700">{row.admission_number}</span>,
    },
    {
      key: 'student_name',
      header: 'Student Name',
      render: (row) => <span className="font-semibold text-slate-900">{row.student_name}</span>,
    },
    {
      key: 'current_placement',
      header: 'Source Placement',
      render: (row) => <span className="text-slate-500">{row.current_class_name} - {row.current_section_name}</span>,
    },
    {
      key: 'decision',
      header: 'Outcome Decision',
      render: (row) => {
        const badgeColors = {
          PENDING: 'neutral' as const,
          PROMOTED: 'success' as const,
          RETAINED: 'warning' as const,
          GRADUATED: 'neutral' as const,
          TRANSFERRED: 'info' as const,
          WITHDRAWN: 'error' as const,
        };
        return <Badge variant={badgeColors[row.decision] || 'default'}>{row.decision}</Badge>;
      },
    },
    {
      key: 'target_placement',
      header: 'Target Placement',
      render: (row) => {
        if (row.decision === 'GRADUATED') return <span className="text-slate-400 font-mono">GRADUATED_OUT</span>;
        if (row.decision === 'TRANSFERRED') return <span className="text-slate-400 font-mono">TRANSFERRED_OUT</span>;
        if (row.decision === 'WITHDRAWN') return <span className="text-slate-400 font-mono">WITHDRAWN_OUT</span>;
        if (row.allocation_status === 'BLOCKED') return <span className="text-red-500 font-mono">EXECUTION_BLOCKED</span>;
        if (row.allocation_status === 'EXCLUDED') return <span className="text-slate-400 font-mono">EXCLUDED_STUDENT</span>;
        return <span className="text-brand-500 font-semibold">{row.target_class_name || 'Class'} - {row.target_section_name || 'A'}</span>;
      },
    },
    {
      key: 'reason',
      header: 'Placement Reason',
      render: (row) => <span className="text-slate-500 text-xs font-mono">{row.reason}</span>,
    },
    {
      key: 'warnings',
      header: 'Warnings / Blocks',
      render: (row) => {
        if (!row.warnings || row.warnings.length === 0) return <span className="text-slate-300 font-mono">—</span>;
        return (
          <div className="space-y-1.5 max-w-xs">
            {row.warnings.map((w, idx) => (
              <div key={idx} className="border-l-2 border-amber-500 pl-2 py-0.5 text-xs text-slate-800 dark:text-slate-200 leading-normal">
                <span className="block text-[9px] uppercase font-mono tracking-wider text-amber-600 font-semibold mb-0.5">
                  Warning
                </span>
                <span className="block whitespace-normal break-words">{w}</span>
              </div>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh]">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            REGISTRAR TRANSITION SERVICES
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Academic Progression Workspace
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Build progression mappings, evaluate dry-run roll-overs, and commit atomic academic year transitions.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('matrix')}
            className={`py-2.5 px-1 text-xs font-mono uppercase tracking-wider border-b-2 transition-colors ${
              activeTab === 'matrix'
                ? 'border-brand-500 text-brand-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Progression Matrix Rules
          </button>
          <button
            onClick={() => setActiveTab('rollover')}
            className={`py-2.5 px-1 text-xs font-mono uppercase tracking-wider border-b-2 transition-colors ${
              activeTab === 'rollover'
                ? 'border-brand-500 text-brand-500 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Dry-Run & Rollover Console
          </button>
        </nav>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Tab: Progression Matrix Rules */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'matrix' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
              PROGRESSION_RULES_MAP
            </p>
            {permissions.includes('progression_matrix.manage') && (
              <Button onClick={handleOpenCreateModal}>+ Create Mapping Rule</Button>
            )}
          </div>

          <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
            <Table
              columns={ruleColumns}
              data={rulesData?.items || []}
              isLoading={isRulesLoading}
              emptyText="No class progression mappings found. Build rules to govern year transition."
            />
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Tab: Dry-Run & Rollover Console */}
      {/* ------------------------------------------------------------- */}
      {activeTab === 'rollover' && (
        <div className="space-y-6">
          {/* Transition Setup Form */}
          <div className="p-4 border border-slate-200 dark:border-slate-800 bg-white rounded-none space-y-4">
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              TRANSITION_PARAMETERS
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="source-year-select"
                  className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Source Academic Year *
                </label>
                <select
                  id="source-year-select"
                  value={sourceYearId}
                  onChange={(e) => setSourceYearId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
                >
                  <option value="">Select Source Year</option>
                  {yearsData?.items?.map((y: AcademicYear) => (
                    <option key={y.id} value={y.id}>{`${y.name} (${y.status})`}</option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="target-year-select"
                  className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1"
                >
                  Target Academic Year *
                </label>
                <select
                  id="target-year-select"
                  value={targetYearId}
                  onChange={(e) => setTargetYearId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
                >
                  <option value="">Select Target Year</option>
                  {yearsData?.items?.map((y: AcademicYear) => (
                    <option key={y.id} value={y.id}>{`${y.name} (${y.status})`}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button onClick={handleTriggerPreview} isLoading={isPreviewLoading}>
                Generate Dry-Run Preview
              </Button>
            </div>

            {previewError && <Alert type="error" title="Dry Run Calculation Error">{previewError}</Alert>}
          </div>

          {/* Audit Completion Result Banner */}
          {executionResult && (
            <div className="p-5 border border-emerald-200 bg-emerald-50/20 rounded-none space-y-3 font-mono text-xs">
              <p className="text-sm font-bold font-serif text-emerald-800">Atomic Rollover Completed Successfully</p>
              <div className="grid grid-cols-2 gap-2 text-emerald-950">
                <div><span className="text-emerald-700 font-semibold">EXECUTION_ID:</span> {executionResult.execution_id}</div>
                <div><span className="text-emerald-700 font-semibold">STATUS:</span> {executionResult.status}</div>
                <div><span className="text-emerald-700 font-semibold">PROMOTED_COUNT:</span> {executionResult.summary?.promoted_count}</div>
                <div><span className="text-emerald-700 font-semibold">GRADUATED_COUNT:</span> {executionResult.summary?.graduated_count}</div>
                <div><span className="text-emerald-700 font-semibold">RETAINED_COUNT:</span> {executionResult.summary?.retained_count}</div>
                <div><span className="text-emerald-700 font-semibold">BLOCKED_COUNT:</span> {executionResult.summary?.blocked_count}</div>
                <div><span className="text-emerald-700 font-semibold">TIMESTAMP:</span> {executionResult.started_at}</div>
              </div>
            </div>
          )}

          {/* Prospective Preview Dry Run Results */}
          {previewData && (
            <div className="space-y-6">
              {/* Summary Stats Ledger */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">EVALUATED</p>
                  <p className="text-xl font-serif font-bold text-brand-500">{previewData.summary.total_students_evaluated}</p>
                </div>
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">PROMOTED</p>
                  <p className="text-xl font-serif font-bold text-emerald-600">{previewData.summary.promoted_count}</p>
                </div>
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">RETAINED</p>
                  <p className="text-xl font-serif font-bold text-amber-600">{previewData.summary.retained_count}</p>
                </div>
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">GRADUATED</p>
                  <p className="text-xl font-serif font-bold text-blue-600">{previewData.summary.graduated_count}</p>
                </div>
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">BLOCKED</p>
                  <p className="text-xl font-serif font-bold text-red-600">{previewData.summary.blocked_count}</p>
                </div>
                <div className="p-3 border border-slate-200 bg-white font-mono text-center">
                  <p className="text-[9px] text-slate-400">WARNINGS</p>
                  <p className="text-xl font-serif font-bold text-rose-600">{previewData.summary.warning_count}</p>
                </div>
              </div>

              {/* Execution Plan Hash Header */}
              <div className="p-3 border border-slate-200 bg-white font-mono text-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                <div>
                  <span className="text-slate-400">PLAN_HASH:</span> <span className="font-bold text-brand-500">{previewData.execution_plan_hash}</span>
                </div>
                {permissions.includes('progression.execute') && (
                  <Button
                    variant="primary"
                    onClick={handleOpenExecutionConfirm}
                    disabled={previewData.summary.blocked_count > 0}
                  >
                    Commit Rollover Execution
                  </Button>
                )}
              </div>

              {previewData.summary.blocked_count > 0 && (
                <Alert type="error" title="Rollover Blocked">
                  Execution is blocked due to active blocks or missing target configurations. Resolve class progression rules or student blocks.
                </Alert>
              )}

              {/* Registry Details Table */}
              <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 space-y-4 rounded-none">
                <p className="text-xs font-mono uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
                  PROSPECTIVE_DECISIONS_LEDGER
                </p>
                <Table
                  columns={previewItemColumns}
                  data={previewData.items || []}
                  isLoading={false}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Modals & Dialogs */}
      {/* ------------------------------------------------------------- */}

      {/* Rule Create/Edit Modal */}
      <Modal
        isOpen={isRuleModalOpen}
        onClose={() => setIsRuleModalOpen(false)}
        title={editingRule ? 'Edit Progression Rule Mapping' : 'Create Progression Rule Mapping'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsRuleModalOpen(false)}>Cancel</Button>
            <Button
              onClick={handleSubmitRule}
              isLoading={createRuleMutation.isPending || updateRuleMutation.isPending}
            >
              Save Mapping Rule
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {ruleError && <Alert type="error" title="Validation Error">{ruleError}</Alert>}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Source School Class *
            </label>
            <select
              value={ruleForm.source_class_id || ''}
              onChange={(e) => setRuleForm({ ...ruleForm, source_class_id: e.target.value })}
              className="w-full px-3 py-2 text-sm rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
            >
              <option value="">Select Source Class</option>
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 py-2">
            <input
              type="checkbox"
              id="is_terminal"
              checked={ruleForm.is_terminal || false}
              onChange={(e) => setRuleForm({ ...ruleForm, is_terminal: e.target.checked, target_class_id: e.target.checked ? '' : ruleForm.target_class_id })}
              className="rounded-sm border-slate-300 text-brand-500"
            />
            <label htmlFor="is_terminal" className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Terminal Class (Graduation Outcome)
            </label>
          </div>

          {!ruleForm.is_terminal && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Target Promotion Class *
              </label>
              <select
                value={ruleForm.target_class_id || ''}
                onChange={(e) => setRuleForm({ ...ruleForm, target_class_id: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
              >
                <option value="">Select Target Class</option>
                {classesData?.items?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          )}

          <Input
            label="Rule Description"
            placeholder="e.g. Nursery promotes to LKG automatically"
            value={ruleForm.description || ''}
            onChange={(e) => setRuleForm({ ...ruleForm, description: e.target.value })}
          />
        </div>
      </Modal>

      {/* Rollover Execution Confirmation Wizard Modal */}
      <Modal
        isOpen={isExecuteConfirmOpen}
        onClose={() => setIsExecuteConfirmOpen(false)}
        title="Institutional Rollover Execution Confirmation"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsExecuteConfirmOpen(false)}>Cancel</Button>
            <Button
              variant="primary"
              onClick={handleExecuteRollover}
              isLoading={isExecuting}
              disabled={confirmHashCheck !== previewData?.execution_plan_hash}
            >
              Confirm and Commit Transaction
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Alert type="warning" title="Critical Action Required">
            You are initiating an atomic rollover transaction. All matching students in the source academic year will be promoted, retained, or graduated according to progression rules.
          </Alert>

          {executionError && <Alert type="error" title="Execution Rejected">{executionError}</Alert>}

          <div className="p-3 border border-slate-200 bg-slate-50 font-mono text-xs space-y-2">
            <div><span className="text-slate-400">PLAN_HASH:</span> <span className="font-bold text-brand-500">{previewData?.execution_plan_hash}</span></div>
            <div><span className="text-slate-400">AFFECTED_COUNT:</span> {previewData?.summary.total_students_evaluated}</div>
            <div><span className="text-slate-400">WARNING_COUNT:</span> {previewData?.summary.warning_count}</div>
          </div>

          <div className="flex items-start gap-2 py-2">
            <input
              type="checkbox"
              id="confirm_warnings"
              checked={confirmWarningsCheck}
              onChange={(e) => setConfirmWarningsCheck(e.target.checked)}
              className="rounded-sm border-slate-300 text-brand-500 mt-0.5"
            />
            <label htmlFor="confirm_warnings" className="text-xs text-slate-700">
              I acknowledge and accept all warning/block indicators identified in the prospective decisions ledger preview.
            </label>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Verify Execution Plan Hash *
            </label>
            <p className="text-[10px] text-slate-400 mb-1.5">
              Enter the exact SHA-256 plan hash from the preview header to verify execution:
            </p>
            <Input
              placeholder="Enter SHA-256 hash value..."
              value={confirmHashCheck}
              onChange={(e) => setConfirmHashCheck(e.target.value)}
              className="font-mono text-xs"
              required
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
