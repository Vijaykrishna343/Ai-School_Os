export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CurrentAcademicYearSummary {
  id: string;
  name: string;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
}

export interface CurrentAcademicTermSummary {
  id: string;
  name: string;
  term_structure?: string | null;
}

export interface DashboardSummary {
  active_students: number;
  active_teachers: number;
  active_parents: number;
  active_classes: number;
  active_sections: number;
  current_academic_year?: CurrentAcademicYearSummary | null;
  current_academic_term?: CurrentAcademicTermSummary | null;
}

export interface AcademicYear {
  id: string;
  school_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: 'UPCOMING' | 'ACTIVE' | 'ARCHIVED';
  is_current?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AcademicYearCreate {
  name: string;
  start_date: string;
  end_date: string;
  status?: 'UPCOMING' | 'ACTIVE' | 'ARCHIVED';
}

export interface AcademicYearUpdate {
  name?: string;
  start_date?: string;
  end_date?: string;
  status?: 'UPCOMING' | 'ACTIVE' | 'ARCHIVED';
}

export interface AcademicTerm {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  display_order: number;
  is_active: boolean;
  academic_year?: AcademicYear;
}

export interface AcademicTermCreate {
  academic_year_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  display_order?: number;
  is_active?: boolean;
}

export interface AcademicTermUpdate {
  name?: string;
  code?: string;
  start_date?: string;
  end_date?: string;
  display_order?: number;
  is_active?: boolean;
}

export interface SchoolClass {
  id: string;
  school_id: string;
  name: string;
  display_order: number;
  status: 'ACTIVE' | 'INACTIVE';
  sections_count?: number;
}

export interface SchoolClassCreate {
  school_id: string;
  name: string;
  display_order: number;
}

export interface SchoolClassUpdate {
  name?: string;
  display_order?: number;
  status?: 'ACTIVE' | 'INACTIVE';
}

export interface Section {
  id: string;
  school_class_id: string;
  name: string;
  room_number?: string | null;
  capacity: number;
  status: 'ACTIVE' | 'INACTIVE';
  school_class?: SchoolClass;
}

export interface SectionCreate {
  school_class_id: string;
  name: string;
  room_number?: string | null;
  capacity?: number;
}

export interface SectionUpdate {
  name?: string;
  room_number?: string | null;
  capacity?: number;
  status?: 'ACTIVE' | 'INACTIVE';
}

export interface Student {
  id: string;
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  parent_id: string;
  admission_number: string;
  roll_number: string;
  first_name: string;
  middle_name?: string | null;
  last_name?: string | null;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  blood_group?: string | null;
  date_of_birth: string;
  admission_date: string;
  phone?: string | null;
  email?: string | null;
  emergency_contact?: string | null;
  address_line1: string;
  address_line2?: string | null;
  city: string;
  district: string;
  state: string;
  postal_code: string;
  status: string;
  school_class?: SchoolClass | null;
  section?: Section | null;
  parent?: Parent | null;
  academic_year?: AcademicYear | null;
}

export interface StudentCreate {
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  parent_id: string;
  admission_number: string;
  roll_number: string;
  first_name: string;
  middle_name?: string;
  last_name?: string;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  date_of_birth: string;
  admission_date: string;
  phone?: string;
  email?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  district: string;
  state: string;
  postal_code: string;
}

export interface StudentUpdate {
  school_class_id?: string;
  section_id?: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  gender?: 'MALE' | 'FEMALE' | 'OTHER';
  phone?: string;
  email?: string;
  address_line1?: string;
  city?: string;
  district?: string;
  state?: string;
  postal_code?: string;
  status?: string;
}

export interface StudentEnrollmentHistory {
  id: string;
  student_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  roll_number: string;
  enrollment_status: string;
  promotion_decision?: string | null;
  academic_year?: AcademicYear | null;
  school_class?: SchoolClass | null;
  section?: Section | null;
  created_at?: string;
}

export interface Parent {
  id: string;
  school_id: string;
  father_name: string;
  mother_name?: string | null;
  guardian_name?: string | null;
  relationship: 'FATHER' | 'MOTHER' | 'GUARDIAN';
  primary_phone: string;
  secondary_phone?: string | null;
  email?: string | null;
  occupation?: string | null;
  annual_income?: number | null;
  address_line1: string;
  city: string;
  district: string;
  state: string;
  postal_code: string;
  is_active: boolean;
  students?: Student[];
}

export interface ParentCreate {
  school_id: string;
  father_name: string;
  mother_name?: string;
  guardian_name?: string;
  relationship?: 'FATHER' | 'MOTHER' | 'GUARDIAN';
  primary_phone: string;
  secondary_phone?: string;
  email?: string;
  occupation?: string;
  address_line1: string;
  city: string;
  district: string;
  state: string;
  postal_code: string;
}

export interface ParentUpdate {
  father_name?: string;
  mother_name?: string;
  guardian_name?: string;
  primary_phone?: string;
  secondary_phone?: string;
  email?: string;
  occupation?: string;
  address_line1?: string;
  city?: string;
  district?: string;
  state?: string;
  postal_code?: string;
  is_active?: boolean;
}

export interface Teacher {
  id: string;
  school_id: string;
  employee_id: string;
  first_name: string;
  middle_name?: string | null;
  last_name?: string | null;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  date_of_birth: string;
  joining_date: string;
  qualification: string;
  specialization?: string | null;
  experience_years?: number;
  phone: string;
  email: string;
  emergency_contact?: string | null;
  address_line1: string;
  city: string;
  district: string;
  state: string;
  postal_code: string;
  status: 'ACTIVE' | 'ON_LEAVE' | 'RESIGNED' | 'TERMINATED' | 'RETIRED';
  full_name?: string;
}

export interface TeacherCreate {
  school_id: string;
  employee_id: string;
  first_name: string;
  middle_name?: string;
  last_name?: string;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  date_of_birth: string;
  joining_date: string;
  qualification: string;
  specialization?: string;
  experience_years?: number;
  phone: string;
  email: string;
  emergency_contact?: string;
  address_line1: string;
  city: string;
  district: string;
  state: string;
  postal_code: string;
  status?: 'ACTIVE' | 'ON_LEAVE' | 'RESIGNED' | 'TERMINATED' | 'RETIRED';
}

export interface TeacherUpdate {
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  gender?: 'MALE' | 'FEMALE' | 'OTHER';
  qualification?: string;
  specialization?: string;
  experience_years?: number;
  phone?: string;
  email?: string;
  emergency_contact?: string;
  address_line1?: string;
  city?: string;
  district?: string;
  state?: string;
  postal_code?: string;
  status?: 'ACTIVE' | 'ON_LEAVE' | 'RESIGNED' | 'TERMINATED' | 'RETIRED';
}

export interface ClassProgressionRule {
  id: string;
  school_id: string;
  source_class_id: string;
  target_class_id: string | null;
  is_terminal: boolean;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
  source_class?: SchoolClass | null;
  target_class?: SchoolClass | null;
}

export interface ClassProgressionRuleCreate {
  source_class_id: string;
  target_class_id: string | null;
  is_terminal: boolean;
  description?: string;
}

export interface ClassProgressionRuleUpdate {
  target_class_id?: string | null;
  is_terminal?: boolean;
  description?: string;
}

export interface StudentProgressionPreviewItem {
  student_id: string;
  admission_number: string;
  student_name: string;
  current_academic_year_id: string;
  current_class_id: string;
  current_class_name: string;
  current_section_id: string;
  current_section_name: string;
  current_roll_number?: string | null;
  decision: 'PENDING' | 'PROMOTED' | 'RETAINED' | 'GRADUATED' | 'TRANSFERRED' | 'WITHDRAWN';
  target_class_id?: string | null;
  target_class_name?: string | null;
  target_section_id?: string | null;
  target_section_name?: string | null;
  proposed_roll_number?: string | null;
  allocation_status: 'EXCLUDED' | 'BLOCKED' | 'READY' | 'PROPOSED' | string;
  reason: string;
  warnings: string[];
}

export interface ProgressionPreviewSummary {
  source_academic_year_id: string;
  target_academic_year_id: string;
  total_students_evaluated: number;
  promoted_count: number;
  graduated_count: number;
  retained_count: number;
  blocked_count: number;
  excluded_count: number;
  warning_count: number;
}

export interface ProgressionPreviewResponse {
  execution_plan_hash: string;
  summary: ProgressionPreviewSummary;
  items: StudentProgressionPreviewItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProgressionExecutionSummaryResponse {
  total_students_evaluated: number;
  promoted_count: number;
  graduated_count: number;
  retained_count: number;
  blocked_count: number;
  excluded_count: number;
}

export interface ProgressionExecutionData {
  execution_id: string;
  status: string;
  source_academic_year_id: string;
  target_academic_year_id: string;
  summary: ProgressionExecutionSummaryResponse;
  started_at: string;
  completed_at?: string | null;
  error_summary?: string | null;
}

export interface Subject {
  id: string;
  school_id: string;
  subject_code: string;
  subject_name: string;
  description?: string | null;
  is_optional: boolean;
  status: 'ACTIVE' | 'INACTIVE';
  created_at?: string;
  updated_at?: string;
}

export interface SubjectCreate {
  school_id?: string;
  subject_code: string;
  subject_name: string;
  description?: string;
  is_optional?: boolean;
  status?: 'ACTIVE' | 'INACTIVE';
}

export interface SubjectUpdate {
  subject_code?: string;
  subject_name?: string;
  description?: string | null;
  is_optional?: boolean;
  status?: 'ACTIVE' | 'INACTIVE';
}

export type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'LATE' | 'HALF_DAY' | 'EXCUSED';

export interface Attendance {
  id: string;
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  student_id: string;
  attendance_date: string;
  status: AttendanceStatus;
  remarks: string | null;
  recorded_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceCreate {
  student_id: string;
  attendance_date: string;
  status: AttendanceStatus;
  remarks?: string | null;
}

export interface AttendanceBulkItem {
  student_id: string;
  status: AttendanceStatus;
  remarks?: string | null;
}

export interface AttendanceBulkCreate {
  section_id: string;
  attendance_date: string;
  records: AttendanceBulkItem[];
}

export interface AttendanceUpdate {
  status?: AttendanceStatus | null;
  remarks?: string | null;
}

export type AssessmentType =
  | 'FORMATIVE_ASSESSMENT'
  | 'SUMMATIVE_ASSESSMENT'
  | 'UNIT_TEST'
  | 'PERIODIC_TEST'
  | 'QUARTERLY'
  | 'HALF_YEARLY'
  | 'TERM'
  | 'PRE_FINAL'
  | 'QUARTER_FINAL'
  | 'SEMI_FINAL'
  | 'FINAL'
  | 'OTHER';

export type AttemptType = 'REGULAR' | 'RETEST' | 'MAKEUP';

export type ExamStatus = 'DRAFT' | 'SCHEDULED' | 'ONGOING' | 'COMPLETED' | 'CANCELLED';

export type ReportCardStatus = 'DRAFT' | 'FINALIZED' | 'PUBLISHED';

export type CalculationMode = 'SIMPLE_TOTAL' | 'WEIGHTED_ASSESSMENT_TYPE';

export type RetestPolicy = 'REPLACE_ORIGINAL' | 'BEST_ATTEMPT' | 'LATEST_ATTEMPT';

export type RoundingMode = 'ROUND_HALF_UP' | 'ROUND_FLOOR' | 'ROUND_CEIL';

export interface Exam {
  id: string;
  school_id: string;
  academic_year_id: string;
  academic_term_id: string | null;
  name: string;
  assessment_type: AssessmentType;
  attempt_type: AttemptType;
  start_date: string;
  end_date: string;
  status: ExamStatus;
  created_at: string;
  updated_at: string;
}

export interface ExamCreate {
  school_id?: string;
  academic_year_id: string;
  academic_term_id?: string | null;
  name: string;
  assessment_type?: AssessmentType;
  attempt_type?: AttemptType;
  start_date: string;
  end_date: string;
  status?: ExamStatus;
}

export interface ExamUpdate {
  academic_term_id?: string | null;
  name?: string;
  assessment_type?: AssessmentType;
  attempt_type?: AttemptType;
  start_date?: string;
  end_date?: string;
  status?: ExamStatus;
}

export interface ExamSchedule {
  id: string;
  exam_id: string;
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  subject_id: string;
  exam_date: string;
  start_time: string;
  end_time: string;
  maximum_marks: number;
  passing_marks: number;
  created_at: string;
  updated_at: string;
  exam?: Exam;
  subject?: any;
  school_class?: { id: string; name: string } | null;
  section?: { id: string; name: string } | null;
}

export interface ExamScheduleCreate {
  exam_id: string;
  school_id?: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  subject_id: string;
  exam_date: string;
  start_time: string;
  end_time: string;
  maximum_marks: number;
  passing_marks: number;
}

export interface ExamScheduleUpdate {
  exam_date?: string;
  start_time?: string;
  end_time?: string;
  maximum_marks?: number;
  passing_marks?: number;
}

export interface StudentExamResult {
  id: string;
  exam_schedule_id: string;
  student_id: string;
  marks_obtained: number;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentExamResultCreate {
  exam_schedule_id: string;
  student_id: string;
  marks_obtained: number;
  remarks?: string | null;
}

export interface StudentExamResultUpdate {
  marks_obtained?: number;
  remarks?: string | null;
}

export interface GradeScaleEntry {
  id: string;
  grade_scale_id: string;
  grade_code: string;
  min_percentage: number;
  max_percentage: number;
  grade_point: number;
  description: string | null;
}

export interface GradeScale {
  id: string;
  school_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  entries?: GradeScaleEntry[];
}

export interface GradeScaleCreate {
  name: string;
  description?: string | null;
  is_default?: boolean;
  entries?: Omit<GradeScaleEntry, 'id' | 'grade_scale_id'>[];
}

export interface GradeScaleUpdate {
  name?: string;
  description?: string | null;
  is_default?: boolean;
  entries?: (Omit<GradeScaleEntry, 'id' | 'grade_scale_id'> | GradeScaleEntry)[];
}

export interface AssessmentTypeWeightage {
  id: string;
  evaluation_config_id: string;
  assessment_type: AssessmentType;
  weightage_percentage: number;
}

export interface EvaluationConfig {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  calculation_mode: CalculationMode;
  retest_policy: RetestPolicy;
  rounding_mode: RoundingMode;
  weightages?: AssessmentTypeWeightage[];
}

export interface EvaluationConfigCreate {
  school_id?: string;
  academic_year_id: string;
  name: string;
  calculation_mode: CalculationMode;
  retest_policy: RetestPolicy;
  rounding_mode: RoundingMode;
  weightages?: Omit<AssessmentTypeWeightage, 'id' | 'evaluation_config_id'>[];
}

export interface ReportCardItemSnapshot {
  id: string;
  report_card_id: string;
  subject_id: string;
  subject_name: string;
  subject_code: string;
  max_marks: number;
  obtained_marks: number;
  percentage: number;
  grade_code: string;
  grade_point: number;
  is_pass: boolean;
  remarks: string | null;
}

export interface ReportCard {
  id: string;
  school_id: string;
  academic_year_id: string;
  academic_term_id: string | null;
  student_id: string;
  school_class_id: string;
  section_id: string;
  grade_scale_id: string;
  evaluation_config_id: string;
  status: ReportCardStatus;
  total_max_marks: number;
  total_obtained_marks: number;
  percentage: number;
  overall_grade: string;
  overall_grade_point: number;
  gpa: number | null;
  is_passed: boolean;
  total_working_days: number;
  present_days: number;
  attendance_percentage: number;
  teacher_remarks: string | null;
  principal_remarks: string | null;
  finalized_at: string | null;
  published_at: string | null;
  items?: ReportCardItemSnapshot[];
  student?: Student | null;
  school_class?: { id: string; name: string } | null;
  section?: { id: string; name: string } | null;
  created_at: string;
  updated_at: string;
}

export interface ReportCardGenerateRequest {
  school_id: string;
  academic_year_id: string;
  academic_term_id?: string | null;
  student_id?: string | null;
  section_id?: string | null;
  school_class_id?: string | null;
  grade_scale_id?: string | null;
  evaluation_config_id?: string | null;
}

export interface ReportCardRemarksUpdate {
  teacher_remarks?: string | null;
  principal_remarks?: string | null;
}

export type FeeCategory =
  | 'TUITION'
  | 'ADMISSION'
  | 'TRANSPORTATION'
  | 'EXAMINATION'
  | 'BOOKS'
  | 'STUDY_MATERIAL'
  | 'UNIFORM'
  | 'ID_CARD'
  | 'TIE'
  | 'BELT'
  | 'SHOES'
  | 'DIARY'
  | 'ACTIVITY'
  | 'MISCELLANEOUS'
  | 'OTHER';

export type FeeStructureStatus = 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';

export type DiscountType =
  | 'SIBLING_CONCESSION'
  | 'SCHOLARSHIP'
  | 'STAFF_CONCESSION'
  | 'MANAGEMENT_CONCESSION'
  | 'SPECIAL_DISCOUNT'
  | 'OTHER';

export type PaymentMode = 'CASH' | 'UPI' | 'BANK_TRANSFER' | 'CARD' | 'CHEQUE' | 'OTHER';

export type StudentFeeAssignmentStatus = 'PENDING' | 'PARTIALLY_PAID' | 'PAID' | 'CANCELLED';

export interface FeeItem {
  id: string;
  fee_structure_id: string;
  category: FeeCategory;
  name: string;
  amount: number;
  is_optional: boolean;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface FeeItemCreate {
  category: FeeCategory;
  name: string;
  amount: number;
  is_optional?: boolean;
  order?: number;
}

export interface FeeStructure {
  id: string;
  school_id: string;
  academic_year_id: string;
  school_class_id: string | null;
  name: string;
  description: string | null;
  status: FeeStructureStatus;
  items: FeeItem[];
  created_at: string;
  updated_at: string;
}

export interface FeeStructureCreate {
  academic_year_id: string;
  school_class_id?: string | null;
  name: string;
  description?: string | null;
  status?: FeeStructureStatus;
  items?: FeeItemCreate[];
}

export interface FeeStructureUpdate {
  name?: string;
  description?: string | null;
  school_class_id?: string | null;
  status?: FeeStructureStatus;
  items?: FeeItemCreate[];
}

export interface StudentFeeItem {
  id: string;
  student_fee_assignment_id: string;
  fee_item_id: string | null;
  category: FeeCategory;
  name: string;
  amount: number;
  is_optional: boolean;
  is_applicable: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentFeeItemCreate {
  fee_item_id?: string | null;
  category: FeeCategory;
  name: string;
  amount: number;
  is_optional?: boolean;
  is_applicable?: boolean;
}

export interface FeeDiscount {
  id: string;
  student_fee_assignment_id: string;
  discount_type: DiscountType;
  name: string;
  amount: number;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeeDiscountCreate {
  discount_type: DiscountType;
  name: string;
  amount: number;
  remarks?: string | null;
}

export interface StudentFeeAssignment {
  id: string;
  school_id: string;
  academic_year_id: string;
  student_id: string;
  fee_structure_id: string;
  status: StudentFeeAssignmentStatus;
  due_date: string | null;
  remarks: string | null;
  gross_amount: number;
  total_discounts: number;
  net_payable: number;
  total_paid: number;
  outstanding_due: number;
  student_fee_items: StudentFeeItem[];
  discounts: FeeDiscount[];
  student?: Student | null;
  fee_structure?: FeeStructure | null;
  created_at: string;
  updated_at: string;
}

export interface StudentFeeAssignmentCreate {
  academic_year_id: string;
  student_id: string;
  fee_structure_id: string;
  due_date?: string | null;
  remarks?: string | null;
  custom_items?: StudentFeeItemCreate[];
}

export interface FeePayment {
  id: string;
  school_id: string;
  student_fee_assignment_id: string;
  receipt_number: string;
  amount: number;
  payment_date: string;
  payment_mode: PaymentMode;
  reference_number: string | null;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeePaymentCreate {
  student_fee_assignment_id: string;
  amount: number;
  payment_date: string;
  payment_mode: PaymentMode;
  reference_number?: string | null;
  remarks?: string | null;
}

export interface FeeReceipt {
  receipt_number: string;
  school_id: string;
  student_id: string;
  student_fee_assignment_id: string;
  payment_id: string;
  payment_date: string;
  payment_mode: PaymentMode;
  reference_number: string | null;
  amount: number;
  gross_amount: number;
  total_discounts: number;
  net_payable: number;
  total_paid: number;
  outstanding_due: number;
}

// =====================================================================
// Timetable & Scheduling
// =====================================================================

export type RoomType = 'CLASSROOM' | 'LABORATORY' | 'AUDITORIUM' | 'SPORTS_GROUND';
export type PeriodType = 'REGULAR' | 'BREAK' | 'ASSEMBLY' | 'LUNCH';
export type TimetableStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
export type DayOfWeek = 'MONDAY' | 'TUESDAY' | 'WEDNESDAY' | 'THURSDAY' | 'FRIDAY' | 'SATURDAY' | 'SUNDAY';

export interface Classroom {
  id: string;
  school_id: string;
  room_number: string;
  building_name: string | null;
  capacity: number;
  room_type: RoomType;
  created_at: string;
  updated_at: string;
}

export interface ClassroomCreate {
  school_id: string;
  room_number: string;
  building_name?: string | null;
  capacity?: number;
  room_type?: RoomType;
}

export interface ClassroomUpdate {
  room_number?: string;
  building_name?: string | null;
  capacity?: number;
  room_type?: RoomType;
}

export interface PeriodSlot {
  id: string;
  school_id: string;
  name: string;
  period_type: PeriodType;
  start_time: string;
  end_time: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface PeriodSlotCreate {
  school_id: string;
  name: string;
  period_type?: PeriodType;
  start_time: string;
  end_time: string;
  display_order: number;
}

export interface PeriodSlotUpdate {
  name?: string;
  period_type?: PeriodType;
  start_time?: string;
  end_time?: string;
  display_order?: number;
}

export interface TimetableEntryCreate {
  day_of_week: DayOfWeek;
  period_slot_id: string;
  subject_id: string;
  teacher_id: string;
  classroom_id?: string | null;
}

export interface PeriodSlotNested {
  id: string;
  name: string;
  period_type: PeriodType;
  start_time: string;
  end_time: string;
  display_order: number;
}

export interface SubjectNested {
  id: string;
  subject_name: string;
  subject_code: string;
}

export interface TeacherNested {
  id: string;
  first_name: string;
  last_name: string;
  employee_id: string;
}

export interface ClassroomNested {
  id: string;
  room_number: string;
  building_name: string | null;
  capacity: number;
  room_type: RoomType;
}

export interface TimetableEntryDetail {
  id: string;
  timetable_id: string;
  day_of_week: DayOfWeek;
  period_slot_id: string;
  subject_id: string;
  teacher_id: string;
  classroom_id: string | null;
  created_at: string;
  updated_at: string;
  period_slot: PeriodSlotNested;
  subject: SubjectNested;
  teacher: TeacherNested;
  classroom: ClassroomNested | null;
}

export interface TimetableCreate {
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  academic_term_id?: string | null;
}

export interface Timetable {
  id: string;
  school_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  academic_term_id: string | null;
  status: TimetableStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimetableDetail extends Timetable {
  entries: TimetableEntryDetail[];
}

export interface TeacherScheduleEntry {
  entry_id: string;
  timetable_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  school_class_name: string;
  section_name: string;
  day_of_week: string;
  period_slot: Record<string, unknown>;
  subject: Record<string, unknown>;
  classroom: Record<string, unknown> | null;
}

export interface TeacherSubstitutionCreate {
  school_id: string;
  timetable_entry_id: string;
  substitution_date: string;
  substitute_teacher_id: string;
  remarks?: string | null;
}

export interface TeacherSubstitutionUpdate {
  substitute_teacher_id?: string;
  remarks?: string | null;
}

export interface TeacherSubstitutionResponse {
  id: string;
  school_id: string;
  timetable_entry_id: string;
  substitution_date: string;
  original_teacher_id: string;
  substitute_teacher_id: string;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeacherSubstitutionDetail extends TeacherSubstitutionResponse {
  original_teacher: TeacherNested;
  substitute_teacher: TeacherNested;
  timetable_entry: TimetableEntryDetail;
}

// =====================================================================
// Identity & Access Management (IAM)
// =====================================================================

export interface User {
  id: string;
  school_id: string;
  email: string;
  username: string | null;
  first_name: string;
  last_name: string | null;
  phone: string | null;
  is_active: boolean;
  status?: string;
  suspended_at?: string | null;
  suspension_reason?: string | null;
  roles?: Role[];
  is_super_admin?: boolean;
  is_verified: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  school_id?: string;
  email: string;
  username?: string | null;
  password: string;
  first_name: string;
  last_name?: string | null;
  phone?: string | null;
}

export interface UserUpdate {
  email?: string | null;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  is_active?: boolean | null;
}

export interface Role {
  id: string;
  school_id: string | null;
  name: string;
  description: string | null;
  is_system: boolean;
  is_system_role?: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  school_id?: string | null;
  name: string;
  description?: string | null;
  is_system_role?: boolean;
}

export interface RoleUpdate {
  name?: string | null;
  description?: string | null;
}

export interface Permission {
  id: string;
  name: string;
  description: string | null;
  module: string;
  action: string;
  created_at: string;
  updated_at: string;
}

export interface PermissionFilter {
  module?: string;
  action?: string;
  page?: number;
  page_size?: number;
}

// =====================================================================
// School & Tenant Settings
// =====================================================================

export type SchoolStatus =
  | 'TRIAL'
  | 'ACTIVE'
  | 'PAYMENT_DUE'
  | 'GRACE_PERIOD'
  | 'SUSPENDED'
  | 'BLOCKED'
  | 'CANCELLED'
  | 'INACTIVE'
  | 'MAINTENANCE'
  | 'ARCHIVED';

export interface School {
  id: string;
  name: string;
  code: string;
  address: string | null;
  address_line1?: string;
  city?: string;
  district?: string;
  state?: string;
  postal_code?: string;
  phone: string | null;
  email: string | null;
  website: string | null;
  status: SchoolStatus;
  subscription_tier?: string;
  max_students?: number;
  max_teachers?: number;
  suspension_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface SchoolCreate {
  name: string;
  code: string;
  address?: string | null;
  address_line1?: string;
  city?: string;
  district?: string;
  state?: string;
  postal_code?: string;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
}

export interface SchoolUpdate {
  name?: string | null;
  code?: string | null;
  address?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  status?: SchoolStatus | null;
}


// =====================================================================
// Student Enrollment History & Transfer Certificate (TC)
// =====================================================================

export interface StudentEnrollmentHistoryResponse {
  id: string;
  student_id: string;
  academic_year_id: string;
  school_class_id: string;
  section_id: string;
  roll_number: string | null;
  status: string;
  promotion_decision: string | null;
  remarks: string | null;
  created_at: string;
  academic_year?: AcademicYear;
  school_class?: SchoolClass;
  section?: Section;
}

export interface TransferCertificate {
  id: string;
  school_id: string;
  student_id: string;
  tc_number: string;
  issue_date: string;
  reason: string | null;
  remarks: string | null;
  status: string;
  created_at: string;
}

export interface TransferCertificateCreate {
  tc_number: string;
  issue_date: string;
  reason?: string | null;
  remarks?: string | null;
}

// =====================================================================
// Visitor Management & Reception CRM (Phase 26)
// =====================================================================

export type VisitorStatus = 'EXPECTED' | 'CHECKED_IN' | 'CHECKED_OUT' | 'CANCELLED';
export type HostType = 'TEACHER' | 'STUDENT' | 'STAFF';
export type IdProofType = 'AADHAAR' | 'DRIVING_LICENSE' | 'PASSPORT' | 'VOTER_ID' | 'OTHER';
export type ReceptionInquiryStatus = 'PENDING' | 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED';

export interface VisitorSummary {
  id: string;
  school_id: string;
  visitor_name: string;
  phone: string;
  email?: string | null;
  id_proof_type?: IdProofType | null;
  purpose: string;
  host_type?: HostType | null;
  host_id?: string | null;
  check_in_time?: string | null;
  check_out_time?: string | null;
  status: VisitorStatus;
  pass_number?: string | null;
  created_at: string;
  updated_at: string;
}

export interface VisitorDetail extends VisitorSummary {
  id_proof_number?: string | null;
  remarks?: string | null;
}

export interface VisitorCreate {
  visitor_name: string;
  phone: string;
  email?: string | null;
  id_proof_type?: IdProofType | null;
  id_proof_number?: string | null;
  purpose: string;
  host_type?: HostType | null;
  host_id?: string | null;
  status?: VisitorStatus;
  remarks?: string | null;
}

export interface VisitorCheckOut {
  check_out_time?: string | null;
  remarks?: string | null;
}

export interface ReceptionInquiry {
  id: string;
  school_id: string;
  visitor_id?: string | null;
  contact_name: string;
  contact_phone: string;
  contact_email?: string | null;
  subject: string;
  details?: string | null;
  host_type?: HostType | null;
  host_id?: string | null;
  appointment_time?: string | null;
  status: ReceptionInquiryStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReceptionInquiryCreate {
  visitor_id?: string | null;
  contact_name: string;
  contact_phone: string;
  contact_email?: string | null;
  subject: string;
  details?: string | null;
  host_type?: HostType | null;
  host_id?: string | null;
  appointment_time?: string | null;
  notes?: string | null;
}

export interface ReceptionInquiryUpdate {
  visitor_id?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  subject?: string | null;
  details?: string | null;
  host_type?: HostType | null;
  host_id?: string | null;
  appointment_time?: string | null;
  status?: ReceptionInquiryStatus | null;
  notes?: string | null;
}

export interface AnalyticsPeriod {
  start_date: string;
  end_date: string;
}

export interface VisitorAnalyticsMetrics {
  total: number;
  checked_in: number;
  checked_out: number;
  currently_active: number;
}

export interface InquiryAnalyticsMetrics {
  total: number;
  pending: number;
  in_progress: number;
  resolved: number;
  cancelled: number;
}

export interface AppointmentAnalyticsMetrics {
  total: number;
  upcoming: number;
  completed: number;
}

export interface PurposeCountItem {
  purpose: string;
  count: number;
}

export interface HostTypeCountItem {
  host_type: string;
  count: number;
}

export interface OperationalAnalyticsMetrics {
  avg_visitor_duration_minutes?: number | null;
  peak_checkin_hour?: number | null;
  visitors_by_purpose: PurposeCountItem[];
  visitors_by_host_type: HostTypeCountItem[];
}

export interface DailyTrendItem {
  date: string;
  count: number;
}

export interface ReceptionAnalyticsResponse {
  period: AnalyticsPeriod;
  visitors: VisitorAnalyticsMetrics;
  inquiries: InquiryAnalyticsMetrics;
  appointments: AppointmentAnalyticsMetrics;
  operational_metrics: OperationalAnalyticsMetrics;
  visitor_trend: DailyTrendItem[];
  inquiry_trend: DailyTrendItem[];
}

export interface VisitorPreRegister {
  visitor_name: string;
  phone: string;
  email?: string | null;
  id_proof_type?: IdProofType | null;
  id_proof_number?: string | null;
  purpose: string;
  host_type?: HostType | null;
  host_id?: string | null;
  expected_arrival_time?: string | null;
  remarks?: string | null;
}

export interface VisitorBadgeResponse {
  id: string;
  pass_number: string;
  visitor_name: string;
  phone: string;
  purpose: string;
  host_type?: HostType | null;
  status: VisitorStatus;
  host_name?: string | null;
  check_in_time: string;
  badge_qr_code?: string | null;
}

// =============================================================================
// TRANSPORT MANAGEMENT TYPES & ENUMS (Phase 28.1)
// =============================================================================

export type VehicleType = 'BUS' | 'MINIBUS' | 'VAN' | 'CAB' | 'OTHER';
export type FuelType = 'PETROL' | 'DIESEL' | 'CNG' | 'ELECTRIC' | 'HYBRID' | 'OTHER';
export type VehicleStatus = 'ACTIVE' | 'MAINTENANCE' | 'OUT_OF_SERVICE' | 'DECOMMISSIONED';
export type TransportAllocationType = 'TWO_WAY' | 'PICKUP_ONLY' | 'DROP_ONLY';
export type TransportAllocationStatus = 'ACTIVE' | 'SUSPENDED' | 'CANCELLED';

export interface TransportVehicle {
  id: string;
  school_id: string;
  registration_number: string;
  vehicle_type: VehicleType;
  fuel_type: FuelType;
  capacity?: number;
  vehicle_code: string;
  seating_capacity: number;
  description?: string | null;
  make?: string | null;
  model?: string | null;
  year_of_manufacture?: number | null;
  chassis_number?: string | null;
  engine_number?: string | null;
  insurance_number?: string | null;
  insurance_expiry?: string | null;
  insurance_expiry_date?: string | null;
  fitness_certificate_expiry?: string | null;
  fitness_expiry_date?: string | null;
  puc_expiry?: string | null;
  gps_device_id?: string | null;
  status: VehicleStatus;
  notes?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface TransportVehicleCreate {
  registration_number: string;
  vehicle_type: VehicleType;
  fuel_type: FuelType;
  capacity?: number;
  vehicle_code: string;
  seating_capacity: number;
  description?: string | null;
  make?: string | null;
  model?: string | null;
  year_of_manufacture?: number | null;
  chassis_number?: string | null;
  engine_number?: string | null;
  insurance_number?: string | null;
  insurance_expiry?: string | null;
  insurance_expiry_date?: string | null;
  fitness_certificate_expiry?: string | null;
  fitness_expiry_date?: string | null;
  puc_expiry?: string | null;
  gps_device_id?: string | null;
  status?: VehicleStatus;
  notes?: string | null;
}

export interface TransportVehicleUpdate {
  vehicle_type?: VehicleType;
  fuel_type?: FuelType;
  capacity?: number;
  vehicle_code?: string;
  seating_capacity?: number;
  description?: string | null;
  make?: string | null;
  model?: string | null;
  year_of_manufacture?: number | null;
  chassis_number?: string | null;
  engine_number?: string | null;
  insurance_number?: string | null;
  insurance_expiry?: string | null;
  insurance_expiry_date?: string | null;
  fitness_certificate_expiry?: string | null;
  fitness_expiry_date?: string | null;
  puc_expiry?: string | null;
  gps_device_id?: string | null;
  status?: VehicleStatus;
  notes?: string | null;
}

export interface TransportDriver {
  id: string;
  school_id: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  license_number: string;
  license_expiry?: string;
  driver_name: string;
  contact_phone: string;
  license_expiry_date?: string | null;
  staff_id?: string | null;
  license_type?: string | null;
  experience_years?: number | null;
  address?: string | null;
  emergency_contact?: string | null;
  is_active: boolean;
  notes?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface TransportDriverCreate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  license_number: string;
  license_expiry?: string;
  driver_name: string;
  contact_phone: string;
  license_expiry_date?: string | null;
  staff_id?: string | null;
  license_type?: string | null;
  experience_years?: number | null;
  address?: string | null;
  emergency_contact?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

export interface TransportDriverUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  license_expiry?: string;
  driver_name?: string;
  contact_phone?: string;
  license_expiry_date?: string | null;
  staff_id?: string | null;
  license_type?: string | null;
  experience_years?: number | null;
  address?: string | null;
  emergency_contact?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

export interface RouteStop {
  id: string;
  school_id: string;
  route_id: string;
  stop_name: string;
  stop_order?: number;
  stop_code: string;
  sequence_order: number;
  is_active?: boolean;
  pickup_time?: string | null;
  morning_pickup_time?: string | null;
  drop_time?: string | null;
  afternoon_drop_time?: string | null;
  landmark?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  monthly_charge?: string | null;
  pickup_fee_amount?: number | string | null;
  created_at: string;
  updated_at?: string;
}

export interface RouteStopCreate {
  stop_name: string;
  stop_order?: number;
  stop_code: string;
  sequence_order: number;
  is_active?: boolean;
  pickup_time?: string | null;
  morning_pickup_time?: string | null;
  drop_time?: string | null;
  afternoon_drop_time?: string | null;
  landmark?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  monthly_charge?: string | null;
  pickup_fee_amount?: number | string;
}

export interface RouteStopUpdate {
  stop_name?: string;
  stop_order?: number;
  stop_code?: string;
  sequence_order?: number;
  is_active?: boolean;
  pickup_time?: string | null;
  morning_pickup_time?: string | null;
  drop_time?: string | null;
  afternoon_drop_time?: string | null;
  landmark?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  monthly_charge?: string | null;
  pickup_fee_amount?: number | string | null;
}

export interface TransportRoute {
  id: string;
  school_id: string;
  name?: string;
  code?: string;
  route_code: string;
  route_name: string;
  description?: string | null;
  vehicle_id?: string | null;
  driver_id?: string | null;
  start_point?: string | null;
  end_point?: string | null;
  morning_start_time?: string | null;
  evening_start_time?: string | null;
  attendant_name?: string | null;
  attendant_phone?: string | null;
  is_active: boolean;
  stops_count?: number;
  allocated_students_count?: number;
  vehicle_registration_number?: string | null;
  vehicle_capacity?: number | null;
  driver_name?: string | null;
  driver_phone?: string | null;
  stops?: RouteStop[];
  created_at: string;
  updated_at?: string;
}

export interface TransportRouteCreate {
  name?: string;
  code?: string;
  route_code: string;
  route_name: string;
  description?: string | null;
  vehicle_id?: string | null;
  driver_id?: string | null;
  start_point?: string | null;
  end_point?: string | null;
  morning_start_time?: string | null;
  evening_start_time?: string | null;
  attendant_name?: string | null;
  attendant_phone?: string | null;
  is_active?: boolean;
}

export interface TransportRouteUpdate {
  name?: string;
  code?: string;
  route_code?: string;
  route_name?: string;
  description?: string | null;
  vehicle_id?: string | null;
  driver_id?: string | null;
  start_point?: string | null;
  end_point?: string | null;
  morning_start_time?: string | null;
  evening_start_time?: string | null;
  attendant_name?: string | null;
  attendant_phone?: string | null;
  is_active?: boolean;
}

export interface StudentTransportAllocation {
  id: string;
  school_id: string;
  student_id: string;
  route_id: string;
  stop_id?: string;
  academic_year_id: string;
  allocation_type: TransportAllocationType;
  status: TransportAllocationStatus;
  start_date: string;
  end_date?: string | null;
  remarks?: string | null;
  student_name?: string | null;
  student_admission_number?: string | null;
  admission_number?: string | null;
  student_class_name?: string | null;
  route_name?: string | null;
  route_code?: string | null;
  stop_name?: string | null;
  pickup_stop_name?: string | null;
  drop_stop_name?: string | null;
  pickup_stop_id?: string;
  drop_stop_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface StudentTransportAllocationCreate {
  student_id: string;
  route_id: string;
  stop_id?: string;
  pickup_stop_id?: string | null;
  drop_stop_id?: string | null;
  academic_year_id: string;
  allocation_type?: TransportAllocationType;
  status?: TransportAllocationStatus;
  start_date: string;
  end_date?: string | null;
  remarks?: string | null;
}

export interface StudentTransportAllocationUpdate {
  route_id?: string;
  stop_id?: string;
  pickup_stop_id?: string | null;
  drop_stop_id?: string | null;
  allocation_type?: TransportAllocationType;
  start_date?: string;
  end_date?: string | null;
  remarks?: string | null;
}

export interface StudentTransportAllocationStatusUpdate {
  status: TransportAllocationStatus;
  end_date?: string | null;
  remarks?: string | null;
}

export interface TransportDashboardStats {
  total_vehicles: number;
  active_vehicles: number;
  maintenance_vehicles: number;
  out_of_service_vehicles?: number;
  decommissioned_vehicles?: number;
  total_drivers: number;
  active_drivers: number;
  total_routes: number;
  active_routes: number;
  total_allocated_students?: number;
  total_fleet_capacity?: number;
  capacity_utilization_percentage?: number;
  total_stops?: number;
  active_allocations?: number;
  overall_occupancy_rate_percent: number;
  total_occupied_seats?: number;
  total_seating_capacity?: number;
  total_available_seats?: number;
  vehicles_occupancy: any[];
}

// =============================================================================
// LIBRARY & CIRCULATION TYPES & ENUMS (Phase 28.2)
// =============================================================================

export type BookCondition = 'NEW' | 'GOOD' | 'FAIR' | 'POOR' | 'DAMAGED';
export type BookCopyStatus = 'AVAILABLE' | 'ISSUED' | 'RESERVED' | 'MAINTENANCE' | 'LOST' | 'DISCARDED';
export type BookLoanStatus = 'ISSUED' | 'RETURNED' | 'OVERDUE' | 'LOST';
export type BookReservationStatus = 'PENDING' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED';
export type LibraryFineReason = 'OVERDUE' | 'DAMAGE' | 'LOSS' | 'OTHER';
export type LibraryFineStatus = 'PENDING' | 'PAID' | 'WAIVED';
export type LibraryMemberType = 'STUDENT' | 'TEACHER' | 'STAFF' | 'OTHER';
export type LibraryMemberStatus = 'ACTIVE' | 'SUSPENDED' | 'EXPIRED' | 'CANCELLED';

export interface Library {
  id: string;
  school_id: string;
  name: string;
  code: string;
  description?: string | null;
  location?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LibraryCreate {
  name: string;
  code: string;
  description?: string | null;
  location?: string | null;
  is_active?: boolean;
}

export interface LibraryUpdate {
  name?: string;
  code?: string;
  description?: string | null;
  location?: string | null;
  is_active?: boolean;
}

export interface BookCategory {
  id: string;
  school_id: string;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BookCategoryCreate {
  name: string;
  code: string;
  description?: string | null;
  is_active?: boolean;
}

export interface BookCategoryUpdate {
  name?: string;
  code?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface Book {
  id: string;
  school_id: string;
  title: string;
  subtitle?: string | null;
  author: string;
  co_authors?: string | null;
  publisher?: string | null;
  publication_year?: number | null;
  isbn?: string | null;
  isbn13?: string | null;
  edition?: string | null;
  language?: string;
  total_pages?: number | null;
  category_id?: string | null;
  library_id?: string | null;
  description?: string | null;
  cover_image_url?: string | null;
  is_active: boolean;
  category_name?: string | null;
  library_name?: string | null;
  total_copies_count?: number;
  copies_count?: number;
  available_copies_count?: number;
  created_at: string;
  updated_at: string;
}

export interface BookCreate {
  title: string;
  subtitle?: string | null;
  author: string;
  co_authors?: string | null;
  publisher?: string | null;
  publication_year?: number | null;
  isbn?: string | null;
  isbn13?: string | null;
  edition?: string | null;
  language?: string;
  total_pages?: number | null;
  category_id?: string | null;
  library_id?: string | null;
  description?: string | null;
  cover_image_url?: string | null;
  is_active?: boolean;
}

export interface BookUpdate {
  title?: string;
  subtitle?: string | null;
  author?: string;
  co_authors?: string | null;
  publisher?: string | null;
  publication_year?: number | null;
  isbn?: string | null;
  isbn13?: string | null;
  edition?: string | null;
  language?: string;
  total_pages?: number | null;
  category_id?: string | null;
  library_id?: string | null;
  description?: string | null;
  cover_image_url?: string | null;
  is_active?: boolean;
}

export interface BookCopy {
  id: string;
  school_id: string;
  book_id: string;
  library_id?: string | null;
  accession_number: string;
  barcode?: string | null;
  rfid_tag?: string | null;
  status: BookCopyStatus;
  condition: BookCondition;
  shelf_location?: string | null;
  acquisition_price?: string | null;
  acquisition_date?: string | null;
  remarks?: string | null;
  book_title?: string | null;
  book_author?: string | null;
  library_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookCopyCreate {
  book_id: string;
  library_id?: string | null;
  accession_number: string;
  barcode?: string | null;
  rfid_tag?: string | null;
  status?: BookCopyStatus;
  condition?: BookCondition;
  shelf_location?: string | null;
  acquisition_price?: string | null;
  acquisition_date?: string | null;
  remarks?: string | null;
}

export interface BookCopyUpdate {
  library_id?: string | null;
  accession_number?: string;
  barcode?: string | null;
  rfid_tag?: string | null;
  status?: BookCopyStatus;
  condition?: BookCondition;
  shelf_location?: string | null;
  acquisition_price?: string | null;
  acquisition_date?: string | null;
  remarks?: string | null;
}

export interface LibraryMember {
  id: string;
  school_id: string;
  member_type: LibraryMemberType;
  student_id?: string | null;
  teacher_id?: string | null;
  user_id?: string | null;
  card_number: string;
  issue_date: string;
  expiry_date?: string | null;
  max_books_allowed: number;
  status: LibraryMemberStatus;
  remarks?: string | null;
  display_name?: string | null;
  email?: string | null;
  phone?: string | null;
  active_loans_count?: number;
  created_at: string;
  updated_at: string;
}

export interface LibraryMemberCreate {
  member_type: LibraryMemberType;
  student_id?: string | null;
  teacher_id?: string | null;
  user_id?: string | null;
  card_number: string;
  issue_date?: string;
  expiry_date?: string | null;
  max_books_allowed?: number;
  status?: LibraryMemberStatus;
  remarks?: string | null;
}

export interface LibraryMemberUpdate {
  card_number?: string;
  expiry_date?: string | null;
  max_books_allowed?: number;
  status?: LibraryMemberStatus;
  remarks?: string | null;
}

export interface BookLoan {
  id: string;
  school_id: string;
  book_copy_id: string;
  member_id: string;
  issued_by_user_id?: string | null;
  received_by_user_id?: string | null;
  issue_date: string;
  due_date: string;
  return_date?: string | null;
  renewal_count: number;
  status: BookLoanStatus;
  remarks?: string | null;
  book_title?: string | null;
  accession_number?: string | null;
  barcode?: string | null;
  member_display_name?: string | null;
  member_card_number?: string | null;
  is_overdue?: boolean;
  days_overdue?: number;
  created_at: string;
  updated_at: string;
}

export interface BookLoanCheckout {
  member_id: string;
  book_copy_id: string;
  issue_date?: string;
  due_date?: string;
  remarks?: string | null;
}

export interface BookLoanReturn {
  return_date?: string;
  remarks?: string | null;
}

export interface BookLoanRenew {
  new_due_date?: string;
  remarks?: string | null;
}

export interface BookReservation {
  id: string;
  school_id: string;
  book_id: string;
  member_id: string;
  reservation_date: string;
  expiry_date?: string | null;
  status: BookReservationStatus;
  remarks?: string | null;
  book_title?: string | null;
  member_display_name?: string | null;
  member_card_number?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookReservationCreate {
  book_id: string;
  member_id: string;
  reservation_date?: string;
  expiry_date?: string | null;
  remarks?: string | null;
}

export interface LibraryFine {
  id: string;
  school_id: string;
  loan_id: string;
  member_id: string;
  assessed_by_user_id?: string | null;
  amount: string;
  fine_reason: LibraryFineReason;
  status: LibraryFineStatus;
  paid_date?: string | null;
  waived_date?: string | null;
  waived_by?: string | null;
  waived_reason?: string | null;
  remarks?: string | null;
  member_display_name?: string | null;
  member_card_number?: string | null;
  book_title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LibraryFineCreate {
  loan_id: string;
  member_id: string;
  amount: string;
  fine_reason?: LibraryFineReason;
  status?: LibraryFineStatus;
  remarks?: string | null;
}

export interface LibraryFineWaive {
  waived_reason: string;
}

export interface LibrarySummaryResponse {
  total_libraries_count: number;
  total_categories_count: number;
  total_books_count: number;
  total_copies_count: number;
  available_copies_count: number;
  issued_copies_count: number;
  reserved_copies_count: number;
  maintenance_copies_count: number;
  active_members_count: number;
  active_loans_count: number;
  overdue_loans_count: number;
  pending_reservations_count: number;
  pending_fines_count: number;
  pending_fines_amount: string;
}

// =============================================================================
// ADMISSIONS PIPELINE TYPES & ENUMS (Phase 28.3)
// =============================================================================

export type AdmissionCycleStatus = 'DRAFT' | 'ACTIVE' | 'CLOSED' | 'ARCHIVED';

export type ApplicantStatus =
  | 'PROSPECT'
  | 'APPLIED'
  | 'ENROLLED'
  | 'REJECTED'
  | 'WITHDRAWN';

export type AdmissionApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'WAITLISTED'
  | 'WITHDRAWN';

export type AdmissionDecisionType = 'ACCEPTED' | 'REJECTED' | 'WAITLISTED';

export interface AdmissionCycle {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  status: AdmissionCycleStatus;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdmissionCycleCreate {
  academic_year_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  description?: string | null;
  status?: AdmissionCycleStatus;
  is_active?: boolean;
}

export interface AdmissionCycleUpdate {
  name?: string;
  code?: string;
  start_date?: string;
  end_date?: string;
  description?: string | null;
  status?: AdmissionCycleStatus;
  is_active?: boolean;
}

export interface Applicant {
  id: string;
  school_id: string;
  admission_cycle_id?: string | null;
  applicant_number: string;
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  date_of_birth: string;
  gender: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  parent_name?: string | null;
  parent_phone?: string | null;
  parent_email?: string | null;
  source?: string | null;
  status: ApplicantStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicantCreate {
  admission_cycle_id?: string | null;
  applicant_number?: string | null;
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  date_of_birth: string;
  gender: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  parent_name?: string | null;
  parent_phone?: string | null;
  parent_email?: string | null;
  source?: string | null;
  status?: ApplicantStatus;
  notes?: string | null;
}

export interface ApplicantUpdate {
  admission_cycle_id?: string | null;
  applicant_number?: string | null;
  first_name?: string;
  middle_name?: string | null;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  parent_name?: string | null;
  parent_phone?: string | null;
  parent_email?: string | null;
  source?: string | null;
  status?: ApplicantStatus;
  notes?: string | null;
}

export interface AdmissionApplication {
  id: string;
  school_id: string;
  applicant_id: string;
  admission_cycle_id: string;
  academic_year_id: string;
  target_class_id: string;
  target_section_id?: string | null;
  application_number: string;
  application_date: string;
  status: AdmissionApplicationStatus;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  decision_at?: string | null;
  remarks?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdmissionApplicationCreate {
  applicant_id: string;
  admission_cycle_id: string;
  academic_year_id: string;
  target_class_id: string;
  target_section_id?: string | null;
  application_number?: string | null;
  application_date?: string;
  status?: AdmissionApplicationStatus;
  remarks?: string | null;
}

export interface AdmissionApplicationUpdate {
  target_class_id?: string;
  target_section_id?: string | null;
  application_date?: string;
  remarks?: string | null;
}

export interface ApplicationSubmitRequest {
  remarks?: string | null;
}

export interface ApplicationReviewRequest {
  remarks?: string | null;
}

export interface ApplicationWithdrawRequest {
  reason: string;
  remarks?: string | null;
}

export interface ApplicationStatusHistory {
  id: string;
  school_id: string;
  application_id: string;
  old_status?: string | null;
  new_status: string;
  changed_by_user_id?: string | null;
  changed_at: string;
  reason?: string | null;
  remarks?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdmissionDecision {
  id: string;
  school_id: string;
  application_id: string;
  decision_type: AdmissionDecisionType;
  decided_by_user_id?: string | null;
  decided_at: string;
  comments?: string | null;
  conditions?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdmissionDecisionCreate {
  decision_type: AdmissionDecisionType;
  comments?: string | null;
  conditions?: string | null;
}

// ============================================================================
// INVENTORY & ASSET MANAGEMENT DOMAIN TYPES
// ============================================================================

export type InventoryItemType = 'CONSUMABLE' | 'ASSET';

export type InventoryLocationType =
  | 'WAREHOUSE'
  | 'STORE_ROOM'
  | 'LAB'
  | 'LIBRARY_STORE'
  | 'OFFICE'
  | 'CLASSROOM'
  | 'SPORTS_ROOM'
  | 'OTHER';

export type InventoryStockMovementType =
  | 'PURCHASE_RECEIPT'
  | 'ISSUE'
  | 'TRANSFER'
  | 'RETURN'
  | 'ADJUSTMENT'
  | 'DISCARD';

export type AssetStatus =
  | 'AVAILABLE'
  | 'ASSIGNED'
  | 'IN_REPAIR'
  | 'DAMAGED'
  | 'LOST'
  | 'RETIRED'
  | 'DISPOSED';

export type AssetCondition = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'DAMAGED';

export type AssetAssignmentType =
  | 'STAFF'
  | 'STUDENT'
  | 'CLASSROOM'
  | 'DEPARTMENT'
  | 'LOCATION'
  | 'OTHER';

export type AssetAssignmentStatus = 'ACTIVE' | 'RETURNED' | 'TRANSFERRED';

export interface InventoryCategory {
  id: string;
  school_id: string;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryCategoryCreate {
  name: string;
  code: string;
  description?: string | null;
  is_active?: boolean;
}

export interface InventoryCategoryUpdate {
  name?: string;
  code?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface InventoryLocation {
  id: string;
  school_id: string;
  name: string;
  code: string;
  location_type: InventoryLocationType;
  parent_location_id?: string | null;
  building_name?: string | null;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryLocationCreate {
  name: string;
  code: string;
  location_type?: InventoryLocationType;
  parent_location_id?: string | null;
  building_name?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface InventoryLocationUpdate {
  name?: string;
  code?: string;
  location_type?: InventoryLocationType;
  parent_location_id?: string | null;
  building_name?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface InventoryVendor {
  id: string;
  school_id: string;
  name: string;
  code: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  tax_id?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryVendorCreate {
  name: string;
  code: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  tax_id?: string | null;
  is_active?: boolean;
}

export interface InventoryVendorUpdate {
  name?: string;
  code?: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  tax_id?: string | null;
  is_active?: boolean;
}

export interface InventoryItem {
  id: string;
  school_id: string;
  category_id: string;
  item_code: string;
  name: string;
  description?: string | null;
  item_type: InventoryItemType;
  unit_of_measure: string;
  track_individually: boolean;
  reorder_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category?: InventoryCategory | null;
}

export interface InventoryItemCreate {
  category_id: string;
  item_code: string;
  name: string;
  description?: string | null;
  item_type?: InventoryItemType;
  unit_of_measure?: string;
  track_individually?: boolean;
  reorder_level?: number;
  is_active?: boolean;
}

export interface InventoryItemUpdate {
  category_id?: string;
  item_code?: string;
  name?: string;
  description?: string | null;
  item_type?: InventoryItemType;
  unit_of_measure?: string;
  track_individually?: boolean;
  reorder_level?: number;
  is_active?: boolean;
}

export interface InventoryStock {
  id: string;
  school_id: string;
  item_id: string;
  location_id: string;
  quantity: number;
  reserved_quantity: number;
  unit_price?: number | string | null;
  last_counted_at?: string | null;
  created_at: string;
  updated_at: string;
  item?: InventoryItem | null;
  location?: InventoryLocation | null;
}

export interface InventoryStockSummary {
  total_items: number;
  total_stock_units: number;
  total_locations: number;
  low_stock_items_count: number;
  out_of_stock_items_count: number;
}

export interface StockReceiveRequest {
  item_id: string;
  location_id: string;
  quantity: number;
  unit_price?: number | null;
  vendor_id?: string | null;
  reference_number?: string | null;
  remarks?: string | null;
}

export interface StockIssueRequest {
  item_id: string;
  location_id: string;
  quantity: number;
  reference_number?: string | null;
  remarks?: string | null;
}

export interface StockReturnRequest {
  item_id: string;
  location_id: string;
  quantity: number;
  reference_number?: string | null;
  remarks?: string | null;
}

export interface StockAdjustmentRequest {
  item_id: string;
  location_id: string;
  adjustment_type: 'ADD' | 'SUBTRACT';
  quantity: number;
  reason: string;
  reference_number?: string | null;
}

export interface StockTransferRequest {
  item_id: string;
  source_location_id: string;
  destination_location_id: string;
  quantity: number;
  reference_number?: string | null;
  remarks?: string | null;
}

export interface InventoryStockMovement {
  id: string;
  school_id: string;
  item_id: string;
  source_location_id?: string | null;
  destination_location_id?: string | null;
  movement_type: InventoryStockMovementType;
  quantity: number;
  unit_price?: number | string | null;
  reference_number?: string | null;
  vendor_id?: string | null;
  performed_by_user_id?: string | null;
  movement_date: string;
  remarks?: string | null;
  created_at: string;
  updated_at: string;
  item?: InventoryItem | null;
  source_location?: InventoryLocation | null;
  destination_location?: InventoryLocation | null;
  vendor?: InventoryVendor | null;
}

export interface PhysicalAsset {
  id: string;
  school_id: string;
  item_id: string;
  location_id?: string | null;
  vendor_id?: string | null;
  asset_tag: string;
  serial_number?: string | null;
  model_number?: string | null;
  status: AssetStatus;
  condition: AssetCondition;
  purchase_date?: string | null;
  purchase_cost?: number | string | null;
  warranty_expiry_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  item?: InventoryItem | null;
  location?: InventoryLocation | null;
  vendor?: InventoryVendor | null;
}

export interface PhysicalAssetCreate {
  item_id: string;
  location_id?: string | null;
  vendor_id?: string | null;
  asset_tag: string;
  serial_number?: string | null;
  model_number?: string | null;
  status?: AssetStatus;
  condition?: AssetCondition;
  purchase_date?: string | null;
  purchase_cost?: number | null;
  warranty_expiry_date?: string | null;
  notes?: string | null;
}

export interface PhysicalAssetUpdate {
  location_id?: string | null;
  vendor_id?: string | null;
  asset_tag?: string;
  serial_number?: string | null;
  model_number?: string | null;
  status?: AssetStatus;
  condition?: AssetCondition;
  purchase_date?: string | null;
  purchase_cost?: number | null;
  warranty_expiry_date?: string | null;
  notes?: string | null;
}

export interface PhysicalAssetRetireRequest {
  status?: AssetStatus;
  notes?: string | null;
}

export interface AssetAssignment {
  id: string;
  school_id: string;
  asset_id: string;
  assignment_type: AssetAssignmentType;
  teacher_id?: string | null;
  student_id?: string | null;
  classroom_id?: string | null;
  user_id?: string | null;
  department_name?: string | null;
  assigned_date: string;
  expected_return_date?: string | null;
  actual_return_date?: string | null;
  assigned_by_user_id?: string | null;
  status: AssetAssignmentStatus;
  condition_on_assignment: AssetCondition;
  condition_on_return?: AssetCondition | null;
  remarks?: string | null;
  created_at: string;
  updated_at: string;
  asset?: PhysicalAsset | null;
}

export interface AssetAssignmentCreate {
  asset_id: string;
  assignment_type?: AssetAssignmentType;
  teacher_id?: string | null;
  student_id?: string | null;
  classroom_id?: string | null;
  user_id?: string | null;
  department_name?: string | null;
  assigned_date: string;
  expected_return_date?: string | null;
  condition_on_assignment?: AssetCondition;
  remarks?: string | null;
}

export interface AssetAssignmentReturnRequest {
  actual_return_date: string;
  condition_on_return?: AssetCondition;
  return_location_id?: string | null;
  remarks?: string | null;
}

export interface AssetAssignmentTransferRequest {
  new_assignment_type?: AssetAssignmentType;
  new_teacher_id?: string | null;
  new_student_id?: string | null;
  new_classroom_id?: string | null;
  new_user_id?: string | null;
  new_department_name?: string | null;
  transfer_date: string;
  condition?: AssetCondition;
  remarks?: string | null;
}





