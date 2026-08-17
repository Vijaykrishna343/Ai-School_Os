import { apiClient } from './client';
import {
  PaginatedResponse,
  FeeStructure,
  FeeStructureCreate,
  FeeStructureUpdate,
  FeeStructureStatus,
  StudentFeeAssignment,
  StudentFeeAssignmentCreate,
  StudentFeeAssignmentStatus,
  StudentFeeItemCreate,
  FeeDiscountCreate,
  FeePayment,
  FeePaymentCreate,
  FeeReceipt,
  PaymentMode,
} from '@/types/models';

export interface FeeStructureFilters {
  academic_year_id?: string;
  school_class_id?: string;
  status?: FeeStructureStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface StudentFeeAssignmentFilters {
  academic_year_id?: string;
  student_id?: string;
  fee_structure_id?: string;
  status?: StudentFeeAssignmentStatus;
  page?: number;
  page_size?: number;
}

export interface FeePaymentFilters {
  assignment_id?: string;
  payment_mode?: PaymentMode;
  page?: number;
  page_size?: number;
}

export const feesApi = {
  // Fee Structures
  getFeeStructures: async (params?: FeeStructureFilters): Promise<PaginatedResponse<FeeStructure>> => {
    return await apiClient.get('/fees/structures', { params });
  },

  getFeeStructure: async (id: string): Promise<FeeStructure> => {
    return await apiClient.get(`/fees/structures/${id}`);
  },

  createFeeStructure: async (data: FeeStructureCreate): Promise<FeeStructure> => {
    return await apiClient.post('/fees/structures', data);
  },

  updateFeeStructure: async (id: string, data: FeeStructureUpdate): Promise<FeeStructure> => {
    return await apiClient.put(`/fees/structures/${id}`, data);
  },

  deleteFeeStructure: async (id: string): Promise<void> => {
    await apiClient.delete(`/fees/structures/${id}`);
  },

  // Student Fee Assignments
  assignFeeStructure: async (data: StudentFeeAssignmentCreate): Promise<StudentFeeAssignment> => {
    return await apiClient.post('/fees/assignments', data);
  },

  getStudentFeeAssignments: async (
    params?: StudentFeeAssignmentFilters
  ): Promise<PaginatedResponse<StudentFeeAssignment>> => {
    return await apiClient.get('/fees/assignments', { params });
  },

  getStudentFeeAssignment: async (id: string): Promise<StudentFeeAssignment> => {
    return await apiClient.get(`/fees/assignments/${id}`);
  },

  deleteStudentFeeAssignment: async (id: string): Promise<void> => {
    await apiClient.delete(`/fees/assignments/${id}`);
  },

  addStudentFeeItem: async (
    assignmentId: string,
    data: StudentFeeItemCreate
  ): Promise<StudentFeeAssignment> => {
    return await apiClient.post(`/fees/assignments/${assignmentId}/items`, data);
  },

  addFeeDiscount: async (
    assignmentId: string,
    data: FeeDiscountCreate
  ): Promise<StudentFeeAssignment> => {
    return await apiClient.post(`/fees/assignments/${assignmentId}/discounts`, data);
  },

  removeFeeDiscount: async (
    assignmentId: string,
    discountId: string
  ): Promise<StudentFeeAssignment> => {
    return await apiClient.delete(`/fees/assignments/${assignmentId}/discounts/${discountId}`);
  },

  cancelStudentFeeAssignment: async (assignmentId: string): Promise<StudentFeeAssignment> => {
    return await apiClient.post(`/fees/assignments/${assignmentId}/cancel`);
  },

  // Fee Payments & Receipts
  recordFeePayment: async (data: FeePaymentCreate): Promise<FeePayment> => {
    return await apiClient.post('/fees/payments', data);
  },

  getFeePayments: async (params?: FeePaymentFilters): Promise<PaginatedResponse<FeePayment>> => {
    return await apiClient.get('/fees/payments', { params });
  },

  getFeePayment: async (id: string): Promise<FeePayment> => {
    return await apiClient.get(`/fees/payments/${id}`);
  },

  getPaymentReceipt: async (paymentId: string): Promise<FeeReceipt> => {
    return await apiClient.get(`/fees/payments/${paymentId}/receipt`);
  },
};
