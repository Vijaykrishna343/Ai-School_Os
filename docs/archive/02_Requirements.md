# AI School OS — System Requirements & Specifications

## 1. Functional Requirements

### 1.1 Multi-Tenant Isolation & Security
- **FR-SEC-01**: The system MUST isolate data between schools using `school_id` tenant scoping.
- **FR-SEC-02**: All protected endpoints MUST require a valid JWT access token. Refresh tokens MUST be rejected for API data access.
- **FR-SEC-03**: Soft-deleted or inactive user accounts MUST be rejected immediately during token authentication.
- **FR-SEC-04**: Role-Based Access Control (RBAC) MUST validate specific permission names (e.g. `student.view`, `progression.execute`) via `@require_permission`.
- **FR-SEC-05**: Cross-tenant resource modification via path or body parameter tampering MUST be blocked with a `422` or `400` validation error.

### 1.2 Academic Infrastructure
- **FR-ACA-01**: Only one `AcademicYear` MUST be marked `is_current = True` per school at any given time.
- **FR-ACA-02**: Deactivating or transitioning an academic year MUST reset all current year flags for the tenant.
- **FR-ACA-03**: Schools MAY define a `ClassProgressionRule` matrix specifying `source_class_id` to `target_class_id` or `is_terminal = True`.

### 1.3 Academic Progression & Rollover Engine (Phase 4B)
- **FR-PRG-01 (Planner)**: The system MUST calculate prospective student promotion decisions based on configured progression rules, student status, and academic standing without mutating persistent data.
- **FR-PRG-02 (Preview)**: The API MUST return a complete read-only dry-run summary (`ProgressionPreviewResponse`) including promoted, retained, graduated, and blocked counts.
- **FR-PRG-03 (Execution)**: The execution rollover endpoint MUST require an `Idempotency-Key` header and an `execution_plan_hash` matching the SHA-256 calculation of the prospective plan.
- **FR-PRG-04 (Atomicity)**: Execution rollover MUST execute in a single atomic transaction. If any student update fails or hash mismatch occurs, the entire transaction MUST abort and roll back.
- **FR-PRG-05 (History Preservation)**: Upon promotion, retention, or graduation, previous enrollment history MUST be preserved immutably in `StudentEnrollmentHistory`.

### 1.4 Student & Parent Management
- **FR-STU-01**: Permanent admission numbers (`admission_number`) MUST be generated automatically and remain unchanged across academic years.
- **FR-STU-02**: Annual roll numbers (`roll_number`) MUST be assigned sequentially per class/section per academic year with retry logic for concurrency safety.
- **FR-STU-03**: Soft-deleted students MUST NOT block creation of new active students or reuse of roll/admission numbers under active records.
- **FR-STU-04**: Transfer Certificates (TC) MUST set student status to `TRANSFERRED` and issue a unique `tc_number`.

---

## 2. Non-Functional Requirements

### 2.1 Performance & Scalability
- **NFR-PERF-01**: Database queries MUST use composite indexes for high-frequency queries (e.g. `(school_id, attendance_date)`, `(school_id, academic_year_id, student_id)`).
- **NFR-PERF-02**: Bulk operations (e.g., bulk student promotion) MUST execute within a single database transaction with batching.

### 2.2 Integrity & Reliability
- **NFR-REL-01**: Partial unique indexing (`WHERE is_deleted = FALSE`) MUST be enforced on tenant-scoped entity names and codes to allow re-creation after soft-deletion.
- **NFR-REL-02**: Production configuration MUST fail fast if `ENVIRONMENT == "production"` is started with `DEBUG = True` or default placeholder `SECRET_KEY`.

### 2.3 Quality Assurance & Standards
- **NFR-QA-01**: Automated unit and integration test suite MUST maintain 100% pass rate.
- **NFR-QA-02**: Standardized API response format MUST be returned for all success and error responses:
  ```json
  {
    "success": boolean,
    "message": string,
    "data": object | null,
    "errors": object | null
  }
  ```
