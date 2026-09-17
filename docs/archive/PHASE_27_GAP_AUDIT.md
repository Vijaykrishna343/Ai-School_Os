# Phase 27 — SMS/WhatsApp Notifications Engine — Gap Audit & Roadmap Discovery Report

## 1. Executive Summary

This document establishes the official product roadmap direction following the completion of **Phase 26 — Reception CRM & Visitor Management** (subphases 26.1–26.6).

Based on an exhaustive audit of repository documentation (`docs/product/feature-roadmap.md` and `docs/product/feature-gap-analysis.md`), the next official phase on the project's roadmap is:

**Phase 27 — SMS/WhatsApp Notifications** (or **SMS & WhatsApp Messaging Integration Engine**)

This audit identifies the authoritative requirements, analyzes existing baseline capabilities, inventories reusable infrastructure (built during Phase 8 and Phase 26), defines remaining technical and compliance gaps (such as Indian DLT regulatory compliance and native Meta WhatsApp Cloud API webhooks), evaluates security constraints, and outlines a safe 5-subphase execution roadmap.

**Strict Audit Boundary Compliance**: No source code, tests, schemas, or migrations were modified during this audit. Core authorization (`app/identity/security/authorization.py`) remains at **0 diff**.

---

## 2. Official Roadmap Evidence

Inspection of official project documentation confirms the following roadmap sequence:

- **Source Document 1**: `docs/product/feature-roadmap.md`
  - Lines 13–16 explicitly specify:
    ```markdown
    ### Planned Future Phases
    - **Phase 25**: Payment Gateway & Online Fee Collection (Unscheduled). [COMPLETED via 25.1–25.5]
    - **Phase 26**: Reception CRM & Visitor Management (Unscheduled). [COMPLETED via 26.1–26.6]
    - **Phase 27**: SMS/WhatsApp Notifications (Unscheduled).
    ```
- **Source Document 2**: `docs/product/feature-gap-analysis.md`
  - Lines 31–34 specify Phase 25, Phase 26, and Phase 27 as the core planned extension modules.
- **Source Document 3**: `PHASE_26_6_GAP_AUDIT.md`
  - Lines 110 & 126 explicitly defer SMS/WhatsApp notification triggers (e.g. host arrival alerts) to Phase 27.

**Conclusion**: **Phase 27 — SMS/WhatsApp Notifications** is unambiguously the next official roadmap phase.

---

## 3. Current Certified Baseline

```
Certified Project Baseline:
- Phase 26.1–26.6 Completed & Certified
- Full Backend Suite: 994 passed / 0 failed
- Full Frontend Suite: 144 passed / 0 failed (21 test files)
- TypeScript: PASS (0 errors)
- Production Build: PASS (vite build complete)
- Alembic Head: 721c276bdd9d (Single head)
- Authorization Core: 0 diff in app/identity/security/authorization.py
- Production Deployment: Intentionally deferred
```

---

## 4. Official Requirements for Phase 27

Phase 27 requires expanding the School ERP's communication engine from stub/mock/Twilio-only messaging into a production-grade, multi-tenant **SMS/WhatsApp Notifications Engine** with regional compliance:

1. **Indian Telecom DLT (Distributed Ledger Technology) SMS Compliance**: Support TRAI mandatory DLT parameters (`entity_id`, `header_id`, `template_id`) for Indian SMS gateways (Fast2SMS, MSG91, Textlocal).
2. **Meta WhatsApp Cloud API Direct Integration**: Support native Graph API messaging (`graph.facebook.com/v18.0/{phone_number_id}/messages`) alongside Twilio WhatsApp adapters, handling approved WhatsApp Highly Structured Message (HSM) templates.
3. **Inbound Delivery Webhooks & Real-Time Tracking**: Webhook endpoints for receiving delivery status receipts (`DELIVERED`, `READ`, `FAILED`) from Meta and Twilio.
4. **Tenant Provider Configuration Management**: Per-school tenant provider credentials and default gateway preferences (Twilio vs Meta Cloud API vs Fast2SMS).
5. **Event-Driven ERP Notification Triggers**: Automatic dispatch bindings for critical ERP events:
   - Visitor Check-In/Arrival alert SMS to Host (Phase 26)
   - Fee Receipt WhatsApp PDF link dispatch (Phase 25)
   - Student Absence SMS alert to Parent (Phase 22)
   - Homework Published WhatsApp alert (Phase 23)
6. **Tenant Quota & Rate Guardrails**: Per-tenant SMS/WhatsApp monthly quotas and rate limiting to prevent cost runaways.

---

## 5. Requirement Matrix

