# AI School OS — Database Design & Schema Specification

## 1. Core Database Entities

| Entity / Table Name | Primary Purpose | Tenant Scoped | Soft Delete Supported |
| :--- | :--- | :--- | :--- |
| `schools` | School tenant root entity | Root | Yes |
| `identity_users` | System user authentication & profile | Yes (`school_id`) | Yes |
| `identity_roles` | RBAC role definitions | Yes (`school_id`) | Yes |
| `identity_permissions` | System permissions dictionary | Global | No |
| `academic_years` | School academic year sessions | Yes (`school_id`) | Yes |
| `academic_terms` | Terms/semesters within academic year | Yes (`school_id`) | Yes |
| `school_classes` | Grade levels / classes | Yes (`school_id`) | Yes |
| `sections` | Class sections / divisions | Via `school_class_id` | Yes |
| `class_progression_rules` | Progression matrix rules | Yes (`school_id`) | Yes |
| `progression_executions` | Academic rollover execution log | Yes (`school_id`) | No |
| `parents` | Parent / guardian master records | Yes (`school_id`) | Yes |
| `students` | Student master records | Yes (`school_id`) | Yes |
| `student_enrollment_histories` | Historical enrollment ledger | Yes (`school_id`) | Yes |
| `transfer_certificates` | Issued Transfer Certificates | Yes (`school_id`) | Yes |
| `attendances` | Daily student attendance records | Yes (`school_id`) | Yes |
| `exams` | Master exam definitions | Yes (`school_id`) | Yes |
| `exam_schedules` | Exam timetable schedules | Yes (`school_id`) | Yes |
| `student_exam_results` | Exam marks & evaluations | Yes (`school_id`) | Yes |
| `fee_structures` | Master fee category definitions | Yes (`school_id`) | Yes |
| `student_fee_assignments` | Assigned student fee ledgers | Yes (`school_id`) | Yes |
| `fee_payments` | Fee collection payment logs | Yes (`school_id`) | Yes |
| `grading_scales` | Grading scale rules & grade entries | Yes (`school_id`) | Yes |
| `evaluation_configs` | Class evaluation weighting configs | Yes (`school_id`) | Yes |
| `report_cards` | Generated student report cards | Yes (`school_id`) | Yes |
| `period_slots` | Timetable period definitions | Yes (`school_id`) | Yes |
| `classrooms` | Room / hall master records | Yes (`school_id`) | Yes |
| `timetables` | Section timetable headers | Yes (`school_id`) | Yes |
| `timetable_entries` | Section timetable schedule slots | Via `timetable_id` | Yes |
| `teacher_substitutions` | Daily teacher substitution logs | Yes (`school_id`) | Yes |

---

## 2. Partial Unique Indexes & Soft Deletion Semantics (Phase 4C.2)

To ensure soft-deleted records do not block creating active entities with identical names, codes, or roll numbers, PostgreSQL partial unique indexes (`WHERE is_deleted = FALSE`) are applied across core entities:

```sql
-- Academic Years
CREATE UNIQUE INDEX uq_academic_years_school_name_active
ON academic_years (school_id, name) WHERE is_deleted = FALSE;

-- School Classes
CREATE UNIQUE INDEX uq_school_classes_school_name_active
ON school_classes (school_id, name) WHERE is_deleted = FALSE;

-- Sections
CREATE UNIQUE INDEX uq_sections_class_name_active
ON sections (school_class_id, name) WHERE is_deleted = FALSE;

-- Student Roll Numbers
CREATE UNIQUE INDEX uq_students_roll_number_active
ON students (academic_year_id, school_class_id, roll_number) WHERE is_deleted = FALSE;

-- Student Admission Numbers
CREATE UNIQUE INDEX uq_students_admission_number_active
ON students (admission_number) WHERE is_deleted = FALSE;

-- Student Enrollment History (One active enrollment record per student per year)
CREATE UNIQUE INDEX uq_enrollment_history_year_active
ON student_enrollment_histories (school_id, student_id, academic_year_id) WHERE is_deleted = FALSE;

-- Transfer Certificates
CREATE UNIQUE INDEX uq_tc_school_number_active
ON transfer_certificates (school_id, tc_number) WHERE is_deleted = FALSE;

-- Class Progression Matrix Rules (One active progression rule per source class)
CREATE UNIQUE INDEX uq_class_progression_school_source
ON class_progression_rules (school_id, source_class_id) WHERE is_deleted = FALSE;
```

---

## 3. High-Performance Composite Indexes (PERF-01)

To optimize frequent tenant-scoped search queries and ledger lookups:

```sql
-- Daily Attendance Range Queries
CREATE INDEX ix_attendances_school_date
ON attendances (school_id, attendance_date);

-- Student Fee Ledger Lookups
CREATE INDEX ix_fee_assignments_school_year_student
ON student_fee_assignments (school_id, academic_year_id, student_id);
```

---

## 4. Foreign Key Delete Cascades & Protections

- **Parent Entities (`schools`, `school_classes`)**: `ON DELETE CASCADE` removes child sections and configuration records upon entity deletion.
- **Historical Ledgers (`student_enrollment_histories`)**: Foreign keys to `academic_years`, `school_classes`, and `sections` use `ON DELETE RESTRICT` to guarantee historical class placement ledgers cannot be orphaned or accidentally purged.