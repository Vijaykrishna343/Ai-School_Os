import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LibraryPage } from '@/pages/LibraryPage';
import { libraryApi } from '@/services/api/libraryApi';
import { studentsApi } from '@/services/api/studentsApi';
import { teachersApi } from '@/services/api/teachersApi';
import { useAuthStore } from '@/store/useAuthStore';
import {
  Book,
  BookCategory,
  BookCopy,
  BookLoan,
  BookReservation,
  Library,
  LibraryFine,
  LibraryMember,
  LibrarySummaryResponse,
} from '@/types/models';

// Mock libraryApi
vi.mock('@/services/api/libraryApi', () => ({
  libraryApi: {
    getSummary: vi.fn(),
    getLibraries: vi.fn(),
    getLibrary: vi.fn(),
    createLibrary: vi.fn(),
    updateLibrary: vi.fn(),
    deleteLibrary: vi.fn(),
    getCategories: vi.fn(),
    getCategory: vi.fn(),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn(),
    getBooks: vi.fn(),
    getBook: vi.fn(),
    createBook: vi.fn(),
    updateBook: vi.fn(),
    deleteBook: vi.fn(),
    getCopies: vi.fn(),
    getCopy: vi.fn(),
    createCopy: vi.fn(),
    updateCopy: vi.fn(),
    deleteCopy: vi.fn(),
    getMembers: vi.fn(),
    getMember: vi.fn(),
    createMember: vi.fn(),
    updateMember: vi.fn(),
    deleteMember: vi.fn(),
    getLoans: vi.fn(),
    getLoan: vi.fn(),
    checkoutLoan: vi.fn(),
    returnLoan: vi.fn(),
    renewLoan: vi.fn(),
    getReservations: vi.fn(),
    createReservation: vi.fn(),
    cancelReservation: vi.fn(),
    getFines: vi.fn(),
    getFine: vi.fn(),
    createFine: vi.fn(),
    waiveFine: vi.fn(),
  },
}));

// Mock studentsApi
vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn().mockResolvedValue({
      items: [
        { id: 'stud-1', first_name: 'Aarav', last_name: 'Sharma', admission_number: 'ADM-101' },
      ],
      total: 1,
    }),
  },
}));

// Mock teachersApi
vi.mock('@/services/api/teachersApi', () => ({
  teachersApi: {
    getTeachers: vi.fn().mockResolvedValue({
      items: [
        { id: 't-1', first_name: 'Rajesh', last_name: 'Verma', employee_id: 'EMP-001' },
      ],
      total: 1,
    }),
  },
}));

// Mock Data
const mockSummary: LibrarySummaryResponse = {
  total_libraries_count: 2,
  total_categories_count: 5,
  total_books_count: 120,
  total_copies_count: 350,
  available_copies_count: 280,
  issued_copies_count: 70,
  reserved_copies_count: 8,
  maintenance_copies_count: 2,
  active_members_count: 150,
  active_loans_count: 70,
  overdue_loans_count: 5,
  pending_reservations_count: 8,
  pending_fines_count: 3,
  pending_fines_amount: '450.00',
};

