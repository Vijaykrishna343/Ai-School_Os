import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { schoolsApi } from '@/services/api/schoolsApi';
import { School, SchoolUpdate, SchoolStatus } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export const SettingsPage: React.FC = () => {
  const { user: currentUser, permissions } = useAuthStore();
  const hasPerm = (p: string) => permissions.includes(p);

  const schoolId = currentUser?.school_id;

  // Alerts
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const clearMessages = () => { setErrorMessage(null); setSuccessMessage(null); };

  // Fetch School Profile
  const {
    data: schoolData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['schoolProfile', schoolId],
    queryFn: () => schoolsApi.getSchool(schoolId!),
    enabled: !!schoolId && hasPerm('school.view'),
  });

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState<SchoolUpdate>({
    name: '',
    code: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    status: 'ACTIVE',
  });

  const openEditModal = (school: School) => {
    setEditForm({
      name: school.name,
      code: school.code,
      address: school.address || '',
      phone: school.phone || '',
      email: school.email || '',
      website: school.website || '',
      status: school.status,
    });
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schoolId) return;
    clearMessages();
    try {
      await schoolsApi.updateSchool(schoolId, {
        name: editForm.name || undefined,
        code: editForm.code || undefined,
        address: editForm.address || undefined,
        phone: editForm.phone || undefined,
        email: editForm.email || undefined,
        website: editForm.website || undefined,
        status: editForm.status || undefined,
      });

      setSuccessMessage('School profile updated successfully.');
      setIsEditModalOpen(false);
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update school profile.');
    }
  };

  const statusBadge = (s: SchoolStatus) => {
    if (s === 'ACTIVE') return <Badge variant="success">ACTIVE</Badge>;
    if (s === 'INACTIVE') return <Badge variant="warning">INACTIVE</Badge>;
    return <Badge variant="default">SUSPENDED</Badge>;
  };

  if (!schoolId) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <Alert type="error" title="Configuration Error">
          No active school ID found for current user session.
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            SYSTEM ADMINISTRATION
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            School Profile & Institutional Settings
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            View and manage institutional profile details, contact information, and operational status.
          </p>
        </div>

        {schoolData && hasPerm('school.update') && (
          <Button onClick={() => openEditModal(schoolData)}>
            Edit Profile
          </Button>
        )}
      </div>

      {/* Alerts */}
      {errorMessage && <Alert type="error" title="Update Failure">{errorMessage}</Alert>}
      {successMessage && <Alert type="success">{successMessage}</Alert>}

      {/* Query Error */}
      {isError && (
        <Alert type="error" title="Failed to load school profile">
          {(error as any)?.message || 'An error occurred while fetching school profile details.'}
          <Button variant="secondary" onClick={() => refetch()} className="ml-2">Retry</Button>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white border border-slate-200 dark:border-slate-800 p-8 rounded-none text-center">
          <p className="text-xs text-slate-400 font-mono">Loading school profile details...</p>
        </div>
      )}

      {/* Profile Card */}
      {schoolData && (
        <div className="bg-white border border-slate-200 dark:border-slate-800 p-6 rounded-none space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400">INSTITUTION_NAME</span>
              <h2 className="text-xl font-bold text-slate-800 font-serif">{schoolData.name}</h2>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">SCHOOL_CODE</span>
                <span className="text-xs font-mono font-bold text-brand-500">{schoolData.code}</span>
              </div>
              {statusBadge(schoolData.status)}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="space-y-4">
              <div>
                <span className="block text-[10px] font-mono uppercase text-slate-400 mb-0.5">Physical Address</span>
                <p className="text-slate-700 font-medium">{schoolData.address || '—'}</p>
              </div>

              <div>
                <span className="block text-[10px] font-mono uppercase text-slate-400 mb-0.5">Phone Contact</span>
                <p className="text-slate-700 font-mono">{schoolData.phone || '—'}</p>
              </div>

              <div>
                <span className="block text-[10px] font-mono uppercase text-slate-400 mb-0.5">Email Address</span>
                <p className="text-slate-700 font-mono">{schoolData.email || '—'}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <span className="block text-[10px] font-mono uppercase text-slate-400 mb-0.5">Website</span>
                <p className="text-slate-700 font-mono">
                  {schoolData.website ? (
                    <a href={schoolData.website} target="_blank" rel="noreferrer" className="text-brand-500 underline">
                      {schoolData.website}
                    </a>
                  ) : (
                    '—'
                  )}
                </p>
              </div>

              <div>
                <span className="block text-[10px] font-mono uppercase text-slate-400 mb-0.5">System Registration</span>
                <p className="text-slate-500 font-mono text-[11px]">
                  Created: {new Date(schoolData.created_at).toLocaleString()}
                </p>
                <p className="text-slate-500 font-mono text-[11px]">
                  Last Updated: {new Date(schoolData.updated_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================= */}
      {/* EDIT MODAL */}
      {/* ============================================================= */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="EDIT INSTITUTIONAL PROFILE">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="School Name *"
            value={editForm.name || ''}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            required
          />
          <Input
            label="School Code *"
            value={editForm.code || ''}
            onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
            required
          />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Status *</label>
            <select
              value={editForm.status || 'ACTIVE'}
              onChange={(e) => setEditForm({ ...editForm, status: e.target.value as SchoolStatus })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
          <Input
            label="Physical Address"
            value={editForm.address || ''}
            onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
          />
          <Input
            label="Phone Number"
            value={editForm.phone || ''}
            onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
          />
          <Input
            label="Email Address"
            type="email"
            value={editForm.email || ''}
            onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
          />
          <Input
            label="Website URL"
            value={editForm.website || ''}
            onChange={(e) => setEditForm({ ...editForm, website: e.target.value })}
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Changes</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