| Official Requirement | Status | Existing Implementation | Gap | Reusable Components | Risk |
|---|---|---|---|---|---|
| Multi-Channel Notification Model & Schema | **COMPLETE** | `notifications` & `user_communication_preferences` ORM tables (`backend/app/models/notification.py`, `communication.py`) | None | `NotificationChannel` enum (`SMS`, `WHATSAPP`, `EMAIL`, `IN_APP`) | Low |
| Basic Twilio SMS Adapter | **PARTIALLY COMPLETE** | `SmsNotificationProvider` (`backend/app/services/notification_providers/sms_provider.py`) | Missing Indian DLT registration parameters (`PE_ID`, `template_id`) & Fast2SMS gateway adapter | `BaseNotificationProvider` interface | Low |
| Basic WhatsApp Adapter | **PARTIALLY COMPLETE** | `WhatsAppNotificationProvider` (`backend/app/services/notification_providers/whatsapp_provider.py`) | Only wraps Twilio WhatsApp; lacks native Meta Cloud API & media document attachments | `BaseNotificationProvider` interface | Medium |
| Notification Service & Inbox | **COMPLETE** | `NotificationService` (`backend/app/services/notification_service.py`) | Needs provider strategy router for tenant-specific provider selection | `render_template`, idempotency handling | Low |
| DLT Parameter Registration | **MISSING** | None | DLT `entity_id`, `header_id`, and `dlt_template_id` metadata fields absent in template schemas | `NotificationTemplate` model | High (Regulatory rejection in India if missing) |
| Meta WhatsApp Cloud API Direct Adapter | **MISSING** | None | Native Graph API bearer token authentication, template component binding, and media object uploads absent | `WhatsAppNotificationProvider` stub | Medium |
| Provider Delivery Status Webhooks | **MISSING** | None | Webhook receivers (`/api/v1/notifications/webhooks/*`) for real-time `DELIVERED`/`READ` updates absent | `NotificationStatus` enum | Medium |
| Tenant Provider Configuration API & UI | **MISSING** | None | Admin UI and endpoint to configure tenant SMS/WhatsApp API credentials | `SchoolsPage.tsx` / `SettingsPage.tsx` | High (Secret credentials handling) |
| Event-Driven ERP Notification Triggers | **PARTIALLY COMPLETE** | `AsyncJobRunner` and notification batch APIs (`jobs.py`, `notifications.py`) | Event listeners binding Visitor arrival, Fee payment, Attendance absence to SMS/WhatsApp absent | `BackgroundTasks`, `async_job_runner` | Low |
| Message Rate & Quota Guardrails | **MISSING** | Sliding window rate limiter for login (`rate_limiter.py`) | Per-tenant outbound SMS/WhatsApp monthly quota enforcement absent | `rate_limiter.py` | Medium |

---

## 6. Existing Implementation Inventory

The codebase already possesses robust notification and communication building blocks established during Phase 8:

1. **Database ORM Models (`backend/app/models/`)**:
   - `Notification`: Stores outbound notifications, channels (`SMS`, `WHATSAPP`, `EMAIL`, `IN_APP`), delivery status (`PENDING`, `QUEUED`, `SENT`, `DELIVERED`, `FAILED`), error messages, retry counts, idempotency keys.
   - `UserCommunicationPreference`: Tracks user channel toggles (`enable_sms`, `enable_whatsapp`) and category preferences (`enable_attendance`, `enable_fees`, `enable_exams`, `enable_events`, etc.).
   - `NotificationTemplate`: Stores parameterized templates (`title_template`, `body_template`) mapped by `template_key`.

2. **Backend Services & Adapters (`backend/app/services/`)**:
   - `NotificationService`: Core coordinator handling template rendering, user preference filtering, idempotency, and retries.
   - `BaseNotificationProvider`: Abstract adapter interface.
   - `SmsNotificationProvider`: Twilio SMS implementation with mock fallback.
   - `WhatsAppNotificationProvider`: Twilio WhatsApp implementation with mock fallback.

3. **API Endpoints (`backend/app/api/v1/endpoints/notifications.py`)**:
   - Inbox: `GET /inbox`, `GET /unread-count`, `POST /inbox/{id}/read`.
   - Preferences: `GET /preferences`, `PUT /preferences`.
   - Operations: `GET /` (Delivery logs), `GET /providers/status`, `POST /send`, `POST /{id}/retry`, `POST /batch-send-async`.

4. **Frontend Interface (`frontend/src/pages/NotificationsPage.tsx`)**:
   - User Notification Inbox drawer, Communication Preferences modal, Admin Delivery Logs table, Provider Status indicators, Template list.

---

## 7. Reusable Infrastructure

Do NOT create a secondary notification framework. The existing architecture will be reused as follows:

