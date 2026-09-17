# PHASE 30.1 — PARENT & STUDENT SELF-SERVICE TRANSACTIONAL WORKFLOWS
**Certified Implementation & Verification Dossier**

---

## 1. Executive Summary & Objective

Phase 30.1 successfully closes the two highest-priority user-facing gaps identified in the certified Phase 30.0 product maturity audit:
* **GAP-01 — Parent Portal Transactional Workflows**: Replaced read-only dashboards with active transactional workflows enabling multi-ward switching, end-to-end online fee settlement (Razorpay / Stripe / Simulator), official receipt retrieval, and published term report card inspection.
* **GAP-02 — Student Portal Transactional Workflows**: Replaced passive summary cards with active daily period schedules, digital homework submissions and resubmissions, and student-scoped library circulation loan tracking.

This phase was executed under strict architecture constraints:
1. **Zero Database Migrations**: Alembic schema maintained at single head `z9a045bc11z5 (head)`.
2. **Zero Security Regressions**: Zero diff on core authorization engine `backend/app/identity/security/authorization.py`.
3. **Fail-Closed Relationship Scoping**: Strict enforcement of `verify_parent_student_relationship` and `enforce_relationship_access` preventing cross-parent and cross-student data leakage.
4. **Draft Confidentiality**: Parents and students can only access `PUBLISHED` academic report cards; draft report cards fail-closed with HTTP 403 Forbidden.

---

## 2. API & Security Matrix

| User Role | Workflow / Capability | Endpoint | Method | Permission Required | Security Scoping Invariant |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Parent** | Multi-Ward Summary | `/api/v1/dashboard/parent/summary` | `GET` | `dashboard.parent.view` | Multi-child resolution via parent email/phone; filters only authorized wards. |
| **Parent** | Fee Assignments & Balances | `/api/v1/fees/assignments` | `GET` | `fee.view` | Scoped to parent's active child via `verify_parent_student_relationship`. |
| **Parent** | Create Payment Order | `/api/v1/payments/orders` | `POST` | `payment.create` / `Parent` role | Validates child belongs to parent; raises 403 if unauthorized assignment. |
| **Parent** | Verify Payment Gateway Sig | `/api/v1/payments/verify` | `POST` | `payment.verify` / `Parent` role | Validates HMAC-SHA256 signature, records fee payment, updates assignment status. |
| **Parent** | View / Download Fee Receipt | `/api/v1/fees/payments/{id}/receipt`| `GET` | `fee.view` | Validates payment belongs to parent's ward; raises 403 if unrelated student. |
| **Parent** | View Published Report Cards | `/api/v1/report-cards` | `GET` | `report_card.view` | Enforces `status=PUBLISHED` for non-staff; filters to parent's selected child. |
| **Student** | Student Academic Summary | `/api/v1/dashboard/student/summary` | `GET` | `dashboard.student.view` | Resolves student profile linked to authenticated user id. |
| **Student** | Daily Class Period Schedule | `/api/v1/timetables/section/{id}` | `GET` | `timetable.view` | Scoped to student's enrolled section and academic term. |
| **Student** | Digital Homework Submission | `/api/v1/homework/{id}/submit` | `POST` | `homework.submit` | Creates submission record; updates to `RESUBMITTED` on repeat submissions. |
| **Student** | My Library Circulation Loans | `/api/v1/library/loans` | `GET` | `library.view` | Scoped strictly to student's own library membership card loans. |

---

## 3. Backend Hardening Details

