# PHASE 27.4 — EVENT-DRIVEN ERP NOTIFICATION AUTOMATION: AUDIT & GAP ANALYSIS

## 1. Objective & Scope
The objective of **Phase 27.4** is to establish an event-driven notification automation layer that connects authoritative ERP business events to the certified SMS/WhatsApp notification infrastructure (Phases 27.1–27.3).

This audit conducts a thorough implementation-readiness review across the codebase, establishing event contracts, recipient resolution rules, transaction safety mechanisms, idempotency keys, and tenant isolation policies prior to code modification.

---

## 2. Current Certified Baseline
- **Phase 26.1–26.6**: Reception / Visitor Management (Certified)
- **Phase 27.1**: Communication Configuration & Encrypted Provider Credentials (Certified)
- **Phase 27.2**: Provider-Neutral SMS Gateway (Fast2SMS & Twilio) + DLT Metadata (Certified)
- **Phase 27.3**: Meta WhatsApp Cloud API v21.0 Adapter & Webhooks (Certified)
- **Full Backend Tests**: 1,019 passed / 0 failed
- **Full Frontend Tests**: 144 passed / 0 failed
- **TypeScript**: PASS (0 errors)
- **Production Build**: PASS
- **Alembic Single Head**: `b5683cd19824`
- **Security Core**: `app/identity/security/authorization.py` (0 diff)

---

## 3. Audit of Existing Event & Job Infrastructure

### A. Core Notification Service (`app/services/notification_service.py`)
- **Capabilities**: Multi-channel dispatch (`EMAIL`, `SMS`, `WHATSAPP`, `IN_APP`), fallback template rendering (`render_template`), user communication preference checking (`should_deliver`), idempotency enforcement (`idempotency_key`), bounded retry execution (`retry_failed_notification`).
- **Template Engine**: Default fallback templates exist for `student_absent_alert`, `fee_payment_received`, `general_announcement`, `emergency_alert`, etc.
- **Provider Layer**: Provider adapters (`SmsNotificationProvider`, `WhatsAppNotificationProvider`) handle DLT routing, Fast2SMS, Twilio, and Meta WhatsApp Cloud API without business domain coupling.

### B. Background Job Runner (`app/services/async_job_runner.py`)
- **Capabilities**: Executes background jobs (`BackgroundJob`) asynchronously with session isolation.
- **Job Types**: Currently supports `BATCH_REPORT_CARD_GEN` and `BULK_NOTIFICATION_DISPATCH`.
- **Integration**: Can be extended or invoked via FastAPI `BackgroundTasks` to ensure DB transaction isolation (business transaction commits *before* background notification dispatch).

---

## 4. ERP Business Event Matrix

| Event | Authoritative Source | Current Event Trigger Exists? | Target Channels | Default Recipient | Idempotency Key Pattern | Gap Identified |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Visitor Arrival (Check-In)** | `visitor_service.check_in_visitor` & `quick_check_in_visitor` | Audit log only | `SMS`, `WHATSAPP`, `IN_APP` | Host Staff / Host Teacher | `visitor_checkin:{visitor_id}` | Needs automated notification dispatch to host upon visitor check-in |
| **2. Visitor Departure (Check-Out)** | `visitor_service.check_out_visitor` | Audit log only | `IN_APP` | Host Staff / Host Teacher | `visitor_checkout:{visitor_id}` | Optional departure alert for host staff |
| **3. Fee Receipt / Payment Received** | `payment_settlement_service.settle_payment_transaction` & `fee_service.record_payment` | Log only | `SMS`, `WHATSAPP`, `EMAIL`, `IN_APP` | Parent / Guardian | `fee_receipt:{receipt_number}` | Needs payment confirmation dispatch to parent/student upon successful settlement |
| **4. Student Absence Alert** | `attendance_service.create_attendance` & `create_bulk_attendance` | None | `SMS`, `WHATSAPP`, `IN_APP` | Parent / Guardian | `student_absence:{student_id}:{attendance_date}` | Needs automated parent alert when student is marked `ABSENT` |
| **5. Homework Published** | `homework_service.publish_homework` | In-App notification only | `SMS`, `WHATSAPP`, `IN_APP` | Students & Parents | `homework_published:{homework_id}` | Existing implementation only creates in-app notification; needs multi-channel SMS/WhatsApp trigger |

