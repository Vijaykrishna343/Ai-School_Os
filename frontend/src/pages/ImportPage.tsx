import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  importApi,
  ImportPreviewResponse,
  ImportCommitResponse,
  ImportSchema,
} from '@/services/api/phase9Api';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Download,
  Eye,
  ShieldCheck,
  RotateCcw,
  Layers,
  CreditCard,
  GraduationCap,
  Users,
  UserCheck,
  Coins,
} from 'lucide-react';

type EntityType =
  | 'students'
  | 'teachers'
  | 'parents'
  | 'fee_structures'
  | 'outstanding_balances'
  | 'historical_marks';

interface EntityTabConfig {
  id: EntityType;
  label: string;
  icon: React.ElementType;
  description: string;
  sampleRows: Array<Record<string, string>>;
}

const ENTITY_CONFIGS: EntityTabConfig[] = [
  {
    id: 'students',
    label: 'Students',
    icon: GraduationCap,
    description: 'Import student rosters with admission numbers, class & section enrollments, and parent links.',
    sampleRows: [
      {
        first_name: 'John',
        last_name: 'Doe',
        admission_number: 'ADM-2024-001',
        date_of_birth: '2010-05-15',
        gender: 'MALE',
        class_name: 'Grade 10',
        section_name: 'A',
        parent_phone: '9876543210',
        parent_email: 'parent.doe@example.com',
      },
    ],
  },
  {
    id: 'teachers',
    label: 'Teachers',
    icon: UserCheck,
    description: 'Import faculty and teaching staff with employee codes and qualification details.',
    sampleRows: [
      {
        first_name: 'Sarah',
        last_name: 'Smith',
        email: 'sarah.smith@school.org',
        employee_id: 'EMP-T-101',
        phone: '9876543211',
        qualification: 'M.Sc Mathematics, B.Ed',
      },
    ],
  },
  {
    id: 'parents',
    label: 'Parents / Guardians',
    icon: Users,
    description: 'Import parent and guardian profiles mapped to student admission numbers.',
    sampleRows: [
      {
        first_name: 'Robert',
        last_name: 'Doe',
        email: 'parent.doe@example.com',
        phone: '9876543210',
        relationship: 'FATHER',
        student_admission_number: 'ADM-2024-001',
      },
    ],
  },
  {
    id: 'fee_structures',
    label: 'Fee Structures',
    icon: Layers,
    description: 'Bulk import legacy fee structures, item categories, assessed amounts, and class bindings.',
    sampleRows: [
      {
        academic_year: '2024-2025',
        fee_structure_name: 'Grade 10 Annual Fee',
        item_name: 'Tuition Fee Term 1',
        item_category: 'TUITION',
        amount: '25000.00',
        class_name: 'Grade 10',
        is_optional: 'false',
        description: 'Standard term 1 tuition fee',
      },
      {
        academic_year: '2024-2025',
        fee_structure_name: 'Grade 10 Annual Fee',
        item_name: 'Science Lab Fee',
        item_category: 'LABORATORY',
        amount: '5000.00',
        class_name: 'Grade 10',
        is_optional: 'false',
        description: 'Laboratory equipment access fee',
      },
    ],
  },
  {
    id: 'outstanding_balances',
    label: 'Outstanding Balances',
    icon: Coins,
    description: 'Migrate legacy opening balances per student without generating fabricated transaction receipts.',
    sampleRows: [
      {
        admission_number: 'ADM-2024-001',
        academic_year: '2023-2024',
        fee_name: 'Tuition Fee Arrears',
        assessed_amount: '15000.00',
        paid_amount: '5000.00',
        due_date: '2024-03-31',
        remarks: 'Opening arrears carried forward from legacy ERP',
      },
    ],
  },
  {
    id: 'historical_marks',
    label: 'Historical Marks',
    icon: CreditCard,
    description: 'Bulk import prior exam marks and grades mapped to academic year, exam, and subject code.',
    sampleRows: [
      {
        admission_number: 'ADM-2024-001',
        academic_year: '2023-2024',
        class_name: 'Grade 9',
        section_name: 'A',
        exam_name: 'Annual Exam',
        subject_code: 'MATH-101',
        marks_obtained: '88.50',
        max_marks: '100.00',
        passing_marks: '35.00',
        remarks: 'Promoted with distinction',
      },
    ],
  },
];

