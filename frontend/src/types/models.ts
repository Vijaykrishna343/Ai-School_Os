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