---

## 5. Recipient Resolution & Relationship Mapping

### 1. Visitor Check-In Alert
- **Host Resolution**:
  - `HostType.TEACHER` -> Resolves `Teacher.email` / `phone` or linked `IdentityUser`.
  - `HostType.STAFF` -> Resolves `IdentityUser` or `Teacher`.
  - `HostType.STUDENT` -> Resolves linked Parent/Guardian contact details via `ParentStudent` relationship.
- **Tenant Protection**: Verifies host `school_id == visitor.school_id`.

### 2. Fee Receipt Confirmation
- **Parent Resolution**: Resolves primary parent/guardian linked to the `Student` via `ParentStudent` relationship (`is_primary=True` or first active linked parent).
- **Fallback**: Student's contact details if no linked parent is registered.

### 3. Student Absence Alert
- **Parent Resolution**: Resolves active `Parent` linked to the `Student` marked `ABSENT`.
- **Tenant Scope**: Guarantees parent and student belong strictly to `current_school_id`.

### 4. Homework Publication Alert
- **Target Audience**: All active students in `school_class_id` (and `section_id` if specified), plus their registered parents.

---

## 6. Architecture & Transaction Safety Controls

### A. Post-Commit Dispatch Pattern (Outbox / Background Task)
To prevent the dangerous flaw where a notification is sent externally before a database transaction rolls back, all event triggers will use a **Post-Commit Dispatch Pattern**:
```text
1. ERP Business Operation (e.g. record payment, mark absent)
2. Create Notification Record (status = PENDING) within DB transaction
3. DB Transaction COMMITS successfully
4. Enqueue Background Task (FastAPI BackgroundTasks or AsyncJobRunner)
5. Background Worker dispatches via NotificationService -> Provider
```
*Result*: If the DB transaction fails or rolls back, zero notifications are sent. If provider dispatch fails, the ERP business transaction remains 100% committed and successful.

### B. Failure Isolation
- Provider outages, timeouts (HTTP 408/504), DLT rejection, or invalid recipient numbers will mark the `Notification` status as `FAILED` or `RETRYABLE`, but will **NEVER** roll back fee receipts, visitor check-ins, or attendance records.

### C. Strict Idempotency Keys
- Deterministic key generation guarantees duplicate API calls, worker retries, or network retransmissions produce zero duplicate notifications:
  - `visitor_checkin:{visitor_id}`
  - `fee_receipt:{receipt_number}`
  - `student_absence:{student_id}:{attendance_date}`
  - `homework_published:{homework_id}`

### D. PII & Credential Security
- Event payloads store strictly non-sensitive entity references (`student_id`, `receipt_number`, `visitor_id`).
- Access tokens, passwords, and sensitive IDs are strictly prohibited from event payloads and log output.

---

## 7. Recommended Internal Execution Subphases

To ensure systematic verification and 0 regression, Phase 27.4 will be executed across the following internal subphases:

1. **Phase 27.4.1 — Event Dispatcher & Idempotency Foundation**
   - Core event trigger interfaces and transaction-safe background queue dispatches.
2. **Phase 27.4.2 — Visitor Event Notifications**
   - Integration with `check_in_visitor`, `quick_check_in_visitor`, and host notification dispatch.
3. **Phase 27.4.3 — Fee Receipt & Payment Confirmation Notifications**
   - Integration with `fee_service.record_payment` and `payment_settlement_service.settle_payment_transaction`.
4. **Phase 27.4.4 — Student Absence & Homework Publication Notifications**
   - Integration with `attendance_service` (`create_attendance`, `create_bulk_attendance`) and `homework_service.publish_homework`.
5. **Phase 27.4.5 — Multi-Domain Integration, Security & Regression Hardening**
   - Full cross-domain tests, preference opt-out verification, tenant isolation tests, and regression suite run.

---

## 8. Schema & Database Migration Impact
- **Database Schema**: Existing `Notification` model already supports `idempotency_key`, `channel`, `recipient_id`, `recipient_type`, `template_key`, `status`, `provider_message_id`, and `school_id`.
- **Migration**: **Zero database migrations required.** Single Alembic head `b5683cd19824` is preserved.

---

## 9. Next Steps
Upon review, implementation will proceed systematically starting with **Phase 27.4.1 (Foundation)** followed by incremental business domain integration.
