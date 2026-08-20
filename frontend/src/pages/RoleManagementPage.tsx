import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Plus, Lock, CheckCircle2, Info, Search } from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { rolesApi } from '@/services/api/rolesApi';
import { permissionsApi } from '@/services/api/permissionsApi';
import { rolePermissionsApi } from '@/services/api/rolePermissionsApi';
import { Role, Permission } from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';

export const RoleManagementPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const [searchTerm, setSearchTerm] = useState('');

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isPermsOpen, setIsPermsOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
  });

  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);
  const [isSavingPerms, setIsSavingPerms] = useState(false);

  const { data: rolesResponse, isLoading: isRolesLoading, refetch: refetchRoles } = useQuery({
    queryKey: ['roleManagementRoles', currentUser?.school_id],
    queryFn: () => rolesApi.getRoles({ page: 1, page_size: 100 }),
  });

  const { data: allPermsResponse } = useQuery({
    queryKey: ['allPermissionsList'],
    queryFn: () => permissionsApi.getPermissions({ page: 1, page_size: 200 }),
  });

  const roles: Role[] = Array.isArray(rolesResponse) ? rolesResponse : (rolesResponse as any)?.items || [];
  const permissions: Permission[] = Array.isArray(allPermsResponse) ? allPermsResponse : (allPermsResponse as any)?.items || [];


  // Group permissions by module
  const groupedPerms = permissions.reduce<Record<string, Permission[]>>((acc, p) => {
    const mod = p.module || 'General';
    if (!acc[mod]) acc[mod] = [];
    acc[mod].push(p);
    return acc;
  }, {});

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await rolesApi.createRole({
        ...createForm,
        school_id: currentUser?.school_id,
        is_system_role: false,
      });
      setIsCreateOpen(false);
      setCreateForm({ name: '', description: '' });
      refetchRoles();
    } catch (err) {
      console.error('Failed to create custom role', err);
    }
  };

  const handleOpenPermsModal = async (role: Role) => {
    setSelectedRole(role);
    try {
      const assigned = await rolePermissionsApi.getRolePermissions(role.id);
      setSelectedPermIds(assigned.map((p) => p.id));
    } catch (err) {
      console.error('Failed to load role permissions', err);
      setSelectedPermIds([]);
    }
    setIsPermsOpen(true);
  };

  const handleSavePerms = async () => {
    if (!selectedRole) return;
    try {
      setIsSavingPerms(true);
      const currentAssigned = await rolePermissionsApi.getRolePermissions(selectedRole.id);
      const currentPermIds = currentAssigned.map((p) => p.id);

      for (const permId of selectedPermIds) {
        if (!currentPermIds.includes(permId)) {
          await rolePermissionsApi.assignRolePermission(selectedRole.id, permId);
        }
      }

      for (const permId of currentPermIds) {
        if (!selectedPermIds.includes(permId)) {
          await rolePermissionsApi.removeRolePermission(selectedRole.id, permId);
        }
      }

      setIsPermsOpen(false);
      setSelectedRole(null);
      refetchRoles();
    } catch (err) {
      console.error('Failed to save permissions', err);
    } finally {
      setIsSavingPerms(false);
    }
  };

  const filteredRoles = roles.filter((r) =>
    r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.description && r.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Shield className="w-7 h-7 text-indigo-600 dark:text-indigo-400" /> Role & Permission Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure system roles and custom school access roles with clear human explanations.
          </p>
        </div>

        <Button variant="primary" onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Create Custom Role
        </Button>
      </div>

      {/* Directory Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search role name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {isRolesLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading roles...</div>
        ) : filteredRoles.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">No matching roles found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRoles.map((role) => (
              <div
                key={role.id}
                className="p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex flex-col justify-between hover:shadow-md transition"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      {role.name}
                      {role.is_system_role && (
                        <span title="System Role — Modification restricted">
                          <Lock className="w-3.5 h-3.5 text-slate-400" />
                        </span>
                      )}
                    </h3>
                    <Badge variant={role.is_system_role ? 'neutral' : 'info'} className="text-[10px]">
                      {role.is_system_role ? 'System Role' : 'Custom Role'}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 line-clamp-2">
                    {role.description || 'Custom access role configured for specific school capabilities.'}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-mono">
                    {role.is_system_role ? 'Core Permission Template' : 'School Specific'}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenPermsModal(role)}
                    disabled={role.is_system || role.is_system_role}
                  >

                    {role.is_system_role ? 'View Permissions' : 'Configure Permissions'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Create Role Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Custom School Role">
        <form onSubmit={handleCreateRole} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Role Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Vice Principal, Lab Assistant"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Human Description</label>
            <textarea
              rows={3}
              placeholder="Describe what staff with this role are responsible for..."
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" type="button" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Create Role</Button>
          </div>
        </form>
      </Modal>

      {/* Configure Permissions Modal */}
      <Modal isOpen={isPermsOpen} onClose={() => setIsPermsOpen(false)} title={`Configure Permissions — ${selectedRole?.name}`}>
        <div className="space-y-4">
          <p className="text-xs text-slate-500">Toggle permissions granted to users assigned this role:</p>

          <div className="max-h-96 overflow-y-auto space-y-4 pr-1">
            {Object.entries(groupedPerms).map(([moduleName, perms]) => (
              <div key={moduleName} className="p-3 bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl">
                <div className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>{moduleName} Module</span>
                  <span className="text-[10px] text-slate-400 font-normal">{perms.length} permissions</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {perms.map((p) => (
                    <label key={p.id} className="flex items-start gap-2.5 p-2 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700/60 rounded-xl cursor-pointer hover:border-indigo-300">
                      <input
                        type="checkbox"
                        checked={selectedPermIds.includes(p.id)}
                        disabled={selectedRole?.is_system_role}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedPermIds([...selectedPermIds, p.id]);
                          } else {
                            setSelectedPermIds(selectedPermIds.filter((id) => id !== p.id));
                          }
                        }}
                        className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <div>
                        <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">{p.name}</div>
                        <div className="text-[10px] text-slate-500">{p.description || p.action}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" onClick={() => setIsPermsOpen(false)}>Cancel</Button>
            {!selectedRole?.is_system_role && (
              <Button variant="primary" onClick={handleSavePerms} isLoading={isSavingPerms}>Save Permissions</Button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};