const mockLibraries: Library[] = [
  {
    id: 'lib-1',
    school_id: 'school-1',
    name: 'Central Campus Library',
    code: 'LIB-CENTRAL',
    location: 'Building A',
    is_active: true,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

const mockCategories: BookCategory[] = [
  {
    id: 'cat-1',
    school_id: 'school-1',
    name: 'Computer Science',
    code: 'CS',
    is_active: true,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

const mockBooks: Book[] = [
  {
    id: 'book-1',
    school_id: 'school-1',
    title: 'Clean Architecture',
    author: 'Robert C. Martin',
    isbn: '978-0134494166',
    category_name: 'Computer Science',
    library_name: 'Central Campus Library',
    language: 'English',
    is_active: true,
    copies_count: 5,
    available_copies_count: 3,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

const mockCopies: BookCopy[] = [
  {
    id: 'copy-1',
    school_id: 'school-1',
    book_id: 'book-1',
    book_title: 'Clean Architecture',
    book_author: 'Robert C. Martin',
    accession_number: 'ACC-1001',
    barcode: 'BAR-1001',
    shelf_location: 'Rack A1',
    status: 'AVAILABLE',
    condition: 'NEW',
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

const mockMembers: LibraryMember[] = [
  {
    id: 'mem-1',
    school_id: 'school-1',
    member_type: 'STUDENT',
    student_id: 'stud-1',
    card_number: 'CARD-STUD-101',
    issue_date: '2026-06-01',
    max_books_allowed: 3,
    status: 'ACTIVE',
    display_name: 'Aarav Sharma',
    active_loans_count: 1,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  },
];

const mockLoans: BookLoan[] = [
  {
    id: 'loan-1',
    school_id: 'school-1',
    book_copy_id: 'copy-1',
    member_id: 'mem-1',
    book_title: 'Clean Architecture',
    accession_number: 'ACC-1001',
    member_display_name: 'Aarav Sharma',
    member_card_number: 'CARD-STUD-101',
    issue_date: '2026-06-01',
    due_date: '2026-06-15',
    renewal_count: 0,
    status: 'ISSUED',
    created_at: '2026-06-01',
    updated_at: '2026-06-01',
  },
];

const mockReservations: BookReservation[] = [
  {
    id: 'res-1',
    school_id: 'school-1',
    book_id: 'book-1',
    member_id: 'mem-1',
    book_title: 'Clean Architecture',
    member_display_name: 'Aarav Sharma',
    member_card_number: 'CARD-STUD-101',
    reservation_date: '2026-06-10',
    expiry_date: '2026-06-17',
    status: 'PENDING',
    created_at: '2026-06-10',
    updated_at: '2026-06-10',
  },
];

const mockFines: LibraryFine[] = [
  {
    id: 'fine-1',
    school_id: 'school-1',
    loan_id: 'loan-1',
    member_id: 'mem-1',
    amount: '150.00',
    fine_reason: 'OVERDUE',
    status: 'PENDING',
    member_display_name: 'Aarav Sharma',
    member_card_number: 'CARD-STUD-101',
    book_title: 'Clean Architecture',
    created_at: '2026-06-16',
    updated_at: '2026-06-16',
  },
];

describe('LibraryPage Workstation Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useAuthStore.setState({
      user: { id: 'u-1', school_id: 'school-1', is_super_admin: true } as any,
      permissions: [
        'library.view',
        'library.create',
        'library.update',
        'library.delete',
        'library.circulate',
        'library.manage',
      ],
      roles: [{ name: 'Super Admin' }] as any,
    });

    vi.mocked(libraryApi.getSummary).mockResolvedValue(mockSummary);
    vi.mocked(libraryApi.getLibraries).mockResolvedValue({ items: mockLibraries, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getCategories).mockResolvedValue({ items: mockCategories, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getBooks).mockResolvedValue({ items: mockBooks, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getCopies).mockResolvedValue({ items: mockCopies, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getMembers).mockResolvedValue({ items: mockMembers, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getLoans).mockResolvedValue({ items: mockLoans, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getReservations).mockResolvedValue({ items: mockReservations, total: 1, page: 1, page_size: 10, total_pages: 1 });
    vi.mocked(libraryApi.getFines).mockResolvedValue({ items: mockFines, total: 1, page: 1, page_size: 10, total_pages: 1 });
  });

  it('1. Renders Library & Book Circulation header and KPI summary cards on Overview tab', async () => {
    render(<LibraryPage />);

    expect(screen.getByText('Library & Book Circulation')).toBeInTheDocument();

    await waitFor(() => {
      expect(libraryApi.getSummary).toHaveBeenCalled();
    });

    expect(await screen.findByText('Total Catalog Titles')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('Physical Inventory')).toBeInTheDocument();
    expect(screen.getByText('350')).toBeInTheDocument();
    expect(screen.getByText('Active Borrowers')).toBeInTheDocument();
    expect(screen.getByText('Central Campus Library')).toBeInTheDocument();
  });

  it('2. Switches to Book Catalog tab and renders book list', async () => {
    render(<LibraryPage />);

    const catalogTab = screen.getByRole('button', { name: /Book Catalog/i });
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(libraryApi.getBooks).toHaveBeenCalled();
    });

    expect(screen.getByText('Clean Architecture')).toBeInTheDocument();
    expect(screen.getByText('by Robert C. Martin')).toBeInTheDocument();
    expect(screen.getByText('978-0134494166')).toBeInTheDocument();
  });

  it('3. Opens Add Book modal, fills form, and submits creation payload', async () => {
    vi.mocked(libraryApi.createBook).mockResolvedValue(mockBooks[0]);

    render(<LibraryPage />);

    const catalogTab = screen.getByRole('button', { name: /Book Catalog/i });
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('Add Book Title')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Add Book Title'));

    expect(screen.getByText('Add New Book Title')).toBeInTheDocument();

    const titleInput = screen.getByPlaceholderText('e.g. Clean Architecture');
    const authorInput = screen.getByPlaceholderText('e.g. Robert C. Martin');

    fireEvent.change(titleInput, { target: { value: 'Refactoring' } });
    fireEvent.change(authorInput, { target: { value: 'Martin Fowler' } });

    const submitBtn = screen.getByRole('button', { name: /Create Book/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(libraryApi.createBook).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Refactoring',
          author: 'Martin Fowler',
        })
      );
    });
  });

  it('4. Switches to Physical Copies tab and renders inventory list', async () => {
    render(<LibraryPage />);

    const copiesTab = screen.getByRole('button', { name: /Physical Copies/i });
    fireEvent.click(copiesTab);

    await waitFor(() => {
      expect(libraryApi.getCopies).toHaveBeenCalled();
    });

    expect(screen.getByText('ACC-1001')).toBeInTheDocument();
    expect(screen.getByText('Rack A1')).toBeInTheDocument();
  });

  it('5. Switches to Members tab and registers member', async () => {
    vi.mocked(libraryApi.createMember).mockResolvedValue(mockMembers[0]);

    render(<LibraryPage />);

    const membersTab = screen.getByRole('button', { name: /Members/i });
    fireEvent.click(membersTab);

    await waitFor(() => {
      expect(libraryApi.getMembers).toHaveBeenCalled();
    });

    expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
    expect(screen.getByText('Card: CARD-STUD-101')).toBeInTheDocument();
  });

  it('6. Switches to Circulation tab and handles Return loan flow', async () => {
    vi.mocked(libraryApi.returnLoan).mockResolvedValue({
      ...mockLoans[0],
      status: 'RETURNED',
    });

    render(<LibraryPage />);

    const circTab = screen.getByRole('button', { name: /Circulation/i });
    fireEvent.click(circTab);

    await waitFor(() => {
      expect(libraryApi.getLoans).toHaveBeenCalled();
    });

    expect(screen.getByText('Clean Architecture')).toBeInTheDocument();
    expect(screen.getByText('Return')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Return'));

    expect(screen.getByText('Return Book Copy')).toBeInTheDocument();

    const confirmReturnBtn = screen.getByRole('button', { name: /Confirm Return/i });
    fireEvent.click(confirmReturnBtn);

    await waitFor(() => {
      expect(libraryApi.returnLoan).toHaveBeenCalledWith('loan-1', expect.any(Object));
    });
  });

  it('7. Switches to Reservations tab and cancels reservation', async () => {
    vi.mocked(libraryApi.cancelReservation).mockResolvedValue({
      ...mockReservations[0],
      status: 'CANCELLED',
    });

    render(<LibraryPage />);

    const resTab = screen.getByRole('button', { name: /Reservations/i });
    fireEvent.click(resTab);

    await waitFor(() => {
      expect(libraryApi.getReservations).toHaveBeenCalled();
    });

    expect(screen.getByText('Cancel Hold')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Cancel Hold'));

    await waitFor(() => {
      expect(screen.getByText(/Cancel reservation hold/i)).toBeInTheDocument();
    });

    const confirmCancelBtn = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      expect(libraryApi.cancelReservation).toHaveBeenCalledWith('res-1');
    });
  });

  it('8. Switches to Fines tab and handles fine waiver', async () => {
    vi.mocked(libraryApi.waiveFine).mockResolvedValue({
      ...mockFines[0],
      status: 'WAIVED',
      waived_reason: 'Principal waiver',
    });

    render(<LibraryPage />);

    const finesTab = screen.getByRole('button', { name: /Fines Ledger/i });
    fireEvent.click(finesTab);

    await waitFor(() => {
      expect(libraryApi.getFines).toHaveBeenCalled();
    });

    expect(screen.getByText('₹150.00')).toBeInTheDocument();
    expect(screen.getByText('Waive Fine')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Waive Fine'));

    expect(screen.getByText(/Waiving fine of ₹150.00/i)).toBeInTheDocument();

    const reasonInput = screen.getByPlaceholderText(/Principal special exemption/i);
    fireEvent.change(reasonInput, { target: { value: 'Principal approved exemption' } });

    const confirmWaiveBtn = screen.getByRole('button', { name: /Confirm Waiver/i });
    fireEvent.click(confirmWaiveBtn);

    await waitFor(() => {
      expect(libraryApi.waiveFine).toHaveBeenCalledWith('fine-1', {
        waived_reason: 'Principal approved exemption',
      });
    });
  });

  it('9. Enforces RBAC visibility rules for view-only users', async () => {
    useAuthStore.setState({
      user: { id: 'u-viewer', school_id: 'school-1', is_super_admin: false } as any,
      permissions: ['library.view'],
      roles: [{ name: 'Viewer' }] as any,
    });

    render(<LibraryPage />);

    // Header mutation buttons should NOT appear for view-only users
    expect(screen.queryByText('Add Book')).not.toBeInTheDocument();
    expect(screen.queryByText('Issue / Checkout')).not.toBeInTheDocument();

    // Switch to Catalog
    const catalogTab = screen.getByRole('button', { name: /Book Catalog/i });
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(libraryApi.getBooks).toHaveBeenCalled();
    });

    // Add Book Title button should NOT be visible
    expect(screen.queryByText('Add Book Title')).not.toBeInTheDocument();
  });
});
