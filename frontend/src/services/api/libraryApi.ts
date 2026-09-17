import { apiClient } from './client';
import {
  Book,
  BookCategory,
  BookCategoryCreate,
  BookCategoryUpdate,
  BookCopy,
  BookCopyCreate,
  BookCopyUpdate,
  BookCreate,
  BookLoan,
  BookLoanCheckout,
  BookLoanRenew,
  BookLoanReturn,
  BookReservation,
  BookReservationCreate,
  BookUpdate,
  Library,
  LibraryCreate,
  LibraryFine,
  LibraryFineCreate,
  LibraryFineWaive,
  LibraryMember,
  LibraryMemberCreate,
  LibraryMemberUpdate,
  LibrarySummaryResponse,
  LibraryUpdate,
  PaginatedResponse,
} from '@/types/models';

export interface LibraryFilterParams {
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface CategoryFilterParams {
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface BookFilterParams {
  search?: string;
  category_id?: string;
  library_id?: string;
  language?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface BookCopyFilterParams {
  book_id?: string;
  library_id?: string;
  status?: string;
  condition?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface MemberFilterParams {
  member_type?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface LoanFilterParams {
  member_id?: string;
  book_copy_id?: string;
  status?: string;
  overdue_only?: boolean;
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ReservationFilterParams {
  member_id?: string;
  book_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface FineFilterParams {
  member_id?: string;
  loan_id?: string;
  status?: string;
  fine_reason?: string;
  page?: number;
  page_size?: number;
}

export const libraryApi = {
  // Operational Summary
  getSummary: async (): Promise<LibrarySummaryResponse> => {
    return await apiClient.get('/library/summary');
  },

  // Libraries
  getLibraries: async (params?: LibraryFilterParams): Promise<PaginatedResponse<Library>> => {
    return await apiClient.get('/library/libraries', { params });
  },

  getLibrary: async (id: string): Promise<Library> => {
    return await apiClient.get(`/library/libraries/${id}`);
  },

  createLibrary: async (data: LibraryCreate): Promise<Library> => {
    return await apiClient.post('/library/libraries', data);
  },

  updateLibrary: async (id: string, data: LibraryUpdate): Promise<Library> => {
    return await apiClient.put(`/library/libraries/${id}`, data);
  },

  deleteLibrary: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/library/libraries/${id}`);
  },

  // Categories
  getCategories: async (params?: CategoryFilterParams): Promise<PaginatedResponse<BookCategory>> => {
    return await apiClient.get('/library/categories', { params });
  },

  getCategory: async (id: string): Promise<BookCategory> => {
    return await apiClient.get(`/library/categories/${id}`);
  },

  createCategory: async (data: BookCategoryCreate): Promise<BookCategory> => {
    return await apiClient.post('/library/categories', data);
  },

  updateCategory: async (id: string, data: BookCategoryUpdate): Promise<BookCategory> => {
    return await apiClient.put(`/library/categories/${id}`, data);
  },

  deleteCategory: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/library/categories/${id}`);
  },

  // Books
  getBooks: async (params?: BookFilterParams): Promise<PaginatedResponse<Book>> => {
    return await apiClient.get('/library/books', { params });
  },

  getBook: async (id: string): Promise<Book> => {
    return await apiClient.get(`/library/books/${id}`);
  },

  createBook: async (data: BookCreate): Promise<Book> => {
    return await apiClient.post('/library/books', data);
  },

  updateBook: async (id: string, data: BookUpdate): Promise<Book> => {
    return await apiClient.put(`/library/books/${id}`, data);
  },

  deleteBook: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/library/books/${id}`);
  },

  // Book Copies
  getCopies: async (params?: BookCopyFilterParams): Promise<PaginatedResponse<BookCopy>> => {
    return await apiClient.get('/library/copies', { params });
  },

  getCopy: async (id: string): Promise<BookCopy> => {
    return await apiClient.get(`/library/copies/${id}`);
  },

  createCopy: async (data: BookCopyCreate): Promise<BookCopy> => {
    return await apiClient.post('/library/copies', data);
  },

  updateCopy: async (id: string, data: BookCopyUpdate): Promise<BookCopy> => {
    return await apiClient.put(`/library/copies/${id}`, data);
  },

  deleteCopy: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/library/copies/${id}`);
  },

  // Members
  getMembers: async (params?: MemberFilterParams): Promise<PaginatedResponse<LibraryMember>> => {
    return await apiClient.get('/library/members', { params });
  },

  getMember: async (id: string): Promise<LibraryMember> => {
    return await apiClient.get(`/library/members/${id}`);
  },

  createMember: async (data: LibraryMemberCreate): Promise<LibraryMember> => {
    return await apiClient.post('/library/members', data);
  },

  updateMember: async (id: string, data: LibraryMemberUpdate): Promise<LibraryMember> => {
    return await apiClient.put(`/library/members/${id}`, data);
  },

  deleteMember: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/library/members/${id}`);
  },

  // Loans / Circulation
  getLoans: async (params?: LoanFilterParams): Promise<PaginatedResponse<BookLoan>> => {
    return await apiClient.get('/library/loans', { params });
  },

  getLoan: async (id: string): Promise<BookLoan> => {
    return await apiClient.get(`/library/loans/${id}`);
  },

  checkoutLoan: async (data: BookLoanCheckout): Promise<BookLoan> => {
    return await apiClient.post('/library/loans/checkout', data);
  },

  returnLoan: async (id: string, data?: BookLoanReturn): Promise<BookLoan> => {
    return await apiClient.post(`/library/loans/${id}/return`, data || {});
  },

  renewLoan: async (id: string, data?: BookLoanRenew): Promise<BookLoan> => {
    return await apiClient.post(`/library/loans/${id}/renew`, data || {});
  },

  // Reservations
  getReservations: async (params?: ReservationFilterParams): Promise<PaginatedResponse<BookReservation>> => {
    return await apiClient.get('/library/reservations', { params });
  },

  createReservation: async (data: BookReservationCreate): Promise<BookReservation> => {
    return await apiClient.post('/library/reservations', data);
  },

  cancelReservation: async (id: string): Promise<BookReservation> => {
    return await apiClient.post(`/library/reservations/${id}/cancel`);
  },

  // Fines
  getFines: async (params?: FineFilterParams): Promise<PaginatedResponse<LibraryFine>> => {
    return await apiClient.get('/library/fines', { params });
  },

  getFine: async (id: string): Promise<LibraryFine> => {
    return await apiClient.get(`/library/fines/${id}`);
  },

  createFine: async (data: LibraryFineCreate): Promise<LibraryFine> => {
    return await apiClient.post('/library/fines', data);
  },

  waiveFine: async (id: string, data: LibraryFineWaive): Promise<LibraryFine> => {
    return await apiClient.post(`/library/fines/${id}/waive`, data);
  },
};