### 3.1 Report Card Status Filtering
In [`backend/app/api/v1/endpoints/report_card.py`](file:///c:/Projects/school-erp/backend/app/api/v1/endpoints/report_card.py):
* When querying report cards, non-staff roles (`Parent`, `Student`) are strictly restricted to `ReportCardStatus.PUBLISHED`.
* Direct retrieval of draft or finalized un-published report cards via `GET /report-cards/{id}` returns HTTP 403 Forbidden.

### 3.2 Library Loan Scoping
In [`backend/app/api/v1/endpoints/library.py`](file:///c:/Projects/school-erp/backend/app/api/v1/endpoints/library.py):
* `GET /api/v1/library/loans` filters loans by student relationship when accessed by student or parent credentials.

### 3.3 Role Permission Seeding
In [`backend/app/identity/seeders/role_permission_seeder.py`](file:///c:/Projects/school-erp/backend/app/identity/seeders/role_permission_seeder.py):
* Explicitly mapped `timetable.view` and `report_card.view` permissions to default `Parent` and `Student` role definitions.

---

## 4. Frontend Self-Service Workstations

### 4.1 Parent Command Center (`DashboardPage.tsx`)
* **Multi-Child Tab Switcher**: Interactive selector tabs allowing parents with multiple wards to toggle instantly between children.
* **Online Fee Settlement Modal**: Allows parents to select payment gateway (Instant Simulator, Razorpay, Stripe), initiate cryptographic payment orders, verify transactions, and auto-refresh the ledger.
* **Official Fee Receipt Modal**: Displays formatted printable transaction details, line items, payment modes, and timestamped receipt numbers.
* **Published Report Cards Viewer**: Full dialog displaying official published term results, subject mark breakdown, GPA, attendance percentages, and teacher remarks.

### 4.2 Student Workstation (`DashboardPage.tsx`)
* **Today's Class Period Schedule**: Real-time cards displaying period slots, timings, subjects, assigned faculty, and classroom designations.
* **Interactive Homework Submission Workspace**: Modal allowing students to submit text answers, work references, and notes directly against published assignments.
* **Library Circulation Docket**: Cards displaying active book loans, accession numbers, authors, and due dates.

---

## 5. Verification & Quality Gates

### 5.1 Backend Pytest Suite
* File: [`backend/tests/test_parent_student_self_service.py`](file:///c:/Projects/school-erp/backend/tests/test_parent_student_self_service.py)
* **11 of 11 tests PASSED (100%)**
* Coverage includes:
  - Multi-ward switching and unassigned student rejection (403)
  - Payment order generation, cryptographic signature verification, ledger balance update, and receipt generation
  - Cross-tenant and cross-parent receipt access denial
  - Report card publication scoping (published allowed, draft forbidden)
  - Student section timetable retrieval
  - Student homework submission and resubmission lifecycle
  - Student library loan isolation
  - Inactive user and unauthenticated request rejection (401)

### 5.2 Frontend Vitest Suite
* File: [`frontend/src/test/parent_student_workflows.test.tsx`](file:///c:/Projects/school-erp/frontend/src/test/parent_student_workflows.test.tsx)
* **6 of 6 tests PASSED (100%)**
* Coverage includes:
  - Parent workstation rendering with multi-ward tabs
  - Ward switching and state synchronization
  - Fee payment modal checkout flow and order initiation
  - Published report card viewer modal
  - Student workstation rendering with schedule, homework, and loans
  - Homework modal submission execution
* **Full Frontend Suite**: 26 test files, 197 tests passing (100%).
* **TypeScript Compilation**: `npx tsc --noEmit` exited with 0 errors.

---

## 6. Security & Invariant Checklist

- [x] Zero database migrations (`z9a045bc11z5 (head)` single head).
- [x] Zero diff on `backend/app/identity/security/authorization.py`.
- [x] Multi-tenant isolation verified across all endpoints.
- [x] Inactive users rejected with HTTP 401 Unauthorized.
- [x] Draft report cards confidential to faculty/staff only.
- [x] Payment amount server-derived with zero client manipulation.
- [x] Homework submission and resubmission scoped strictly to enrolled student.
- [x] Library circulation loans scoped strictly to student / parent relationship.

---

## 7. Final Certification Gate

### 7.1 Fresh Execution Evidence

| Quality Gate | Exact Command | Execution Result | Time / Duration |
| :--- | :--- | :--- | :--- |
| **Focused Backend Suite** | `pytest tests/test_parent_student_self_service.py -v` | **11 passed, 0 failed, 1 warning** | 35.89s |
| **Full Backend Regression** | `pytest -q` | **1,233 passed, 0 failed, 0 errors, 0 skipped, 7 warnings** | 1568.92s (0:26:08) |
| **Full Frontend Vitest Suite** | `npx vitest run` | **26 test files passed, 197 / 197 tests passed** | 39.20s |
| **TypeScript Typecheck** | `npx tsc --noEmit` | **0 errors (Exit code 0)** | 14.12s |
| **Production Bundle Build** | `npm run build` | **Build completed (Exit code 0)** | 12.94s |
| **Alembic Head Integrity** | `alembic heads` | **`z9a045bc11z5 (head)` (Single head)** | Instant |
| **Migration Status** | `alembic current` | **0 migrations added in Phase 30.1** | Instant |
| **Core Authorization Invariant** | `git diff -- authorization.py` | **0 diff** | Instant |
| **Secret Scan** | `git diff HEAD \| findstr /I "secret password..."` | **0 plaintext keys/secrets detected** | Instant |

### 7.2 Complete Changed-File Classification

| File Path | Classification | Rationale |
| :--- | :--- | :--- |
| `backend/app/api/v1/endpoints/report_card.py` | Phase 30.1 Implementation | Enforces `status=PUBLISHED` and draft denial (403) for non-staff. |
| `backend/app/identity/seeders/role_permission_seeder.py` | Phase 30.1 Implementation | Seeds `timetable.view` and `report_card.view` to Parent and Student roles. |
| `frontend/src/services/api/paymentsApi.ts` | Phase 30.1 Implementation | Typed API client for `/api/v1/payments/orders` and `/verify`. |
| `frontend/src/services/api/index.ts` | Phase 30.1 Implementation | Re-exports `paymentsApi`. |
| `frontend/src/pages/DashboardPage.tsx` | Phase 30.1 Implementation | Parent and student transactional workstation UI modals and workflows. |
| `backend/tests/test_parent_student_self_service.py` | Phase 30.1 Test | Complete backend transactional test suite (11 tests). |
| `frontend/src/test/parent_student_workflows.test.tsx` | Phase 30.1 Test | Complete frontend workstation test suite (6 tests). |
| `docs/PHASE_30_1_PARENT_STUDENT_PORTALS.md` | Phase 30.1 Documentation | Formal architecture, security, and certification dossier. |

### 7.3 Security Audit Verification

1. **Parent Relationship Authorization**: Server-side verification via `verify_parent_student_relationship` prevents cross-parent fee access and unauthorized ward switching.
2. **Student Self-Access Authorization**: Students access only their own section timetables, own homework submissions, and own library loans.
3. **Payment Security**: Payable amount is server-derived from `StudentFeeAssignment` ledger balance; HMAC-SHA256 signature verification validates authenticity.
4. **Report Card Confidentiality**: `PUBLISHED` cards accessible; un-published draft cards fail-closed with HTTP 403 Forbidden.
5. **Homework Submission Security**: Submissions bound to authenticated student id and school tenant. Digital submission accepts text writeup/notes and references.
6. **Library Security**: Scoped via `enforce_relationship_access` to membership records belonging to authenticated student.

### 7.4 Final Certification Decision

# PHASE 30.1 — CERTIFIED

