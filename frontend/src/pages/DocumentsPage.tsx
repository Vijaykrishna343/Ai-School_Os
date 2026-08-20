import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi, DocumentItem } from '@/services/api/documentsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { teachersApi } from '@/services/api/teachersApi';
import { Student } from '@/types/models';
import { Teacher } from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  FileText,
  Upload,
  Download,
  Eye,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Filter,
} from 'lucide-react';

const DOCUMENT_CATEGORIES = [
  { value: 'BIRTH_CERTIFICATE', label: 'Birth Certificate', owner: 'STUDENT' },
  { value: 'STUDENT_ID', label: 'Student ID Card', owner: 'STUDENT' },
  { value: 'PREVIOUS_SCHOOL_CERT', label: 'Previous School Cert', owner: 'STUDENT' },
  { value: 'TRANSFER_CERTIFICATE', label: 'Transfer Certificate (TC)', owner: 'STUDENT' },
  { value: 'BONAFIDE_CERTIFICATE', label: 'Bonafide Certificate', owner: 'STUDENT' },
  { value: 'PASSPORT_PHOTO', label: 'Passport Photo', owner: 'BOTH' },
  { value: 'ADMISSION_DOC', label: 'Admission Document', owner: 'STUDENT' },
  { value: 'QUALIFICATION_CERT', label: 'Qualification Certificate', owner: 'STAFF' },
  { value: 'EXPERIENCE_CERT', label: 'Experience Certificate', owner: 'STAFF' },
  { value: 'IDENTITY_DOC', label: 'Identity Document', owner: 'STAFF' },
  { value: 'JOINING_DOC', label: 'Joining Document', owner: 'STAFF' },
  { value: 'APPOINTMENT_DOC', label: 'Appointment Document', owner: 'STAFF' },
  { value: 'OTHER', label: 'Other Document', owner: 'BOTH' },
];

