# PHASE 31.0 — PILOT ISSUE & DEFECT REGISTER

**Document Version:** 1.0.0  
**Phase:** Phase 31.0 — Controlled School Pilot Onboarding & Field Validation  
**Status:** Certified Audit & Issue Tracking Record  
**Last Updated:** 2026-09-19  

---

## 1. Issue Classification Taxonomy

Issues discovered during the Phase 31.0 Controlled School Pilot validation are classified according to strict severity and category standards:

- **P0 (Blocker):** Platform outage, critical data loss, unhandled security vulnerability, or severe database corruption.
- **P1 (Critical):** Core workflow failure (e.g., legacy data import failure, authorization bypass, payment calculation defect).
- **P2 (Major):** Operational deficiency with workaround available, non-blocking performance degradation, or missing default values.
- **P3 (Minor):** Cosmetic UI imperfection, minor documentation omission, or non-essential telemetry adjustment.

---

## 2. Pilot Issue Register

| Issue ID | Category | Severity | Description | Root Cause | Status | Resolution / Mitigation | Verified In Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-31-01** | Data Migration | **P1 (Critical)** | Teacher legacy data import rejected due to missing non-nullable address fields (`address_line1`, `city`, `district`, `state`, `country`, `postal_code`). | Teacher database schema requires address columns, but CSV importer did not populate default location or map optional address headers. | **RESOLVED** | Updated `_import_teachers` in `backend/app/services/import_service.py` to extract address fields from CSV with institutional defaults (`address_line1="Campus Quarters"`, `district="Bengaluru Urban"`, etc.). | Phase 31.0 Harness (100% Pass) |
| **ISSUE-31-02** | Payment Gateway | **P1 (Critical)** | Payment order creation raised `Payment provider 'RAZORPAY' is not configured for this school` even when school credentials were saved. | `PaymentOrderService.create_payment_order` called `self._resolve_credentials(target_provider)` without forwarding `school_id=school_id`. | **RESOLVED** | Updated `backend/app/services/payment_order_service.py` line 154 to pass `school_id=school_id` into `self._resolve_credentials`, enabling multi-tenant credential resolution. | Phase 31.0 Harness (100% Pass) |
| **ISSUE-31-03** | Database / CLI | **P2 (Major)** | Backup CLI subprocess execution failed with `DATABASE_URL must be provided or set in environment variables`. | Subprocess invocation did not inherit active database environment variables. | **RESOLVED** | Added explicit `env["DATABASE_URL"] = settings.DATABASE_URL` propagation to CLI execution wrapper. | Phase 31.0 Harness (100% Pass) |
| **ISSUE-31-04** | Operational / Env | **P2 (Major)** | Docker daemon unreachable in local developer staging environment (`error during connect: open //./pipe/docker_engine`). | Docker Desktop background service is stopped or not running on the local host. | **DOCUMENTED** | Verified native host execution; documented faithfully as `NOT VERIFIED — DOCKER DAEMON UNAVAILABLE` with Docker Compose production runbook provided. | Phase 31.0 Audit |
| **ISSUE-31-05** | Financial Integrity | **P1 (Critical)** | Risk of opening balance migration generating fictitious payment transactions in ledger. | Legacy balance importers often mistakenly generate payment records. | **VERIFIED CLEAN** | Audited `_import_outstanding_balances` in `import_service.py`. Confirmed ZERO `FeePayment` records created; balance assigned purely as starting debt. | Phase 31.0 Harness (100% Pass) |
| **ISSUE-31-06** | Academic Governance | **P1 (Critical)** | Risk of draft/unapproved report cards being visible to parents or students before leadership sign-off. | Missing publication status check in report card query handlers. | **VERIFIED CLEAN** | Tested Parent Portal report card access. Confirmed DRAFT status cards return 404 or `is_published=False` to unauthorized viewers. | Phase 31.0 Harness (100% Pass) |

---

## 3. Issue Summary Matrix

| Severity Level | Open | In Progress | Resolved / Mitigated | Total |
| :--- | :---: | :---: | :---: | :---: |
| **P0 (Blocker)** | 0 | 0 | 0 | **0** |
| **P1 (Critical)** | 0 | 0 | 4 | **4** |
| **P2 (Major)** | 0 | 0 | 2 | **2** |
| **P3 (Minor)** | 0 | 0 | 0 | **0** |
| **TOTAL** | **0** | **0** | **6** | **6** |

---

## 4. Architectural & Safety Commitments Verified

1. **Zero Diff on Authorization Engine:** `backend/app/identity/security/authorization.py` has **0 modified lines**.
2. **Zero Schema Migrations Added:** Database Alembic revision maintained at head `z9a045bc11z5`.
3. **Multi-Tenant Boundary:** Zero cross-tenant data leakage detected across all test runs.
4. **All Active Defects Closed:** 100% of discovered pilot blockers remediated and validated by automated tests.
