import { useState, useEffect } from 'react';
import {
  Building2,
  Plus,
  Search,
  ShieldCheck,
  ShieldAlert,
  Edit,
  Sliders,
  CheckCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { schoolsApi } from '@/services/api/schoolsApi';
import { School } from '@/types/models';

export const SchoolsPage = () => {
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isStatusOpen, setIsStatusOpen] = useState(false);
  const [isSubOpen, setIsSubOpen] = useState(false);

  const [selectedSchool, setSelectedSchool] = useState<School | null>(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    name: '',
    code: '',
    email: '',
    phone: '',
    address_line1: '',
    city: '',
    district: '',
    state: '',
    postal_code: '',
  });

  const [statusForm, setStatusForm] = useState({
    status: 'ACTIVE',
    suspension_reason: '',
  });

  const [subForm, setSubForm] = useState({
    subscription_tier: 'STANDARD',
    max_students: 500,
    max_teachers: 50,
  });

  useEffect(() => {
    fetchSchools();
  }, []);

  const fetchSchools = async () => {
    try {
      setLoading(true);
      const res = await schoolsApi.getAll({ page: 1, page_size: 100 });
      setSchools(res.items || []);
    } catch (err) {
      console.error('Failed to load schools', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schoolsApi.createSchool(createForm);
      setIsCreateOpen(false);
      setCreateForm({
        name: '', code: '', email: '', phone: '',
        address_line1: '', city: '', district: '', state: '', postal_code: '',
      });
      fetchSchools();
    } catch (err) {
      console.error('Create school error', err);
    }
  };

  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSchool) return;
    try {
      await schoolsApi.updateStatus(selectedSchool.id, statusForm.status, statusForm.suspension_reason);
      setIsStatusOpen(false);
      setSelectedSchool(null);
      fetchSchools();
    } catch (err) {
      console.error('Status update error', err);
    }
  };

  const handleSubSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSchool) return;
    try {
      await schoolsApi.updateSubscription(selectedSchool.id, subForm);
      setIsSubOpen(false);
      setSelectedSchool(null);
      fetchSchools();
    } catch (err) {
      console.error('Subscription update error', err);
    }
  };

  const filteredSchools = schools.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Building2 className="w-7 h-7 text-indigo-600 dark:text-indigo-400" /> School Tenant Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Super Admin platform management for all multi-tenant schools, statuses, and subscriptions.
          </p>
        </div>

        <Button variant="primary" onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Register New School
        </Button>
      </div>

      {/* Directory Table Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search school name or code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading school directory...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 font-semibold">School Name</th>
                  <th className="py-3 px-4 font-semibold">Code</th>
                  <th className="py-3 px-4 font-semibold">City / State</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Subscription</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {filteredSchools.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{s.name}</td>
                    <td className="py-3 px-4 font-mono">{s.code}</td>
                    <td className="py-3 px-4">{s.city || s.address || '—'}</td>
                    <td className="py-3 px-4">
                      <Badge variant={s.status === 'ACTIVE' ? 'success' : s.status === 'SUSPENDED' ? 'error' : 'warning'}>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-semibold text-indigo-600 dark:text-indigo-400">{s.subscription_tier || 'STANDARD'}</td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedSchool(s);
                          setStatusForm({ status: s.status, suspension_reason: s.suspension_reason || '' });
                          setIsStatusOpen(true);
                        }}
                        leftIcon={<ShieldCheck className="w-3 h-3" />}
                      >
                        Status
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedSchool(s);
                          setSubForm({
                            subscription_tier: s.subscription_tier || 'STANDARD',
                            max_students: s.max_students || 500,
                            max_teachers: s.max_teachers || 50,
                          });
                          setIsSubOpen(true);
                        }}
                        leftIcon={<Sliders className="w-3 h-3" />}
                      >
                        Licensing
                      </Button>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create School Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Register New School Tenant">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">School Name *</label>
            <input
              type="text"
              required
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">School Code *</label>
              <input
                type="text"
                required
                value={createForm.code}
                onChange={(e) => setCreateForm({ ...createForm, code: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Contact Email</label>
              <input
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">City *</label>
              <input
                type="text"
                required
                value={createForm.city}
                onChange={(e) => setCreateForm({ ...createForm, city: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">District *</label>
              <input
                type="text"
                required
                value={createForm.district}
                onChange={(e) => setCreateForm({ ...createForm, district: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">State *</label>
              <input
                type="text"
                required
                value={createForm.state}
                onChange={(e) => setCreateForm({ ...createForm, state: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Address Line 1 *</label>
            <input
              type="text"
              required
              value={createForm.address_line1}
              onChange={(e) => setCreateForm({ ...createForm, address_line1: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Postal Code *</label>
            <input
              type="text"
              required
              value={createForm.postal_code}
              onChange={(e) => setCreateForm({ ...createForm, postal_code: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" type="button" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Create School</Button>
          </div>
        </form>
      </Modal>

      {/* Update Status Modal */}
      <Modal isOpen={isStatusOpen} onClose={() => setIsStatusOpen(false)} title={`Update Status — ${selectedSchool?.name}`}>
        <form onSubmit={handleStatusSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">School Status</label>
            <select
              value={statusForm.status}
              onChange={(e) => setStatusForm({ ...statusForm, status: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="TRIAL">TRIAL</option>
              <option value="PAYMENT_DUE">PAYMENT_DUE</option>
              <option value="GRACE_PERIOD">GRACE_PERIOD</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="BLOCKED">BLOCKED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          {(statusForm.status === 'SUSPENDED' || statusForm.status === 'BLOCKED') && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Suspension Reason</label>
              <textarea
                rows={3}
                value={statusForm.suspension_reason}
                onChange={(e) => setStatusForm({ ...statusForm, suspension_reason: e.target.value })}
                placeholder="Reason for suspension or blocking..."
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" type="button" onClick={() => setIsStatusOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Status</Button>
          </div>
        </form>
      </Modal>

      {/* Update Subscription Modal */}
      <Modal isOpen={isSubOpen} onClose={() => setIsSubOpen(false)} title={`Licensing & Limits — ${selectedSchool?.name}`}>
        <form onSubmit={handleSubSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Subscription Tier</label>
            <select
              value={subForm.subscription_tier}
              onChange={(e) => setSubForm({ ...subForm, subscription_tier: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold"
            >
              <option value="FREE">FREE</option>
              <option value="BASIC">BASIC</option>
              <option value="STANDARD">STANDARD</option>
              <option value="PREMIUM">PREMIUM</option>
              <option value="ENTERPRISE">ENTERPRISE</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Max Student Quota</label>
              <input
                type="number"
                value={subForm.max_students}
                onChange={(e) => setSubForm({ ...subForm, max_students: parseInt(e.target.value, 10) })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Max Teacher Quota</label>
              <input
                type="number"
                value={subForm.max_teachers}
                onChange={(e) => setSubForm({ ...subForm, max_teachers: parseInt(e.target.value, 10) })}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" type="button" onClick={() => setIsSubOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Update Licensing</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
