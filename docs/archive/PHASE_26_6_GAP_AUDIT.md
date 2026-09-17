# Phase 26.6 — Reception CRM Gap Audit & Next Capability Definition

## 1. Scope Clarification
This document represents an **internal planning and gap audit** following the completion of internal execution increments Phase 26.1 through Phase 26.5.

**Critical Note:** The official repository roadmap (`docs/product/feature-roadmap.md` and `docs/product/feature-gap-analysis.md`) defines only **Phase 26 — Reception CRM & Visitor Management**. The repository does **NOT** define official sub-phases such as 26.1, 26.2, 26.3, 26.4, 26.5, or 26.6. 

These sub-phases are internal, team-level execution subdivisions created to deliver Reception CRM capabilities in controlled increments. This document does not claim Phase 26.6 is an official roadmap phase; rather, it audits current Reception CRM capabilities, identifies remaining feature gaps, and recommends **one** controlled next implementation subdivision.

---

## 2. Official Phase 26 Requirements
According to `docs/product/feature-roadmap.md` and `docs/product/feature-gap-analysis.md`, the repository's official requirement specification for Phase 26 is high-level and encompasses:

* **Phase 26 — Reception CRM & Visitor Management**: Front-desk operations, visitor registration, visitor entry/exit tracking, gate pass generation, inquiry tracking, appointment management, and operational reception reporting.

---

## 3. Requirement Coverage Matrix

| Requirement | Status | Existing Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Visitor Registration & Identity Details** | COMPLETE | `Visitor` model, `VisitorCreate` schema, `check_in_visitor` service | `backend/app/models/visitor/visitor.py`, `backend/app/api/v1/endpoints/visitors.py` |
| **Gate Pass Generation** | COMPLETE | Server-generated `GP-YYYYMMDD-XXX` tenant-unique pass numbers | `backend/app/services/visitor_service.py` (`_generate_pass_number`) |
| **Visitor Check-Out & State Transitions** | COMPLETE | `check_out_visitor` service, state machine enforcement (`CHECKED_IN` -> `CHECKED_OUT`) | `backend/app/services/visitor_service.py`, `POST /api/v1/visitors/{id}/check-out` |
| **Visitor Search & Pagination** | COMPLETE | Paginated `GET /api/v1/visitors` with status, date, and text search | `backend/app/api/v1/endpoints/visitors.py` |
| **Visitor Identity Privacy (PII Protection)** | COMPLETE | `VisitorSummaryResponse` (omits ID proof number) vs `VisitorResponse` (detailed single record) | `backend/app/schemas/visitor.py` |
| **Reception Inquiries & Appointments** | COMPLETE | `ReceptionInquiry` model, CRUD endpoints, `PENDING` -> `IN_PROGRESS` -> `RESOLVED`/`CANCELLED` state machine | `backend/app/models/visitor/reception_inquiry.py`, `backend/app/api/v1/endpoints/reception_inquiries.py` |
| **Reception Workstation Dashboard** | COMPLETE | `ReceptionPage.tsx` with 4 operational tabs (Overview, Visitors, Inquiries/Appointments, Analytics) | `frontend/src/pages/ReceptionPage.tsx` |
| **Reception Analytics & Reporting** | COMPLETE | `reception_analytics_service.py`, `GET /api/v1/reception/analytics` returning metrics, daily trends, purposes, and host breakdowns | `backend/app/services/reception_analytics_service.py`, `backend/app/api/v1/endpoints/reception_analytics.py` |
| **Tenant Isolation & RBAC** | COMPLETE | `school_id` FK on all models, composite DB indexes, permission guards (`visitors.*`, `reception.*`) | `backend/app/models/visitor/`, `app/identity/models/user.py` |
| **Expected Visitor Pre-Registration** | PARTIALLY COMPLETE | `VisitorStatus.EXPECTED` state exists in database enum, but no dedicated endpoint/UI flow for pre-arrival registration | `backend/app/common/enums/visitor.py` |
| **Printable Visitor Badge / Gate Pass Export** | MISSING | Gate pass number generated, but no printable badge HTML/PDF rendering or pass export | Front desk currently views pass number text only |
| **Interactive Host Directory Search** | PARTIALLY COMPLETE | `host_type` and `host_id` supported in backend models/validation, but UI uses raw text box instead of staff/teacher combobox | `frontend/src/pages/ReceptionPage.tsx` |
| **Host Arrival Notification** | MISSING | No automated notification sent to host staff member on visitor check-in | Notification module unused by reception |

---

