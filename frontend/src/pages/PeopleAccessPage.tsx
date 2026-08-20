import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Search,
  UserPlus,
  Shield,
  UserCheck,
  UserX,
  Lock,
  Mail,
  Phone,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { usersApi } from '@/services/api/usersApi';
import { rolesApi } from '@/services/api/rolesApi';
import { userRolesApi } from '@/services/api/userRolesApi';
import { User, Role } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';

export const PeopleAccessPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modals
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [isRolesModalOpen, setIsRolesModalOpen] = useState(false);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);

  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // User form
  const [userForm, setUserForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
  });

  // Status form
  const [statusForm, setStatusForm] = useState({
    status: 'ACTIVE',
    suspension_reason: '',
  });

  // User roles selection
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [isUpdatingRoles, setIsUpdatingRoles] = useState(false);

  // Queries
  const { data: usersResponse, isLoading: isUsersLoading, refetch: refetchUsers } = useQuery({
    queryKey: ['peopleAccessUsers', currentUser?.school_id, statusFilter, searchTerm],
    queryFn: () => usersApi.getUsers({ page: 1, page_size: 100 }),
  });

  const { data: allRolesResponse } = useQuery({
    queryKey: ['peopleAccessRoles', currentUser?.school_id],
    queryFn: () => rolesApi.getRoles({ page: 1, page_size: 100 }),
  });

  const users: User[] = usersResponse?.items || [];
  const roles: Role[] = Array.isArray(allRolesResponse) ? allRolesResponse : (allRolesResponse as any)?.items || [];


  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await usersApi.createUser({
        ...userForm,
        username: userForm.email.split('@')[0],
      });
      setIsAddUserOpen(false);
      setUserForm({ first_name: '', last_name: '', email: '', phone: '', password: '' });
      refetchUsers();
    } catch (err) {
      console.error('Failed to create user', err);
    }
  };

  const handleOpenRolesModal = async (u: User) => {
    setSelectedUser(u);
    try {
      const assigned = await userRolesApi.getUserRoles(u.id);
      setSelectedRoleIds(assigned.map((r) => r.id));
    } catch (err) {
      console.error('Failed to load user roles', err);
      setSelectedRoleIds([]);
    }
    setIsRolesModalOpen(true);
  };

  const handleSaveRoles = async () => {
    if (!selectedUser) return;
    try {
      setIsUpdatingRoles(true);
      const currentAssigned = await userRolesApi.getUserRoles(selectedUser.id);
      const currentRoleIds = currentAssigned.map((r) => r.id);

      // Add missing roles
      for (const roleId of selectedRoleIds) {
        if (!currentRoleIds.includes(roleId)) {
          await userRolesApi.assignUserRole(selectedUser.id, roleId);
        }
      }

      // Remove unselected roles
      for (const roleId of currentRoleIds) {
        if (!selectedRoleIds.includes(roleId)) {
          await userRolesApi.removeUserRole(selectedUser.id, roleId);
        }
      }

      setIsRolesModalOpen(false);
      setSelectedUser(null);
      refetchUsers();
    } catch (err) {
      console.error('Failed to update user roles', err);
    } finally {
      setIsUpdatingRoles(false);
    }
  };

  const handleUpdateUserStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await usersApi.updateUserStatus(selectedUser.id, statusForm.status, statusForm.suspension_reason);
      setIsStatusModalOpen(false);
      setSelectedUser(null);
      refetchUsers();
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || u.status === statusFilter || (statusFilter === 'ACTIVE' && u.is_active);
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Users className="w-7 h-7 text-indigo-600 dark:text-indigo-400" /> People & Access Directory
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage school staff, teachers, administrators, user statuses, and role assignments cleanly.
          </p>
        </div>

        <Button variant="primary" onClick={() => setIsAddUserOpen(true)} leftIcon={<UserPlus className="w-4 h-4" />}>
          Add New User
        </Button>
      </div>

      {/* Directory Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>
        </div>

        {isUsersLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading school user directory...</div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">No school users match your filter.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 font-semibold">User Details</th>
                  <th className="py-3 px-4 font-semibold">Contact Email</th>
                  <th className="py-3 px-4 font-semibold">Assigned Roles</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">
                      {u.first_name} {u.last_name}
                    </td>
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-400">{u.email}</td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {u.roles && u.roles.length > 0 ? (
                          u.roles.map((r) => (
                            <Badge key={r.id} variant="info" className="text-[10px]">
                              {r.name}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-slate-400 italic">No roles assigned</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={u.status === 'SUSPENDED' ? 'error' : u.is_active ? 'success' : 'warning'}>
                        {u.status || (u.is_active ? 'ACTIVE' : 'INACTIVE')}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenRolesModal(u)}
                        leftIcon={<Shield className="w-3 h-3" />}
                      >
                        Roles
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedUser(u);
                          setStatusForm({ status: u.status || 'ACTIVE', suspension_reason: u.suspension_reason || '' });
                          setIsStatusModalOpen(true);
                        }}
                        leftIcon={<UserCheck className="w-3 h-3" />}
                      >
                        Status
                      </Button>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add User Modal */}
      <Modal isOpen={isAddUserOpen} onClose={() => setIsAddUserOpen(false)} title="Create New School User">
        <form onSubmit={handleCreateUser} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">First Name *</label>
              <input
                type="text"
                required
                value={userForm.first_name}
                onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Last Name</label>
              <input
                type="text"
                value={userForm.last_name}
                onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address *</label>
            <input
              type="email"
              required
              value={userForm.email}
              onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Password *</label>
            <input
              type="password"
              required
              value={userForm.password}
              onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" type="button" onClick={() => setIsAddUserOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Create User</Button>
          </div>
        </form>
      </Modal>

      {/* Role Assignment Modal */}
      <Modal isOpen={isRolesModalOpen} onClose={() => setIsRolesModalOpen(false)} title={`Assign Roles — ${selectedUser?.first_name} ${selectedUser?.last_name}`}>
        <div className="space-y-4">
          <p className="text-xs text-slate-500">Select roles to grant this user authorization within the school:</p>
          <div className="space-y-2 max-h-60 overflow-y-auto p-1">
            {roles
              .filter((r) => r.name !== 'Super Admin') // Exclude Super Admin from School Admin view
              .map((r) => (
                <label key={r.id} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl cursor-pointer hover:bg-indigo-50/50">
                  <input
                    type="checkbox"
                    checked={selectedRoleIds.includes(r.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedRoleIds([...selectedRoleIds, r.id]);
                      } else {
                        setSelectedRoleIds(selectedRoleIds.filter((id) => id !== r.id));
                      }
                    }}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div>
                    <div className="text-xs font-semibold text-slate-900 dark:text-white">{r.name}</div>
                    <div className="text-[11px] text-slate-500">{r.description || 'Standard role'}</div>
                  </div>
                </label>
              ))}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" onClick={() => setIsRolesModalOpen(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleSaveRoles} isLoading={isUpdatingRoles}>Save Roles</Button>
          </div>
        </div>
      </Modal>

      {/* Status Modal */}
      <Modal isOpen={isStatusModalOpen} onClose={() => setIsStatusModalOpen(false)} title={`User Status — ${selectedUser?.first_name} ${selectedUser?.last_name}`}>
        <form onSubmit={handleUpdateUserStatus} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Status</label>
            <select
              value={statusForm.status}
              onChange={(e) => setStatusForm({ ...statusForm, status: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>

          {statusForm.status === 'SUSPENDED' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Suspension Reason</label>
              <textarea
                rows={3}
                value={statusForm.suspension_reason}
                onChange={(e) => setStatusForm({ ...statusForm, suspension_reason: e.target.value })}
                placeholder="Specify reason for suspending user..."
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" type="button" onClick={() => setIsStatusModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Status</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
