import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { feesApi } from '@/services/api/feesApi';
import {
  FeeStructure,
  FeeStructureCreate,
  FeeItemCreate,
  StudentFeeAssignment,
  StudentFeeAssignmentCreate,
  FeePayment,
  FeePaymentCreate,
  FeeReceipt,
  FeeDiscountCreate,
  FeeCategory,
  FeeStructureStatus,
  DiscountType,
  PaymentMode,
  StudentFeeAssignmentStatus,
} from '@/types/models';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { Drawer } from '@/components/ui/Drawer';

export const FeesPage: React.FC = () => {
  const { permissions, user } = useAuthStore();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'structures' | 'assignments' | 'payments'>('structures');

  // Shared state filters
  const [selectedYearId, setSelectedYearId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState('');

  // ------------------------------------------------------------------
  // Tab 1: Fee Structure State
  // ------------------------------------------------------------------
  const [isStructureModalOpen, setIsStructureModalOpen] = useState(false);
  const [editingStructure, setEditingStructure] = useState<FeeStructure | null>(null);
  const [structureForm, setStructureForm] = useState<Partial<FeeStructureCreate>>({
    name: '',
    description: '',
    school_class_id: null,
    status: 'ACTIVE',
    items: [],
  });
  const [structureItems, setStructureItems] = useState<FeeItemCreate[]>([
    { category: 'TUITION', name: 'Tuition Fee', amount: 10000, is_optional: false, order: 1 },
  ]);

  // ------------------------------------------------------------------
  // Tab 2: Assignments & Payments Ledger State
  // ------------------------------------------------------------------
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [statusFilter, setStatusFilter] = useState<StudentFeeAssignmentStatus | ''>('');

  // Assign Structure Modal
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignForm, setAssignForm] = useState<Partial<StudentFeeAssignmentCreate>>({
    student_id: '',
    fee_structure_id: '',
    due_date: '',
    remarks: '',
  });

  // Concession / Discount Modal
  const [isDiscountModalOpen, setIsDiscountModalOpen] = useState(false);
  const [selectedAssignmentForDiscount, setSelectedAssignmentForDiscount] =
    useState<StudentFeeAssignment | null>(null);
  const [discountForm, setDiscountForm] = useState<FeeDiscountCreate>({
    discount_type: 'SCHOLARSHIP',
    name: 'Merit Scholarship',
    amount: 1000,
    remarks: '',
  });

  // Record Payment Modal
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [selectedAssignmentForPayment, setSelectedAssignmentForPayment] =
    useState<StudentFeeAssignment | null>(null);
  const [paymentForm, setPaymentForm] = useState<Partial<FeePaymentCreate>>({
    amount: 0,
    payment_date: new Date().toISOString().split('T')[0],
    payment_mode: 'CASH',
    reference_number: '',
    remarks: '',
  });

  // ------------------------------------------------------------------
  // Tab 3: Receipts Modal State
  // ------------------------------------------------------------------
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState<FeeReceipt | null>(null);
  const [paymentModeFilter, setPaymentModeFilter] = useState<PaymentMode | ''>('');

  // Error & Message Banners
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // ------------------------------------------------------------------
  // Queries
  // ------------------------------------------------------------------
  const { data: yearsData } = useQuery({
    queryKey: ['academicYearsFees'],
    queryFn: () => academicYearsApi.getAcademicYears({ page: 1, page_size: 100 }),
    enabled: permissions.includes('fees.view'),
  });

  const { data: classesData } = useQuery({
    queryKey: ['schoolClassesFees'],
    queryFn: () => schoolClassesApi.getSchoolClasses({ page: 1, page_size: 100 }),
    enabled: permissions.includes('fees.view'),
  });

  const { data: sectionsData } = useQuery({
    queryKey: ['sectionsFees', selectedClassId],
    queryFn: () => sectionsApi.getSectionsByClass(selectedClassId, { page: 1, page_size: 100 }),
    enabled: !!selectedClassId,
  });

  const { data: studentsData } = useQuery({
    queryKey: ['studentsFees', selectedSectionId],
    queryFn: () =>
      studentsApi.getStudents({
        section_id: selectedSectionId,
        status: 'ACTIVE',
        page_size: 100,
      }),
    enabled: !!selectedSectionId,
  });

  // Structures List Query
  const { data: structuresData, refetch: refetchStructures } = useQuery({
    queryKey: ['feeStructuresList', selectedYearId, selectedClassId],
    queryFn: () =>
      feesApi.getFeeStructures({
        academic_year_id: selectedYearId || undefined,
        school_class_id: selectedClassId || undefined,
        page_size: 100,
      }),
    enabled: permissions.includes('fees.view') && !!selectedYearId,
  });

  // Student Fee Assignments Query
  const { data: assignmentsData, refetch: refetchAssignments } = useQuery({
    queryKey: ['studentFeeAssignmentsList', selectedYearId, selectedStudentId, statusFilter],
    queryFn: () =>
      feesApi.getStudentFeeAssignments({
        academic_year_id: selectedYearId || undefined,
        student_id: selectedStudentId || undefined,
        status: statusFilter || undefined,
        page_size: 100,
      }),
    enabled: permissions.includes('fees.view') && !!selectedYearId,
  });

  // Payments History Query
  const { data: paymentsData } = useQuery({
    queryKey: ['feePaymentsList', paymentModeFilter],
    queryFn: () =>
      feesApi.getFeePayments({
        payment_mode: paymentModeFilter || undefined,
        page_size: 100,
      }),
    enabled: permissions.includes('fees.view') && activeTab === 'payments',
  });

  // Set default active academic year
  useEffect(() => {
    if (yearsData?.items && yearsData.items.length > 0 && !selectedYearId) {
      const activeYear = yearsData.items.find((y) => y.status === 'ACTIVE');
      if (activeYear) {
        setSelectedYearId(activeYear.id);
      } else {
        setSelectedYearId(yearsData.items[0].id);
      }
    }
  }, [yearsData, selectedYearId]);

  // ------------------------------------------------------------------
  // Handlers - Fee Structure
  // ------------------------------------------------------------------
  const handleOpenStructureModal = (structure: FeeStructure | null = null) => {
    if (structure) {
      setEditingStructure(structure);
      setStructureForm({
        name: structure.name,
        description: structure.description || '',
        school_class_id: structure.school_class_id,
        status: structure.status,
      });
      setStructureItems(
        structure.items.map((i) => ({
          category: i.category,
          name: i.name,
          amount: i.amount,
          is_optional: i.is_optional,
          order: i.order,
        }))
      );
    } else {
      setEditingStructure(null);
      setStructureForm({
        name: '',
        description: '',
        school_class_id: null,
        status: 'ACTIVE',
      });
      setStructureItems([
        { category: 'TUITION', name: 'Tuition Fee', amount: 10000, is_optional: false, order: 1 },
      ]);
    }
    setIsStructureModalOpen(true);
  };

  const handleAddStructureItem = () => {
    setStructureItems((prev) => [
      ...prev,
      { category: 'MISCELLANEOUS', name: 'Misc Fee', amount: 500, is_optional: false, order: prev.length + 1 },
    ]);
  };

  const handleRemoveStructureItem = (index: number) => {
    setStructureItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSaveStructure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedYearId) return;

    setErrorMessage(null);
    setSuccessMessage(null);

    const payload: FeeStructureCreate = {
      academic_year_id: selectedYearId,
      school_class_id: structureForm.school_class_id || null,
      name: structureForm.name || '',
      description: structureForm.description || null,
      status: structureForm.status || 'ACTIVE',
      items: structureItems,
    };

    try {
      if (editingStructure) {
        await feesApi.updateFeeStructure(editingStructure.id, payload);
        setSuccessMessage('Fee structure updated successfully.');
      } else {
        await feesApi.createFeeStructure(payload);
        setSuccessMessage('Fee structure created successfully.');
      }
      refetchStructures();
      setIsStructureModalOpen(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save fee structure.');
    }
  };

  const handleDeleteStructure = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this fee structure?')) return;
    try {
      await feesApi.deleteFeeStructure(id);
      refetchStructures();
    } catch (err: any) {
      alert(err.message || 'Failed to delete fee structure.');
    }
  };

  // ------------------------------------------------------------------
  // Handlers - Student Fee Assignment
  // ------------------------------------------------------------------
  const handleOpenAssignModal = () => {
    setAssignForm({
      student_id: selectedStudentId || '',
      fee_structure_id: '',
      due_date: '',
      remarks: '',
    });
    setIsAssignModalOpen(true);
  };

  const handleSaveAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedYearId || !assignForm.student_id || !assignForm.fee_structure_id) return;

    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await feesApi.assignFeeStructure({
        academic_year_id: selectedYearId,
        student_id: assignForm.student_id,
        fee_structure_id: assignForm.fee_structure_id,
        due_date: assignForm.due_date || null,
        remarks: assignForm.remarks || null,
      });
      setSuccessMessage('Fee structure assigned to student successfully.');
      refetchAssignments();
      setIsAssignModalOpen(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to assign fee structure.');
    }
  };

  const handleCancelAssignment = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this student fee assignment?')) return;
    try {
      await feesApi.cancelStudentFeeAssignment(id);
      refetchAssignments();
    } catch (err: any) {
      alert(err.message || 'Failed to cancel assignment.');
    }
  };

  // ------------------------------------------------------------------
  // Handlers - Discounts & Concessions
  // ------------------------------------------------------------------
  const handleOpenDiscountModal = (assignment: StudentFeeAssignment) => {
    setSelectedAssignmentForDiscount(assignment);
    setDiscountForm({
      discount_type: 'SCHOLARSHIP',
      name: 'Merit Scholarship',
      amount: 1000,
      remarks: '',
    });
    setIsDiscountModalOpen(true);
  };

  const handleSaveDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentForDiscount) return;

    setErrorMessage(null);
    setSuccessMessage(null);

    const discountAmount = Number(discountForm.amount);
    if (discountAmount <= 0) {
      setErrorMessage('Discount amount must be greater than zero.');
      return;
    }

    if (discountAmount > Number(selectedAssignmentForDiscount.gross_amount)) {
      setErrorMessage('Total discount cannot exceed gross payable amount.');
      return;
    }

    try {
      await feesApi.addFeeDiscount(selectedAssignmentForDiscount.id, {
        ...discountForm,
        amount: discountAmount,
      });
      setSuccessMessage('Concession applied successfully.');
      refetchAssignments();
      setIsDiscountModalOpen(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to apply discount.');
    }
  };

  // ------------------------------------------------------------------
  // Handlers - Record Payment
  // ------------------------------------------------------------------
  const handleOpenPaymentModal = (assignment: StudentFeeAssignment) => {
    setSelectedAssignmentForPayment(assignment);
    setPaymentForm({
      amount: Number(assignment.outstanding_due),
      payment_date: new Date().toISOString().split('T')[0],
      payment_mode: 'CASH',
      reference_number: '',
      remarks: '',
    });
    setIsPaymentModalOpen(true);
  };

  const handleSavePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentForPayment) return;

    setErrorMessage(null);
    setSuccessMessage(null);

    const paymentAmount = Number(paymentForm.amount);
    const outstanding = Number(selectedAssignmentForPayment.outstanding_due);

    if (paymentAmount <= 0) {
      setErrorMessage('Payment amount must be greater than zero.');
      return;
    }

    if (paymentAmount > outstanding) {
      setErrorMessage(`Payment amount cannot exceed outstanding due balance (INR ${outstanding}).`);
      return;
    }

    try {
      const paymentRecord = await feesApi.recordFeePayment({
        student_fee_assignment_id: selectedAssignmentForPayment.id,
        amount: paymentAmount,
        payment_date: paymentForm.payment_date || new Date().toISOString().split('T')[0],
        payment_mode: paymentForm.payment_mode || 'CASH',
        reference_number: paymentForm.reference_number || undefined,
        remarks: paymentForm.remarks || undefined,
      });

      setSuccessMessage(`Payment recorded successfully with Receipt Number ${paymentRecord.receipt_number}.`);
      refetchAssignments();
      setIsPaymentModalOpen(false);

      // Automatically fetch receipt representation
      const receipt = await feesApi.getPaymentReceipt(paymentRecord.id);
      setSelectedReceipt(receipt);
      setIsReceiptModalOpen(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to record payment.');
    }
  };

  const handleViewReceipt = async (paymentId: string) => {
    try {
      const receipt = await feesApi.getPaymentReceipt(paymentId);
      setSelectedReceipt(receipt);
      setIsReceiptModalOpen(true);
    } catch (err: any) {
      alert(err.message || 'Failed to load receipt.');
    }
  };

  // RBAC Gating
  const canManageFees = permissions.includes('fees.create') || permissions.includes('fees.update');

  const getStatusBadge = (status: StudentFeeAssignmentStatus) => {
    switch (status) {
      case 'PAID':
        return <Badge variant="success">PAID</Badge>;
      case 'PARTIALLY_PAID':
        return <Badge variant="warning">PARTIALLY PAID</Badge>;
      case 'CANCELLED':
        return <Badge variant="error">CANCELLED</Badge>;
      default:
        return <Badge variant="default">PENDING</Badge>;
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto bg-[#fcf9f8] min-h-[85vh] text-ink">
      {/* Editorial Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
            FINANCIAL OPERATIONS & SERVICES
          </p>
          <h1 className="text-2xl font-bold font-serif text-brand-500 dark:text-white mt-1">
            Fees & Billing Ledger
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure fee structures, issue student fee billing ledgers, apply concessions, and record payments.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('structures')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'structures'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Fee Structures
        </button>
        <button
          onClick={() => setActiveTab('assignments')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'assignments'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Student Fee Ledgers
        </button>
        <button
          onClick={() => setActiveTab('payments')}
          className={`px-4 py-2 text-xs font-mono uppercase border-b-2 tracking-wider ${
            activeTab === 'payments'
              ? 'border-brand-500 text-brand-500 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Payment Transactions
        </button>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <Alert type="error" title="Financial Action Error">
          {errorMessage}
        </Alert>
      )}
      {successMessage && <Alert type="success">{successMessage}</Alert>}

      {/* Shared Selector Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white border border-slate-200 dark:border-slate-800 p-4 rounded-none">
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-4 gap-3 w-full">
          <div>
            <label
              htmlFor="year-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Academic Year
            </label>
            <select
              id="year-select"
              value={selectedYearId}
              onChange={(e) => setSelectedYearId(e.target.value)}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
            >
              <option value="">Select Year</option>
              {yearsData?.items?.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.name} ({y.status})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="class-select"
              className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
            >
              Class (Optional)
            </label>
            <select
              id="class-select"
              value={selectedClassId}
              onChange={(e) => {
                setSelectedClassId(e.target.value);
                setSelectedSectionId('');
                setSelectedStudentId('');
              }}
              className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white"
            >
              <option value="">All Classes</option>
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {activeTab === 'assignments' && (
            <>
              <div>
                <label
                  htmlFor="section-select"
                  className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
                >
                  Section (Optional)
                </label>
                <select
                  id="section-select"
                  value={selectedSectionId}
                  onChange={(e) => {
                    setSelectedSectionId(e.target.value);
                    setSelectedStudentId('');
                  }}
                  disabled={!selectedClassId}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white disabled:opacity-40"
                >
                  <option value="">All Sections</option>
                  {sectionsData?.items?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="student-select"
                  className="block text-[10px] font-mono uppercase text-slate-500 mb-1"
                >
                  Student (Optional)
                </label>
                <select
                  id="student-select"
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  disabled={!selectedSectionId}
                  className="w-full px-2 py-1.5 text-xs rounded-sm border border-slate-300 dark:border-slate-700 bg-white disabled:opacity-40"
                >
                  <option value="">All Students</option>
                  {studentsData?.items?.map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.first_name} {st.last_name || ''} ({st.admission_number})
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------
          TAB 1: Fee Structures
          ------------------------------------------------------------------ */}
      {activeTab === 'structures' && (
        <div className="space-y-4 border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
              FEE_STRUCTURE_TEMPLATES
            </p>
            {permissions.includes('fees.create') && (
              <Button onClick={() => handleOpenStructureModal(null)}>Create Fee Structure</Button>
            )}
          </div>

          <Table
            columns={[
              {
                key: 'name',
                header: 'Structure Name',
                className: 'font-semibold text-xs',
                render: (row) => row.name,
              },
              {
                key: 'class',
                header: 'Applicable Class',
                render: (row) => (
                  <span className="text-xs font-mono">
                    {classesData?.items?.find((c) => c.id === row.school_class_id)?.name || 'All Classes'}
                  </span>
                ),
              },
              {
                key: 'items_count',
                header: 'Line Items',
                render: (row) => (
                  <span className="text-xs font-mono">{row.items?.length || 0} Fee Heads</span>
                ),
              },
              {
                key: 'total_amount',
                header: 'Gross Total',
                className: 'font-mono text-xs font-bold',
                render: (row) => {
                  const sum = row.items?.reduce((acc, i) => acc + Number(i.amount), 0) || 0;
                  return `INR ${sum.toLocaleString('en-IN')}`;
                },
              },
              {
                key: 'status',
                header: 'Status',
                render: (row) => (
                  <Badge variant={row.status === 'ACTIVE' ? 'success' : 'default'}>{row.status}</Badge>
                ),
              },
              {
                key: 'actions',
                header: 'Actions',
                render: (row) => (
                  <div className="flex items-center gap-2">
                    {permissions.includes('fees.update') && (
                      <Button variant="secondary" onClick={() => handleOpenStructureModal(row)}>
                        Edit
                      </Button>
                    )}
                    {permissions.includes('fees.delete') && (
                      <Button variant="secondary" onClick={() => handleDeleteStructure(row.id)}>
                        Delete
                      </Button>
                    )}
                  </div>
                ),
              },
            ]}
            data={structuresData?.items || []}
            emptyText="No fee structures found for the selected academic year."
          />
        </div>
      )}

      {/* ------------------------------------------------------------------
          TAB 2: Student Fee Assignments & Payment Collection
          ------------------------------------------------------------------ */}
      {activeTab === 'assignments' && (
        <div className="space-y-4 border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-2">
            <div>
              <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
                STUDENT_FEE_BILLING_LEDGERS
              </p>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
              >
                <option value="">All Billing Statuses</option>
                <option value="PENDING">PENDING</option>
                <option value="PARTIALLY_PAID">PARTIALLY PAID</option>
                <option value="PAID">PAID</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>

              {permissions.includes('fees.create') && (
                <Button onClick={handleOpenAssignModal}>Assign Fee Structure</Button>
              )}
            </div>
          </div>

          <Table
            columns={[
              {
                key: 'student',
                header: 'Student',
                className: 'font-semibold text-xs',
                render: (row) => row.student ? `${row.student.first_name} ${row.student.last_name || ''}`.trim() : 'Student',
              },
              {
                key: 'gross',
                header: 'Gross Amount',
                render: (row) => (
                  <span className="text-xs font-mono">INR {Number(row.gross_amount).toLocaleString('en-IN')}</span>
                ),
              },
              {
                key: 'discounts',
                header: 'Concessions',
                render: (row) => (
                  <span className="text-xs font-mono text-emerald-600 font-bold">
                    - INR {Number(row.total_discounts).toLocaleString('en-IN')}
                  </span>
                ),
              },
              {
                key: 'net',
                header: 'Net Payable',
                className: 'font-mono text-xs font-bold',
                render: (row) => `INR ${Number(row.net_payable).toLocaleString('en-IN')}`,
              },
              {
                key: 'paid',
                header: 'Total Paid',
                render: (row) => (
                  <span className="text-xs font-mono text-blue-600">
                    INR {Number(row.total_paid).toLocaleString('en-IN')}
                  </span>
                ),
              },
              {
                key: 'due',
                header: 'Outstanding Due',
                className: 'font-mono text-xs font-bold text-red-600',
                render: (row) => `INR ${Number(row.outstanding_due).toLocaleString('en-IN')}`,
              },
              {
                key: 'status',
                header: 'Status',
                render: (row) => getStatusBadge(row.status),
              },
              {
                key: 'actions',
                header: 'Actions',
                render: (row) => (
                  <div className="flex items-center gap-2">
                    {row.status !== 'PAID' && row.status !== 'CANCELLED' && permissions.includes('fees.create') && (
                      <Button onClick={() => handleOpenPaymentModal(row)}>Record Payment</Button>
                    )}
                    {row.status !== 'CANCELLED' && permissions.includes('fees.update') && (
                      <Button variant="secondary" onClick={() => handleOpenDiscountModal(row)}>
                        Concession
                      </Button>
                    )}
                    {row.status !== 'CANCELLED' && permissions.includes('fees.update') && (
                      <Button variant="secondary" onClick={() => handleCancelAssignment(row.id)}>
                        Cancel
                      </Button>
                    )}
                  </div>
                ),
              },
            ]}
            data={assignmentsData?.items || []}
            emptyText="No student fee assignments found for the current filter."
          />
        </div>
      )}

      {/* ------------------------------------------------------------------
          TAB 3: Payment Transactions
          ------------------------------------------------------------------ */}
      {activeTab === 'payments' && (
        <div className="space-y-4 border border-slate-200 dark:border-slate-800 bg-white p-4 rounded-none">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <p className="text-xs font-mono uppercase tracking-wider text-slate-500">
              PAYMENT_TRANSACTION_RECORDS
            </p>
            <div>
              <select
                value={paymentModeFilter}
                onChange={(e) => setPaymentModeFilter(e.target.value as any)}
                className="px-2 py-1.5 text-xs rounded-sm border border-slate-300 bg-white"
              >
                <option value="">All Payment Modes</option>
                <option value="CASH">CASH</option>
                <option value="UPI">UPI</option>
                <option value="BANK_TRANSFER">BANK TRANSFER</option>
                <option value="CARD">CARD</option>
                <option value="CHEQUE">CHEQUE</option>
              </select>
            </div>
          </div>

          <Table
            columns={[
              {
                key: 'receipt',
                header: 'Receipt No',
                className: 'font-mono text-xs font-bold text-brand-500',
                render: (row) => row.receipt_number,
              },
              {
                key: 'date',
                header: 'Payment Date',
                render: (row) => <span className="text-xs font-mono">{row.payment_date}</span>,
              },
              {
                key: 'mode',
                header: 'Mode',
                render: (row) => <Badge variant="default">{row.payment_mode}</Badge>,
              },
              {
                key: 'reference',
                header: 'Ref Number',
                render: (row) => <span className="text-xs font-mono text-slate-500">{row.reference_number || 'N/A'}</span>,
              },
              {
                key: 'amount',
                header: 'Amount Paid',
                className: 'font-mono text-xs font-bold text-emerald-600',
                render: (row) => `INR ${Number(row.amount).toLocaleString('en-IN')}`,
              },
              {
                key: 'actions',
                header: 'Receipt',
                render: (row) => (
                  <Button variant="secondary" onClick={() => handleViewReceipt(row.id)}>
                    View Receipt
                  </Button>
                ),
              },
            ]}
            data={paymentsData?.items || []}
            emptyText="No payment transactions recorded yet."
          />
        </div>
      )}

      {/* ------------------------------------------------------------------
          Fee Structure Form Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isStructureModalOpen}
        onClose={() => setIsStructureModalOpen(false)}
        title={editingStructure ? 'EDIT FEE STRUCTURE' : 'CREATE FEE STRUCTURE'}
      >
        <form onSubmit={handleSaveStructure} className="space-y-4 text-xs">
          <Input
            label="Structure Name *"
            value={structureForm.name || ''}
            onChange={(e) => setStructureForm({ ...structureForm, name: e.target.value })}
            required
          />

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Applicable Class (Optional)</label>
            <select
              value={structureForm.school_class_id || ''}
              onChange={(e) =>
                setStructureForm({ ...structureForm, school_class_id: e.target.value || null })
              }
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="">All Classes (School-wide)</option>
              {classesData?.items?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <p className="text-xs font-mono font-bold uppercase text-slate-600">Line Items / Fee Heads</p>
              <Button type="button" variant="secondary" onClick={handleAddStructureItem}>
                Add Line Item
              </Button>
            </div>

            {structureItems.map((item, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-center bg-slate-50 p-2 border border-slate-200">
                <div className="col-span-3">
                  <select
                    value={item.category}
                    onChange={(e) => {
                      const val = e.target.value as FeeCategory;
                      const updated = [...structureItems];
                      updated[idx].category = val;
                      setStructureItems(updated);
                    }}
                    className="w-full text-xs py-1 border border-slate-300 bg-white"
                  >
                    <option value="TUITION">Tuition</option>
                    <option value="ADMISSION">Admission</option>
                    <option value="TRANSPORTATION">Transportation</option>
                    <option value="EXAMINATION">Examination</option>
                    <option value="BOOKS">Books</option>
                    <option value="ACTIVITY">Activity</option>
                    <option value="MISCELLANEOUS">Misc</option>
                  </select>
                </div>
                <div className="col-span-4">
                  <Input
                    value={item.name}
                    onChange={(e) => {
                      const updated = [...structureItems];
                      updated[idx].name = e.target.value;
                      setStructureItems(updated);
                    }}
                    placeholder="Fee Head Name"
                  />
                </div>
                <div className="col-span-3">
                  <Input
                    type="number"
                    value={item.amount}
                    onChange={(e) => {
                      const updated = [...structureItems];
                      updated[idx].amount = Number(e.target.value);
                      setStructureItems(updated);
                    }}
                    placeholder="Amount"
                  />
                </div>
                <div className="col-span-2 text-right">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => handleRemoveStructureItem(idx)}
                    disabled={structureItems.length === 1}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsStructureModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save Structure</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Assign Structure Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        title="ASSIGN FEE STRUCTURE TO STUDENT"
      >
        <form onSubmit={handleSaveAssignment} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Student *</label>
            <select
              value={assignForm.student_id}
              onChange={(e) => setAssignForm({ ...assignForm, student_id: e.target.value })}
              required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="">Select Student</option>
              {studentsData?.items?.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.first_name} {st.last_name || ''} ({st.admission_number})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Fee Structure *</label>
            <select
              value={assignForm.fee_structure_id}
              onChange={(e) => setAssignForm({ ...assignForm, fee_structure_id: e.target.value })}
              required
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="">Select Fee Structure</option>
              {structuresData?.items?.map((fs) => (
                <option key={fs.id} value={fs.id}>
                  {fs.name}
                </option>
              ))}
            </select>
          </div>

          <Input
            type="date"
            label="Due Date"
            value={assignForm.due_date || ''}
            onChange={(e) => setAssignForm({ ...assignForm, due_date: e.target.value })}
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsAssignModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Assign Structure</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Apply Concession / Discount Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isDiscountModalOpen}
        onClose={() => setIsDiscountModalOpen(false)}
        title="APPLY FEE CONCESSION / DISCOUNT"
      >
        <form onSubmit={handleSaveDiscount} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Discount Type *</label>
            <select
              value={discountForm.discount_type}
              onChange={(e) =>
                setDiscountForm({ ...discountForm, discount_type: e.target.value as DiscountType })
              }
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="SCHOLARSHIP">Merit Scholarship</option>
              <option value="SIBLING_CONCESSION">Sibling Concession</option>
              <option value="STAFF_CONCESSION">Staff Concession</option>
              <option value="MANAGEMENT_CONCESSION">Management Concession</option>
              <option value="SPECIAL_DISCOUNT">Special Discount</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <Input
            label="Concession Name *"
            value={discountForm.name}
            onChange={(e) => setDiscountForm({ ...discountForm, name: e.target.value })}
            required
          />

          <Input
            type="number"
            label="Discount Amount (INR) *"
            value={discountForm.amount}
            onChange={(e) => setDiscountForm({ ...discountForm, amount: Number(e.target.value) })}
            required
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsDiscountModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Apply Concession</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Record Payment Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        title="RECORD FEE PAYMENT"
      >
        <form onSubmit={handleSavePayment} className="space-y-4 text-xs">
          <div className="bg-slate-50 p-3 border border-slate-200">
            <p className="text-[10px] font-mono uppercase text-slate-500">OUTSTANDING BALANCE</p>
            <p className="text-lg font-mono font-bold text-red-600 mt-0.5">
              INR {Number(selectedAssignmentForPayment?.outstanding_due || 0).toLocaleString('en-IN')}
            </p>
          </div>

          <Input
            type="number"
            label="Payment Amount (INR) *"
            value={paymentForm.amount || ''}
            onChange={(e) => setPaymentForm({ ...paymentForm, amount: Number(e.target.value) })}
            required
          />

          <Input
            type="date"
            label="Payment Date *"
            value={paymentForm.payment_date || ''}
            onChange={(e) => setPaymentForm({ ...paymentForm, payment_date: e.target.value })}
            required
          />

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Payment Mode *</label>
            <select
              value={paymentForm.payment_mode}
              onChange={(e) =>
                setPaymentForm({ ...paymentForm, payment_mode: e.target.value as PaymentMode })
              }
              className="w-full px-2 py-1.5 rounded-sm border border-slate-300 bg-white"
            >
              <option value="CASH">Cash</option>
              <option value="UPI">UPI</option>
              <option value="BANK_TRANSFER">Bank Transfer / NEFT</option>
              <option value="CARD">Card</option>
              <option value="CHEQUE">Cheque</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <Input
            label="Reference / Transaction Number"
            value={paymentForm.reference_number || ''}
            onChange={(e) => setPaymentForm({ ...paymentForm, reference_number: e.target.value })}
            placeholder="e.g. UPI-99887766 or Chq #12345"
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={() => setIsPaymentModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Submit & Generate Receipt</Button>
          </div>
        </form>
      </Modal>

      {/* ------------------------------------------------------------------
          Receipt Modal
          ------------------------------------------------------------------ */}
      <Modal
        isOpen={isReceiptModalOpen}
        onClose={() => setIsReceiptModalOpen(false)}
        title="FEE PAYMENT RECEIPT"
      >
        {selectedReceipt && (
          <div className="space-y-4 p-4 bg-white border border-slate-200 text-xs font-mono">
            <div className="border-b border-slate-200 pb-3 flex justify-between items-start">
              <div>
                <p className="font-bold text-sm text-brand-500">PAYMENT RECEIPT</p>
                <p className="text-[10px] text-slate-400">NO: {selectedReceipt.receipt_number}</p>
              </div>
              <Badge variant="success">PAID</Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 py-2 border-b border-slate-100 text-[11px]">
              <div>
                <p className="text-slate-400">PAYMENT DATE</p>
                <p className="font-bold">{selectedReceipt.payment_date}</p>
              </div>
              <div>
                <p className="text-slate-400">PAYMENT MODE</p>
                <p className="font-bold">{selectedReceipt.payment_mode}</p>
              </div>
              <div>
                <p className="text-slate-400">REFERENCE NO</p>
                <p className="font-bold">{selectedReceipt.reference_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-slate-400">AMOUNT PAID</p>
                <p className="font-bold text-emerald-600">
                  INR {Number(selectedReceipt.amount).toLocaleString('en-IN')}
                </p>
              </div>
            </div>

            <div className="space-y-1 text-[11px] pt-2">
              <div className="flex justify-between">
                <span>Gross Payable:</span>
                <span>INR {Number(selectedReceipt.gross_amount).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-emerald-600">
                <span>Total Concessions:</span>
                <span>- INR {Number(selectedReceipt.total_discounts).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between font-bold border-t border-slate-100 pt-1">
                <span>Net Payable:</span>
                <span>INR {Number(selectedReceipt.net_payable).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-blue-600">
                <span>Total Amount Paid:</span>
                <span>INR {Number(selectedReceipt.total_paid).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between font-bold text-red-600 border-t border-slate-100 pt-1">
                <span>Remaining Due Balance:</span>
                <span>INR {Number(selectedReceipt.outstanding_due).toLocaleString('en-IN')}</span>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button onClick={() => setIsReceiptModalOpen(false)}>Close Receipt</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
