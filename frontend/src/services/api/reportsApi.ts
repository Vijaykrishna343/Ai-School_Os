import { apiClient } from './client';
import axios from 'axios';

export interface ReportFilterParams {
  academic_year_id?: string;
  academic_term_id?: string;
  class_id?: string;
  section_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface ExecutiveKpiCard {
  id: string;
  title: string;
  value: string;
  numeric_value: number;
  unit?: string;
  subtext?: string;
  trend_direction?: 'up' | 'down' | 'neutral';
  trend_label?: string;
  status?: 'success' | 'warning' | 'info' | 'danger';
}

export interface ExecutiveSummaryResponse {
  school_id: string;
  school_name: string;
  generated_at: string;
  active_students: number;
  active_teachers: number;
  active_classes: number;
  overall_attendance_pct: number;
  total_fees_assigned: number;
  total_fees_collected: number;
  total_fees_outstanding: number;
  fee_collection_rate_pct: number;
  admissions_inquiries: number;
  admissions_applicants: number;
  admissions_enrolled: number;
  admissions_conversion_pct: number;
  published_report_cards_pct: number;
  kpi_cards: ExecutiveKpiCard[];
  operations_highlights: Record<string, any>;
}

export interface ClassEnrollmentItem {
  class_id: string;
  class_name: string;
  section_id?: string;
  section_name?: string;
  student_count: number;
  male_count: number;
  female_count: number;
  other_count: number;
  capacity?: number;
  occupancy_pct?: number;
}

export interface EnrollmentTrendItem {
  period: string;
  active_count: number;
  new_admissions: number;
}

export interface StudentEnrollmentReportResponse {
  total_active_students: number;
  total_inactive_students: number;
  total_students: number;
  gender_distribution: Record<string, number>;
  by_class_section: ClassEnrollmentItem[];
  enrollment_trends: EnrollmentTrendItem[];
  total_items: number;
  page: number;
  page_size: number;
}

export interface ClassAttendanceItem {
  class_id: string;
  class_name: string;
  section_id?: string;
  section_name?: string;
  total_students: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  attendance_pct: number;
}

export interface ChronicAbsenteeItem {
  student_id: string;
  admission_number: string;
  student_name: string;
  class_name: string;
  section_name: string;
  total_days: number;
  present_days: number;
  absent_days: number;
  attendance_pct: number;
}

export interface AttendanceReportResponse {
  date_evaluated: string;
  overall_attendance_pct: number;
  total_expected_students: number;
  total_present: number;
  total_absent: number;
  total_late: number;
  total_excused: number;
  by_class_section: ClassAttendanceItem[];
  chronic_absentee_count: number;
  chronic_absentees: ChronicAbsenteeItem[];
  total_items: number;
  page: number;
  page_size: number;
}

export interface PaymentMethodItem {
  method: string;
  total_amount: number;
  transaction_count: number;
  percentage_of_total: number;
}

export interface AgingBucketSummary {
  bucket_0_30_days: number;
  bucket_31_60_days: number;
  bucket_61_90_days: number;
  bucket_90_plus_days: number;
}

export interface RecentCollectionItem {
  payment_id: string;
  payment_reference: string;
  student_name: string;
  admission_number: string;
  amount: number;
  payment_method: string;
  payment_date: string;
  fee_type: string;
}

export interface FinanceReportResponse {
  total_fees_assigned: number;
  total_fees_collected: number;
  total_fees_outstanding: number;
  collection_rate_pct: number;
  hostel_fees_collected: number;
  transport_fees_collected: number;
  academic_fees_collected: number;
  payment_methods_breakdown: PaymentMethodItem[];
  aging_buckets: AgingBucketSummary;
  recent_collections: RecentCollectionItem[];
  total_collections_count: number;
  page: number;
  page_size: number;
}

export interface AdmissionsStageItem {
  stage: string;
  stage_label: string;
  count: number;
  percentage: number;
}

export interface AdmissionsReportResponse {
  total_inquiries: number;
  total_applications: number;
  total_under_review: number;
  total_admitted: number;
  total_enrolled: number;
  total_rejected: number;
  inquiry_to_app_conversion_pct: number;
  app_to_enroll_conversion_pct: number;
  stages_breakdown: AdmissionsStageItem[];
  pending_followups_count: number;
}

export interface ClassPerformanceSummaryItem {
  class_id: string;
  class_name: string;
  section_id?: string;
  section_name?: string;
  total_report_cards: number;
  published_count: number;
  draft_count: number;
  average_score_pct: number;
  average_gpa?: number;
  pass_rate_pct: number;
}

export interface AcademicReportResponse {
  total_report_cards: number;
  total_published: number;
  total_draft: number;
  overall_publication_pct: number;
  overall_average_score_pct: number;
  overall_pass_rate_pct: number;
  by_class_section: ClassPerformanceSummaryItem[];
  total_items: number;
  page: number;
  page_size: number;
}

export interface TransportOperationsSummary {
  total_vehicles: number;
  total_routes: number;
  total_assigned_students: number;
  active_vehicles_count: number;
}

export interface LibraryOperationsSummary {
  total_books: number;
  active_loans_count: number;
  overdue_loans_count: number;
  available_copies_count: number;
}

export interface InventoryOperationsSummary {
  total_items: number;
  low_stock_items_count: number;
  out_of_stock_items_count: number;
  total_inventory_valuation: number;
}

export interface HostelOperationsSummary {
  total_rooms: number;
  total_bed_capacity: number;
  occupied_beds_count: number;
  available_beds_count: number;
  occupancy_rate_pct: number;
}

export interface NotificationOperationsSummary {
  total_notifications_sent: number;
  delivered_count: number;
  pending_count: number;
  failed_count: number;
  delivery_success_rate_pct: number;
}

export interface OperationsReportResponse {
  transport: TransportOperationsSummary;
  library: LibraryOperationsSummary;
  inventory: InventoryOperationsSummary;
  hostel: HostelOperationsSummary;
  notifications: NotificationOperationsSummary;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const reportsApi = {
  getExecutiveSummary: async (filters?: ReportFilterParams): Promise<ExecutiveSummaryResponse> => {
    return await apiClient.get('/reports/executive-summary', { params: filters });
  },

  getStudentReport: async (filters?: ReportFilterParams): Promise<StudentEnrollmentReportResponse> => {
    return await apiClient.get('/reports/students', { params: filters });
  },

  getAttendanceReport: async (filters?: ReportFilterParams): Promise<AttendanceReportResponse> => {
    return await apiClient.get('/reports/attendance', { params: filters });
  },

  getFinanceReport: async (filters?: ReportFilterParams): Promise<FinanceReportResponse> => {
    return await apiClient.get('/reports/finance', { params: filters });
  },

  getAdmissionsReport: async (): Promise<AdmissionsReportResponse> => {
    return await apiClient.get('/reports/admissions');
  },

  getAcademicReport: async (filters?: ReportFilterParams): Promise<AcademicReportResponse> => {
    return await apiClient.get('/reports/academic', { params: filters });
  },

  getOperationsReport: async (): Promise<OperationsReportResponse> => {
    return await apiClient.get('/reports/operations');
  },

  exportCsv: async (category: string, filters?: ReportFilterParams): Promise<Blob> => {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(`${BASE_URL}/reports/export/csv`, {
      params: { category, ...filters },
      responseType: 'blob',
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    });
    return response.data;
  },
};