export const ImportPage: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState<EntityType>('students');
  const [file, setFile] = useState<File | null>(null);
  const [atomicMode, setAtomicMode] = useState<boolean>(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [commitLoading, setCommitLoading] = useState(false);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [commitResult, setCommitResult] = useState<ImportCommitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activeConfig = ENTITY_CONFIGS.find((c) => c.id === selectedEntity)!;

  const { data: schema } = useQuery<ImportSchema>({
    queryKey: ['import-schema', selectedEntity],
    queryFn: () => importApi.getSchema(selectedEntity),
  });

  const handleEntityChange = (entity: EntityType) => {
    setSelectedEntity(entity);
    setFile(null);
    setPreviewData(null);
    setCommitResult(null);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setPreviewData(null);
      setCommitResult(null);
      setError(null);
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    setPreviewLoading(true);
    setError(null);
    setCommitResult(null);

    try {
      const res = await importApi.previewImport(selectedEntity, file);
      setPreviewData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Validation failed.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!file) return;
    setCommitLoading(true);
    setError(null);

    try {
      const res = await importApi.commitImport(selectedEntity, file, atomicMode);
      setCommitResult(res);
      setPreviewData(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Commit failed.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setCommitLoading(false);
    }
  };

  const downloadSampleCsv = () => {
    if (!schema) return;
    const headers = [...schema.required_columns, ...schema.optional_columns];
    const rows = activeConfig.sampleRows;
    const csvHeaderLine = headers.join(',');
    const sampleLines = rows.map((row) =>
      headers.map((h) => (row[h] !== undefined ? `"${row[h]}"` : '""')).join(',')
    );
    const csvContent = `data:text/csv;charset=utf-8,${csvHeaderLine}\n${sampleLines.join('\n')}`;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `sample_${selectedEntity}_template.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-ink dark:text-stone-100 tracking-tight flex items-center space-x-2">
          <ShieldCheck className="w-7 h-7 text-brand-500" />
          <span>Bulk Data Onboarding & Migration</span>
        </h1>
        <p className="text-sm text-ink-muted dark:text-stone-400 mt-1">
          Safely validate and migrate school rosters, legacy fee schedules, opening balances, and historical grades.
        </p>
      </div>

      {/* Entity Selection Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 border-b border-stone-200 dark:border-stone-800 pb-3">
        {ENTITY_CONFIGS.map((config) => {
          const Icon = config.icon;
          const isSelected = selectedEntity === config.id;
          return (
            <button
              key={config.id}
              onClick={() => handleEntityChange(config.id)}
              className={`flex items-center space-x-2 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all border ${
                isSelected
                  ? 'bg-brand-500 text-white border-brand-600 shadow-sm'
                  : 'bg-white dark:bg-stone-900 text-stone-600 dark:text-stone-300 border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">{config.label}</span>
            </button>
          );
        })}
      </div>

      {/* Description & Schema Info */}
      <div className="bg-stone-50 dark:bg-stone-900/60 border border-stone-200 dark:border-stone-800 rounded-xl p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-ink dark:text-stone-100 flex items-center space-x-2">
              <span>{activeConfig.label} Migration Schema</span>
            </h3>
            <p className="text-xs text-ink-muted dark:text-stone-400 mt-0.5">
              {activeConfig.description}
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={downloadSampleCsv} disabled={!schema}>
            <Download className="w-4 h-4 mr-1.5" />
            Download Sample CSV
          </Button>
        </div>

        {schema && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs border-t border-stone-200 dark:border-stone-800">
            <div>
              <span className="font-semibold text-rose-600 dark:text-rose-400">Required Columns:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {schema.required_columns.map((c) => (
                  <span
                    key={c}
                    className="px-2 py-0.5 bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 rounded border border-rose-200 dark:border-rose-900 font-mono"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span className="font-semibold text-stone-600 dark:text-stone-400">Optional Columns:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {schema.optional_columns.length > 0 ? (
                  schema.optional_columns.map((c) => (
                    <span
                      key={c}
                      className="px-2 py-0.5 bg-stone-100 text-stone-700 dark:bg-stone-800 dark:text-stone-300 rounded border border-stone-200 dark:border-stone-700 font-mono"
                    >
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-stone-400 italic">None</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload & Action Card */}
      <div className="border-2 border-dashed border-stone-300 dark:border-stone-700 rounded-xl p-6 text-center bg-white dark:bg-stone-900 space-y-4">
        <FileSpreadsheet className="w-12 h-12 text-brand-500 mx-auto" />
        <div>
          <label className="cursor-pointer inline-flex items-center space-x-2 bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm">
            <Upload className="w-4 h-4" />
            <span>Select {activeConfig.label} File (.csv, .xlsx)</span>
            <input
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          {file && (
            <p className="mt-2 text-sm font-medium text-ink dark:text-stone-200">
              Selected: <span className="font-mono text-brand-600 dark:text-brand-400">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        {file && (
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <label className="flex items-center space-x-2 text-xs font-medium text-stone-700 dark:text-stone-300 cursor-pointer">
              <input
                type="checkbox"
                checked={atomicMode}
                onChange={(e) => setAtomicMode(e.target.checked)}
                className="rounded border-stone-300 text-brand-600 focus:ring-brand-500 h-4 w-4"
              />
              <span>Atomic Mode (Rollback entire batch if any row fails)</span>
            </label>
          </div>
        )}

        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <Button
            variant="secondary"
            disabled={!file || previewLoading || commitLoading}
            onClick={handlePreview}
            isLoading={previewLoading}
          >
            <Eye className="w-4 h-4 mr-1.5" />
            Validate & Preview (Dry Run)
          </Button>
          <Button
            disabled={!file || previewLoading || commitLoading}
            onClick={handleCommit}
            isLoading={commitLoading}
          >
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            Commit {activeConfig.label} Import
          </Button>
        </div>
      </div>

      {error && (
        <Alert type="error" title="Import Error">
          {error}
        </Alert>
      )}

      {/* Dry-Run Preview Results */}
      {previewData && (
        <div className="space-y-4 border border-blue-200 dark:border-blue-900/60 rounded-xl p-6 bg-blue-50/30 dark:bg-blue-950/10">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-blue-900 dark:text-blue-200 flex items-center space-x-2">
              <Eye className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span>Dry-Run Validation Preview (Zero Database Mutations)</span>
            </h2>
            <span
              className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                previewData.can_commit
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                  : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
              }`}
            >
              {previewData.can_commit ? 'Ready for Commit' : 'Has Blocking Errors'}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-white dark:bg-stone-900 p-3 rounded-lg text-center border border-stone-200 dark:border-stone-800">
              <span className="text-xs text-stone-500 block">Total Rows</span>
              <span className="text-lg font-bold text-ink dark:text-stone-100">{previewData.total_rows}</span>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950/50 p-3 rounded-lg text-center border border-emerald-200 dark:border-emerald-900">
              <span className="text-xs text-emerald-700 dark:text-emerald-300 block">Valid Rows</span>
              <span className="text-lg font-bold text-emerald-700 dark:text-emerald-300">{previewData.valid_rows}</span>
            </div>
            <div className="bg-rose-50 dark:bg-rose-950/50 p-3 rounded-lg text-center border border-rose-200 dark:border-rose-900">
              <span className="text-xs text-rose-700 dark:text-rose-300 block">Invalid Rows</span>
              <span className="text-lg font-bold text-rose-700 dark:text-rose-300">{previewData.invalid_rows}</span>
            </div>
            <div className="bg-amber-50 dark:bg-amber-950/50 p-3 rounded-lg text-center border border-amber-200 dark:border-amber-900">
              <span className="text-xs text-amber-700 dark:text-amber-300 block">Duplicate Candidates</span>
              <span className="text-lg font-bold text-amber-700 dark:text-amber-300">{previewData.duplicate_candidates}</span>
            </div>
            <div className="bg-purple-50 dark:bg-purple-950/50 p-3 rounded-lg text-center border border-purple-200 dark:border-purple-900">
              <span className="text-xs text-purple-700 dark:text-purple-300 block">Reference Errors</span>
              <span className="text-lg font-bold text-purple-700 dark:text-purple-300">{previewData.reference_errors}</span>
            </div>
          </div>

          {previewData.errors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-rose-700 dark:text-rose-300 flex items-center space-x-1">
                <AlertTriangle className="w-4 h-4" />
                <span>Detected Validation Errors ({previewData.errors.length})</span>
              </h4>
              <div className="max-h-48 overflow-y-auto border border-rose-200 dark:border-rose-900 rounded-lg p-2 bg-rose-50/50 dark:bg-rose-950/20 text-xs space-y-1 font-mono">
                {previewData.errors.map((err, idx) => (
                  <div key={idx} className="text-rose-700 dark:text-rose-300">
                    Row {err.row_number}: {err.field ? `[${err.field}] ` : ''}{err.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {previewData.preview_rows.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-stone-700 dark:text-stone-300">
                Sample Valid Rows Preview (First {previewData.preview_rows.length})
              </h4>
              <div className="overflow-x-auto border border-stone-200 dark:border-stone-800 rounded-lg bg-white dark:bg-stone-900">
                <table className="min-w-full text-xs text-left">
                  <thead className="bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300">
                    <tr>
                      {Object.keys(previewData.preview_rows[0] || {}).map((header) => (
                        <th key={header} className="px-3 py-2 font-mono">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200 dark:divide-stone-800 font-mono">
                    {previewData.preview_rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-stone-50 dark:hover:bg-stone-800/50">
                        {Object.values(row).map((val, cellIdx) => (
                          <td key={cellIdx} className="px-3 py-1.5 text-stone-700 dark:text-stone-300">
                            {val !== null && val !== undefined ? String(val) : ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Committed Result Report */}
      {commitResult && (
        <div className="space-y-4 border border-stone-200 dark:border-stone-800 rounded-xl p-6 bg-white dark:bg-stone-900">
          <h2 className="text-base font-bold text-ink dark:text-stone-100 flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <span>Commit Execution Report</span>
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-stone-50 dark:bg-stone-800 p-3 rounded-lg text-center">
              <span className="text-xs text-stone-500 dark:text-stone-400 block">Total Rows</span>
              <span className="text-xl font-bold text-ink dark:text-stone-100">{commitResult.total_rows}</span>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950 p-3 rounded-lg text-center">
              <span className="text-xs text-emerald-700 dark:text-emerald-300 block">Inserted Rows</span>
              <span className="text-xl font-bold text-emerald-700 dark:text-emerald-300">{commitResult.inserted_rows}</span>
            </div>
            <div className="bg-amber-50 dark:bg-amber-950 p-3 rounded-lg text-center">
              <span className="text-xs text-amber-700 dark:text-amber-300 block">Skipped / Duplicates</span>
              <span className="text-xl font-bold text-amber-700 dark:text-amber-300">{commitResult.skipped_rows}</span>
            </div>
            <div className="bg-rose-50 dark:bg-rose-950 p-3 rounded-lg text-center">
              <span className="text-xs text-rose-700 dark:text-rose-300 block">Errors</span>
              <span className="text-xl font-bold text-rose-700 dark:text-rose-300">{commitResult.errors.length}</span>
            </div>
          </div>

          {commitResult.errors.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-semibold text-rose-600 dark:text-rose-400 flex items-center space-x-1">
                <AlertTriangle className="w-4 h-4" />
                <span>Execution Errors ({commitResult.errors.length})</span>
              </h4>
              <div className="max-h-60 overflow-y-auto border border-rose-200 dark:border-rose-900 rounded-lg p-2 bg-rose-50/50 dark:bg-rose-950/20 text-xs space-y-1 font-mono">
                {commitResult.errors.map((err, idx) => (
                  <div key={idx} className="text-rose-700 dark:text-rose-300">
                    Row {err.row_number}: {err.field ? `[${err.field}] ` : ''}{err.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

