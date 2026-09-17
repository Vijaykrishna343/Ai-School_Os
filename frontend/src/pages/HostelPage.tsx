import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { hostelApi, HostelBuilding, HostelRoom, HostelOutpass, HostelFeeAllocation, HostelFeeStructure } from '@/api/hostel';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Building, Home, Bed, UserCheck, ShieldAlert, LogOut, DollarSign, Calendar, Plus, RefreshCw, CheckCircle, XCircle, CreditCard } from 'lucide-react';

export function HostelPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'buildings' | 'outpasses' | 'fees'>('dashboard');

  // Modal states
  const [isBldgModalOpen, setIsBldgModalOpen] = useState(false);
  const [newBldg, setNewBldg] = useState({ name: '', code: '', gender_designation: 'BOYS', capacity: 100 });

  const [isOutpassModalOpen, setIsOutpassModalOpen] = useState(false);
  const [newOutpass, setNewOutpass] = useState({ student_id: '', reason: '', destination: '', departure_time: '', expected_return_time: '' });

  const [isFeeAllocModalOpen, setIsFeeAllocModalOpen] = useState(false);
  const [newFeeAlloc, setNewFeeAlloc] = useState({ student_id: '', fee_structure_id: '', due_date: new Date().toISOString().split('T')[0] });

  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [selectedAllocForPay, setSelectedAllocForPay] = useState<HostelFeeAllocation | null>(null);
  const [paymentForm, setPaymentForm] = useState({ payment_amount: 0, payment_mode: 'CASH', reference_number: '', remarks: '' });

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

  const { data: feeAllocations = [], isLoading: isAllocationsLoading } = useQuery({
    queryKey: ['hostel-fee-allocations'],
    queryFn: () => hostelApi.getFeeAllocations(),
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

  const allocateFeeMutation = useMutation({
    mutationFn: hostelApi.allocateFee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hostel-fee-allocations'] });
      setIsFeeAllocModalOpen(false);
      setNewFeeAlloc({ student_id: '', fee_structure_id: '', due_date: new Date().toISOString().split('T')[0] });
    },
  });

  const payFeeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => hostelApi.payFeeAllocation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hostel-fee-allocations'] });
      setIsPaymentModalOpen(false);
      setSelectedAllocForPay(null);
    },
  });

  const handleOpenPayment = (alloc: HostelFeeAllocation) => {
    const outstanding = Math.max(0, alloc.amount_due - alloc.paid_amount);
    setSelectedAllocForPay(alloc);
    setPaymentForm({
      payment_amount: outstanding,
      payment_mode: 'CASH',
      reference_number: '',
      remarks: '',
    });
    setIsPaymentModalOpen(true);
  };

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
          {activeTab === 'fees' && (
            <Button onClick={() => setIsFeeAllocModalOpen(true)} className="flex items-center gap-2">
              <Plus className="h-4 w-4" /> Allocate Hostel Fee
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
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Total Bed Capacity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.total_beds || 0}</div>
                  <p className="text-xs text-slate-500 mt-1">{metrics?.occupied_beds || 0} Occupied / {metrics?.available_beds || 0} Available</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Occupancy Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.occupancy_percentage || 0}%</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-slate-500">Pending Outpasses</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-amber-600">{metrics?.pending_outpasses || 0}</div>
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
            <div className="p-12 text-center text-slate-500">Loading buildings...</div>
          ) : buildings.length === 0 ? (
            <div className="p-12 text-center border rounded-lg bg-slate-50 dark:bg-slate-900 border-dashed">
              <Building className="mx-auto h-10 w-10 text-slate-400 mb-3" />
              <p className="text-slate-600 dark:text-slate-400 font-medium">No hostel buildings configured yet.</p>
              <Button onClick={() => setIsBldgModalOpen(true)} className="mt-4" size="sm">
                Add First Building Block
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {buildings.map((b) => (
                <Card key={b.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-base font-semibold">{b.name}</CardTitle>
                      <span className="text-xs text-slate-500 font-mono">{b.code}</span>
                    </div>
                    <Badge variant={b.gender_designation === 'BOYS' ? 'default' : b.gender_designation === 'GIRLS' ? 'info' : 'neutral'}>
                      {b.gender_designation}
                    </Badge>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Capacity: <span className="font-semibold text-slate-900 dark:text-white">{b.capacity} Students</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Status: {b.is_active ? <span className="text-emerald-600 font-medium">Active</span> : <span className="text-red-500 font-medium">Inactive</span>}
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
            <div className="p-12 text-center text-slate-500">Loading outpass requests...</div>
          ) : outpasses.length === 0 ? (
            <div className="p-12 text-center border rounded-lg bg-slate-50 dark:bg-slate-900 border-dashed">
              <LogOut className="mx-auto h-10 w-10 text-slate-400 mb-3" />
              <p className="text-slate-600 dark:text-slate-400 font-medium">No outpass requests found.</p>
              <Button onClick={() => setIsOutpassModalOpen(true)} className="mt-4" size="sm">
                Create Outpass Request
              </Button>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-b">
                  <tr>
                    <th className="p-3">Student ID</th>
                    <th className="p-3">Reason</th>
                    <th className="p-3">Destination</th>
                    <th className="p-3">Departure</th>
                    <th className="p-3">Expected Return</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {outpasses.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="p-3 font-mono text-xs">{o.student_id.slice(0, 8)}...</td>
                      <td className="p-3">{o.reason}</td>
                      <td className="p-3">{o.destination}</td>
                      <td className="p-3 text-xs">{new Date(o.departure_time).toLocaleString()}</td>
                      <td className="p-3 text-xs">{new Date(o.expected_return_time).toLocaleString()}</td>
                      <td className="p-3">
                        <Badge
                          variant={
                            o.status === 'APPROVED' ? 'success' : o.status === 'REJECTED' ? 'error' : o.status === 'CHECKED_OUT' ? 'info' : 'warning'
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
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">Hostel Fee Structures</h3>
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

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Student Hostel Fee Allocations & Central Ledger</h3>
            </div>
            {isAllocationsLoading ? (
              <div className="p-12 text-center text-slate-500">Loading fee allocations...</div>
            ) : feeAllocations.length === 0 ? (
              <div className="p-8 text-center border rounded-lg bg-slate-50 dark:bg-slate-900 border-dashed">
                <DollarSign className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">No student hostel fee allocations recorded yet.</p>
                <Button onClick={() => setIsFeeAllocModalOpen(true)} className="mt-3" size="sm">
                  Allocate Hostel Fee to Student
                </Button>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-b">
                    <tr>
                      <th className="p-3">Student ID</th>
                      <th className="p-3">Due Date</th>
                      <th className="p-3">Amount Due</th>
                      <th className="p-3">Paid Amount</th>
                      <th className="p-3">Outstanding</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {feeAllocations.map((a) => {
                      const outstanding = Math.max(0, a.amount_due - a.paid_amount);
                      return (
                        <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                          <td className="p-3 font-mono text-xs">{a.student_id.slice(0, 8)}...</td>
                          <td className="p-3 text-xs">{a.due_date}</td>
                          <td className="p-3 font-semibold">${a.amount_due.toFixed(2)}</td>
                          <td className="p-3 text-emerald-600">${a.paid_amount.toFixed(2)}</td>
                          <td className="p-3 font-medium text-amber-600">${outstanding.toFixed(2)}</td>
                          <td className="p-3">
                            <Badge
                              variant={
                                a.status === 'PAID' ? 'success' : a.status === 'PARTIAL' ? 'warning' : 'neutral'
                              }
                            >
                              {a.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-right">
                            {a.status !== 'PAID' && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-indigo-600 hover:text-indigo-700 flex items-center gap-1 ml-auto"
                                onClick={() => handleOpenPayment(a)}
                              >
                                <CreditCard className="h-3.5 w-3.5" /> Record Payment
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
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

      {/* ALLOCATE FEE MODAL */}
      <Modal isOpen={isFeeAllocModalOpen} onClose={() => setIsFeeAllocModalOpen(false)} title="Allocate Hostel Fee">
        <div className="space-y-4 p-4">
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Student ID (UUID)</label>
            <Input
              value={newFeeAlloc.student_id}
              onChange={(e) => setNewFeeAlloc({ ...newFeeAlloc, student_id: e.target.value })}
              placeholder="Enter student UUID"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Hostel Fee Structure</label>
            <select
              value={newFeeAlloc.fee_structure_id}
              onChange={(e) => setNewFeeAlloc({ ...newFeeAlloc, fee_structure_id: e.target.value })}
              className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
            >
              <option value="">-- Select Fee Structure --</option>
              {feeStructures.map((fs) => (
                <option key={fs.id} value={fs.id}>
                  {fs.name} (${fs.amount})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Due Date</label>
            <Input
              type="date"
              value={newFeeAlloc.due_date}
              onChange={(e) => setNewFeeAlloc({ ...newFeeAlloc, due_date: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsFeeAllocModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => allocateFeeMutation.mutate(newFeeAlloc)}
              disabled={!newFeeAlloc.student_id || !newFeeAlloc.fee_structure_id || !newFeeAlloc.due_date}
            >
              Allocate Fee
            </Button>
          </div>
        </div>
      </Modal>

      {/* RECORD PAYMENT MODAL */}
      <Modal isOpen={isPaymentModalOpen} onClose={() => setIsPaymentModalOpen(false)} title="Record Hostel Fee Payment">
        <div className="space-y-4 p-4">
          {selectedAllocForPay && (
            <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg text-sm space-y-1">
              <div>Total Amount: <span className="font-semibold">${selectedAllocForPay.amount_due.toFixed(2)}</span></div>
              <div>Already Paid: <span className="font-semibold text-emerald-600">${selectedAllocForPay.paid_amount.toFixed(2)}</span></div>
              <div>Remaining Due: <span className="font-semibold text-amber-600">${Math.max(0, selectedAllocForPay.amount_due - selectedAllocForPay.paid_amount).toFixed(2)}</span></div>
            </div>
          )}
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Payment Amount ($)</label>
            <Input
              type="number"
              step="0.01"
              value={paymentForm.payment_amount}
              onChange={(e) => setPaymentForm({ ...paymentForm, payment_amount: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Payment Mode</label>
            <select
              value={paymentForm.payment_mode}
              onChange={(e) => setPaymentForm({ ...paymentForm, payment_mode: e.target.value })}
              className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
            >
              <option value="CASH">Cash</option>
              <option value="CARD">Card</option>
              <option value="UPI">UPI</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHEQUE">Cheque</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Reference Number (Optional)</label>
            <Input
              value={paymentForm.reference_number}
              onChange={(e) => setPaymentForm({ ...paymentForm, reference_number: e.target.value })}
              placeholder="e.g. TXN-123456"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Remarks (Optional)</label>
            <Input
              value={paymentForm.remarks}
              onChange={(e) => setPaymentForm({ ...paymentForm, remarks: e.target.value })}
              placeholder="e.g. Partial boarding installment"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsPaymentModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (selectedAllocForPay) {
                  payFeeMutation.mutate({ id: selectedAllocForPay.id, data: paymentForm });
                }
              }}
              disabled={paymentForm.payment_amount <= 0}
            >
              Record Payment
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
