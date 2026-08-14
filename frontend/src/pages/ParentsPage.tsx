import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { parentsApi } from '@/services/api';
import { Parent, ParentCreate, ParentUpdate } from '@/types/models';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, Column } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';

export const ParentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');

  const [isParentModalOpen, setIsParentModalOpen] = useState(false);
  const [editingParent, setEditingParent] = useState<Parent | null>(null);
  const [viewingParent, setViewingParent] = useState<Parent | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Parent | null>(null);

  const [parentForm, setParentForm] = useState<Partial<ParentCreate>>({
    father_name: '',
    mother_name: '',
    guardian_name: '',
    relationship: 'FATHER',
    primary_phone: '',
    secondary_phone: '',
    email: '',
    occupation: '',
    address_line1: '',
    city: '',
    district: '',
    state: '',
    postal_code: '110001',
  });

  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const { data: parentsData, isLoading: isParentsLoading } = useQuery({
    queryKey: ['parents', page, pageSize, search],
    queryFn: () => parentsApi.getParents({ page, page_size: pageSize, search: search || undefined }),
  });

  // Mutations
  const createParentMutation = useMutation({
    mutationFn: (data: ParentCreate) => parentsApi.createParent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      setIsParentModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to create parent record.'),
  });

  const updateParentMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ParentUpdate }) => parentsApi.updateParent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      setIsParentModalOpen(false);
    },
    onError: (err: any) => setFormError(err.message || 'Failed to update parent record.'),
  });

  const deleteParentMutation = useMutation({
    mutationFn: (id: string) => parentsApi.deleteParent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      setDeleteTarget(null);
    },
  });

  const handleOpenCreateModal = () => {
    setFormError(null);
    setEditingParent(null);
    setParentForm({
      school_id: user?.school_id || '',
      father_name: '',
      mother_name: '',
      guardian_name: '',
      relationship: 'FATHER',
      primary_phone: '',
      secondary_phone: '',
      email: '',
      occupation: '',
      address_line1: '123 Street',
      city: 'Delhi',
      district: 'Central',
      state: 'Delhi',
      postal_code: '110001',
    });
    setIsParentModalOpen(true);
  };

  const handleOpenEditModal = (parent: Parent) => {
    setFormError(null);
    setEditingParent(parent);
    setParentForm({
      father_name: parent.father_name || '',
      mother_name: parent.mother_name || '',
      guardian_name: parent.guardian_name || '',
      relationship: parent.relationship,
      primary_phone: parent.primary_phone,
      secondary_phone: parent.secondary_phone || '',
      email: parent.email || '',
      occupation: parent.occupation || '',
      address_line1: parent.address_line1,
      city: parent.city,
      district: parent.district,
      state: parent.state,
      postal_code: parent.postal_code,
    });
    setIsParentModalOpen(true);
  };

  const handleSubmitParent = () => {
    setFormError(null);
    if (editingParent) {
      updateParentMutation.mutate({
        id: editingParent.id,
        data: parentForm,
      });
    } else {
      createParentMutation.mutate(parentForm as ParentCreate);
    }
  };

  const columns: Column<Parent>[] = [
    {
      key: 'name',
      header: 'Parent / Guardian',
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">
            {row.father_name || row.mother_name || row.guardian_name}
          </p>
          {row.mother_name && row.father_name && (
            <p className="text-xs text-slate-400">Mother: {row.mother_name}</p>
          )}
        </div>
      ),
    },
    {
      key: 'primary_phone',
      header: 'Primary Phone',
      render: (row) => <span className="font-mono text-xs text-slate-700 dark:text-slate-300">{row.primary_phone}</span>,
    },
    {
      key: 'city',
      header: 'City & State',
      render: (row) => <span className="text-xs">{row.city}, {row.state}</span>,
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.is_active ? 'success' : 'default'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setViewingParent(row)}>
            Details
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

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8]">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            OFFICE OF THE REGISTRAR
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Guardian Directory
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Directory of parents and guardians linked to enrolled student profiles.
          </p>
        </div>
        <Button onClick={handleOpenCreateModal}>+ Add Parent / Guardian</Button>
      </div>

      <div className="p-4 border border-slate-200 dark:border-slate-800 bg-white rounded-none">
        <Input
          placeholder="Search by parent name or phone number..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      <div className="border border-slate-200 dark:border-slate-800 bg-white p-4 space-y-4 rounded-none">
        <Table
          columns={columns}
          data={parentsData?.items || []}
          isLoading={isParentsLoading}
          emptyText="No parents found matching search criteria."
        />
        {parentsData && (
          <Pagination
            page={parentsData.page}
            totalPages={parentsData.total_pages}
            totalItems={parentsData.total}
            pageSize={parentsData.page_size}
            onPageChange={(p) => setPage(p)}
          />
        )}
      </div>

      {/* Parent Create/Edit Modal */}
      <Modal
        isOpen={isParentModalOpen}
        onClose={() => setIsParentModalOpen(false)}
        title={editingParent ? 'Edit Parent Profile' : 'Add New Parent / Guardian'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsParentModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitParent}
              isLoading={createParentMutation.isPending || updateParentMutation.isPending}
            >
              {editingParent ? 'Save Changes' : 'Create Parent'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          {formError && <Alert type="error" title="Error">{formError}</Alert>}

          <Input
            label="Father's Name *"
            value={parentForm.father_name || ''}
            onChange={(e) => setParentForm({ ...parentForm, father_name: e.target.value })}
            required
          />

          <Input
            label="Mother's Name (Optional)"
            value={parentForm.mother_name || ''}
            onChange={(e) => setParentForm({ ...parentForm, mother_name: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Primary Phone Number *"
              value={parentForm.primary_phone || ''}
              onChange={(e) => setParentForm({ ...parentForm, primary_phone: e.target.value })}
              required
            />
            <Input
              label="Secondary Phone (Optional)"
              value={parentForm.secondary_phone || ''}
              onChange={(e) => setParentForm({ ...parentForm, secondary_phone: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Email (Optional)"
              value={parentForm.email || ''}
              onChange={(e) => setParentForm({ ...parentForm, email: e.target.value })}
            />
            <Input
              label="Occupation (Optional)"
              value={parentForm.occupation || ''}
              onChange={(e) => setParentForm({ ...parentForm, occupation: e.target.value })}
            />
          </div>

          <Input
            label="Address Line 1 *"
            value={parentForm.address_line1 || ''}
            onChange={(e) => setParentForm({ ...parentForm, address_line1: e.target.value })}
            required
          />

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="City *"
              value={parentForm.city || ''}
              onChange={(e) => setParentForm({ ...parentForm, city: e.target.value })}
              required
            />
            <Input
              label="District *"
              value={parentForm.district || ''}
              onChange={(e) => setParentForm({ ...parentForm, district: e.target.value })}
              required
            />
            <Input
              label="State *"
              value={parentForm.state || ''}
              onChange={(e) => setParentForm({ ...parentForm, state: e.target.value })}
              required
            />
          </div>
        </div>
      </Modal>

      {/* Viewing Parent Modal */}
      <Modal
        isOpen={!!viewingParent}
        onClose={() => setViewingParent(null)}
        title="Parent Details"
        footer={<Button variant="outline" onClick={() => setViewingParent(null)}>Close</Button>}
      >
        {viewingParent && (
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg space-y-1">
              <p><span className="font-semibold text-slate-500">Father Name:</span> {viewingParent.father_name}</p>
              {viewingParent.mother_name && <p><span className="font-semibold text-slate-500">Mother Name:</span> {viewingParent.mother_name}</p>}
              <p><span className="font-semibold text-slate-500">Primary Phone:</span> {viewingParent.primary_phone}</p>
              <p><span className="font-semibold text-slate-500">Address:</span> {viewingParent.address_line1}, {viewingParent.city}, {viewingParent.state} - {viewingParent.postal_code}</p>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteParentMutation.mutate(deleteTarget.id)}
        title={`Soft Delete Parent Profile`}
        message={`Are you sure you want to delete parent "${deleteTarget?.father_name}"?`}
        isLoading={deleteParentMutation.isPending}
      />
    </div>
  );
};