## 4. Current Capability Inventory

### 4.1 Visitor Management
* **Registration**: Full visitor creation via `POST /api/v1/visitors/check-in`.
* **Fields Mapped**: Name, Phone, Email, ID Proof Type (`AADHAAR`, `PAN`, `PASSPORT`, `DRIVING_LICENSE`, `VOTER_ID`, `OTHER`), ID Proof Number, Purpose, Host Type (`TEACHER`, `STAFF`, `STUDENT`, `OTHER`), Host ID, Check-In Time, Pass Number, Remarks.
* **Gate Pass**: Automated per-tenant gate pass sequence (`GP-YYYYMMDD-001`, `GP-YYYYMMDD-002`, etc.) backed by unique DB index (`uq_visitor_school_pass_number`).
* **Check-Out**: State machine validation (`POST /api/v1/visitors/{id}/check-out`) enforcing checkout timestamp and remarks recording.
* **PII Protection**: List queries return `VisitorSummaryResponse` (excluding `id_proof_number`). Detailed single-record query requires explicit `visitors.view` permission.

### 4.2 Reception Inquiries & Appointments
* **Creation & Management**: `POST`, `GET`, `PATCH` endpoints for reception inquiries.
* **Fields Mapped**: Contact Name, Contact Phone, Contact Email, Subject, Details, Host Type, Host ID, Appointment Time, Status (`PENDING`, `IN_PROGRESS`, `RESOLVED`, `CANCELLED`), Notes, Linked Visitor ID.
* **Status State Machine**: Transition control preventing illegal updates on resolved or cancelled inquiries.

