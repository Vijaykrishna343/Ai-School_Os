import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeesPage } from '@/pages/FeesPage';
import { useAuthStore } from '@/store/useAuthStore';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { schoolClassesApi } from '@/services/api/schoolClassesApi';
import { sectionsApi } from '@/services/api/sectionsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { feesApi } from '@/services/api/feesApi';

vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: { getAcademicYears: vi.fn() },
}));

vi.mock('@/services/api/schoolClassesApi', () => ({
  schoolClassesApi: { getSchoolClasses: vi.fn() },
}));

vi.mock('@/services/api/sectionsApi', () => ({
  sectionsApi: { getSectionsByClass: vi.fn() },
}));

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: { getStudents: vi.fn() },
}));

vi.mock('@/services/api/feesApi', () => ({
  feesApi: {
    getFeeStructures: vi.fn(),
    getFeeStructure: vi.fn(),
    createFeeStructure: vi.fn(),
    updateFeeStructure: vi.fn(),
    deleteFeeStructure: vi.fn(),
    assignFeeStructure: vi.fn(),
    getStudentFeeAssignments: vi.fn(),
    getStudentFeeAssignment: vi.fn(),
    deleteStudentFeeAssignment: vi.fn(),
    addStudentFeeItem: vi.fn(),
    addFeeDiscount: vi.fn(),
    removeFeeDiscount: vi.fn(),
    cancelStudentFeeAssignment: vi.fn(),
    recordFeePayment: vi.fn(),
    getFeePayments: vi.fn(),
    getFeePayment: vi.fn(),
    getPaymentReceipt: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('FeesPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 'user-1', email: 'accountant@school.com', school_id: 'school-1' } as any,
      permissions: ['fees.view', 'fees.create', 'fees.update', 'fees.delete'],
    });

    vi.mocked(academicYearsApi.getAcademicYears).mockResolvedValue({
      items: [{ id: 'ay-2026', school_id: 'school-1', name: '2026-2027', status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(schoolClassesApi.getSchoolClasses).mockResolvedValue({
      items: [{ id: 'class-5', school_id: 'school-1', name: 'Class 5', display_order: 1, status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(sectionsApi.getSectionsByClass).mockResolvedValue({
      items: [{ id: 'sec-5a', school_class_id: 'class-5', name: 'A', capacity: 30, status: 'ACTIVE' }],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(studentsApi.getStudents).mockResolvedValue({
      items: [
        { id: 'stud-1', first_name: 'John', last_name: 'Doe', admission_number: 'ADM-101', status: 'ACTIVE' },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(feesApi.getFeeStructures).mockResolvedValue({
      items: [
        {
          id: 'struct-1',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          school_class_id: 'class-5',
          name: 'Class 5 Standard Fees',
          description: 'Tuition and books package',
          status: 'ACTIVE',
          items: [
            { id: 'item-1', fee_structure_id: 'struct-1', category: 'TUITION', name: 'Tuition Fee', amount: 10000, is_optional: false, order: 1 },
          ],
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(feesApi.getStudentFeeAssignments).mockResolvedValue({
      items: [
        {
          id: 'assign-1',
          school_id: 'school-1',
          academic_year_id: 'ay-2026',
          student_id: 'stud-1',
          fee_structure_id: 'struct-1',
          status: 'PENDING',
          due_date: '2026-05-30',
          remarks: 'Annual fee',
          gross_amount: 10000,
          total_discounts: 1000,
          net_payable: 9000,
          total_paid: 3000,
          outstanding_due: 6000,
          student_fee_items: [],
          discounts: [],
          student: { first_name: 'John', last_name: 'Doe' },
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(feesApi.getFeePayments).mockResolvedValue({
      items: [
        {
          id: 'pay-1',
          school_id: 'school-1',
          student_fee_assignment_id: 'assign-1',
          receipt_number: 'REC-20260817-001',
          amount: 3000,
          payment_date: '2026-05-10',
          payment_mode: 'UPI',
          reference_number: 'UPI987654321',
          remarks: 'First installment',
        },
      ],
      total: 1, page: 1, page_size: 100, total_pages: 1,
    } as any);

    vi.mocked(feesApi.getPaymentReceipt).mockResolvedValue({
      receipt_number: 'REC-20260817-001',
      school_id: 'school-1',
      student_id: 'stud-1',
      student_fee_assignment_id: 'assign-1',
      payment_id: 'pay-1',
      payment_date: '2026-05-10',
      payment_mode: 'UPI',
      reference_number: 'UPI987654321',
      amount: 3000,
      gross_amount: 10000,
      total_discounts: 1000,
      net_payable: 9000,
      total_paid: 3000,
      outstanding_due: 6000,
    } as any);
  });

  it('1. renders fees page with workspace tabs and academic year selector', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Fees & Billing Ledger')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Fee Structures' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Student Fee Ledgers' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Payment Transactions' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Class 5 Standard Fees')).toBeInTheDocument();
    });
  });

  it('2. opens create fee structure modal and triggers creation', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Class 5 Standard Fees')).toBeInTheDocument();
    });

    const createBtn = screen.getByRole('button', { name: 'Create Fee Structure' });
    fireEvent.click(createBtn);

    expect(screen.getByText('CREATE FEE STRUCTURE')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Structure Name *'), { target: { value: 'Class 6 Package' } });

    const saveBtn = screen.getByRole('button', { name: 'Save Structure' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(feesApi.createFeeStructure).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Class 6 Package',
        })
      );
    });
  });

  it('3. handles fee structure deletion', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Class 5 Standard Fees')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByRole('button', { name: 'Delete' });
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(feesApi.deleteFeeStructure).toHaveBeenCalledWith('struct-1');
    });
  });

  it('4. displays student fee assignments ledger with calculated financial metrics', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Student Fee Ledgers' }));

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('INR 10,000')).toBeInTheDocument();
      expect(screen.getByText('- INR 1,000')).toBeInTheDocument();
      expect(screen.getByText('INR 9,000')).toBeInTheDocument();
      expect(screen.getByText('INR 3,000')).toBeInTheDocument();
      expect(screen.getByText('INR 6,000')).toBeInTheDocument();
    });
  });

  it('5. triggers concession / discount application modal', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Student Fee Ledgers' }));

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const concessionBtn = screen.getByRole('button', { name: 'Concession' });
    fireEvent.click(concessionBtn);

    expect(screen.getByText('APPLY FEE CONCESSION / DISCOUNT')).toBeInTheDocument();

    const saveDiscountBtn = screen.getByRole('button', { name: 'Apply Concession' });
    fireEvent.click(saveDiscountBtn);

    await waitFor(() => {
      expect(feesApi.addFeeDiscount).toHaveBeenCalledWith(
        'assign-1',
        expect.objectContaining({
          discount_type: 'SCHOLARSHIP',
          amount: 1000,
        })
      );
    });
  });

  it('6. records fee payment and opens receipt modal', async () => {
    vi.mocked(feesApi.recordFeePayment).mockResolvedValue({
      id: 'pay-1',
      school_id: 'school-1',
      student_fee_assignment_id: 'assign-1',
      receipt_number: 'REC-20260817-001',
      amount: 6000,
      payment_date: '2026-05-15',
      payment_mode: 'CASH',
      reference_number: null,
      remarks: null,
    } as any);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Student Fee Ledgers' }));

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const payBtn = screen.getByRole('button', { name: 'Record Payment' });
    fireEvent.click(payBtn);

    expect(screen.getByText('RECORD FEE PAYMENT')).toBeInTheDocument();

    const submitPayBtn = screen.getByRole('button', { name: 'Submit & Generate Receipt' });
    fireEvent.click(submitPayBtn);

    await waitFor(() => {
      expect(feesApi.recordFeePayment).toHaveBeenCalledWith(
        expect.objectContaining({
          student_fee_assignment_id: 'assign-1',
          amount: 6000,
        })
      );
      expect(screen.getByText('FEE PAYMENT RECEIPT')).toBeInTheDocument();
      expect(screen.getByText('NO: REC-20260817-001')).toBeInTheDocument();
    });
  });

  it('7. loads payment transactions tab and opens receipt details', async () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <FeesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Payment Transactions' }));

    await waitFor(() => {
      expect(screen.getByText('REC-20260817-001')).toBeInTheDocument();
      expect(screen.getAllByText('UPI').length).toBeGreaterThan(0);
    });

    const viewReceiptBtn = screen.getByRole('button', { name: 'View Receipt' });
    fireEvent.click(viewReceiptBtn);

    await waitFor(() => {
      expect(feesApi.getPaymentReceipt).toHaveBeenCalledWith('pay-1');
      expect(screen.getByText('FEE PAYMENT RECEIPT')).toBeInTheDocument();
    });
  });
});