- **Core Dispatcher**: Extend `NotificationService` (`backend/app/services/notification_service.py`) to route messages to dynamic tenant-configured providers.
- **Provider Adapters**: Extend `backend/app/services/notification_providers/` by adding `fast2sms_provider.py` and `meta_whatsapp_provider.py`.
- **Async Execution**: Reuse FastAPI `BackgroundTasks` and `AsyncJobRunner` (`backend/app/services/async_job_runner.py`) for non-blocking batch dispatches.
- **AI Content Generation**: Reuse AI Communication Draft Engine (`backend/app/ai/communication/engine.py`) for generating optimized SMS and WhatsApp text variants.
- **Frontend Workspace**: Extend `frontend/src/pages/NotificationsPage.tsx` and `communicationApi.ts` rather than building a duplicate page.

---

## 8. Backend Gap Analysis

1. **DLT Compliance Schema Extensions**: `NotificationTemplate` requires fields for `dlt_entity_id`, `dlt_header_id`, and `dlt_template_id`.
2. **Meta Cloud API Adapter**: Implement `MetaWhatsAppNotificationProvider` calling Meta Graph API v18.0 with Bearer token authentication and HSM JSON structure.
3. **Indian SMS Adapter**: Implement `Fast2SmsNotificationProvider` incorporating DLT parameters into POST payload.
4. **Webhook Receivers**:
   - `POST /api/v1/notifications/webhooks/whatsapp`: Validates Meta signature (`X-Hub-Signature-256`), parses delivery/read status updates, and updates `Notification` record.
   - `POST /api/v1/notifications/webhooks/twilio`: Validates Twilio signature (`X-Twilio-Signature`) for status callbacks.
5. **Tenant Provider Configuration**: Model `SchoolCommunicationConfig` (or encrypted tenant configuration fields) storing credentials per tenant (`school_id`).

---

## 9. Frontend Gap Analysis

1. **Communication Center Extensions (`NotificationsPage.tsx`)**:
   - **Tab 1: Inbox & Preferences** (Existing — operational).
   - **Tab 2: Provider Configuration & DLT Registry** (New — Admin manage API credentials & DLT IDs).
   - **Tab 3: Broadcast SMS/WhatsApp Campaign** (New — Multi-channel broadcast dispatcher with audience selectors).
   - **Tab 4: Delivery Analytics & Webhook Logs** (Enhanced — Real-time `DELIVERED`/`READ` badges).

---

## 10. Data Model / Migration Analysis

- **Schema Requirements**:
  - `NotificationTemplate`: Add optional fields `dlt_entity_id`, `dlt_template_id`, `whatsapp_template_name`, `whatsapp_language_code`.
  - `SchoolCommunicationConfig` (New Table): Stores per-tenant provider selection (`sms_provider_type`, `whatsapp_provider_type`) and encrypted API credentials (`school_id`, `twilio_account_sid`, `fast2sms_api_key`, `meta_whatsapp_token`, `meta_phone_number_id`, `sms_monthly_quota`).
- **Migration**: An Alembic migration will be required during implementation of Phase 27.1. (NO migration created during this audit).

---

## 11. Security & Authorization Analysis

1. **Multi-Tenant Isolation**: All provider credentials, templates, logs, and webhook updates MUST be strictly scoped by `school_id`.
2. **Webhook Security**:
   - Meta WhatsApp webhooks MUST verify SHA256 HMAC signature against app secret.
   - Twilio webhooks MUST verify Twilio signature header.
   - Unauthenticated/unverified webhook payloads MUST be rejected with HTTP 401.
3. **Secret Credential Storage**: Provider API keys/tokens must be encrypted at rest or fetched securely from environment variables.
4. **RBAC Guard**: Provider management requires `notification.provider.manage` permission.
5. **Authorization Core Protection**: `app/identity/security/authorization.py` MUST remain at **0 diff**.

---

## 12. Testing Requirements for Implementation

### Backend Tests
- DLT parameter validation & payload formatting.
- Meta WhatsApp Graph API payload construction & HSM template parameter substitution.
- Webhook signature validation (valid vs tampered signature).
- Webhook status state transitions (`SENT` -> `DELIVERED` -> `READ`).
- Cross-tenant isolation & provider credential scoping.
- Fallback to mock providers when credentials are omitted.

### Frontend Tests
- Provider configuration form rendering & validation.
- DLT template mapping drawer interactions.
- Campaign broadcast form submission.
- Real-time delivery status badge rendering.

### Full Regression Suite
- 994+ backend tests passing
- 144+ frontend tests passing
- TypeScript 0 errors
- Production build success
- Single Alembic head
- `authorization.py` 0 diff

---

## 13. Recommended Internal Subphases