export const DocumentsPage: React.FC = () => {
  const { roles } = useAuthStore();
  const queryClient = useQueryClient();
  const userRole = roles[0]?.name || 'Teacher';

  const isAccountant = userRole === 'Accountant';
  const canVerify = ['Super Admin', 'School Admin', 'Principal', 'Vice Principal'].includes(userRole);
  const canDelete = ['Super Admin', 'School Admin', 'Principal'].includes(userRole);

  // Pagination & Filter States
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [selectedOwnerType, setSelectedOwnerType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  // Modals & Drawers
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isReplaceModalOpen, setIsReplaceModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);

  const [activeDocument, setActiveDocument] = useState<DocumentItem | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Upload Form State
  const [uploadForm, setUploadForm] = useState({
    owner_type: 'STUDENT',
    owner_id: '',
    document_type: 'BIRTH_CERTIFICATE',
    title: '',
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Queries
  const { data: summaryData } = useQuery({
    queryKey: ['documentsSummary'],
    queryFn: documentsApi.getDocumentSummary,
    enabled: !isAccountant,
  });

  const {
    data: documentsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['documents', page, pageSize, selectedOwnerType, selectedStatus, selectedCategory],
    queryFn: () =>
      documentsApi.listDocuments({
        page,
        page_size: pageSize,
        owner_type: selectedOwnerType || undefined,
        status: selectedStatus || undefined,
        document_type: selectedCategory || undefined,
      }),
    enabled: !isAccountant,
  });

  // Students & Teachers options for upload selection
  const { data: studentsList } = useQuery({
    queryKey: ['studentsForDocs'],
    queryFn: () => studentsApi.getStudents({ page_size: 100 }),
    enabled: isUploadModalOpen && uploadForm.owner_type === 'STUDENT',
  });

  const { data: teachersList } = useQuery({
    queryKey: ['teachersForDocs'],
    queryFn: () => teachersApi.getTeachers({ page_size: 100 }),
    enabled: isUploadModalOpen && uploadForm.owner_type === 'STAFF',
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!uploadFile) throw new Error('Please select a file to upload.');
      if (!uploadForm.owner_id) throw new Error('Please select an owner (student or staff).');
      if (!uploadForm.title.trim()) throw new Error('Please enter a document title.');

      const fd = new FormData();
      fd.append('owner_type', uploadForm.owner_type);
      fd.append('owner_id', uploadForm.owner_id);
      fd.append('document_type', uploadForm.document_type);
      fd.append('title', uploadForm.title);
      fd.append('file', uploadFile);

      return documentsApi.uploadDocument(fd);
    },
    onSuccess: () => {
      setActionSuccess('Document uploaded successfully!');
      setIsUploadModalOpen(false);
      setUploadFile(null);
      setUploadForm({ owner_type: 'STUDENT', owner_id: '', document_type: 'BIRTH_CERTIFICATE', title: '' });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documentsSummary'] });
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || 'Failed to upload document.');
    },
  });

  const replaceMutation = useMutation({
    mutationFn: async () => {
      if (!activeDocument || !uploadFile) throw new Error('Please select a file.');
      const fd = new FormData();
      fd.append('file', uploadFile);
      return documentsApi.replaceDocument(activeDocument.id, fd);
    },
    onSuccess: () => {
      setActionSuccess('Document replaced with new version successfully!');
      setIsReplaceModalOpen(false);
      setUploadFile(null);
      setActiveDocument(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || 'Failed to replace document.');
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (id: string) => documentsApi.verifyDocument(id),
    onSuccess: () => {
      setActionSuccess('Document verified successfully.');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documentsSummary'] });
    },
    onError: (err: any) => setActionError(err.response?.data?.detail || 'Failed to verify document.'),
  });

  const rejectMutation = useMutation({
    mutationFn: async () => {
      if (!activeDocument || !rejectionReason.trim()) throw new Error('Rejection reason required.');
      return documentsApi.rejectDocument(activeDocument.id, { rejection_reason: rejectionReason });
    },
    onSuccess: () => {
      setActionSuccess('Document rejected.');
      setIsRejectModalOpen(false);
      setActiveDocument(null);
      setRejectionReason('');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documentsSummary'] });
    },
    onError: (err: any) => setActionError(err.response?.data?.detail || err.message || 'Failed to reject document.'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.deleteDocument(id),
    onSuccess: () => {
      setActionSuccess('Document deleted successfully.');
      setDeleteTarget(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documentsSummary'] });
    },
    onError: (err: any) => setActionError(err.response?.data?.detail || 'Failed to delete document.'),
  });

  if (isAccountant) {
    return (
      <div className="p-6">
        <ErrorState title="Access Denied" message="Accountant role does not have document management permissions." />
      </div>
    );
  }

  const formatCategoryLabel = (cat: string) => {
    return DOCUMENT_CATEGORIES.find((c) => c.value === cat)?.label || cat;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-ink">Private Document Vault</h1>
          <p className="text-sm text-ink-muted">
            Secure, encrypted document management for Students & Staff with strict RBAC & tenant isolation.
          </p>
        </div>
        <button
          onClick={() => setIsUploadModalOpen(true)}
          className="flex items-center gap-2 bg-brand text-paper px-4 py-2 rounded font-medium hover:bg-brand-dark transition text-sm shadow-sm"
        >
          <Upload className="w-4 h-4" /> Upload Document
        </button>
      </div>

      {actionError && <Alert type="error" title="Error" onClose={() => setActionError(null)}>{actionError}</Alert>}
      {actionSuccess && <Alert type="success" title="Success" onClose={() => setActionSuccess(null)}>{actionSuccess}</Alert>}

      {/* Summary Metric Cards */}
      {summaryData && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-ink-muted font-mono uppercase">Total Vault</div>
            <div className="text-2xl font-bold text-ink mt-1">{summaryData.total_documents}</div>
          </Card>
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-amber-600 font-mono uppercase">Pending Review</div>
            <div className="text-2xl font-bold text-amber-600 mt-1">{summaryData.uploaded_count}</div>
          </Card>
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-emerald-600 font-mono uppercase">Verified</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{summaryData.verified_count}</div>
          </Card>
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-rose-600 font-mono uppercase">Rejected</div>
            <div className="text-2xl font-bold text-rose-600 mt-1">{summaryData.rejected_count}</div>
          </Card>
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-sky-600 font-mono uppercase">Student Docs</div>
            <div className="text-2xl font-bold text-sky-600 mt-1">{summaryData.student_documents_count}</div>
          </Card>
          <Card className="p-4 bg-paper dark:bg-stone-900 border-divider">
            <div className="text-xs text-purple-600 font-mono uppercase">Staff Docs</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">{summaryData.staff_documents_count}</div>
          </Card>
        </div>
      )}

      {/* Toolbar & Filters */}
      <Card className="p-4 bg-paper dark:bg-stone-900 border-divider flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1 text-ink-muted font-mono uppercase">
            <Filter className="w-3.5 h-3.5" /> Filters:
          </div>
          <select
            className="border border-divider rounded px-3 py-1.5 bg-paper text-ink"
            value={selectedOwnerType}
            onChange={(e) => { setSelectedOwnerType(e.target.value); setPage(1); }}
          >
            <option value="">All Owner Types</option>
            <option value="STUDENT">Student Documents</option>
            <option value="STAFF">Staff Documents</option>
          </select>

          <select
            className="border border-divider rounded px-3 py-1.5 bg-paper text-ink"
            value={selectedStatus}
            onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
          >
            <option value="">All Statuses</option>
            <option value="UPLOADED">Uploaded / Pending</option>
            <option value="VERIFIED">Verified</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <select
            className="border border-divider rounded px-3 py-1.5 bg-paper text-ink"
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
          >
            <option value="">All Categories</option>
            {DOCUMENT_CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>

        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 text-xs text-ink-muted hover:text-ink transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </Card>

      {/* Main Document Table */}
      <Card className="p-0 overflow-hidden bg-paper border-divider">
        {isLoading ? (
          <div className="p-12 text-center text-sm text-ink-muted font-mono animate-pulse">
            Loading private document vault...
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorState title="Error Loading Vault" message="Could not retrieve documents. Please check permissions." />
          </div>
        ) : !documentsData?.items.length ? (
          <div className="p-12 text-center text-sm text-ink-muted space-y-2">
            <FileText className="w-8 h-8 mx-auto text-ink-muted opacity-40" />
            <div>No documents found matching the selected filters.</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-canvas dark:bg-stone-900 border-b border-divider font-mono uppercase text-ink-muted text-[11px]">
                <tr>
                  <th className="px-4 py-3">Document Title</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Owner</th>
                  <th className="px-4 py-3">Uploaded By</th>
                  <th className="px-4 py-3">Size / Ver</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-divider">
                {documentsData.items.map((doc) => (
                  <tr key={doc.id} className="hover:bg-canvas/50 transition">
                    <td className="px-4 py-3">
                      <div className="font-medium text-ink flex items-center gap-2">
                        <FileText className="w-4 h-4 text-brand flex-shrink-0" />
                        <div>
                          <div>{doc.title}</div>
                          <div className="text-[10px] font-mono text-ink-muted">{doc.original_filename}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <Badge variant="default" className="text-[10px]">
                        {formatCategoryLabel(doc.document_type)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <div className="text-ink font-sans">{doc.owner_name || 'Owner'}</div>
                      <div className="text-[10px] text-ink-muted">{doc.owner_type}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-ink-muted">
                      <div>{doc.uploaded_by_name}</div>
                      <div className="text-[10px]">{new Date(doc.uploaded_at).toLocaleDateString()}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-ink-muted">
                      <div>{formatFileSize(doc.file_size)}</div>
                      <div className="text-[10px]">v{doc.version}</div>
                    </td>
                    <td className="px-4 py-3">
                      {doc.status === 'VERIFIED' && (
                        <Badge variant="success" className="text-[10px]">VERIFIED</Badge>
                      )}
                      {doc.status === 'UPLOADED' && (
                        <Badge variant="warning" className="text-[10px]">PENDING</Badge>
                      )}
                      {doc.status === 'REJECTED' && (
                        <div>
                          <Badge variant="error" className="text-[10px]">REJECTED</Badge>
                          {doc.rejection_reason && (
                            <div className="text-[10px] text-rose-600 max-w-xs truncate" title={doc.rejection_reason}>
                              {doc.rejection_reason}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setActiveDocument(doc);
                            setIsPreviewModalOpen(true);
                          }}
                          title="Preview Document"
                          className="p-1 text-ink-muted hover:text-brand transition"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => documentsApi.downloadDocument(doc.id, doc.original_filename)}
                          title="Download Document"
                          className="p-1 text-ink-muted hover:text-emerald-600 transition"
                        >
                          <Download className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => {
                            setActiveDocument(doc);
                            setIsReplaceModalOpen(true);
                          }}
                          title="Replace Document (New Version)"
                          className="p-1 text-ink-muted hover:text-amber-600 transition"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>

                        {canVerify && doc.status === 'UPLOADED' && (
                          <>
                            <button
                              onClick={() => verifyMutation.mutate(doc.id)}
                              title="Verify Document"
                              className="p-1 text-emerald-600 hover:text-emerald-700 transition"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                setActiveDocument(doc);
                                setIsRejectModalOpen(true);
                              }}
                              title="Reject Document"
                              className="p-1 text-rose-600 hover:text-rose-700 transition"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </>
                        )}

                        {canDelete && (
                          <button
                            onClick={() => setDeleteTarget(doc)}
                            title="Delete Document"
                            className="p-1 text-ink-muted hover:text-rose-600 transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Upload Document Modal */}
      {isUploadModalOpen && (
        <Modal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          title="Upload Private Document"
        >
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">Owner Type *</label>
              <select
                className="w-full border border-divider p-2 rounded bg-paper"
                value={uploadForm.owner_type}
                onChange={(e) =>
                  setUploadForm({ ...uploadForm, owner_type: e.target.value, owner_id: '' })
                }
              >
                <option value="STUDENT">Student Document</option>
                <option value="STAFF">Staff / Teacher Document</option>
              </select>
            </div>

            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">
                Select {uploadForm.owner_type === 'STUDENT' ? 'Student' : 'Staff Member'} *
              </label>
              <select
                className="w-full border border-divider p-2 rounded bg-paper"
                value={uploadForm.owner_id}
                onChange={(e) => setUploadForm({ ...uploadForm, owner_id: e.target.value })}
              >
                <option value="">-- Choose Owner --</option>
                {uploadForm.owner_type === 'STUDENT'
                  ? studentsList?.items.map((st: Student) => (
                      <option key={st.id} value={st.id}>
                        {st.first_name} {st.last_name} ({st.admission_number})
                      </option>
                    ))
                  : teachersList?.items.map((t: Teacher) => (
                      <option key={t.id} value={t.id}>
                        {t.first_name} {t.last_name} ({t.employee_id})
                      </option>
                    ))}
              </select>
            </div>

            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">Document Category *</label>
              <select
                className="w-full border border-divider p-2 rounded bg-paper"
                value={uploadForm.document_type}
                onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value })}
              >
                {DOCUMENT_CATEGORIES.filter(
                  (c) => c.owner === 'BOTH' || c.owner === uploadForm.owner_type
                ).map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">Document Title *</label>
              <input
                type="text"
                className="w-full border border-divider p-2 rounded bg-paper"
                placeholder="e.g. Birth Certificate Copy 2026"
                value={uploadForm.title}
                onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
              />
            </div>

            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">
                Select File (PDF, JPG, PNG, WEBP — Max 10MB) *
              </label>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                className="w-full text-xs border border-divider p-2 rounded bg-paper"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="px-4 py-2 border border-divider rounded hover:bg-canvas transition"
              >
                Cancel
              </button>
              <button
                onClick={() => uploadMutation.mutate()}
                disabled={uploadMutation.isPending}
                className="px-4 py-2 bg-brand text-paper rounded hover:bg-brand-dark transition font-medium"
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload Document'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Replace Document Modal */}
      {isReplaceModalOpen && activeDocument && (
        <Modal
          isOpen={isReplaceModalOpen}
          onClose={() => setIsReplaceModalOpen(false)}
          title={`Replace Document — ${activeDocument.title}`}
        >
          <div className="space-y-4 text-xs">
            <p className="text-ink-muted">
              Uploading a new file will increment the document version to <strong>v{activeDocument.version + 1}</strong>.
            </p>

            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">
                Select New File (PDF, JPG, PNG, WEBP — Max 10MB) *
              </label>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                className="w-full text-xs border border-divider p-2 rounded bg-paper"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                onClick={() => setIsReplaceModalOpen(false)}
                className="px-4 py-2 border border-divider rounded hover:bg-canvas transition"
              >
                Cancel
              </button>
              <button
                onClick={() => replaceMutation.mutate()}
                disabled={replaceMutation.isPending}
                className="px-4 py-2 bg-brand text-paper rounded hover:bg-brand-dark transition font-medium"
              >
                {replaceMutation.isPending ? 'Replacing...' : 'Upload New Version'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reject Modal */}
      {isRejectModalOpen && activeDocument && (
        <Modal
          isOpen={isRejectModalOpen}
          onClose={() => setIsRejectModalOpen(false)}
          title={`Reject Document — ${activeDocument.title}`}
        >
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-mono uppercase text-ink-muted text-[11px] block mb-1">Rejection Reason *</label>
              <textarea
                rows={3}
                className="w-full border border-divider p-2 rounded bg-paper"
                placeholder="Explain why this document was rejected (e.g. Document image is blurry)..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsRejectModalOpen(false)}
                className="px-4 py-2 border border-divider rounded hover:bg-canvas transition"
              >
                Cancel
              </button>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={rejectMutation.isPending}
                className="px-4 py-2 bg-rose-600 text-paper rounded hover:bg-rose-700 transition font-medium"
              >
                {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* In-Browser Preview Modal */}
      {isPreviewModalOpen && activeDocument && (
        <Modal
          isOpen={isPreviewModalOpen}
          onClose={() => setIsPreviewModalOpen(false)}
          title={`Preview — ${activeDocument.title}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-2 bg-canvas rounded border border-divider flex items-center justify-between font-mono text-[11px]">
              <div>
                <span>MIME: {activeDocument.mime_type}</span> | <span>Size: {formatFileSize(activeDocument.file_size)}</span>
              </div>
              <button
                onClick={() => documentsApi.downloadDocument(activeDocument.id, activeDocument.original_filename)}
                className="flex items-center gap-1 text-brand hover:underline font-sans"
              >
                <Download className="w-3.5 h-3.5" /> Download Original
              </button>
            </div>

            {activeDocument.mime_type.startsWith('image/') ? (
              <div className="max-h-96 overflow-auto flex justify-center bg-black/5 p-4 rounded">
                <img
                  src={documentsApi.getPreviewUrl(activeDocument.id)}
                  alt={activeDocument.title}
                  className="max-h-80 object-contain rounded shadow"
                />
              </div>
            ) : activeDocument.mime_type === 'application/pdf' ? (
              <iframe
                src={documentsApi.getPreviewUrl(activeDocument.id)}
                title={activeDocument.title}
                className="w-full h-96 border border-divider rounded"
              />
            ) : (
              <div className="p-8 text-center text-ink-muted">
                Preview not available in-browser for this format. Please download the file to view.
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          isOpen={Boolean(deleteTarget)}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          title="Delete Private Document"
          message={`Are you sure you want to soft-delete '${deleteTarget.title}'? The file will be archived.`}
          confirmText="Delete"
        />
      )}
    </div>
  );
};