### 4.3 Reception Workstation UI
* **Tab 1 — Daily Overview**: Metric counters (Active Visitors, Checked Out Today, Pending Inquiries, In-Progress Inquiries, Today's Appointments) and Quick Active Visitors Snapshot with one-click check-out.
* **Tab 2 — Campus Visitors**: Searchable, paginated table with status filters, Check-In modal, Check-Out modal, and Detailed Visitor Dossier drawer.
* **Tab 3 — Inquiries & Appointments**: Inquiry listing, search, create modal, and status/resolution update drawer.
* **Tab 4 — Analytics & Reporting**: Interactive date-preset selector (Today, 7 Days, 30 Days, Custom Range), visitor trend chart, inquiry trend chart, status distribution, top purposes, and host category breakdowns.

---

## 5. Security Gap Audit
* **Tenant Isolation**: **PASS**. `school_id` foreign key with `CASCADE` on all models. DB indexes `ix_visitors_school_id`, `ix_visitors_school_status`, `ix_reception_inquiries_school_id`, etc. enforce isolation. Every service method filters strictly by `current_school_id`.
* **Authorization**: **PASS**. Fine-grained permissions (`visitors.view`, `visitors.checkin`, `visitors.checkout`, `reception.view`, `reception.create`, `reception.update`). Super Admin role bypass handled cleanly via central `authorization.py`.
* **PII Protection**: **PASS**. Government ID proof numbers (`id_proof_number`) omitted from summary list endpoints (`VisitorSummaryResponse`).
* **Audit Logging**: **PASS**. Critical operational actions (`VISITOR_CHECK_IN`, `VISITOR_CHECK_OUT`, `RECEPTION_INQUIRY_CREATE`, `RECEPTION_INQUIRY_UPDATE`) log detailed audit trails via `AuditLog`.
* **Input Validation & Concurrency**: **PASS**. Pydantic string length & enum validation; DB unique constraint `uq_visitor_school_pass_number` prevents gate pass collision during concurrent check-ins; status transition guards prevent double checkouts.

---

## 6. Performance Gap Audit
* **Database Indexing**: **PASS**. Comprehensive composite indexes cover search columns (`school_id`, `status`, `check_in_time`, `phone`, `host_type`, `host_id`, `appointment_time`).
* **Pagination**: **PASS**. API defaults to `page=1`, `page_size=10` (capped at 100). Standard SQL `.limit()` and `.offset()` applied.
* **Analytics Aggregation**: **PASS**. SQL-level aggregation (`func.count()`, `func.avg()`, `extract('hour')`, `group_by()`) prevents in-memory processing overhead.

---

## 7. UX Gap Audit
* **Expected Visitors**: Currently missing a dedicated workflow for pre-registering upcoming visitors prior to arrival.
* **Printable / Downloadable Visitor Gate Pass**: Missing printable badge/pass generation UI. Receptionists must rely on on-screen text pass numbers.
* **Host Directory Selection**: Front-desk receptionist enters host UUIDs manually in a text field rather than choosing staff/teachers from an interactive dropdown.
* **Repeat Visitor Quick Check-In**: No quick-lookup feature to populate visitor identity details for frequent return visitors.

---

## 8. Duplication Audit
Before proposing new capabilities, existing modules were evaluated to prevent duplicate architecture:
* **Appointment Engine**: `ReceptionInquiry.appointment_time` handles reception appointments natively. No duplicate appointment engine needed.
* **Calendar Events**: `Event` model under `app/models/event/` handles campus-wide academic events.
* **PDF / Document Generation**: `student_certificate_service.py` provides HTML-to-PDF / printable document patterns using existing ReportLab / browser print utilities.
* **Notifications**: `notification_service.py` handles internal in-app notifications.

---

## 9. Recommended Next Increment

### **Proposed Phase 26.6 — Expected Visitor Pre-Registration & Visitor Badge Export**

> **Note**: This is an internal capability recommendation, NOT an official repository roadmap requirement.

#### Objective
Extend the Reception CRM system by introducing:
1. **Expected Visitor Pre-Registration**: A dedicated API endpoint and UI flow enabling staff/receptionists to pre-register expected visitors (`VisitorStatus.EXPECTED`), generating pre-registration passes and enabling 1-click check-in upon arrival.
2. **Visitor Badge & Gate Pass Print/Export**: A clean, printable/downloadable visitor badge component (HTML print stylesheet & PDF export layout) containing gate pass number, visitor name, photo/ID reference, host details, check-in timestamp, and a scannable pass QR/barcode visual representation.
3. **Interactive Host Directory Selector**: Front-end host selection component that queries existing Staff and Teacher APIs (`/api/v1/teachers`, `/api/v1/users`) to allow receptionists to search and select hosts by name rather than UUID string input.

#### Why it is next
* Directly completes the operational front-desk visitor lifecycle (pre-register -> check-in -> print badge -> check-out).
* Builds directly on `VisitorStatus.EXPECTED` foundation established in Phase 26.1.
* Fills the biggest UX gap identified in front-desk operations (printable gate pass badge and host directory lookup).
* Preserves clean architecture without triggering Phase 27 SMS/WhatsApp notifications.

#### Scope Breakdown
* **Backend**: 
  - `POST /api/v1/visitors/pre-register` endpoint for expected visitor creation.
  - `POST /api/v1/visitors/{id}/quick-check-in` to transition `EXPECTED` -> `CHECKED_IN`.
  - `GET /api/v1/visitors/{id}/badge` endpoint (or frontend client-side print view) formatted for standard thermal label printers (3"x2") and standard A4/letter pass slips.
* **Frontend**:
  - Pre-Register Visitor modal in `ReceptionPage.tsx`.
  - Interactive Host Lookup Combobox (searching Staff/Teachers by name/department).
  - Printable Gate Pass Badge drawer & print modal (`@media print` optimized).
  - 1-Click "Check-In Expected Visitor" action button on Overview and Visitors tabs.
* **RBAC & Security**:
  - Reuses `visitors.checkin` and `visitors.view` permissions.
  - Strict tenant isolation enforced on all new endpoints.
* **Explicit Out-of-Scope**:
  - SMS/WhatsApp alerts on visitor arrival (Deferred to Phase 27).
  - Facial recognition or biometric hardware integrations.
  - Self-service kiosk mode.

---

## 10. Alternative Future Capabilities
Secondary candidates for future internal increments (after Phase 26.6):
1. **Host Arrival Notification Integration**: Sending in-app notifications to host staff when their visitor checks in.
2. **Repeat Visitor Directory & Quick Re-Entry**: Automatic phone number lookup to pre-fill past visitor details for frequent guests.
3. **Visitor Blacklist / Security Watchlist Alerts**: Warning alerts for flagged phone numbers or unauthorized individuals.

---

## 11. Regression Verification Baseline

The full system regression suite was executed to certify the baseline prior to closing this audit.

```text
Backend Regression (pytest):
983 passed / 0 failed

Frontend Regression (Vitest):
142 passed / 0 failed (21 test files)

TypeScript Compilation (npx tsc --noEmit):
PASS (0 errors)

Production Build (npm run build):
PASS (vite build success in 6.63s)

Alembic Migration Heads (python -m alembic heads):
721c276bdd9d (head) [Single alembic head verified]

Core Authorization Integrity (git diff -- app/identity/security/authorization.py):
0 diff / UNCHANGED
```