To execute Phase 27 cleanly and safely, it should be subdivided into 5 internal execution increments:

1. **Phase 27.1 — SMS/WhatsApp Foundation & Tenant Provider Configuration**
   - Data model & Alembic migration for `SchoolCommunicationConfig` & DLT template metadata.
2. **Phase 27.2 — Indian DLT SMS Gateway & Provider Adapters**
   - Fast2SMS / Twilio SMS adapters with DLT parameter headers (`PE_ID`, `template_id`).
3. **Phase 27.3 — Meta WhatsApp Cloud API Adapter & Webhooks**
   - Native Graph API direct adapter, HSM template renderer, and webhook receivers for delivery/read callbacks.
4. **Phase 27.4 — Event-Driven ERP Triggers & Broadcast Engine**
   - Automated event listeners for Visitor arrival (Phase 26), Fee receipt (Phase 25), Absence (Phase 22), Homework (Phase 23).
5. **Phase 27.5 — Communication Center UI & Delivery Analytics**
   - Provider management UI, DLT mapping ledger, campaign broadcast builder, delivery status dashboards.

---

## 14. Explicit Out-of-Scope Items

- Inbound two-way conversational AI chat / auto-reply bots (out of scope for Phase 27).
- Voice call / IVR integration.
- Custom payment gateway webhooks (already handled in Phase 25).

---

## 15. Risks / Open Questions

1. **Meta WhatsApp Template Approval**: Meta requires template pre-approval before HSM dispatches can be sent via WhatsApp Cloud API. The implementation must gracefully fall back to SMS or mock dispatch if a template is not yet approved by Meta.
2. **TRAI DLT Template Registration**: Indian telecom operators require DLT template ID matching. Templates must strictly match registered DLT text.

---

## 16. Audit Verification

Verification checks executed during audit:
- `git status --short`: Verified (Only untracked uploaded test documents in storage).
- `git diff -- app/identity/security/authorization.py`: **0 diff**
- `python -m alembic heads`: **Single head (`721c276bdd9d`)**

---

## FINAL REPORT SUMMARY

### Official Next Phase
**Phase 27 — SMS/WhatsApp Notifications** (SMS & WhatsApp Messaging Integration Engine)

### Confidence
**HIGH** (Supported by `docs/product/feature-roadmap.md`, `docs/product/feature-gap-analysis.md`, and `PHASE_26_6_GAP_AUDIT.md`)

### Implementation Readiness
**READY** (Architecture, Phase 8 baseline, models, and gaps are fully defined)

### Major Gaps
- Indian Telecom DLT registration metadata (`PE_ID`, `template_id`)
- Direct Meta WhatsApp Cloud API adapter & HSM payload builder
- Inbound provider status webhooks (`DELIVERED`, `READ`)
- Tenant provider credentials configuration (`SchoolCommunicationConfig`)
- Event-driven ERP trigger bindings

### Reusable Infrastructure
- `Notification` & `UserCommunicationPreference` ORM models (`backend/app/models/`)
- `NotificationService` coordinator (`backend/app/services/notification_service.py`)
- `SmsNotificationProvider` & `WhatsAppNotificationProvider` adapters (`backend/app/services/notification_providers/`)
- `AsyncJobRunner` for background dispatch (`backend/app/services/async_job_runner.py`)
- `NotificationsPage.tsx` & `communicationApi.ts` (`frontend/src/`)

### Migration Required?
**YES** (Requires Alembic migration for `SchoolCommunicationConfig` and DLT metadata fields on `NotificationTemplate` when Phase 27.1 starts).

### Recommended Internal Subphases
1. Phase 27.1 — SMS/WhatsApp Foundation & Tenant Provider Configuration
2. Phase 27.2 — Indian DLT SMS Gateway & Provider Adapters
3. Phase 27.3 — Meta WhatsApp Cloud API Adapter & Webhooks
4. Phase 27.4 — Event-Driven ERP Triggers & Broadcast Engine
5. Phase 27.5 — Communication Center UI & Delivery Analytics

### Security Risks
- Signature forgery on WhatsApp/Twilio webhooks (Mitigation: HMAC SHA-256 header validation)
- Exposure of provider API keys (Mitigation: Encrypted storage or environment variable overrides)
- Unbounded outbound messaging costs (Mitigation: Tenant monthly SMS quota guardrails)

### Open Questions
- Should default SMS gateway for Indian tenants default to Fast2SMS or Twilio SMS? (Recommendation: Configurable per tenant, default to Twilio with Fast2SMS as alternative).

### Recommended Next Action
Prompt the user for approval to proceed with **Phase 27.1 — SMS/WhatsApp Foundation & Tenant Provider Configuration**.
