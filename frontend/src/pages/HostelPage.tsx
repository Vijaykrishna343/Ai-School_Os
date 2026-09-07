import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { hostelApi, HostelBuilding, HostelRoom, HostelOutpass } from '@/api/hostel';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Building, Home, Bed, UserCheck, ShieldAlert, LogOut, DollarSign, Calendar, Plus, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

export function HostelPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'buildings' | 'outpasses' | 'fees'>('dashboard');

  // Modal states
  const [isBldgModalOpen, setIsBldgModalOpen] = useState(false);
  const [newBldg, setNewBldg] = useState({ name: '', code: '', gender_designation: 'BOYS', capacity: 100 });

  const [isOutpassModalOpen, setIsOutpassModalOpen] = useState(false);
  const [newOutpass, setNewOutpass] = useState({ student_id: '', reason: '', destination: '', departure_time: '', expected_return_time: '' });

  // Queries
  const { data: metrics, isLoading: isMetricsLoading, isError: isMetricsError } = useQuery({
    queryKey: ['hostel-dashboard'],
    queryFn: hostelApi.getDashboard,
  });

  const { data: buildings = [], isLoading: isBldgsLoading } = useQuery({
    queryKey: ['hostel-buildings'],
    queryFn: hostelApi.getBuildings,
    enabled: activeTab === 'buildings',
  });

  const { data: outpasses = [], isLoading: isOutpassesLoading } = useQuery({
    queryKey: ['hostel-outpasses'],
    queryFn: () => hostelApi.getOutpasses(),
    enabled: activeTab === 'outpasses',
  });

  const { data: feeStructures = [] } = useQuery({
    queryKey: ['hostel-fee-structures'],
    queryFn: () => hostelApi.getFeeStructures(),
    enabled: activeTab === 'fees',
  });

  // Mutations
  const createBldgMutation = useMutation({
    mutationFn: hostelApi.createBuilding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hostel-buildings'] });
      queryClient.invalidateQueries({ queryKey: ['hostel-dashboard'] });
      setIsBldgModalOpen(false);
      setNewBldg({ name: '', code: '', gender_designation: 'BOYS', capacity: 100 });
    },
  });

  const createOutpassMutation = useMutation({
    mutationFn: hostelApi.createOutpass,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hostel-outpasses'] });
      queryClient.invalidateQueries({ queryKey: ['hostel-dashboard'] });
      setIsOutpassModalOpen(false);
    },
  });

  const approveOutpassMutation = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) => hostelApi.approveOutpass(id, approve),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hostel-outpasses'] });
      queryClient.invalidateQueries({ queryKey: ['hostel-dashboard'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Building className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Hostel Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage hostel blocks, rooms, bed allocations, night roll call, outpass gate passes, and boarding fees.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'buildings' && (
            <Button onClick={() => setIsBldgModalOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" /> Add Building Block
            </Button>
          )}
          {activeTab === 'outpasses' && (
            <Button onClick={() => setIsOutpassModalOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" /> Request Outpass
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`pb-3 font-medium text-sm border-b-2 flex items-center gap-2 ${
            activeTab === 'dashboard'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Home className="h-4 w-4" /> Dashboard Overview
        </button>
        <button
          onClick={() => setActiveTab('buildings')}
          className={`pb-3 font-medium text-sm border-b-2 flex items-center gap-2 ${
            activeTab === 'buildings'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Building className="h-4 w-4" /> Buildings & Rooms
        </button>
        <button
          onClick={() => setActiveTab('outpasses')}
          className={`pb-3 font-medium text-sm border-b-2 flex items-center gap-2 ${
            activeTab === 'outpasses'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <LogOut className="h-4 w-4" /> Outpass Requests
        </button>
        <button
          onClick={() => setActiveTab('fees')}
          className={`pb-3 font-medium text-sm border-b-2 flex items-center gap-2 ${
            activeTab === 'fees'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <DollarSign className="h-4 w-4" /> Hostel Fees
        </button>
      </div>

      {/* DASHBOARD TAB */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {isMetricsLoading ? (
            <div className="p-12 text-center text-slate-500">Loading hostel metrics...</div>
          ) : isMetricsError ? (
            <div className="p-6 bg-red-50 text-red-700 rounded-lg">Failed to load hostel metrics.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Hostel Buildings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.total_hostels || 0}</div>
                  <p className="text-xs text-slate-400 mt-1">{metrics?.total_rooms || 0} Total Rooms</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Occupancy Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.occupancy_percentage || 0}%</div>
                  <p className="text-xs text-slate-400 mt-1">
                    {metrics?.occupied_beds || 0} / {metrics?.total_beds || 0} Beds Occupied
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Night Roll Call</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-600">{metrics?.today_present_count || 0}</div>
                  <p className="text-xs text-slate-400 mt-1">Students Checked Present Today</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Pending Outpasses</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-amber-600">{metrics?.pending_outpasses || 0}</div>
                  <p className="text-xs text-slate-400 mt-1">{metrics?.checked_out_students || 0} Students Currently Out</p>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* BUILDINGS TAB */}
      {activeTab === 'buildings' && (
        <div className="space-y-4">
          {isBldgsLoading ? (
            <div className="p-8 text-center text-slate-500">Loading buildings...</div>
          ) : buildings.length === 0 ? (
            <div className="p-12 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
              <Building className="h-10 w-10 text-slate-400 mx-auto mb-3" />
              <h3 className="font-semibold text-slate-700 dark:text-slate-300">No Hostel Buildings Found</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">Create your first hostel building block to begin assigning rooms and beds.</p>
              <Button onClick={() => setIsBldgModalOpen(true)}>Add Hostel Building</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {buildings.map((bldg) => (
                <Card key={bldg.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{bldg.name}</CardTitle>
                      <span className="text-xs text-slate-400 font-mono">{bldg.code}</span>
                    </div>
                    <Badge variant={bldg.gender_designation === 'GIRLS' ? 'info' : 'default'}>
                      {bldg.gender_designation}
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                      {bldg.description || 'No description provided.'}
                    </p>
                    <div className="flex justify-between items-center text-xs text-slate-500 border-t pt-3 border-slate-100 dark:border-slate-800">
                      <span>Max Capacity: {bldg.capacity}</span>
                      <span className={bldg.is_active ? 'text-emerald-600' : 'text-slate-400'}>
                        {bldg.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* OUTPASSES TAB */}
      {activeTab === 'outpasses' && (
        <div className="space-y-4">
          {isOutpassesLoading ? (
            <div className="p-8 text-center text-slate-500">Loading outpass requests...</div>
          ) : outpasses.length === 0 ? (
            <div className="p-12 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
              <LogOut className="h-10 w-10 text-slate-400 mx-auto mb-3" />
              <h3 className="font-semibold text-slate-700 dark:text-slate-300">No Outpass Requests</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">There are currently no active or historical outpass requests.</p>
              <Button onClick={() => setIsOutpassModalOpen(true)}>Request Outpass</Button>
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-lg">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-medium border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="p-3">Destination</th>
                    <th className="p-3">Reason</th>
                    <th className="p-3">Departure</th>
                    <th className="p-3">Expected Return</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {outpasses.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/50">
                      <td className="p-3 font-medium text-slate-900 dark:text-white">{o.destination}</td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{o.reason}</td>
                      <td className="p-3 text-xs text-slate-500">{new Date(o.departure_time).toLocaleString()}</td>
                      <td className="p-3 text-xs text-slate-500">{new Date(o.expected_return_time).toLocaleString()}</td>
                      <td className="p-3">
                        <Badge
                          variant={
                            o.status === 'APPROVED'
                              ? 'success'
                              : o.status === 'PENDING'
                              ? 'warning'
                              : o.status === 'REJECTED'
                              ? 'error'
                              : 'neutral'
                          }
                        >
                          {o.status}
                        </Badge>
                      </td>
                      <td className="p-3 text-right space-x-2">
                        {o.status === 'PENDING' && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-emerald-600 hover:text-emerald-700"
                              onClick={() => approveOutpassMutation.mutate({ id: o.id, approve: true })}
                            >
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => approveOutpassMutation.mutate({ id: o.id, approve: false })}
                            >
                              Reject
                            </Button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* FEES TAB */}
      {activeTab === 'fees' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {feeStructures.map((f) => (
              <Card key={f.id}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{f.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                    ${f.amount.toLocaleString()}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{f.description || 'Hostel boarding & lodging structure'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ADD BUILDING MODAL */}
      <Modal isOpen={isBldgModalOpen} onClose={() => setIsBldgModalOpen(false)} title="Add Hostel Building">
        <div className="space-y-4 p-4">
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Building Name</label>
            <Input
              value={newBldg.name}
              onChange={(e) => setNewBldg({ ...newBldg, name: e.target.value })}
              placeholder="e.g. Senior Boys Hostel"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Building Code</label>
            <Input
              value={newBldg.code}
              onChange={(e) => setNewBldg({ ...newBldg, code: e.target.value })}
              placeholder="e.g. SBH-01"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Gender Designation</label>
            <select
              value={newBldg.gender_designation}
              onChange={(e) => setNewBldg({ ...newBldg, gender_designation: e.target.value })}
              className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
            >
              <option value="BOYS">Boys Hostel</option>
              <option value="GIRLS">Girls Hostel</option>
              <option value="COED">Co-Ed Hostel</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsBldgModalOpen(false)}>Cancel</Button>
            <Button onClick={() => createBldgMutation.mutate(newBldg)} disabled={!newBldg.name || !newBldg.code}>
              Save Building
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
