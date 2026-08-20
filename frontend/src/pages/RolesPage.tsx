import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { rolesApi } from '@/services/api/rolesApi';
import { permissionsApi } from '@/services/api/permissionsApi';
import { rolePermissionsApi } from '@/services/api/rolePermissionsApi';
import { Role, RoleCreate, RoleUpdate, Permission } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export const RolesPage: React.FC = () => {
  const { user: currentUser, permissions: userPermissions } = useAuthStore();
  const hasPerm = (p: string) => userPermissions.includes(p);

  // Search filter
  const [searchQuery, setSearchQuery] = useState('');

  // Alerts
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const clearMessages = () => { setErrorMessage(null); setSuccessMessage(null); };

  // Fetch Roles
  const {
    data: rolesData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['rolesList', currentUser?.school_id],
    queryFn: () => rolesApi.getRoles({ school_id: currentUser?.school_id }),
  });

  // Fetch All System Permissions
  const { data: allPermissions } = useQuery({
    queryKey: ['allSystemPermissions'],
    queryFn: () => permissionsApi.getPermissions(),
    enabled: hasPerm('role.view'),
  });

  // Create Role Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState<RoleCreate>({
    name: '',
    description: '',
  });

  // Edit Role Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [editForm, setEditForm] = useState<RoleUpdate>({
    name: '',
    description: '',
  });

  // Permission Matrix Drawer / Modal
  const [isMatrixOpen, setIsMatrixOpen] = useState(false);
  const [selectedRoleForMatrix, setSelectedRoleForMatrix] = useState<Role | null>(null);
  const [assignedPermissionIds, setAssignedPermissionIds] = useState<string[]>([]);
  const [isMatrixLoading, setIsMatrixLoading] = useState(false);

  // Group permissions by module
  const groupedPermissions = useMemo(() => {
    const map: Record<string, Permission[]> = {};
    if (allPermissions) {
      allPermissions.forEach((p) => {
        const mod = p.module || 'general';
        if (!map[mod]) map[mod] = [];
        map[mod].push(p);
      });
    }
    return map;
  }, [allPermissions]);

  // Handlers
  const openCreateModal = () => {
    setCreateForm({ name: '', description: '' });
    setIsCreateModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    try {
      await rolesApi.createRole({
        school_id: currentUser?.school_id,
        name: createForm.name,
        description: createForm.description || null,
      });
      setSuccessMessage('Custom role created successfully.');
      setIsCreateModalOpen(false);
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create role.');
    }
  };

  const openEditModal = (role: Role) => {
    if (role.is_system) {
      setErrorMessage('System roles cannot be modified.');
      return;
    }
    setEditingRole(role);
    setEditForm({
      name: role.name,
      description: role.description || '',
    });
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRole) return;
    clearMessages();
    try {
      await rolesApi.updateRole(editingRole.id, {
        name: editForm.name,
        description: editForm.description || null,
      });
      setSuccessMessage('Role updated successfully.');
      setIsEditModalOpen(false);
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update role.');
    }
  };

  const handleDeleteRole = async (role: Role) => {
    if (role.is_system) {
      setErrorMessage('System roles cannot be deleted.');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete custom role "${role.name}"?`)) return;
    clearMessages();
    try {
      await rolesApi.deleteRole(role.id);
      setSuccessMessage('Role deleted successfully.');
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete role.');
    }
  };

  // Open Permission Matrix
  const openPermissionMatrix = async (role: Role) => {
    setSelectedRoleForMatrix(role);
    setIsMatrixOpen(true);
    setIsMatrixLoading(true);
    try {
      const perms: Permission[] = await rolePermissionsApi.getRolePermissions(role.id);
      setAssignedPermissionIds(perms.map((p) => p.id));
    } catch (err: any) {
      setErrorMessage('Failed to load role permissions.');
    } finally {
      setIsMatrixLoading(false);
    }
  };

  // Toggle individual permission on a role (Strictly using backend individual assign/remove endpoints)
  const handleTogglePermission = async (permissionId: string) => {
    if (!selectedRoleForMatrix) return;
    if (selectedRoleForMatrix.is_system) {
      setErrorMessage('System role permissions are read-only.');
      return;
    }
    clearMessages();
    const isAssigned = assignedPermissionIds.includes(permissionId);
    try {
      if (isAssigned) {
        await rolePermissionsApi.removePermission(selectedRoleForMatrix.id, permissionId);
        setAssignedPermissionIds((prev) => prev.filter((id) => id !== permissionId));
      } else {
        await rolePermissionsApi.assignPermission(selectedRoleForMatrix.id, permissionId);
        setAssignedPermissionIds((prev) => [...prev, permissionId]);
      }
      setSuccessMessage('Permission assignment updated.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update permission assignment.');
    }
  };

  // Filter display
  const filteredRoles = (rolesData || []).filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return r.name.toLowerCase().includes(q) || (r.description && r.description.toLowerCase().includes(q));
  });

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
          IDENTITY & ACCESS MANAGEMENT
        </p>
        <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
          Role & Access Control Configuration
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure security roles, inspect platform system roles, and assign fine-grained permissions.
        </p>
      </div>

      {/* Alerts */}
      {errorMessage && <Alert type="error" title="Role Operation Error">{errorMessage}</Alert>}
      {successMessage && <Alert type="success">{successMessage}</Alert>}

      {/* Toolbar */}
      <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none flex flex-col sm:flex-row items-center justify-between gap-3">
        <Input
          type="text"
          placeholder="Search roles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="text-xs w-full sm:w-64"
        />

        {hasPerm('role.create') && (
          <Button onClick={openCreateModal}>+ Create Custom Role</Button>
        )}
      </div>

      {/* Roles Table */}
      <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-4">
        {isError && (
          <Alert type="error" title="Failed to load roles">
            {(error as any)?.message || 'An error occurred while fetching roles.'}
            <Button variant="secondary" onClick={() => refetch()} className="ml-2">Retry</Button>
          </Alert>
        )}

        <Table
          columns={[
            {
              key: 'name',
              header: 'Role Name',
              className: 'font-semibold text-xs',
              render: (r: Role) => (
                <div className="flex items-center gap-2">
                  <span>{r.name}</span>
                  {r.is_system ? <Badge variant="default">SYSTEM</Badge> : <Badge variant="success">CUSTOM</Badge>}
                </div>
              ),
            },
            {
              key: 'description',
              header: 'Description',
              render: (r: Role) => <span className="text-xs text-slate-600">{r.description || '—'}</span>,
            },
            {
              key: 'type',
              header: 'Role Scope',
              render: (r: Role) => (
                <span className="text-[10px] font-mono uppercase text-slate-500">
                  {r.is_system ? 'Platform Global' : 'School Specific'}
                </span>
              ),
            },
            {
              key: 'actions',
              header: 'Actions',
              render: (r: Role) => (
                <div className="flex items-center gap-2">
                  <Button variant="secondary" onClick={() => openPermissionMatrix(r)}>
                    {r.is_system ? 'View Matrix' : 'Permissions'}
                  </Button>
                  {!r.is_system && hasPerm('role.update') && (
                    <Button variant="secondary" onClick={() => openEditModal(r)}>
                      Edit
                    </Button>
                  )}
                  {!r.is_system && hasPerm('role.delete') && (
                    <Button variant="secondary" onClick={() => handleDeleteRole(r)}>
                      Delete
                    </Button>
                  )}
                </div>
              ),
            },
          ]}
          data={filteredRoles}
          emptyText={isLoading ? 'Loading roles...' : 'No roles found.'}
        />
      </div>

      {/* ============================================================= */}
      {/* MODALS */}
      {/* ============================================================= */}

      {/* Create Role Modal */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="CREATE CUSTOM ROLE">
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <Input
            label="Role Name *"
            value={createForm.name}
            onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            required
            placeholder="e.g., Exam Coordinator"
          />
          <Input
            label="Description"
            value={createForm.description || ''}
            onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
            placeholder="Description of role responsibilities"
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Role</Button>
          </div>
        </form>
      </Modal>

      {/* Edit Role Modal */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="EDIT CUSTOM ROLE">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Role Name *"
            value={editForm.name || ''}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            required
          />
          <Input
            label="Description"
            value={editForm.description || ''}
            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Changes</Button>
          </div>
        </form>
      </Modal>

      {/* Permission Matrix Drawer / Modal */}
      <Modal
        isOpen={isMatrixOpen}
        onClose={() => setIsMatrixOpen(false)}
        title={`PERMISSION MATRIX — ${selectedRoleForMatrix?.name.toUpperCase()} ${selectedRoleForMatrix?.is_system ? '(READ-ONLY SYSTEM ROLE)' : ''}`}
      >
        <div className="space-y-4 text-xs">
          {selectedRoleForMatrix?.is_system && (
            <Alert type="info">
              System roles are platform built-ins. Permissions for system roles are read-only.
            </Alert>
          )}

          {isMatrixLoading ? (
            <p className="text-slate-400 py-6 text-center">Loading permission matrix...</p>
          ) : (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto border border-slate-200 p-3 bg-slate-50/50">
              {Object.keys(groupedPermissions).sort().map((moduleName) => (
                <div key={moduleName} className="bg-white border border-slate-200 p-3 rounded-none space-y-2">
                  <div className="font-mono text-[11px] font-bold uppercase text-brand-500 border-b border-slate-100 pb-1 flex justify-between items-center">
                    <span>MODULE: {moduleName}</span>
                    <span className="text-[9px] text-slate-400 font-normal">
                      {groupedPermissions[moduleName].filter((p) => assignedPermissionIds.includes(p.id)).length} / {groupedPermissions[moduleName].length} granted
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {groupedPermissions[moduleName].map((perm) => {
                      const isChecked = assignedPermissionIds.includes(perm.id);
                      return (
                        <label
                          key={perm.id}
                          className={`flex items-start gap-2 p-1.5 rounded-sm border ${
                            isChecked ? 'border-brand-500/30 bg-brand-500/5' : 'border-slate-100 bg-white'
                          } ${selectedRoleForMatrix?.is_system ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            disabled={selectedRoleForMatrix?.is_system}
                            onChange={() => handleTogglePermission(perm.id)}
                            className="mt-0.5 rounded border-slate-300 text-brand-500 focus:ring-brand-500"
                          />
                          <div>
                            <div className="font-mono text-[10px] font-semibold text-slate-800">{perm.name}</div>
                            <div className="text-[9px] text-slate-400">{perm.description || perm.action}</div>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}

              {Object.keys(groupedPermissions).length === 0 && (
                <p className="text-slate-400 text-center py-4">No system permissions loaded.</p>
              )}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button variant="secondary" onClick={() => setIsMatrixOpen(false)}>
              Close Matrix
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
