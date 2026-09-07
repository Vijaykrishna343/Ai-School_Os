import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { staffLeaveApi, StaffLeaveRequest, StaffLeaveBalance, StaffLeaveType } from '@/api/staffLeave';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { useAuthStore } from '@/store/useAuthStore';
import {
  Calendar as CalendarIcon,
  Clock,
  Plus,
  CheckCircle,
  XCircle,
  FileText,
  AlertCircle,
  UserCheck,
  Building2,
  Filter,
} from 'lucide-react';

export function StaffLeavePage() {
  const queryClient = useQueryClient();
  const { permissions, user } = useAuthStore();

  const isApproverOrAdmin = ['School Admin', 'Principal', 'Vice Principal', 'Super Admin'].some((r) =>
    user?.roles?.map((role: any) => typeof role === 'string' ? role : role.name).includes(r)
  ) || permissions.includes('staff_leave.approve') || permissions.includes('staff_leave.manage');

  const [activeTab, setActiveTab] = useState<'my_leave' | 'approvals' | 'policies'>('my_leave');
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<StaffLeaveRequest | null>(null);

  const [actionRemarks, setActionRemarks] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');

  // Form State for New Leave Request
  const [newRequest, setNewRequest] = useState({
    academic_year_id: '',
    leave_type_id: '',
    start_date: '',
    end_date: '',
    half_day_type: 'FULL_DAY',
    reason: '',
    attachment_url: '',
  });

  // Fetch Academic Years
  const { data: academicYearsRes } = useQuery({
    queryKey: ['academic-years'],
    queryFn: () => academicYearsApi.getAcademicYears(),
  });

  const academicYears = Array.isArray(academicYearsRes) ? academicYearsRes : (academicYearsRes?.items || []);
  const currentYear = academicYears.find((ay: any) => ay.is_current) || academicYears[0];
  const yearId = currentYear?.id || '';

  // Queries
  const { data: leaveTypes = [] } = useQuery({
    queryKey: ['staff-leave-types'],
    queryFn: staffLeaveApi.getLeaveTypes,
  });

  const { data: myBalances = [] } = useQuery({
    queryKey: ['my-leave-balances', yearId],
    queryFn: () => staffLeaveApi.getMyBalances(yearId),
    enabled: !!yearId,
  });

  const { data: leaveRequests = [], isLoading } = useQuery({
    queryKey: ['staff-leave-requests', yearId, activeTab],
    queryFn: () => staffLeaveApi.getLeaveRequests(yearId ? { academic_year_id: yearId } : undefined),
    enabled: !!yearId,
  });

  const { data: summaryReport } = useQuery({
    queryKey: ['staff-leave-summary', yearId],
    queryFn: () => staffLeaveApi.getSummaryReport(yearId),
    enabled: !!yearId && isApproverOrAdmin,
  });

  // Mutations
  const createRequestMutation = useMutation({
    mutationFn: staffLeaveApi.createLeaveRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['my-leave-balances'] });
      queryClient.invalidateQueries({ queryKey: ['staff-leave-summary'] });
      setIsApplyModalOpen(false);
      setNewRequest({
        academic_year_id: '',
        leave_type_id: '',
        start_date: '',
        end_date: '',
        half_day_type: 'FULL_DAY',
        reason: '',
        attachment_url: '',
      });
    },
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, remarks }: { id: string; remarks?: string }) =>
      staffLeaveApi.approveLeaveRequest(id, remarks),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['staff-leave-summary'] });
      setIsApproveModalOpen(false);
      setActionRemarks('');
      setSelectedRequest(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      staffLeaveApi.rejectLeaveRequest(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['staff-leave-summary'] });
      setIsRejectModalOpen(false);
      setRejectionReason('');
      setSelectedRequest(null);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => staffLeaveApi.cancelLeaveRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['my-leave-balances'] });
      queryClient.invalidateQueries({ queryKey: ['staff-leave-summary'] });
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <Badge variant="success">APPROVED</Badge>;
      case 'REJECTED':
        return <Badge variant="error">REJECTED</Badge>;
      case 'CANCELLED':
        return <Badge variant="neutral">CANCELLED</Badge>;
      case 'PENDING':
      default:
        return <Badge variant="warning">PENDING</Badge>;
    }
  };

  const handleApplySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRequest.leave_type_id || !newRequest.start_date || !newRequest.end_date || !newRequest.reason) return;
    createRequestMutation.mutate({
      ...newRequest,
      academic_year_id: yearId,
    });
  };

  const pendingRequests = leaveRequests.filter((r) => r.status === 'PENDING');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-divider dark:border-stone-800 pb-4">
        <div>
          <h1 className="text-xl font-semibold text-ink dark:text-stone-100 flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-brand-500" />
            Staff Leave & Approval Workspace
          </h1>
          <p className="text-xs text-ink-muted dark:text-stone-400 mt-1">
            Submit leave applications, track balances, approve pending staff leave, and manage policies.
          </p>
        </div>
        <Button onClick={() => setIsApplyModalOpen(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> Apply for Leave
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-divider dark:border-stone-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('my_leave')}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === 'my_leave'
              ? 'border-brand-500 text-brand-500 font-semibold'
              : 'border-transparent text-ink-muted hover:text-ink dark:hover:text-stone-200'
          }`}
        >
          My Leave & Balances
        </button>
        {isApproverOrAdmin && (
          <button
            onClick={() => setActiveTab('approvals')}
            className={`pb-2 border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'approvals'
                ? 'border-brand-500 text-brand-500 font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink dark:hover:text-stone-200'
            }`}
          >
            Approvals Dashboard
            {pendingRequests.length > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] bg-amber-500 text-white rounded-full font-bold">
                {pendingRequests.length}
              </span>
            )}
          </button>
        )}
        {isApproverOrAdmin && (
          <button
            onClick={() => setActiveTab('policies')}
            className={`pb-2 border-b-2 transition-colors ${
              activeTab === 'policies'
                ? 'border-brand-500 text-brand-500 font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink dark:hover:text-stone-200'
            }`}
          >
            Leave Policies & Quotas
          </button>
        )}
      </div>

      {/* Tab 1: My Leave & Balances */}
      {activeTab === 'my_leave' && (
        <div className="space-y-6">
          {/* Balance Cards */}
          <div>
            <h2 className="text-sm font-semibold text-ink dark:text-stone-200 mb-3">Annual Leave Quota & Remaining Balance</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {myBalances.map((b) => (
                <Card key={b.id} className="p-4 border-l-4 border-l-brand-500">
                  <div className="text-xs font-semibold text-ink-muted uppercase tracking-wider">{b.leave_type_name}</div>
                  <div className="text-2xl font-bold text-ink dark:text-stone-100 mt-1">
                    {b.remaining_days} <span className="text-xs font-normal text-ink-muted">days left</span>
                  </div>
                  <div className="text-[11px] text-ink-muted mt-2 space-y-0.5">
                    <div>Allocated: {b.allocated_days} days</div>
                    <div>Used: {b.used_days} days | Pending: {b.pending_days} days</div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* My Leave Requests Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-divider dark:border-stone-800">
              <CardTitle className="text-sm font-semibold">My Leave History & Requests</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-6 text-center text-xs text-ink-muted">Loading leave requests...</div>
              ) : leaveRequests.length === 0 ? (
                <div className="p-8 text-center text-xs text-ink-muted">No leave requests recorded. Click Apply for Leave to submit one.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-paper-dim dark:bg-stone-900 border-b border-divider dark:border-stone-800 text-ink-muted uppercase">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Type</th>
                        <th className="px-4 py-3 font-semibold">Dates</th>
                        <th className="px-4 py-3 font-semibold">Duration</th>
                        <th className="px-4 py-3 font-semibold">Reason</th>
                        <th className="px-4 py-3 font-semibold">Status</th>
                        <th className="px-4 py-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider dark:divide-stone-800">
                      {leaveRequests.map((r) => (
                        <tr key={r.id} className="hover:bg-paper-dim/50 dark:hover:bg-stone-800/50">
                          <td className="px-4 py-3 font-medium text-ink dark:text-stone-200">
                            {r.leave_type_name}
                            {r.half_day_type !== 'FULL_DAY' && (
                              <span className="block text-[10px] text-amber-600 dark:text-amber-400 font-mono">
                                ({r.half_day_type})
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-ink-muted">
                            {r.start_date} to {r.end_date}
                          </td>
                          <td className="px-4 py-3 font-semibold text-ink dark:text-stone-200">
                            {r.requested_days} day(s)
                          </td>
                          <td className="px-4 py-3 text-ink-muted max-w-xs truncate">{r.reason}</td>
                          <td className="px-4 py-3">{getStatusBadge(r.status)}</td>
                          <td className="px-4 py-3 text-right">
                            {['PENDING', 'APPROVED'].includes(r.status) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => cancelMutation.mutate(r.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                Cancel
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Approvals Dashboard */}
      {activeTab === 'approvals' && isApproverOrAdmin && (
        <div className="space-y-6">
          {/* KPI Summary Cards */}
          {summaryReport && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <Card className="p-4 border-l-4 border-l-amber-500">
                <div className="text-xs font-semibold text-ink-muted uppercase">Pending Approvals</div>
                <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                  {summaryReport.pending_requests}
                </div>
              </Card>
              <Card className="p-4 border-l-4 border-l-emerald-500">
                <div className="text-xs font-semibold text-ink-muted uppercase">Currently On Leave</div>
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {summaryReport.currently_on_leave}
                </div>
              </Card>
              <Card className="p-4 border-l-4 border-l-blue-500">
                <div className="text-xs font-semibold text-ink-muted uppercase">Approved Today</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {summaryReport.approved_today}
                </div>
              </Card>
              <Card className="p-4 border-l-4 border-l-purple-500">
                <div className="text-xs font-semibold text-ink-muted uppercase">Total Reqs (Year)</div>
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                  {summaryReport.total_requests}
                </div>
              </Card>
            </div>
          )}

          {/* Pending Approval Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-divider dark:border-stone-800">
              <CardTitle className="text-sm font-semibold">Pending Staff Leave Approvals</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {pendingRequests.length === 0 ? (
                <div className="p-8 text-center text-xs text-ink-muted flex flex-col items-center gap-2">
                  <CheckCircle className="w-8 h-8 text-emerald-500" />
                  No pending leave requests awaiting approval. All clear!
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-paper-dim dark:bg-stone-900 border-b border-divider dark:border-stone-800 text-ink-muted uppercase">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Staff Member</th>
                        <th className="px-4 py-3 font-semibold">Leave Type</th>
                        <th className="px-4 py-3 font-semibold">Dates</th>
                        <th className="px-4 py-3 font-semibold">Duration</th>
                        <th className="px-4 py-3 font-semibold">Reason</th>
                        <th className="px-4 py-3 font-semibold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider dark:divide-stone-800">
                      {pendingRequests.map((r) => (
                        <tr key={r.id} className="hover:bg-paper-dim/50 dark:hover:bg-stone-800/50">
                          <td className="px-4 py-3 font-semibold text-ink dark:text-stone-200">
                            {r.teacher_name}
                            <span className="block text-[10px] text-ink-muted font-mono">{r.employee_id}</span>
                          </td>
                          <td className="px-4 py-3 text-ink-muted">{r.leave_type_name}</td>
                          <td className="px-4 py-3 text-ink-muted">
                            {r.start_date} to {r.end_date}
                          </td>
                          <td className="px-4 py-3 font-semibold text-ink dark:text-stone-200">
                            {r.requested_days} day(s)
                          </td>
                          <td className="px-4 py-3 text-ink-muted max-w-xs truncate">{r.reason}</td>
                          <td className="px-4 py-3 text-right space-x-2">
                            <Button
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                              onClick={() => {
                                setSelectedRequest(r);
                                setIsApproveModalOpen(true);
                              }}
                            >
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => {
                                setSelectedRequest(r);
                                setIsRejectModalOpen(true);
                              }}
                            >
                              Reject
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 3: Leave Policies */}
      {activeTab === 'policies' && isApproverOrAdmin && (
        <Card>
          <CardHeader className="border-b border-divider dark:border-stone-800">
            <CardTitle className="text-sm font-semibold">Configured School Leave Policies</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-paper-dim dark:bg-stone-900 border-b border-divider dark:border-stone-800 text-ink-muted uppercase">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Code</th>
                    <th className="px-4 py-3 font-semibold">Name</th>
                    <th className="px-4 py-3 font-semibold">Max Days / Year</th>
                    <th className="px-4 py-3 font-semibold">Requires Doc</th>
                    <th className="px-4 py-3 font-semibold">Paid Leave</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-divider dark:divide-stone-800">
                  {leaveTypes.map((t) => (
                    <tr key={t.id} className="hover:bg-paper-dim/50 dark:hover:bg-stone-800/50">
                      <td className="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">{t.code}</td>
                      <td className="px-4 py-3 font-medium text-ink dark:text-stone-200">{t.name}</td>
                      <td className="px-4 py-3 font-semibold">{t.max_days_per_year} days</td>
                      <td className="px-4 py-3">{t.requires_attachment ? <Badge variant="warning">YES</Badge> : <Badge variant="neutral">NO</Badge>}</td>
                      <td className="px-4 py-3">{t.is_paid ? <Badge variant="success">PAID</Badge> : <Badge variant="error">UNPAID</Badge>}</td>
                      <td className="px-4 py-3">{t.is_active ? <Badge variant="success">ACTIVE</Badge> : <Badge variant="neutral">INACTIVE</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal: Apply Leave */}
      <Modal isOpen={isApplyModalOpen} onClose={() => setIsApplyModalOpen(false)} title="Submit Staff Leave Application">
        <form onSubmit={handleApplySubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Leave Type</label>
            <select
              value={newRequest.leave_type_id}
              onChange={(e) => setNewRequest({ ...newRequest, leave_type_id: e.target.value })}
              className="w-full p-2 border border-divider dark:border-stone-700 bg-paper dark:bg-stone-900 rounded text-xs"
              required
            >
              <option value="">Select Leave Type</option>
              {leaveTypes.map((lt) => (
                <option key={lt.id} value={lt.id}>
                  {lt.name} ({lt.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink dark:text-stone-300 mb-1">Start Date</label>
              <Input
                type="date"
                value={newRequest.start_date}
                onChange={(e) => setNewRequest({ ...newRequest, start_date: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block font-medium text-ink dark:text-stone-300 mb-1">End Date</label>
              <Input
                type="date"
                value={newRequest.end_date}
                onChange={(e) => setNewRequest({ ...newRequest, end_date: e.target.value })}
                required
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Duration Type</label>
            <select
              value={newRequest.half_day_type}
              onChange={(e) => setNewRequest({ ...newRequest, half_day_type: e.target.value })}
              className="w-full p-2 border border-divider dark:border-stone-700 bg-paper dark:bg-stone-900 rounded text-xs"
            >
              <option value="FULL_DAY">Full Day(s)</option>
              <option value="FIRST_HALF">First Half (Morning Only)</option>
              <option value="SECOND_HALF">Second Half (Afternoon Only)</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Reason for Leave</label>
            <textarea
              value={newRequest.reason}
              onChange={(e) => setNewRequest({ ...newRequest, reason: e.target.value })}
              className="w-full p-2 border border-divider dark:border-stone-700 bg-paper dark:bg-stone-900 rounded text-xs h-20"
              placeholder="Provide reason for leave application..."
              required
            />
          </div>

          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Attachment Reference (Optional)</label>
            <Input
              type="text"
              value={newRequest.attachment_url}
              onChange={(e) => setNewRequest({ ...newRequest, attachment_url: e.target.value })}
              placeholder="Document URL or reference ID (e.g. medical certificate)"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider dark:border-stone-800">
            <Button variant="outline" type="button" onClick={() => setIsApplyModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createRequestMutation.isPending}>
              Submit Application
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Approve Request */}
      <Modal isOpen={isApproveModalOpen} onClose={() => setIsApproveModalOpen(false)} title="Approve Staff Leave Request">
        <div className="space-y-4 text-xs">
          <p className="text-ink-muted">
            Are you sure you want to approve leave for <strong className="text-ink dark:text-stone-100">{selectedRequest?.teacher_name}</strong> from {selectedRequest?.start_date} to {selectedRequest?.end_date}?
          </p>
          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Approval Remarks (Optional)</label>
            <Input
              type="text"
              value={actionRemarks}
              onChange={(e) => setActionRemarks(e.target.value)}
              placeholder="e.g. Substitute assigned, approved by Principal"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-divider dark:border-stone-800">
            <Button variant="outline" onClick={() => setIsApproveModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              onClick={() => selectedRequest && approveMutation.mutate({ id: selectedRequest.id, remarks: actionRemarks })}
              disabled={approveMutation.isPending}
            >
              Confirm Approval
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Reject Request */}
      <Modal isOpen={isRejectModalOpen} onClose={() => setIsRejectModalOpen(false)} title="Reject Staff Leave Request">
        <div className="space-y-4 text-xs">
          <p className="text-ink-muted">
            Rejecting leave request for <strong className="text-ink dark:text-stone-100">{selectedRequest?.teacher_name}</strong>.
          </p>
          <div>
            <label className="block font-medium text-ink dark:text-stone-300 mb-1">Rejection Reason (Required)</label>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full p-2 border border-divider dark:border-stone-700 bg-paper dark:bg-stone-900 rounded text-xs h-20"
              placeholder="State reason for rejection..."
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-divider dark:border-stone-800">
            <Button variant="outline" onClick={() => setIsRejectModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              className="bg-red-600 text-white hover:bg-red-700"
              onClick={() => selectedRequest && rejectionReason && rejectMutation.mutate({ id: selectedRequest.id, reason: rejectionReason })}
              disabled={rejectMutation.isPending || !rejectionReason}
            >
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
