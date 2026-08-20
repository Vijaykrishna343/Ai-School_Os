import { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  ShieldAlert,
  Activity,
  CheckCircle,
  Clock,
  ExternalLink,
  Search,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { schoolsApi } from '@/services/api/schoolsApi';
import { School } from '@/types/models';


export const PlatformDashboard = () => {
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchSchools();
  }, []);

  const fetchSchools = async () => {
    try {
      setLoading(true);
      const data = await schoolsApi.getAll({ page: 1, page_size: 50 });
      setSchools(data.items || []);
    } catch (err) {
      console.error('Failed to fetch schools for platform dashboard', err);
    } finally {
      setLoading(false);
    }
  };


  const activeSchools = schools.filter((s) => s.status === 'ACTIVE').length;
  const suspendedSchools = schools.filter((s) => s.status === 'SUSPENDED' || s.status === 'BLOCKED').length;
  const trialSchools = schools.filter((s) => s.status === 'TRIAL').length;

  const filteredSchools = schools.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.code.toLowerCase().includes(searchTerm.toLowerCase())
  );


  return (
    <div className="space-y-6">
      {/* Platform Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-3xl border border-indigo-900/50 shadow-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-indigo-300 text-xs font-semibold mb-2">
            <Activity className="w-3.5 h-3.5" /> Level 1 — Platform Command Center
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Super Admin Platform Overview</h1>
          <p className="text-sm text-slate-400 mt-1">Multi-tenant infrastructure health, school licensing, and platform metrics.</p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="primary" onClick={() => window.location.href = '/app/schools'}>
            Manage All Schools
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-5 flex items-center gap-4 border border-slate-200 dark:border-slate-800">
          <div className="p-3 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-2xl">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">{schools.length}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Total Registered Schools</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-4 border border-slate-200 dark:border-slate-800">
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 rounded-2xl">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">{activeSchools}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Active Tenant Licenses</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-4 border border-slate-200 dark:border-slate-800">
          <div className="p-3 bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 rounded-2xl">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">{trialSchools}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Trial Period Tenants</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-4 border border-slate-200 dark:border-slate-800">
          <div className="p-3 bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 rounded-2xl">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">{suspendedSchools}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Suspended / Blocked</div>
          </div>
        </Card>
      </div>

      {/* Quick Search & Tenant Table */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Tenant Schools Directory</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Inspect multi-tenant status, tier allocations, and access status.</p>
          </div>

          <div className="relative w-full md:w-72">
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
          <div className="p-8 text-center text-sm text-slate-500">Loading platform tenant data...</div>
        ) : filteredSchools.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">No schools found matching search criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 font-semibold">School Name</th>
                  <th className="py-3 px-4 font-semibold">Code</th>
                  <th className="py-3 px-4 font-semibold">City / State</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Tier</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {filteredSchools.map((school) => (
                  <tr key={school.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{school.name}</td>
                    <td className="py-3 px-4 font-mono">{school.code}</td>
                    <td className="py-3 px-4">{school.city || school.address || '—'}</td>
                    <td className="py-3 px-4">
                      <Badge variant={school.status === 'ACTIVE' ? 'success' : school.status === 'SUSPENDED' ? 'error' : 'warning'}>
                        {school.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-semibold text-indigo-600 dark:text-indigo-400">{school.subscription_tier || 'STANDARD'}</td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.location.href = `/app/schools?id=${school.id}`}
                        rightIcon={<ExternalLink className="w-3 h-3" />}
                      >
                        Inspect Tenant
                      </Button>

                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
