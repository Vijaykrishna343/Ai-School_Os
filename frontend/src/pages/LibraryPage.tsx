import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Library as LibraryIcon,
  Users,
  Repeat,
  Bookmark,
  DollarSign,
  Search,
  Plus,
  Edit2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { libraryApi } from '@/services/api/libraryApi';
import { studentsApi } from '@/services/api/studentsApi';
import { teachersApi } from '@/services/api/teachersApi';
import {
  Book,
  BookCategory,
  BookCondition,
  BookCopy,
  BookCopyCreate,
  BookCopyUpdate,
  BookCreate,
  BookLoan,
  BookLoanCheckout,
  BookReservation,
  BookReservationCreate,
  BookUpdate,
  Library,
  LibraryFine,
  LibraryFineCreate,
  LibraryFineReason,
  LibraryMember,
  LibraryMemberCreate,
  LibraryMemberType,
  LibraryMemberUpdate,
  LibrarySummaryResponse,
  Student,
  Teacher,
} from '@/types/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';

export const LibraryPage: React.FC = () => {
  const { user, permissions, roles } = useAuthStore();
  const isSuperAdmin =
    user?.is_super_admin ||
    roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');

  const hasPermission = (perm: string) => isSuperAdmin || permissions.includes(perm);

  const canCreate = hasPermission('library.create');
  const canUpdate = hasPermission('library.update');
  const canDelete = hasPermission('library.delete');
  const canCirculate = hasPermission('library.circulate');
  const canManage = hasPermission('library.manage');

  // Active Tab
  const [activeTab, setActiveTab] = useState<
    'dashboard' | 'catalog' | 'copies' | 'members' | 'circulation' | 'reservations' | 'fines'
  >('dashboard');

  // Reference Data
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [categories, setCategories] = useState<BookCategory[]>([]);
  const [studentsList, setStudentsList] = useState<Student[]>([]);
  const [teachersList, setTeachersList] = useState<Teacher[]>([]);

  // Dashboard State
  const [summary, setSummary] = useState<LibrarySummaryResponse | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Books State
  const [books, setBooks] = useState<Book[]>([]);
  const [bookSearch, setBookSearch] = useState('');
  const [bookCategoryFilter, setBookCategoryFilter] = useState('');
  const [bookLibraryFilter, setBookLibraryFilter] = useState('');
  const [bookPage, setBookPage] = useState(1);
  const [bookTotalPages, setBookTotalPages] = useState(1);
  const [loadingBooks, setLoadingBooks] = useState(false);
  const [bookError, setBookError] = useState<string | null>(null);

  const [showBookModal, setShowBookModal] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [bookFormData, setBookFormData] = useState<BookCreate>({
    title: '',
    author: '',
    isbn: '',
    publisher: '',
    language: 'English',
    category_id: '',
    library_id: '',
    total_pages: undefined,
    publication_year: undefined,
    description: '',
  });
  const [bookSaving, setBookSaving] = useState(false);
  const [deleteBookTarget, setDeleteBookTarget] = useState<Book | null>(null);

  // Book Copies State
  const [copies, setCopies] = useState<BookCopy[]>([]);
  const [copySearch, setCopySearch] = useState('');
  const [copyStatusFilter, setCopyStatusFilter] = useState('');
  const [copyConditionFilter, setCopyConditionFilter] = useState('');
  const [copyBookFilter, setCopyBookFilter] = useState('');
  const [copyPage, setCopyPage] = useState(1);
  const [copyTotalPages, setCopyTotalPages] = useState(1);
  const [loadingCopies, setLoadingCopies] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);

  const [showCopyModal, setShowCopyModal] = useState(false);
  const [editingCopy, setEditingCopy] = useState<BookCopy | null>(null);
  const [copyFormData, setCopyFormData] = useState<BookCopyCreate>({
    book_id: '',
    accession_number: '',
    barcode: '',
    shelf_location: '',
    acquisition_price: '',
    status: 'AVAILABLE',
    condition: 'NEW',
    remarks: '',
  });
  const [copySaving, setCopySaving] = useState(false);
  const [deleteCopyTarget, setDeleteCopyTarget] = useState<BookCopy | null>(null);

  // Members State
  const [members, setMembers] = useState<LibraryMember[]>([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [memberTypeFilter, setMemberTypeFilter] = useState('');
  const [memberStatusFilter, setMemberStatusFilter] = useState('');
  const [memberPage, setMemberPage] = useState(1);
  const [memberTotalPages, setMemberTotalPages] = useState(1);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);

  const [showMemberModal, setShowMemberModal] = useState(false);
  const [editingMember, setEditingMember] = useState<LibraryMember | null>(null);
  const [memberFormData, setMemberFormData] = useState<LibraryMemberCreate>({
    member_type: 'STUDENT',
    student_id: '',
    teacher_id: '',
    card_number: '',
    max_books_allowed: 3,
    status: 'ACTIVE',
    remarks: '',
  });
  const [memberSaving, setMemberSaving] = useState(false);
  const [deleteMemberTarget, setDeleteMemberTarget] = useState<LibraryMember | null>(null);

  // Loans State
  const [loans, setLoans] = useState<BookLoan[]>([]);
  const [loanSearch, setLoanSearch] = useState('');
  const [loanStatusFilter, setLoanStatusFilter] = useState('');
  const [loanOverdueFilter, setLoanOverdueFilter] = useState(false);
  const [loanPage, setLoanPage] = useState(1);
  const [loanTotalPages, setLoanTotalPages] = useState(1);
  const [loadingLoans, setLoadingLoans] = useState(false);
  const [loanError, setLoanError] = useState<string | null>(null);

  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [checkoutFormData, setCheckoutFormData] = useState<BookLoanCheckout>({
    member_id: '',
    book_copy_id: '',
    due_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
    remarks: '',
  });
  const [checkoutSaving, setCheckoutSaving] = useState(false);

  const [returningLoan, setReturningLoan] = useState<BookLoan | null>(null);
  const [returnRemarks, setReturnRemarks] = useState('');
  const [returnSaving, setReturnSaving] = useState(false);

  const [renewingLoan, setRenewingLoan] = useState<BookLoan | null>(null);
  const [renewDueDate, setRenewDueDate] = useState('');
  const [renewRemarks, setRenewRemarks] = useState('');
  const [renewSaving, setRenewSaving] = useState(false);

  // Reservations State
  const [reservations, setReservations] = useState<BookReservation[]>([]);
  const [reservationStatusFilter, setReservationStatusFilter] = useState('');
  const [reservationPage, setReservationPage] = useState(1);
  const [reservationTotalPages, setReservationTotalPages] = useState(1);
  const [loadingReservations, setLoadingReservations] = useState(false);
  const [reservationError, setReservationError] = useState<string | null>(null);

  const [showReservationModal, setShowReservationModal] = useState(false);
  const [reservationFormData, setReservationFormData] = useState<BookReservationCreate>({
    book_id: '',
    member_id: '',
    reservation_date: new Date().toISOString().split('T')[0],
    expiry_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0],
    remarks: '',
  });
  const [reservationSaving, setReservationSaving] = useState(false);
  const [cancelReservationTarget, setCancelReservationTarget] = useState<BookReservation | null>(null);

  // Fines State
  const [fines, setFines] = useState<LibraryFine[]>([]);
  const [fineStatusFilter, setFineStatusFilter] = useState('');
  const [fineReasonFilter, setFineReasonFilter] = useState('');
  const [finePage, setFinePage] = useState(1);
  const [fineTotalPages, setFineTotalPages] = useState(1);
  const [loadingFines, setLoadingFines] = useState(false);
  const [fineError, setFineError] = useState<string | null>(null);

  const [showFineModal, setShowFineModal] = useState(false);
  const [fineFormData, setFineFormData] = useState<LibraryFineCreate>({
    loan_id: '',
    member_id: '',
    amount: '50.00',
    fine_reason: 'OVERDUE',
    remarks: '',
  });
  const [fineSaving, setFineSaving] = useState(false);

  const [waivingFine, setWaivingFine] = useState<LibraryFine | null>(null);
  const [waiveReason, setWaiveReason] = useState('');
  const [waiveSaving, setWaiveSaving] = useState(false);

  // Feedback Toast
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback(null), 5000);
  };

  useEffect(() => {
    loadMasterReferences();
  }, []);

  const loadMasterReferences = async () => {
    try {
      const [libRes, catRes, studRes, teachRes] = await Promise.all([
        libraryApi.getLibraries({ page_size: 100 }),
        libraryApi.getCategories({ page_size: 100 }),
        studentsApi.getStudents({ page: 1, page_size: 100 } as any),
        teachersApi.getTeachers({ page: 1, page_size: 100 } as any),
      ]);
      setLibraries(libRes?.items || []);
      setCategories(catRes?.items || []);
      setStudentsList((studRes as any)?.items || (studRes as any)?.data || []);
      setTeachersList((teachRes as any)?.items || (teachRes as any)?.data || []);
    } catch (err) {
      console.error('Failed to load master references', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'dashboard') fetchDashboardStats();
    if (activeTab === 'catalog') fetchBooks();
    if (activeTab === 'copies') fetchCopies();
    if (activeTab === 'members') fetchMembers();
    if (activeTab === 'circulation') fetchLoans();
    if (activeTab === 'reservations') fetchReservations();
    if (activeTab === 'fines') fetchFines();
  }, [
    activeTab,
    bookPage,
    bookSearch,
    bookCategoryFilter,
    bookLibraryFilter,
    copyPage,
    copySearch,
    copyStatusFilter,
    copyConditionFilter,
    copyBookFilter,
    memberPage,
    memberSearch,
    memberTypeFilter,
    memberStatusFilter,
    loanPage,
    loanSearch,
    loanStatusFilter,
    loanOverdueFilter,
    reservationPage,
    reservationStatusFilter,
    finePage,
    fineStatusFilter,
    fineReasonFilter,
  ]);

  const fetchDashboardStats = async () => {
    try {
      setLoadingSummary(true);
      setSummaryError(null);
      const res = await libraryApi.getSummary();
      setSummary(res);
    } catch (err: any) {
      setSummaryError(err.response?.data?.detail || err.message || 'Failed to load summary stats');
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchBooks = async () => {
    try {
      setLoadingBooks(true);
      setBookError(null);
      const res = await libraryApi.getBooks({
        search: bookSearch || undefined,
        category_id: bookCategoryFilter || undefined,
        library_id: bookLibraryFilter || undefined,
        page: bookPage,
        page_size: 10,
      });
      setBooks(res?.items || []);
      setBookTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setBookError(err.response?.data?.detail || err.message || 'Failed to load books');
    } finally {
      setLoadingBooks(false);
    }
  };

  const fetchCopies = async () => {
    try {
      setLoadingCopies(true);
      setCopyError(null);
      const res = await libraryApi.getCopies({
        search: copySearch || undefined,
        status: copyStatusFilter || undefined,
        condition: copyConditionFilter || undefined,
        book_id: copyBookFilter || undefined,
        page: copyPage,
        page_size: 10,
      });
      setCopies(res?.items || []);
      setCopyTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setCopyError(err.response?.data?.detail || err.message || 'Failed to load copies');
    } finally {
      setLoadingCopies(false);
    }
  };

  const fetchMembers = async () => {
    try {
      setLoadingMembers(true);
      setMemberError(null);
      const res = await libraryApi.getMembers({
        search: memberSearch || undefined,
        member_type: memberTypeFilter || undefined,
        status: memberStatusFilter || undefined,
        page: memberPage,
        page_size: 10,
      });
      setMembers(res?.items || []);
      setMemberTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setMemberError(err.response?.data?.detail || err.message || 'Failed to load members');
    } finally {
      setLoadingMembers(false);
    }
  };

  const fetchLoans = async () => {
    try {
      setLoadingLoans(true);
      setLoanError(null);
      const res = await libraryApi.getLoans({
        search: loanSearch || undefined,
        status: loanStatusFilter || undefined,
        overdue_only: loanOverdueFilter || undefined,
        page: loanPage,
        page_size: 10,
      });
      setLoans(res?.items || []);
      setLoanTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setLoanError(err.response?.data?.detail || err.message || 'Failed to load loans');
    } finally {
      setLoadingLoans(false);
    }
  };

  const fetchReservations = async () => {
    try {
      setLoadingReservations(true);
      setReservationError(null);
      const res = await libraryApi.getReservations({
        status: reservationStatusFilter || undefined,
        page: reservationPage,
        page_size: 10,
      });
      setReservations(res?.items || []);
      setReservationTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setReservationError(err.response?.data?.detail || err.message || 'Failed to load reservations');
    } finally {
      setLoadingReservations(false);
    }
  };

  const fetchFines = async () => {
    try {
      setLoadingFines(true);
      setFineError(null);
      const res = await libraryApi.getFines({
        status: fineStatusFilter || undefined,
        fine_reason: fineReasonFilter || undefined,
        page: finePage,
        page_size: 10,
      });
      setFines(res?.items || []);
      setFineTotalPages(Math.ceil((res?.total || 1) / 10));
    } catch (err: any) {
      setFineError(err.response?.data?.detail || err.message || 'Failed to load fines');
    } finally {
      setLoadingFines(false);
    }
  };

  // Book Handlers
  const handleOpenBookModal = (book?: Book) => {
    if (book) {
      setEditingBook(book);
      setBookFormData({
        title: book.title,
        subtitle: book.subtitle || '',
        author: book.author,
        publisher: book.publisher || '',
        publication_year: book.publication_year || undefined,
        isbn: book.isbn || '',
        edition: book.edition || '',
        language: book.language || 'English',
        category_id: book.category_id || '',
        library_id: book.library_id || '',
        total_pages: book.total_pages || undefined,
        description: book.description || '',
      });
    } else {
      setEditingBook(null);
      setBookFormData({
        title: '',
        author: '',
        language: 'English',
        category_id: categories[0]?.id || '',
        library_id: libraries[0]?.id || '',
        description: '',
      });
    }
    setShowBookModal(true);
  };

  const handleSaveBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookFormData.title || !bookFormData.author) {
      showFeedback('error', 'Title and Author are required.');
      return;
    }
    try {
      setBookSaving(true);
      if (editingBook) {
        await libraryApi.updateBook(editingBook.id, bookFormData as BookUpdate);
        showFeedback('success', 'Book title updated successfully.');
      } else {
        await libraryApi.createBook(bookFormData);
        showFeedback('success', 'Book title created successfully.');
      }
      setShowBookModal(false);
      fetchBooks();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to save book.');
    } finally {
      setBookSaving(false);
    }
  };

  const handleDeleteBook = async () => {
    if (!deleteBookTarget) return;
    try {
      await libraryApi.deleteBook(deleteBookTarget.id);
      showFeedback('success', `Book '${deleteBookTarget.title}' removed.`);
      setDeleteBookTarget(null);
      fetchBooks();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to delete book.');
    }
  };

  // Copy Handlers
  const handleOpenCopyModal = (copy?: BookCopy) => {
    if (copy) {
      setEditingCopy(copy);
      setCopyFormData({
        book_id: copy.book_id,
        library_id: copy.library_id || '',
        accession_number: copy.accession_number,
        barcode: copy.barcode || '',
        shelf_location: copy.shelf_location || '',
        acquisition_price: copy.acquisition_price || '',
        status: copy.status,
        condition: copy.condition,
        remarks: copy.remarks || '',
      });
    } else {
      setEditingCopy(null);
      setCopyFormData({
        book_id: books[0]?.id || '',
        library_id: libraries[0]?.id || '',
        accession_number: `ACC-${Math.floor(1000 + Math.random() * 9000)}`,
        barcode: `BAR-${Math.floor(1000 + Math.random() * 9000)}`,
        shelf_location: 'Rack A1',
        acquisition_price: '500.00',
        status: 'AVAILABLE',
        condition: 'NEW',
        remarks: '',
      });
    }
    setShowCopyModal(true);
  };

  const handleSaveCopy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!copyFormData.book_id || !copyFormData.accession_number) {
      showFeedback('error', 'Book and Accession Number are required.');
      return;
    }
    try {
      setCopySaving(true);
      if (editingCopy) {
        await libraryApi.updateCopy(editingCopy.id, copyFormData as BookCopyUpdate);
        showFeedback('success', 'Physical copy updated successfully.');
      } else {
        await libraryApi.createCopy(copyFormData);
        showFeedback('success', 'Physical copy added to inventory.');
      }
      setShowCopyModal(false);
      fetchCopies();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to save copy.');
    } finally {
      setCopySaving(false);
    }
  };

  const handleDeleteCopy = async () => {
    if (!deleteCopyTarget) return;
    try {
      await libraryApi.deleteCopy(deleteCopyTarget.id);
      showFeedback('success', `Copy '${deleteCopyTarget.accession_number}' deleted.`);
      setDeleteCopyTarget(null);
      fetchCopies();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to delete copy.');
    }
  };

  // Member Handlers
  const handleOpenMemberModal = (member?: LibraryMember) => {
    if (member) {
      setEditingMember(member);
      setMemberFormData({
        member_type: member.member_type,
        student_id: member.student_id || '',
        teacher_id: member.teacher_id || '',
        card_number: member.card_number,
        max_books_allowed: member.max_books_allowed,
        status: member.status,
        remarks: member.remarks || '',
      });
    } else {
      setEditingMember(null);
      setMemberFormData({
        member_type: 'STUDENT',
        student_id: studentsList[0]?.id || '',
        teacher_id: '',
        card_number: `CARD-${Math.floor(1000 + Math.random() * 9000)}`,
        max_books_allowed: 3,
        status: 'ACTIVE',
        remarks: '',
      });
    }
    setShowMemberModal(true);
  };

  const handleSaveMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberFormData.card_number) {
      showFeedback('error', 'Card Number is required.');
      return;
    }
    if (memberFormData.member_type === 'STUDENT' && !memberFormData.student_id) {
      showFeedback('error', 'Student must be selected for student membership.');
      return;
    }
    if (memberFormData.member_type === 'TEACHER' && !memberFormData.teacher_id) {
      showFeedback('error', 'Teacher must be selected for teacher membership.');
      return;
    }
    try {
      setMemberSaving(true);
      if (editingMember) {
        await libraryApi.updateMember(editingMember.id, memberFormData as LibraryMemberUpdate);
        showFeedback('success', 'Library membership updated.');
      } else {
        await libraryApi.createMember(memberFormData);
        showFeedback('success', 'Library membership registered.');
      }
      setShowMemberModal(false);
      fetchMembers();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to save member.');
    } finally {
      setMemberSaving(false);
    }
  };

  const handleDeleteMember = async () => {
    if (!deleteMemberTarget) return;
    try {
      await libraryApi.deleteMember(deleteMemberTarget.id);
      showFeedback('success', `Member '${deleteMemberTarget.card_number}' deactivated.`);
      setDeleteMemberTarget(null);
      fetchMembers();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to deactivate member.');
    }
  };

  // Circulation Handlers
  const handleOpenCheckoutModal = () => {
    setCheckoutFormData({
      member_id: members[0]?.id || '',
      book_copy_id: copies.find((c) => c.status === 'AVAILABLE')?.id || '',
      due_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
      remarks: '',
    });
    setShowCheckoutModal(true);
  };

  const handleCheckoutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkoutFormData.member_id || !checkoutFormData.book_copy_id) {
      showFeedback('error', 'Please select both a Member and an available Book Copy.');
      return;
    }
    try {
      setCheckoutSaving(true);
      await libraryApi.checkoutLoan(checkoutFormData);
      showFeedback('success', 'Book successfully checked out.');
      setShowCheckoutModal(false);
      fetchLoans();
      if (activeTab === 'dashboard') fetchDashboardStats();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Checkout failed.');
    } finally {
      setCheckoutSaving(false);
    }
  };

  const handleReturnSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returningLoan) return;
    try {
      setReturnSaving(true);
      await libraryApi.returnLoan(returningLoan.id, {
        return_date: new Date().toISOString().split('T')[0],
        remarks: returnRemarks,
      });
      showFeedback('success', `Book loan #${returningLoan.accession_number || returningLoan.id} returned.`);
      setReturningLoan(null);
      setReturnRemarks('');
      fetchLoans();
      if (activeTab === 'dashboard') fetchDashboardStats();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Return failed.');
    } finally {
      setReturnSaving(false);
    }
  };

  const handleRenewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renewingLoan) return;
    try {
      setRenewSaving(true);
      await libraryApi.renewLoan(renewingLoan.id, {
        new_due_date: renewDueDate || new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
        remarks: renewRemarks,
      });
      showFeedback('success', `Loan renewed successfully.`);
      setRenewingLoan(null);
      setRenewDueDate('');
      setRenewRemarks('');
      fetchLoans();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Renewal failed.');
    } finally {
      setRenewSaving(false);
    }
  };

  // Reservation Handlers
  const handleOpenReservationModal = () => {
    setReservationFormData({
      book_id: books[0]?.id || '',
      member_id: members[0]?.id || '',
      reservation_date: new Date().toISOString().split('T')[0],
      expiry_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0],
      remarks: '',
    });
    setShowReservationModal(true);
  };

  const handleSaveReservation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reservationFormData.book_id || !reservationFormData.member_id) {
      showFeedback('error', 'Book and Member are required.');
      return;
    }
    try {
      setReservationSaving(true);
      await libraryApi.createReservation(reservationFormData);
      showFeedback('success', 'Book reservation placed.');
      setShowReservationModal(false);
      fetchReservations();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Reservation failed.');
    } finally {
      setReservationSaving(false);
    }
  };

  const handleCancelReservation = async () => {
    if (!cancelReservationTarget) return;
    try {
      await libraryApi.cancelReservation(cancelReservationTarget.id);
      showFeedback('success', 'Reservation cancelled.');
      setCancelReservationTarget(null);
      fetchReservations();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Failed to cancel reservation.');
    }
  };

  // Fine Handlers
  const handleOpenFineModal = () => {
    setFineFormData({
      loan_id: loans[0]?.id || '',
      member_id: loans[0]?.member_id || members[0]?.id || '',
      amount: '50.00',
      fine_reason: 'OVERDUE',
      remarks: '',
    });
    setShowFineModal(true);
  };

  const handleSaveFine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fineFormData.loan_id || !fineFormData.member_id || !fineFormData.amount) {
      showFeedback('error', 'Loan, Member, and Amount are required.');
      return;
    }
    try {
      setFineSaving(true);
      await libraryApi.createFine(fineFormData);
      showFeedback('success', 'Fine assessed successfully.');
      setShowFineModal(false);
      fetchFines();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Fine assessment failed.');
    } finally {
      setFineSaving(false);
    }
  };

  const handleWaiveFineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!waivingFine || !waiveReason) {
      showFeedback('error', 'A waiver reason is required.');
      return;
    }
    try {
      setWaiveSaving(true);
      await libraryApi.waiveFine(waivingFine.id, { waived_reason: waiveReason });
      showFeedback('success', `Fine of ₹${waivingFine.amount} waived.`);
      setWaivingFine(null);
      setWaiveReason('');
      fetchFines();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || err.message || 'Waiver failed.');
    } finally {
      setWaiveSaving(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-indigo-600" />
            Library & Book Circulation
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage catalog, physical inventory, member borrowing, circulation loans, reservations, and fines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {canCirculate && (
            <Button
              variant="outline"
              onClick={handleOpenCheckoutModal}
              className="border-indigo-600 text-indigo-600 hover:bg-indigo-50"
            >
              <Repeat className="w-4 h-4 mr-2" />
              Issue / Checkout
            </Button>
          )}
          {canCreate && (
            <Button onClick={() => handleOpenBookModal()} className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Add Book
            </Button>
          )}
        </div>
      </div>

      {/* Toast Feedback */}
      {feedback && (
        <Alert type={feedback.type === 'success' ? 'success' : 'error'} className="transition-all">
          <span>{feedback.message}</span>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-4 overflow-x-auto pb-2" aria-label="Tabs">
          {[
            { id: 'dashboard', label: 'Overview', icon: LibraryIcon },
            { id: 'catalog', label: 'Book Catalog', icon: BookOpen },
            { id: 'copies', label: 'Physical Copies', icon: Layers },
            { id: 'members', label: 'Members', icon: Users },
            { id: 'circulation', label: 'Circulation', icon: Repeat },
            { id: 'reservations', label: 'Reservations', icon: Bookmark },
            { id: 'fines', label: 'Fines Ledger', icon: DollarSign },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-gray-400'}`} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* 1. OVERVIEW & ANALYTICS TAB */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {loadingSummary ? (
            <LoadingState message="Loading library metrics..." />
          ) : summaryError ? (
            <ErrorState message={summaryError} onRetry={fetchDashboardStats} />
          ) : summary ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase">Total Catalog Titles</p>
                      <h3 className="text-2xl font-bold text-gray-900 mt-1">{summary.total_books_count}</h3>
                      <p className="text-xs text-gray-400 mt-1">{summary.total_categories_count} Categories</p>
                    </div>
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                      <BookOpen className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase">Physical Inventory</p>
                      <h3 className="text-2xl font-bold text-gray-900 mt-1">{summary.total_copies_count}</h3>
                      <div className="flex gap-2 text-xs mt-1">
                        <span className="text-emerald-600 font-medium">{summary.available_copies_count} Available</span>
                        <span className="text-gray-300">|</span>
                        <span className="text-indigo-600 font-medium">{summary.issued_copies_count} Issued</span>
                      </div>
                    </div>
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                      <Layers className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase">Active Borrowers</p>
                      <h3 className="text-2xl font-bold text-gray-900 mt-1">{summary.active_members_count}</h3>
                      <p className="text-xs text-gray-400 mt-1">{summary.active_loans_count} Active Loans</p>
                    </div>
                    <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
                      <Users className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase">Overdue / Fines</p>
                      <h3 className="text-2xl font-bold text-amber-600 mt-1">{summary.overdue_loans_count}</h3>
                      <p className="text-xs text-red-500 font-medium mt-1">
                        ₹{summary.pending_fines_amount} ({summary.pending_fines_count} fines)
                      </p>
                    </div>
                    <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                      <Clock className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <LibraryIcon className="w-5 h-5 text-indigo-600" />
                      Physical Library Facilities
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {libraries.length === 0 ? (
                      <p className="text-sm text-gray-500">No physical library facilities configured.</p>
                    ) : (
                      <div className="divide-y divide-gray-100">
                        {libraries.map((lib) => (
                          <div key={lib.id} className="py-3 flex justify-between items-center">
                            <div>
                              <p className="text-sm font-semibold text-gray-900">{lib.name}</p>
                              <p className="text-xs text-gray-500">{lib.location || 'Main Campus'} • Code: {lib.code}</p>
                            </div>
                            <Badge variant={lib.is_active ? 'success' : 'neutral'}>
                              {lib.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Repeat className="w-5 h-5 text-indigo-600" />
                      Circulation Quick Desk
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-gray-500">
                      Issue physical books to students and teachers, record returns, extend loan terms, or reserve titles.
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2">
                      {canCirculate && (
                        <Button onClick={handleOpenCheckoutModal} className="bg-indigo-600 text-white">
                          <Repeat className="w-4 h-4 mr-2" />
                          New Checkout
                        </Button>
                      )}
                      {canCirculate && (
                        <Button variant="outline" onClick={handleOpenReservationModal}>
                          <Bookmark className="w-4 h-4 mr-2" />
                          Reserve Book
                        </Button>
                      )}
                      {canManage && (
                        <Button variant="outline" onClick={handleOpenFineModal}>
                          <DollarSign className="w-4 h-4 mr-2" />
                          Assess Fine
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* 2. BOOK CATALOG TAB */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <div className="flex flex-1 gap-2 flex-wrap items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Search by title, author, ISBN..."
                  value={bookSearch}
                  onChange={(e) => setBookSearch(e.target.value)}
                  className="pl-9"
                />
              </div>

              <select
                value={bookCategoryFilter}
                onChange={(e) => setBookCategoryFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>

              <select
                value={bookLibraryFilter}
                onChange={(e) => setBookLibraryFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Libraries</option>
                {libraries.map((lib) => (
                  <option key={lib.id} value={lib.id}>
                    {lib.name}
                  </option>
                ))}
              </select>
            </div>

            {canCreate && (
              <Button onClick={() => handleOpenBookModal()} className="bg-indigo-600 text-white shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                Add Book Title
              </Button>
            )}
          </div>

          {loadingBooks ? (
            <LoadingState message="Loading catalog..." />
          ) : bookError ? (
            <ErrorState message={bookError} onRetry={fetchBooks} />
          ) : books.length === 0 ? (
            <EmptyState
              title="No books in catalog"
              description="Start building your school catalog by adding book titles."
              action={
                canCreate ? (
                  <Button onClick={() => handleOpenBookModal()} className="bg-indigo-600 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Add First Book
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Title & Author</th>
                      <th className="p-3 font-semibold">Category</th>
                      <th className="p-3 font-semibold">ISBN</th>
                      <th className="p-3 font-semibold">Copies Available</th>
                      <th className="p-3 font-semibold">Library Facility</th>
                      <th className="p-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {books.map((book) => (
                      <tr key={book.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900">{book.title}</p>
                          <p className="text-xs text-gray-500">by {book.author}</p>
                        </td>
                        <td className="p-3">
                          <Badge variant="neutral">{book.category_name || 'General'}</Badge>
                        </td>
                        <td className="p-3 font-mono text-xs text-gray-600">{book.isbn || '—'}</td>
                        <td className="p-3">
                          <span className="font-medium text-emerald-600">{book.available_copies_count ?? 0}</span>
                          <span className="text-gray-400"> / {book.copies_count ?? 0}</span>
                        </td>
                        <td className="p-3 text-gray-600">{book.library_name || 'Main Library'}</td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {canUpdate && (
                              <Button variant="ghost" size="sm" onClick={() => handleOpenBookModal(book)}>
                                <Edit2 className="w-4 h-4 text-gray-600" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteBookTarget(book)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={bookPage} totalPages={bookTotalPages} onPageChange={setBookPage} />
            </Card>
          )}
        </div>
      )}

      {/* 3. PHYSICAL COPIES TAB */}
      {activeTab === 'copies' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <div className="flex flex-1 gap-2 flex-wrap items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Search accession number, barcode..."
                  value={copySearch}
                  onChange={(e) => setCopySearch(e.target.value)}
                  className="pl-9"
                />
              </div>

              <select
                value={copyStatusFilter}
                onChange={(e) => setCopyStatusFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Statuses</option>
                <option value="AVAILABLE">Available</option>
                <option value="ISSUED">Issued</option>
                <option value="RESERVED">Reserved</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="LOST">Lost</option>
                <option value="DAMAGED">Damaged</option>
              </select>

              <select
                value={copyConditionFilter}
                onChange={(e) => setCopyConditionFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Conditions</option>
                <option value="NEW">New</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
              </select>
            </div>

            {canCreate && (
              <Button onClick={() => handleOpenCopyModal()} className="bg-indigo-600 text-white shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                Add Physical Copy
              </Button>
            )}
          </div>

          {loadingCopies ? (
            <LoadingState message="Loading physical inventory..." />
          ) : copyError ? (
            <ErrorState message={copyError} onRetry={fetchCopies} />
          ) : copies.length === 0 ? (
            <EmptyState
              title="No physical copies found"
              description="Register physical copy barcodes and accession numbers."
              action={
                canCreate ? (
                  <Button onClick={() => handleOpenCopyModal()} className="bg-indigo-600 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Copy
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Accession / Barcode</th>
                      <th className="p-3 font-semibold">Book Title</th>
                      <th className="p-3 font-semibold">Location</th>
                      <th className="p-3 font-semibold">Condition</th>
                      <th className="p-3 font-semibold">Status</th>
                      <th className="p-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {copies.map((copy) => (
                      <tr key={copy.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900 font-mono">{copy.accession_number}</p>
                          <p className="text-xs text-gray-500 font-mono">{copy.barcode || 'No Barcode'}</p>
                        </td>
                        <td className="p-3">
                          <p className="font-medium text-gray-900">{copy.book_title}</p>
                          <p className="text-xs text-gray-500">{copy.book_author}</p>
                        </td>
                        <td className="p-3 text-gray-600">{copy.shelf_location || 'Unassigned'}</td>
                        <td className="p-3">
                          <Badge variant="neutral">{copy.condition}</Badge>
                        </td>
                        <td className="p-3">
                          <Badge
                            variant={
                              copy.status === 'AVAILABLE'
                                ? 'success'
                                : copy.status === 'ISSUED'
                                ? 'info'
                                : 'error'
                            }
                          >
                            {copy.status}
                          </Badge>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {canUpdate && (
                              <Button variant="ghost" size="sm" onClick={() => handleOpenCopyModal(copy)}>
                                <Edit2 className="w-4 h-4 text-gray-600" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteCopyTarget(copy)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={copyPage} totalPages={copyTotalPages} onPageChange={setCopyPage} />
            </Card>
          )}
        </div>
      )}

      {/* 4. MEMBERS DIRECTORY TAB */}
      {activeTab === 'members' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <div className="flex flex-1 gap-2 flex-wrap items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Search card number, member name..."
                  value={memberSearch}
                  onChange={(e) => setMemberSearch(e.target.value)}
                  className="pl-9"
                />
              </div>

              <select
                value={memberTypeFilter}
                onChange={(e) => setMemberTypeFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Types</option>
                <option value="STUDENT">Student</option>
                <option value="TEACHER">Teacher</option>
                <option value="STAFF">Staff</option>
              </select>

              <select
                value={memberStatusFilter}
                onChange={(e) => setMemberStatusFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="SUSPENDED">Suspended</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>

            {canCreate && (
              <Button onClick={() => handleOpenMemberModal()} className="bg-indigo-600 text-white shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                Register Member
              </Button>
            )}
          </div>

          {loadingMembers ? (
            <LoadingState message="Loading members..." />
          ) : memberError ? (
            <ErrorState message={memberError} onRetry={fetchMembers} />
          ) : members.length === 0 ? (
            <EmptyState
              title="No library members registered"
              description="Register student and faculty memberships to enable borrowing."
              action={
                canCreate ? (
                  <Button onClick={() => handleOpenMemberModal()} className="bg-indigo-600 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Register Member
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Card / Identity</th>
                      <th className="p-3 font-semibold">Type</th>
                      <th className="p-3 font-semibold">Borrowing Limit</th>
                      <th className="p-3 font-semibold">Active Loans</th>
                      <th className="p-3 font-semibold">Status</th>
                      <th className="p-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {members.map((mem) => (
                      <tr key={mem.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900">{mem.display_name || 'Member'}</p>
                          <p className="text-xs text-gray-500 font-mono">Card: {mem.card_number}</p>
                        </td>
                        <td className="p-3">
                          <Badge variant="neutral">{mem.member_type}</Badge>
                        </td>
                        <td className="p-3 text-gray-600">{mem.max_books_allowed} Books</td>
                        <td className="p-3">
                          <span className="font-semibold text-indigo-600">{mem.active_loans_count ?? 0}</span>
                        </td>
                        <td className="p-3">
                          <Badge variant={mem.status === 'ACTIVE' ? 'success' : 'warning'}>{mem.status}</Badge>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {canUpdate && (
                              <Button variant="ghost" size="sm" onClick={() => handleOpenMemberModal(mem)}>
                                <Edit2 className="w-4 h-4 text-gray-600" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteMemberTarget(mem)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={memberPage} totalPages={memberTotalPages} onPageChange={setMemberPage} />
            </Card>
          )}
        </div>
      )}

      {/* 5. CIRCULATION WORKSTATION TAB */}
      {activeTab === 'circulation' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <div className="flex flex-1 gap-2 flex-wrap items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Search loan member, accession, barcode..."
                  value={loanSearch}
                  onChange={(e) => setLoanSearch(e.target.value)}
                  className="pl-9"
                />
              </div>

              <select
                value={loanStatusFilter}
                onChange={(e) => setLoanStatusFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Loans</option>
                <option value="ISSUED">Issued / Active</option>
                <option value="RETURNED">Returned</option>
                <option value="OVERDUE">Overdue</option>
              </select>

              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer bg-white px-3 py-2 border rounded-lg">
                <input
                  type="checkbox"
                  checked={loanOverdueFilter}
                  onChange={(e) => setLoanOverdueFilter(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                Overdue Only
              </label>
            </div>

            {canCirculate && (
              <Button onClick={handleOpenCheckoutModal} className="bg-indigo-600 text-white shrink-0">
                <Repeat className="w-4 h-4 mr-2" />
                Issue Book Copy
              </Button>
            )}
          </div>

          {loadingLoans ? (
            <LoadingState message="Loading circulation loans..." />
          ) : loanError ? (
            <ErrorState message={loanError} onRetry={fetchLoans} />
          ) : loans.length === 0 ? (
            <EmptyState
              title="No active loans"
              description="Issue book copies to registered members from this desk."
              action={
                canCirculate ? (
                  <Button onClick={handleOpenCheckoutModal} className="bg-indigo-600 text-white">
                    <Repeat className="w-4 h-4 mr-2" />
                    New Checkout
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Borrower</th>
                      <th className="p-3 font-semibold">Book & Copy</th>
                      <th className="p-3 font-semibold">Issue Date</th>
                      <th className="p-3 font-semibold">Due Date</th>
                      <th className="p-3 font-semibold">Status</th>
                      <th className="p-3 font-semibold text-right">Circulation Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {loans.map((loan) => (
                      <tr key={loan.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900">{loan.member_display_name}</p>
                          <p className="text-xs text-gray-500 font-mono">Card: {loan.member_card_number}</p>
                        </td>
                        <td className="p-3">
                          <p className="font-medium text-gray-900">{loan.book_title}</p>
                          <p className="text-xs text-gray-500 font-mono">Acc: {loan.accession_number}</p>
                        </td>
                        <td className="p-3 text-gray-600">{loan.issue_date}</td>
                        <td className="p-3">
                          <span
                            className={
                              loan.is_overdue || loan.status === 'OVERDUE'
                                ? 'text-red-600 font-semibold'
                                : 'text-gray-700'
                            }
                          >
                            {loan.due_date}
                          </span>
                          {loan.renewal_count > 0 && (
                            <span className="text-xs text-indigo-600 block">({loan.renewal_count} renewals)</span>
                          )}
                        </td>
                        <td className="p-3">
                          <Badge
                            variant={
                              loan.status === 'RETURNED'
                                ? 'neutral'
                                : loan.status === 'OVERDUE' || loan.is_overdue
                                ? 'error'
                                : 'info'
                            }
                          >
                            {loan.status}
                          </Badge>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {loan.status !== 'RETURNED' && canCirculate && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setRenewingLoan(loan)}
                                  className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                                >
                                  Renew
                                </Button>
                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={() => setReturningLoan(loan)}
                                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                                >
                                  Return
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={loanPage} totalPages={loanTotalPages} onPageChange={setLoanPage} />
            </Card>
          )}
        </div>
      )}

      {/* 6. RESERVATIONS TAB */}
      {activeTab === 'reservations' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <select
              value={reservationStatusFilter}
              onChange={(e) => setReservationStatusFilter(e.target.value)}
              className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">All Reservations</option>
              <option value="PENDING">Pending</option>
              <option value="FULFILLED">Fulfilled</option>
              <option value="CANCELLED">Cancelled</option>
            </select>

            {canCirculate && (
              <Button onClick={handleOpenReservationModal} className="bg-indigo-600 text-white shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                New Reservation
              </Button>
            )}
          </div>

          {loadingReservations ? (
            <LoadingState message="Loading reservations..." />
          ) : reservationError ? (
            <ErrorState message={reservationError} onRetry={fetchReservations} />
          ) : reservations.length === 0 ? (
            <EmptyState
              title="No reservations on file"
              description="Members can place holds on high-demand books."
              action={
                canCirculate ? (
                  <Button onClick={handleOpenReservationModal} className="bg-indigo-600 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Place Reservation
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Member</th>
                      <th className="p-3 font-semibold">Book Title</th>
                      <th className="p-3 font-semibold">Date Placed</th>
                      <th className="p-3 font-semibold">Expiry Date</th>
                      <th className="p-3 font-semibold">Status</th>
                      <th className="p-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {reservations.map((res) => (
                      <tr key={res.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900">{res.member_display_name}</p>
                          <p className="text-xs text-gray-500 font-mono">Card: {res.member_card_number}</p>
                        </td>
                        <td className="p-3 font-medium text-gray-900">{res.book_title}</td>
                        <td className="p-3 text-gray-600">{res.reservation_date}</td>
                        <td className="p-3 text-gray-600">{res.expiry_date || '—'}</td>
                        <td className="p-3">
                          <Badge variant={res.status === 'PENDING' ? 'warning' : 'neutral'}>{res.status}</Badge>
                        </td>
                        <td className="p-3 text-right">
                          {res.status === 'PENDING' && canCirculate && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setCancelReservationTarget(res)}
                              className="text-red-600 border-red-200 hover:bg-red-50"
                            >
                              Cancel Hold
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={reservationPage} totalPages={reservationTotalPages} onPageChange={setReservationPage} />
            </Card>
          )}
        </div>
      )}

      {/* 7. FINES LEDGER TAB */}
      {activeTab === 'fines' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3 justify-between items-stretch md:items-center">
            <div className="flex flex-1 gap-2 flex-wrap items-center">
              <select
                value={fineStatusFilter}
                onChange={(e) => setFineStatusFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="PAID">Paid</option>
                <option value="WAIVED">Waived</option>
              </select>

              <select
                value={fineReasonFilter}
                onChange={(e) => setFineReasonFilter(e.target.value)}
                className="h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">All Reasons</option>
                <option value="OVERDUE">Overdue</option>
                <option value="DAMAGE">Damage</option>
                <option value="LOSS">Loss</option>
              </select>
            </div>

            {canManage && (
              <Button onClick={handleOpenFineModal} className="bg-indigo-600 text-white shrink-0">
                <Plus className="w-4 h-4 mr-2" />
                Assess Fine
              </Button>
            )}
          </div>

          {loadingFines ? (
            <LoadingState message="Loading fines ledger..." />
          ) : fineError ? (
            <ErrorState message={fineError} onRetry={fetchFines} />
          ) : fines.length === 0 ? (
            <EmptyState title="No fines recorded" description="No pending or settled library fines." />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50/50 text-gray-600">
                      <th className="p-3 font-semibold">Borrower</th>
                      <th className="p-3 font-semibold">Reason</th>
                      <th className="p-3 font-semibold">Amount</th>
                      <th className="p-3 font-semibold">Status</th>
                      <th className="p-3 font-semibold">Waiver / Settlement Details</th>
                      <th className="p-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {fines.map((fine) => (
                      <tr key={fine.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-3">
                          <p className="font-semibold text-gray-900">{fine.member_display_name}</p>
                          <p className="text-xs text-gray-500 font-mono">Card: {fine.member_card_number}</p>
                        </td>
                        <td className="p-3">
                          <Badge variant="neutral">{fine.fine_reason}</Badge>
                        </td>
                        <td className="p-3 font-bold text-gray-900">₹{fine.amount}</td>
                        <td className="p-3">
                          <Badge
                            variant={
                              fine.status === 'PAID'
                                ? 'neutral'
                                : fine.status === 'WAIVED'
                                ? 'info'
                                : 'error'
                            }
                          >
                            {fine.status}
                          </Badge>
                        </td>
                        <td className="p-3 text-xs text-gray-600">
                          {fine.status === 'WAIVED' ? (
                            <span>Waived: {fine.waived_reason}</span>
                          ) : fine.status === 'PAID' ? (
                            <span>Settled</span>
                          ) : (
                            <span className="text-amber-600 font-medium">Pending collection</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          {fine.status === 'PENDING' && canManage && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setWaivingFine(fine)}
                              className="text-purple-600 border-purple-200 hover:bg-purple-50"
                            >
                              Waive Fine
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={finePage} totalPages={fineTotalPages} onPageChange={setFinePage} />
            </Card>
          )}
        </div>
      )}

      {/* Add / Edit Book Modal */}
      <Modal
        isOpen={showBookModal}
        onClose={() => setShowBookModal(false)}
        title={editingBook ? 'Edit Book Title' : 'Add New Book Title'}
      >
        <form onSubmit={handleSaveBook} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Book Title *</label>
            <Input
              required
              value={bookFormData.title}
              onChange={(e) => setBookFormData({ ...bookFormData, title: e.target.value })}
              placeholder="e.g. Clean Architecture"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Author *</label>
              <Input
                required
                value={bookFormData.author}
                onChange={(e) => setBookFormData({ ...bookFormData, author: e.target.value })}
                placeholder="e.g. Robert C. Martin"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">ISBN</label>
              <Input
                value={bookFormData.isbn || ''}
                onChange={(e) => setBookFormData({ ...bookFormData, isbn: e.target.value })}
                placeholder="e.g. 978-0134494166"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Category</label>
              <select
                value={bookFormData.category_id || ''}
                onChange={(e) => setBookFormData({ ...bookFormData, category_id: e.target.value })}
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">Select Category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Library Facility</label>
              <select
                value={bookFormData.library_id || ''}
                onChange={(e) => setBookFormData({ ...bookFormData, library_id: e.target.value })}
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">Select Library</option>
                {libraries.map((lib) => (
                  <option key={lib.id} value={lib.id}>
                    {lib.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Description / Summary</label>
            <textarea
              value={bookFormData.description || ''}
              onChange={(e) => setBookFormData({ ...bookFormData, description: e.target.value })}
              className="w-full p-2 text-sm border border-gray-300 rounded-lg"
              rows={3}
              placeholder="Summary or book contents..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowBookModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={bookSaving} className="bg-indigo-600 text-white">
              {bookSaving ? 'Saving...' : editingBook ? 'Save Changes' : 'Create Book'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add / Edit Physical Copy Modal */}
      <Modal
        isOpen={showCopyModal}
        onClose={() => setShowCopyModal(false)}
        title={editingCopy ? 'Edit Physical Copy' : 'Add Physical Inventory Copy'}
      >
        <form onSubmit={handleSaveCopy} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Book Title *</label>
            <select
              required
              disabled={!!editingCopy}
              value={copyFormData.book_id}
              onChange={(e) => setCopyFormData({ ...copyFormData, book_id: e.target.value })}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Book</option>
              {books.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title} (by {b.author})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Accession Number *</label>
              <Input
                required
                value={copyFormData.accession_number}
                onChange={(e) => setCopyFormData({ ...copyFormData, accession_number: e.target.value })}
                placeholder="ACC-1001"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Barcode</label>
              <Input
                value={copyFormData.barcode || ''}
                onChange={(e) => setCopyFormData({ ...copyFormData, barcode: e.target.value })}
                placeholder="BAR-1001"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Shelf Location</label>
              <Input
                value={copyFormData.shelf_location || ''}
                onChange={(e) => setCopyFormData({ ...copyFormData, shelf_location: e.target.value })}
                placeholder="e.g. Rack B3, Shelf 2"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Condition</label>
              <select
                value={copyFormData.condition || 'NEW'}
                onChange={(e) => setCopyFormData({ ...copyFormData, condition: e.target.value as BookCondition })}
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="NEW">New</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
                <option value="DAMAGED">Damaged</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowCopyModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={copySaving} className="bg-indigo-600 text-white">
              {copySaving ? 'Saving...' : editingCopy ? 'Save Changes' : 'Add Copy'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Register Member Modal */}
      <Modal
        isOpen={showMemberModal}
        onClose={() => setShowMemberModal(false)}
        title={editingMember ? 'Edit Library Membership' : 'Register Library Member'}
      >
        <form onSubmit={handleSaveMember} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Member Type *</label>
            <select
              disabled={!!editingMember}
              value={memberFormData.member_type}
              onChange={(e) =>
                setMemberFormData({
                  ...memberFormData,
                  member_type: e.target.value as LibraryMemberType,
                  student_id: '',
                  teacher_id: '',
                })
              }
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="STUDENT">Student</option>
              <option value="TEACHER">Teacher</option>
            </select>
          </div>

          {memberFormData.member_type === 'STUDENT' && !editingMember && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Student *</label>
              <select
                required
                value={memberFormData.student_id || ''}
                onChange={(e) => setMemberFormData({ ...memberFormData, student_id: e.target.value })}
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">Choose Student</option>
                {studentsList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name} ({s.admission_number})
                  </option>
                ))}
              </select>
            </div>
          )}

          {memberFormData.member_type === 'TEACHER' && !editingMember && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Teacher *</label>
              <select
                required
                value={memberFormData.teacher_id || ''}
                onChange={(e) => setMemberFormData({ ...memberFormData, teacher_id: e.target.value })}
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="">Choose Teacher</option>
                {teachersList.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.first_name} {t.last_name} ({t.employee_id})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Library Card Number *</label>
              <Input
                required
                value={memberFormData.card_number}
                onChange={(e) => setMemberFormData({ ...memberFormData, card_number: e.target.value })}
                placeholder="CARD-001"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Borrowing Limit (Books)</label>
              <Input
                type="number"
                min={1}
                max={20}
                value={memberFormData.max_books_allowed || 3}
                onChange={(e) =>
                  setMemberFormData({ ...memberFormData, max_books_allowed: parseInt(e.target.value) || 3 })
                }
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowMemberModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={memberSaving} className="bg-indigo-600 text-white">
              {memberSaving ? 'Saving...' : editingMember ? 'Save Changes' : 'Register Member'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Issue / Checkout Modal */}
      <Modal isOpen={showCheckoutModal} onClose={() => setShowCheckoutModal(false)} title="Issue Book Copy (Checkout)">
        <form onSubmit={handleCheckoutSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Borrowing Member *</label>
            <select
              required
              value={checkoutFormData.member_id}
              onChange={(e) => setCheckoutFormData({ ...checkoutFormData, member_id: e.target.value })}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Member</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name} ({m.card_number} • {m.member_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Available Physical Copy *</label>
            <select
              required
              value={checkoutFormData.book_copy_id}
              onChange={(e) => setCheckoutFormData({ ...checkoutFormData, book_copy_id: e.target.value })}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Available Copy</option>
              {copies
                .filter((c) => c.status === 'AVAILABLE')
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.book_title} — Acc: {c.accession_number} ({c.shelf_location || 'Rack'})
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Due Date *</label>
            <Input
              type="date"
              required
              value={checkoutFormData.due_date}
              onChange={(e) => setCheckoutFormData({ ...checkoutFormData, due_date: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowCheckoutModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={checkoutSaving} className="bg-indigo-600 text-white">
              {checkoutSaving ? 'Issuing...' : 'Complete Checkout'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Return Loan Modal */}
      <Modal isOpen={!!returningLoan} onClose={() => setReturningLoan(null)} title="Return Book Copy">
        {returningLoan && (
          <form onSubmit={handleReturnSubmit} className="space-y-4">
            <div className="p-3 bg-gray-50 rounded-lg space-y-1">
              <p className="text-sm font-semibold text-gray-900">{returningLoan.book_title}</p>
              <p className="text-xs text-gray-500">Accession: {returningLoan.accession_number}</p>
              <p className="text-xs text-gray-500">Borrower: {returningLoan.member_display_name}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Remarks (Optional)</label>
              <Input
                value={returnRemarks}
                onChange={(e) => setReturnRemarks(e.target.value)}
                placeholder="Condition on return, notes..."
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setReturningLoan(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={returnSaving} className="bg-emerald-600 text-white">
                {returnSaving ? 'Processing...' : 'Confirm Return'}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Renew Loan Modal */}
      <Modal isOpen={!!renewingLoan} onClose={() => setRenewingLoan(null)} title="Extend / Renew Loan">
        {renewingLoan && (
          <form onSubmit={handleRenewSubmit} className="space-y-4">
            <div className="p-3 bg-gray-50 rounded-lg space-y-1">
              <p className="text-sm font-semibold text-gray-900">{renewingLoan.book_title}</p>
              <p className="text-xs text-gray-500">Borrower: {renewingLoan.member_display_name}</p>
              <p className="text-xs text-gray-500">Current Due Date: {renewingLoan.due_date}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">New Due Date</label>
              <Input
                type="date"
                required
                value={renewDueDate}
                onChange={(e) => setRenewDueDate(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setRenewingLoan(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={renewSaving} className="bg-indigo-600 text-white">
                {renewSaving ? 'Renewing...' : 'Extend Due Date'}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Reservation Modal */}
      <Modal
        isOpen={showReservationModal}
        onClose={() => setShowReservationModal(false)}
        title="Place Book Hold / Reservation"
      >
        <form onSubmit={handleSaveReservation} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Book Title *</label>
            <select
              required
              value={reservationFormData.book_id}
              onChange={(e) => setReservationFormData({ ...reservationFormData, book_id: e.target.value })}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Book</option>
              {books.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title} (by {b.author})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Reserving Member *</label>
            <select
              required
              value={reservationFormData.member_id}
              onChange={(e) => setReservationFormData({ ...reservationFormData, member_id: e.target.value })}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Member</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name} ({m.card_number})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowReservationModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={reservationSaving} className="bg-indigo-600 text-white">
              {reservationSaving ? 'Saving...' : 'Place Hold'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Assess Fine Modal */}
      <Modal isOpen={showFineModal} onClose={() => setShowFineModal(false)} title="Assess Library Fine">
        <form onSubmit={handleSaveFine} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Select Loan Reference *</label>
            <select
              required
              value={fineFormData.loan_id}
              onChange={(e) => {
                const selected = loans.find((l) => l.id === e.target.value);
                setFineFormData({
                  ...fineFormData,
                  loan_id: e.target.value,
                  member_id: selected?.member_id || fineFormData.member_id,
                });
              }}
              className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Select Loan</option>
              {loans.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.book_title} — {l.member_display_name} ({l.status})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Fine Amount (₹) *</label>
              <Input
                required
                value={fineFormData.amount}
                onChange={(e) => setFineFormData({ ...fineFormData, amount: e.target.value })}
                placeholder="50.00"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Reason</label>
              <select
                value={fineFormData.fine_reason || 'OVERDUE'}
                onChange={(e) =>
                  setFineFormData({ ...fineFormData, fine_reason: e.target.value as LibraryFineReason })
                }
                className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white"
              >
                <option value="OVERDUE">Overdue Return</option>
                <option value="DAMAGE">Book Damage</option>
                <option value="LOSS">Book Lost</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowFineModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={fineSaving} className="bg-indigo-600 text-white">
              {fineSaving ? 'Assessing...' : 'Record Fine'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Waive Fine Modal */}
      <Modal isOpen={!!waivingFine} onClose={() => setWaivingFine(null)} title="Waive Library Fine">
        {waivingFine && (
          <form onSubmit={handleWaiveFineSubmit} className="space-y-4">
            <div className="p-3 bg-purple-50 text-purple-900 rounded-lg">
              <p className="text-sm font-semibold">
                Waiving fine of ₹{waivingFine.amount} for {waivingFine.member_display_name}
              </p>
              <p className="text-xs text-purple-700">Reason: {waivingFine.fine_reason}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                Waiver Justification / Approval Reason *
              </label>
              <Input
                required
                value={waiveReason}
                onChange={(e) => setWaiveReason(e.target.value)}
                placeholder="e.g. Principal special exemption, medical delay"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setWaivingFine(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={waiveSaving} className="bg-purple-600 text-white">
                {waiveSaving ? 'Waiving...' : 'Confirm Waiver'}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Delete Confirmation Dialogs */}
      <ConfirmDialog
        isOpen={!!deleteBookTarget}
        onClose={() => setDeleteBookTarget(null)}
        onConfirm={handleDeleteBook}
        title="Delete Book Title"
        message={`Are you sure you want to remove '${deleteBookTarget?.title}' from the catalog?`}
      />

      <ConfirmDialog
        isOpen={!!deleteCopyTarget}
        onClose={() => setDeleteCopyTarget(null)}
        onConfirm={handleDeleteCopy}
        title="Delete Physical Copy"
        message={`Are you sure you want to remove copy '${deleteCopyTarget?.accession_number}'?`}
      />

      <ConfirmDialog
        isOpen={!!deleteMemberTarget}
        onClose={() => setDeleteMemberTarget(null)}
        onConfirm={handleDeleteMember}
        title="Deactivate Member"
        message={`Are you sure you want to deactivate library card '${deleteMemberTarget?.card_number}'?`}
      />

      <ConfirmDialog
        isOpen={!!cancelReservationTarget}
        onClose={() => setCancelReservationTarget(null)}
        onConfirm={handleCancelReservation}
        title="Cancel Reservation"
        message={`Cancel reservation hold for '${cancelReservationTarget?.book_title}'?`}
      />
    </div>
  );
};
