# Phase 30.9 — Legacy Data Migration & Bulk Onboarding Subsystem (GAP-05)

## 1. Overview

Phase 30.9 resolves **GAP-05 (Data Onboarding)** identified during the Phase 30.7 system audit. It establishes a resilient, production-ready legacy data migration and bulk onboarding subsystem allowing school administrators to migrate historical data from CSV/Excel-derived datasets into the AI School OS.

---

## 2. Supported Entity Migration Types

| Entity Type | Endpoint Key | Required Columns | Optional Columns | Mutation Semantics |
|---|---|---|---|---|
| **Students** | `students` | `first_name, last_name, gender, admission_number` | `middle_name, roll_number, date_of_birth, admission_date, blood_group, phone, email, address_line1, city, district, state, country, postal_code, class_name, section_name, academic_year_name, parent_phone, parent_name` | Creates/links parents, academic years, classes, and sections. Deduplicates against admission number. |
| **Teachers** | `teachers` | `first_name, last_name` | `middle_name, employee_id, phone, email, gender, date_of_birth, qualification, specialization, joining_date, experience_years, address_line1, city, state` | Creates teacher profiles with contact info and system user linkage. |
| **Parents** | `parents` | `primary_phone` | `father_name, mother_name, guardian_name, relationship, secondary_phone, email, occupation, annual_income, address_line1, city, district, state` | Deduplicates by primary phone number. |
| **Legacy Fee Structures** | `fee_structures` | `academic_year, fee_structure_name, item_name, amount` | `class_name, item_category, is_optional, description` | Groups rows by fee structure name, resolves/creates fee items under correct `FeeCategory` using `Decimal` amounts. |
| **Outstanding Balances** | `outstanding_balances` | `admission_number, academic_year, fee_name, assessed_amount` | `paid_amount, due_date, remarks` | Creates opening `StudentFeeAssignment` and `StudentFeeItem` entries with `PARTIALLY_PAID`, `PENDING`, or `PAID` statuses. **Guarantees 0 fake `FeePayment` records are fabricated.** |
| **Historical Marks** | `historical_marks` | `admission_number, academic_year, class_name, section_name, exam_name, subject_code, marks_obtained` | `max_marks, passing_marks, remarks` | Resolves `Subject`, `Exam`, and `ExamSchedule`. Validates `0 <= marks_obtained <= max_marks`. Updates `StudentExamResult` idempotently. |

---

## 3. Core Architectural Guarantees

### A. Dry-Run Savepoint Isolation (Zero Persistent DB Mutations)
- `POST /api/v1/import/{entity_type}/preview` executes within a database savepoint (`db.begin_nested()`).
- All validation rules, foreign key lookups, and simulated inserts execute against the live schema.
- At the end of the preview cycle, `savepoint.rollback()` is unconditionally invoked.
- Zero mutations or orphaned sequences remain in the database.

### B. Two-Phase Commit with Atomic / Non-Atomic Modes
- `POST /api/v1/import/{entity_type}/commit?atomic_mode=true` (default):
  - Previews dataset first. If any row fails validation, aborts immediately with `HTTP 422 Unprocessable Entity` and commits 0 rows.
  - If preview passes, executes commit inside a top-level transactional block. Any unhandled exception triggers a full rollback.
- `atomic_mode=false`:
  - Inserts valid rows while capturing and returning invalid row diagnostics.

### C. Financial & Mathematical Precision
- All monetary and score values (`amount`, `assessed_amount`, `paid_amount`, `marks_obtained`, `max_marks`, `passing_marks`) are processed strictly as Python `Decimal` objects.
- Float conversions are completely prohibited to prevent IEEE-754 precision loss.

### D. Multi-Tenant & RBAC Isolation
- All entity lookups and mutations strictly filter on `school_id = current_user.school_id`.
- Foreign entities from other tenants trigger reference errors and cannot be accessed.
- Endpoint RBAC mappings:
  - `students` -> `student.create`
  - `teachers` -> `staff.create`
  - `parents` -> `parent.create`
  - `fee_structures` -> `fees.create`
  - `outstanding_balances` -> `fees.create`
  - `historical_marks` -> `marks.create`

---

## 4. Verification & Test Coverage

- **Automated Backend Tests**: `backend/tests/test_legacy_data_migration.py` (12 tests, 100% pass)
  - Legacy fee structures validation & category parsing.
  - Outstanding balances opening assignments without fake payments.
  - Historical marks validation, upper bounds checking, and idempotent updates.
  - Dry-run zero DB persistent mutation guarantee.
  - Atomic rollback on partial failure.
  - RBAC permission enforcement (HTTP 403) and multi-tenant isolation.
- **Phase 9 Core Import/Export Tests**: `backend/tests/test_phase9.py` (37 tests, 100% pass).
- **Frontend Vitest Suite**: 30 test files, 214 unit/integration tests passing.
- **Frontend Production Build**: `npm run build` succeeds cleanly with 0 TypeScript/Vite errors.
- **Alembic Head**: `z9a045bc11z5` preserved with 0 new database migrations.
- **Authorization Guard**: `backend/app/identity/security/authorization.py` has 0 diff.
