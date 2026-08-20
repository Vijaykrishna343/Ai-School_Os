import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { importApi, ImportResult, ImportSchema } from '@/services/api/phase9Api';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Upload, FileSpreadsheet, CheckCircle2, AlertTriangle, FileText, Download } from 'lucide-react';

export const ImportPage: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState<'students' | 'teachers' | 'parents'>('students');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: schema } = useQuery<ImportSchema>({
    queryKey: ['import-schema', selectedEntity],
    queryFn: () => importApi.getSchema(selectedEntity),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await importApi.importData(selectedEntity, file);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Import failed. Please check the file format.');
    } finally {
      setLoading(false);
    }
  };

  const downloadSampleCsv = () => {
    if (!schema) return;
    const headers = [...schema.required_columns, ...schema.optional_columns].join(',');
    const sampleRow = schema.required_columns.map(c => `sample_${c}`).join(',');
    const csvContent = `data:text/csv;charset=utf-8,${headers}\n${sampleRow}`;
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
        <h1 className="text-2xl font-bold text-ink dark:text-stone-100 tracking-tight">
          Bulk Data Import
        </h1>
        <p className="text-sm text-ink-muted dark:text-stone-400 mt-1">
          Import student rosters, teacher directories, and guardian contacts using CSV or XLSX files.
        </p>
      </div>

      {/* Entity Selection Tabs */}
      <div className="flex space-x-2 border-b border-stone-200 dark:border-stone-800 pb-2">
        {(['students', 'teachers', 'parents'] as const).map((entity) => (
          <button
            key={entity}
            onClick={() => {
              setSelectedEntity(entity);
              setFile(null);
              setResult(null);
              setError(null);
            }}
            className={`px-4 py-2 text-sm font-medium rounded-lg capitalize transition-colors ${
              selectedEntity === entity
                ? 'bg-brand-500 text-white shadow-sm'
                : 'text-ink-muted dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800'
            }`}
          >
            {entity}
          </button>
        ))}
      </div>

      {/* Schema Card */}
      {schema && (
        <div className="bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink dark:text-stone-200 capitalize">
              {selectedEntity} Column Requirements
            </h3>
            <Button variant="secondary" size="sm" onClick={downloadSampleCsv}>
              <Download className="w-4 h-4 mr-2" />
              Download Sample CSV
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div>
              <span className="font-semibold text-red-600 dark:text-red-400">Required Columns:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {schema.required_columns.map((c) => (
                  <span key={c} className="px-2 py-0.5 bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 rounded font-mono">
                    {c}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span className="font-semibold text-stone-600 dark:text-stone-400">Optional Columns:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {schema.optional_columns.map((c) => (
                  <span key={c} className="px-2 py-0.5 bg-stone-200 text-stone-700 dark:bg-stone-800 dark:text-stone-300 rounded font-mono">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Dropzone */}
      <div className="border-2 border-dashed border-stone-300 dark:border-stone-700 rounded-xl p-8 text-center bg-white dark:bg-stone-900 space-y-4">
        <FileSpreadsheet className="w-12 h-12 text-brand-500 mx-auto" />
        <div>
          <label className="cursor-pointer inline-flex items-center space-x-2 bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm">
            <Upload className="w-4 h-4" />
            <span>Select File (.csv, .xlsx)</span>
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
        <div className="flex justify-center">
          <Button
            disabled={!file || loading}
            onClick={handleUpload}
            isLoading={loading}
          >
            Start {selectedEntity} Import
          </Button>
        </div>
      </div>

      {error && (
        <Alert type="error" title="Import Error">
          {error}
        </Alert>
      )}

      {/* Summary Report */}
      {result && (
        <div className="space-y-4 border border-stone-200 dark:border-stone-800 rounded-xl p-6 bg-white dark:bg-stone-900">
          <h2 className="text-lg font-bold text-ink dark:text-stone-100 flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <span>Import Results Summary</span>
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-stone-50 dark:bg-stone-800 p-3 rounded-lg text-center">
              <span className="text-xs text-ink-muted dark:text-stone-400 block">Total Rows</span>
              <span className="text-xl font-bold text-ink dark:text-stone-100">{result.total_rows}</span>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950 p-3 rounded-lg text-center">
              <span className="text-xs text-emerald-700 dark:text-emerald-300 block">Inserted Rows</span>
              <span className="text-xl font-bold text-emerald-700 dark:text-emerald-300">{result.inserted_rows}</span>
            </div>
            <div className="bg-amber-50 dark:bg-amber-950 p-3 rounded-lg text-center">
              <span className="text-xs text-amber-700 dark:text-amber-300 block">Duplicates Skipped</span>
              <span className="text-xl font-bold text-amber-700 dark:text-amber-300">{result.duplicate_rows}</span>
            </div>
            <div className="bg-rose-50 dark:bg-rose-950 p-3 rounded-lg text-center">
              <span className="text-xs text-rose-700 dark:text-rose-300 block">Invalid Rows</span>
              <span className="text-xl font-bold text-rose-700 dark:text-rose-300">{result.invalid_rows}</span>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-semibold text-rose-600 dark:text-rose-400 flex items-center space-x-1">
                <AlertTriangle className="w-4 h-4" />
                <span>Row-Level Errors & Warnings ({result.errors.length})</span>
              </h4>
              <div className="max-h-60 overflow-y-auto border border-rose-200 dark:border-rose-900 rounded-lg p-2 bg-rose-50/50 dark:bg-rose-950/20 text-xs space-y-1 font-mono">
                {result.errors.map((err, idx) => (
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
