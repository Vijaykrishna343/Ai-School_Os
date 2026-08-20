import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { usersApi } from '@/services/api/usersApi';
import { rolesApi } from '@/services/api/rolesApi';
import { userRolesApi } from '@/services/api/userRolesApi';
import { User, UserCreate, UserUpdate, Role } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';

export const UsersPage: React.FC = () => {
  const { user: currentUser, permissions } = useAuthStore();
  const hasPerm = (p: string) => permissions.includes(p);

  // Filters & Pagination
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Alerts
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const clearMessages = () => { setErrorMessage(null); setSuccessMessage(null); };

  // Fetch Users
  const {
    data: usersData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['usersList', currentUser?.school_id, statusFilter, page, searchQuery],
    queryFn: () =>
      usersApi.getUsers({
        school_id: currentUser?.school_id,
        is_active: statusFilter === 'ALL' ? undefined : statusFilter === 'ACTIVE',
        page,
        page_size: pageSize,
      }),
  });

  // Fetch All Roles for role assignment
  const { data: allRoles } = useQuery({
    queryKey: ['allSchoolRoles', currentUser?.school_id],
    queryFn: () => rolesApi.getRoles({ school_id: currentUser?.school_id }),
    enabled: hasPerm('user_role.assign') || hasPerm('user.view'),
  });

  // Create User Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState<Omit<UserCreate, 'school_id'>>({
    email: '',
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
  });

  // Edit User Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState<UserUpdate>({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    phone: '',
    is_active: true,
  });

  // Manage Roles Modal
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [selectedUserForRoles, setSelectedUserForRoles] = useState<User | null>(null);
  const [userRoleIds, setUserRoleIds] = useState<string[]>([]);
  const [isRolesLoading, setIsRolesLoading] = useState(false);

  // Handlers
  const openCreateModal = () => {
    setCreateForm({
      email: '',
      username: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
    });
    setIsCreateModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser?.school_id) return;
    clearMessages();
    try {
      await usersApi.createUser({
        school_id: currentUser.school_id,
        email: createForm.email,
        username: createForm.username || null,
        password: createForm.password,
        first_name: createForm.first_name,
        last_name: createForm.last_name || null,
        phone: createForm.phone || null,
      });
      setSuccessMessage('User account created successfully.');
      setIsCreateModalOpen(false);
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create user.');
    }
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setEditForm({
      email: user.email,
      username: user.username || '',
      first_name: user.first_name,
      last_name: user.last_name || '',
      phone: user.phone || '',
      is_active: user.is_active,
    });
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    clearMessages();
    try {
      await usersApi.updateUser(editingUser.id, {
        email: editForm.email,
        username: editForm.username || null,
        first_name: editForm.first_name,
        last_name: editForm.last_name || null,
        phone: editForm.phone || null,
        is_active: editForm.is_active,
      });
      setSuccessMessage('User updated successfully.');
      setIsEditModalOpen(false);
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update user.');
    }
  };

  const handleDeleteUser = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    clearMessages();
    try {
      await usersApi.deleteUser(id);
      setSuccessMessage('User deleted successfully.');
      refetch();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete user.');
    }
  };

  // Roles modal open
  const openRoleModal = async (user: User) => {
    setSelectedUserForRoles(user);
    setIsRoleModalOpen(true);
    setIsRolesLoading(true);
    try {
      const roles: Role[] = await userRolesApi.getUserRoles(user.id);
      setUserRoleIds(roles.map((r) => r.id));
    } catch (err: any) {
      setErrorMessage('Failed to fetch user assigned roles.');
    } finally {
      setIsRolesLoading(false);
    }
  };

  const handleToggleRole = async (roleId: string) => {
    if (!selectedUserForRoles) return;
    clearMessages();
    const isAssigned = userRoleIds.includes(roleId);
    try {
      if (isAssigned) {
        await userRolesApi.removeRole(selectedUserForRoles.id, roleId);
        setUserRoleIds((prev) => prev.filter((id) => id !== roleId));
      } else {
        await userRolesApi.assignRole(selectedUserForRoles.id, roleId);
        setUserRoleIds((prev) => [...prev, roleId]);
      }
      setSuccessMessage('User roles updated successfully.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update role assignment.');
    }
  };

  // Filtered display data
  const filteredUsers = (usersData?.items || []).filter((u) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      u.email.toLowerCase().includes(q) ||
      (u.username && u.username.toLowerCase().includes(q)) ||
      u.first_name.toLowerCase().includes(q) ||
      (u.last_name && u.last_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
          IDENTITY & ACCESS MANAGEMENT
        </p>
        <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
          User Management & Staff Accounts
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage system user accounts, credentials, active status, and security role assignments.
        </p>
      </div>

      {/* Alerts */}
      {errorMessage && <Alert type="error" title="User Operation Error">{errorMessage}</Alert>}
      {successMessage && <Alert type="success">{successMessage}</Alert>}

      {/* Filter & Action Toolbar */}
      <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-3">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Input
              type="text"
              placeholder="Search by name, email, or username..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-xs w-full sm:w-64"
            />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any);
                setPage(1);
              }}
              className="px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
            >
              <option value="ALL">All Status</option>
              <option value="ACTIVE">Active Only</option>
              <option value="INACTIVE">Inactive Only</option>
            </select>
          </div>

          {hasPerm('user.create') && (
            <Button onClick={openCreateModal}>+ Create User</Button>
          )}
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none space-y-4">
        {isError && (
          <Alert type="error" title="Failed to load users">
            {(error as any)?.message || 'An error occurred while fetching users.'}
            <Button variant="secondary" onClick={() => refetch()} className="ml-2">Retry</Button>
          </Alert>
        )}

        <Table
          columns={[
            {
              key: 'name',
              header: 'Full Name',
              className: 'font-semibold text-xs',
              render: (u: User) => `${u.first_name} ${u.last_name || ''}`,
            },
            {
              key: 'email',
              header: 'Email / Username',
              render: (u: User) => (
                <div className="text-xs">
                  <div className="font-mono text-slate-700">{u.email}</div>
                  {u.username && <div className="text-[10px] text-slate-400">@{u.username}</div>}
                </div>
              ),
            },
            {
              key: 'phone',
              header: 'Phone',
              render: (u: User) => <span className="text-xs font-mono">{u.phone || '—'}</span>,
            },
            {
              key: 'status',
              header: 'Status',
              render: (u: User) =>
                u.is_active ? <Badge variant="success">ACTIVE</Badge> : <Badge variant="warning">INACTIVE</Badge>,
            },
            {
              key: 'actions',
              header: 'Actions',
              render: (u: User) => (
                <div className="flex items-center gap-2">
                  {hasPerm('user_role.assign') && (
                    <Button variant="secondary" onClick={() => openRoleModal(u)}>
                      Roles
                    </Button>
                  )}
                  {hasPerm('user.update') && (
                    <Button variant="secondary" onClick={() => openEditModal(u)}>
                      Edit
                    </Button>
                  )}
                  {hasPerm('user.delete') && (
                    <Button variant="secondary" onClick={() => handleDeleteUser(u.id)}>
                      Delete
                    </Button>
                  )}
                </div>
              ),
            },
          ]}
          data={filteredUsers}
          emptyText={isLoading ? 'Loading users...' : 'No users found matching the criteria.'}
        />

        {/* Pagination Footer */}
        {usersData && usersData.total_pages > 1 && (
          <div className="flex items-center justify-between pt-2 text-xs font-mono text-slate-500">
            <span>Page {usersData.page} of {usersData.total_pages} ({usersData.total} total)</span>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={page >= usersData.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* ============================================================= */}
      {/* MODALS */}
      {/* ============================================================= */}

      {/* Create User Modal */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="CREATE USER ACCOUNT">
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <Input
            label="Email Address *"
            type="email"
            value={createForm.email}
            onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
            required
            placeholder="user@school.com"
          />
          <Input
            label="Username (Optional)"
            value={createForm.username || ''}
            onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
            placeholder="john_doe"
          />
          <Input
            label="Password *"
            type="password"
            value={createForm.password}
            onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
            required
            minLength={8}
            placeholder="Minimum 8 characters"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name *"
              value={createForm.first_name}
              onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
              required
            />
            <Input
              label="Last Name"
              value={createForm.last_name || ''}
              onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
            />
          </div>
          <Input
            label="Phone Number"
            value={createForm.phone || ''}
            onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
            placeholder="+1234567890"
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create User</Button>
          </div>
        </form>
      </Modal>

      {/* Edit User Modal */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="EDIT USER ACCOUNT">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Email Address *"
            type="email"
            value={editForm.email || ''}
            onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
            required
          />
          <Input
            label="Username"
            value={editForm.username || ''}
            onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name *"
              value={editForm.first_name || ''}
              onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
              required
            />
            <Input
              label="Last Name"
              value={editForm.last_name || ''}
              onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
            />
          </div>
          <Input
            label="Phone Number"
            value={editForm.phone || ''}
            onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
          />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Status</label>
            <select
              value={editForm.is_active ? 'ACTIVE' : 'INACTIVE'}
              onChange={(e) => setEditForm({ ...editForm, is_active: e.target.value === 'ACTIVE' })}
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Changes</Button>
          </div>
        </form>
      </Modal>

      {/* Manage Roles Modal */}
      <Modal
        isOpen={isRoleModalOpen}
        onClose={() => setIsRoleModalOpen(false)}
        title={`MANAGE ROLES — ${selectedUserForRoles?.first_name.toUpperCase()} ${selectedUserForRoles?.last_name?.toUpperCase() || ''}`}
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-500">
            Select the security roles assigned to this user account:
          </p>

          {isRolesLoading ? (
            <p className="text-slate-400 py-4 text-center">Loading assigned roles...</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto border border-slate-200 p-3">
              {allRoles?.map((role) => {
                const isChecked = userRoleIds.includes(role.id);
                return (
                  <label
                    key={role.id}
                    className="flex items-center justify-between p-2 rounded-sm hover:bg-slate-50 border border-slate-100 cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleRole(role.id)}
                        className="rounded border-slate-300 text-brand-500 focus:ring-brand-500"
                      />
                      <span className="font-semibold text-slate-800">{role.name}</span>
                      {role.is_system && <Badge variant="default">SYSTEM</Badge>}
                    </div>
                    <span className="text-[10px] text-slate-400">{role.description || 'No description'}</span>
                  </label>
                );
              })}
              {allRoles?.length === 0 && <p className="text-slate-400 text-center py-2">No roles found.</p>}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button variant="secondary" onClick={() => setIsRoleModalOpen(false)}>
              Done
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
